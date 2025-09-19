# BioMuteBot

🤖 **BioMuteBot** एक Telegram bot है जो groups में automatically users को mute कर देता है  
अगर उनके **bio, name या message में link** होता है।  

---

## ✨ Features
- `/start` → Force channel join + welcome photo + buttons  
- Bio या message में link मिले तो:
  - 3 warnings → 4th बार auto mute (custom hours)  
  - Mute notification + unmute button  
- New user join करे और उसके **name/bio में link** हो → Permanent mute  
- Group + DM दोनों में notification  
- Owner commands:
  - `/broadcast` → सभी users को message भेजो  
  - `/status` → Groups और users की count  
  - `/setmute <hours>` → Mute duration बदलो  
  - `/restart` → Bot restart करो  

---

## 🚀 Deploy to Heroku

नीचे button पर click करके आप सीधे Heroku पर deploy कर सकते हो 👇  

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/babaji067/babaji067)

---

## 🔧 Manual Deploy (Heroku / VPS)

1. इस repo को clone या fork करें:  
   ```bash
   git clone https://github.com/babaji067/babaji067
   cd babaji067
