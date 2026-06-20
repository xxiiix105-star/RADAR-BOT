from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, UniqueConstraint, Index
from sqlalchemy.sql import func
from Shaheen.db.database import Base
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
    
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
    )

class ServedChat(Base):
    """Stores bot served chats"""
    __tablename__ = "served_chats"
    
    chat_id = Column(Integer, primary_key=True)
    chat_name = Column(String(255), nullable=True)
    members_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_chat_id', 'chat_id'),
    )

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
    
    __table_args__ = (
        UniqueConstraint('chat_id', 'user_id', name='uq_chat_user'),
        Index('idx_chat_user', 'chat_id', 'user_id'),
    )

# ==================== BLACKLIST MODEL ====================

class Blacklist(Base):
    """Stores blacklisted words"""
    __tablename__ = "blacklists"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    word = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_chat_word', 'chat_id', 'word'),
    )

# ==================== FILTER MODEL ====================

class Filter(Base):
    """Stores chat filters"""
    __tablename__ = "filters"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    trigger = Column(String(255))
    response = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_chat_trigger', 'chat_id', 'trigger'),
    )

# ==================== NOTE MODEL ====================

class Note(Base):
    """Stores notes"""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    note_name = Column(String(255))
    note_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_chat_note', 'chat_id', 'note_name'),
    )

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
    
    __table_args__ = (
        Index('idx_chat_user_warn', 'chat_id', 'user_id'),
    )

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
    
    __table_args__ = (
        Index('idx_user_chat_conn', 'user_id', 'chat_id'),
    )

# ==================== FEDERATION MODEL ====================

class Federation(Base):
    """Stores federation data"""
    __tablename__ = "federations"
    
    fed_id = Column(String(255), primary_key=True)
    fed_name = Column(String(255))
    owner_id = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_owner_fed', 'owner_id'),
    )

# ==================== BANNED USER MODEL ====================

class FedBanUser(Base):
    """Stores federation-banned users"""
    __tablename__ = "fed_ban_users"
    
    id = Column(Integer, primary_key=True)
    fed_id = Column(String(255))
    user_id = Column(Integer)
    reason = Column(Text, nullable=True)
    banned_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_fed_user_ban', 'fed_id', 'user_id'),
    )

# ==================== CHATBOT SETTINGS MODEL ====================

class ChatbotSettings(Base):
    """Stores per-chat chatbot settings"""
    __tablename__ = "chatbot_settings"
    
    chat_id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=False)
    system_prompt = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
