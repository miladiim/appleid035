from flask import Flask, request
import telebot
import os
import json
import datetime

API_TOKEN = '8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs'
ADMIN_ID = 368422936
CARD_NUMBER = '6037-9911-9073-3544'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

USERS_FILE = 'users.json'
PAYMENTS_FILE = 'payments.json'
SUPPORT_FILE = 'support.json'
ACCOUNTS_FILE = 'accounts.json'

PRODUCTS = [
    {"id": 1, "name": "جیمیل 2018 قدیمی", "price": 250000, "stock": 9},
    {"id": 2, "name": "جیمیل 2025 جدید (کیفیت بالا)", "price": 200000, "stock": 12},
    {"id": 3, "name": "اپل‌آیدی با اطلاعات شخصی شما", "price": 300000, "stock": 1000},
]

def load_data(filename, default):
    if not os.path.exists(filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
    with open(filename, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return default

def save_data(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user(user_id):
    users = load_data(USERS_FILE, {})
    return users.get(str(user_id))

def set_user(user_id, user):
    users = load_data(USERS_FILE, {})
    users[str(user_id)] = user
    save_data(USERS_FILE, users)

def add_payment(payment):
    payments = load_data(PAYMENTS_FILE, [])
    payments.append(payment)
    save_data(PAYMENTS_FILE, payments)

def get_payments():
    return load_data(PAYMENTS_FILE, [])

def add_support(support):
    supports = load_data(SUPPORT_FILE, [])
    supports.append(support)
    save_data(SUPPORT_FILE, supports)

def get_supports():
    return load_data(SUPPORT_FILE, [])

def load_accounts():
    return load_data(ACCOUNTS_FILE, {"1": [], "2": []})

def save_accounts(data):
    save_data(ACCOUNTS_FILE, data)

def give_account(product_id, user_id):
    accounts = load_accounts()
    product_accounts = accounts.get(str(product_id), [])
    if product_accounts:
        account = product_accounts.pop(0)
        save_accounts(accounts)
        user = get_user(user_id)
        if "accounts" not in user:
            user["accounts"] = []
        user["accounts"].append({
            "product_id": product_id,
            "email": account.get("email"),
            "pass": account.get("pass"),
            "q1": account.get("q1", ""),
            "q2": account.get("q2", ""),
            "q3": account.get("q3", ""),
            "birth": account.get("birth", ""),
            "rules": account.get("rules", ""),
            "datetime": str(datetime.datetime.now())[:19]
        })
        set_user(user_id, user)
        for p in PRODUCTS:
            if p["id"] == product_id:
                p["stock"] = max(0, p["stock"] - 1)
        return account
    else:
        return None

def is_admin(user_id):
    return user_id == ADMIN_ID

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
    if is_admin(chat_id):
        markup.row(telebot.types.KeyboardButton("پنل مدیریت 👑"))
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
    user = get_user(user_id)
    if not user:
        set_user(user_id, {
            "id": user_id,
            "name": message.from_user.first_name,
            "mobile": "",
            "joined": str(datetime.datetime.now())[:19],
            "wallet": 0,
            "purchases": 0
        })
    user = get_user(user_id)
    if not user.get("mobile"):
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(telebot.types.KeyboardButton("📱 ارسال شماره موبایل", request_contact=True))
        bot.send_message(user_id, "برای ادامه، لطفاً شماره موبایل خود را ارسال کنید:", reply_markup=markup)
        return
    send_main_menu(user_id)

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    mobile = message.contact.phone_number
    user = get_user(user_id)
    if user:
        user["mobile"] = mobile
        set_user(user_id, user)
        bot.send_message(user_id, "✅ شماره موبایل شما ثبت شد.")
        send_main_menu(user_id)

# ===== خرید اپل‌آیدی (شخصی: اول رسید بعد اسم) =====
@bot.message_handler(func=lambda m: m.text == "🛒 خرید اپل‌آیدی")
def buy_appleid(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for p in PRODUCTS:
        markup.add(telebot.types.InlineKeyboardButton(
            f"{p['name']} ({p.get('stock', 'نامشخص')} موجودی)", callback_data=f"select_{p['id']}"
        ))
    bot.send_message(message.chat.id, "🎉 یکی از سرویس‌های زیر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("select_"))
def product_info(call):
    product_id = int(call.data.split("_")[1])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    user = get_user(call.from_user.id)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    text = (
        f"🎉 سرویس: {product['name']}\n"
        f"💸 قیمت هر اکانت: {product['price']:,} تومان\n"
        f"🔢 تعداد اکانت‌ها: {product['stock']}\n"
        f"💳 موجودی شما: {user['wallet']:,} تومان\n"
        f"💰 قیمت کل: {product['price']:,} تومان\n"
        "------\n"
        "روش پرداخت را انتخاب کنید:"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{product_id}"),
        telebot.types.InlineKeyboardButton("💰 کیف پول", callback_data=f"pay_wallet_{product_id}")
    )
    bot.send_message(call.message.chat.id, text, reply_markup=markup)

# ---- خرید اپل‌آیدی شخصی: کارت به کارت (رسید، بعد اسم) ----
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if product_id == 3:
        bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز و تصویر رسید را ارسال کنید:\n\n{CARD_NUMBER}")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_personal_receipt(m, product))
        return
    bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز و تصویر رسید را ارسال کنید:\n\n{CARD_NUMBER}")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_receipt(m, product, False))

def receive_personal_receipt(message, product):
    if message.photo:
        photo_id = message.photo[-1].file_id
        user = get_user(message.from_user.id)
        bot.send_message(message.chat.id, "✅ رسید دریافت شد.\n\nلطفاً اسم و فامیل صاحب اپل‌آیدی را وارد کنید:")
        bot.register_next_step_handler(message, lambda m: save_personal_name(m, product, photo_id))
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

def save_personal_name(message, product, photo_id):
    name = message.text
    user = get_user(message.from_user.id)
    caption = f"خرید اپل آیدی شخصی\nکاربر: {user['name']} ({user['mobile']})\nنام صاحب اپل‌آیدی: {name}"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("پاسخ به کاربر", callback_data=f"admin_personal_answer_{user['id']}"))
    bot.send_photo(ADMIN_ID, photo_id, caption=caption, reply_markup=markup)
    bot.send_message(message.chat.id, f"✅ سفارش شما ثبت شد و برای ادمین ارسال شد.\nتا ۲۴ ساعت اطلاعات اپل‌آیدی جدید دریافت می‌کنید.")
    send_main_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_personal_answer_"))
def admin_personal_answer(call):
    user_id = int(call.data.split("_")[-1])
    bot.send_message(call.message.chat.id, "پاسخ به کاربر را وارد کنید (اطلاعات اکانت):")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: send_personal_answer(m, user_id))

def send_personal_answer(message, user_id):
    bot.send_message(user_id, f"👑 پاسخ ادمین برای اپل‌آیدی شخصی:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام برای کاربر ارسال شد.")

# ---- خرید اپل‌آیدی شخصی: کیف پول (اول پرداخت، بعد اسم) ----
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_wallet_"))
def pay_wallet(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    user = get_user(call.from_user.id)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if product["stock"] < 1:
        bot.send_message(call.message.chat.id, "❌ موجودی این محصول کافی نیست.")
        return
    if user["wallet"] >= product["price"]:
        if product_id == 3:
            user["wallet"] -= product["price"]
            user["purchases"] += 1
            set_user(call.from_user.id, user)
            bot.send_message(call.message.chat.id, "✅ پرداخت موفق!\nلطفاً اسم و فامیل صاحب اپل‌آیدی را وارد کنید:")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_personal_name_wallet(m, product))
            return
        # محصولات آماده
        account = give_account(product_id, call.from_user.id)
        if account:
            send_ready_account(call.message.chat.id, account)
        else:
            bot.send_message(call.message.chat.id, "❌ موجودی اکانت این محصول به پایان رسیده.")
        bot.send_message(ADMIN_ID, f"🔔 خرید با کیف پول توسط {user['name']}\nمحصول: {product['name']}")
    else:
        bot.send_message(call.message.chat.id, "❌ موجودی کیف پول شما کافی نیست.")

def save_personal_name_wallet(message, product):
    name = message.text
    user = get_user(message.from_user.id)
    caption = f"خرید اپل آیدی شخصی با کیف پول\nکاربر: {user['name']} ({user['mobile']})\nنام صاحب اپل‌آیدی: {name}"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("پاسخ به کاربر", callback_data=f"admin_personal_answer_{user['id']}"))
    bot.send_message(ADMIN_ID, caption, reply_markup=markup)
    bot.send_message(message.chat.id, f"✅ سفارش شما ثبت شد و برای ادمین ارسال شد.\nتا ۲۴ ساعت اطلاعات اپل‌آیدی جدید دریافت می‌کنید.")
    send_main_menu(message.chat.id)

# ---- ارسال اطلاعات اکانت آماده ----
def send_ready_account(chat_id, account):
    account_details = (
        f"✅ خرید موفق!\n\n"
        f"📧 ایمیل: `{account['email']}`\n"
        f"🔑 پسورد: `{account['pass']}`\n"
        f"🟢 سوال۱: {account.get('q1','')}\n"
        f"🟢 سوال۲: {account.get('q2','')}\n"
        f"🟢 سوال۳: {account.get('q3','')}\n"
        f"📆 تولد: {account.get('birth','')}\n"
        f"📜 قوانین: {account.get('rules','')}\n"
    )
    bot.send_message(chat_id, account_details, parse_mode="Markdown")

# ===== ادامه امکانات (پنل مدیریت، تیکت، شارژ و ...) مثل نسخه‌های قبلی =====
# اگر همین نسخه نهایی رو خواستی با تمام امکانات (بدون هیچ تغییری)، کامل می‌فرستم،
# کافی بگی فقط دقیقاً همین نسخه رو یکجا بده.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
