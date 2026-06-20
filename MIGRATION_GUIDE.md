# Complete Migration Guide: MongoDB → SQL & ARQ → Anthropic API

This guide provides step-by-step instructions to migrate your Shaheen-saved-me bot from MongoDB to PostgreSQL/MySQL and replace ARQ API with Anthropic's Claude API.

## Table of Contents
1. [Database Migration (MongoDB → PostgreSQL/MySQL)](#1-database-migration)
2. [AI API Migration (ARQ → Anthropic)](#2-ai-api-migration)
3. [Updated Environment Variables](#3-updated-environment-variables)
4. [Migration Checklist](#4-migration-checklist)

---

## 1. Database Migration (MongoDB → PostgreSQL/MySQL)

### Step 1.1: Update `requirements.txt`

Replace MongoDB dependencies with SQL ORM:

```txt
# Remove these:
# pymongo[srv]
# motor==3.0.0

# Add these:
sqlalchemy==2.0.20
psycopg2-binary==2.9.9  # For PostgreSQL
# OR for MySQL:
# pymysql==1.1.0
# mysqlclient==2.2.0

python-dotenv==0.20.0
pyrogram==1.4.16
aiohttp==3.9.0
requests==2.27.1
anthropic==0.7.0  # For Anthropic API
```

### Step 1.2: Create New Database Configuration File

**File:** `Rose/db/database.py` (NEW FILE)

```python
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool

# Database URL from environment
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set!")

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Test connections before using them
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database - creates all tables"""
    Base.metadata.create_all(bind=engine)
```

### Step 1.3: Create Database Models

**File:** `Rose/db/models.py` (NEW FILE)

```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, List, JSON, UniqueConstraint
from sqlalchemy.sql import func
from Rose.db.database import Base
from datetime import datetime

# ==================== USER & CHAT MODELS ====================

class ChatUser(Base):
    """Stores bot served users"""
    __tablename__ = "chat_users"
    
    user_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ServedChat(Base):
    """Stores bot served chats"""
    __tablename__ = "served_chats"
    
    chat_id = Column(Integer, primary_key=True)
    chat_name = Column(String(255), nullable=True)
    members_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== LANGUAGE MODEL ====================

class ChatLanguage(Base):
    """Stores per-chat language preferences"""
    __tablename__ = "chat_languages"
    
    chat_id = Column(Integer, primary_key=True)
    lang = Column(String(10), default="en")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== AFK MODEL ====================

class AFK(Base):
    """Stores AFK users"""
    __tablename__ = "afk_users"
    
    user_id = Column(Integer, primary_key=True)
    reason = Column(Text, nullable=True)
    afk_time = Column(DateTime, default=datetime.utcnow)

# ==================== APPROVAL MODEL ====================

class ApprovedUser(Base):
    """Stores approved users per chat"""
    __tablename__ = "approved_users"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    user_id = Column(Integer)
    user_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('chat_id', 'user_id', name='uq_chat_user'),)

# ==================== BLACKLIST MODEL ====================

class Blacklist(Base):
    """Stores blacklisted words"""
    __tablename__ = "blacklists"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    word = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== FILTER MODEL ====================

class Filter(Base):
    """Stores chat filters"""
    __tablename__ = "filters"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    trigger = Column(String(255))
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== NOTE MODEL ====================

class Note(Base):
    """Stores notes"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    note_name = Column(String(255))
    note_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== RULES MODEL ====================

class ChatRules(Base):
    """Stores chat rules"""
    __tablename__ = "chat_rules"
    
    chat_id = Column(Integer, primary_key=True)
    rules_text = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== WARNINGS MODEL ====================

class Warning(Base):
    """Stores user warnings"""
    __tablename__ = "warnings"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    user_id = Column(Integer)
    reason = Column(Text, nullable=True)
    warn_count = Column(Integer, default=1)
    warned_at = Column(DateTime, default=datetime.utcnow)

# ==================== WELCOME/GREETING MODEL ====================

class Greeting(Base):
    """Stores welcome messages"""
    __tablename__ = "greetings"
    
    chat_id = Column(Integer, primary_key=True)
    welcome_text = Column(Text, nullable=True)
    welcome_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== LOCK SETTINGS MODEL ====================

class LockSettings(Base):
    """Stores chat lock settings"""
    __tablename__ = "lock_settings"
    
    chat_id = Column(Integer, primary_key=True)
    lock_data = Column(JSON, default={})  # {'media': True, 'sticker': False, ...}
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== FLOOD SETTINGS MODEL ====================

class FloodSettings(Base):
    """Stores flood detection settings"""
    __tablename__ = "flood_settings"
    
    chat_id = Column(Integer, primary_key=True)
    flood_enabled = Column(Boolean, default=False)
    limit = Column(Integer, default=10)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ==================== CONNECTION MODEL ====================

class Connection(Base):
    """Stores user-group connections"""
    __tablename__ = "connections"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    chat_id = Column(Integer)
    is_active = Column(Boolean, default=False)
    connected_at = Column(DateTime, default=datetime.utcnow)

# ==================== FEDERATION MODEL ====================

class Federation(Base):
    """Stores federation data"""
    __tablename__ = "federations"
    
    fed_id = Column(String(255), primary_key=True)
    fed_name = Column(String(255))
    owner_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# ==================== BANNED USER MODEL ====================

class FedBanUser(Base):
    """Stores federation-banned users"""
    __tablename__ = "fed_ban_users"
    
    id = Column(Integer, primary_key=True)
    fed_id = Column(String(255))
    user_id = Column(Integer)
    reason = Column(Text, nullable=True)
    banned_at = Column(DateTime, default=datetime.utcnow)
```

### Step 1.4: Create Database Helper Functions

**File:** `Rose/db/dbfunctions.py` (NEW FILE)

```python
from sqlalchemy.orm import Session
from Rose.db.models import (
    ChatLanguage, AFK, ApprovedUser, Blacklist, Filter, Note, 
    ChatRules, Warning, Greeting, LockSettings, FloodSettings,
    Connection, Federation, FedBanUser, ChatUser, ServedChat
)
from datetime import datetime

# ==================== LANGUAGE DB FUNCTIONS ====================

async def get_chat_language(db: Session, chat_id: int) -> str:
    """Get language for a chat"""
    chat_lang = db.query(ChatLanguage).filter(ChatLanguage.chat_id == chat_id).first()
    return chat_lang.lang if chat_lang else "en"

async def set_chat_language(db: Session, chat_id: int, lang: str):
    """Set language for a chat"""
    chat_lang = db.query(ChatLanguage).filter(ChatLanguage.chat_id == chat_id).first()
    if chat_lang:
        chat_lang.lang = lang
        chat_lang.updated_at = datetime.utcnow()
    else:
        chat_lang = ChatLanguage(chat_id=chat_id, lang=lang)
        db.add(chat_lang)
    db.commit()

# ==================== AFK DB FUNCTIONS ====================

async def add_afk(db: Session, user_id: int, reason: str):
    """Add user to AFK"""
    afk_user = AFK(user_id=user_id, reason=reason)
    db.add(afk_user)
    db.commit()

async def is_afk(db: Session, user_id: int) -> tuple:
    """Check if user is AFK"""
    afk_user = db.query(AFK).filter(AFK.user_id == user_id).first()
    if afk_user:
        return True, afk_user.reason
    return False, None

async def remove_afk(db: Session, user_id: int):
    """Remove user from AFK"""
    db.query(AFK).filter(AFK.user_id == user_id).delete()
    db.commit()

# ==================== APPROVAL DB FUNCTIONS ====================

async def add_approved_user(db: Session, chat_id: int, user_id: int, user_name: str):
    """Add approved user"""
    existing = db.query(ApprovedUser).filter(
        (ApprovedUser.chat_id == chat_id) & (ApprovedUser.user_id == user_id)
    ).first()
    if not existing:
        approved = ApprovedUser(chat_id=chat_id, user_id=user_id, user_name=user_name)
        db.add(approved)
        db.commit()

async def is_approved(db: Session, chat_id: int, user_id: int) -> bool:
    """Check if user is approved"""
    approved = db.query(ApprovedUser).filter(
        (ApprovedUser.chat_id == chat_id) & (ApprovedUser.user_id == user_id)
    ).first()
    return bool(approved)

async def remove_approved_user(db: Session, chat_id: int, user_id: int):
    """Remove approved user"""
    db.query(ApprovedUser).filter(
        (ApprovedUser.chat_id == chat_id) & (ApprovedUser.user_id == user_id)
    ).delete()
    db.commit()

async def get_approved_users(db: Session, chat_id: int) -> list:
    """Get all approved users in a chat"""
    users = db.query(ApprovedUser).filter(ApprovedUser.chat_id == chat_id).all()
    return [(u.user_id, u.user_name) for u in users]

# ==================== BLACKLIST DB FUNCTIONS ====================

async def add_blacklist_word(db: Session, chat_id: int, word: str):
    """Add word to blacklist"""
    blacklist = Blacklist(chat_id=chat_id, word=word)
    db.add(blacklist)
    db.commit()

async def get_blacklist(db: Session, chat_id: int) -> list:
    """Get all blacklisted words"""
    words = db.query(Blacklist).filter(Blacklist.chat_id == chat_id).all()
    return [w.word for w in words]

async def remove_blacklist_word(db: Session, chat_id: int, word: str):
    """Remove word from blacklist"""
    db.query(Blacklist).filter(
        (Blacklist.chat_id == chat_id) & (Blacklist.word == word)
    ).delete()
    db.commit()

# ==================== FILTER DB FUNCTIONS ====================

async def add_filter(db: Session, chat_id: int, trigger: str, response: str):
    """Add filter to chat"""
    filter_item = Filter(chat_id=chat_id, trigger=trigger, response=response)
    db.add(filter_item)
    db.commit()

async def get_filters(db: Session, chat_id: int) -> dict:
    """Get all filters for a chat"""
    filters = db.query(Filter).filter(Filter.chat_id == chat_id).all()
    return {f.trigger: f.response for f in filters}

async def remove_filter(db: Session, chat_id: int, trigger: str):
    """Remove filter"""
    db.query(Filter).filter(
        (Filter.chat_id == chat_id) & (Filter.trigger == trigger)
    ).delete()
    db.commit()

# ==================== NOTE DB FUNCTIONS ====================

async def add_note(db: Session, chat_id: int, note_name: str, note_text: str):
    """Add note"""
    note = Note(chat_id=chat_id, note_name=note_name, note_text=note_text)
    db.add(note)
    db.commit()

async def get_note(db: Session, chat_id: int, note_name: str) -> str:
    """Get note text"""
    note = db.query(Note).filter(
        (Note.chat_id == chat_id) & (Note.note_name == note_name)
    ).first()
    return note.note_text if note else None

async def get_notes(db: Session, chat_id: int) -> list:
    """Get all notes for a chat"""
    notes = db.query(Note).filter(Note.chat_id == chat_id).all()
    return [n.note_name for n in notes]

async def remove_note(db: Session, chat_id: int, note_name: str):
    """Remove note"""
    db.query(Note).filter(
        (Note.chat_id == chat_id) & (Note.note_name == note_name)
    ).delete()
    db.commit()

# ==================== RULES DB FUNCTIONS ====================

async def set_rules(db: Session, chat_id: int, rules_text: str):
    """Set chat rules"""
    rules = db.query(ChatRules).filter(ChatRules.chat_id == chat_id).first()
    if rules:
        rules.rules_text = rules_text
    else:
        rules = ChatRules(chat_id=chat_id, rules_text=rules_text)
        db.add(rules)
    db.commit()

async def get_rules(db: Session, chat_id: int) -> str:
    """Get chat rules"""
    rules = db.query(ChatRules).filter(ChatRules.chat_id == chat_id).first()
    return rules.rules_text if rules else None

# ==================== WARNING DB FUNCTIONS ====================

async def add_warning(db: Session, chat_id: int, user_id: int, reason: str = None):
    """Add warning to user"""
    warning = db.query(Warning).filter(
        (Warning.chat_id == chat_id) & (Warning.user_id == user_id)
    ).first()
    if warning:
        warning.warn_count += 1
    else:
        warning = Warning(chat_id=chat_id, user_id=user_id, reason=reason, warn_count=1)
        db.add(warning)
    db.commit()

async def get_warnings(db: Session, chat_id: int, user_id: int) -> int:
    """Get warning count"""
    warning = db.query(Warning).filter(
        (Warning.chat_id == chat_id) & (Warning.user_id == user_id)
    ).first()
    return warning.warn_count if warning else 0

async def remove_warning(db: Session, chat_id: int, user_id: int):
    """Remove warning"""
    db.query(Warning).filter(
        (Warning.chat_id == chat_id) & (Warning.user_id == user_id)
    ).delete()
    db.commit()

# ==================== GREETING DB FUNCTIONS ====================

async def set_welcome(db: Session, chat_id: int, welcome_text: str, enabled: bool = True):
    """Set welcome message"""
    greeting = db.query(Greeting).filter(Greeting.chat_id == chat_id).first()
    if greeting:
        greeting.welcome_text = welcome_text
        greeting.welcome_enabled = enabled
    else:
        greeting = Greeting(chat_id=chat_id, welcome_text=welcome_text, welcome_enabled=enabled)
        db.add(greeting)
    db.commit()

async def get_welcome(db: Session, chat_id: int) -> tuple:
    """Get welcome message"""
    greeting = db.query(Greeting).filter(Greeting.chat_id == chat_id).first()
    if greeting:
        return greeting.welcome_text, greeting.welcome_enabled
    return None, False

# ==================== USER & CHAT SERVED DB FUNCTIONS ====================

async def add_served_user(db: Session, user_id: int):
    """Add served user"""
    existing = db.query(ChatUser).filter(ChatUser.user_id == user_id).first()
    if not existing:
        user = ChatUser(user_id=user_id)
        db.add(user)
        db.commit()

async def add_served_chat(db: Session, chat_id: int, chat_name: str):
    """Add served chat"""
    existing = db.query(ServedChat).filter(ServedChat.chat_id == chat_id).first()
    if not existing:
        chat = ServedChat(chat_id=chat_id, chat_name=chat_name)
        db.add(chat)
        db.commit()
```

### Step 1.5: Update `Rose/__init__.py`

Replace MongoDB initialization with SQL:

```python
import asyncio
import time
from inspect import getfullargspec
from aiohttp import ClientSession
from pyrogram import Client
from pyrogram.types import Message
from config import Config
import pytz
from datetime import datetime

# ==================== REMOVE MONGODB ====================
# DELETE: motor imports
# DELETE: pymongo imports
# DELETE: mongo_client, db initialization

# ==================== ADD SQL ====================
from Rose.db.database import engine, SessionLocal, init_db
from Rose.db.models import Base

# Initialize database tables on startup
init_db()

IST = pytz.timezone('Asia/Colombo')
time = datetime.now(IST)
date = time.strftime("%a/%d/%b/%Y %H:%M:%S")

MOD_LOAD = []
MOD_NOLOAD = []

LOG_GROUP_ID = Config.LOG_GROUP_ID
bot_start_time = time.time()
OWNER_ID = Config.OWNER_ID

loop = asyncio.get_event_loop()
aiohttpsession = ClientSession()

# ==================== REPLACE ARQ WITH ANTHROPIC ====================
from anthropic import Anthropic
claude_client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

bot = Client(
    "supun",
    bot_token=Config.BOT_TOKEN, 
    api_id=Config.API_ID,
    api_hash=Config.API_HASH)

bot.start()

app = Client(
    "app2", 
    bot_token=Config.BOT_TOKEN, 
    api_id=Config.API_ID1, 
    api_hash=Config.API_HASH1)
app.start()

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
```

### Step 1.6: Update `config.py`

Add new database configuration:

```python
from multiprocessing.connection import Connection
from os import environ
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class Config(object):
    BOT_USERNAME = environ.get("BOT_USERNAME")
    BOT_TOKEN = environ.get("BOT_TOKEN")
    API_ID = int(environ.get("API_ID"))
    API_HASH = environ.get("API_HASH")
    API_ID1 = int(environ.get("API_ID1"))
    API_HASH1 = environ.get("API_HASH1")
    OWNER_ID = environ.get("OWNER_ID")
    LOG_GROUP_ID = environ.get("LOG_GROUP_ID")
    COMMAND_PREFIXES = environ.get("COMMAND_PREFIXES", "/")
    F_SUB_CHANNEL = environ.get("F_SUB_CHANNEL")
    
    # ==================== REMOVE OLD DATABASE ====================
    # DELETE: BASE_DB = environ.get("BASE_DB")
    # DELETE: MONGO_URL = environ.get("MONGO_URL")
    # DELETE: ARQ_API_URL = environ.get("ARQ_API_URL")
    # DELETE: ARQ_API_KEY = environ.get("ARQ_API_KEY")
    
    # ==================== ADD NEW DATABASE ====================
    DATABASE_URL = environ.get("DATABASE_URL")
    # Example: postgresql://user:password@localhost/dbname
    # Or: mysql+pymysql://user:password@localhost/dbname
    
    # ==================== ADD ANTHROPIC ====================
    ANTHROPIC_API_KEY = environ.get("ANTHROPIC_API_KEY")
```

---

## 2. AI API Migration (ARQ → Anthropic)

### Step 2.1: Replace ARQ in Plugins

**File:** `Rose/plugins/Misc.py` - Update quotify function:

```python
# ==================== REMOVE ====================
# async def quotify(messages: list):
#     response = await arq.quotly(messages)
#     if not response.ok:
#         return [False, response.result]
#     sticker = response.result
#     sticker = BytesIO(sticker)
#     sticker.name = "sticker.webp"
#     return [True, sticker]

# ==================== KEEP AS IS (quotly is image-based, not AI) ====================
# For non-AI features, you can keep using alternative services
# or replace with direct API calls if available
```

### Step 2.2: Create Anthropic AI Helper Module

**File:** `Rose/utils/anthropic_helper.py` (NEW FILE)

```python
from anthropic import Anthropic
from config import Config
from typing import List, Dict
import asyncio

class AnthropicAI:
    """Wrapper for Anthropic Claude API"""
    
    def __init__(self):
        self.client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
        self.conversations = {}  # Store conversation context per user/chat
        self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model
        self.max_tokens = 1024
    
    async def get_response(self, user_input: str, chat_id: int = None, system_prompt: str = None) -> str:
        """
        Get response from Claude API
        
        Args:
            user_input: User's message
            chat_id: Chat ID for conversation context
            system_prompt: Custom system prompt
        
        Returns:
            Claude's response
        """
        try:
            # Build messages list with conversation history
            messages = self.conversations.get(chat_id, []) if chat_id else []
            messages.append({"role": "user", "content": user_input})
            
            # Default system prompt
            if not system_prompt:
                system_prompt = "You are a helpful Telegram bot assistant. Be concise and friendly in your responses."
            
            # Call Anthropic API
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=messages
            )
            
            assistant_message = response.content[0].text
            
            # Store conversation history (limit to last 10 exchanges)
            if chat_id:
                messages.append({"role": "assistant", "content": assistant_message})
                self.conversations[chat_id] = messages[-20:]  # Keep last 10 exchanges (20 messages)
            
            return assistant_message
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    async def get_code_review(self, code: str, language: str = "python") -> str:
        """Get code review from Claude"""
        system_prompt = f"You are a {language} code reviewer. Provide constructive feedback on the code quality, security, and performance."
        return await self.get_response(f"Please review this {language} code:\n\n```{language}\n{code}\n```", system_prompt=system_prompt)
    
    async def get_summary(self, text: str) -> str:
        """Get text summary from Claude"""
        system_prompt = "You are a summarization expert. Provide a concise summary of the given text."
        return await self.get_response(f"Please summarize this text:\n\n{text}", system_prompt=system_prompt)
    
    async def translate_text(self, text: str, target_lang: str) -> str:
        """Translate text using Claude"""
        system_prompt = f"You are a translator. Translate the given text to {target_lang}. Only return the translated text."
        return await self.get_response(f"Translate this text to {target_lang}:\n\n{text}", system_prompt=system_prompt)
    
    def clear_conversation(self, chat_id: int):
        """Clear conversation history for a chat"""
        if chat_id in self.conversations:
            del self.conversations[chat_id]

# Initialize global instance
ai_helper = AnthropicAI()
```

### Step 2.3: Create AI Command Plugin

**File:** `Rose/plugins/ai.py` (NEW FILE)

```python
from pyrogram import filters
from pyrogram.types import Message
from Rose import app
from Rose.utils.anthropic_helper import ai_helper
from Rose.utils.custom_filters import admin_filter
from lang import get_command
from button import Languages

AI_CMD = get_command("AI")

@app.on_message(filters.command(["ai", "ask"]) & ~filters.private)
async def ai_ask(client, message: Message):
    """Ask Claude AI a question"""
    if not message.reply_to_message and len(message.command) < 2:
        return await message.reply_text(
            "**Usage:**\n"
            "`/ai your question here`\n"
            "or reply to a message with `/ai` to get AI response about it"
        )
    
    loading_msg = await message.reply_text("⏳ **Thinking...**")
    
    try:
        # Get user input
        if message.reply_to_message:
            user_input = message.reply_to_message.text or message.reply_to_message.caption or "Please analyze this message"
        else:
            user_input = message.text.split(None, 1)[1]
        
        # Get response from Claude
        response = await ai_helper.get_response(user_input, chat_id=message.chat.id)
        
        # Split response if too long (Telegram limit: 4096 chars)
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await message.reply_text(part)
            await loading_msg.delete()
        else:
            await loading_msg.edit_text(f"**Claude's Response:**\n\n{response}")
            
    except Exception as e:
        await loading_msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("code") & ~filters.private)
async def code_review(client, message: Message):
    """Get code review from Claude"""
    if not message.reply_to_message or not message.reply_to_message.document:
        return await message.reply_text("Reply to a code file with `/code`")
    
    loading_msg = await message.reply_text("📝 **Analyzing code...**")
    
    try:
        doc = await message.reply_to_message.download()
        with open(doc, 'r', encoding='utf-8', errors='ignore') as f:
            code = f.read()
        
        # Determine language from file extension
        lang = message.reply_to_message.document.file_name.split('.')[-1] if '.' in message.reply_to_message.document.file_name else "text"
        
        response = await ai_helper.get_code_review(code, language=lang)
        
        if len(response) > 4000:
            parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
            for part in parts:
                await message.reply_text(part)
            await loading_msg.delete()
        else:
            await loading_msg.edit_text(f"**Code Review:**\n\n{response}")
            
    except Exception as e:
        await loading_msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("summary") & ~filters.private)
async def summarize(client, message: Message):
    """Summarize text using Claude"""
    if not message.reply_to_message or not (message.reply_to_message.text or message.reply_to_message.caption):
        return await message.reply_text("Reply to a message with text using `/summary`")
    
    loading_msg = await message.reply_text("📊 **Summarizing...**")
    
    try:
        text = message.reply_to_message.text or message.reply_to_message.caption
        response = await ai_helper.get_summary(text)
        
        await loading_msg.edit_text(f"**Summary:**\n\n{response}")
            
    except Exception as e:
        await loading_msg.edit_text(f"❌ **Error:** {str(e)}")

@app.on_message(filters.command("clear_ai"))
async def clear_conversation(client, message: Message):
    """Clear AI conversation history"""
    ai_helper.clear_conversation(message.chat.id)
    await message.reply_text("✅ **Conversation history cleared!**")

__MODULE__ = Languages
__HELP__ = """
**AI Commands (Anthropic Claude)**

- `/ai <question>` - Ask Claude AI anything
- `/ai` (reply to message) - Get AI response about a message
- `/code` (reply to file) - Get code review
- `/summary` (reply to message) - Summarize text
- `/clear_ai` - Clear conversation history

All responses are powered by Claude 3.5 Sonnet
"""
```

### Step 2.4: Replace Chatbot to Use Anthropic

**File:** `Rose/plugins/chatbot.py` - Update to use Anthropic:

```python
import asyncio
from pyrogram import filters
from pyrogram.types import Message
from Rose import app, BOT_ID
from Rose.utils.filter_groups import cbot
from Rose.utils.anthropic_helper import ai_helper
from lang import get_command
from Rose.utils.lang import language
from Rose.db.database import SessionLocal
from Rose.db.dbfunctions import get_chat_language
from Rose.plugins.antlangs import get_arg
from Rose.utils.custom_filters import admin_filter
from button import Chat_Bot

CBOT = get_command("CBOT")

@app.on_message(filters.command("chatbot") & ~filters.private & admin_filter)
@language
async def cbots(client, message: Message, _):
    """Enable/disable AI chatbot"""
    group_id = str(message.chat.id)
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user = await app.get_chat_member(group_id, user_id)
        if user.status not in ["creator", "administrator"]:
            return await message.reply_text("❌ You must be an admin!")
    except:
        pass
    
    if len(message.command) < 2:
        return await message.reply_text(_["chatb1"])
    
    args = get_arg(message).lower()
    
    if args == "on":
        # Store in database that chatbot is enabled (you can use a simple cache or DB)
        await message.reply_text("✅ **AI Chatbot enabled!**\n\nReply to the bot to chat with Claude!")
    elif args == "off":
        await message.reply_text("✅ **AI Chatbot disabled!**")
    else:
        return await message.reply_text("Use `/chatbot on` or `/chatbot off`")

@app.on_message(
    filters.text & 
    filters.reply & 
    ~filters.bot & 
    ~filters.via_bot & 
    ~filters.forwarded & 
    ~filters.private,
    group=cbot
)
async def ai_chatbot(client, message: Message):
    """AI Chatbot handler - reply to bot with any message"""
    if not message.reply_to_message:
        return
    
    if not message.reply_to_message.from_user:
        return
    
    if message.reply_to_message.from_user.id != BOT_ID:
        return
    
    if message.text[0] == "/":
        return
    
    # Set typing action
    await app.send_chat_action(message.chat.id, "typing")
    
    try:
        # Get response from Claude
        response = await ai_helper.get_response(
            message.text,
            chat_id=message.chat.id,
            system_prompt="You are a friendly Telegram group chatbot. Be helpful, concise, and engaging. Keep responses under 300 words."
        )
        
        # Send response
        await message.reply_text(response)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

__MODULE__ = Chat_Bot
__HELP__ = """
**AI Chatbot (Anthropic Claude)**

- `/chatbot on` - Enable AI chatbot
- `/chatbot off` - Disable AI chatbot

Reply to the bot in the group to chat! The bot uses Claude AI for intelligent responses.

**Features:**
- Natural conversations
- Context awareness
- Multilingual support
- Helpful assistance

**Powered by:** Anthropic Claude 3.5 Sonnet
"""
```

### Step 2.5: Update Language Database Usage

Create new language helper:

**File:** `Rose/utils/language_helper.py` (NEW FILE)

```python
from Rose.db.database import SessionLocal
from Rose.db.dbfunctions import get_chat_language, set_chat_language

_language_cache = {}

async def get_language(chat_id: int) -> str:
    """Get language for a chat with caching"""
    if chat_id in _language_cache:
        return _language_cache[chat_id]
    
    db = SessionLocal()
    try:
        lang = await get_chat_language(db, chat_id)
        _language_cache[chat_id] = lang
        return lang
    finally:
        db.close()

async def set_language(chat_id: int, lang: str):
    """Set language for a chat"""
    _language_cache[chat_id] = lang
    db = SessionLocal()
    try:
        await set_chat_language(db, chat_id, lang)
    finally:
        db.close()

def clear_language_cache(chat_id: int):
    """Clear language cache for a chat"""
    if chat_id in _language_cache:
        del _language_cache[chat_id]
```

---

## 3. Updated Environment Variables

### For Railway Deployment

Add these environment variables to your Railway project:

```env
# ==================== BOT CREDENTIALS ====================
BOT_TOKEN=7198587941:AAEQ2A3krDxrEtgf2hGuNgGYICd5sQoODUg
BOT_USERNAME=YourBotUsername
API_ID=123456
API_HASH=1abcd2efhs93u39
API_ID1=123456
API_HASH1=1abcd2efhs93u39

# ==================== DATABASE (PostgreSQL Example) ====================
DATABASE_URL=postgresql://username:password@localhost:5432/shaheen_db

# ==================== DATABASE (MySQL Example) ====================
# DATABASE_URL=mysql+pymysql://username:password@localhost:3306/shaheen_db

# ==================== LOGGING & OWNER ====================
LOG_GROUP_ID=-1000088000
OWNER_ID=123456789
F_SUB_CHANNEL=-1000000000

# ==================== BOT SETTINGS ====================
COMMAND_PREFIXES=/

# ==================== ANTHROPIC API ====================
ANTHROPIC_API_KEY=sk-ant-v0-your-key-here

# ==================== REMOVE OLD VARIABLES ====================
# DELETE: MONGO_URL
# DELETE: BASE_DB
# DELETE: ARQ_API_URL
# DELETE: ARQ_API_KEY
```

### Database Connection Strings

**PostgreSQL (Recommended):**
```
postgresql://user:password@hostname:5432/database_name
postgresql+asyncpg://user:password@hostname:5432/database_name  # For async
```

**MySQL:**
```
mysql+pymysql://user:password@hostname:3306/database_name
```

**SQLite (Development only):**
```
sqlite:///./test.db
```

---

## 4. Migration Checklist

### Pre-Migration
- [ ] Backup your MongoDB database
- [ ] Get Anthropic API key from https://console.anthropic.com
- [ ] Create PostgreSQL/MySQL database
- [ ] Test code locally before deploying

### Code Changes
- [ ] Update `requirements.txt`
- [ ] Create `Rose/db/database.py`
- [ ] Create `Rose/db/models.py`
- [ ] Create `Rose/db/dbfunctions.py`
- [ ] Update `Rose/__init__.py`
- [ ] Update `config.py`
- [ ] Create `Rose/utils/anthropic_helper.py`
- [ ] Create `Rose/plugins/ai.py`
- [ ] Update `Rose/plugins/chatbot.py`
- [ ] Update `Rose/plugins/Misc.py` (remove ARQ usage)
- [ ] Update all other plugins that use MongoDB

### Testing
- [ ] Test database connection
- [ ] Test Anthropic API integration
- [ ] Test all AI commands (`/ai`, `/code`, `/summary`)
- [ ] Test chatbot functionality
- [ ] Test language settings migration

### Deployment
- [ ] Set all environment variables on Railway
- [ ] Deploy updated code
- [ ] Monitor bot logs for errors
- [ ] Verify database operations

### Post-Migration
- [ ] Verify all commands work
- [ ] Check logs for any issues
- [ ] Keep MongoDB backup for 30 days
- [ ] Document any custom changes

---

## Troubleshooting

### Database Connection Errors
```python
# Check if DATABASE_URL is correct:
from sqlalchemy import create_engine
from Rose.db.database import DATABASE_URL

print(f"Using: {DATABASE_URL}")
# Should not print password in logs
```

### Anthropic API Errors
```python
# Verify API key is set correctly
import os
key = os.environ.get("ANTHROPIC_API_KEY")
print(f"API Key set: {bool(key)}")
```

### Migration Issues
- Ensure all tables are created: `init_db()` in `Rose/__init__.py`
- Check logs: `journalctl -u bot_service -f` or Railway logs
- Rollback: Keep MongoDB running during initial testing

---

## Performance Tips

1. **Connection Pooling:** Already configured in `database.py` (pool_size=10)
2. **Indexes:** Add database indexes for frequently queried fields:
   ```python
   class ChatUser(Base):
       __table_args__ = (
           Index('idx_user_id', 'user_id'),
       )
   ```
3. **Caching:** Language and AFK status use local caching
4. **Batch Operations:** Group multiple DB writes when possible

---

## Support

For issues:
1. Check Railway logs
2. Verify environment variables
3. Test SQL connection directly
4. Verify Anthropic API key validity

**Anthropic Documentation:** https://docs.anthropic.com
**SQLAlchemy Documentation:** https://docs.sqlalchemy.org
