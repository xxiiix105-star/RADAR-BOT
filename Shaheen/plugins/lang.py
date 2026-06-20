from lang import get_string
from Shaheen.mongo.language import set_lang,get_lang
from Shaheen import app,LOG_GROUP_ID
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup,Message
from Shaheen.utils.lang import language
from button import Languages


keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="🇵🇸 English", callback_data="languages_en")],
     [InlineKeyboardButton(text="🇵🇸 සිංහල", callback_data="languages_si"), 
      InlineKeyboardButton(text="🇵🇸 हिन्दी", callback_data="languages_hi")], 
     [InlineKeyboardButton(text="🇵🇸 Italiano", callback_data="languages_it"), 
      InlineKeyboardButton(text="🇵🇸 తెలుగు", callback_data="languages_ta")], 
     [InlineKeyboardButton(text="🇵🇸 Indonesia", callback_data="languages_id"), 
      InlineKeyboardButton(text="🇵🇸 عربي", callback_data="languages_ar")], 
     [InlineKeyboardButton(text="🇵🇸 മലയാളം", callback_data="languages_ml"), 
      InlineKeyboardButton(text="🇵🇸 Chichewa", callback_data="languages_ny")], 
     [InlineKeyboardButton(text="🇵🇸 German", callback_data="languages_ge"), 
      InlineKeyboardButton(text="🇵🇸 Russian", callback_data="languages_ru")]])


@app.on_message(filters.command("lang"))
@language
async def langs_command(client, message: Message, _):
    userid = message.from_user.id if message.from_user else None
    chat_type = message.chat.type
    if chat_type == "private":
        await message.reply_text("🇵🇸 Choose your language:", reply_markup=keyboard)
    elif chat_type in ["group", "supergroup"]:
        group_id = message.chat.id
        st = await app.get_chat_member(group_id, userid)
        if(st.status != "administrator" and st.status != "creator"):
            return 
        try:   
            await message.reply_text("🇵🇸 Choose your language:", reply_markup=keyboard)
        except Exception as e:
            return await app.send_message(LOG_GROUP_ID, text=e)


@app.on_callback_query(filters.regex("languages"))
async def language_markup(_, CallbackQuery):
    langauge = (CallbackQuery.data).split("_")[1]
    old = await get_lang(CallbackQuery.message.chat.id)
    if str(old) == str(langauge):
        return await CallbackQuery.answer("⛔️ You're already using this language.")
    await set_lang(CallbackQuery.message.chat.id, langauge)
    try:
        _ = get_string(langauge)
        await CallbackQuery.answer("✅ Language changed successfully.")
    except:
        return await CallbackQuery.answer("This language is under construction 👷")
    await set_lang(CallbackQuery.message.chat.id, langauge)
    return await CallbackQuery.message.edit(
        f"🇵🇸 Language successfully changed from `{old}` → `{langauge}` ✅"
    )

__MODULE__ = f"{Languages}"
__HELP__ = """
🇵🇸 **Languages**

Not every group speaks fluent English; some groups would prefer Shaheen to respond in their own language.

Change the language of most replies to be in the language of your choice!

**Admin commands:**
- /lang : Set your preferred language.
"""
__helpbtns__ = (
    [[InlineKeyboardButton(text="🇵🇸 English", callback_data="languages_en")],
     [InlineKeyboardButton(text="🇵🇸 සිංහල", callback_data="languages_si"), 
      InlineKeyboardButton(text="🇵🇸 हिन्दी", callback_data="languages_hi")], 
     [InlineKeyboardButton(text="🇵🇸 Italiano", callback_data="languages_it"), 
      InlineKeyboardButton(text="🇵🇸 తెలుగు", callback_data="languages_ta")], 
     [InlineKeyboardButton(text="🇵🇸 Indonesia", callback_data="languages_id"), 
      InlineKeyboardButton(text="🇵🇸 عربي", callback_data="languages_ar")], 
     [InlineKeyboardButton(text="🇵🇸 മലയാളം", callback_data="languages_ml"), 
      InlineKeyboardButton(text="🇵🇸 Chichewa", callback_data="languages_ny")], 
     [InlineKeyboardButton(text="🇵🇸 German", callback_data="languages_ge"), 
      InlineKeyboardButton(text="🇵🇸 Russian", callback_data="languages_ru")]])
