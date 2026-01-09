import nest_asyncio
import asyncio
import re
import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient

from telegram import (
    Update, ChatPermissions,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

nest_asyncio.apply()

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL")
MONGO_URI = os.environ.get("MONGO_URI")

LOG_GROUP_ID = -5205587291   # logging group
mute_duration = 2           # global mute (owner sets)
# =========================================


# ================= MONGO ==================
mongo = MongoClient(MONGO_URI)
db = mongo.biomutebot
users_db = db.users
groups_db = db.groups
warns_db = db.warns
# =========================================


# ================= LANG ===================
LANG = {
    "warn": {
        "en": "⚠️ {name}, links are not allowed! Warning {count}/3",
        "hi": "⚠️ {name}, link allowed nahi hai! Warning {count}/3"
    },
    "muted": {
        "en": "🔇 Muted for {h} hour(s)",
        "hi": "🔇 {h} ghante ke liye mute"
    }
}
DEFAULT_LANG = "en"
# =========================================


def has_link(text: str) -> bool:
    return bool(re.search(r"(http|www\.|t\.me|instagram\.com|facebook\.com)", text, re.I))


async def log(context, text):
    try:
        await context.bot.send_message(LOG_GROUP_ID, text)
    except:
        pass


async def get_bio(context, user_id):
    try:
        chat = await context.bot.get_chat(user_id)
        return chat.bio or ""
    except:
        return ""


def save_user(uid):
    users_db.update_one({"user_id": uid}, {"$set": {"user_id": uid}}, upsert=True)


def save_group(gid):
    groups_db.update_one({"group_id": gid}, {"$set": {"group_id": gid}}, upsert=True)


def add_warn(uid):
    doc = warns_db.find_one({"user_id": uid})
    if not doc:
        warns_db.insert_one({"user_id": uid, "count": 1})
        return 1
    count = doc["count"] + 1
    warns_db.update_one({"user_id": uid}, {"$set": {"count": count}})
    return count


def reset_warn(uid):
    warns_db.delete_one({"user_id": uid})


# ================= MAIN CHECK =================
async def check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.message.from_user
    chat = update.effective_chat
    text = update.message.text or ""

    if chat.type in ["group", "supergroup"]:
        save_group(chat.id)
    else:
        save_user(user.id)

    try:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status in ["administrator", "creator"]:
            return
    except:
        return

    # 🔴 FIRST NAME LINK → PERMANENT MUTE
    if has_link(user.first_name):
        await context.bot.restrict_chat_member(
            chat.id, user.id,
            ChatPermissions(can_send_messages=False)
        )
        await log(context,
            f"🚫 PERMANENT MUTE\n👤 {user.first_name}\n🆔 {user.id}\n👥 {chat.id}"
        )
        return

    # 🔶 BIO / MESSAGE LINK
    if has_link(text) or has_link(await get_bio(context, user.id)):
        try:
            await update.message.delete()
        except:
            pass

        count = add_warn(user.id)

        if count < 4:
            msg = LANG["warn"][DEFAULT_LANG].format(
                name=user.first_name, count=count
            )
            await chat.send_message(msg)
            await log(context,
                f"⚠️ WARNING {count}/3\n👤 {user.first_name}\n👥 {chat.id}"
            )
        else:
            until = datetime.utcnow() + timedelta(hours=mute_duration)
            await context.bot.restrict_chat_member(
                chat.id, user.id,
                ChatPermissions(can_send_messages=False),
                until_date=until
            )

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Update Channel",
                    url=f"https://t.me/{UPDATE_CHANNEL.lstrip('@')}")],
                [InlineKeyboardButton("🔓 Unmute",
                    url=f"https://t.me/{context.bot.username}")]
            ])

            await chat.send_message(
                LANG["muted"][DEFAULT_LANG].format(h=mute_duration),
                reply_markup=keyboard
            )

            await log(context,
                f"🔇 MUTED\n👤 {user.first_name}\n🆔 {user.id}\n👥 {chat.id}\n⏱ {mute_duration}h"
            )
            reset_warn(user.id)


# ================= COMMANDS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id)

    try:
        member = await context.bot.get_chat_member(UPDATE_CHANNEL, user.id)
        if member.status not in ["member", "administrator", "creator"]:
            raise Exception
    except:
        return await update.message.reply_text(
            "📛 Join update channel first.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel",
                    url=f"https://t.me/{UPDATE_CHANNEL.lstrip('@')}")]
            ])
        )

    await update.message.reply_text("👋 Welcome to BioMuteBot")


async def set_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global mute_duration
    if update.effective_user.id != OWNER_ID:
        return
    mute_duration = int(context.args[0])
    await update.message.reply_text(f"✅ Mute set to {mute_duration}h")
    await log(context, f"👑 OWNER SET MUTE = {mute_duration}h")


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("♻️ Restarting bot…")
    await log(context, "♻️ BOT RESTARTED")
    os.execl(sys.executable, sys.executable, *sys.argv)


async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    sent = failed = 0
    text = update.message.reply_to_message.text if update.message.reply_to_message else " ".join(context.args)

    targets = [x["group_id"] for x in groups_db.find()] + \
              [x["user_id"] for x in users_db.find()]

    for tid in targets:
        try:
            await context.bot.send_message(tid, text)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"📢 Broadcast done\n✅ {sent} | ❌ {failed}")
    await log(context, f"📢 BROADCAST\n✅ {sent} | ❌ {failed}")


# ================= RUN =====================
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setmute", set_mute))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.ALL, check_user))

    await app.run_polling()

asyncio.run(main())
