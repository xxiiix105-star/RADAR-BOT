from multiprocessing.connection import Connection
from os import environ
from pyrogram.types import InlineKeyboardButton,InlineKeyboardMarkup


class Config(object):
        #Your telegram BOT username(without @) : get it from @BotFather
        BOT_USERNAME = environ.get("BOT_USERNAME")
        #Your telegram BOT API token : get it from @BotFather
        BOT_TOKEN = environ.get("BOT_TOKEN")
        #API_ID of your Telegram Account my.telegram.org/apps
        API_ID = int(environ.get("API_ID", 0))
        #API_HASH of your Telegram Account my.telegram.org/apps
        API_HASH = environ.get("API_HASH")
        #API_ID of your Telegram Account my.telegram.org/apps
        API_ID1 = int(environ.get("API_ID1", environ.get("API_ID", 0)))
        #API_HASH of your Telegram Account my.telegram.org/apps
        API_HASH1 = environ.get("API_HASH1", environ.get("API_HASH"))
        #Your telegram user id
        OWNER_ID = environ.get("OWNER_ID")
        #For logs channel to note down important bot level events, recommend to make this public. ex: '-123456'
        LOG_GROUP_ID = environ.get("LOG_GROUP_ID")
        #Get From Here.https://www.mongodb.com/ (Same as MONGO_URL but give differant value for this)
        BASE_DB = environ.get("BASE_DB", "")
        #Get From Here.https://www.mongodb.com/
        MONGO_URL = environ.get("MONGO_URL", "")
        #Don't change this value:https://arq.hamker.in
        ARQ_API_URL = environ.get("ARQ_API_URL")
        #Get this from @ARQRobot.
        ARQ_API_KEY = environ.get("ARQ_API_KEY")
        #now you can set custom command handler like : / ! ,
        COMMAND_PREFIXES = environ.get("COMMAND_PREFIXES")
        #The Telegram channel id you want focus user.(User can't start your bot without join it)
        F_SUB_CHANNEL = environ.get("F_SUB_CHANNEL")
        #PostgreSQL Database URL
        DATABASE_URL = environ.get("DATABASE_URL")
        #Anthropic API Key for AI features
        ANTHROPIC_API_KEY = environ.get("ANTHROPIC_API_KEY")

class var(object):
        #Shaheen group start message here 
        group_start_text = "🇵🇸 Shaheen is here to protect your group. Use /help to see all commands."
        #Shaheen help menu text message here 
        help_text = """
🇵🇸 **Shaheen — Help Menu**

Welcome! I am **Shaheen**, your powerful group management assistant.

Use the buttons below to explore my features, or type a command directly.

**All commands can be used with the following prefix: /**"""
        #Shaheen start menu connections (split commands on start)
        Connection_text_start = "🇵🇸 **Run /connections to view or disconnect from groups!**"
        #Shaheen private start message here
        pm_start_text = """
🇵🇸 **Hello {}, I am {}!**

I am a powerful group management bot built to keep your community safe and organised.

Use the buttons below to get started, or add me to your group and let me do the work!"""
        #Languages change text menu here 
        lang_text = "🇵🇸 Choose your language:"

        #Languages change button menu here — all decorative flags updated to 🇵🇸
        lang_keyboard = InlineKeyboardMarkup(
                [
                        [
                                InlineKeyboardButton(text="🇵🇸 English", callback_data="languages_en")
                        ],
                        [
                                InlineKeyboardButton(text="🇵🇸 සිංහල", callback_data="languages_si"), 
                                InlineKeyboardButton(text="🇵🇸 हिन्दी", callback_data="languages_hi")
                        ], 
                        [
                                InlineKeyboardButton(text="🇵🇸 Italiano", callback_data="languages_it"), 
                                InlineKeyboardButton(text="🇵🇸 తెలుగు", callback_data="languages_ta")
                        ], 
                        [
                                InlineKeyboardButton(text="🇵🇸 Indonesia", callback_data="languages_id"), 
                                InlineKeyboardButton(text="🇵🇸 عربي", callback_data="languages_ar")
                        ], 
                        [
                                InlineKeyboardButton(text="🇵🇸 മലയാളം", callback_data="languages_ml"), 
                                InlineKeyboardButton(text="🇵🇸 Chichewa", callback_data="languages_ny")
                        ], 
                        [
                                InlineKeyboardButton(text="🇵🇸 German", callback_data="languages_ge"), 
                                InlineKeyboardButton(text="🇵🇸 Russian", callback_data="languages_ru")
                        ], 
                        [
                                InlineKeyboardButton("« Back", callback_data='startcq')
                        ]
                ]
)
        #Shaheen informations button menu here
        about_buttons = InlineKeyboardMarkup(
                [
                        [
                                InlineKeyboardButton(text="🇵🇸 Support Group", url="https://t.me/szrosesupport"),
                                InlineKeyboardButton(text="🇵🇸 News Channel", url="https://t.me/Theszrosebot")
                        ], 
                        [ 
                                InlineKeyboardButton(text="⚒ Source Code", url="https://github.com/yousef94s/Shaheen-saved-me"),
                                InlineKeyboardButton(text="📓 Documentation", url="https://github.com/yousef94s/Shaheen-saved-me")
                        ], 
                        [
                                InlineKeyboardButton(text="🖥 How To Deploy", url="https://github.com/yousef94s/Shaheen-saved-me")
                        ],
                        [
                                InlineKeyboardButton("« Back", callback_data='startcq')
                        ]
                ]
)
        #Shaheen private start button menu here
        home_keyboard_pm = InlineKeyboardMarkup(
                [
                        [
                                InlineKeyboardButton(text="🇵🇸 Add Me To Your Group",url=f"http://t.me/{Config.BOT_USERNAME}?startgroup=new")
                        ],
                        [
                                InlineKeyboardButton(text="About ✨",callback_data="_about"),
                                InlineKeyboardButton(text="🇵🇸 Languages",callback_data="_langs")
                        ],
                        [
                                InlineKeyboardButton(text="Help Menu ⚒",callback_data="bot_commands")
                        ],
                        [
                                InlineKeyboardButton(text="🇵🇸 News Channel 📢",url=f"https://t.me/szroseupdates")
                        ]
                ]
)
