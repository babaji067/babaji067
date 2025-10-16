import os
import re
import asyncio
import logging
from datetime import timedelta, datetime
from telegram import (
    Update, ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from config import *

# ---------------- LOGGING ----------------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ---------------- DATABASES ----------------
USERS, GROUPS, WARNINGS = set(), set(), {}

# ---------------- HELPERS ----------------
def link_detected(text):
    return bool(re.search(r"(https?://|t\.me|telegram\.me|\.com|\.in)", text, re.IGNORECASE))

def owner_only(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in [OWNER_ID] + SUDO_USERS:
            await update.message.reply_text("⛔ This command is reserved for the bot owner and sudo users only.")
            return
        return await func(update, context)
    return wrapper

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    USERS.add(user.id)
    keyboard = [
        [InlineKeyboardButton("🔗 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@', '')}")],
        [InlineKeyboardButton("🤖 Add Me to Your Group", url=f"https://t.me/{context.bot.username}?startgroup=true")]
    ]
    caption = (
        f"🌐 Hey {user.first_name}!\n"
        f"Welcome aboard to **Bio Mute Bot** ⚡\n\n"
        f"I’m your personal group guardian — keeping chats clean & calm 😎"
    )
    if update.message.chat.type == "private":
        await update.message.reply_photo(photo=WELCOME_PHOTO, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))

# ---------------- FILTER LINKS ----------------
async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    if not message.text:
        return

    if link_detected(message.text):
        await message.delete()
        WARNINGS.setdefault(user.id, 0)
        WARNINGS[user.id] += 1

        if WARNINGS[user.id] < 4:
            await chat.send_message(f"🚨 Hold on {user.mention_html()}!\nLinks aren’t allowed here 💥\nThat’s warning [{WARNINGS[user.id]} / 3] — stay clean 😇", parse_mode="HTML")
        else:
            WARNINGS[user.id] = 0
            until_date = datetime.now() + timedelta(hours=MUTE_HOURS)
            await chat.restrict_member(user.id, permissions=ChatPermissions(can_send_messages=False), until_date=until_date)
            await chat.send_message(
                f"🔇 {user.mention_html()} has been muted for {MUTE_HOURS} hours ⚙️",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@','')}")],
                    [InlineKeyboardButton("🔓 Unmute Me", url=f"https://t.me/{context.bot.username}")]
                ])
            )
            try:
                await context.bot.send_message(
                    user.id,
                    f"🔇 You’ve been muted for {MUTE_HOURS} hours in {chat.title} 💬\nReason: Link sharing 🌐",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 Update Channel", url=f"https://t.me/{UPDATE_CHANNEL.replace('@','')}")],
                        [InlineKeyboardButton("🔓 Unmute Me", url=f"https://t.me/{context.bot.username}")]
                    ])
                )
            except:
                pass
            await context.bot.send_message(
                LOG_CHANNEL,
                f"🚫 {user.mention_html()} muted in <b>{chat.title}</b> for link sharing ⚠️",
                parse_mode="HTML"
            )

# ---------------- OWNER COMMANDS ----------------
@owner_only
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args and not update.message.reply_to_message:
        await update.message.reply_text("Usage: Reply or `/broadcast <message>`")
        return

    text = update.message.text.split(None, 1)[1] if len(context.args) else update.message.reply_to_message.text
    sent_user = 0
    sent_group = 0

    for user_id in list(USERS):
        try:
            await context.bot.send_message(user_id, text)
            sent_user += 1
        except:
            USERS.discard(user_id)
    for group_id in list(GROUPS):
        try:
            await context.bot.send_message(group_id, text)
            sent_group += 1
        except:
            GROUPS.discard(group_id)

    await update.message.reply_text(f"📣 Broadcast Done!\n✅ Users: {sent_user}\n✅ Groups: {sent_group}")

@owner_only
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📊 **System Vitals**\n\n"
        f"👥 Users Connected – {len(USERS)}\n"
        f"💬 Groups Linked – {len(GROUPS)}\n"
        f"⚙️ Mode – Ultra Fast ⚡",
        parse_mode="Markdown"
    )

@owner_only
async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start = datetime.now()
    msg = await update.message.reply_text("🏓 Pong!")
    end = datetime.now()
    ms = (end - start).microseconds / 1000
    await msg.edit_text(f"🏓 Pong! Response Speed: {int(ms)} ms ⚡")

@owner_only
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ System rebooting... Please wait ⚙️")
    os.execv(sys.executable, ['python'] + sys.argv)

@owner_only
async def setmute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MUTE_HOURS
    if not context.args:
        await update.message.reply_text("Usage: /setmute <hours>")
        return
    MUTE_HOURS = int(context.args[0])
    await update.message.reply_text(f"🕓 Default mute time set to {MUTE_HOURS} hours ⚡")

# ---------------- ADMIN PANEL ----------------
@owner_only
async def baba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👑 **Admin Command Panel**\n\n"
        "/banall <group_id> – Ban everyone ⚔️\n"
        "/kickall <group_id> – Kick all members 💨\n"
        "/unbanall <group_id> – Clear bans 🔄\n"
        "/leave <group_id> – Exit a group 👋\n"
        "/addsudo <user_id> – Grant power ⚡",
        parse_mode="Markdown"
    )

# ---------------- BAN/KICK ----------------
@owner_only
async def banall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /banall <group_id>")
        return
    gid = int(context.args[0])
    members = await context.bot.get_chat_administrators(gid)
    for m in members:
        if not m.user.is_bot:
            try:
                await context.bot.ban_chat_member(gid, m.user.id)
            except:
                pass
    await update.message.reply_text(f"⚔️ All members banned in {gid}")

@owner_only
async def kickall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /kickall <group_id>")
        return
    gid = int(context.args[0])
    async for member in context.bot.get_chat_administrators(gid):
        if not member.user.is_bot:
            try:
                await context.bot.ban_chat_member(gid, member.user.id)
                await asyncio.sleep(0.2)
                await context.bot.unban_chat_member(gid, member.user.id)
            except:
                pass
    await update.message.reply_text(f"💨 All members kicked in {gid}")

# ---------------- HANDLERS ----------------
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("setmute", setmute))
    app.add_handler(CommandHandler("baba", baba))
    app.add_handler(CommandHandler("banall", banall))
    app.add_handler(CommandHandler("kickall", kickall))

    logging.info("🚀 Bio Mute Bot is now running!")
    app.run_polling()

if __name__ == "__main__":
    main()
