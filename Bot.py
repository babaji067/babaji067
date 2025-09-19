import os
import re
import logging
import nest_asyncio
from datetime import datetime, timedelta
from telegram import (
    Update, ChatPermissions, InlineKeyboardButton,
    InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ========== CONFIG ==========
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))
UPDATE_CHANNEL = os.environ.get("UPDATE_CHANNEL", None)

SUDO_USERS = set()  # Dynamic sudo system

USERS, GROUPS, WARNS = {}, {}, {}
MUTE_HOURS = 4  # Default mute duration

# ========== LOGGING ==========
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

nest_asyncio.apply()

# ========== HELPERS ==========
def is_sudo(uid: int) -> bool:
    return uid == OWNER_ID or uid in SUDO_USERS

async def force_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if UPDATE_CHANNEL:
        try:
            member = await context.bot.get_chat_member(UPDATE_CHANNEL, update.effective_user.id)
            if member.status in ["left", "kicked"]:
                btn = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("📢 Join Update Channel", url=f"https://t.me/{UPDATE_CHANNEL}")]]
                )
                await update.message.reply_text(
                    "⚠️ पहले Update Channel Join करो फिर bot use कर पाओगे!",
                    reply_markup=btn
                )
                return False
        except Exception as e:
            logging.warning(f"Force join error: {e}")
    return True

async def mute_user(chat_id, user_id, context, reason="Link detected"):
    until = datetime.now() + timedelta(hours=MUTE_HOURS)
    await context.bot.restrict_chat_member(
        chat_id,
        user_id,
        ChatPermissions(can_send_messages=False),
        until_date=until
    )
    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔓 Unmute Me", url=f"https://t.me/{context.bot.username}")],
        [InlineKeyboardButton("📢 Update Channel", url=f"https://t.me/{UPDATE_CHANNEL}")]
    ])
    return btn

# ========== MAIN COMMANDS ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await force_join(update, context): return
    USERS[update.effective_user.id] = True
    if update.effective_chat.type in ["group", "supergroup"]:
        GROUPS[update.effective_chat.id] = True

    btn = InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Add Me To Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("📢 Update Channel", url=f"https://t.me/{UPDATE_CHANNEL}")]
    ])
    photo_path = "welcome.jpg"
    if os.path.exists(photo_path):
        await update.message.reply_photo(InputFile(photo_path), caption=f"👋 Welcome {update.effective_user.first_name}!", reply_markup=btn)
    else:
        await update.message.reply_text(f"👋 Welcome {update.effective_user.first_name}!", reply_markup=btn)

async def check_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    user = msg.from_user
    if re.search(r"(t\.me/|http|www\.|@)", msg.text or ""):
        await msg.delete()
        count = WARNS.get(user.id, 0) + 1
        WARNS[user.id] = count
        if count >= 4:
            btn = await mute_user(msg.chat_id, user.id, context)
            await msg.reply_text(f"🔇 {user.mention_html()} Muted {MUTE_HOURS} hours (reason: link)", parse_mode="HTML", reply_markup=btn)
        else:
            await msg.reply_text(f"⚠️ {user.mention_html()} Warning {count}/3 (reason: link)", parse_mode="HTML")

# ========== OWNER/SUDO COMMANDS ==========
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")
    text = " ".join(context.args)
    sent, failed = 0, 0
    for uid in list(USERS.keys()) + list(GROUPS.keys()):
        try:
            await context.bot.send_message(uid, text)
            sent += 1
        except:
            failed += 1
    await update.message.reply_text(f"📢 Broadcast Done\n✅ Sent: {sent}\n❌ Failed: {failed}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    await update.message.reply_text(f"👥 Users: {len(USERS)}\n👥 Groups: {len(GROUPS)}")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    start = datetime.now()
    m = await update.message.reply_text("🏓 Pong...")
    end = datetime.now()
    latency = (end - start).microseconds // 1000
    await m.edit_text(f"🏓 Pong: {latency} ms")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    await update.message.reply_text("♻️ Restarting...")
    os.execl(sys.executable, sys.executable, *sys.argv)

async def leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    await update.message.reply_text("👋 Leaving this group...")
    await context.bot.leave_chat(update.effective_chat.id)

async def addsudo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    if not context.args:
        return await update.message.reply_text("Usage: /addsudo <user_id>")
    uid = int(context.args[0])
    SUDO_USERS.add(uid)
    await update.message.reply_text(f"✅ Added {uid} as SUDO")

async def baba(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    text = """
📌 Available Commands:
/broadcast <msg>
/status
/ping
/restart
/banall
/unbanall
/kickall
/leave
/addsudo <id>
    """
    await update.message.reply_text(text)

# ========== GROUP ADMIN ACTIONS ==========
async def banall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    chat = update.effective_chat
    async for member in context.bot.get_chat_administrators(chat.id):
        admin_ids = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
        async for member in context.bot.get_chat_members(chat.id):
            if member.user.id not in admin_ids:
                try:
                    await context.bot.ban_chat_member(chat.id, member.user.id)
                except: pass
    await update.message.reply_text("✅ All non-admins banned.")

async def unbanall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    chat = update.effective_chat
    banned = await context.bot.get_chat_administrators(chat.id)
    for u in banned:
        try: await context.bot.unban_chat_member(chat.id, u.user.id)
        except: pass
    await update.message.reply_text("✅ All unbanned.")

async def kickall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    chat = update.effective_chat
    admin_ids = [a.user.id for a in await context.bot.get_chat_administrators(chat.id)]
    async for member in context.bot.get_chat_members(chat.id):
        if member.user.id not in admin_ids:
            try: await context.bot.ban_chat_member(chat.id, member.user.id)
            except: pass
    await update.message.reply_text("✅ All non-admins kicked.")

# ========== MAIN ==========
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Normal
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_message))

    # Owner/Sudo
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("leave", leave))
    app.add_handler(CommandHandler("addsudo", addsudo))
    app.add_handler(CommandHandler("baba", baba))

    # Group admin
    app.add_handler(CommandHandler("banall", banall))
    app.add_handler(CommandHandler("unbanall", unbanall))
    app.add_handler(CommandHandler("kickall", kickall))

    app.run_polling()

if __name__ == "__main__":
    main()
