import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler

TOKEN = os.getenv("8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip()

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

# دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات شما با وبهوک روی Render فعال شد.")

application.add_handler(CommandHandler("start", start))

# دریافت پیام‌ها
async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await update.message.reply_text(f"پیام شما: {text}")

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

# مسیر وبهوک تلگرام
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK"

# ست کردن وبهوک به تلگرام
@app.route("/")
async def set_webhook():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    return "Webhook set!"

if __name__ == "__main__":
    application.run_polling()  # فقط برای تست لوکال
