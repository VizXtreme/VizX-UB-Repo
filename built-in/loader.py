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

import hashlib
import os
import shutil
import subprocess
import sys

import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message

from utils import modules_help, prefix
from utils.config import custom_repo, gh_token
from utils.db import db
from utils.scripts import load_module, unload_module

BASE_PATH = os.path.abspath(os.getcwd())
CATEGORIES = [
    "ai",
    "dl",
    "admin",
    "anime",
    "fun",
    "images",
    "info",
    "misc",
    "music",
    "news",
    "paste",
    "rev",
    "tts",
    "utils",
]


async def fetch_from_custom_repo(session, module_name):
    """Try to fetch a module from the VizXtreme custom repo.
    Returns (content_bytes, source_name) or (None, None) if not found.
    """
    if not custom_repo:
        return None, None
    url = f"{custom_repo}/{module_name}.py"
    headers = {}
    if gh_token:
        headers["Authorization"] = f"token {gh_token}"
    try:
        async with session.get(url, headers=headers) as resp:
            if resp.status == 200:
                return await resp.read(), "custom"
    except Exception:
        pass
    return None, None


async def fetch_from_moonub(session, module_name):
    """Try to fetch a module from the MoonTg custom_modules repo.
    Returns (content_bytes, source_name) or (None, None) if not found.
    """
    try:
        async with session.get(
            "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/full.txt"
        ) as resp:
            f = await resp.text()
    except Exception:
        return None, None
    modules_dict = {
        line.split("/")[-1].split()[0]: line.strip() for line in f.splitlines()
    }
    if module_name not in modules_dict:
        return None, None
    url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{modules_dict[module_name]}.py"
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read(), "moonub"
    except Exception:
        pass
    return None, None


@Client.on_message(filters.command(["modhash", "mh"], prefix) & filters.me)
async def get_mod_hash(_, message: Message):
    if len(message.command) == 1:
        return
    url = message.command[1].lower()
    async with aiohttp.ClientSession() as session, session.get(url) as resp:
        if resp.status != 200:
            await message.edit(
                f"<b>Troubleshooting with downloading module <code>{url}</code></b>"
            )
            return
        content = await resp.read()

    await message.edit(
        f"<b>Module hash: <code>{hashlib.sha256(content).hexdigest()}</code>\n"
        f"Link: <code>{url}</code>\nFile: <code>{url.split('/')[-1]}</code></b>",
    )


@Client.on_message(filters.command(["loadmod", "lm"], prefix) & filters.me)
async def loadmod(client: Client, message: Message):
    if (
        not (
            message.reply_to_message
            and message.reply_to_message.document
            and message.reply_to_message.document.file_name.endswith(".py")
        )
        and len(message.command) == 1
    ):
        await message.edit("<b>Specify module to download</b>")
        return

    if len(message.command) > 1:
        await message.edit("<b>Fetching module...</b>")
        url = message.command[1].lower()
        resp_content = None

        if url.startswith(
            "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/"
        ):
            module_name = url.split("/")[-1].split(".")[0]
        elif url.startswith("https://") or url.startswith("http://"):
            # Arbitrary URL — verify hash against MoonTg
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/modules_hashes.txt"
                ) as resp:
                    modules_hashes = await resp.text()
                async with session.get(url) as resp:
                    if resp.status != 200:
                        await message.edit(
                            f"<b>Troubleshooting with downloading module <code>{url}</code></b>",
                        )
                        return
                    resp_content = await resp.read()

            if hashlib.sha256(resp_content).hexdigest() not in modules_hashes:
                return await message.edit(
                    "<b>Only <a href=https://github.com/The-MoonTg-project/custom_modules/tree/main/modules_hashes.txt>"
                    "verified</a> modules or from the official "
                    "<a href=https://github.com/The-MoonTg-project/custom_modules>"
                    "custom_modules</a> repository are supported!</b>",
                    disable_web_page_preview=True,
                )

            module_name = url.split("/")[-1].split(".")[0]
        else:
            # Bare module name — search custom repo first, then MoonTg
            module_name = url.lower()
            async with aiohttp.ClientSession() as session:
                resp_content, source = await fetch_from_custom_repo(
                    session, module_name
                )
                if resp_content is None:
                    resp_content, source = await fetch_from_moonub(
                        session, module_name
                    )

            if resp_content is None:
                await message.edit(
                    f"<b>Module <code>{module_name}</code> is not found in any repo</b>"
                )
                return

        # Download from URL if content not already fetched (MoonTg direct URL case)
        if resp_content is None:
            async with aiohttp.ClientSession() as session, session.get(url) as resp:
                if resp.status != 200:
                    await message.edit(
                        f"<b>Module <code>{module_name}</code> is not found</b>"
                    )
                    return
                resp_content = await resp.read()

        if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
            os.mkdir(f"{BASE_PATH}/modules/custom_modules")

        with open(f"./modules/custom_modules/{module_name}.py", "wb") as f:
            f.write(resp_content)
    else:
        file_name = await message.reply_to_message.download()
        module_name = message.reply_to_message.document.file_name[:-3]

        with open(file_name, "rb") as f:
            content = f.read()

        async with (
            aiohttp.ClientSession() as session,
            session.get(
                "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/modules_hashes.txt"
            ) as resp,
        ):
            modules_hashes = await resp.text()

        if hashlib.sha256(content).hexdigest() not in modules_hashes:
            os.remove(file_name)
            return await message.edit(
                "<b>Only <a href=https://github.com/The-MoonTg-project/custom_modules/tree/main/modules_hashes.txt>"
                "verified</a> modules or from the official "
                "<a href=https://github.com/The-MoonTg-project/custom_modules>"
                "custom_modules</a> repository are supported!</b>",
                disable_web_page_preview=True,
            )
        os.rename(file_name, f"./modules/custom_modules/{module_name}.py")

    all_modules = db.get("custom.modules", "allModules", [])
    if module_name not in all_modules:
        all_modules.append(module_name)
        db.set("custom.modules", "allModules", all_modules)
    try:
        await load_module(module_name, client, message)
        await message.edit(f"<b>The module <code>{module_name}</code> is loaded!</b>")
    except Exception as e:
        await message.edit(
            f"<b>Failed to load module <code>{module_name}</code>:\n{e}</b>"
        )


