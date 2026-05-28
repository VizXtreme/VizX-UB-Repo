#  VizX-UB - telegram userbot
#  Copyright (C) 2020-present VizX-UB
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.

import os
import sys
import aiohttp
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message

from utils import modules_help, prefix
from utils.config import custom_repo, gh_token
from utils.scripts import load_module

BASE_PATH = os.path.abspath(os.getcwd())


@Client.on_message(filters.command(["hotupdate", "hu"], prefix) & filters.me)
async def hot_update(client: Client, message: Message):
    if not custom_repo:
        return await message.edit("<b>❌ Error: No custom repository configured!</b>")

    await message.edit("<b>⏳ Starting hot-reload update...</b>")

    success_templates = []
    failed_templates = []
    success_builtin = []
    failed_builtin = []
    success_custom = []
    failed_custom = []

    # 1. Update Web UI templates (public/)
    public_dir = os.path.join(BASE_PATH, "public")
    if os.path.exists(public_dir):
        templates = [f for f in os.listdir(public_dir) if f.endswith(".html")]
        if templates:
            await message.edit("<b>⏳ Updating Web UI templates...</b>")
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
                for t in templates:
                    url = f"{custom_repo}/public/{t}"
                    try:
                        async with session.get(url, headers=headers) as resp:
                            if resp.status == 200:
                                content = await resp.read()
                                with open(os.path.join(public_dir, t), "wb") as f:
                                    f.write(content)
                                success_templates.append(t)
                            else:
                                failed_templates.append(f"{t} (status {resp.status})")
                    except Exception as e:
                        failed_templates.append(f"{t} ({str(e)})")

    # 2. Update Built-in modules (modules/)
    modules_dir = os.path.join(BASE_PATH, "modules")
    builtin_modules = []
    for f in os.listdir(modules_dir):
        if (
            f.endswith(".py")
            and not f.startswith("_")
            and f not in ("loader.py", "__init__.py")
            and os.path.isfile(os.path.join(modules_dir, f))
        ):
            builtin_modules.append(f[:-3])

    if builtin_modules:
        await message.edit("<b>⏳ Updating built-in modules...</b>")
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
            for name in builtin_modules:
                url = f"{custom_repo}/built-in/{name}.py"
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            dest_path = os.path.join(modules_dir, f"{name}.py")
                            with open(dest_path, "wb") as f:
                                f.write(content)
                            
                            # Reload it
                            await load_module(name, client, core=True)
                            success_builtin.append(name)
                        else:
                            failed_builtin.append(f"{name} (status {resp.status})")
                except Exception as e:
                    failed_builtin.append(f"{name} ({str(e)})")

    # 3. Update Custom modules (modules/custom_modules/)
    custom_dir = os.path.join(BASE_PATH, "modules", "custom_modules")
    custom_modules = []
    if os.path.exists(custom_dir):
        for f in os.listdir(custom_dir):
            if f.endswith(".py") and os.path.isfile(os.path.join(custom_dir, f)):
                custom_modules.append(f[:-3])

    if custom_modules:
        await message.edit("<b>⏳ Updating custom modules...</b>")
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"token {gh_token}"} if gh_token else {}
            for name in custom_modules:
                url = f"{custom_repo}/{name}.py"
                try:
                    async with session.get(url, headers=headers) as resp:
                        if resp.status == 200:
                            content = await resp.read()
                            dest_path = os.path.join(custom_dir, f"{name}.py")
                            with open(dest_path, "wb") as f:
                                f.write(content)
                            
                            # Reload it
                            await load_module(name, client, core=False)
                            success_custom.append(name)
                        else:
                            failed_custom.append(f"{name} (status {resp.status})")
                except Exception as e:
                    failed_custom.append(f"{name} ({str(e)})")

    # Create formatted report
    report = "<b>⚡ Hot Update Complete!</b>\n"
    report += "━━━━━━━━━━━━━━━━━━━━\n"
    
    if success_templates or failed_templates:
        report += "🖥️ <b>Web UI Templates:</b>\n"
        if success_templates:
            report += f"  ✅ Updated: <code>{', '.join(success_templates)}</code>\n"
        if failed_templates:
            report += f"  ❌ Failed: <code>{', '.join(failed_templates)}</code>\n"
        report += "\n"

    if success_builtin or failed_builtin:
        report += "📦 <b>Built-in Modules:</b>\n"
        if success_builtin:
            report += f"  ✅ Reloaded: <code>{', '.join(success_builtin)}</code>\n"
        if failed_builtin:
            report += f"  ❌ Failed: <code>{', '.join(failed_builtin)}</code>\n"
        report += "\n"

    if success_custom or failed_custom:
        report += "🧩 <b>Custom Modules:</b>\n"
        if success_custom:
            report += f"  ✅ Reloaded: <code>{', '.join(success_custom)}</code>\n"
        if failed_custom:
            report += f"  ❌ Failed: <code>{', '.join(failed_custom)}</code>\n"
        report += "\n"

    total_success = len(success_templates) + len(success_builtin) + len(success_custom)
    total_failed = len(failed_templates) + len(failed_builtin) + len(failed_custom)
    report += f"✨ <b>Status:</b> {total_success} success, {total_failed} failed."

    await message.edit(report)


modules_help["hotupdater"] = {
    "hotupdate": "Update templates, built-in, and custom modules from custom repository and hot-reload them immediately without restart",
}
