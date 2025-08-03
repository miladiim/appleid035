import logging
from flask import Flask, request
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from pymongo import MongoClient
import json
import requests

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"
CHANNEL_LINK = config["channel"]
ADMIN_ID = 368422936  # آیدی عددی ادمین



@app.route("/")
def index():
    return "Bot is running."

# Telegram Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[KeyboardButton("ارسال شماره 📱", request_contact=True)]]
    await update.message.reply_text("برای شروع شماره موبایل خود را ارسال کنید:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True))

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.message.contact
    user_id = update.effective_user.id

    users_col.update_one({"user_id": user_id}, {"$set": {
        "user_id": user_id,
        "phone_number": contact.phone_number,
        "step": "menu"
    }}, upsert=True)

    keyboard = [
        ["🟣 خرید اپل‌آیدی آماده 2025 - 200 هزار"],
        ["🟢 خرید اپل‌آیدی آماده 2018 - 300 هزار"],
        ["🔴 خرید اپل‌آیدی با اطلاعات شخصی - 350 هزار"]
    ]
    await update.message.reply_text(
        "✅ شماره ثبت شد. یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    user = users_col.find_one({"user_id": user_id}) or {}

    if text.startswith("🟣"):
        users_col.update_one({"user_id": user_id}, {"$set": {"step": "waiting_receipt", "product": "اپل‌آیدی 2025 - 200 هزار"}})
        await update.message.reply_text("مبلغ 200,000 تومان به شماره کارت زیر واریز کنید و رسید را ارسال نمایید:

6037 9917 1234 5678")

    elif text.startswith("🟢"):
        users_col.update_one({"user_id": user_id}, {"$set": {"step": "waiting_receipt", "product": "اپل‌آیدی 2018 - 300 هزار"}})
        await update.message.reply_text("مبلغ 300,000 تومان به شماره کارت زیر واریز کنید و رسید را ارسال نمایید:

6037 9917 1234 5678")

    elif text.startswith("🔴"):
        users_col.update_one({"user_id": user_id}, {"$set": {"step": "waiting_info", "product": "اپل‌آیدی اطلاعات شخصی - 350 هزار"}})
        await update.message.reply_text(
            "مبلغ 350,000 تومان به شماره کارت زیر واریز کنید:

6037 9917 1234 5678

سپس رسید + نام و نام خانوادگی خود را ارسال کنید.
مثال:
رسید پرداخت 350 تومن
نام: علی رضایی")

    elif user.get("step") == "waiting_receipt":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 رسید جدید:

از: {user_id}
محصول: {user.get('product')}

{text}"
        )
        await update.message.reply_text("✅ رسید ارسال شد. منتظر تایید ادمین باشید.")

    elif user.get("step") == "waiting_info":
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"📥 اطلاعات خرید اپل‌آیدی شخصی:

از: {user_id}
{user.get('product')}

{text}"
        )
        await update.message.reply_text("✅ اطلاعات ارسال شد. منتظر دریافت اپل‌آیدی از طرف ادمین باشید.")

    elif user_id == ADMIN_ID and update.message.reply_to_message:
        target_id = update.message.reply_to_message.text.split("
")[2].replace("از: ", "")
        try:
            target_id = int(target_id)
            await context.bot.send_message(chat_id=target_id, text=f"📤 پاسخ ادمین:
{update.message.text}")
            await update.message.reply_text("✅ پیام برای کاربر ارسال شد.")
        except:
            await update.message.reply_text("❌ ارسال پیام ناموفق بود.")

if __name__ == "__main__":
    app_telegram = Application.builder().token(TOKEN).build()
    app_telegram.add_handler(CommandHandler("start", start))
    app_telegram.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    app_telegram.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app_telegram.run_polling()
