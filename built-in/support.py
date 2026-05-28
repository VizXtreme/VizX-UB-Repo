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

import datetime
import random

from dulwich.refs import Ref
from pyrogram import Client, filters
from pyrogram.types import Message

from utils import gitrepo, modules_help, prefix, python_version, userbot_version


@Client.on_message(filters.command(["support", "repo"], prefix) & filters.me)
async def support(_, message: Message):
    dev = ["@VizXtreme"]
    random.shuffle(dev)

    commands_count = 0.0
    for module in modules_help:
        for _cmd in module:
            commands_count += 1

    await message.edit(
        "📘 <b>VizX-UB</b> │ <code>Info</code>\n\n"
        "  ╭─ About\n"
        "  │  Userbot: <b>VizX-UB</b>\n"
        f"  │  Version: <code>{userbot_version}</code>\n"
        f"  │  Python: <code>{python_version}</code>\n"
        "  │\n"
        "  ├─ Stats\n"
        f"  │  Modules: <code>{len(modules_help)}</code>\n"
        f"  │  Commands: <code>{int(commands_count)}</code>\n"
        "  │\n"
        "  ├─ Links\n"
        "  │  <a href='https://github.com/VizXtreme'>GitHub</a>\n"
        "  │  <a href='https://github.com/VizX-UB-Repo'>Custom Modules</a>\n"
        "  │\n"
        "  ├─ Dev\n"
        f"  │  {', '.join(dev)}\n"
        "  │\n"
        "  ╰─────────────",
        disable_web_page_preview=True,
    )


@Client.on_message(filters.command(["version", "ver"], prefix) & filters.me)
async def version(client: Client, message: Message):
    changelog = ""
    ub_version = ".".join(userbot_version.split(".")[:2])
    async for m in client.search_messages("moonuserbot", query=f"{userbot_version}."):
        if ub_version in m.text:
            changelog = m.message_id

    await message.delete()

    config = gitrepo.get_config()
    try:
        remote_url = config.get((b"remote", b"origin"), b"url").decode("utf-8")
        if remote_url.endswith(".git"):
            remote_url = remote_url[:-4]
    except KeyError:
        remote_url = "https://github.com/VizXtreme/VizXtreme-UB"

    head_sha = gitrepo.head()
    hexsha = head_sha.decode("utf-8")
    commit_obj = gitrepo.get_object(head_sha)

    commit_time = (
        datetime.datetime.fromtimestamp(commit_obj.commit_time)
        .astimezone(datetime.timezone.utc)
        .strftime("%Y-%m-%d %H:%M:%S %Z")
    )

    _, ref_path = gitrepo.refs.follow(Ref(b"HEAD"))
    if ref_path:
        active_branch = ref_path.split(b"/")[-1].decode("utf-8")
    else:
        active_branch = "detached"

    author_name = commit_obj.author.decode("utf-8").split("<")[0].strip()

    branch_line = (
        f"  │  Branch: <a href='{remote_url}/tree/{active_branch}'>{active_branch}</a>\n"
        if active_branch not in ["master", "main"]
        else f"  │  Branch: <code>{active_branch}</code>\n"
    )

    await message.reply(
        "📘 <b>VizX-UB</b> │ <code>Version</code>\n\n"
        "  ╭─ Details\n"
        f"  │  Version: <code>{userbot_version}</code>\n"
        + branch_line
        + f"  │  Commit: <a href='{remote_url}/commit/{hexsha}'>{hexsha[:7]}</a>\n"
        f"  │  Author: <i>{author_name}</i>\n"
        f"  │  Time: <code>{commit_time}</code>\n"
        "  │\n"
        "  ╰─────────────",
        disable_web_page_preview=True,
    )


modules_help["support"] = {
    "support": "Information about userbot",
    "version": "Check userbot version",
}
