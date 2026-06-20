import asyncio
import importlib
import logging
import re
from contextlib import (
    closing,
    suppress
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logging.getLogger("Rose.plugins.lang").setLevel(logging.DEBUG)
from Rose.utils.lang import *
from uvloop import install
from pyrogram import ( 
    filters, 
    idle
)
from pyrogram.types import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup, 
    Message
)
from Rose import (
    app,
    BOT_USERNAME,
    bot,
    BOT_NAME,
    aiohttpsession,
    HELPABLE,
)
from Rose.plugins import ALL_MODULES
from Rose.utils import paginate_modules
from lang import get_command
from Rose.utils.lang import (
    language,
    languageCB
)
from Rose.utils.start import (
    get_private_rules,
    get_learn
)
from Rose.mongo.usersdb import (
    adds_served_user,
    add_served_user
)
from config import var
from Rose.mongo.chatsdb import add_served_chat
from Rose.plugins.fsub import ForceSub
from config import Config
try:
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

flood = {}
# HELPABLE is now the shared dict in Rose/__init__.py — imported above.
# Do NOT re-declare it here; doing so would create a local copy that lang.py
# cannot see, causing "dead keyboard" (no module buttons after language switch).

async def start_bot():
    # Pre-seed MsgId with real system time to fix BadMsgNotification [16]
    import time as _time
    from pyrogram.session.internals.msg_id import MsgId
    MsgId.set_server_time(_time.time())

    # Start pyrogram clients inside the async event loop (correct pattern)
    await bot.start()
    await app.start()
    from Rose import _init_bot_info
    await _init_bot_info()

    for module in ALL_MODULES:
        imported_module = importlib.import_module("Rose.plugins." + module)
        if (
            hasattr(imported_module, "__MODULE__")
            and imported_module.__MODULE__
        ):
            imported_module.__MODULE__ = imported_module.__MODULE__
            if (
                hasattr(imported_module, "__HELP__")
                and imported_module.__HELP__
            ):
                HELPABLE[
                    imported_module.__MODULE__.replace(" ", "_").lower()
                ] = imported_module

    all_module = ""
    j = 1
    for i in ALL_MODULES:
        if j == 1:
            all_module += "•≫ Successfully imported:{:<15}.py\n".format(i)
            j = 0
        else:
            all_module += "•≫ Successfully imported:{:<15}.py".format(i)
        j += 1   

    print(f"{all_module}")
    print("""
 _____________________________________________   
|                                             |  
|          Deployed Successfully              |  
|         (C) 2021-2022 by @szteambots        | 
|          Greetings from supun  :)           |
|_____________________________________________| """)

    # Auto-register bot commands menu so shortcuts appear without manual BotFather setup
    try:
        bot_cmds = [
            BotCommand("start",       "Start the bot"),
            BotCommand("help",        "Get help menu"),
            BotCommand("ban",         "Ban a user"),
            BotCommand("kick",        "Kick a user"),
            BotCommand("mute",        "Mute a user"),
            BotCommand("warn",        "Warn a user"),
            BotCommand("adminlist",   "List group admins"),
            BotCommand("filter",      "Add a message filter"),
            BotCommand("filters",     "View active filters"),
            BotCommand("notes",       "View saved notes"),
            BotCommand("save",        "Save a note"),
            BotCommand("rules",       "Show group rules"),
            BotCommand("lock",        "Lock a chat permission"),
            BotCommand("unlock",      "Unlock a chat permission"),
            BotCommand("flood",       "Configure anti-flood"),
            BotCommand("captcha",     "Toggle captcha for new members"),
            BotCommand("lang",        "Change bot language"),
            BotCommand("setlang",     "Set language directly, e.g. /setlang ar"),
            BotCommand("connections", "Manage group connections"),
            BotCommand("approve",     "Approve a user"),
            BotCommand("blacklist",   "View blacklisted words"),
        ]
        await app.set_bot_commands(bot_cmds)
        print("✅ Bot commands menu registered successfully.")
    except Exception as e:
        print(f"⚠️  Could not set bot commands: {e}")
    await idle()
    await aiohttpsession.close()
    print("Stopping clients")
    await app.stop()
    await bot.stop()
    print("Cancelling asyncio tasks")
    for task in asyncio.all_tasks():
        task.cancel()
    print("Bot offline")


@app.on_message(filters.command("start"))
@language
async def start(client, message: Message, _):
    chat_id = message.chat.id
    FSub = await ForceSub(bot, message)
    if FSub == 400:
        return
    if message.chat.type != "private":
        await message.reply_text(var.group_start_text)
        await adds_served_user(message.from_user.id)     
        return await add_served_chat(chat_id) 
    if len(message.text.split()) > 1:
        name = (message.text.split(None, 1)[1]).lower()
        if name.startswith("rules"):
                return await get_private_rules(app, message, name)
        if name.startswith("learn"):
                return await get_learn(app, message, name)
        if "_" in name:
            module = name.split("_", 1)[1]
            text = (_["main6"].format({HELPABLE[module].__MODULE__}
                + HELPABLE[module].__HELP__)
            )
            await message.reply(text, disable_web_page_preview=True)
        if name == "help":
            text, keyb = await help_parser(message.from_user.first_name)
            await message.reply(_["main5"],reply_markup=keyb, disable_web_page_preview=True)
        if name == "connections":
            await message.reply(var.Connection_text_start)
    else:
        user_mention = message.from_user.mention
        await message.reply_text(var.pm_start_text.format(user_mention,BOT_NAME),reply_markup=var.home_keyboard_pm)
        return await add_served_user(chat_id) 

