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

# ------------------------ خرید اپل‌آیدی --------------------------
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
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_name_personal(m, product_id, "wallet"))
            return
        account = give_account(product_id, call.from_user.id)
        if account:
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
            bot.send_message(call.message.chat.id, account_details, parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "❌ موجودی اکانت این محصول به پایان رسیده.")
        bot.send_message(ADMIN_ID, f"🔔 خرید با کیف پول توسط {user['name']}\nمحصول: {product['name']}")
    else:
        bot.send_message(call.message.chat.id, "❌ موجودی کیف پول شما کافی نیست.")

def save_name_personal(message, product_id, method):
    name = message.text
    user = get_user(message.from_user.id)
    note = f"خرید اپل آیدی شخصی (روش: {method})\nکاربر: {user['name']} ({user['mobile']})\nنام صاحب اپل آیدی: {name}"
    bot.send_message(message.chat.id, f"اسمتون ثبت شد: {name}\n\nسفارش اپل‌آیدی شخصی برای ادمین ارسال شد و طی ۱ تا ۲۴ ساعت ساخته و ارسال می‌شود.")
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("پاسخ به کاربر", callback_data=f"admin_personal_answer_{user['id']}"))
    bot.send_message(ADMIN_ID, f"🔔 {note}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if product_id == 3:
        bot.send_message(call.message.chat.id, f"لطفاً اسم و فامیل صاحب اپل آیدی را وارد کنید:")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_name_personal(m, product_id, "card"))
        return
    bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز و تصویر رسید را ارسال کنید:\n\n{CARD_NUMBER}")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_receipt(m, product, False))

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_personal_answer_"))
def admin_personal_answer(call):
    user_id = int(call.data.split("_")[-1])
    bot.send_message(call.message.chat.id, "پاسخ به کاربر را وارد کنید (اطلاعات اکانت):")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: send_personal_answer(m, user_id))

def send_personal_answer(message, user_id):
    bot.send_message(user_id, f"👑 پاسخ ادمین برای اپل‌آیدی شخصی:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام برای کاربر ارسال شد.")

def receive_receipt(message, product, is_personal):
    if message.photo:
        if is_personal:
            bot.send_message(message.chat.id, "لطفاً اسم صاحب اپل آیدی را وارد کنید:")
            bot.register_next_step_handler(message, lambda m: save_name_personal(m, product["id"], "card"))
            photo_id = message.photo[-1].file_id
            user = get_user(message.from_user.id)
            bot.send_photo(ADMIN_ID, photo_id, caption=f"رسید پرداخت اپل آیدی شخصی از {user['name']} ({user['mobile']})")
            return
        payment = {
            "user_id": message.from_user.id,
            "name": message.from_user.first_name,
            "product": product["name"],
            "amount": product["price"],
            "type": "buy",
            "status": "pending"
        }
        add_payment(payment)
        photo_id = message.photo[-1].file_id
        user = get_user(message.from_user.id)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("تحویل اکانت آماده", callback_data=f"admin_sendacc_{product['id']}_{user['id']}"))
        bot.send_photo(ADMIN_ID, photo_id, caption=f"رسید پرداخت {user['name']} - محصول: {product['name']}", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ رسید شما ارسال شد، منتظر تایید مدیر باشید.")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_sendacc_"))
def admin_sendacc(call):
    _, _, pid, uid = call.data.split("_")
    pid = int(pid)
    uid = int(uid)
    account = give_account(pid, uid)
    if account:
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
        bot.send_message(uid, account_details, parse_mode="Markdown")
        bot.send_message(call.message.chat.id, "اکانت برای کاربر ارسال شد.")
    else:
        bot.send_message(call.message.chat.id, "موجودی اکانت این محصول صفر است.")

# ------------------------ ادامه بخش‌ها مثل قبل ------------------------

# در ادامه، تمام بخش‌های قبلی (تیکت، شارژ حساب، حساب کاربری، پنل مدیریت و...)  
# **عیناً همون قبلیه** (اگر نیاز داری همین نسخه رو کامل و تمیز با همه این اصلاحیه‌ها برات یک‌جا بنویسم،  
# پیام بده تا کل کد رو آماده و شسته‌رفته برایت قرار بدم.)

