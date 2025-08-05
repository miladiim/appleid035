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
        # اگر شخصی بود، بعد از پرداخت اسم بگیرد!
        if product_id == 3:
            bot.send_message(call.message.chat.id, "لطفاً اسم و فامیل صاحب اپل آیدی را وارد کنید:")
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_name_personal(m, product_id))
            return
        # تحویل اپل آیدی آماده
        account = give_account(product_id, call.from_user.id)
        if account:
            bot.send_message(call.message.chat.id, f"✅ خرید موفق!\n\n📧 ایمیل: `{account['email']}`\n🔑 پسورد: `{account['pass']}`", parse_mode="Markdown")
        else:
            bot.send_message(call.message.chat.id, "❌ موجودی اکانت این محصول به پایان رسیده.")
        bot.send_message(ADMIN_ID, f"🔔 خرید با کیف پول توسط {user['name']}\nمحصول: {product['name']}")
    else:
        bot.send_message(call.message.chat.id, "❌ موجودی کیف پول شما کافی نیست.")

def save_name_personal(message, product_id):
    name = message.text
    bot.send_message(message.chat.id, f"اسمتون ثبت شد: {name}\n\nسفارش اپل‌آیدی شخصی برای ادمین ارسال شد و طی ۱ تا ۲۴ ساعت ساخته و ارسال می‌شود.")
    # اطلاع به ادمین برای ساخت اپل آیدی شخصی
    user = get_user(message.from_user.id)
    bot.send_message(ADMIN_ID, f"🔔 سفارش اپل آیدی شخصی\nکاربر: {user['name']} ({user['mobile']})\nنام صاحب اپل آیدی: {name}")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if product_id == 3:
        bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز کرده، تصویر رسید و **اسم صاحب اپل آیدی** را ارسال کنید:")
    else:
        bot.send_message(call.message.chat.id, f"💳 لطفاً مبلغ {product['price']:,} تومان را به شماره کارت زیر واریز و تصویر رسید را ارسال کنید:\n\n{CARD_NUMBER}")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_receipt(m, product, product_id==3))

def receive_receipt(message, product, is_personal):
    if message.photo:
        if is_personal:
            bot.send_message(message.chat.id, "لطفاً اسم صاحب اپل آیدی را وارد کنید:")
            bot.register_next_step_handler(message, lambda m: save_name_personal(m, product["id"]))
            # ادمین در پیام قبلی رسید را دریافت می‌کند
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
        # ادمین با دکمه تحویل اکانت تایید و تحویل می‌دهد
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
        bot.send_message(uid, f"✅ خرید موفق!\n\n📧 ایمیل: `{account['email']}`\n🔑 پسورد: `{account['pass']}`", parse_mode="Markdown")
        bot.send_message(call.message.chat.id, "اکانت برای کاربر ارسال شد.")
    else:
        bot.send_message(call.message.chat.id, "موجودی اکانت این محصول صفر است.")

# ------------------------ شارژ حساب --------------------------
@bot.message_handler(func=lambda m: m.text == "💳 شارژ حساب")
def charge_account(message):
    bot.send_message(message.chat.id, f"مبلغ دلخواه خود را به شماره کارت زیر واریز کنید و رسید را ارسال کنید:\n\n{CARD_NUMBER}")
    bot.register_next_step_handler(message, receive_charge_receipt)

def receive_charge_receipt(message):
    if message.photo:
        user = get_user(message.from_user.id)
        photo_id = message.photo[-1].file_id
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("پاسخ (شارژ کن)", callback_data=f"admin_charge_{user['id']}"))
        bot.send_photo(ADMIN_ID, photo_id, caption=f"درخواست شارژ کیف پول از {user['name']} ({user['mobile']})", reply_markup=markup)
        bot.send_message(message.chat.id, "✅ رسید ارسال شد. منتظر تایید مدیر باشید.")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_charge_"))
def admin_charge_user_call(call):
    user_id = int(call.data.split("_")[2])
    bot.send_message(call.message.chat.id, "مبلغ شارژ را برای کاربر وارد کنید (عدد تومان):")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: do_admin_charge(m, user_id))

def do_admin_charge(message, user_id):
    if message.text.isdigit():
        user = get_user(user_id)
        user["wallet"] += int(message.text)
        set_user(user_id, user)
        bot.send_message(user_id, f"💰 کیف پول شما {int(message.text):,} تومان شارژ شد.")
        bot.send_message(message.chat.id, "✅ کیف پول کاربر شارژ شد.")
    else:
        bot.send_message(message.chat.id, "فقط عدد وارد کنید:")
        bot.register_next_step_handler(message, lambda m: do_admin_charge(m, user_id))

# ------------------------ پنل مدیریت ویژه ادمین ------------------------
@bot.message_handler(func=lambda m: m.text == "پنل مدیریت 👑" and is_admin(m.from_user.id))
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("لیست اعضا 👥"))
    markup.add(telebot.types.KeyboardButton("شارژ مستقیم کاربر ➕"))
    markup.add(telebot.types.KeyboardButton("پیام همگانی 📢"))
    markup.add(telebot.types.KeyboardButton("مدیریت موجودی محصولات 🗃"))
    markup.add(telebot.types.KeyboardButton("افزودن اکانت آماده ➕"))
    markup.add(telebot.types.KeyboardButton("بازگشت 🔙"))
    bot.send_message(message.chat.id, "🎛 پنل مدیریت:", reply_markup=markup)

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
    bot.send_message(message.chat.id, "اکانت را به صورت:\nایمیل:پسورد\nوارد کن (مثال: test@mail.com:pass123):")
    bot.register_next_step_handler(message, lambda m: save_account_ready(m, product["id"]))

