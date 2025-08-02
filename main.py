import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ---------------- تنظیمات ----------------
TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"  # توکن ربات
CHANNEL_ID = -1002891641618  # آیدی عددی کانال VIP
ADMIN_ID = 368422936  # آیدی عددی ادمین (میلاد)

CARD_NUMBER = """6219 8619 0952 1360
به نام: میلاد محبوبیان"""

PRODUCTS = {
    "2018": {"price": "250,000", "title": "اپل آیدی ساخت 2018"},
    "2025": {"price": "200,000", "title": "اپل آیدی ساخت 2025"},
    "custom": {"price": "350,000", "title": "اپل آیدی با اطلاعات شخصی"}
}

# ---------------- لاگ ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- /start ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    member = await context.bot.get_chat_member(CHANNEL_ID, user.id)

    if member.status in ["left", "kicked"]:
        btn = InlineKeyboardMarkup(
            [[InlineKeyboardButton("عضویت در کانال 📢", url="https://t.me/+Bnko8vYkvcRkYjdk")]]
        )
        await update.message.reply_text(
            "👋 خوش اومدی! برای ادامه، اول عضو کانال شو:",
            reply_markup=btn
        )
        return

    await update.message.reply_text(
        "📱 لطفاً شماره موبایلت رو به صورت دستی وارد کن و روی دکمه زیر بزن:",
        reply_markup=ReplyKeyboardMarkup([["ارسال شماره"]], resize_keyboard=True)
    )

# ---------------- پیام‌ها ----------------
async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user_data = context.user_data

    if text == "ارسال شماره":
        await update.message.reply_text(
            "✅ شماره دریافت شد. حالا یکی از اپل‌آیدی‌های زیر رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup([
                ["📦 اپل آیدی 2018 - 250 تومان"],
                ["📦 اپل آیدی 2025 - 200 تومان"],
                ["📝 اپل آیدی با اطلاعات شخصی - 350 تومان"]
            ], resize_keyboard=True)
        )

    elif "2018" in text:
        user_data["product"] = "2018"
        await update.message.reply_text(
            f"""🔻 لطفاً مبلغ {PRODUCTS['2018']['price']} تومان رو به شماره کارت زیر واریز کن:

{CARD_NUMBER}

سپس رسید پرداخت رو همین‌جا ارسال کن."""
        )

    elif "2025" in text:
        user_data["product"] = "2025"
        await update.message.reply_text(
            f"""🔻 لطفاً مبلغ {PRODUCTS['2025']['price']} تومان رو به شماره کارت زیر واریز کن:

{CARD_NUMBER}

سپس رسید پرداخت رو همین‌جا ارسال کن."""
        )

    elif "اطلاعات شخصی" in text:
        user_data["product"] = "custom"
        await update.message.reply_text(
            f"""🔻 لطفاً مبلغ {PRODUCTS['custom']['price']} تومان رو به شماره کارت زیر واریز کن:

{CARD_NUMBER}

سپس رسید پرداخت و مشخصات دلخواه برای اپل‌آیدی رو ارسال کن."""
        )

    else:
        msg = f"""📩 پیام جدید از {update.effective_user.full_name} (ID: {update.effective_user.id}):

{text}"""
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("✅ پیام شما دریافت شد. منتظر پاسخ پشتیبانی باشید.")

# ---------------- پاسخ ادمین ----------------
async def support_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if update.message.reply_to_message:
        try:
            first_line = update.message.reply_to_message.text.splitlines()[0]
            user_id = int(first_line.split("ID: ")[-1].replace(")", ""))
            await context.bot.send_message(chat_id=user_id, text=update.message.text)
            await update.message.reply_text("✅ پاسخ ارسال شد.")
        except Exception as e:
            await update.message.reply_text(f"❌ خطا در ارسال پاسخ: {e}")

# ---------------- اجرا ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.User(ADMIN_ID), support_response))

    app.run_polling()

if __name__ == "__main__":
    main()
