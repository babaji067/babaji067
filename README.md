# BioMuteBot

🤖 A Telegram bot that mutes users if they have links in their bio, name, or messages.  
Built with [python-telegram-bot](https://python-telegram-bot.org).

## Features
- Auto mute if link found in bio, name, or messages
- 3 warnings → 4th time mute
- Welcome message with buttons
- Broadcast, status, set mute duration, restart

---

## 🚀 Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/babaji067/babaji067)

---

## Manual Deploy
1. Fork or Clone this repo  
2. Add config vars in Heroku:  
   - `BOT_TOKEN`  
   - `OWNER_ID`  
   - `UPDATE_CHANNEL`  
3. Deploy with:
