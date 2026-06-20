import asyncio
import time
from inspect import getfullargspec
from aiohttp import ClientSession
from pyrogram import Client
from pyrogram.types import Message
from config import Config
import pytz
from datetime import datetime

IST = pytz.timezone('UTC')
current_datetime = datetime.now(IST)
date = current_datetime.strftime("%a/%d/%b/%Y %H:%M:%S")

MOD_LOAD = []
MOD_NOLOAD = []

LOG_GROUP_ID = Config.LOG_GROUP_ID
bot_start_time = time.time()
DB_URI = Config.BASE_DB
MONGO_URL = Config.MONGO_URL
OWNER_ID = Config.OWNER_ID

from pgstore import get_pool, PGDatabase, init_store
get_pool()
init_store()

dbn = PGDatabase()
db = PGDatabase()

loop = asyncio.get_event_loop()
aiohttpsession = ClientSession(loop=loop)

bot = Client(
    "supun",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    ipv6=False
)

app = Client(
    "app2",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID1,
    api_hash=Config.API_HASH1,
    ipv6=False
)

BOT_ID = int(Config.BOT_TOKEN.split(":")[0])
BOT_NAME = "Shaheen"
BOT_USERNAME = Config.BOT_USERNAME or ""
BOT_MENTION = f"@{BOT_USERNAME}" if BOT_USERNAME else "Shaheen"
BOT_DC_ID = 1

async def _init_bot_info():
    global BOT_NAME, BOT_USERNAME, BOT_MENTION, BOT_DC_ID
    try:
        me = await app.get_me()
        BOT_NAME = me.first_name + (me.last_name or "")
        BOT_USERNAME = me.username or ""
        BOT_MENTION = me.mention
        BOT_DC_ID = me.dc_id
    except Exception as e:
        print(f"Could not fetch bot info: {e}")

async def eor(msg: Message, **kwargs):
    func = (
        (msg.edit_text if msg.from_user.is_self else msg.reply)
        if msg.from_user
        else msg.reply
    )
    spec = getfullargspec(func.__wrapped__).args
    return await func(**{k: v for k, v in kwargs.items() if k in spec})
