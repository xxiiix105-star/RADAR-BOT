import asyncio
import time
from inspect import getfullargspec
from aiohttp import ClientSession
from pyrogram import Client
from pyrogram.types import Message
from config import Config
import pytz
from datetime import datetime

# استخدام التوقيت العالمي لضبط التزامن
IST = pytz.timezone('UTC')
current_datetime = datetime.now(IST)
date = current_datetime.strftime("%a/%d/%b/%Y %H:%M:%S")

MOD_LOAD = []
MOD_NOLOAD = []

LOG_GROUP_ID = Config.LOG_GROUP_ID
bot_start_time = time.time()
DB_URI = Config.BASE_DB
OWNER_ID = Config.OWNER_ID

# تهيئة مخزن وقاعدة بيانات PostgreSQL بالمسار الجديد المستقر
from shaheen.db.pg_store import get_pool, PGDatabase, init_store
get_pool()
init_store()

# استبدال كائنات الـ MongoDB بكائنات الـ PostgreSQL الجديدة
dbn = PGDatabase()
db = PGDatabase()

loop = asyncio.get_event_loop()
aiohttpsession = ClientSession(loop=loop)

# 1. تعريف وتشغيل البوت الأساسي مع تصفير فارق الوقت فوراً
bot = Client(
    "supun",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    ipv6=True
)

bot.start()
bot.session.session_time_offset = 0

# 2. تعريف وتشغيل الحساب المساعد مع تصفير فارق الوقت فوراً
app = Client(
    "app2",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID1,
    api_hash=Config.API_HASH1,
    ipv6=True
)

app.start()
app.session.session_time_offset = 0

x = app.get_me()

BOT_ID = int(Config.BOT_TOKEN.split(":")[0])
BOT_NAME = x.first_name + (x.last_name or "")
BOT_USERNAME = x.username
BOT_MENTION = x.mention
BOT_DC_ID = x.dc_id

async def eor(msg: Message, **kwargs):
    func = (
        (msg.edit_text if msg.from_user.is_self else msg.reply)
        if msg.from_user
        else msg.reply
    )
    spec = getfullargspec(func.__wrapped__).args
    return await func(**{k: v for k, v in kwargs.items() if k in spec})
    
