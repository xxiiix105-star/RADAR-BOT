
from pyrogram import filters
from pyrogram.types import ChatPermissions
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from Shaheen.plugins.nightmode import night
from Shaheen.utils.custom_filters import can_change_filter
from Shaheen import app

@app.on_message(filters.command("nightmode") & can_change_filter)
async def anti_service(_, message):
    if len(message.command) != 2:
        return await message.reply_text("Usage: /nightmode [on | off].")
    status = message.text.split(None, 1)[1].strip()
    status = status.lower()
    chat_id = message.chat.id

    if status == "on":
        details = night.find_one({"chat_id": chat_id})
        if details:
            return await message.reply_text("Night Mode is Already on for this Chat.")
        else:
            Data = {'chat_id': chat_id}
            night.insert_one(Data)

        await message.reply_text("Night Mode is on successfully for this chat.")

    elif status == "off":
        details = night.find_one({"chat_id": chat_id})
        if details:
            return await message.reply_text("Night Mode is Already Off for this Chat.")
        else:
            Data = {'chat_id': chat_id}
            night.deleteOne(Data)

        await message.reply_text("Night Mode is off successfully for this chat.")

    else:
        await message.reply_text("Usage: /nightmode [on | off].")


async def job_close():
    print("Good Night!")
    chats = night.find({})
    if not chats:
        return
    for c in chats:
        chat_id = c["chat_id"]
        await app.send_message(chat_id,"""
🌖 START NIGHT MODE

✅ From now on users can't send media (photos, videos, files...) and links in the group again.""")

    await app.set_chat_permissions(
            chat_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_send_polls=False,
                can_add_web_page_previews=False,
                can_invite_users=False,
                can_pin_messages=False,  
                can_change_info=False))
        
scheduler = AsyncIOScheduler(timezone="Asia/colombo")
scheduler.add_job(job_close, trigger="cron", hour=23, minute=59)
scheduler.start()


async def job_open():
    print("Hey guys wake up !")
    chats = night.find({})
    if not chats:
        return
    for c in chats:
        chat_id = c["chat_id"]
        await app.send_message(chat_id,"""
🌖 END NIGHT MODE

✅ From now on users can send media (photos, videos, files...) and links in the group again.""")
        await app.set_chat_permissions(chat_id,
        ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_send_polls=True,
            can_add_web_page_previews=True,
            can_invite_users=True,
            can_pin_messages=False,  
            can_change_info=False))
        
scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")
scheduler.add_job(job_open, trigger="cron", hour=5, minute=59)
scheduler.start()