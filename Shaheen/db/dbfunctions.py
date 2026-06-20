from sqlalchemy.orm import Session
from Shaheen.db.models import (
    ChatLanguage, AFK, ApprovedUser, Blacklist, Filter, Note, 
    ChatRules, Warning, Greeting, LockSettings, FloodSettings,
    Connection, Federation, FedBanUser, ChatUser, ServedChat, ChatbotSettings
)
from datetime import datetime

# ==================== LANGUAGE DB FUNCTIONS ====================

async def get_chat_language(db: Session, chat_id: int) -> str:
    """Get language for a chat"""
    try:
        chat_lang = db.query(ChatLanguage).filter(ChatLanguage.chat_id == chat_id).first()
        return chat_lang.lang if chat_lang else "en"
    except:
        return "en"

async def set_chat_language(db: Session, chat_id: int, lang: str):
    """Set language for a chat"""
    try:
        chat_lang = db.query(ChatLanguage).filter(ChatLanguage.chat_id == chat_id).first()
        if chat_lang:
            chat_lang.lang = lang
            chat_lang.updated_at = datetime.utcnow()
        else:
            chat_lang = ChatLanguage(chat_id=chat_id, lang=lang)
            db.add(chat_lang)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error setting language: {e}")

# ==================== AFK DB FUNCTIONS ====================

async def add_afk(db: Session, user_id: int, reason: str):
    """Add user to AFK"""
    try:
        db.query(AFK).filter(AFK.user_id == user_id).delete()
        afk_user = AFK(user_id=user_id, reason=reason)
        db.add(afk_user)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding AFK: {e}")

async def is_afk(db: Session, user_id: int) -> tuple:
    """Check if user is AFK"""
    try:
        afk_user = db.query(AFK).filter(AFK.user_id == user_id).first()
        if afk_user:
            return True, afk_user.reason
        return False, None
    except:
        return False, None

async def remove_afk(db: Session, user_id: int):
    """Remove user from AFK"""
    try:
        db.query(AFK).filter(AFK.user_id == user_id).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error removing AFK: {e}")

async def get_afk_users(db: Session) -> list:
    """Get all AFK users"""
    try:
        users = db.query(AFK).all()
        return users
    except:
        return []

# ==================== APPROVAL DB FUNCTIONS ====================

async def add_approved_user(db: Session, chat_id: int, user_id: int, user_name: str):
    """Add approved user"""
    try:
        existing = db.query(ApprovedUser).filter(
            (ApprovedUser.chat_id == chat_id) & (ApprovedUser.user_id == user_id)
        ).first()
        if not existing:
            approved = ApprovedUser(chat_id=chat_id, user_id=user_id, user_name=user_name)
            db.add(approved)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding approved user: {e}")

async def is_approved(db: Session, chat_id: int, user_id: int) -> bool:
    """Check if user is approved"""
    try:
        approved = db.query(ApprovedUser).filter(
            (ApprovedUser.chat_id == chat_id) & (ApprovedUser.user_id == user_id)
        ).first()
        return bool(approved)
    except:
        return False

