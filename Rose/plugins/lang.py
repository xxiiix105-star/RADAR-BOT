import logging
from lang import get_string
from Rose.mongo.language import set_lang, get_lang
from Rose import app, LOG_GROUP_ID, HELPABLE
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from Rose.utils.lang import language
from button import Languages

log = logging.getLogger(__name__)

# ── Language-picker keyboard (static — shown by /lang with no argument) ───────
LANG_KEYBOARD = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text="🇬🇧 English",    callback_data="languages_en")],
        [
            InlineKeyboardButton(text="🇱🇰 සිංහල",    callback_data="languages_si"),
            InlineKeyboardButton(text="🇮🇳 हिन्दी",    callback_data="languages_hi"),
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Italiano",  callback_data="languages_it"),
            InlineKeyboardButton(text="🇮🇳 తెలుగు",    callback_data="languages_ta"),
        ],
        [
            InlineKeyboardButton(text="🇮🇩 Indonesia", callback_data="languages_id"),
            InlineKeyboardButton(text="🇸🇦 عربي",      callback_data="languages_ar"),
        ],
        [
            InlineKeyboardButton(text="🇮🇳 മലയാളം",   callback_data="languages_ml"),
            InlineKeyboardButton(text="🇲🇼 Chichewa",  callback_data="languages_ny"),
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch",   callback_data="languages_ge"),
            InlineKeyboardButton(text="🇷🇺 Русский",   callback_data="languages_ru"),
        ],
    ]
)

# Human-readable names for every supported language code.
LANG_NAMES = {
    "en": "🇬🇧 English",
    "si": "🇱🇰 සිංහල",
    "hi": "🇮🇳 हिन्दी",
    "it": "🇮🇹 Italiano",
    "ta": "🇮🇳 తెలుగు",
    "id": "🇮🇩 Indonesia",
    "ar": "🇸🇦 عربي",
    "ml": "🇮🇳 മലയാളം",
    "ny": "🇲🇼 Chichewa",
    "ge": "🇩🇪 Deutsch",
}

# ── Module-button mapping: (helpable_key, btn_*_yaml_key) ─────────────────────
# helpable_key  = module.__MODULE__.replace(" ", "_").lower()
# btn_*_yaml_key = key that exists in every lang/langs/<code>.yml under btn_*
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
    # Previously missing — these modules have __HELP__ so they land in HELPABLE
    ("afk",         "btn_afk"),
    ("f-sub",       "btn_fsub"),
    ("disabling",   "btn_disabling"),
    ("whisper",     "btn_whisper"),
    ("developer",   "btn_developer"),
]

