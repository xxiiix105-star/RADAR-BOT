from Shaheen.db.pg_store import AsyncCollection

_nsfwdb = AsyncCollection("nsfw")

async def is_nsfw_on(chat_id: int) -> bool:
    chat = await _nsfwdb.find_one({"chat_id": chat_id})
    return bool(chat)

async def nsfw_on(chat_id: int):
    if await is_nsfw_on(chat_id):
        return
    return await _nsfwdb.insert_one({"chat_id": chat_id})

async def nsfw_off(chat_id: int):
    if not await is_nsfw_on(chat_id):
        return
    return await _nsfwdb.delete_one({"chat_id": chat_id})
