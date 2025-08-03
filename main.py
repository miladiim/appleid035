import logging
from flask import Flask, request, abort
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

# تنظیمات شخصی شما
TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"
CHANNEL_ID = -1002276225309
ADMIN_ID = 368422936
WEBHOOK_URL = "https://appleid035.onrender.com/"  # حتما این آدرس رو درست بزار

START_MSG = "👋 خوش اومدی! برای ادامه اول باید عضو کانال پشتیبانی بشی:"
CARD_NUMBER = "6219 8619 0952 136\nبه نام: میلاد"

PRODUCTS = {
    "2018": {"price": "250,000", "title": "اپل آیدی ساخت 2018"},
    "2025": {"price": "200,000", "title": "اپل آیدی ساخت 2025"},
    "custom": {"price": "350,000", "title": "اپل آیدی با اطلاعات شخصی"}
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# این تابع برای بررسی عضویت کاربر در کانال است
async def check_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ["left", "kicked"]:
            btn = InlineKeyboardMarkup(
                [[InlineKeyboardButton("عضویت در کانال 📢", url="https://t.me/appleid035")]]
            )
            await update.message.reply_text(START_MSG, reply_markup=btn)
            return False
        return True
    except Exception as e:
        logger.error(f"Error checking membership: {e}")
        return False

# هندلر دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_membership(update, context):
        return
    await update.message.reply_text(
        "📱 لطفاً شماره موبایل خود را به صورت دستی وارد کرده و روی دکمه زیر بزنید:",
        reply_markup=ReplyKeyboardMarkup([["ارسال شماره"]], resize_keyboard=True),
    )

# مدیریت پیام‌ها
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if text == "ارسال شماره":
        await update.message.reply_text(
            "✅ شماره دریافت شد. حالا یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(
                [
                    ["📦 اپل آیدی 2018 - 250 تومان"],
                    ["📦 اپل آیدی 2025 - 200 تومان"],
                    ["📝 اپل آیدی با اطلاعات شخصی - 350 تومان"],
                ],
                resize_keyboard=True,
            ),
        )
    elif "2018" in text:
        user_data["product"] = "2018"
        await update.message.reply_text(
            f"🔻 لطفاً مبلغ {PRODUCTS['2018']['price']} تومان رو به شماره کارت زیر واریز کن:\n\n"
            f"{CARD_NUMBER}\n\nسپس رسید پرداخت رو همینجا ارسال کن."
        )
    elif "2025" in text:
        user_data["product"] = "2025"
        await update.message.reply_text(
            f"🔻 لطفاً مبلغ {PRODUCTS['2025']['price']} تومان رو به شماره کارت زیر واریز کن:\n\n"
            f"{CARD_NUMBER}\n\nسپس رسید پرداخت رو همینجا ارسال کن."
        )
    elif "اطلاعات شخصی" in text:
        user_data["product"] = "custom"
        await update.message.reply_text(
            f"🔻 لطفاً مبلغ {PRODUCTS['custom']['price']} تومان رو به شماره کارت زیر واریز کن:\n\n"
            f"{CARD_NUMBER}\n\nسپس رسید پرداخت به همراه اسم و فامیل صاحب اپل آیدی رو همینجا بفرست."
        )
    else:
        # پیام کاربر به ادمین ارسال شود
        msg = f"🧾 پیام جدید از {update.effective_user.full_name} ({update.effective_user.id}):\n\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("✅ پیام شما ثبت شد. منتظر پاسخ پشتیبانی باشید.")

# هندلر اصلی برای دریافت آپدیت‌ها از تلگرام (وبهوک)
@app.route("/", methods=["POST"])
def webhook():
    if request.method == "POST":
        update = Update.de_json(request.get_json(force=True), bot)
        # اجرای هندلرها به صورت async و غیرهمزمان
        import asyncio

        asyncio.run(application.process_update(update))
        return "OK"
    else:
        abort(400)

if __name__ == "__main__":
    # ساخت بات تلگرام
    application = ApplicationBuilder().token(TOKEN).build()
    bot = Bot(token=TOKEN)

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    # تنظیم وبهوک روی تلگرام (این خط رو فقط یک بار اجرا کن، بعد از اون کامنتش کن)
    # یا میتونی این خط رو تو یه اسکریپت جدا اجرا کنی
    # import asyncio
    # asyncio.run(bot.set_webhook(WEBHOOK_URL))

    # اجرای سرور فلاسک روی پورت 10000
    app.run(host="0.0.0.0", port=10000)
