#  VizX-UB - telegram userbot
#  Copyright (C) 2020-present VizX-UB
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.


from pyrogram import Client, filters
from pyrogram.types import Message

from utils import modules_help, prefix


from datetime import datetime

@Client.on_message(filters.command(["ping", "p"], prefix) & filters.me)
async def ping(client: Client, message: Message):
    start = datetime.now()
    msg = await message.edit("<code>Pinging...</code>")
    end = datetime.now()
    # Using classic userbot ping calculation
    latency = round((end - start).microseconds / 1000, 2)
    await msg.edit(f"<b>[VizX]</b> <code>PING</code> → <b>{latency}ms</b> ⚡")


modules_help["ping"] = {
    "ping": "Check ping to Telegram servers",
}

