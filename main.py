import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")  # توکن رباتتو تو تنظیمات Render بذار

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ربات تستی فعال شد! سلام :)")

application.add_handler(CommandHandler("start", start))

@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
async def set_webhook():
    url = f"https://your-render-url.onrender.com/{TOKEN}"  # آدرس پروژه‌ات تو Render رو اینجا بذار
    await application.bot.set_webhook(url)
    return "Webhook set!"

if __name__ == "__main__":
    application.run_polling()
