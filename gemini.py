import os
import re
import asyncio
import aiohttp

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ParseMode

from utils import modules_help, prefix
from utils.db import db
from utils.conv import Conversation

MODEL = "gemini-3.1-flash-lite-preview"


@Client.on_message(filters.command("aiconfig", prefix) & filters.me)
async def ai_config(client: Client, message: Message):
    args = message.text.split(maxsplit=2)
    
    if len(args) > 1:
        cmd = args[1].lower()
        if cmd == "list":
            profiles = db.get("custom.ai", "profiles", ["default"])
            active = db.get("custom.ai", "active_profile", "default")
            text = "<b>Saved AI Profiles:</b>\n"
            for p in profiles:
                text += f"- <code>{p}</code> {'(Active)' if p == active else ''}\n"
            return await message.edit(text)
            
        elif cmd == "set":
            if len(args) < 3:
                return await message.edit(f"<b>Usage:</b> <code>{prefix}aiconfig set &lt;profile_name&gt;</code>")
            profile_name = args[2]
            profiles = db.get("custom.ai", "profiles", ["default"])
            if profile_name not in profiles:
                return await message.edit(f"<b>Error:</b> Profile <code>{profile_name}</code> not found.")
            db.set("custom.ai", "active_profile", profile_name)
            return await message.edit(f"<b>Success:</b> Active AI profile set to <code>{profile_name}</code>")
            
        elif cmd == "add":
            if len(args) < 3:
                return await message.edit(f"<b>Usage:</b> <code>{prefix}aiconfig add &lt;profile_name&gt;</code>")
            profile_name = args[2]
            if profile_name == "default":
                return await message.edit("<b>Error:</b> Cannot overwrite the default profile.")
                
            async with Conversation(client, message.chat.id) as conv:
                msg = await message.edit(f"<b>AI Configuration for '{profile_name}'</b>\nPlease send the API Provider URL (e.g., <code>https://api.openai.com/v1/chat/completions</code>).")
                try:
                    response = await conv.get_response(filters.user(message.from_user.id), timeout=60)
                    provider_url = response.text.strip()
                    await response.delete()
                except asyncio.TimeoutError:
                    return await msg.edit("<b>Configuration timed out.</b>")

                await msg.edit(f"<b>AI Configuration for '{profile_name}'</b>\nPlease send the API Key.")
                try:
                    response = await conv.get_response(filters.user(message.from_user.id), timeout=60)
                    api_key = response.text.strip()
                    await response.delete()
                except asyncio.TimeoutError:
                    return await msg.edit("<b>Configuration timed out.</b>")

                await msg.edit(f"<b>AI Configuration for '{profile_name}'</b>\nPlease send the Model Name (e.g., <code>gpt-4o</code>).")
                try:
                    response = await conv.get_response(filters.user(message.from_user.id), timeout=60)
                    model_name = response.text.strip()
                    await response.delete()
                except asyncio.TimeoutError:
                    return await msg.edit("<b>Configuration timed out.</b>")

                await msg.edit(f"<b>AI Configuration for '{profile_name}'</b>\nEnable Thinking Mode? (yes/no)")
                try:
                    response = await conv.get_response(filters.user(message.from_user.id), timeout=60)
                    thinking = True if response.text.strip().lower() in ["yes", "y", "true"] else False
                    await response.delete()
                except asyncio.TimeoutError:
                    return await msg.edit("<b>Configuration timed out.</b>")

                db.set(f"custom.ai.{profile_name}", "provider_url", provider_url)
                db.set(f"custom.ai.{profile_name}", "api_key", api_key)
                db.set(f"custom.ai.{profile_name}", "model_name", model_name)
                db.set(f"custom.ai.{profile_name}", "thinking", thinking)
                
                profiles = db.get("custom.ai", "profiles", ["default"])
                if profile_name not in profiles:
                    profiles.append(profile_name)
                    db.set("custom.ai", "profiles", profiles)
                
                db.set("custom.ai", "active_profile", profile_name)

                return await msg.edit(f"<b>AI Profile '{profile_name}' saved and set as active!</b>")
        else:
            return await message.edit(
                "<b>Usage:</b>\n"
                f"<code>{prefix}aiconfig list</code> - List profiles\n"
                f"<code>{prefix}aiconfig add &lt;name&gt;</code> - Add new profile\n"
                f"<code>{prefix}aiconfig set &lt;name&gt;</code> - Set active profile\n"
            )
            
    else:
        return await message.edit(
            "<b>Usage:</b>\n"
            f"<code>{prefix}aiconfig list</code> - List profiles\n"
            f"<code>{prefix}aiconfig add &lt;name&gt;</code> - Add new profile\n"
            f"<code>{prefix}aiconfig set &lt;name&gt;</code> - Set active profile\n"
        )


