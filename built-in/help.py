#  VizX-UB - telegram userbot
#  Copyright (C) 2020-present VizX-UB
#
#  This program is free software: you can redistribute it and/or modify

#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.

#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import modules_help, prefix
from utils.module import ModuleManager
from utils.scripts import format_module_help, with_reply

module_manager = ModuleManager.get_instance()


@Client.on_message(filters.command(["help", "h"], prefix) & filters.me)
async def help_cmd(_, message: Message):
    if not module_manager.help_navigator:
        await message.edit("<b>Help system is not initialized yet. Please wait...</b>")
        return

    if len(message.command) == 1:
        module_manager.help_navigator.current_page = 1
        await module_manager.help_navigator.send_page(message)
    elif message.command[1].lower() in modules_help:
        await message.edit(format_module_help(message.command[1].lower(), prefix))
    else:
        command_name = message.command[1].lower()
        module_found = False
        for module_name, commands in modules_help.items():
            for command in commands.keys():
                if command.split()[0] == command_name:
                    cmd = command.split(maxsplit=1)
                    cmd_desc = commands[command]
                    module_found = True
                    return await message.edit(
                        f"📘 <b>VizX-UB</b> │ <code>Command: {command_name}</code>\n\n"
                        f"  ╭─ Details\n"
                        f"  │  Module: <b>{module_name}</b>\n"
                        f"  │\n"
                        f"  │  <code>{prefix}{cmd[0]}</code>"
                        f"{' <code>' + cmd[1] + '</code>' if len(cmd) > 1 else ''}\n"
                        f"  │  <i>{cmd_desc}</i>\n"
                        f"  ╰─────────────",
                    )
        if not module_found:
            found = await module_manager.help_navigator.send_search_results(
                message, command_name
            )
            if not found:
                await message.edit(
                    f"<b>Module or command <code>{command_name}</code> not found</b>"
                )


@Client.on_message(filters.command("hs", prefix) & filters.me)
async def search_cmd(_, message: Message):
    if not module_manager.help_navigator:
        await message.edit("<b>Help system is not initialized yet. Please wait...</b>")
        return

    if len(message.command) < 2:
        return await message.edit(f"<b>Usage:</b> <code>{prefix}search [query]</code>")

    query = " ".join(message.command[1:]).lower()
    found = await module_manager.help_navigator.send_search_results(message, query)
    if not found:
        await message.edit(f"<b>No results found for <code>{query}</code></b>")


@Client.on_message(filters.command(["pn", "pp", "pq"], prefix) & filters.me)
@with_reply
async def handle_navigation(_, message: Message):
    if not module_manager.help_navigator:
        await message.edit("<b>Help system is not initialized yet. Please wait...</b>")
        return

    reply_message = message.reply_to_message
    if not reply_message:
        return await message.edit("<b>Reply to a help message to navigate.</b>")

    cmd = message.command[0].lower()
    
    if cmd == "pq":
        await reply_message.delete()
        return await message.delete()

    if "VizX-UB" in reply_message.text or "Help" in reply_message.text:
        if cmd == "pn":
            if module_manager.help_navigator.next_page():
                await module_manager.help_navigator.send_page(reply_message)
                return await message.delete()
            await message.edit("No more pages available.")
        elif cmd == "pp":
            if module_manager.help_navigator.prev_page():
                await module_manager.help_navigator.send_page(reply_message)
                return await message.delete()
            return await message.edit("This is the first page.")


modules_help["help"] = {
    "help [module/command name]": "Get common/module/command help",
    "h [module/command name]": "Get common/module/command help",
    "hs [query]": "Fuzzy search modules and commands by name",
    "pn/pp/pq": "Navigate through help pages"
    + " (pn: next page, pp: previous page, pq: quit help)",
}
