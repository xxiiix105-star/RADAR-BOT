"""
Broadcast system — owner-only mass messaging.

Commands:
  /broadcast   — إرسال رسالة لجميع المستخدمين المسجلين
  /gbroadcast  — إرسال رسالة لجميع المجموعات
  /abroadcast  — إرسال لكلٍّ من المستخدمين والمجموعات معاً

كيفية الاستخدام:
  • رد على رسالة (نص/صورة/فيديو/مستند/ملصق) بأحد الأوامر أعلاه
  • أو اكتب الأمر ثم النص مباشرةً: /broadcast مرحباً بالجميع
"""

import asyncio
import logging
from typing import Optional

from pyrogram import filters
from pyrogram.errors import (
    FloodWait,
    InputUserDeactivated,
    PeerIdInvalid,
    UserIsBlocked,
    ChatWriteForbidden,
    ChannelPrivate,
    UserDeactivated,
)
from pyrogram.types import Message

from Rose import app
from Rose.mongo.usersdb import get_served_users
from Rose.mongo.chatsdb import get_served_chats
from config import Config

log = logging.getLogger(__name__)

OWNER_ID = int(Config.OWNER_ID) if Config.OWNER_ID else None

_SKIP_ERRORS = (
    UserIsBlocked,
    InputUserDeactivated,
    PeerIdInvalid,
    ChatWriteForbidden,
    ChannelPrivate,
    UserDeactivated,
)

_active: bool = False


def _owner_only(_, __, m: Message) -> bool:
    if not m.from_user:
        return False
    return OWNER_ID is not None and m.from_user.id == OWNER_ID


owner_filter = filters.create(_owner_only)


async def _send_one(chat_id: int, origin: Message, text: Optional[str]) -> bool:
    """
    Send a single message to chat_id.
    Returns True on success, False on expected failure.
    Raises for unexpected errors so the caller can surface them.
    """
    try:
        if origin.reply_to_message:
            src = origin.reply_to_message
            if src.text or src.caption:
                await app.send_message(chat_id, src.text or src.caption)
            elif src.photo:
                await app.send_photo(chat_id, src.photo.file_id, caption=src.caption)
            elif src.video:
                await app.send_video(chat_id, src.video.file_id, caption=src.caption)
            elif src.document:
                await app.send_document(chat_id, src.document.file_id, caption=src.caption)
            elif src.sticker:
                await app.send_sticker(chat_id, src.sticker.file_id)
            elif src.animation:
                await app.send_animation(chat_id, src.animation.file_id, caption=src.caption)
            elif src.voice:
                await app.send_voice(chat_id, src.voice.file_id, caption=src.caption)
            elif src.audio:
                await app.send_audio(chat_id, src.audio.file_id, caption=src.caption)
            else:
                await src.forward(chat_id)
        elif text:
            await app.send_message(chat_id, text)
        else:
            return False
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        return await _send_one(chat_id, origin, text)
    except _SKIP_ERRORS:
        return False