@Client.on_message(filters.command("ai", prefix) & filters.me)
async def gemini_ai(client: Client, message: Message):
    query = ""
    prompt = ""

    # Direct query support
    if len(message.command) > 1:
        prompt = message.text.split(maxsplit=1)[1]

    # Reply support
    if message.reply_to_message:
        reply = message.reply_to_message
        replied_text = reply.text or reply.caption or ""
        if prompt and replied_text:
            query = f"{prompt}\n\n[Context: {replied_text}]"
        elif replied_text:
            query = replied_text
        elif prompt:
            query = prompt
    else:
        query = prompt

    if not query:
        return await message.edit(
            f"<b>Usage:</b>\n"
            f"<code>{prefix}ai what is linux?</code>\n\n"
            f"<b>Or reply to a message:</b>\n"
            f"<code>{prefix}ai explain this</code>"
        )

    active_profile = db.get("custom.ai", "active_profile", "default")
    
    if active_profile == "default":
        api_key = os.getenv("GEMINI_API_KEY")
        model = MODEL
        
        if not api_key:
            return await message.edit(
                "<b>Error:</b>\n<code>GEMINI_API_KEY not set in .env</code>"
            )
            
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": query}]}]
        }
        is_openai = False
        thinking_enabled = False
    else:
        custom_url = str(db.get(f"custom.ai.{active_profile}", "provider_url", "")).strip()
        custom_key = str(db.get(f"custom.ai.{active_profile}", "api_key", "")).strip()
        custom_model = str(db.get(f"custom.ai.{active_profile}", "model_name", "")).strip()
        thinking_enabled = db.get(f"custom.ai.{active_profile}", "thinking", False)
        
        api_key = custom_key
        model = custom_model
        url = custom_url
        
        # Auto-fix standard OpenAI compatible URLs if they only provided the base domain
        if not url.endswith(("/chat/completions", "/completions", "/generateContent")):
            if url.endswith("/v1") or url.endswith("/v1/"):
                url = url.rstrip("/") + "/chat/completions"
            else:
                url = url.rstrip("/") + "/v1/chat/completions"
                
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": query}]
        }
        is_openai = True

    await message.edit(f"<b>Thinking ({active_profile})...</b>")

    headers = {}
    if is_openai and api_key:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers, timeout=60) as response:
                data = await response.json()

        if is_openai:
            if "choices" not in data:
                error_msg = data.get("error", {}).get("message", "Unknown API error")
                return await message.edit(f"<b>API Error:</b>\n<code>{error_msg}</code>")
                
            choice = data["choices"][0]
            msg_content = choice.get("message", {})
            text = msg_content.get("content", "")
            
            # Extract reasoning_content natively if available (e.g. DeepSeek APIs)
            reasoning = msg_content.get("reasoning_content", "")
            if reasoning:
                text = f"<think>\n{reasoning}\n</think>\n\n{text}"
                
        else:
            if "candidates" not in data:
                error_msg = data.get("error", {}).get("message", "Unknown API error")
                return await message.edit(f"<b>Gemini API Error:</b>\n<code>{error_msg}</code>")
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            
        # Unified thinking parsing for both APIs
        if "<think>" in text:
            if thinking_enabled:
                think_match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
                if think_match:
                    thinking_text = think_match.group(1).strip()
                    clean_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
                    text = f"<blockquote><b>Thinking Process:</b>\n{thinking_text}</blockquote>\n\n{clean_text}"
            else:
                text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        if not text:
            return await message.edit("<b>Error:</b>\n<code>Empty response from API</code>")

        if len(text) > 4000:
            text = text[:4000] + "..."

        await message.edit(text, parse_mode=ParseMode.HTML)

    except asyncio.TimeoutError:
        await message.edit("<b>Error:</b>\n<code>Request timed out</code>")

    except Exception as e:
        await message.edit(f"<b>Error:</b>\n<code>{str(e)}</code>")


modules_help["gemini_ai"] = {
    "ai [prompt]": "Ask Active AI",
    "ai (reply)": "Reply to ask AI",
    "aiconfig list": "List saved AI profiles",
    "aiconfig add [name]": "Add new AI profile",
    "aiconfig set [name]": "Set active AI profile",
}
