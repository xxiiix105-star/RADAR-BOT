"""
Daily PostgreSQL backup — dumps the database, compresses it, and sends
the file to the LOG_GROUP_ID channel.

Commands (owner-only):
  /backup        — trigger an immediate backup
  /backupinfo    — show backup schedule and last-run time

Automatic schedule: every day at 02:00 UTC.
"""
import asyncio
import gzip
import io
import logging
import os
import shutil
import subprocess
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import filters
from pyrogram.types import Message

from Rose import app, LOG_GROUP_ID
from config import Config

log = logging.getLogger(__name__)

_scheduler = AsyncIOScheduler(timezone="UTC")
_last_backup_time: str = "اخستبار لم يُجرَ بعد"

OWNER_ID = int(Config.OWNER_ID) if Config.OWNER_ID else None


def _owner_only(_, __, m: Message) -> bool:
    if not m.from_user:
        return False
    return OWNER_ID is not None and m.from_user.id == OWNER_ID


owner_filter = filters.create(_owner_only)


def _run_pg_dump() -> bytes:
    """Run pg_dump synchronously and return the raw SQL as bytes."""
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    url = db_url.replace("postgres://", "postgresql://", 1)

    result = subprocess.run(
        ["pg_dump", "--no-password", url],
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.decode(errors="replace"))
    return result.stdout


async def _do_backup(triggered_by: str = "scheduler") -> None:
    """Core backup logic — shared by the scheduler and /backup command."""
    global _last_backup_time

    if not LOG_GROUP_ID:
        log.warning("backup: LOG_GROUP_ID not set — skipping send")
        return

    now_utc = datetime.now(timezone.utc)
    stamp = now_utc.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"shaheen_backup_{stamp}.sql.gz"

    log.info("backup: starting (triggered_by=%s)", triggered_by)

    try:
        raw_sql = await asyncio.to_thread(_run_pg_dump)
    except Exception as exc:
        log.exception("backup: pg_dump failed — %s", exc)
        try:
            await app.send_message(
                LOG_GROUP_ID,
                f"⚠️ **فشل النسخ الاحتياطي** ({triggered_by})\n\n`{exc}`",
            )
        except Exception:
            pass
        return

    buf = io.BytesIO()
    with gzip.GzipFile(filename=filename, mode="wb", fileobj=buf) as gz:
        gz.write(raw_sql)
    buf.seek(0)
    size_kb = len(buf.getvalue()) / 1024

    caption = (
        f"🗄 **نسخة احتياطية تلقائية**\n\n"
        f"📅 التاريخ: `{now_utc.strftime('%Y-%m-%d %H:%M UTC')}`\n"
        f"📦 الحجم: `{size_kb:.1f} KB`\n"
        f"🔧 المُشغّل: `{triggered_by}`"
    )

    try:
        await app.send_document(
            chat_id=LOG_GROUP_ID,
            document=buf,
            file_name=filename,
            caption=caption,
        )
        _last_backup_time = now_utc.strftime("%Y-%m-%d %H:%M UTC")
        log.info("backup: sent successfully (%s, %.1f KB)", filename, size_kb)
    except Exception as exc:
        log.exception("backup: failed to send document — %s", exc)


@app.on_message(filters.command("backup") & owner_filter)
async def backup_command(_, message: Message):
    """Trigger an immediate backup on demand."""
    notice = await message.reply_text("`⏳ جارٍ إنشاء النسخة الاحتياطية...`")
    await _do_backup(triggered_by=f"manual by {message.from_user.mention}")
    await notice.edit("`✅ تم إرسال النسخة الاحتياطية إلى قناة السجلات.`")


@app.on_message(filters.command("backupinfo") & owner_filter)
async def backupinfo_command(_, message: Message):
    """Show backup schedule and last run."""
    jobs = _scheduler.get_jobs()
    job_info = "\n".join(
        f"• `{j.id}` → التشغيل القادم: `{j.next_run_time}`" for j in jobs
    ) or "لا توجد مهام مجدولة."

    await message.reply_text(
        f"🗄 **معلومات النسخ الاحتياطي**\n\n"
        f"🕑 آخر نسخة احتياطية: `{_last_backup_time}`\n\n"
        f"📅 **المهام المجدولة:**\n{job_info}"
    )


def start_backup_scheduler():
    """Register and start the daily backup job at 02:00 UTC."""
    if not _scheduler.running:
        _scheduler.add_job(
            _do_backup,
            trigger="cron",
            hour=2,
            minute=0,
            id="daily_db_backup",
            name="Daily PostgreSQL Backup",
            replace_existing=True,
            kwargs={"triggered_by": "daily scheduler"},
        )
        _scheduler.start()
        log.info("backup: daily scheduler started — runs every day at 02:00 UTC")


start_backup_scheduler()


__MODULE__ = "Backup"
__HELP__ = """
**نسخ احتياطي تلقائي لقاعدة البيانات**

يتم إجراء نسخ احتياطي تلقائي يومياً للقاعدة كل يوم في الساعة 02:00 UTC
ويُرسل ملف مضغوط (.sql.gz) إلى قناة السجلات.

**أوامر المالك فقط:**
- /backup — تشغيل نسخة احتياطية فورية
- /backupinfo — عرض جدول النسخ الاحتياطي وآخر تشغيل
"""
