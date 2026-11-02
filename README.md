# Telegram AI Group Bot (Claude)

## 1. Bot banao
1. Telegram mein **@BotFather** -> `/newbot` -> token copy karo.
2. `/setprivacy` -> apna bot -> **Disable**.
3. Bot ko group mein add karo.

## 2. API key
https://console.anthropic.com se API key lo.

## 3. Local chalana
```
pip install -r requirements.txt
cp .env.example .env     # .env mein token aur key bharo
python bot.py
```

## 4. Free host par deploy (Render / Railway / koyeb)
- Code ko GitHub repo mein push karo (`.env` push mat karna).
- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Environment variables mein `TELEGRAM_BOT_TOKEN` aur `ANTHROPIC_API_KEY` daalo.
- Render free "Web Service" use karo to bot ek port khol deta hai (PORT auto set hota hai).
  Free plan 15 min idle par sleep ho jata hai, to https://uptimerobot.com se
  apne service URL ko har 5 min ping karwao.

## Use kaise karein
- Group mein `@your_bot_username sawal` likho, ya bot ke message ka reply do.
- Private chat mein seedha message karo.
- `/reset` = memory clear, `/start` = intro.

## Customize
`.env` mein `SYSTEM_PROMPT` badal kar bot ki personality set karo.
