import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs"
CHANNEL_ID = -1002276225309
ADMIN_ID = 368422936

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

START_MSG = "👋 خوش اومدی! لطفا اول عضو کانال پشتیبانی بشید:"
CARD_NUMBER = "6219 8619 0952 136\nبه نام: میلاد"

PRODUCTS = {
    "2018": {"price": "250,000", "title": "اپل آیدی ساخت 2018"},
    "2025": {"price": "200,000", "title": "اپل آیدی ساخت 2025"},
    "custom": {"price": "350,000", "title": "اپل آیدی با اطلاعات شخصی"},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user.id)
        if member.status in ["left", "kicked"]:
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("عضویت در کانال 📢", url="https://t.me/appleid035")]
            ])
            await update.message.reply_text(START_MSG, reply_markup=btn)
            return
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        await update.message.reply_text("خطایی رخ داد، لطفا دوباره تلاش کنید.")
        return

    await update.message.reply_text(
        "📱 لطفا شماره موبایل خود را به صورت دستی وارد کرده و روی دکمه زیر بزنید:",
        reply_markup=ReplyKeyboardMarkup([["ارسال شماره"]], resize_keyboard=True),
    )

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
        msg = f"🧾 پیام جدید از {update.effective_user.full_name} ({update.effective_user.id}):\n\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("✅ پیام شما ثبت شد. منتظر پاسخ پشتیبانی باشید.")

async def support_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if update.message.reply_to_message:
        original_msg = update.message.reply_to_message.text
        user_id = None

        try:
            first_line = original_msg.split("\n")[0]
            user_id = int(first_line.split("(")[1].split(")")[0])
        except:
            pass

        if user_id:
            await context.bot.send_message(chat_id=user_id, text=f"👨‍💻 پاسخ پشتیبانی:\n\n{update.message.text}")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))
    app.add_handler(MessageHandler(filters.REPLY, support_response))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
