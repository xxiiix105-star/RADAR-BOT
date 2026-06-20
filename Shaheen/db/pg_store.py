"""
PostgreSQL document store — provides MongoDB-compatible API using JSONB.
This module is the heart of the Shaheen bot's database layer.
"""
import asyncio
import json
import os
import uuid
from threading import RLock

import psycopg2
import psycopg2.extras
from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool

DATABASE_URL = os.environ.get("DATABASE_URL", "")

_pool_lock = RLock()
_pool = None


def get_pool() -> ThreadedConnectionPool:
    global _pool
    with _pool_lock:
        if _pool is None:
            if not DATABASE_URL:
                raise RuntimeError("DATABASE_URL environment variable is not set")
            url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
            _pool = ThreadedConnectionPool(1, 15, url)
    return _pool


def init_store():
    """Create the generic_store table and indexes on startup."""
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS generic_store (
                    collection TEXT NOT NULL,
                    doc_id     TEXT NOT NULL,
                    data       JSONB NOT NULL,
                    PRIMARY KEY (collection, doc_id)
                )
            """)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_gs_collection "
                "ON generic_store(collection)"
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_gs_data "
                "ON generic_store USING GIN(data)"
            )
            conn.commit()
    finally:
        get_pool().putconn(conn)


def _matches(data: dict, query: dict) -> bool:
    """Python-side JSONB document query matching."""
    import re as _re
    for key, val in query.items():
        d_val = data.get(key)
        if isinstance(val, dict):
            for op, op_val in val.items():
                if op == '$gt':
                    if d_val is None or not (d_val > op_val):
                        return False
                elif op == '$lt':
                    if d_val is None or not (d_val < op_val):
                        return False
                elif op == '$gte':
                    if d_val is None or not (d_val >= op_val):
                        return False
                elif op == '$lte':
                    if d_val is None or not (d_val <= op_val):
                        return False
                elif op == '$ne':
                    if d_val == op_val:
                        return False
                elif op == '$in':
                    if d_val not in op_val:
                        return False
                elif op == '$regex':
                    if not _re.search(op_val, str(d_val or '')):
                        return False
                elif op == '$exists':
                    if op_val and key not in data:
                        return False
                    if not op_val and key in data:
                        return False
        else:
            if d_val != val:
                return False
    return True


def _apply_update_operators(doc: dict, update: dict) -> dict:
    """Apply MongoDB-style update operators to a document dict."""
    merged = dict(doc)
    has_op = any(k.startswith('$') for k in update)
    if not has_op:
        merged.update(update)
        return merged
    for op, op_data in update.items():
        if op == '$set':
            merged.update(op_data)
        elif op == '$addToSet':
            for field, spec in op_data.items():
                arr = list(merged.get(field, []))
                items = (
                    spec.get('$each', []) if isinstance(spec, dict) and '$each' in spec
                    else [spec]
                )
                for item in items:
                    if item not in arr:
                        arr.append(item)
                merged[field] = arr
        elif op == '$push':
            for field, spec in op_data.items():
                arr = list(merged.get(field, []))
                items = (
                    spec.get('$each', []) if isinstance(spec, dict) and '$each' in spec
                    else [spec]
                )
                arr.extend(items)
                merged[field] = arr
        elif op == '$pull':
            for field, spec in op_data.items():
                arr = list(merged.get(field, []))
                if isinstance(spec, dict):
                    arr = [
                        item for item in arr
                        if not all(
                            item.get(k) == v
                            for k, v in spec.items()
                            if not isinstance(v, dict)
                        )
                    ]
                else:
                    arr = [item for item in arr if item != spec]
                merged[field] = arr
        elif op == '$unset':
            for field in op_data:
                merged.pop(field, None)
        elif op == '$inc':
            for field, inc_val in op_data.items():
                merged[field] = merged.get(field, 0) + inc_val
    return merged


# ─────────────────────────────────────────────────────────
#  Sync MongoDB-compatible class
# ─────────────────────────────────────────────────────────

class MongoDB:
    """Sync MongoDB-compatible class backed by PostgreSQL JSONB store."""

    def __init__(self, collection: str) -> None:
        self.collection = collection

    # ── write ──────────────────────────────────────────────

    def insert_one(self, document: dict):
        doc = dict(document)
        if '_id' not in doc:
            doc['_id'] = str(uuid.uuid4())
        doc_id = str(doc['_id'])
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO generic_store (collection, doc_id, data) "
                    "VALUES (%s, %s, %s) "
                    "ON CONFLICT (collection, doc_id) DO NOTHING",
                    (self.collection, doc_id, Json(doc)),
                )
                conn.commit()
        finally:
            pool.putconn(conn)
        return doc_id

    def update(self, query: dict, update_data: dict):
        doc = self.find_one(query)
        if not doc:
            return 0, None
        doc_id = str(doc.get('_id', ''))
        merged = _apply_update_operators(doc, update_data)
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE generic_store SET data=%s "
                    "WHERE collection=%s AND doc_id=%s",
                    (Json(merged), self.collection, doc_id),
                )
                conn.commit()
        finally:
            pool.putconn(conn)
        return 1, merged

    def replace(self, query: dict, new_data: dict):
        old = self.find_one(query)
        if not old:
            return old, None
        doc_id = str(old.get('_id', str(uuid.uuid4())))
        new_data = dict(new_data)
        new_data['_id'] = old['_id']
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE generic_store SET data=%s "
                    "WHERE collection=%s AND doc_id=%s",
                    (Json(new_data), self.collection, doc_id),
                )
                conn.commit()
        finally:
            pool.putconn(conn)
        return old, new_data

    def delete_one(self, query: dict):
        pool = get_pool()
        conn = pool.getconn()
        try:
            if '_id' in query:
                doc_id = str(query['_id'])
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM generic_store WHERE collection=%s AND doc_id=%s",
                        (self.collection, doc_id),
                    )
                    conn.commit()
            else:
                doc = self.find_one(query)
                if doc and '_id' in doc:
                    with conn.cursor() as cur:
                        cur.execute(
                            "DELETE FROM generic_store WHERE collection=%s AND doc_id=%s",
                            (self.collection, str(doc['_id'])),
                        )
                        conn.commit()
        finally:
            pool.putconn(conn)
        return self.count()

    def delete_many(self, query: dict):
        docs = self.find_all(query)
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                for doc in docs:
                    if '_id' in doc:
                        cur.execute(
                            "DELETE FROM generic_store WHERE collection=%s AND doc_id=%s",
                            (self.collection, str(doc['_id'])),
                        )
                conn.commit()
        finally:
            pool.putconn(conn)

    # ── read ───────────────────────────────────────────────

    def find_one(self, query: dict):
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                # Fast path: single _id lookup
                if '_id' in query and len(query) == 1:
                    cur.execute(
                        "SELECT data FROM generic_store "
                        "WHERE collection=%s AND doc_id=%s LIMIT 1",
                        (self.collection, str(query['_id'])),
                    )
                    row = cur.fetchone()
                    return row[0] if row else False

                # Medium path: single simple key lookup → use JSONB containment
                if len(query) == 1:
                    key, val = next(iter(query.items()))
                    if not isinstance(val, dict):
                        cur.execute(
                            "SELECT data FROM generic_store "
                            "WHERE collection=%s AND data @> %s::jsonb LIMIT 1",
                            (self.collection, json.dumps({key: val})),
                        )
                        row = cur.fetchone()
                        return row[0] if row else False

                # Full scan with Python matching
                cur.execute(
                    "SELECT data FROM generic_store WHERE collection=%s",
                    (self.collection,),
                )
                for row in cur.fetchall():
                    if _matches(row[0], query):
                        return row[0]
                return False
        finally:
            pool.putconn(conn)

    def find_all(self, query: dict = None):
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                if query is None:
                    cur.execute(
                        "SELECT data FROM generic_store WHERE collection=%s",
                        (self.collection,),
                    )
                    return [row[0] for row in cur.fetchall()]

                if len(query) == 1:
                    key, val = next(iter(query.items()))
                    if not isinstance(val, dict):
                        cur.execute(
                            "SELECT data FROM generic_store "
                            "WHERE collection=%s AND data @> %s::jsonb",
                            (self.collection, json.dumps({key: val})),
                        )
                        return [row[0] for row in cur.fetchall()]

                cur.execute(
                    "SELECT data FROM generic_store WHERE collection=%s",
                    (self.collection,),
                )
                return [row[0] for row in cur.fetchall() if _matches(row[0], query)]
        finally:
            pool.putconn(conn)

    def count(self, query: dict = None):
        if query is None:
            pool = get_pool()
            conn = pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT COUNT(*) FROM generic_store WHERE collection=%s",
                        (self.collection,),
                    )
                    return cur.fetchone()[0]
            finally:
                pool.putconn(conn)
        return len(self.find_all(query))

    @staticmethod
    def close():
        pass


# ─────────────────────────────────────────────────────────
#  Sync collection (pymongo-like surface)
# ─────────────────────────────────────────────────────────

class SyncCollection:
    """Sync pymongo-compatible collection object."""

    def __init__(self, name: str):
        self._db = MongoDB(name)
        self._name = name

    def find_one(self, query=None, projection=None):
        return self._db.find_one(query or {})

    def insert_one(self, doc):
        return self._db.insert_one(doc)

    def delete_one(self, query):
        return self._db.delete_one(query)

    def delete_many(self, query):
        self._db.delete_many(query)

    def find(self, query=None):
        return self._db.find_all(query or {})

    def count_documents(self, query=None):
        return self._db.count(query)

    def update_one(self, query: dict, update: dict, upsert: bool = False):
        doc = self._db.find_one(query)
        if not doc and not upsert:
            class _R:
                modified_count = 0
            return _R()

        if not doc and upsert:
            new_doc = {k: v for k, v in query.items() if not isinstance(v, dict)}
            new_doc = _apply_update_operators(new_doc, update)
            self._db.insert_one(new_doc)
            class _R:
                modified_count = 1
            return _R()

        merged = _apply_update_operators(doc, update)
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE generic_store SET data=%s "
                    "WHERE collection=%s AND doc_id=%s",
                    (Json(merged), self._name, str(doc.get('_id', ''))),
                )
                conn.commit()
        finally:
            pool.putconn(conn)

        class _R:
            modified_count = 1
        return _R()

    def update(self, query, update, upsert=False, multi=False):
        return self.update_one(query, update, upsert=upsert)


# ─────────────────────────────────────────────────────────
#  Async collection (motor-like surface)
# ─────────────────────────────────────────────────────────

class AsyncCollection:
    """Async motor-compatible collection (sync ops wrapped in asyncio.to_thread)."""

    def __init__(self, name: str):
        self._sync = SyncCollection(name)
        self._db = MongoDB(name)
        self._name = name

    async def find_one(self, query: dict):
        return await asyncio.to_thread(self._db.find_one, query)

    async def insert_one(self, doc: dict):
        return await asyncio.to_thread(self._db.insert_one, doc)

    async def delete_one(self, query: dict):
        return await asyncio.to_thread(self._db.delete_one, query)

    async def update_one(self, query: dict, update: dict, upsert: bool = False):
        return await asyncio.to_thread(self._sync.update_one, query, update, upsert)

    async def count_documents(self, query: dict = None):
        return await asyncio.to_thread(self._db.count, query)

    def find(self, query: dict = None):
        return AsyncCursor(self._db, query)


class AsyncCursor:
    """Async cursor with to_list() and async-iteration support."""

    def __init__(self, db: MongoDB, query: dict = None):
        self._db = db
        self._query = query
        self._items = None
        self._index = 0

    async def _load(self):
        if self._items is None:
            self._items = await asyncio.to_thread(self._db.find_all, self._query)

    async def to_list(self, length=None):
        await self._load()
        if length is not None:
            return self._items[:length]
        return list(self._items)

    def __aiter__(self):
        return self

    async def __anext__(self):
        await self._load()
        if self._index >= len(self._items):
            raise StopAsyncIteration
        item = self._items[self._index]
        self._index += 1
        return item


# ─────────────────────────────────────────────────────────
#  Database proxy objects (replace pymongo client)
# ─────────────────────────────────────────────────────────

class PGDatabase:
    """
    Replaces both the motor AsyncIOMotorClient db handle AND the pymongo
    client database handle.  Attribute access returns AsyncCollection (for
    motor-style code); subscript access returns SyncCollection (for pymongo-
    style code).
    """

    def __getitem__(self, collection_name: str) -> SyncCollection:
        return SyncCollection(collection_name)

    def __getattr__(self, collection_name: str) -> AsyncCollection:
        if collection_name.startswith('_'):
            raise AttributeError(collection_name)
        return AsyncCollection(collection_name)