# English fallbacks — used when a language file is missing a btn_* key.
BTN_FALLBACKS = {
    "btn_admin":       "👮 Admin",
    "btn_locks":       "🔒 Locks",
    "btn_captcha":     "🤖 Captcha",
    "btn_greetings":   "👋 Greetings",
    "btn_filters":     "🔍 Filters",
    "btn_blacklists":  "🚫 Blacklists",
    "btn_notes":       "📝 Notes",
    "btn_warnings":    "⚠️ Warnings",
    "btn_rules":       "📜 Rules",
    "btn_connections": "🔗 Connections",
    "btn_pin":         "📌 Pin",
    "btn_purge":       "🗑 Purge",
    "btn_protection":  "🛡 Protection",
    "btn_languages":   "🌐 Languages",
    "btn_approval":    "✅ Approval",
    "btn_restrict":    "🔇 Restrict",
    "btn_nightmode":   "🌙 N-Mode",
    "btn_chatbot":     "💬 Chat-Bot",
    "btn_formatting":  "✏️ Formatting",
    "btn_federations": "🌍 Federations",
    "btn_reports":     "📢 Reports",
    "btn_tagalert":    "🔔 Tagalert",
    "btn_sticker":     "🎭 Sticker",
    "btn_afk":         "💤 AFK",
    "btn_fsub":        "📢 F-Sub",
    "btn_disabling":   "🚫 Disabling",
    "btn_whisper":     "🤫 Whisper",
    "btn_developer":   "👨‍💻 Developer",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def build_translated_help_keyboard(_, helpable: dict) -> InlineKeyboardMarkup:
    """
    Build the help-module keyboard entirely from the live translation dict.
    Called fresh on every callback — never serves cached / stale labels.
    Two buttons per row; localised Back button at the bottom.

    `_`        — translation dict for the active language (from get_string)
    `helpable` — the shared HELPABLE registry from Rose/__init__.py
    """
    log.debug(
        "build_translated_help_keyboard: helpable has %d entries: %s",
        len(helpable), list(helpable.keys()),
    )

    buttons: list = []
    row: list = []

    for module_key, btn_key in MODULE_BTN_KEYS:
        if module_key not in helpable:
            log.debug("  skip '%s' — not in HELPABLE", module_key)
            continue
        label = _.get(btn_key) or BTN_FALLBACKS.get(btn_key, module_key.title())
        log.debug("  button '%s' → label '%s'", module_key, label)
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

    back_label = _.get("back") or "« Back"
    buttons.append([InlineKeyboardButton(text=back_label, callback_data="startcq")])
    return InlineKeyboardMarkup(buttons)


async def _is_admin(chat_id: int, user_id: int) -> bool:
    """Return True if user is admin or creator in the given chat."""
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def _apply_language(chat_id: int, selected: str, actor_mention: str) -> tuple:
    """
    Validate selected language code, persist it, and return
    (translation_dict, translated_header, translated_keyboard).

    DB write is awaited BEFORE the keyboard is built so the UI always
    reflects the stored state.

    Raises ValueError with a user-facing message if the code is unknown.
    """
    try:
        _ = get_string(selected)
    except Exception:
        available = "  •  ".join(
            f"`{code}` {name}" for code, name in LANG_NAMES.items()
        )
        raise ValueError(
            f"⚠️ Language code `{selected}` is not available.\n\n"
            f"**Supported codes:**\n{available}"
        )

    # DB write FIRST — keyboard is built from the confirmed state
    await set_lang(chat_id, selected)
    log.info("Language set: chat=%d  lang=%s  by=%s", chat_id, selected, actor_mention)

    header = _["setting_2"].format(actor_mention)
    keyboard = build_translated_help_keyboard(_, HELPABLE)
    return _, header, keyboard


# ── /lang — interactive picker ────────────────────────────────────────────────

@app.on_message(filters.command("lang"))
@language
async def langs_command(client, message: Message, _):
    user_id   = message.from_user.id if message.from_user else None
    chat_type = message.chat.type
    header    = _["setting_1"].format(message.from_user.first_name)

    if chat_type == "private":
        await message.reply_text(header, reply_markup=LANG_KEYBOARD)

    elif chat_type in ("group", "supergroup"):
        if not await _is_admin(message.chat.id, user_id):
            return
        try:
            await message.reply_text(header, reply_markup=LANG_KEYBOARD)
        except Exception as exc:
            log.exception("/lang group error: %s", exc)
            if LOG_GROUP_ID:
                await app.send_message(LOG_GROUP_ID, text=str(exc))


# ── /setlang <code> — direct one-shot language setter ────────────────────────

@app.on_message(filters.command("setlang"))
@language
async def setlang_command(client, message: Message, _):
    """
    Usage:
      /setlang ar        → immediately switch to Arabic (admin-only in groups)
      /setlang           → show the interactive picker (same as /lang)

    Supported codes: en  si  hi  it  ta  id  ar  ml  ny  ge
    """
    user_id   = message.from_user.id if message.from_user else None
    chat_type = message.chat.type

    # No argument → fall back to the interactive picker
    if len(message.command) < 2:
        header = _["setting_1"].format(message.from_user.first_name)
        if chat_type == "private":
            return await message.reply_text(header, reply_markup=LANG_KEYBOARD)
        if chat_type in ("group", "supergroup"):
            if not await _is_admin(message.chat.id, user_id):
                return await message.reply_text(
                    "⛔️ Only group admins can change the language."
                )
            return await message.reply_text(header, reply_markup=LANG_KEYBOARD)

    selected  = message.command[1].lower().strip()
    chat_id   = message.chat.id

    # Admin gate for groups
    if chat_type in ("group", "supergroup"):
        if not await _is_admin(chat_id, user_id):
            return await message.reply_text(
                "⛔️ Only group admins can change the language."
            )

    # Guard: already using this language
    current = await get_lang(chat_id)
    if current == selected:
        lang_name = LANG_NAMES.get(selected, f"`{selected}`")
        return await message.reply_text(
            f"ℹ️ The language is already set to **{lang_name}**."
        )

    # Validate, persist, build response
    try:
        _, header, keyboard = await _apply_language(
            chat_id, selected, message.from_user.mention
        )
    except ValueError as err:
        return await message.reply_text(str(err))

    lang_name = LANG_NAMES.get(selected, selected)
    await message.reply_text(
        f"✅ Language set to **{lang_name}**\n\n{header}",
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


# ── Callback: language-picker button pressed ──────────────────────────────────
# callback_data pattern: "languages_<code>"  e.g. "languages_ar"

@app.on_callback_query(filters.regex(r"^languages_([a-z]+)$"))
async def language_markup(client, CallbackQuery):
    cdata    = CallbackQuery.data          # e.g. "languages_ar"
    selected = cdata.split("_", 1)[1]     # "ar"   — split on first _ only
    chat_id  = CallbackQuery.message.chat.id
    user_id  = CallbackQuery.from_user.id

    log.info(
        "lang callback: data='%s' selected='%s' chat=%d user=%d",
        cdata, selected, chat_id, user_id,
    )

    # ── Guard: already active ────────────────────────────────────────────────
    old = await get_lang(chat_id)
    if str(old) == str(selected):
        log.debug("lang callback: already active, answering early")
        return await CallbackQuery.answer(
            "⚠️ Already using this language.", show_alert=False
        )

    # ── Validate & persist BEFORE answering ─────────────────────────────────
    # (DB write completes first; then we answer the Telegram callback)
    try:
        _, header, keyboard = await _apply_language(
            chat_id, selected, CallbackQuery.from_user.mention
        )
    except ValueError as exc:
        log.warning("lang callback: invalid code '%s' — %s", selected, exc)
        return await CallbackQuery.answer(
            "⚠️ This language is under construction.", show_alert=True
        )

    # Answer exactly once, after the write succeeded
    await CallbackQuery.answer("✅ Language changed!", show_alert=False)

    log.debug(
        "lang callback: editing message with keyboard (%d rows)",
        len(keyboard.inline_keyboard),
    )

    try:
        await CallbackQuery.message.edit(
            text=header,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
    except Exception as exc:
        log.exception("lang callback: edit_message failed — %s", exc)


# ── Module metadata ───────────────────────────────────────────────────────────

__MODULE__ = f"{Languages}"
__HELP__ = """
Not every group speaks fluent English; some groups would rather have Shaheen respond in their own language.

**Admin commands:**
- /lang : Open the interactive language picker.
- /setlang `<code>` : Set the language directly without a menu.

**Supported language codes:**
`en` 🇬🇧  `ar` 🇸🇦  `hi` 🇮🇳  `si` 🇱🇰  `it` 🇮🇹
`id` 🇮🇩  `ml` 🇮🇳  `ny` 🇲🇼  `ge` 🇩🇪  `ta` 🇮🇳

**Example:** `/setlang ar` switches the bot to Arabic instantly.
"""
__helpbtns__ = (
    [
        [InlineKeyboardButton(text="🇬🇧 English",    callback_data="languages_en")],
        [
            InlineKeyboardButton(text="🇱🇰 සිංහල",    callback_data="languages_si"),
            InlineKeyboardButton(text="🇮🇳 हिन्दी",    callback_data="languages_hi"),
        ],
        [
            InlineKeyboardButton(text="🇮🇹 Italiano",  callback_data="languages_it"),
            InlineKeyboardButton(text="🇮🇳 తెలుగు",    callback_data="languages_ta"),
        ],
        [
            InlineKeyboardButton(text="🇮🇩 Indonesia", callback_data="languages_id"),
            InlineKeyboardButton(text="🇸🇦 عربي",      callback_data="languages_ar"),
        ],
        [
            InlineKeyboardButton(text="🇮🇳 മലയാളം",   callback_data="languages_ml"),
            InlineKeyboardButton(text="🇲🇼 Chichewa",  callback_data="languages_ny"),
        ],
        [
            InlineKeyboardButton(text="🇩🇪 Deutsch",   callback_data="languages_ge"),
            InlineKeyboardButton(text="🇷🇺 Русский",   callback_data="languages_ru"),
        ],
    ]
)
