from Shaheen.db.pg_store import SyncCollection

class captchas():
    def __init__(self):
        self.chats = SyncCollection("captcha_chats")

    def chat_in_db(self, chat_id):
        return self.chats.find_one({"chat_id": chat_id})

    def add_chat(self, chat_id, captcha):
        if self.chat_in_db(chat_id):
            return 404
        self.chats.insert_one({"chat_id": chat_id, "captcha": captcha})
        return 200

    def delete_chat(self, chat_id):
        self.chats.delete_many({"chat_id": chat_id})
        return True
