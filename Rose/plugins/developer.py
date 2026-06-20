"""
Developer card — shows the bot developer's profile card with social links.
Triggered by the 👨‍💻 Developer button on the start menu.
"""

import logging

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Rose import app
from Rose.utils.lang import languageCB

log = logging.getLogger(__name__)

DEV_PHOTO = "https://i.postimg.cc/s2Xm3qSf/IMG-20260620-133210-543.jpg"

_SOCIAL_BUTTONS = [
    [
        InlineKeyboardButton(
            "📸 Instagram",
            url="https://www.instagram.com/1.0_v_?igsh=N2N5MXNwN3p4ZDY2",
        ),
        InlineKeyboardButton(
            "📘 Facebook",
            url="https://www.facebook.com/profile.php?id=61590653501533&mibextid=ZbWKwL",
        ),
    ],
    [
        InlineKeyboardButton(
            "🎵 TikTok",
            url="https://www.tiktok.com/@zix8ii",
        ),
        InlineKeyboardButton(
            "✈️ Telegram",
            url="https://t.me/Y9_S4",
        ),
    ],
]


def _build_dev_keyboard(back_label: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        _SOCIAL_BUTTONS + [[InlineKeyboardButton(back_label, callback_data="startcq")]]
    )


@app.on_callback_query(filters.regex(r"^_developer$"))
@languageCB
async def developer_callback(client, query, _):
    back_label = _.get("back", "« Back")
    dev_text   = _.get(
        "dev_text",
        "👨‍💻 **Developer**\n\nHello! I'm the developer of **Shaheen Bot**.\n\nFeel free to reach out on social media!",
    )

    keyboard = _build_dev_keyboard(back_label)

    try:
        await query.message.delete()
    except Exception:
        pass

    try:
        await app.send_photo(
            chat_id=query.message.chat.id,
            photo=DEV_PHOTO,
            caption=dev_text,
            reply_markup=keyboard,
        )
    except Exception as exc:
        log.warning("developer_callback: send_photo failed (%s), sending text only", exc)
        await app.send_message(
            chat_id=query.message.chat.id,
            text=dev_text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )

    await query.answer()


__MODULE__ = "Developer"
__HELP__ = ""
