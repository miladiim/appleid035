import json
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ContextTypes, filters
)

# خواندن تنظیمات از فایل config.json
with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["TOKEN"]
ADMIN_ID = config["ADMIN_ID"]
CHANNEL_ID = config["CHANNEL_ID"]
CHANNEL_LINK = config["CHANNEL_LINK"]

CARD_NUMBER = "6219 8619 0952 136\nبه نام: میلاد"

PRODUCTS = {
    "2018": {"price": "250,000", "title": "اپل آیدی ساخت 2018"},
    "2025": {"price": "200,000", "title": "اپل آیدی ساخت 2025"},
    "custom": {"price": "350,000", "title": "اپل آیدی با اطلاعات شخصی"}
}

# فعال‌سازی لاگ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

    if member.status in ["left", "kicked"]:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال 📢", url=CHANNEL_LINK)]])
        await update.message.reply_text("👋 برای ادامه ابتدا عضو کانال شو:", reply_markup=btn)
        return

    await update.message.reply_text(
        "📱 لطفاً شماره موبایل خود را وارد کنید و سپس دکمه زیر را بزنید:",
        reply_markup=ReplyKeyboardMarkup([["ارسال شماره"]], resize_keyboard=True)
    )

# مدیریت پیام‌ها
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if text == "ارسال شماره":
        await update.message.reply_text(
            "✅ شماره دریافت شد. حالا یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup([
                ["📦 اپل آیدی 2018 - 250 تومان"],
                ["📦 اپل آیدی 2025 - 200 تومان"],
                ["📝 اپل آیدی با اطلاعات شخصی - 350 تومان"]
            ], resize_keyboard=True)
        )

    elif "2018" in text:
        user_data["product"] = "2018"
        await update.message.reply_text(
            f"🔻 مبلغ {PRODUCTS['2018']['price']} تومان را به کارت زیر واریز کن:\n\n"
            f"{CARD_NUMBER}\n\nسپس رسید را همین‌جا ارسال کن."
        )

    elif "2025" in text:
        user_data["product"] = "2025"
        await update.message.reply_text(
            f"🔻 مبلغ {PRODUCTS['2025']['price']} تومان را به کارت زیر واریز کن:\n\n"
            f"{CARD_NUMBER}\n\nسپس رسید را همین‌جا ارسال کن."
        )

    elif "اطلاعات شخصی" in text:
        user_data["product"] = "custom"
        await update.message.reply_text(
            f"🔻 مبلغ {PRODUCTS['custom']['price']} تومان را به کارت زیر واریز کن:\n\n"
            f"{CARD_NUMBER}\n\nسپس رسید + اطلاعات لازم (نام و ...) را ارسال کن."
        )

    else:
        msg = f"🧾 پیام جدید از {update.effective_user.full_name} ({update.effective_user.id}):\n\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("✅ پیام شما به پشتیبانی ارسال شد.")

# Flask app برای Webhook
app = Flask(__name__)
application = None

@app.route('/')
def index():
    return 'ربات فعاله ✅'

@app.route(f'/{TOKEN}', methods=['POST'])
async def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), application.bot)
        await application.process_update(update)
        return 'ok'

# راه‌اندازی کامل ربات
async def main():
    global application
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # تنظیم Webhook برای render
    await application.bot.set_webhook(f"https://appleid035.onrender.com/{TOKEN}")
    print("✅ Webhook فعال شد.")

    return application

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
    app.run(host="0.0.0.0", port=10000)