@app.on_callback_query(filters.regex("_langs"))
@languageCB
async def commands_callbacc(client, CallbackQuery, _):
    await CallbackQuery.message.edit(
        text= var.lang_text,
        reply_markup = var.lang_keyboard,
        disable_web_page_preview=True)

@app.on_callback_query(filters.regex("_about"))
@languageCB
async def commands_callbacc(client, CallbackQuery, _):
    await CallbackQuery.message.edit(
        text=_["menu"],
        reply_markup=var.about_buttons,
        disable_web_page_preview=True)
    
@app.on_message(filters.command("help"))
@language
async def help_command(client, message: Message, _):
    if message.chat.type != "private":
        if len(message.command) >= 2:
            name = (message.text.split(None, 1)[1]).replace(" ", "_").lower()
            if str(name) in HELPABLE:
                help_keyboard_button = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(text=_["main3"], url=f"t.me/{BOT_USERNAME}?start=help_{name}")
                        ]
                    ]
)
                await message.reply_text(_["main4"],reply_markup=help_keyboard_button)
            else:
                await message.reply_text(_["main2"], reply_markup=help_keyboard_button)
        else:
            await message.reply_text(_["main2"], reply_markup=help_keyboard_button)

    else:
        if len(message.command) >= 2:
            name = (message.text.split(None, 1)[1]).replace(" ", "_").lower()
            if str(name) in HELPABLE:
                text = (_["main6"].format({HELPABLE[name].__MODULE__}
                + HELPABLE[name].__HELP__))
                if hasattr(HELPABLE[name], "__helpbtns__"):
                       button = (HELPABLE[name].__helpbtns__) + [[InlineKeyboardButton("« Back", callback_data="bot_commands")]]
                if not hasattr(HELPABLE[name], "__helpbtns__"): button = [[InlineKeyboardButton("« Back", callback_data="bot_commands")]]
                await message.reply_text(text,reply_markup=InlineKeyboardMarkup(button),disable_web_page_preview=True)
            else:
                text, help_keyboard = await help_parser(message.from_user.first_name)
                await message.reply_text(_["main5"],reply_markup=help_keyboard,disable_web_page_preview=True)
        else:
            text, help_keyboard = await help_parser(message.from_user.first_name)
            await message.reply_text(
                text, reply_markup=help_keyboard, disable_web_page_preview=True
            )
    return
  
@app.on_callback_query(filters.regex("startcq"))
@languageCB
async def startcq(client,CallbackQuery, _):
    user_mention = CallbackQuery.from_user.mention
    await CallbackQuery.message.edit(
        text=var.pm_start_text.format(user_mention,BOT_NAME),
        disable_web_page_preview=True,
        reply_markup=var.home_keyboard_pm)

async def help_parser(name, keyboard=None):
    if not keyboard:
        help_keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    return (var.help_text,help_keyboard)

@app.on_callback_query(filters.regex("bot_commands"))
@languageCB
async def commands_callbacc(client,CallbackQuery, _):
    text ,help_keyboard = await help_parser(CallbackQuery.from_user.mention)
    await CallbackQuery.message.edit(text=_["main5"],reply_markup=help_keyboard,disable_web_page_preview=True)

@app.on_callback_query(filters.regex(r"help_(.*?)"))
@languageCB
async def help_button(client, query, _):
    home_match = re.match(r"help_home\((.+?)\)", query.data)
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)
    create_match = re.match(r"help_create", query.data)
    top_text = _["main5"]
    if mod_match:
        module = (mod_match.group(1)).replace(" ", "_")
        text = (
            "{} **{}**:\n".format(
                "Here is the help for", HELPABLE[module].__MODULE__
            )
            + HELPABLE[module].__HELP__)
        if hasattr(HELPABLE[module], "__helpbtns__"):
                       button = (HELPABLE[module].__helpbtns__) + [[InlineKeyboardButton("Back", callback_data="bot_commands")]]
        if not hasattr(HELPABLE[module], "__helpbtns__"): button = [[InlineKeyboardButton("Back", callback_data="bot_commands")]]
        await query.message.edit(text=text,reply_markup=InlineKeyboardMarkup(button),disable_web_page_preview=True,)
    elif home_match:
        await query.message.edit(query.from_user.id,text= _["main2"],reply_markup=var.home_keyboard_pm)
    elif prev_match:
        curr_page = int(prev_match.group(1))
        await query.message.edit(text=top_text,reply_markup=InlineKeyboardMarkup(paginate_modules(curr_page - 1, HELPABLE, "help")),disable_web_page_preview=True)
    elif next_match:
        next_page = int(next_match.group(1))
        await query.message.edit(text=top_text,reply_markup=InlineKeyboardMarkup(paginate_modules(next_page + 1, HELPABLE, "help")),disable_web_page_preview=True)
    elif back_match:
        await query.message.edit(text=top_text,reply_markup=InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help")),disable_web_page_preview=True)
    elif create_match:
        text, keyboard = await help_parser(query)
        await query.message.edit(text=text,reply_markup=keyboard,disable_web_page_preview=True)
    return await client.answer_callback_query(query.id)


if __name__ == "__main__":
    install()
    loop.run_until_complete(start_bot())
