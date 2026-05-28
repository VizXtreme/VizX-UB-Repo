import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from utils import modules_help, prefix
from utils.db import db

DB_KEY = "custom.global_filters"


@Client.on_message(filters.private & ~filters.me, group=1)
async def global_filter_listener(client: Client, message: Message):
    if not message.text:
        return

    g_filters = db.get(DB_KEY, "data", {})
    text_lower = message.text.lower().strip()

    if text_lower not in g_filters:
        return

    data = g_filters[text_lower]

    if data.get("manual_only", False):
        return

    me = await client.get_me()
    my_name = me.first_name
    user_name = message.from_user.first_name

    reply_type = data.get("type")
    content = data.get("content")

    if reply_type == "text":
        final_text = (
            content.replace("{user}", user_name)
            .replace("{my_name}", my_name)
        )

        await message.reply(
            final_text,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )

    elif reply_type == "sticker":
        await message.reply_sticker(
            content,
            reply_to_message_id=message.id
        )

    elif reply_type == "photo":
        await message.reply_photo(
            content,
            reply_to_message_id=message.id
        )

    elif reply_type == "animation":
        await message.reply_animation(
            content,
            reply_to_message_id=message.id
        )


@Client.on_message(filters.command("gfilter", prefix) & filters.me)
async def add_global_filter(client: Client, message: Message):

    if not message.reply_to_message:
        return await message.edit(
            f"<b>Reply to a message/sticker/media.</b>\n"
            f"<code>{prefix}gfilter hi</code>"
        )

    if len(message.command) < 2:
        return await message.edit(
            f"<b>Usage:</b>\n"
            f"<code>{prefix}gfilter hi</code>"
        )

    keywords_raw = message.text.split(maxsplit=1)[1]

    if keywords_raw.startswith("(") and keywords_raw.endswith(")"):
        keywords = [
            k.strip().strip("'").strip('"').lower()
            for k in keywords_raw[1:-1].split(",")
        ]
    else:
        keywords = [keywords_raw.lower()]

    reply = message.reply_to_message

    # Detect media type
    if reply.sticker:
        data = {
            "type": "sticker",
            "content": reply.sticker.file_id
        }

    elif reply.photo:
        data = {
            "type": "photo",
            "content": reply.photo.file_id
        }

    elif reply.animation:
        data = {
            "type": "animation",
            "content": reply.animation.file_id
        }

    elif reply.text or reply.caption:
        data = {
            "type": "text",
            "content": reply.text or reply.caption
        }

    else:
        return await message.edit("<b>Unsupported media type.</b>")

    g_filters = db.get(DB_KEY, "data", {})

    for k in keywords:
        g_filters[k] = data

    db.set(DB_KEY, "data", g_filters)

    await message.edit(
        f"<b>Global filter(s) added!</b>\n"
        f"<b>Keywords:</b> <code>{', '.join(keywords)}</code>\n"
        f"<b>Type:</b> <code>{data['type']}</code>"
    )


@Client.on_message(filters.command(["gdel", "pdel"], prefix) & filters.me)
async def del_global_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit(
            f"<b>Usage:</b> <code>{prefix}gdel [keyword]</code>"
        )

    keyword = message.command[1].lower()
    g_filters = db.get(DB_KEY, "data", {})

    if keyword in g_filters:
        del g_filters[keyword]
        db.set(DB_KEY, "data", g_filters)

        await message.edit(
            f"<b>Global filter deleted:</b> <code>{keyword}</code>"
        )
    else:
        await message.edit("<b>Filter not found.</b>")


