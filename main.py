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
        telebot.types.KeyboardButton('📱 ارسال شماره موبایل'),
        telebot.types.KeyboardButton('🛒 خرید اپل‌آیدی'),
        telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی')
    )
    bot.send_message(chat_id, "📋 منوی اصلی:", reply_markup=markup)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    if user_id in users and "phone" in users[user_id]:
        send_main_menu(chat_id)
    else:
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
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == '📱 ارسال شماره موبایل')
def ask_phone_again(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "لطفاً شماره موبایلت رو ارسال کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🛒 خرید اپل‌آیدی')
def show_appleid_menu(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("🍎 اپل‌آیدی ساخت 2018 آمریکا (250,000 تومان)", callback_data='buy_2018'),
        telebot.types.InlineKeyboardButton("🍏 اپل‌آیدی ساخت 2025 آمریکا (200,000 تومان)", callback_data='buy_2025'),
        telebot.types.InlineKeyboardButton("📧 هات‌میل ساخت 2025 (ارزان) (180,000 تومان)", callback_data='buy_hotmail')
    )
    bot.send_message(message.chat.id, "لطفاً نوع اپل‌آیدی مورد نظر خود را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy(call):
    user_id = call.from_user.id
    if user_id not in users or "phone" not in users[user_id]:
        bot.answer_callback_query(call.id, "لطفاً ابتدا شماره موبایل خود را ارسال کنید.")
        return
    apple_ids = load_apple_ids()
    # فیلتر اپل‌آیدی‌ها بر اساس نوع
    type_map = {
        'buy_2018': '2018',
        'buy_2025': '2025',
        'buy_hotmail': 'hotmail'
    }
    t = type_map.get(call.data)
    selected_appleid = None
    for a in apple_ids:
        if not a.get("sold", False) and a.get("type") == t:
            selected_appleid = a
            break
    if selected_appleid is None:
        bot.answer_callback_query(call.id, "❗️ متأسفانه اپل‌آیدی موجود نیست.")
        return
    users[user_id]["selected_appleid"] = selected_appleid
    bot.send_message(user_id, f"✅ اپل‌آیدی انتخاب شد. لطفاً شماره کارت بانکی خود را ارسال کنید تا فرایند خرید تکمیل شود.")

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and "selected_appleid" in users.get(m.from_user.id, {}))
def receive_card_number(message):
    user_id = message.from_user.id
    card_number = message.text
    appleid = users[user_id].pop("selected_appleid")
    apple_ids = load_apple_ids()
    # علامت گذاری اپل‌آیدی به عنوان فروخته شده
    for a in apple_ids:
        if a == appleid:
            a["sold"] = True
            break
    save_apple_ids(apple_ids)
    text = f"""🎉 خرید با موفقیت انجام شد!

ایمیل: {appleid['email']}
رمز عبور: {appleid['password']}
سوال امنیتی ۱: {appleid['q1']}
سوال امنیتی ۲: {appleid['q2']}
سوال امنیتی ۳: {appleid['q3']}

شماره کارت شما برای پیگیری ثبت شد: {card_number}

✅ از خرید شما سپاسگزاریم!"""
    bot.send_message(user_id, text)
    bot.send_message(ADMIN_ID, f"💳 خرید توسط کاربر {user_id} انجام شد.\nشماره کارت: {card_number}")

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📋 لیست کاربران", callback_data='list_users'),
        telebot.types.InlineKeyboardButton("🟢 فعال‌سازی دستی", callback_data='confirm_user'),
        telebot.types.InlineKeyboardButton("❌ اخراج کاربر", callback_data='remove_user'),
        telebot.types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data='broadcast'),
        telebot.types.InlineKeyboardButton("📦 موجودی اپل‌آیدی", callback_data='stock')
    )
    bot.send_message(message.chat.id, "🛠 پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "list_users":
        text = "📋 لیست کاربران:\n"
        for user_id, info in users.items():
            phone = info.get("phone", "-")
            active = "✅" if info.get("active", False) else "❌"
            text += f"{user_id} | {phone} | {active}\n"
        bot.send_message(ADMIN_ID, text or "❗️کاربری یافت نشد.")

    elif call.data == "confirm_user":
        bot.send_message(ADMIN_ID, "لطفاً آیدی عددی کاربر را بفرستید تا فعال شود.")
        bot.register_next_step_handler(call.message, confirm_user_step)

    elif call.data == "remove_user":
        bot.send_message(ADMIN_ID, "آیدی عددی کاربر برای اخراج را بفرستید:")
        bot.register_next_step_handler(call.message, remove_user_step)

    elif call.data == "broadcast":
        bot.send_message(ADMIN_ID, "پیامی که باید به همه ارسال شود را بفرستید:")
        bot.register_next_step_handler(call.message, broadcast_step)

    elif call.data == "stock":
        apple_ids = load_apple_ids()
        available = len([a for a in apple_ids if not a.get("sold", False)])
        bot.send_message(ADMIN_ID, f"📦 موجودی اپل‌آیدی‌ها: {available}")

def confirm_user_step(message):
    try:
        user_id = int(message.text)
        if user_id in users:
            users[user_id]["active"] = True
            users[user_id]["timestamp"] = int(time.time())
            bot.send_message(user_id, "✅ حساب شما فعال شد.")
            bot.send_message(ADMIN_ID, f"✅ کاربر {user_id} فعال شد.")
        else:
            bot.send_message(ADMIN_ID, "❌ کاربر یافت نشد.")
    except:
        bot.send_message(ADMIN_ID, "❌ ورودی نامعتبر است.")

def remove_user_step(message):
    try:
        user_id = int(message.text)
        if user_id in users:
            users.pop(user_id)
            bot.send_message(user_id, "❌ شما از سیستم حذف شدید.")
            bot.send_message(ADMIN_ID, f"❌ کاربر {user_id} حذف شد.")
        else:
            bot.send_message(ADMIN_ID, "❌ کاربر یافت نشد.")
    except:
        bot.send_message(ADMIN_ID, "❌ ورودی نامعتبر است.")

def broadcast_step(message):
    text = message.text
    count = 0
    for user_id in users.keys():
        try:
            bot.send_message(user_id, text)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"پیام به {count} کاربر ارسال شد.")

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url='https://appleid035.onrender.com/webhook')  # ← دامنه واقعی روی Render
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_bot()