# فقط بخش افزودن اکانت آماده رو هم اینجوری بگذار:

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
    bot.send_message(
        message.chat.id,
        "اکانت را به این صورت وارد کن (هر مورد را در یک خط جدا بنویس):\n"
        "ایمیل\n"
        "پسورد\n"
        "سوال امنیتی ۱\n"
        "سوال امنیتی ۲\n"
        "سوال امنیتی ۳\n"
        "تاریخ تولد\n"
        "قوانین و توضیحات"
    )
    bot.register_next_step_handler(message, lambda m: save_account_ready(m, product["id"]))

def save_account_ready(message, product_id):
    lines = message.text.strip().split('\n')
    if len(lines) < 7:
        bot.send_message(message.chat.id, "فرمت صحیح نیست! باید دقیقاً ۷ خط وارد کنید.")
        return
    account = {
        "email": lines[0].strip(),
        "pass": lines[1].strip(),
        "q1": lines[2].strip(),
        "q2": lines[3].strip(),
        "q3": lines[4].strip(),
        "birth": lines[5].strip(),
        "rules": lines[6].strip()
    }
    accounts = load_accounts()
    accounts[str(product_id)].append(account)
    save_accounts(accounts)
    for p in PRODUCTS:
        if p["id"] == product_id:
            p["stock"] += 1
    bot.send_message(message.chat.id, f"✅ اکانت با جزییات کامل اضافه شد. الان {len(accounts[str(product_id)])} اکانت آماده داری.")

# ------------------------ لیست اعضا با موبایل و آی‌دی ------------------------
@bot.message_handler(func=lambda m: m.text == "لیست اعضا 👥" and is_admin(m.from_user.id))
def show_users_list(message):
    users = load_data(USERS_FILE, {})
    msg = f"👥 تعداد کل اعضا: {len(users)}\n"
    preview = "\n".join([f"{u['name']} | {u['mobile']} | {u['id']}" for u in users.values()][:30])
    if len(users) > 30:
        msg += preview + "\n... (بقیه نمایش داده نشد)"
    else:
        msg += preview
    bot.send_message(message.chat.id, msg)

# ------------------------ مدیریت حرفه‌ای تیکت‌ها (ادمین) ------------------------
@bot.message_handler(func=lambda m: m.text == "مدیریت تیکت‌ها 🎫" and is_admin(m.from_user.id))
def admin_tickets_panel(message):
    supports = get_supports()
    if not supports:
        bot.send_message(message.chat.id, "هیچ تیکتی وجود ندارد.")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    for t in supports[-20:][::-1]:
        status = "باز" if t["status"] == "open" else "بسته"
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"#{t['ticket_id']} | {t['user_name']} | {status}",
                callback_data=f"admin_view_ticket_{t['ticket_id']}"
            )
        )
    bot.send_message(message.chat.id, "🗂 لیست تیکت‌ها (۲۰ مورد آخر):", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_view_ticket_"))
def admin_view_ticket_callback(call):
    ticket_id = int(call.data.split("_")[-1])
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if not ticket:
        bot.send_message(call.message.chat.id, "تیکت پیدا نشد.")
        return
    chat_history = ""
    for msg in ticket["messages"]:
        sender = "کاربر" if msg["sender"] == "user" else "ادمین"
        chat_history += f"{sender}: {msg['text']}\n"
    markup = telebot.types.InlineKeyboardMarkup()
    if ticket["status"] == "open":
        markup.add(
            telebot.types.InlineKeyboardButton("پاسخ", callback_data=f"admin_reply_{ticket_id}"),
            telebot.types.InlineKeyboardButton("بستن تیکت", callback_data=f"close_ticket_{ticket_id}")
        )
    else:
        markup.add(
            telebot.types.InlineKeyboardButton("باز کردن تیکت", callback_data=f"reopen_ticket_{ticket_id}")
        )
    bot.send_message(call.message.chat.id, f"تیکت #{ticket_id}\n{chat_history}", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reopen_ticket_"))
def reopen_ticket(call):
    ticket_id = int(call.data.split("_")[-1])
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if ticket:
        ticket["status"] = "open"
        save_data(SUPPORT_FILE, supports)
        bot.send_message(call.message.chat.id, "✅ تیکت باز شد و می‌توانید پاسخ دهید.")
        bot.send_message(ticket["user_id"], f"تیکت #{ticket_id} شما مجدداً توسط مدیریت باز شد.")

# ----------------- بقیه کد (مثل قبل) -----------------
# تو هر بخش قبلی نیاز داشتی، به همین صورت استفاده کن
# اگر نسخه کامل‌شده و ادغام‌شده خواستی، پیام بده تا کل فایل تمیزش رو بذارم 👑

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
