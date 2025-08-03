import logging
from flask import Flask, request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, Dispatcher

TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"
WEBHOOK_URL = "https://appleid035.onrender.com/"  # آدرس رندر خودت

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

app = Flask(__name__)

# تعریف هندلر /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات با webhook آماده است.")

# ساخت اپلیکیشن تلگرام (ApplicationBuilder)
telegram_app = ApplicationBuilder().token(TOKEN).build()
telegram_app.add_handler(CommandHandler("start", start))

# تنظیم webhook به محض اجرای برنامه
async def set_webhook():
    await telegram_app.bot.set_webhook(WEBHOOK_URL)

import asyncio
asyncio.run(set_webhook())

# روت اصلی برای دریافت آپدیت‌ها از تلگرام
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), telegram_app.bot)
    asyncio.run(telegram_app.update_queue.put(update))
    return "OK"

# اجرای Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
