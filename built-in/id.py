#  VizX-UB - telegram userbot
#  Copyright (C) 2020-present VizX-UB
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pyrogram import Client, enums, filters
from pyrogram.types import Message, MessageOriginHiddenUser

from utils import modules_help, prefix


@Client.on_message(filters.command("id", prefix) & filters.me)
async def ids(_, message: Message):
    output = f"<b>[VizX]</b> 🆔 <code>ID Info</code>\n\n"
    output += f"  <b>›</b> Chat: <code>{message.chat.id}</code> (DC {message.chat.dc_id})\n"
    output += f"  <b>›</b> Msg: <code>{message.id}</code>\n"
    if message.from_user:
        output += f"  <b>›</b> User: <code>{message.from_user.id}</code> (DC {message.from_user.dc_id})\n"
    else:
        output += f"  <b>›</b> Sender: <code>{message.sender_chat.id}</code>\n"

    if rtm := message.reply_to_message:
        output += f"\n  <b>›</b> Replied Msg: <code>{rtm.id}</code>\n"
        if user := rtm.from_user:
            output += f"  <b>›</b> Replied User: <code>{user.id}</code> (DC {user.dc_id})\n"
        else:
            output += f"  <b>›</b> Replied Chat: <code>{rtm.sender_chat.id}</code> (DC {rtm.sender_chat.dc_id})\n"

        if rtm.forward_origin and rtm.forward_origin.date:
            if isinstance(rtm.forward_origin, MessageOriginHiddenUser):
                output += "\n  <b>›</b> Forwarded: <i>Hidden User</i>\n"
            elif ffc := rtm.forward_origin.sender_user:
                output += f"\n  <b>›</b> Fwd Msg: <code>{getattr(rtm.forward_origin, 'message_id', None)}</code>\n"
                output += f"  <b>›</b> Fwd Chat: <code>{ffc.id}</code> (DC {ffc.dc_id})\n"

    await message.edit(output)


modules_help["id"] = {
    "id": "simply run or reply to message",
}
