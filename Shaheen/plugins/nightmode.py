import asyncio
from datetime import timedelta
import dateparser
from pyrogram import filters
from pyrogram.types import ChatPermissions, Message
from Shaheen import app
from Shaheen.utils.filter_groups import nm_g
from lang import get_command
from Shaheen.utils.commands import command
from Shaheen.utils.lang import language
from Shaheen.utils.custom_filters import can_change_filter
from button import Nightmode
from Shaheen.db.pg_store import SyncCollection

nightmod = SyncCollection('nightmodes')
night    = SyncCollection('night')

NMODE = get_command("NMODE2")
Night_mode = []


def get_info(chat_id):
    return nightmod.find_one({"id": chat_id})


@app.on_message(command(NMODE) & can_change_filter)
@language
async def customize_night(client, message: Message, _):
    rose = await message.reply(_["nm2"])
    if message.chat.type == "private":
        return await rose.edit(_["nm5"])
    if message.chat.type == "channel":
        return
    parameter = message.text.split(None, 1)[1]
    if parameter == "off":
        nightmod.delete_one({"id": message.chat.id})
        return
    if len(message.command) < 3:
        return await rose.edit(_["nm11"])
    if "|" not in parameter:
        return await rose.edit(_["nm12"])
    zone, ctime, otime = parameter.split("|")
    zone = zone.strip(); ctime = ctime.strip(); otime = otime.strip()
    if len(ctime) != 11:
        return await rose.edit(_["nm13"])
    if len(otime) != 11:
        return await rose.edit(_["nm13"])
    if not zone:
        return await rose.edit(_["nm14"])
    ttime = dateparser.parse("now", settings={"TIMEZONE": zone, "DATE_ORDER": "YMD"})
    if ttime is None:
        return await rose.edit("Please enter a valid timezone, e.g. `Asia/Amman`")
    cctime = dateparser.parse(ctime, settings={"TIMEZONE": zone, "DATE_ORDER": "DMY"}) + timedelta(days=1)
    ootime = dateparser.parse(otime, settings={"TIMEZONE": zone, "DATE_ORDER": "DMY"}) + timedelta(days=1)
    if cctime == ootime:
        return await rose.edit(_["nm15"])
    if cctime >= ootime:
        return await rose.edit("Chat closing time can't be greater than or equal to opening time")
    chats = nightmod.find({})
    for c in chats:
        if message.chat.id == c["id"] and c.get("valid"):
            to_check = get_info(message.chat.id)
            nightmod.update_one({"_id": to_check["_id"]}, {"$set": {"zone": zone, "ctime": cctime, "otime": ootime}})
            await rose.edit("**Nightmode updated successfully.**")
            return
    nightmod.insert_one({"id": message.chat.id, "valid": True, "zone": zone, "ctime": cctime, "otime": ootime})
    await rose.edit(f"**Nightmode set successfully in {message.chat.title}!**")


@app.on_message(filters.incoming, group=nm_g)
async def night_mode(app, message):
    try:
        if not message or not message.from_user:
            return message.continue_propagation()
        chats = nightmod.find({})
        if not chats:
            return
        for c in chats:
            chat_id = c["id"]; valid = c.get("valid"); zone = c["zone"]; otime = c["otime"]
            present = dateparser.parse("now", settings={"TIMEZONE": zone, "DATE_ORDER": "YMD"})
            try:
                if present and present > otime and valid:
                    newtime = otime + timedelta(days=1)
                    to_check = get_info(chat_id)
                    if not to_check:
                        continue
                    nightmod.update_one({"_id": to_check["_id"]}, {"$set": {"otime": newtime}})
                    sed = await app.send_message(chat_id, "🌗 Night Mode Ending…\n\n`Chat opening…`")
                    await app.set_chat_permissions(
                        chat_id,
                        ChatPermissions(
                            can_send_messages=True, can_send_media_messages=True,
                            can_send_other_messages=True, can_send_polls=True,
                            can_add_web_page_previews=True, can_invite_users=True,
                        ),
                    )
                    await sed.edit("**🌗 Night Mode Ended** — Chat is open ✅")
            except Exception:
                pass
        chats = nightmod.find({})
        if not chats:
            return
        for c in chats:
            chat_id = c["id"]; valid = c.get("valid"); zone = c["zone"]; ctime = c["ctime"]
            present = dateparser.parse("now", settings={"TIMEZONE": zone, "DATE_ORDER": "YMD"})
            try:
                if present and present > ctime and valid:
                    newtime = ctime + timedelta(days=1)
                    to_check = get_info(chat_id)
                    if not to_check:
                        continue
                    nightmod.update_one({"_id": to_check["_id"]}, {"$set": {"ctime": newtime}})
                    sed = await app.send_message(chat_id, "🌗 Night Mode Starting…\n\n`Chat closing…`")
                    await app.set_chat_permissions(
                        chat_id,
                        ChatPermissions(
                            can_send_messages=False, can_send_media_messages=False,
                            can_send_other_messages=False, can_send_polls=False,
                            can_add_web_page_previews=False, can_invite_users=False,
                        ),
                    )
                    await sed.edit("**🌗 Night Mode Started** — Chat is closed ❌")
            except Exception:
                pass
        return message.continue_propagation()
    except Exception:
        return


__MODULE__ = Nightmode
__HELP__ = """
🇵🇸 **Night Mode**

Automatically close and open your group at scheduled times.

**Admin Only:**
- /setnightmode [TIMEZONE] | [CLOSE TIME] | [OPEN TIME]
- /setnightmode off — Disable night mode

**Example:**
<code>/setnightmode Asia/Amman | 12:00:00 AM | 06:00:00 AM</code>
"""