def save_account_ready(message, product_id):
    try:
        email, passwd = message.text.split(":")
        accounts = load_accounts()
        accounts[str(product_id)].append({"email": email.strip(), "pass": passwd.strip()})
        save_accounts(accounts)
        for p in PRODUCTS:
            if p["id"] == product_id:
                p["stock"] += 1
        bot.send_message(message.chat.id, f"✅ اکانت اضافه شد. (الان {len(accounts[str(product_id)])} اکانت آماده داری)")
    except:
        bot.send_message(message.chat.id, "فرمت صحیح نیست. به صورت ایمیل:پسورد وارد کن.")

# ------------------- باقی مانده مدیریت و بازگشت و پروفایل مثل قبل --------------------
@bot.message_handler(func=lambda m: m.text == "لیست اعضا 👥" and is_admin(m.from_user.id))
def show_users_list(message):
    users = load_data(USERS_FILE, {})
    msg = f"👥 تعداد کل اعضا: {len(users)}\n"
    preview = "\n".join([f"{u['name']} | {u['mobile']}" for u in users.values()][:30])
    if len(users) > 30:
        msg += preview + "\n... (بقیه نمایش داده نشد)"
    else:
        msg += preview
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "مدیریت موجودی محصولات 🗃" and is_admin(m.from_user.id))
def manage_stock(message):
    markup = telebot.types.InlineKeyboardMarkup()
    for p in PRODUCTS:
        markup.add(
            telebot.types.InlineKeyboardButton(
                f"{p['name']} ({p['stock']} موجودی)",
                callback_data=f"editstock_{p['id']}"
            )
        )
    bot.send_message(message.chat.id, "برای ویرایش موجودی یک محصول، انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("editstock_"))
def edit_stock(call):
    product_id = int(call.data.split("_")[1])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.send_message(call.message.chat.id, "محصول پیدا نشد.")
        return
    bot.send_message(call.message.chat.id,
        f"🔹 نام محصول: {product['name']}\n🔢 موجودی فعلی: {product['stock']}\n\n"
        "عدد جدید موجودی را وارد کنید:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: set_stock(m, product_id))

def set_stock(message, product_id):
    if not message.text.isdigit():
        bot.send_message(message.chat.id, "لطفاً فقط عدد وارد کنید:")
        bot.register_next_step_handler(message, lambda m: set_stock(m, product_id))
        return
    new_stock = int(message.text)
    for p in PRODUCTS:
        if p["id"] == product_id:
            p["stock"] = new_stock
            break
    bot.send_message(message.chat.id, f"✅ موجودی محصول به {new_stock} تغییر کرد.")

@bot.message_handler(func=lambda m: m.text == "شارژ مستقیم کاربر ➕" and is_admin(m.from_user.id))
def admin_charge_user_start(message):
    bot.send_message(message.chat.id, "آی‌دی عددی یا شماره موبایل کاربر را وارد کنید:")
    bot.register_next_step_handler(message, admin_charge_user_amount)

def admin_charge_user_amount(message):
    query = message.text.strip()
    users = load_data(USERS_FILE, {})
    target_user = None
    if query.isdigit() and query in users:
        target_user = users[query]
    else:
        for u in users.values():
            if u.get("mobile") == query:
                target_user = u
                break
    if not target_user:
        bot.send_message(message.chat.id, "کاربر پیدا نشد. دوباره تلاش کنید یا آی‌دی/شماره را درست وارد کنید.")
        return
    bot.send_message(message.chat.id, f"مبلغ شارژ (تومان) برای {target_user['name']} ({target_user['mobile']}) را وارد کنید:")
    bot.register_next_step_handler(message, lambda m: do_admin_charge(m, target_user["id"]))

def do_admin_charge(message, user_id):
    if message.text.isdigit():
        user = get_user(user_id)
        user["wallet"] += int(message.text)
        set_user(user_id, user)
        bot.send_message(message.chat.id, f"کیف پول کاربر به مبلغ {message.text} تومان شارژ شد.")
        bot.send_message(user_id, f"💰 کیف پول شما توسط ادمین به مبلغ {message.text} تومان شارژ شد.")
    else:
        bot.send_message(message.chat.id, "فقط عدد وارد کنید:")
        bot.register_next_step_handler(message, lambda m: do_admin_charge(m, user_id))

@bot.message_handler(func=lambda m: m.text == "پیام همگانی 📢" and is_admin(m.from_user.id))
def admin_broadcast_start(message):
    bot.send_message(message.chat.id, "متن پیام همگانی را وارد کنید:")
    bot.register_next_step_handler(message, admin_broadcast_do)

def admin_broadcast_do(message):
    users = load_data(USERS_FILE, {})
    for user_id in users:
        try:
            bot.send_message(int(user_id), f"📢 پیام مدیریت:\n{message.text}")
        except Exception:
            pass
    bot.send_message(message.chat.id, "✅ پیام برای همه کاربران ارسال شد.")

@bot.message_handler(func=lambda m: m.text == "بازگشت 🔙" and is_admin(m.from_user.id))
def admin_back(message):
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    send_main_menu(message.chat.id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
