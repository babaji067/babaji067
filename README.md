# 🤖 BioMuteBot

A smart Telegram bot that automatically **detects and mutes users** who share unwanted links, usernames, or spam messages in your groups.  
Protect your community with style — built using **python-telegram-bot v20+** 💥

---

## ✨ Features

- 🚫 Detects links in messages or bios  
- ⚠️ Gives 3 warnings → then mutes on 4th offense  
- 🔇 Custom mute duration via `/setmute`  
- 💬 Private mute notifications to users  
- 📢 `/broadcast` to groups + users (with support for reply messages)  
- 🧑‍💻 Admin-only commands (ban/kick/restart/status)  
- 🧾 Auto-remove inactive users/groups from cache  
- ⚙️ Simple Heroku deploy setup  

---

## 🧩 Required Files

| File | Description |
|------|--------------|
| `bot.py` | Main bot file |
| `config.py` | Stores your bot token, owner ID, etc. |
| `requirements.txt` | Dependencies list |
| `Procfile` | Heroku start command |
| `runtime.txt` | Python version |
| `app.json` | For Heroku deploy button |
| `.env` *(optional)* | Local environment variables |

---

## ⚙️ Installation (Local)

```bash
git clone https://github.com/babaji067/babaji067.git
cd babaji067
pip install -r requirements.txt
python bot.py
