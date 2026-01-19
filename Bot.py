import asyncio
import os
import re
import sys
from datetime import datetime, timedelta
from collections import defaultdict

from motor.motor_asyncio import AsyncIOMotorClient
from telegram import (
    Update,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.error import RetryAfter
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters
)

# ================== CONFIG ==================

BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL").lstrip("@")
MONGO_URI = os.environ.get("MONGO_URI")

# ================== MONGO ==================

mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo.biomutebot

users_col = db.users
groups_col = db.groups
warns_col = db.warns
settings_col = db.settings

# ================== SPEED ==================

LINK_REGEX = re.compile(
    r"(http|https|www\.|t\.me|telegram\.me|instagram\.com|facebook\.com)",
    re.I
)

bio_cache = {}              # user_id -> (bio, timestamp)
warn_cache = defaultdict(int)
mute_duration = 2           # default (hours)

# ================== HELPERS ==================

def has_link(text: str) -> bool:
    return bool(text and LINK_REGEX.search(text))


async def get_bio(context, user_id: int) -> str:
    now = datetime.utcnow()
    if user_id in bio_cache:
        bio, ts = bio_cache[user_id]
        if now - ts < timedelta(minutes=5):
            return bio
    try:
        chat = await context.bot.get_chat(user_id)
        bio = chat.bio or ""
        bio_cache[user_id] = (bio, now)
        return bio
    except:
        return ""


async def save_user(user):
    await users_col.update_one(
        {"_id": user.id},
        {"$set": {"name": user.first_name}},
        upsert=True
    )


async def save_chat(chat):
    if chat.type in ["group", "supergroup"]:
        await groups_col.update_one(
            {"_id": chat.id},
            {"$set": {"title": chat.title}},
            upsert=True
        )


async def load_settings():
    global mute_duration
    s = await settings_col.find_one({"_id": "config"})
    if s:
        mute_duration = s.get("mute_duration", 2)

# ================== CORE ==================

async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text

    if user.is_bot:
        return

    await save_user(user)
    await save_chat(chat)

    # 🔴 Link in FIRST NAME → Permanent mute
    if has_link(user.first_name):
        try:
            await context.bot.restrict_chat_member(
                chat.id,
                user.id,
                ChatPermissions(can_send_messages=False)
            )
        except:
            pass
        return

    # 🔴 Link in message or bio
    if has_link(text) or has_link(await get_bio(context, user.id)):
        try:
            await update.message.delete()
        except:
            pass

        warn_cache[user.id] += 1
        await warns_col.update_one(
            {"_id": user.id},
            {"$inc": {"count": 1}},
            upsert=True
        )

        if warn_cache[user.id] < 4:
            msg = f"⚠️ {user.first_name}, links not allowed ({warn_cache[user.id]}/3)"
            try:
                await chat.send_message(msg)
                await context.bot.send_message(user.id, msg)
            except:
                pass
        else:
            until = datetime.utcnow() + timedelta(hours=mute_duration)
            try:
                await context.bot.restrict_chat_member(
                    chat.id,
                    user.id,
                    ChatPermissions(can_send_messages=False),
                    until_date=until
                )
            except:
                pass
            warn_cache[user.id] = 0
            await warns_col.delete_one({"_id": user.id})

# ================== COMMANDS ==================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_user(update.effective_user)
    await save_chat(update.effective_chat)

    try:
        member = await context.bot.get_chat_member(
            f"@{UPDATE_CHANNEL}",
            update.effective_user.id
        )
        if member.status not in ["member", "administrator", "creator"]:
            raise Exception
    except:
        return await update.message.reply_text(
            "📛 Please join the update channel first.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔗 Join Channel",
                 url=f"https://t.me/{UPDATE_CHANNEL}")]
            ])
        )

    await update.message.reply_text(
        "━━━ ✦ ʙɪᴏᴍᴜᴛᴇʙᴏᴛ ✦ ━━━\n"
        "✅ Bot is active\n"
        "🛡️ Anti bio & link system ON",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(
                "➕ Add Me To Group",
                url=f"https://t.me/{context.bot.username}?startgroup=true"
            )],
            [InlineKeyboardButton(
                "🔄 Update Channel",
                url=f"https://t.me/{UPDATE_CHANNEL}"
            )]
        ])
    )


async def set_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mute_duration
    if update.effective_user.id != OWNER_ID:
        return
    if not context.args or not context.args[0].isdigit():
        return await update.message.reply_text("/setmute <hours>")
    mute_duration = int(context.args[0])
    await settings_col.update_one(
        {"_id": "config"},
        {"$set": {"mute_duration": mute_duration}},
        upsert=True
    )
    await update.message.reply_text(f"✅ Mute set to {mute_duration} hours")


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    users = await users_col.count_documents({})
    groups = await groups_col.count_documents({})
    await update.message.reply_text(
        f"📊 Status\n\n👤 Users: {users}\n👥 Groups: {groups}"
    )


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("♻️ Restarting bot...")
    await mongo.close()
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ================== BROADCAST ==================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    msg = update.message
    text_low = msg.text.lower()

    to_users = "-user" in text_low or "-wfuser" in text_low
    to_chats = "-wfchat" in text_low or not to_users
    pin = "-pin" in text_low
    pin_loud = "-pinloud" in text_low

    photo_id = caption = message_text = None
    reply_markup = None

    if msg.reply_to_message:
        r = msg.reply_to_message
        reply_markup = r.reply_markup
        if r.photo:
            photo_id = r.photo[-1].file_id
            caption = r.caption
        elif r.text:
            message_text = r.text
    else:
        if not context.args:
            return await msg.reply_text(
                "❌ Usage:\n/broadcast <text>\nReply message + /broadcast"
            )
        message_text = msg.text.split(None, 1)[1]
        for f in ["-pin", "-pinloud", "-user", "-wfchat", "-wfuser"]:
            message_text = message_text.replace(f, "").strip()

    status = await msg.reply_text(
        "━━━ ✦ ʙʀᴏᴀᴅᴄᴀsᴛ ✦ ━━━\n"
        "➤ Status : Running..."
    )

    sent = failed = pinned = 0
    targets = []

    if to_chats:
        async for g in groups_col.find({}, {"_id": 1}):
            targets.append((g["_id"], False))
    if to_users:
        async for u in users_col.find({}, {"_id": 1}):
            targets.append((u["_id"], True))

    for target_id, is_user in targets:
        try:
            if photo_id:
                m = await context.bot.send_photo(
                    target_id,
                    photo_id,
                    caption=caption,
                    reply_markup=reply_markup
                )
            else:
                m = await context.bot.send_message(
                    target_id,
                    message_text,
                    reply_markup=reply_markup
                )

            if not is_user and (pin or pin_loud):
                try:
                    await m.pin(disable_notification=not pin_loud)
                    pinned += 1
                except:
                    pass

            sent += 1
            await asyncio.sleep(0.25)

        except RetryAfter as e:
            await asyncio.sleep(e.retry_after)
        except:
            failed += 1

    await status.edit_text(
        "━━━ ✦ ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇ ✦ ━━━\n\n"
        f"✔ Sent   : {sent}\n"
        f"📌 Pinned : {pinned}\n"
        f"❌ Failed : {failed}"
    )

# ================== MAIN ==================

async def main():
    await load_settings()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setmute", set_mute))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_user))

    print("🤖 BioMuteBot FAST MongoDB MODE ON")
    await app.run_polling()


if __name__ == "__main__":
    asyncio.run(main()) 
