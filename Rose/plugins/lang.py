from lang import get_string
from Rose.mongo.language import set_lang, get_lang
from Rose import app, LOG_GROUP_ID
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Rose.utils.lang import language
from button import Languages

# Static language-picker keyboard shown by /lang command
LANG_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="🇬🇧 English",   callback_data="languages_en")],
        [
            InlineKeyboardButton(text="🇱🇰 සිංහල",   callback_data="languages_si"),
            InlineKeyboardButton(text="🇮🇳 हिन्दी",   callback_data="languages_hi"),
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Italiano", callback_data="languages_it"),
            InlineKeyboardButton(text="🇮🇳 తెలుగు",   callback_data="languages_ta"),
        ],
        [
            InlineKeyboardButton(text="🇮🇩 Indonesia",callback_data="languages_id"),
            InlineKeyboardButton(text="🇸🇦 عربي",     callback_data="languages_ar"),
        ],
        [
            InlineKeyboardButton(text="🇮🇳 മലയാളം",  callback_data="languages_ml"),
            InlineKeyboardButton(text="🇲🇼 Chichewa", callback_data="languages_ny"),
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch",  callback_data="languages_ge"),
            InlineKeyboardButton(text="🇷🇺 Русский",  callback_data="languages_ru"),
        ],
    ]
)

# Ordered list of (module_key, translation_dict_key) pairs that map
# each help module to its btn_* key in the language YAML files.
MODULE_BTN_KEYS = [
    ("admin",       "btn_admin"),
    ("locks",       "btn_locks"),
    ("captcha",     "btn_captcha"),
    ("greetings",   "btn_greetings"),
    ("filters",     "btn_filters"),
    ("blacklists",  "btn_blacklists"),
    ("notes",       "btn_notes"),
    ("warnings",    "btn_warnings"),
    ("rules",       "btn_rules"),
    ("connections", "btn_connections"),
    ("pin",         "btn_pin"),
    ("purge",       "btn_purge"),
    ("protection",  "btn_protection"),
    ("languages",   "btn_languages"),
    ("approval",    "btn_approval"),
    ("restrict",    "btn_restrict"),
    ("n-mode",      "btn_nightmode"),
    ("chat-bot",    "btn_chatbot"),
    ("formatting",  "btn_formatting"),
    ("federations", "btn_federations"),
    ("reports",     "btn_reports"),
    ("tagalert",    "btn_tagalert"),
    ("sticker",     "btn_sticker"),
]

# English fallbacks for every module button (mirrors button.py labels)
BTN_FALLBACKS = {
    "btn_admin":       "Admin",
    "btn_locks":       "Locks",
    "btn_captcha":     "Captcha",
    "btn_greetings":   "Greetings",
    "btn_filters":     "Filters",
    "btn_blacklists":  "Blacklists",
    "btn_notes":       "Notes",
    "btn_warnings":    "Warnings",
    "btn_rules":       "Rules",
    "btn_connections": "Connections",
    "btn_pin":         "Pin",
    "btn_purge":       "Purge",
    "btn_protection":  "Protection",
    "btn_languages":   "Languages",
    "btn_approval":    "Approval",
    "btn_restrict":    "Restrict",
    "btn_nightmode":   "N-Mode",
    "btn_chatbot":     "Chat-Bot",
    "btn_formatting":  "Formatting",
    "btn_federations": "Federations",
    "btn_reports":     "Reports",
    "btn_tagalert":    "Tagalert",
    "btn_sticker":     "Sticker",
}


