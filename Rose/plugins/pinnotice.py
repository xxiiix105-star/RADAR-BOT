"""
Pin Notice — إرسال إشعار مثبّت لجميع المجموعات دفعةً واحدة.

Commands (owner-only):
  /pinnotice   — يُرسل رسالة لجميع المجموعات ويثبّتها
  /unpinall    — يُزيل آخر رسالة مثبّتة من جميع المجموعات
  /stopp       — يوقف عملية pinnotice/unpinall الجارية

كيفية الاستخدام:
  • رد على رسالة (نص/صورة/فيديو/مستند/ملصق) بـ /pinnotice
  • أو: /pinnotice نص الإشعار المطلوب تثبيته
"""

import asyncio
import logging
from typing import Optional

from pyrogram import filters
from pyrogram.errors import (
    ChatAdminRequired,
    ChatWriteForbidden,
    ChannelPrivate,
    FloodWait,
    PeerIdInvalid,
    RightForbidden,
    UserNotParticipant,
)
from pyrogram.types import Message

from Rose import app
from Rose.mongo.chatsdb import get_served_chats
from config import Config

log = logging.getLogger(__name__)

OWNER_ID = int(Config.OWNER_ID) if Config.OWNER_ID else None
_active: bool = False

_SKIP_ERRORS = (
    ChatAdminRequired,
    ChatWriteForbidden,
    ChannelPrivate,
    PeerIdInvalid,
    RightForbidden,
    UserNotParticipant,
)


def _owner_only(_, __, m: Message) -> bool:
    if not m.from_user:
        return False
    return OWNER_ID is not None and m.from_user.id == OWNER_ID


owner_filter = filters.create(_owner_only)


async def _send_and_pin(chat_id: int, origin: Message, text: Optional[str]) -> str:
    """
    Send a message to chat_id and pin it.
    Returns 'ok', 'send_failed', or 'pin_failed'.
    """
    try:
        src = origin.reply_to_message
        if src:
            if src.text or src.caption:
                sent = await app.send_message(chat_id, src.text or src.caption)
            elif src.photo:
                sent = await app.send_photo(chat_id, src.photo.file_id, caption=src.caption)
            elif src.video:
                sent = await app.send_video(chat_id, src.video.file_id, caption=src.caption)
            elif src.document:
                sent = await app.send_document(chat_id, src.document.file_id, caption=src.caption)
            elif src.sticker:
                sent = await app.send_sticker(chat_id, src.sticker.file_id)
            elif src.animation:
                sent = await app.send_animation(chat_id, src.animation.file_id, caption=src.caption)
            else:
                sent = await src.forward(chat_id)
        elif text:
            sent = await app.send_message(chat_id, text)
        else:
            return "send_failed"
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        return await _send_and_pin(chat_id, origin, text)
    except _SKIP_ERRORS:
        return "send_failed"
    except Exception as exc:
        log.debug("pinnotice send error chat=%d: %s", chat_id, exc)
        return "send_failed"

    # Pin the sent message (loud=False → silent pin, no notification storm)
    try:
        await app.pin_chat_message(chat_id, sent.id, disable_notification=True)
        return "ok"
    except (ChatAdminRequired, RightForbidden, ChatWriteForbidden):
        return "pin_failed"
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        try:
            await app.pin_chat_message(chat_id, sent.id, disable_notification=True)
            return "ok"
        except Exception:
            return "pin_failed"
    except Exception as exc:
        log.debug("pinnotice pin error chat=%d: %s", chat_id, exc)
        return "pin_failed"


async def _unpin_latest(chat_id: int) -> str:
    """Unpin the latest pinned message in a chat. Returns 'ok' or 'failed'."""
    try:
        await app.unpin_chat_message(chat_id)
        return "ok"
    except FloodWait as e:
        await asyncio.sleep(e.value + 2)
        return await _unpin_latest(chat_id)
    except _SKIP_ERRORS:
        return "failed"
    except Exception as exc:
        log.debug("unpinall error chat=%d: %s", chat_id, exc)
        return "failed"


