from flask import Flask, request
import telebot
import os
import json

# === Configurations ===
API_TOKEN = '8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs'
CHANNEL_ID = -1002891641618
ADMIN_ID = 368422936
CHANNEL_LINK = 'https://t.me/appleid035'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# === Data Files ===
APPLEID_FILE = 'apple_ids.json'
PAYMENTS_FILE = 'payments.json'
USERS_FILE = 'users.json'

# === Helper functions ===
def load_data(filename, default):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return default

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        return False

def get_user(user_id):
    users = load_data(USERS_FILE, {})
    return users.get(str(user_id), {})

def set_user(user_id, data):
    users = load_data(USERS_FILE, {})
    users[str(user_id)] = data
    save_data(USERS_FILE, users)

# === Load existing Apple IDs ===
products = load_data(APPLEID_FILE, [
    {"name": "جیمیل 2018 قدیمی", "price": 110000, "stock": 9},
    {"name": "جیمیل 2025 جدید", "price": 77000, "stock": 12}
])

# === Flask Routes ===
@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data(as_text=True))
    bot.process_new_updates([update])
    return 'ok'

# === Bot Menus ===
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

# === Handlers ===
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if not is_member(user_id):
        join_markup = telebot.types.InlineKeyboardMarkup()
        join_markup.add(telebot.types.InlineKeyboardButton("عضویت در کانال", url=CHANNEL_LINK))
        bot.send_message(user_id, "برای استفاده از ربات ابتدا در کانال عضو شوید و سپس /start را بزنید.", reply_markup=join_markup)
        return

    user = get_user(user_id)
    if not user.get("mobile"):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = telebot.types.KeyboardButton("📱 ارسال شماره موبایل", request_contact=True)
        markup.add(btn)
        bot.send_message(user_id, "لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=markup)
    else:
        send_main_menu(user_id)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    mobile = message.contact.phone_number

    user = get_user(user_id)
    user["mobile"] = mobile
    set_user(user_id, user)

    bot.send_message(message.chat.id, "✅ شماره شما با موفقیت ثبت شد.")
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == "💲 قیمت و موجودی")
def show_prices(message):
    if not is_member(message.from_user.id):
        bot.send_message(message.chat.id, "❌ لطفاً ابتدا در کانال عضو شوید و سپس دوباره تلاش کنید.")
        return
    text = "📦 لیست محصولات:\n"
    for p in products:
        text += f"- {p['name']} | 💰 قیمت: {p['price']:,} تومان | 📦 موجودی: {p['stock']} عدد\n"
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "💳 شارژ حساب")
def charge_account(message):
    if not is_member(message.from_user.id):
        bot.send_message(message.chat.id, "❌ لطفاً ابتدا در کانال عضو شوید و سپس دوباره تلاش کنید.")
        return
    bot.send_message(message.chat.id, """برای شارژ حساب لطفاً کارت به کارت کنید و تصویر رسید را ارسال نمایید:
💳 کارت: XXXX-XXXX-XXXX-XXXX
سپس تصویر رسید را ارسال کنید.""")
    bot.register_next_step_handler(message, receive_receipt)

def receive_receipt(message):
    if message.photo:
        payments = load_data(PAYMENTS_FILE, [])
        payment_id = len(payments) + 1
        payments.append({
            "id": payment_id,
            "user": message.from_user.id,
            "status": "pending"
        })
        save_data(PAYMENTS_FILE, payments)

        approve_markup = telebot.types.InlineKeyboardMarkup()
        approve_markup.add(
            telebot.types.InlineKeyboardButton("✅ تایید", callback_data=f"approve_{payment_id}"),
            telebot.types.InlineKeyboardButton("❌ رد", callback_data=f"reject_{payment_id}")
        )

        bot.send_message(ADMIN_ID, f"📥 رسید جدید از کاربر {message.from_user.id} (شناسه پرداخت: {payment_id})", reply_markup=approve_markup)
        bot.send_message(message.chat.id, "✅ رسید شما ارسال شد و منتظر تایید مدیر است.")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

# === Admin Approval ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("approve_") or call.data.startswith("reject_"))
def handle_payment_decision(call):
    payments = load_data(PAYMENTS_FILE, [])
    action, pid = call.data.split("_")
    pid = int(pid)

    for payment in payments:
        if payment["id"] == pid:
            if action == "approve":
                payment["status"] = "approved"
                bot.send_message(payment["user"], "✅ پرداخت شما تایید شد. موجودی شما افزایش یافت.")
                bot.send_message(CHANNEL_ID, f"💰 پرداخت کاربر {payment['user']} تایید شد.")
            elif action == "reject":
                payment["status"] = "rejected"
                bot.send_message(payment["user"], "❌ پرداخت شما رد شد. لطفاً مجدداً اقدام کنید.")
            break

    save_data(PAYMENTS_FILE, payments)
    bot.answer_callback_query(call.id, "عملیات انجام شد.")

# === Fallback for any unhandled text ===
@bot.message_handler(func=lambda m: True)
def fallback(message):
    send_main_menu(message.chat.id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
