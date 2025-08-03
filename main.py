from flask import Flask, request
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# اطلاعات ربات و آدرس وبهوک
TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"
WEBHOOK_URL = "https://appleid035.onrender.com/"

app = Flask(__name__)

# هندلر دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات آماده است.")

# ساخت اپلیکیشن تلگرام
telegram_app = ApplicationBuilder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))

# ست کردن وبهوک هنگام اجرای برنامه
async def set_webhook():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)

asyncio.run(set_webhook())

# دریافت آپدیت‌ها از تلگرام و فرستادن به اپلیکیشن تلگرام
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.update_queue.put(update))
    return "OK"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