async def _run_loop(
    group_ids: list[int],
    status_msg: Message,
    action_fn,
    label: str,
) -> tuple[int, int, int, int]:
    """
    Generic loop over group_ids calling action_fn(chat_id).
    Returns (total, ok, pin_failed_or_failed, send_failed).
    """
    global _active
    ok = pin_fail = send_fail = 0
    total = len(group_ids)

    for i, chat_id in enumerate(group_ids, 1):
        if not _active:
            break
        result = await action_fn(chat_id)
        if result == "ok":
            ok += 1
        elif result == "pin_failed":
            pin_fail += 1
        else:
            send_fail += 1

        await asyncio.sleep(0.08)

        if i % 30 == 0 or i == total:
            pct = int(i / total * 100)
            bar = "▓" * (pct // 10) + "░" * (10 - pct // 10)
            try:
                await status_msg.edit(
                    f"📌 **{label}** — جارٍ...\n\n"
                    f"`[{bar}]` {pct}%\n"
                    f"✅ نجح: `{ok}` | 📌 بدون تثبيت: `{pin_fail}` | ❌ فشل: `{send_fail}` | 📊 `{i}/{total}`"
                )
            except Exception:
                pass

    return total, ok, pin_fail, send_fail


@app.on_message(filters.command("pinnotice") & owner_filter)
async def cmd_pinnotice(_, message: Message):
    """إرسال إشعار مثبّت لجميع المجموعات."""
    global _active

    if _active:
        return await message.reply_text(
            "⚠️ توجد عملية جارية. استخدم /stopp لإيقافها أولاً."
        )

    text: Optional[str] = None
    if not message.reply_to_message:
        parts = message.text.split(None, 1)
        if len(parts) < 2:
            return await message.reply_text(
                "**الاستخدام:**\n"
                "• رد على رسالة بـ /pinnotice\n"
                "• أو: `/pinnotice نص الإشعار`"
            )
        text = parts[1]

    _active = True
    status = await message.reply_text("`⏳ جارٍ جمع المجموعات...`")

    try:
        rows = await get_served_chats()
        group_ids = [
            r["chat_id"] for r in rows
            if isinstance(r.get("chat_id"), int) and r["chat_id"] < 0
        ]

        if not group_ids:
            await status.edit("⚠️ لا توجد مجموعات مسجلة بعد.")
            return

        total, ok, pin_fail, send_fail = await _run_loop(
            group_ids,
            status,
            lambda cid: _send_and_pin(cid, message, text),
            "إشعار مثبّت",
        )

        stopped = not _active and (ok + pin_fail + send_fail) < total
        footer = "\n🛑 _تم الإيقاف مبكراً_" if stopped else ""

        await status.edit(
            f"📌 **اكتمل إرسال الإشعار المثبّت**{footer}\n\n"
            f"👥 المجموعات المستهدفة: `{total}`\n\n"
            f"✅ أُرسل وثُبِّت: `{ok}`\n"
            f"📌 أُرسل بدون تثبيت: `{pin_fail}` _(لا صلاحية تثبيت)_\n"
            f"❌ فشل الإرسال: `{send_fail}` _(محظور / خاص)_"
        )

    except Exception as exc:
        log.exception("pinnotice error: %s", exc)
        await status.edit(f"⚠️ **حدث خطأ:**\n`{exc}`")
    finally:
        _active = False


@app.on_message(filters.command("unpinall") & owner_filter)
async def cmd_unpinall(_, message: Message):
    """إزالة آخر رسالة مثبّتة من جميع المجموعات."""
    global _active

    if _active:
        return await message.reply_text(
            "⚠️ توجد عملية جارية. استخدم /stopp لإيقافها أولاً."
        )

    _active = True
    status = await message.reply_text("`⏳ جارٍ جمع المجموعات...`")

    try:
        rows = await get_served_chats()
        group_ids = [
            r["chat_id"] for r in rows
            if isinstance(r.get("chat_id"), int) and r["chat_id"] < 0
        ]

        if not group_ids:
            await status.edit("⚠️ لا توجد مجموعات مسجلة بعد.")
            return

        total, ok, failed, _ = await _run_loop(
            group_ids,
            status,
            _unpin_latest,
            "إلغاء تثبيت",
        )

        stopped = not _active and (ok + failed) < total
        footer = "\n🛑 _تم الإيقاف مبكراً_" if stopped else ""

        await status.edit(
            f"📌 **اكتمل إلغاء التثبيت**{footer}\n\n"
            f"👥 المجموعات: `{total}`\n"
            f"✅ نجح: `{ok}`\n"
            f"❌ فشل: `{failed}` _(لا صلاحية / محظور)_"
        )

    except Exception as exc:
        log.exception("unpinall error: %s", exc)
        await status.edit(f"⚠️ **حدث خطأ:**\n`{exc}`")
    finally:
        _active = False


@app.on_message(filters.command("stopp") & owner_filter)
async def cmd_stopp(_, message: Message):
    """إيقاف عملية pinnotice أو unpinall الجارية."""
    global _active
    if _active:
        _active = False
        await message.reply_text("🛑 تم إيقاف العملية.")
    else:
        await message.reply_text("ℹ️ لا توجد عملية جارية حالياً.")


__MODULE__ = "PinNotice"
__HELP__ = """
**نظام الإشعار المثبّت الجماعي** — للمالك فقط

أرسل إشعاراً مثبّتاً لجميع المجموعات دفعةً واحدة.

**الأوامر:**
- /pinnotice — إرسال رسالة وتثبيتها في جميع المجموعات
- /unpinall — إلغاء تثبيت آخر رسالة مثبّتة في جميع المجموعات
- /stopp — إيقاف العملية الجارية فوراً

**كيفية الاستخدام:**
• **رد على رسالة** (نص/صورة/فيديو/مستند/ملصق) بـ `/pinnotice`
• أو كتابة النص مباشرةً: `/pinnotice مرحباً بالجميع!`

**ملاحظات:**
• يُرسل الإشعار بصمت (بدون إشعار صوتي) لتفادي إزعاج المجموعات
• إذا لم يكن للبوت صلاحية التثبيت — يُرسل الرسالة فقط دون تثبيت
• يعرض تقرير تفصيلي: مثبَّت / مُرسَل بدون تثبيت / فشل
"""
