"""
Shaheen bot — database collection registry.
All MongoDB/motor references replaced with PostgreSQL-backed equivalents.
"""
from Shaheen.db.pg_store import MongoDB, AsyncCollection, SyncCollection

# ── Async collections (motor-style, used with `await`) ────────────────────
langdb        = AsyncCollection('language')
chatsdb       = AsyncCollection('chats')
nexaub_antif  = AsyncCollection('nexa_antif')
antiservicedb = AsyncCollection('antiservice')
flooddb       = AsyncCollection('flood_toggle')
usersdb       = AsyncCollection('users')
restartdb     = AsyncCollection('restart_stage')
kukib         = AsyncCollection('kuki')
lunab         = AsyncCollection('luna')
taggeddb      = AsyncCollection('tagallert')
botlock       = AsyncCollection('botlock')
afkusers      = AsyncCollection('afkusers')

# ── Sync collections (pymongo-style, used without `await`) ─────────────────
chatb         = SyncCollection('chatbot')
nightmod      = SyncCollection('nightmode2')
lockdb        = SyncCollection('lockdb1')
urllockdb     = SyncCollection('urllockdb')
nm            = SyncCollection('Nightmode')
federation    = SyncCollection('federation')
