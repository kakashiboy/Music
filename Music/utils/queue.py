from config import Config
from Music import local_db


class QueueDB:
    def __init__(self):
        pass

    def put_queue(
        self,
        chat_id: int,
        user_id: int,
        duration: str,
        file: str,
        title: str,
        user: str,
        video_id: str,
        vc_type: str = "voice",
        forceplay: bool = False,
    ) -> int:
        context = {
            "chat_id": chat_id,
            "user_id": user_id,
            "duration": duration,
            "file": file,
            "title": title,
            "user": user,
            "video_id": video_id,
            "vc_type": vc_type,
            "played": 0,
        }
        if forceplay:
            que = local_db.get(chat_id)
            if que:
                que.insert(0, context)
            else:
                local_db[chat_id] = []
                local_db[chat_id].append(context)
        else:
            try:
                local_db[chat_id].append(context)
            except KeyError:
                local_db[chat_id] = []
                local_db[chat_id].append(context)
        try:
            Config.CACHE[chat_id].append(file)
        except KeyError:
            Config.CACHE[chat_id] = []
            Config.CACHE[chat_id].append(file)

        position = len(local_db.get(chat_id)) - 1

        return position

    def get_queue(self, chat_id: int) -> dict:
        try:
            que = local_db.get(chat_id)
        except KeyError:
            que = {}
        return que

    def rm_queue(self, chat_id: int, index: int):
        try:
            db = local_db.get(chat_id)
            db.pop(index)
        except IndexError:
            pass

    def clear_queue(self, chat_id: int):
        try:
            local_db[chat_id] = []
        except KeyError:
            pass

    def get_current(self, chat_id: int):
        try:
            return local_db[chat_id][0]
        except KeyError:
            return None
        except IndexError:
            return None

    def update_duration(self, chat_id: int, seek_type: int, time: int):
        try:
            if seek_type == 0:
                local_db[chat_id][0]["played"] -= time
            else:
                local_db[chat_id][0]["played"] += time
        except IndexError:
            pass


Queue = QueueDB()