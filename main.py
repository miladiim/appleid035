from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from telegram import Update

TOKEN = "توکن-ربات-تو-اینجا"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! ربات با موفقیت اجرا شد.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
