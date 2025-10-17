import os

# ✅ Telegram Bot Token (from @BotFather)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# ✅ Bot Owner ID (from @userinfobot)
OWNER_ID = int(os.getenv("OWNER_ID", 1234567890))

# ✅ Update Channel username (without https://)
UPDATE_CHANNEL = os.getenv("UPDATE_CHANNEL", "@biomute_bot")