def build_translated_help_keyboard(_, helpable: dict) -> InlineKeyboardMarkup:
    """
    Dynamically build the help-module keyboard using labels from the
    selected language's translation dictionary.

    Only modules present in *helpable* (populated at runtime) are shown.
    Two buttons per row, with a localised Back button at the bottom.
    """
    buttons = []
    row = []
    for module_key, btn_key in MODULE_BTN_KEYS:
        if module_key not in helpable:
            continue
        label = _.get(btn_key, BTN_FALLBACKS.get(btn_key, module_key.title()))
        row.append(
            InlineKeyboardButton(
                text=label,
                callback_data=f"help_module({module_key})",
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    back_label = _.get("back", "« Back")
    buttons.append([InlineKeyboardButton(text=back_label, callback_data="startcq")])
    return InlineKeyboardMarkup(buttons)


@app.on_message(filters.command("lang"))
@language
async def langs_command(client, message: Message, _):
    userid = message.from_user.id if message.from_user else None
    chat_type = message.chat.type
    header = _["setting_1"].format(message.from_user.first_name)
    if chat_type == "private":
        await message.reply_text(header, reply_markup=LANG_KEYBOARD)
    elif chat_type in ["group", "supergroup"]:
        group_id = message.chat.id
        st = await app.get_chat_member(group_id, userid)
        if st.status not in ("administrator", "creator"):
            return
        try:
            await message.reply_text(header, reply_markup=LANG_KEYBOARD)
        except Exception as e:
            return await app.send_message(LOG_GROUP_ID, text=str(e))


@app.on_callback_query(filters.regex(r"^languages_"))
async def language_markup(client, CallbackQuery):
    selected_lang = CallbackQuery.data.split("_")[1]
    chat_id = CallbackQuery.message.chat.id

    old = await get_lang(chat_id)

    if str(old) == str(selected_lang):
        return await CallbackQuery.answer(
            "⛔️ You're already using this language.", show_alert=False
        )

    # Answer the callback immediately to prevent FloodWait / timeout
    await CallbackQuery.answer("✅ Language changed successfully!", show_alert=False)

    # Validate that the language exists in our translation files
    try:
        _ = get_string(selected_lang)
    except (KeyError, Exception):
        return await CallbackQuery.answer(
            "⚠️ This language is under construction.", show_alert=True
        )

    # Persist the selection to PostgreSQL so it survives restarts
    await set_lang(chat_id, selected_lang)

    # Lazy-import HELPABLE (populated after all plugins are loaded)
    try:
        import Rose.__main__ as _main
        helpable = _main.HELPABLE
    except Exception:
        helpable = {}

    # Build fully-translated header and keyboard in one edit call
    header = _["setting_2"].format(CallbackQuery.from_user.mention)
    keyboard = build_translated_help_keyboard(_, helpable)

    await CallbackQuery.message.edit(
        text=header,
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


__MODULE__ = f"{Languages}"
__HELP__ = """
Not every group speaks fluent english; some groups would rather have Shaheen respond in their own language.

This is where translations come in; you can change the language of most replies to be in the language of your choice!

**Admin commands:**
- /lang : Set your preferred language.
"""
__helpbtns__ = (
    [
        [InlineKeyboardButton(text="🇬🇧 English",   callback_data="languages_en")],
        [
            InlineKeyboardButton(text="🇱🇰 සිංහල",   callback_data="languages_si"),
            InlineKeyboardButton(text="🇮🇳 हिन्दी",   callback_data="languages_hi"),
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Italiano", callback_data="languages_it"),
            InlineKeyboardButton(text="🇮🇳 తెలుగు",   callback_data="languages_ta"),
        ],
        [
            InlineKeyboardButton(text="🇮🇩 Indonesia",callback_data="languages_id"),
            InlineKeyboardButton(text="🇸🇦 عربي",     callback_data="languages_ar"),
        ],
        [
            InlineKeyboardButton(text="🇮🇳 മലയാളം",  callback_data="languages_ml"),
            InlineKeyboardButton(text="🇲🇼 Chichewa", callback_data="languages_ny"),
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch",  callback_data="languages_ge"),
            InlineKeyboardButton(text="🇷🇺 Русский",  callback_data="languages_ru"),
        ],
    ]
)
