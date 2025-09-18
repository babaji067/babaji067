import os
import re
import sys
import asyncio
import logging
from datetime import timedelta, datetime
from telegram import (
    Update, ChatPermissions, InlineKeyboardButton,
    InlineKeyboardMarkup, ChatInviteLink
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------------- ENVIRONMENT VARS ----------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
SUDO_IDS = list(map(int, os.environ.get("SUDO_IDS", "").split())) if os.environ.get("SUDO_IDS") else []
UPDATE_CHANNEL = "@biomute_bot"

# ---------------- GLOBAL STORAGE ----------------
WARN_LIMIT = 3
MUTE_HOURS = int(os.environ.get("MUTE_HOURS", 6))
warns = {}
groups = set()
users = set()
mute_logs = []
group_logs = []

# ---------------- HELPERS ----------------
def is_sudo(uid: int) -> bool:
    return uid == OWNER_ID or uid in SUDO_IDS

async def force_subscribe(user_id: int, client) -> bool:
    try:
        member = await client.get_chat_member(UPDATE_CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    if chat_id < 0:
        groups.add(chat_id)
    else:
        users.add(user.id)

    if not await force_subscribe(user.id, context.bot):
        await update.message.reply_text(
            f"Hello {user.first_name}!\nPlease join our update channel first:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.strip('@')}")]]
            )
        )
        return

    photo_url = "https://i.ibb.co/pw4wRpG/deadpool.jpg"
    buttons = [
        [InlineKeyboardButton("Kidnap Me", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.strip('@')}")]
    ]
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=photo_url,
        caption=f"🔥 Welcome {user.first_name}! 🔥\n\nI am BioMute Bot.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------------- WARN / MUTE ----------------
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message or not user or is_sudo(user.id):
        return

    bio = (user.bio or "").lower()
    text = (message.text or "").lower()

    if ("http" in bio or "@" in bio or "http" in text or "t.me" in text):
        warns.setdefault(chat.id, {}).setdefault(user.id, 0)
        warns[chat.id][user.id] += 1

        if warns[chat.id][user.id] <= WARN_LIMIT:
            try:
                await message.delete()
            except:
                pass
            await chat.send_message(
                f"⚠️ {user.mention_html()} warned ({warns[chat.id][user.id]}/{WARN_LIMIT}) for link use.",
                parse_mode="HTML"
            )
        else:
            try:
                await message.delete()
            except:
                pass
            until = datetime.now() + timedelta(hours=MUTE_HOURS)
            await chat.restrict_member(user.id, ChatPermissions(can_send_messages=False), until_date=until)

            btns = [[
                InlineKeyboardButton("Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.strip('@')}"),
                InlineKeyboardButton("Unmute Me", url=f"https://t.me/{context.bot.username}")
            ]]
            try:
                await context.bot.send_message(
                    user.id,
                    f"🔇 You are muted for {MUTE_HOURS} hours in {chat.title}!",
                    reply_markup=InlineKeyboardMarkup(btns)
                )
            except:
                pass

            log_entry = f"Muted {user.mention_html()} (ID {user.id}) in {chat.title} ({chat.id})"
            mute_logs.append(log_entry)
            await chat.send_message(f"🔇 {user.mention_html()} muted for {MUTE_HOURS}h!", parse_mode="HTML")

# ---------------- COMMANDS ----------------
async def sethour(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    global MUTE_HOURS
    try:
        MUTE_HOURS = int(context.args[0])
        await update.message.reply_text(f"✅ Mute duration set to {MUTE_HOURS} hours.")
    except:
        await update.message.reply_text("❌ Usage: /sethour <hours>")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    start = datetime.now()
    msg = await update.message.reply_text("Pinging...")
    end = datetime.now()
    await msg.edit_text(f"🏓 Pong: {(end - start).microseconds // 1000} ms")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    text = f"📊 Status:\nUsers: {len(users)}\nGroups: {len(groups)}\nMute Hours: {MUTE_HOURS}"
    await update.message.reply_text(text)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("Usage: /broadcast <text> or reply to message")
        return

    sent, failed = 0, 0
    targets = list(users | groups)
    text = " ".join(context.args) if context.args else None

    for target in targets:
        try:
            if update.message.reply_to_message and update.message.reply_to_message.photo:
                file_id = update.message.reply_to_message.photo[-1].file_id
                caption = update.message.reply_to_message.caption or text
                await context.bot.send_photo(target, file_id, caption=caption)
            elif text:
                await context.bot.send_message(target, text)
            sent += 1
        except:
            failed += 1

    await update.message.reply_text(f"✅ Broadcast done\nDelivered: {sent}\nFailed: {failed}")

async def banall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    chat = update.effective_chat
    members = await chat.get_administrators()
    admin_ids = [m.user.id for m in members]
    count = 0
    async for member in chat.get_members():
        if member.user.id not in admin_ids and not member.user.is_bot:
            try:
                await chat.ban_member(member.user.id)
                count += 1
            except:
                pass
    await update.message.reply_text(f"✅ Banned {count} users.")

async def unbanall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    chat = update.effective_chat
    count = 0
    async for member in chat.get_members():
        try:
            await chat.unban_member(member.user.id)
            count += 1
        except:
            pass
    await update.message.reply_text(f"✅ Unbanned {count} users.")

async def kickall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    chat = update.effective_chat
    members = await chat.get_administrators()
    admin_ids = [m.user.id for m in members]
    count = 0
    async for member in chat.get_members():
        if member.user.id not in admin_ids and not member.user.is_bot:
            try:
                await chat.ban_member(member.user.id)
                await asyncio.sleep(0.1)
                await chat.unban_member(member.user.id)
                count += 1
            except:
                pass
    await update.message.reply_text(f"✅ Kicked {count} users.")

async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        uid = int(context.args[0])
        if uid not in SUDO_IDS:
            SUDO_IDS.append(uid)
            await update.message.reply_text(f"✅ {uid} added as sudo.")
    except:
        await update.message.reply_text("❌ Usage: /addsudo <user_id>")

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    await update.message.reply_text("👋 Leaving group...")
    await context.bot.leave_chat(update.effective_chat.id)

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    await update.message.reply_text("♻️ Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)

async def baba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    text = """
⚡ Commands List ⚡
/sethour <h> - Set mute hours
/ping - Check ping
/status - Bot stats
/broadcast <msg> - Broadcast
/banall - Ban all
/unbanall - Unban all
/kickall - Kick non-admins
/addsudo <id> - Add sudo
/leave - Leave group
/restart - Restart bot
"""
    await update.message.reply_text(text)

# ---------------- LOGS ----------------
async def log_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if update.message.new_chat_members:
        for u in update.message.new_chat_members:
            log_entry = f"➕ Added to group {chat.title} ({chat.id})"
            group_logs.append(log_entry)
    if update.message.left_chat_member:
        log_entry = f"➖ Removed from group {chat.title} ({chat.id})"
        group_logs.append(log_entry)

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sethour", sethour))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("banall", banall))
    app.add_handler(CommandHandler("unbanall", unbanall))
    app.add_handler(CommandHandler("kickall", kickall))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("baba", baba))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))
    app.add_handler(MessageHandler(filters.ALL, log_group))

    app.run_polling()

if __name__ == "__main__":
    main()
