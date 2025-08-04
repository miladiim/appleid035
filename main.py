from flask import Flask, request
import telebot
import time
import threading
import json
import os

API_TOKEN = '8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs'
CHANNEL_ID = -1002891641618
ADMIN_ID = 368422936

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

APPLEID_FILE = 'apple_ids.json'

def load_apple_ids():
    if not os.path.exists(APPLEID_FILE):
        with open(APPLEID_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(APPLEID_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_apple_ids(data):
    with open(APPLEID_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

users = {}

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data(as_text=True))
    bot.process_new_updates([update])
    return 'ok'

def send_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        telebot.types.KeyboardButton('🛒 خرید اپل‌آیدی'),
        telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی')
    )
    bot.send_message(chat_id, "📋 منوی اصلی:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    # اگر شماره موبایل قبلا ارسال شده بود، منوی اصلی نشان داده شود
    if user_id in users and "phone" in users[user_id]:
        send_main_menu(chat_id)
    else:
        # دکمه درخواست شماره موبایل (request_contact=True)
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
        markup.add(btn)
        bot.send_message(chat_id, "سلام 👋 لطفاً شماره موبایلت رو با دکمه زیر ارسال کن:", reply_markup=markup)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    users[user_id] = {"phone": phone, "active": False, "timestamp": int(time.time())}
    bot.send_message(ADMIN_ID, f"📥 کاربر جدید ثبت شد\nآیدی: {user_id}\nشماره: {phone}")
    # ارسال منوی اصلی بدون دکمه ارسال شماره موبایل (حذف دکمه ارسال شماره پس از ارسال)
    send_main_menu(message.chat.id)

# حذف handler شماره موبایل دستی (func=lambda m: m.text == '📱 ارسال شماره موبایل') که قبلا وجود داشت
# تا کاربر فقط بتواند با دکمه ارسال شماره، شماره را بفرستد و شماره دستی تایپ نکند.

# ادامه کد قبلی خرید اپل‌آیدی، رسید پرداخت و تیکت‌ها بدون تغییر

@bot.message_handler(func=lambda m: m.text == '🛒 خرید اپل‌آیدی')
def show_appleid_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🍎 اپل‌آیدی ساخت 2018 آمریکا (250,000 تومان)", callback_data='buy_2018'),
        telebot.types.InlineKeyboardButton("🍏 اپل‌آیدی ساخت 2025 آمریکا (200,000 تومان)", callback_data='buy_2025'),
        telebot.types.InlineKeyboardButton("🔐 اپل‌آیدی با اطلاعات شخصی (350,000 تومان)", callback_data='buy_personal')
    )
    bot.send_message(message.chat.id, "لطفاً نوع اپل‌آیدی مورد نظر خود را انتخاب کنید:", reply_markup=markup)

# بقیه‌ی کدها دقیقاً مثل شما بدون تغییر باقی می‌ماند

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def support_ticket(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "لطفاً پیام خود را برای پشتیبانی ارسال کنید. پس از ارسال، پیام به ادمین خواهد رسید.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.reply_to_message.from_user.id == ADMIN_ID)
def admin_reply(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message or not message.reply_to_message.text:
        return
    # استخراج آیدی کاربر از پیام قبلی (خط اول)
    lines = message.reply_to_message.text.split('\n')
    if len(lines) < 2:
        return
    try:
        user_line = lines[0]
        user_id = int(user_line.split()[-1])
        bot.send_message(user_id, f"💬 پاسخ پشتیبانی:\n{message.text}")
    except:
        pass

@bot.message_handler(func=lambda m: m.text and m.text not in ['🎫 تیکت به پشتیبانی', '🛒 خرید اپل‌آیدی'])
def forward_ticket(message):
    if message.from_user.id == ADMIN_ID:
        return
    user_id = message.from_user.id
    bot.send_message(ADMIN_ID, f"📩 پیام از کاربر {user_id}:\n{message.text}")
    bot.send_message(user_id, "✅ پیام شما به پشتیبانی ارسال شد.")

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url='https://appleid035.onrender.com/webhook')  # ← دامنه واقعی روی Render
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_bot()

    