@Client.on_message(filters.command(["unloadmod", "ulm"], prefix) & filters.me)
async def unload_mods(client: Client, message: Message):
    if len(message.command) <= 1:
        return

    module_name = message.command[1].lower()

    if module_name.startswith(
        "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/"
    ):
        module_name = module_name.split("/")[-1].split(".")[0]

    if os.path.exists(f"{BASE_PATH}/modules/custom_modules/{module_name}.py"):
        await unload_module(module_name, client)
        os.remove(f"{BASE_PATH}/modules/custom_modules/{module_name}.py")
        if module_name == "musicbot":
            subprocess.run(
                [sys.executable, "-m", "pip", "uninstall", "-y", "requirements.txt"],
                cwd=f"{BASE_PATH}/musicbot",
            )
            shutil.rmtree(f"{BASE_PATH}/musicbot")
        all_modules = db.get("custom.modules", "allModules", [])
        if module_name in all_modules:
            all_modules.remove(module_name)
            db.set("custom.modules", "allModules", all_modules)
        await message.edit(f"<b>The module <code>{module_name}</code> removed!</b>")
    elif os.path.exists(f"{BASE_PATH}/modules/{module_name}.py"):
        await message.edit(
            "<b>It is forbidden to remove built-in modules, it will disrupt the updater</b>"
        )
    else:
        await message.edit(f"<b>Module <code>{module_name}</code> is not found</b>")


@Client.on_message(filters.command(["loadallmods", "lmall"], prefix) & filters.me)
async def load_all_mods(client: Client, message: Message):
    await message.edit("<b>Fetching info...</b>")

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        os.mkdir(f"{BASE_PATH}/modules/custom_modules")

    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/full.txt"
            ) as resp,
        ):
            f = await resp.text()
    except Exception:
        return await message.edit("Failed to fetch custom modules list")
    modules_list = f.splitlines()

    await message.edit("<b>Loading modules...</b>")
    async with aiohttp.ClientSession() as session:
        for module_name in modules_list:
            url = f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{module_name}.py"
            async with session.get(url) as resp:
                if resp.status != 200:
                    continue
                content = await resp.read()
            with open(
                f"./modules/custom_modules/{module_name.split('/')[1]}.py", "wb"
            ) as f:
                f.write(content)

    loaded = 0
    for module_name in modules_list:
        name = module_name.split("/")[-1].split()[0]
        try:
            await load_module(name, client)
            loaded += 1
        except Exception:
            pass

    await message.edit(
        f"<b>Successfully loaded new modules: {loaded}</b>",
    )


