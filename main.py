import os
from flask import Flask, request
from telegram import Update
from telegram.ext import Application

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8443))

app = Flask(__name__)
application = Application.builder().token(TOKEN).build()

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
async def index():
    # ست کردن وبهوک هر بار که رندر سایت بالا میاد (مناسب برای تست)
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    return "Webhook set!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