async def remove_approved_user(db: Session, chat_id: int, user_id: int):
    """Remove approved user"""
    try:
        db.query(ApprovedUser).filter(
            (ApprovedUser.chat_id == chat_id) & (ApprovedUser.user_id == user_id)
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error removing approved user: {e}")

async def get_approved_users(db: Session, chat_id: int) -> list:
    """Get all approved users in a chat"""
    try:
        users = db.query(ApprovedUser).filter(ApprovedUser.chat_id == chat_id).all()
        return [(u.user_id, u.user_name) for u in users]
    except:
        return []

# ==================== BLACKLIST DB FUNCTIONS ====================

async def add_blacklist_word(db: Session, chat_id: int, word: str):
    """Add word to blacklist"""
    try:
        existing = db.query(Blacklist).filter(
            (Blacklist.chat_id == chat_id) & (Blacklist.word == word)
        ).first()
        if not existing:
            blacklist = Blacklist(chat_id=chat_id, word=word)
            db.add(blacklist)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding blacklist: {e}")

async def get_blacklist(db: Session, chat_id: int) -> list:
    """Get all blacklisted words"""
    try:
        words = db.query(Blacklist).filter(Blacklist.chat_id == chat_id).all()
        return [w.word for w in words]
    except:
        return []

async def remove_blacklist_word(db: Session, chat_id: int, word: str):
    """Remove word from blacklist"""
    try:
        db.query(Blacklist).filter(
            (Blacklist.chat_id == chat_id) & (Blacklist.word == word)
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error removing blacklist: {e}")

# ==================== FILTER DB FUNCTIONS ====================

async def add_filter(db: Session, chat_id: int, trigger: str, response: str):
    """Add filter to chat"""
    try:
        existing = db.query(Filter).filter(
            (Filter.chat_id == chat_id) & (Filter.trigger == trigger)
        ).first()
        if existing:
            existing.response = response
        else:
            filter_item = Filter(chat_id=chat_id, trigger=trigger, response=response)
            db.add(filter_item)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding filter: {e}")

async def get_filters(db: Session, chat_id: int) -> dict:
    """Get all filters for a chat"""
    try:
        filters = db.query(Filter).filter(Filter.chat_id == chat_id).all()
        return {f.trigger: f.response for f in filters}
    except:
        return {}

async def remove_filter(db: Session, chat_id: int, trigger: str):
    """Remove filter"""
    try:
        db.query(Filter).filter(
            (Filter.chat_id == chat_id) & (Filter.trigger == trigger)
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error removing filter: {e}")

# ==================== NOTE DB FUNCTIONS ====================

async def add_note(db: Session, chat_id: int, note_name: str, note_text: str):
    """Add note"""
    try:
        existing = db.query(Note).filter(
            (Note.chat_id == chat_id) & (Note.note_name == note_name)
        ).first()
        if existing:
            existing.note_text = note_text
        else:
            note = Note(chat_id=chat_id, note_name=note_name, note_text=note_text)
            db.add(note)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding note: {e}")

async def get_note(db: Session, chat_id: int, note_name: str) -> str:
    """Get note text"""
    try:
        note = db.query(Note).filter(
            (Note.chat_id == chat_id) & (Note.note_name == note_name)
        ).first()
        return note.note_text if note else None
    except:
        return None

async def get_notes(db: Session, chat_id: int) -> list:
    """Get all notes for a chat"""
    try:
        notes = db.query(Note).filter(Note.chat_id == chat_id).all()
        return [n.note_name for n in notes]
    except:
        return []

async def remove_note(db: Session, chat_id: int, note_name: str):
    """Remove note"""
    try:
        db.query(Note).filter(
            (Note.chat_id == chat_id) & (Note.note_name == note_name)
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error removing note: {e}")

# ==================== RULES DB FUNCTIONS ====================

async def set_rules(db: Session, chat_id: int, rules_text: str):
    """Set chat rules"""
    try:
        rules = db.query(ChatRules).filter(ChatRules.chat_id == chat_id).first()
        if rules:
            rules.rules_text = rules_text
        else:
            rules = ChatRules(chat_id=chat_id, rules_text=rules_text)
            db.add(rules)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error setting rules: {e}")

async def get_rules(db: Session, chat_id: int) -> str:
    """Get chat rules"""
    try:
        rules = db.query(ChatRules).filter(ChatRules.chat_id == chat_id).first()
        return rules.rules_text if rules else None
    except:
        return None

# ==================== WARNING DB FUNCTIONS ====================

async def add_warning(db: Session, chat_id: int, user_id: int, reason: str = None):
    """Add warning to user"""
    try:
        warning = db.query(Warning).filter(
            (Warning.chat_id == chat_id) & (Warning.user_id == user_id)
        ).first()
        if warning:
            warning.warn_count += 1
        else:
            warning = Warning(chat_id=chat_id, user_id=user_id, reason=reason, warn_count=1)
            db.add(warning)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding warning: {e}")

async def get_warnings(db: Session, chat_id: int, user_id: int) -> int:
    """Get warning count"""
    try:
        warning = db.query(Warning).filter(
            (Warning.chat_id == chat_id) & (Warning.user_id == user_id)
        ).first()
        return warning.warn_count if warning else 0
    except:
        return 0

async def remove_warning(db: Session, chat_id: int, user_id: int):
    """Remove warning"""
    try:
        db.query(Warning).filter(
            (Warning.chat_id == chat_id) & (Warning.user_id == user_id)
        ).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error removing warning: {e}")

# ==================== GREETING DB FUNCTIONS ====================

async def set_welcome(db: Session, chat_id: int, welcome_text: str, enabled: bool = True):
    """Set welcome message"""
    try:
        greeting = db.query(Greeting).filter(Greeting.chat_id == chat_id).first()
        if greeting:
            greeting.welcome_text = welcome_text
            greeting.welcome_enabled = enabled
        else:
            greeting = Greeting(chat_id=chat_id, welcome_text=welcome_text, welcome_enabled=enabled)
            db.add(greeting)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error setting welcome: {e}")

async def get_welcome(db: Session, chat_id: int) -> tuple:
    """Get welcome message"""
    try:
        greeting = db.query(Greeting).filter(Greeting.chat_id == chat_id).first()
        if greeting:
            return greeting.welcome_text, greeting.welcome_enabled
        return None, False
    except:
        return None, False

# ==================== USER & CHAT SERVED DB FUNCTIONS ====================

async def add_served_user(db: Session, user_id: int):
    """Add served user"""
    try:
        existing = db.query(ChatUser).filter(ChatUser.user_id == user_id).first()
        if not existing:
            user = ChatUser(user_id=user_id)
            db.add(user)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding served user: {e}")

async def add_served_chat(db: Session, chat_id: int, chat_name: str = None):
    """Add served chat"""
    try:
        existing = db.query(ServedChat).filter(ServedChat.chat_id == chat_id).first()
        if not existing:
            chat = ServedChat(chat_id=chat_id, chat_name=chat_name)
            db.add(chat)
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error adding served chat: {e}")

# ==================== CHATBOT SETTINGS DB FUNCTIONS ====================

async def enable_chatbot(db: Session, chat_id: int):
    """Enable chatbot for a chat"""
    try:
        settings = db.query(ChatbotSettings).filter(ChatbotSettings.chat_id == chat_id).first()
        if settings:
            settings.enabled = True
        else:
            settings = ChatbotSettings(chat_id=chat_id, enabled=True)
            db.add(settings)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error enabling chatbot: {e}")

async def disable_chatbot(db: Session, chat_id: int):
    """Disable chatbot for a chat"""
    try:
        settings = db.query(ChatbotSettings).filter(ChatbotSettings.chat_id == chat_id).first()
        if settings:
            settings.enabled = False
            db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error disabling chatbot: {e}")

async def is_chatbot_enabled(db: Session, chat_id: int) -> bool:
    """Check if chatbot is enabled"""
    try:
        settings = db.query(ChatbotSettings).filter(ChatbotSettings.chat_id == chat_id).first()
        return settings.enabled if settings else False
    except:
        return False