@Client.on_message(filters.command(["unloadallmods", "ulmall"], prefix) & filters.me)
async def unload_all_mods(client, message: Message):
    await message.edit("<b>Fetching info...</b>")

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        return await message.edit("<b>You don't have any modules installed</b>")

    custom_modules = [
        f[:-3]
        for f in os.listdir(f"{BASE_PATH}/modules/custom_modules")
        if f.endswith(".py")
    ]
    for name in custom_modules:
        await unload_module(name, client)

    shutil.rmtree(f"{BASE_PATH}/modules/custom_modules")
    db.set("custom.modules", "allModules", [])
    await message.edit("<b>Successfully unloaded all modules!</b>")


@Client.on_message(filters.command(["updateallmods"], prefix) & filters.me)
async def updateallmods(client, message: Message):
    await message.edit("<b>Updating modules...</b>")

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        os.mkdir(f"{BASE_PATH}/modules/custom_modules")

    modules_installed = list(os.walk("modules/custom_modules"))[0][2]

    if not modules_installed:
        return await message.edit("<b>You don't have any modules installed</b>")

    updated = 0
    async with aiohttp.ClientSession() as session:
        for module_file in modules_installed:
            if not module_file.endswith(".py"):
                continue
            try:
                async with session.get(
                    "https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/full.txt"
                ) as resp:
                    f = await resp.text()
            except Exception:
                return await message.edit("Failed to fetch custom modules list")
            modules_dict = {
                line.split("/")[-1].split()[0]: line.strip() for line in f.splitlines()
            }
            module_name = module_file[:-3]
            if module_name in modules_dict:
                async with session.get(
                    f"https://raw.githubusercontent.com/The-MoonTg-project/custom_modules/main/{modules_dict[module_name]}.py"
                ) as resp:
                    if resp.status != 200:
                        continue
                    content = await resp.read()

                with open(f"./modules/custom_modules/{module_name}.py", "wb") as f:
                    f.write(content)
                try:
                    await load_module(module_name, client)
                    updated += 1
                except Exception:
                    pass

    await message.edit(f"<b>Successfully updated {updated} modules</b>")


@Client.on_message(filters.command(["loadcustom", "lmc"], prefix) & filters.me)
async def loadcustom(client: Client, message: Message):
    """Load a module from the VizXtreme custom repo."""
    if len(message.command) <= 1:
        await message.edit(
            "<b>Usage:</b> <code>.loadcustom [module_name]</code>\n"
            "Loads a module from the VizXtreme custom repo."
        )
        return

    module_name = message.command[1].lower()
    await message.edit(f"<b>Fetching <code>{module_name}</code> from custom repo...</b>")

    async with aiohttp.ClientSession() as session:
        content, source = await fetch_from_custom_repo(session, module_name)

    if content is None:
        await message.edit(
            f"<b>Module <code>{module_name}</code> not found in custom repo</b>"
        )
        return

    if not os.path.exists(f"{BASE_PATH}/modules/custom_modules"):
        os.mkdir(f"{BASE_PATH}/modules/custom_modules")

    with open(f"./modules/custom_modules/{module_name}.py", "wb") as f:
        f.write(content)

    all_modules = db.get("custom.modules", "allModules", [])
    if module_name not in all_modules:
        all_modules.append(module_name)
        db.set("custom.modules", "allModules", all_modules)

    try:
        await load_module(module_name, client, message)
        await message.edit(
            f"<b>Module <code>{module_name}</code> loaded from custom repo!</b>"
        )
    except Exception as e:
        await message.edit(
            f"<b>Failed to load module <code>{module_name}</code>:\n{e}</b>"
        )


modules_help["loader"] = {
    "loadmod [module_name]*": "Download module (searches custom repo first, then MoonUB).\n"
    "Also supports direct URLs and replying to .py files",
    "loadcustom [module_name]*": "Load a module from the VizXtreme custom repo",
    "unloadmod [module_name]*": "Delete module",
    "modhash [link]*": "Get module hash by link",
    "loadallmods": "Load all custom modules from MoonUB (use at your own risk)",
    "unloadallmods": "Unload all custom modules",
    "updateallmods": "Update all custom modules"
    "\n\n* - required argument"
    "\n <b>short cmds:</b>"
    "\n loadmod - lm"
    "\n loadcustom - lmc"
    "\n unloadmod - ulm"
    "\n modhash - mh"
    "\n loadallmods - lmall"
    "\n unloadallmods - ulmall",
}
