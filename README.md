# 🤖 Bio Mute Bot

A stylish and powerful Telegram bot that automatically moderates messages, removes link spam, and offers advanced admin tools — all with a beautiful, fast, and smooth design.  

---

## ✨ **Key Features**

- 🔗 Detects **all types of links** in bio or messages  
- ⚠️ 3 warnings → then automatic **custom hour mute**  
- 🧊 Mute message includes **Update Channel + Unmute Me** buttons  
- 🖼️ Attractive photo welcome message on /start  
- 📢 Full broadcast support — photo, text, reply, or link  
- ⚙️ Owner & Sudo-only commands panel (`/baba`)  
- 🧮 Auto database cleanup — removes left users/groups  
- ⚡ Fast, lightweight, and Heroku-ready  

---

## 🧩 **Commands Overview**

| Command | Description | Access |
|----------|--------------|--------|
| `/start` | Welcome message + join update channel button | Everyone |
| `/broadcast` | Send message/photo/link to all users & groups | Owner / Sudo |
| `/status` | Show total users & groups count | Owner / Sudo |
| `/ping` | Check bot’s response speed (ms) | Owner / Sudo |
| `/restart` | Restart the bot | Owner / Sudo |
| `/setmute <hours>` | Change default mute duration | Owner / Sudo |
| `/baba` | Show admin panel (banall, kickall, etc.) | Owner / Sudo |
| `/banall <group_id>` | Ban all users in a group | Owner / Sudo |
| `/kickall <group_id>` | Kick all non-admin users | Owner / Sudo |
| `/unbanall <group_id>` | Unban all banned users | Owner / Sudo |
| `/leave <group_id>` | Make bot leave the group | Owner / Sudo |
| `/addsudo <user_id>` | Grant sudo access | Owner Only |

---

## ⚙️ **Setup Guide**

### 🔧 Step 1: Create a Telegram Bot
- Go to [@BotFather](https://t.me/BotFather)
- Use `/newbot` → get your **BOT TOKEN**

### 📂 Step 2: Create `config.py`
Add your configuration in a file named `config.py`:

```python
TOKEN = "YOUR_BOT_TOKEN"
OWNER_ID = 123456789
SUDO_USERS = [OWNER_ID, 987654321]
UPDATE_CHANNEL = "@YourUpdateChannel"
LOG_CHANNEL = -1001234567890
MUTE_HOURS = 6
WELCOME_PHOTO = "https://telegra.ph/file/56b7d7c8d1b0f8f3c43f5.jpg"
