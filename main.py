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
users = {}

def load_apple_ids():
    if not os.path.exists(APPLEID_FILE):
        with open(APPLEID_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(APPLEID_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_apple_ids(data):
    with open(APPLEID_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

@bot.message_handler(func=lambda m: m.text == '🛒 خرید اپل‌آیدی')
def show_appleid_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🍎 اپل‌آیدی ساخت 2018 آمریکا (250,000 تومان)", callback_data='buy_2018'),
        telebot.types.InlineKeyboardButton("🍏 اپل‌آیدی ساخت 2025 آمریکا (200,000 تومان)", callback_data='buy_2025'),
        telebot.types.InlineKeyboardButton("📧 هات‌میل ساخت 2025 (180,000 تومان)", callback_data='buy_hotmail')
    )
    bot.send_message(message.chat.id, "📦 لطفاً نوع اپل‌آیدی را انتخاب کن:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy(call):
    user_id = call.from_user.id
    if user_id not in users or "phone" not in users[user_id]:
        bot.answer_callback_query(call.id, "لطفاً ابتدا شماره موبایل خود را ارسال کنید.")
        return
    apple_ids = load_apple_ids()
    type_map = {
        'buy_2018': '2018',
        'buy_2025': '2025',
        'buy_hotmail': 'hotmail'
    }
    t = type_map.get(call.data)
    selected_appleid = next((a for a in apple_ids if not a.get("sold", False) and a.get("type") == t), None)
    if not selected_appleid:
        bot.answer_callback_query(call.id, "❗️ متأسفانه موجودی نداریم.")
        return
    users[user_id]["selected_appleid"] = selected_appleid
    bot.send_message(user_id, "لطفاً شماره کارت خود را وارد کنید.\nبعد از آن رسید واریز را بفرستید.")

@bot.message_handler(func=lambda m: m.text and m.text.isdigit() and "selected_appleid" in users.get(m.from_user.id, {}))
def receive_card_number(message):
    user_id = message.from_user.id
    card_number = message.text
    appleid = users[user_id].pop("selected_appleid")
    apple_ids = load_apple_ids()
    for a in apple_ids:
        if a == appleid:
            a["sold"] = True
            break
    save_apple_ids(apple_ids)
    msg = (
        f"🎉 خرید انجام شد!\n\n"
        f"ایمیل: {appleid['email']}\nرمز: {appleid['password']}\n"
        f"سؤال ۱: {appleid['q1']}\nسؤال ۲: {appleid['q2']}\nسؤال ۳: {appleid['q3']}\n\n"
        f"شماره کارت شما: {card_number}\n\n"
        "✅ لطفاً رسید واریز خود را ارسال کنید."
    )
    bot.send_message(user_id, msg)
    bot.send_message(ADMIN_ID, f"✅ خرید توسط {user_id}\nشماره کارت: {card_number}")

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("📋 لیست کاربران", callback_data='list_users'),
        telebot.types.InlineKeyboardButton("➕ افزودن اپل‌آیدی", callback_data='add_appleid'),
        telebot.types.InlineKeyboardButton("📦 موجودی", callback_data='stock')
    )
    bot.send_message(message.chat.id, "🛠 پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ['list_users', 'add_appleid', 'stock'])
def callback_admin(call):
    if call.data == 'list_users':
        text = "📋 کاربران:\n"
        for uid, info in users.items():
            phone = info.get("phone", "-")
            active = "✅" if info.get("active") else "❌"
            text += f"{uid} | {phone} | {active}\n"
        bot.send_message(ADMIN_ID, text or "کاربری یافت نشد.")

    elif call.data == 'add_appleid':
        bot.send_message(ADMIN_ID, "لطفاً اطلاعات اپل‌آیدی را با فرمت زیر ارسال کنید:\n\n"
                                   "type:2018\nemail:mail@domain.com\npassword:1234\nq1:سؤال1\nq2:سؤال2\nq3:سؤال3")
        bot.register_next_step_handler(call.message, add_appleid_step)

    elif call.data == 'stock':
        data = load_apple_ids()
        count = len([i for i in data if not i.get("sold")])
        bot.send_message(ADMIN_ID, f"📦 موجودی اپل‌آیدی: {count} عدد")

def add_appleid_step(message):
    lines = message.text.splitlines()
    entry = {}
    for line in lines:
        if ":" in line:
            key, val = line.split(":", 1)
            entry[key.strip()] = val.strip()
    if all(k in entry for k in ["type", "email", "password", "q1", "q2", "q3"]):
        entry["sold"] = False
        data = load_apple_ids()
        data.append(entry)
        save_apple_ids(data)
        bot.send_message(ADMIN_ID, "✅ اپل‌آیدی با موفقیت ذخیره شد.")
    else:
        bot.send_message(ADMIN_ID, "❌ فرمت اشتباه است. دوباره امتحان کن.")

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url='https://appleid035.onrender.com/webhook')  # ← دامنه واقعی روی Render
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_bot()
