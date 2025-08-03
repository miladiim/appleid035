import logging
from flask import Flask, request
from telegram import (
    Update, KeyboardButton, ReplyKeyboardMarkup,
    ReplyKeyboardRemove, InputMediaPhoto
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from pymongo import MongoClient
import json

# پیکربندی
TOKEN = "494613530:AAHQFmKNzgoehLf9i35mIPn1Z8WhtkrBZa4"
ADMIN_ID = 368422936
CARD_NUMBER = "6037991234567890"

# اتصال به دیتابیس
client = MongoClient("mongodb+srv://vipadmin:milad137555@cluster0.g6mqucj.mongodb.net")
db = client["vip_bot"]
users_col = db["users"]
orders_col = db["orders"]

# راه‌اندازی فلَسک
app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = KeyboardButton("ارسال شماره 📱", request_contact=True)
    markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=markup)

# ذخیره شماره موبایل و نمایش گزینه‌ها
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id
    phone = contact.phone_number

    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"phone": phone}},
        upsert=True
    )

    buttons = [
        ["🟣 اپل‌آیدی آماده 2025 - 200 هزار تومان"],
        ["🔵 اپل‌آیدی آماده 2018 - 300 هزار تومان"],
        ["🟢 اپل‌آیدی با اطلاعات شخصی - 350 هزار تومان"]
    ]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("یک گزینه را برای خرید انتخاب کنید:", reply_markup=markup)

# مدیریت انتخاب محصول
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if "آماده 2025" in text:
        product = "اپل‌آیدی آماده 2025"
        price = 200000
    elif "آماده 2018" in text:
        product = "اپل‌آیدی آماده 2018"
        price = 300000
    elif "اطلاعات شخصی" in text:
        product = "اپل‌آیدی با اطلاعات شخصی"
        price = 350000
        await update.message.reply_text("🔶 لطفاً *نام و نام خانوادگی* خود را هم همراه با رسید ارسال کنید.", parse_mode="Markdown")
    else:
        # رسید پرداخت یا پیام دیگر
        if update.message.photo:
            caption = update.message.caption or ""
            orders_col.insert_one({
                "user_id": user_id,
                "photo": True,
                "caption": caption
            })
            await context.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=update.message.photo[-1].file_id,
                caption=f"✅ رسید جدید از کاربر {user_id}\n{caption}"
            )
            await update.message.reply_text("✅ رسید شما دریافت شد. منتظر تأیید ادمین بمانید.")
        else:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"📨 پیام جدید از {user_id}:\n{text}")
            await update.message.reply_text("📩 پیام شما به ادمین ارسال شد.")
        return

    # ذخیره سفارش در دیتابیس
    users_col.update_one({"user_id": user_id}, {"$set": {
        "selected_product": product,
        "price": price
    }})

    await update.message.reply_text(
        f"✅ محصول انتخابی: {product}\n💳 لطفاً مبلغ {price:,} تومان را به شماره کارت زیر واریز کرده و رسید را ارسال کنید:\n\n`{CARD_NUMBER}`",
        parse_mode="Markdown"
    )

# پاسخ ادمین به کاربر
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if update.message.reply_to_message:
        original_text = update.message.reply_to_message.text
        lines = original_text.split()
        for line in lines:
            if line.isdigit():
                target_user = int(line)
                await context.bot.send_message(chat_id=target_user, text=update.message.text)
                await update.message.reply_text("✅ پیام برای کاربر ارسال شد.")
                return
    await update.message.reply_text("⛔️ این پاسخ، ریپلای روی پیام کاربر نیست.")

# وب‌هوک تلگرام
@app.route("/", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), Application.builder().token(TOKEN).build().bot)
    Application.builder().token(TOKEN).build().process_update(update)
    return "ok"

@app.route("/")
def index():
    return "ربات فعال است."

# اجرای ربات
def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    application.add_handler(MessageHandler(filters.ALL & filters.User(user_id=ADMIN_ID), admin_reply))
    application.run_polling()

if __name__ == "__main__":
    main()
