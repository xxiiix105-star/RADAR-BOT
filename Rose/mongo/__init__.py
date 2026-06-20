"""
Rose/mongo/__init__.py — PostgreSQL-backed drop-in for the old pymongo layer.
All collection names are preserved so every plugin continues to work unchanged.
"""
from Shaheen.db.pg_store import PGDatabase, MongoDB, get_pool, init_store

# Ensure the PostgreSQL store is initialised
get_pool()
init_store()

# Primary database proxy
db = PGDatabase()

# Named collection aliases — mirrors the old pymongo collection variables
langdb        = db.language
chatsdb       = db.chats
nexaub_antif  = db.nexa_mongodb
antiservicedb = db.antiservice
flooddb       = db.flood_toggle
usersdb       = db.users
restartdb     = db.restart_stage
chatb         = db.chatbot
kukib         = db.kuki
lunab         = db.luna
nightmod      = db.nightmode2
taggeddb      = db.tagallert
lockdb        = db.lockdb1
botlock       = db.botlock
afkusers      = db.afkusers

# Federation / nightmode collections (were backed by a separate Mongo client)
federation    = db["federation"]   # SyncCollection
nm            = db["Nightmode"]    # SyncCollection

__all__ = [
    "db", "MongoDB",
    "langdb", "chatsdb", "nexaub_antif", "antiservicedb", "flooddb",
    "usersdb", "restartdb", "chatb", "kukib", "lunab", "nightmod",
    "taggeddb", "lockdb", "botlock", "afkusers", "federation", "nm",
]