@Client.on_message(filters.command("pfilter", prefix) & filters.me)
async def add_personal_filter(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.edit(
            f"<b>Reply to a message/sticker/media.</b>\n"
            f"<code>{prefix}pfilter keyword</code>"
        )

    if len(message.command) < 2:
        return await message.edit(
            f"<b>Usage:</b>\n"
            f"<code>{prefix}pfilter keyword</code>"
        )

    keywords_raw = message.text.split(maxsplit=1)[1]

    if keywords_raw.startswith("(") and keywords_raw.endswith(")"):
        keywords = [
            k.strip().strip("'").strip('"').lower()
            for k in keywords_raw[1:-1].split(",")
        ]
    else:
        keywords = [keywords_raw.lower()]

    reply = message.reply_to_message

    # Detect media type
    if reply.sticker:
        data = {
            "type": "sticker",
            "content": reply.sticker.file_id
        }
    elif reply.photo:
        data = {
            "type": "photo",
            "content": reply.photo.file_id
        }
    elif reply.animation:
        data = {
            "type": "animation",
            "content": reply.animation.file_id
        }
    elif reply.text or reply.caption:
        data = {
            "type": "text",
            "content": reply.text or reply.caption
        }
    else:
        return await message.edit("<b>Unsupported media type.</b>")

    # Mark as manual-only (personal)
    data["manual_only"] = True

    g_filters = db.get(DB_KEY, "data", {})

    for k in keywords:
        g_filters[k] = data

    db.set(DB_KEY, "data", g_filters)

    await message.edit(
        f"<b>Personal filter(s) added!</b>\n"
        f"<b>Keywords:</b> <code>{', '.join(keywords)}</code>\n"
        f"<b>Type:</b> <code>{data['type']}</code> (manual-only)"
    )


@Client.on_message(filters.command(["gfilters", "gflist"], prefix) & filters.me)
async def list_global_filters(client: Client, message: Message):
    g_filters = db.get(DB_KEY, "data", {})
    if not g_filters:
        return await message.edit("<b>No global filters found.</b>")
    
    text = "<b>Global Filters:</b>\n\n"
    for index, (key, value) in enumerate(sorted(g_filters.items()), start=1):
        is_personal = " (personal)" if value.get("manual_only", False) else ""
        text += f"{index}. <code>{key}</code>{is_personal}\n"
    
    await message.edit(text[:4096])


@Client.on_message(filters.command(["g", "gf"], prefix) & filters.me)
async def trigger_global_filter(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.edit(
            f"<b>Usage:</b> <code>{prefix}g [keyword]</code>"
        )
    
    keyword = message.text.split(maxsplit=1)[1].lower()
    g_filters = db.get(DB_KEY, "data", {})
    
    if keyword not in g_filters:
        return await message.edit(f"<b>Global filter not found for</b> <code>{keyword}</code>")
    
    data = g_filters[keyword]
    reply_type = data.get("type")
    content = data.get("content")
    
    # Target message for reply
    target_message_id = message.reply_to_message.id if message.reply_to_message else None
    
    me = await client.get_me()
    my_name = me.first_name
    
    # Resolve {user} placeholder
    if message.reply_to_message and message.reply_to_message.from_user:
        user_name = message.reply_to_message.from_user.first_name
    else:
        user_name = my_name
        
    await message.delete()  # Delete the trigger command
    
    if reply_type == "text":
        final_text = (
            content.replace("{user}", user_name)
            .replace("{my_name}", my_name)
        )
        await client.send_message(
            message.chat.id,
            final_text,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=target_message_id
        )
            
    elif reply_type == "sticker":
        await client.send_sticker(
            message.chat.id,
            content,
            reply_to_message_id=target_message_id
        )
            
    elif reply_type == "photo":
        await client.send_photo(
            message.chat.id,
            content,
            reply_to_message_id=target_message_id
        )
            
    elif reply_type == "animation":
        await client.send_animation(
            message.chat.id,
            content,
            reply_to_message_id=target_message_id
        )


modules_help["global_filters"] = {
    "gfilter [word]": "Reply to text/sticker/media to create public filter",
    "pfilter [word]": "Reply to text/sticker/media to create personal (manual-only) filter",
    "gfilter (w1, w2)": "Add multiple keywords to public filter",
    "pfilter (w1, w2)": "Add multiple keywords to personal filter",
    "gdel [word]": "Delete a global filter",
    "pdel [word]": "Delete a global filter",
    "g [word]": "Trigger a global filter manually (also replies if used as reply)",
    "gfilters": "List all global filters (showing public vs personal)",
}


