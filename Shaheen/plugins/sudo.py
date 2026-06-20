import os
import asyncio
import psutil
from telegraph.aio import Telegraph
from pyrogram import filters
from Shaheen import dbn,app
from config import Config
from Shaheen.mongo.filterdb import Filters
from Shaheen.mongo.notesdb import Notes
from Shaheen.mongo.rulesdb import Rules
from Shaheen.mongo.usersdb import get_served_users,gets_served_users,remove_served_user
from Shaheen.mongo.chatsdb import get_served_chats
from pyrogram import __version__ as pyrover
from pyrogram.errors import InputUserDeactivated,FloodWait, UserIsBlocked, PeerIdInvalid


@app.on_message(filters.command("stats"))
async def gstats(_, message):
    response = await message.reply_text(text="Getting Stats!"
    )
    notesdb = Notes()
    rulesdb = Rules
    fldb = Filters()
    served_chats = len(await get_served_chats())
    served_chats = []
    chats = await get_served_chats()
    for chat in chats:
        served_chats.append(int(chat["chat_id"]))
    served_users = len(await get_served_users())
    served_users = []
    users = await get_served_users()
    for user in users:
        served_users.append(int(user["bot_users"]))   
    serve_users = len(await gets_served_users())
    serve_users = []
    user = await gets_served_users()
    for use in user:
        serve_users.append(int(use["bots_users"]))  
    ram = (str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB")
    supun = dbn.command("dbstats")
    datasiz = supun["dataSize"] / 1024
    datasiz = str(datasiz)
    storag = supun["storageSize"] / 1024
    smex = f"""
** General Stats of Rose Bot**

• **Ram:** `{ram}`
• **Pyrogram Version:** `{pyrover}`
• **DB Size:** `{datasiz[:6]} Mb`
• **Storage:** `{storag} Mb`
• **Total Chats:** `{len(served_chats)}`
• **Bot PM Users:** `{len(served_users)}`
• **Filter Count** : `{(fldb.count_filters_all())}`  **In**  `{(fldb.count_filters_chats())}`  **chats**
• **Notes Count** : `{(notesdb.count_all_notes())}`  **In**  `{(notesdb.count_notes_chats())}`  **chats**
• **Rules:** `{(rulesdb.count_chats_with_rules())}` 
• **Total Users I see:**`{len(serve_users)}`
• **Total languages** : `10`

"""
    await response.edit_text(smex)
    return


async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await remove_served_user(user_id)
        return False, "Deleted"
    except UserIsBlocked:
        await remove_served_user(user_id)
        return False, "Blocked"
    except PeerIdInvalid:
        await remove_served_user(user_id)
        return False, "Error"
    except Exception as e:
        return False, "Error"

@app.on_message(filters.private & filters.command("bcast") & filters.user(1467358214) & filters.reply)
async def broadcast_message(_, message):
    lel = await message.reply_text("Broadcast started")
    success = 0
    failed = 0
    deactivated = 0
    blocked = 0
    chats = await get_served_users() 
    for chat in chats:
        try:
            if message.command[0] == "bcast":
                await message.reply_to_message.copy(int(chat['bot_users']))
            success +=1
        except errors.InputUserDeactivated:
            deactivated +=1
            await remove_served_user(int(chat['bot_users']))
        except errors.UserIsBlocked:
            blocked +=1
        except Exception as e:
            print(e)
            failed +=1

        await lel.edit(f"✅Successfully Broadcast to `{success}` users.\n❌Faild to Broadcast `{failed}` users.\nFound `{blocked}` Blocked users and `{deactivated}` Deactivated users.")

        
@app.on_message(filters.private & filters.command("gcast") & filters.user(1467358214) & filters.reply)
async def broadcast_message(_, message):
    lel = await message.reply_text("Broadcast started")
    success = 0
    failed = 0
    deactivated = 0
    blocked = 0
    chats = await get_served_chats() 
    for chat in chats:
        try:
            if message.command[0] == "gcast":
                await message.reply_to_message.copy(int(chat['chat_id']))
            success +=1
        except errors.InputUserDeactivated:
            deactivated +=1
            await remove_served_user(int(chat['chat_id']))
        except errors.UserIsBlocked:
            blocked +=1
        except Exception as e:
            print(e)
            failed +=1

        await lel.edit(f"✅Successfully Broadcast to `{success}` users.\n❌Faild to Broadcast `{failed}` users.\nFound `{blocked}` Blocked users and `{deactivated}` Deactivated users.")

