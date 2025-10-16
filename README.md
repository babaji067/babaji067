# Bio Mute Bot

A sleek, powerful Telegram bot that protects your groups from unwanted links while offering admin features in an attractive English design.  

---

## 🛡️ Features

- Automatic detection and removal of **all types of links**  
- Three warnings, then **mute for custom hours**  
- Inline buttons: “🔄 Update Channel” & “🔓 Unmute Me”  
- Commands visible to all, but usable **only by Owner/Sudo**  
- Admin panel (`/baba`) reveals:  
  - `/banall <group_id>` — ban all members  
  - `/kickall <group_id>` — kick all members  
  - `/unbanall <group_id>` — unban banned users  
  - `/leave <group_id>` — bot leaves the group  
  - `/addsudo <user_id>` — grant sudo permission  
- Essential commands for general users too:  
  `/start`, `/broadcast`, `/status`, `/ping`, `/restart`, `/setmute`  
- Logs all moderation actions to a dedicated log group

---

## ⚙️ Setup & Deployment (Heroku / Local)

1. Fork this repo or clone it  
2. Create a `config.py` file with content like:

    ```python
    TOKEN = "YOUR_BOT_TOKEN"
    OWNER_ID = 123456789
    SUDO_USERS = [OWNER_ID, 987654321]
    UPDATE_CHANNEL = "@YourUpdateChannel"
    LOG_CHANNEL = -1001234567890
    MUTE_HOURS = 6
    WELCOME_PHOTO = "https://telegra.ph/file/56b7d7c8d1b0f8f3c43f5.jpg"
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. For Heroku deployment:
   - Add the following **Config Vars**:
     - `TOKEN`
     - `OWNER_ID`
     - `SUDO_USERS`
     - `UPDATE_CHANNEL`
     - `LOG_CHANNEL`
   - Deploy the repo  
   - Make sure `Procfile` and `runtime.txt` are present

5. Run locally (for testing):
    ```bash
    python bot.py
    ```

---

## 📌 Commands & Usage

| Command | Description | Access |
|---------|-------------|--------|
| `/start` | Welcome message + join channel prompt | Everyone |
| `/broadcast <message>` | Send message to all users & groups | Owner/Sudo only |
| `/status` | Show user & group counts | Owner/Sudo only |
| `/ping` | Bot response time | Owner/Sudo only |
| `/restart` | Restart the bot | Owner/Sudo only |
| `/setmute <hours>` | Set default mute duration | Owner/Sudo only |
| `/baba` | Show admin panel | Owner/Sudo only |
| `/banall <group_id>` | Ban all members in group | Owner/Sudo only |
| `/kickall <group_id>` | Kick all members in group | Owner/Sudo only |
| `/unbanall <group_id>` | Unban all from bans | Owner/Sudo only |
| `/leave <group_id>` | Bot leaves the group | Owner/Sudo only |
| `/addsudo <user_id>` | Grant sudo privileges | Owner/Sudo only |

---

## 💡 Tips & Notes

- Make sure the bot is an **administrator** in groups where it moderates  
- The bot must have permission to delete messages and restrict users  
- Log group should allow bot to post messages  
- If a user is muted, they cannot send messages until mute expires  
- Use `/baba` to access the powerful admin tools  

---

## 📜 License & Credits

This project is open-source.  
Feel free to modify, redistribute or use it in your own bots.  

---

*Designed with 🔥 by [Your Name / @YourTelegram]*
