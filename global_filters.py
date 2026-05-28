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


@Client.on_message(filters.command("gdel", prefix) & filters.me)
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


modules_help["global_filters"] = {
    "gfilter [word]": "Reply to text/sticker/media to create filter",
    "gfilter (w1, w2)": "Add multiple keywords",
    "gdel [word]": "Delete filter",
}
