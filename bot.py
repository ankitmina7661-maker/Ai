import os
import re
import logging
import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer

import anthropic
from dotenv import load_dotenv
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

load_dotenv()

TG_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", "10"))  # kitne purane messages yaad rakhe
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "700"))
SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "Tum ek helpful, friendly AI assistant ho jo Telegram group mein hai. "
    "User jis language mein likhe (Hindi, Hinglish ya English) usi mein jawab do. "
    "Jawab chhote aur clear rakho, Telegram chat ke hisaab se.",
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO
)
log = logging.getLogger("bot")

client = anthropic.AsyncAnthropic(api_key=API_KEY)
history = defaultdict(list)  # chat_id -> [{"role":..., "content":...}]


def trim(chat_id: int):
    h = history[chat_id]
    if len(h) > MAX_HISTORY:
        del h[: len(h) - MAX_HISTORY]
    while h and h[0]["role"] != "user":
        h.pop(0)


def chunks(text: str, size: int = 4000):
    for i in range(0, len(text), size):
        yield text[i : i + size]


async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "Namaste! Main AI bot hu. Group mein mujhe @mention karo ya mere "
        "message ka reply do. /reset se purani baat bhula dunga."
    )


async def reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    history.pop(update.effective_chat.id, None)
    await update.effective_message.reply_text("Done, memory clear kar di.")


async def on_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not msg.text:
        return

    text = msg.text
    bot_username = ctx.bot.username

    # Group mein sirf mention ya reply par jawab do
    if chat.type != "private":
        mentioned = f"@{bot_username}".lower() in text.lower()
        replied = (
            msg.reply_to_message
            and msg.reply_to_message.from_user
            and msg.reply_to_message.from_user.id == ctx.bot.id
        )
        if not (mentioned or replied):
            return
        text = re.sub(f"@{bot_username}", "", text, flags=re.IGNORECASE).strip()

    if not text:
        return

    name = msg.from_user.first_name if msg.from_user else "User"
    user_content = f"{name}: {text}" if chat.type != "private" else text

    await ctx.bot.send_chat_action(chat.id, ChatAction.TYPING)

    history[chat.id].append({"role": "user", "content": user_content})
    trim(chat.id)

    try:
        resp = await client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=history[chat.id],
        )
        answer = "".join(b.text for b in resp.content if b.type == "text").strip()
        if not answer:
            answer = "Kuch samajh nahi aaya, dobara bolo."
        history[chat.id].append({"role": "assistant", "content": answer})
        for part in chunks(answer):
            await msg.reply_text(part)
    except Exception as e:
        log.exception("Claude error: %s", e)
        history[chat.id].pop()  # fail hua message history se hata do
        await msg.reply_text("Abhi kuch problem aa gayi, thodi der baad try karo.")


# Free hosts (Render etc.) ko ek open port chahiye hota hai
class Health(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


def start_health_server():
    port = os.getenv("PORT")
    if not port:
        return
    server = HTTPServer(("0.0.0.0", int(port)), Health)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("Health server on port %s", port)


def main():
    start_health_server()
    app = ApplicationBuilder().token(TG_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    log.info("Bot chalu ho gaya...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
