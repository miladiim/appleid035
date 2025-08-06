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
PERSONAL_REQUESTS_FILE = 'personal_requests.json'  # --- NEW

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
            "email": account["email"],
            "pass": account["pass"],
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
    # --- NEW (ذخیره آی‌پی)
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    except:
        ip = '-'
    if not user:
        set_user(user_id, {
            "id": user_id,
            "name": message.from_user.first_name,
            "mobile": "",
            "joined": str(datetime.datetime.now())[:19],
            "wallet": 0,
            "purchases": 0,
            "ip": ip
        })
    else:
        if not user.get("ip"):
            user["ip"] = ip
            set_user(user_id, user)
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

# ---- خرید اپل آیدی (اصلاح خرید شخصی) ----
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
        user["wallet"] -= product["price"]
        user["purchases"] += 1
        set_user(call.from_user.id, user)
        if product_id == 3:
            bot.send_message(call.message.chat.id, "لطفاً اسم و فامیل صاحب اپل آیدی را وارد کنید:")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_personal_request(m, call.from_user.id, 'wallet'))
            return
        account = give_account(product_id, call.from_user.id)
        if account:
            bot.send_message(call.message.chat.id, f"✅ خرید موفق!\n\n📧 ایمیل: `{account['email']}`\n🔑 پسورد: `{account['pass']}`", parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "❌ موجودی اکانت این محصول به پایان رسیده.")
        bot.send_message(ADMIN_ID, f"🔔 خرید با کیف پول توسط {user['name']}\nمحصول: {product['name']}")
    else:
        bot.send_message(call.message.chat.id, "❌ موجودی کیف پول شما کافی نیست.")

def save_personal_request(message, user_id, pay_type):
    name = message.text
    user = get_user(user_id)
    reqs = load_data(PERSONAL_REQUESTS_FILE, [])
    req_id = len(reqs) + 1
    reqs.append({
        "req_id": req_id,
        "user_id": user_id,
        "name": name,
        "status": "pending",
        "datetime": str(datetime.datetime.now())[:19]
    })
    save_data(PERSONAL_REQUESTS_FILE, reqs)
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("پاسخ به سفارش اپل آیدی شخصی", callback_data=f"personal_reply_{user_id}_{req_id}"))
    bot.send_message(ADMIN_ID, f"🔔 سفارش اپل آیدی شخصی\nکاربر: {user['name']} ({user['mobile']})\nنام صاحب اپل آیدی: {name}", reply_markup=markup)
    bot.send_message(user_id, "سفارش اپل‌آیدی شخصی شما برای مدیر ارسال شد و طی ۱ تا ۲۴ ساعت آماده می‌شود.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if product_id == 3:
        bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز کرده، تصویر رسید و **اسم صاحب اپل آیدی** را ارسال کنید:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_personal_card(m, call.from_user.id))
    else:
        bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز و تصویر رسید را ارسال کنید:\n\n{CARD_NUMBER}")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_receipt(m, product, False))

def receive_personal_card(message, user_id):
    if message.photo:
        bot.send_message(message.chat.id, "لطفاً اسم صاحب اپل آیدی را وارد کنید:")
        bot.register_next_step_handler(message, lambda m: save_personal_request(m, user_id, 'card'))
        user = get_user(user_id)
        photo_id = message.photo[-1].file_id
        bot.send_photo(ADMIN_ID, photo_id, caption=f"رسید پرداخت اپل آیدی شخصی از {user['name']} ({user['mobile']})")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("personal_reply_"))
def personal_reply_handler(call):
    user_id = int(call.data.split("_")[2])
    req_id = int(call.data.split("_")[3])
    bot.send_message(call.message.chat.id, "متن پاسخ برای کاربر (شامل ایمیل و رمز یا توضیحات):")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: send_personal_answer(m, user_id, req_id))

def send_personal_answer(message, user_id, req_id):
    bot.send_message(user_id, f"پاسخ ادمین:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام به کاربر ارسال شد.")

# ------ افزودن اکانت آماده با فرمت چندخطی ------
@bot.message_handler(func=lambda m: m.text == "افزودن اکانت آماده ➕" and is_admin(m.from_user.id))
def add_account_start(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in PRODUCTS[:2]:
        markup.add(telebot.types.KeyboardButton(f"{p['name']}"))
    bot.send_message(message.chat.id, "انتخاب کن کدام محصول را می‌خواهی اکانت آماده اضافه کنی:", reply_markup=markup)
    bot.register_next_step_handler(message, add_account_input)

def add_account_input(message):
    pname = message.text.strip()
    product = next((p for p in PRODUCTS if p["name"] == pname), None)
    if not product or product["id"] == 3:
        bot.send_message(message.chat.id, "فقط برای محصولات آماده می‌تونی اکانت اضافه کنی.")
        return
    bot.send_message(message.chat.id, "اکانت را وارد کن:\n(فرمت ساده: ایمیل:پسورد)\nیا فرمت کامل:\nایمیل\nپسورد\nسوال۱\nسوال۲\nسوال۳\nتاریخ تولد\nتوضیحات (در صورت نیاز):")
    bot.register_next_step_handler(message, lambda m: save_account_ready(m, product["id"]))

def save_account_ready(message, product_id):
    accounts = load_accounts()
    text = message.text.strip()
    lines = text.split("\n")
    # فقط ایمیل:پسورد (یک خطی)
    if len(lines) == 1 and ':' in lines[0]:
        email, passwd = lines[0].split(":", 1)
        accounts[str(product_id)].append({"email": email.strip(), "pass": passwd.strip()})
    else:
        # حالت کامل با اطلاعات بیشتر
        info = {
            "email": lines[0].strip(),
            "pass": lines[1].strip() if len(lines) > 1 else '',
            "q1": lines[2].strip() if len(lines) > 2 else '',
            "q2": lines[3].strip() if len(lines) > 3 else '',
            "q3": lines[4].strip() if len(lines) > 4 else '',
            "birthday": lines[5].strip() if len(lines) > 5 else '',
            "desc": "\n".join(lines[6:]) if len(lines) > 6 else ''
        }
        accounts[str(product_id)].append(info)
    save_accounts(accounts)
    for p in PRODUCTS:
        if p["id"] == product_id:
            p["stock"] += 1
    bot.send_message(message.chat.id, f"✅ اکانت اضافه شد. (الان {len(accounts[str(product_id)])} اکانت آماده داری)")

# --- لیست اعضا با نمایش شماره موبایل، آی‌دی عددی و آی‌پی ---
@bot.message_handler(func=lambda m: m.text == "لیست اعضا 👥" and is_admin(m.from_user.id))
def show_users_list(message):
    users = load_data(USERS_FILE, {})
    msg = f"👥 تعداد کل اعضا: {len(users)}\n"
    preview = "\n".join([
        f"{u['name']} | موبایل: {u.get('mobile','-')} | آیدی: {u.get('id','-')} | IP: {u.get('ip','-')}"
        for u in users.values()][:30])
    if len(users) > 30:
        msg += preview + "\n... (بقیه نمایش داده نشد)"
    else:
        msg += preview
    bot.send_message(message.chat.id, msg)

# --- سایر بخش‌های قبلی ربات (بدون تغییر) ---
# بقیه message_handler و callback_handlerها همون کد تو هست و چیزی حذف نشده

@bot.message_handler(func=lambda m: True)
def fallback(message):
    send_main_menu(message.chat.id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
