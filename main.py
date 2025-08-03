import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# اطلاعات اصلی ربات
TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"
CHANNEL_ID = -1002891641618
ADMIN_ID = 368422936
WEBHOOK_URL = "https://appleid035.onrender.com"  # آدرس واقعی پروژه در Render

# محصولات اپل‌آیدی
PRODUCTS = {
    "2018": {"price": "250,000", "title": "اپل آیدی ساخت 2018"},
    "2025": {"price": "200,000", "title": "اپل آیدی ساخت 2025"},
    "custom": {"price": "350,000", "title": "اپل آیدی با اطلاعات شخصی"}
}
CARD_NUMBER = "6219 8619 0952 136\nبه نام: میلاد"

# تنظیمات
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
application = Application.builder().token(TOKEN).build()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
    if member.status in ["left", "kicked"]:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("عضویت در کانال 📢", url="https://t.me/appleid035")]])
        await update.message.reply_text("👋 برای ادامه، لطفاً ابتدا عضو کانال شو:", reply_markup=btn)
        return
    await update.message.reply_text(
        "📱 شماره موبایل خودتو وارد کن و بعد روی دکمه زیر بزن:",
        reply_markup=ReplyKeyboardMarkup([["ارسال شماره"]], resize_keyboard=True)
    )

# پیام‌ها
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if text == "ارسال شماره":
        await update.message.reply_text(
            "✅ شماره دریافت شد. لطفاً یکی از گزینه‌های زیر را انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup([
                ["📦 اپل آیدی 2018 - 250 تومان"],
                ["📦 اپل آیدی 2025 - 200 تومان"],
                ["📝 اپل آیدی با اطلاعات شخصی - 350 تومان"]
            ], resize_keyboard=True)
        )
    elif "2018" in text:
        user_data["product"] = "2018"
        await update.message.reply_text(
            f"💳 مبلغ {PRODUCTS['2018']['price']} تومان را به کارت زیر واریز کن:\n\n{CARD_NUMBER}\n\nسپس رسید پرداخت را ارسال کن."
        )
    elif "2025" in text:
        user_data["product"] = "2025"
        await update.message.reply_text(
            f"💳 مبلغ {PRODUCTS['2025']['price']} تومان را به کارت زیر واریز کن:\n\n{CARD_NUMBER}\n\nسپس رسید پرداخت را ارسال کن."
        )
    elif "اطلاعات شخصی" in text:
        user_data["product"] = "custom"
        await update.message.reply_text(
            f"💳 مبلغ {PRODUCTS['custom']['price']} تومان را به کارت زیر واریز کن:\n\n{CARD_NUMBER}\n\nسپس رسید پرداخت + اسم و فامیل رو بفرست."
        )
    else:
        msg = f"🧾 پیام از {update.effective_user.full_name} ({update.effective_user.id}):\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

# هندلرها
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

# Webhook endpoint
@app.route(f"/{TOKEN}", methods=["POST"])
async def receive_update():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

@app.route("/", methods=["GET"])
async def set_webhook():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    return "Webhook set!"

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