async def _broadcast_loop(
    targets: list[int],
    origin: Message,
    text: Optional[str],
    status_msg: Message,
    label: str,
) -> tuple[int, int, int]:
    """Iterate over targets, send, update progress every 50, return (done, ok, fail)."""
    global _active
    ok = fail = 0
    total = len(targets)

    for i, chat_id in enumerate(targets, 1):
        if not _active:
            break
        success = await _send_one(chat_id, origin, text)
        if success:
            ok += 1
        else:
            fail += 1
        await asyncio.sleep(0.05)

        if i % 50 == 0 or i == total:
            pct = int(i / total * 100)
            bar = "▓" * (pct // 10) + "░" * (10 - pct // 10)
            try:
                await status_msg.edit(
                    f"📡 **{label}** — جارٍ الإرسال...\n\n"
                    f"`[{bar}]` {pct}%\n"
                    f"✅ نجح: `{ok}` | ❌ فشل: `{fail}` | 📊 المجموع: `{i}/{total}`"
                )
            except Exception:
                pass

    return total, ok, fail


async def _run_broadcast(message: Message, send_users: bool, send_groups: bool):
    global _active

    if _active:
        return await message.reply_text(
            "⚠️ يوجد بث جارٍ بالفعل. انتظر حتى ينتهي أو استخدم `/stopbroadcast`."
        )

    # Determine message content
    text: Optional[str] = None
    if not message.reply_to_message:
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "**الاستخدام:**\n"
                "• رد على رسالة بالأمر\n"
                "• أو: `/broadcast نص الرسالة`"
            )
        text = parts[1]

    _active = True
    status = await message.reply_text("`⏳ جارٍ جمع البيانات...`")

    try:
        user_ids: list[int] = []
        group_ids: list[int] = []

        if send_users:
            rows = await get_served_users()
            for row in rows:
                uid = row.get("bot_users") or row.get("bots_users")
                if uid and isinstance(uid, int) and uid > 0:
                    user_ids.append(uid)

        if send_groups:
            rows = await get_served_chats()
            for row in rows:
                cid = row.get("chat_id")
                if cid and isinstance(cid, int) and cid < 0:
                    group_ids.append(cid)

        grand_ok = grand_fail = 0

        if send_users and user_ids:
            _, ok, fail = await _broadcast_loop(
                user_ids, message, text, status, "بث للمستخدمين"
            )
            grand_ok += ok
            grand_fail += fail

        if send_groups and group_ids:
            _, ok, fail = await _broadcast_loop(
                group_ids, message, text, status, "بث للمجموعات"
            )
            grand_ok += ok
            grand_fail += fail

        total_targets = len(user_ids) + len(group_ids)
        summary = (
            f"✅ **اكتمل البث**\n\n"
            f"👤 مستخدمون: `{len(user_ids)}`\n"
            f"👥 مجموعات:  `{len(group_ids)}`\n"
            f"📊 المجموع:   `{total_targets}`\n\n"
            f"✅ نجح:  `{grand_ok}`\n"
            f"❌ فشل:  `{grand_fail}` (محظور / غير نشط / خاص)"
        )
        await status.edit(summary)

    except Exception as exc:
        log.exception("broadcast error: %s", exc)
        await status.edit(f"⚠️ **حدث خطأ أثناء البث:**\n`{exc}`")
    finally:
        _active = False


@app.on_message(filters.command("broadcast") & owner_filter)
async def cmd_broadcast(_, message: Message):
    """إرسال رسالة لجميع المستخدمين."""
    await _run_broadcast(message, send_users=True, send_groups=False)


@app.on_message(filters.command("gbroadcast") & owner_filter)
async def cmd_gbroadcast(_, message: Message):
    """إرسال رسالة لجميع المجموعات."""
    await _run_broadcast(message, send_users=False, send_groups=True)


@app.on_message(filters.command("abroadcast") & owner_filter)
async def cmd_abroadcast(_, message: Message):
    """إرسال رسالة لجميع المستخدمين والمجموعات معاً."""
    await _run_broadcast(message, send_users=True, send_groups=True)


@app.on_message(filters.command("stopbroadcast") & owner_filter)
async def cmd_stopbroadcast(_, message: Message):
    """إيقاف البث الجاري."""
    global _active
    if _active:
        _active = False
        await message.reply_text("🛑 تم إيقاف البث.")
    else:
        await message.reply_text("ℹ️ لا يوجد بث جارٍ حالياً.")


__MODULE__ = "Broadcast"
__HELP__ = """
**نظام البث الجماعي** — للمالك فقط

**الأوامر:**
- /broadcast — إرسال رسالة لجميع المستخدمين المسجلين
- /gbroadcast — إرسال رسالة لجميع المجموعات
- /abroadcast — إرسال لجميع المستخدمين والمجموعات معاً
- /stopbroadcast — إيقاف البث الجاري فوراً

**كيفية الاستخدام:**
• **رد على رسالة** (نص/صورة/فيديو/مستند/ملصق) بأحد الأوامر
• أو اكتب النص مباشرةً: `/broadcast مرحباً بالجميع!`

**ملاحظات:**
• يعرض تقدم الإرسال كل 50 رسالة
• يتجاهل تلقائياً: الحسابات المحظورة، المجموعات المغلقة، المستخدمين غير النشطين
• يعالج FloodWait تلقائياً دون توقف
"""
