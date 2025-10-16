# 🤖 BioMuteBot

A smart Telegram bot that automatically **detects and mutes users** who share unwanted links or usernames in your group.  
Protect your chats from spam and self-promo — all on auto-mode ⚡

---

## 🚀 Deploy to Heroku

You can deploy this bot to Heroku with one click below 👇

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/babaji067/babaji067)

---

## 🧩 Required Files

| File | Description |
|------|--------------|
| `bot.py` | Main bot script |
| `config.py` | Stores token, owner ID, and channel details |
| `requirements.txt` | Python dependencies |
| `Procfile` | Start command for Heroku |
| `runtime.txt` | Python version used |
| `app.json` | Heroku app metadata |
| `.env` *(optional)* | Local environment variables |

---

## ⚙️ Local Setup (Optional)

If you want to run it locally or in Pydroid3:

```bash
git clone https://github.com/babaji067/babaji067.git
cd babaji067
pip install -r requirements.txt
python bot.py
