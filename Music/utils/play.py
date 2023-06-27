from pyrogram.enums import MessageEntityType
from pyrogram.types import InlineKeyboardMarkup, Message

from Music.core.auto_cmds import auto_delete
from Music.core.calls import hellmusic
from Music.core.clients import hellbot
from Music.core.database import db
from Music.helpers.buttons import Buttons
from Music.helpers.strings import TEXTS

from .exceptions import UserException
from .queue import Queue
from .thumbnail import thumb
from .youtube import ytube


class Player:
    def __init__(self) -> None:
        pass

    async def get_url(self, message: Message):
        msg = [message]
        if message.reply_to_message:
            msg.append(message.reply_to_message)
        url = ""
        offset = length = None
        for m in msg:
            if offset:
                break
            if m.entities:
                for entity in m.entities:
                    if entity.type == MessageEntityType.URL:
                        url = m.text or m.caption
                        offset, length = entity.offset, entity.length
                        break
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
            elif m.caption_entities:
                for entity in m.caption_entities:
                    if entity.type == MessageEntityType.URL:
                        url = m.text or m.caption
                        offset, length = entity.offset, entity.length
                        break
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return url[offset : offset + length]

    async def play(self, message: Message, context: dict, edit: bool = True):
        (
            chat_id,
            user_id,
            duration,
            file,
            title,
            user,
            video_id,
            vc_type,
            force,
        ) = context.values()
        if force:
            await hellmusic.leave_vc(chat_id, True)
        if video_id == "telegram":
            file_path = file
        else:
            try:
                if edit:
                    await message.edit_text("Downloading ...")
                else:
                    await message.reply_text("Downloading ...")
                success, file_path = await ytube.download(video_id, True)
            except Exception as e:
                if edit:
                    await message.edit_text(str(e))
                else:
                    await message.reply_text(str(e))
                return
            if not success:
                if edit:
                    await message.edit_text(file_path)
                else:
                    await message.reply_text(file_path)
                return
        position = Queue.put_queue(
            chat_id,
            user_id,
            duration,
            file_path,
            title,
            user,
            video_id,
            vc_type,
            force,
        )
        if position == 0:
            if not force:
                Queue.clear_queue(chat_id)
            photo = thumb.generate((359), (297, 302), video_id)
            try:
                await hellmusic.join_vc(
                    chat_id, file_path, True if vc_type == "video" else False
                )
            except UserException as e:
                await message.delete()
                await message.reply_text(str(e))
                return
            btns = Buttons.player_markup(chat_id, video_id, hellbot.app.username)
            if photo:
                sent = await hellbot.app.send_photo(
                    chat_id,
                    photo,
                    TEXTS.PLAYING.format(
                        hellbot.app.mention,
                        title,
                        duration,
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(btns),
                )
            else:
                sent = await hellbot.app.send_message(
                    chat_id,
                    TEXTS.PLAYING.format(
                        hellbot.app.mention,
                        title,
                        duration,
                        user,
                    ),
                    reply_markup=InlineKeyboardMarkup(btns),
                )
        else:
            await hellbot.app.send_message(
                chat_id,
                TEXTS.QUEUE.format(
                    position,
                    title,
                    duration,
                    user,
                ),
                reply_markup=InlineKeyboardMarkup(Buttons.close_markup()),
            )
        await message.delete()
        await db.update_songs_count(1)
        await db.update_user(user_id, "songs_played", 1)
        await auto_delete(sent, duration)
        await hellbot.logit(
            f"play {vc_type}",
            f"Song: `{title}` \nChat: `{chat_id}` \nUser: {user}"
        )


player = Player()