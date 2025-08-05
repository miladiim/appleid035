from flask import Flask, request
import telebot
import os
import json

API_TOKEN = '8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs'
CHANNEL_ID = -1002891641618
ADMIN_ID = 368422936
CHANNEL_LINK = 'https://t.me/appleid035'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

USERS_FILE = 'users.json'

def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception:
        return False

def set_joined(user_id):
    users = load_users()
    users[str(user_id)] = {"joined": True}
    save_users(users)

def has_joined(user_id):
    users = load_users()
    return users.get(str(user_id), {}).get("joined", False)

def send_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        telebot.types.KeyboardButton("🛒 خرید اپل‌آیدی"),
        telebot.types.KeyboardButton("📨 تیکت پشتیبانی")
    )
    markup.row(
        telebot.types.KeyboardButton("👤 حساب کاربری"),
        telebot.types.KeyboardButton("💳 شارژ حساب")
    )
    markup.row(
        telebot.types.KeyboardButton("💲 قیمت و موجودی")
    )
    bot.send_message(chat_id, "📋 منوی اصلی:", reply_markup=markup)

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data(as_text=True))
    bot.process_new_updates([update])
    return 'ok'

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if not is_member(user_id):
        join_markup = telebot.types.InlineKeyboardMarkup()
        join_markup.add(telebot.types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
        bot.send_message(user_id, "برای استفاده از ربات ابتدا در کانال عضو شوید و سپس /start را بزنید.", reply_markup=join_markup)
        return
    set_joined(user_id)
    send_main_menu(user_id)

@bot.message_handler(func=lambda m: m.text == "🛒 خرید اپل‌آیدی")
def buy_appleid(message):
    user_id = message.from_user.id
    if not has_joined(user_id):
        if not is_member(user_id):
            join_markup = telebot.types.InlineKeyboardMarkup()
            join_markup.add(telebot.types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
            bot.send_message(user_id, "❌ لطفاً ابتدا در کانال عضو شوید و سپس دوباره تلاش کنید.", reply_markup=join_markup)
            return
        set_joined(user_id)
    text = (
        "🍏 لیست اپل‌آیدی‌های آماده:\n"
        "1️⃣ اپل‌آیدی آماده 2018 — 💸 250,000 تومان\n"
        "2️⃣ اپل‌آیدی آماده 2025 — 💸 200,000 تومان\n"
        "3️⃣ اپل‌آیدی با اطلاعات شخصی شما — 💸 300,000 تومان\n\n"
        "برای خرید، نوع اپل‌آیدی موردنظر را انتخاب یا با پشتیبانی ارتباط بگیرید."
    )
    bot.send_message(user_id, text)

@bot.message_handler(func=lambda m: m.text == "💲 قیمت و موجودی")
def show_prices(message):
    user_id = message.from_user.id
    if not has_joined(user_id):
        if not is_member(user_id):
            join_markup = telebot.types.InlineKeyboardMarkup()
            join_markup.add(telebot.types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
            bot.send_message(user_id, "❌ لطفاً ابتدا در کانال عضو شوید و سپس دوباره تلاش کنید.", reply_markup=join_markup)
            return
        set_joined(user_id)
    text = (
        "💵 قیمت و موجودی:\n"
        "1️⃣ اپل‌آیدی آماده 2018 — 💸 250,000 تومان\n"
        "2️⃣ اپل‌آیدی آماده 2025 — 💸 200,000 تومان\n"
        "3️⃣ اپل‌آیدی با اطلاعات شخصی شما — 💸 300,000 تومان"
    )
    bot.send_message(user_id, text)

@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def show_profile(message):
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "💳 شارژ حساب")
def charge_account(message):
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "📨 تیکت پشتیبانی")
def support_ticket(message):
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    send_main_menu(message.chat.id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
