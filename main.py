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
        "📌 اطلاعات سرویس:\n"
        "------\n"
        f"🛒 سرویس: 🔸{product['name']}\n"
        f"💰 قیمت هر اکانت: {product['price']:,} تومان\n"
        f"📦 موجودی: {product.get('stock', 'نامشخص')} عدد\n"
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    text = (
        f"💳 برای خرید {product['name']} به مبلغ {product['price']:,} تومان:\n"
        f"۱. مبلغ را به شماره کارت زیر واریز کنید:\n\n{CARD_NUMBER}\n\n"
        f"۲. سپس رسید پرداخت را ارسال کنید."
    )
    bot.send_message(call.message.chat.id, text)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_receipt(m, product))

def receive_receipt(message, product):
    if message.photo:
        payment = {
            "user_id": message.from_user.id,
            "name": message.from_user.first_name,
            "product": product["name"],
            "amount": product["price"],
            "type": "buy",
            "status": "pending",
            "msg_id": None
        }
        add_payment(payment)
        caption = (
            f"🆕 رسید خرید\n"
            f"کاربر: {message.from_user.first_name}\n"
            f"محصول: {product['name']}\n"
            f"مبلغ: {product['price']:,} تومان\n"
            f"برای پاسخ‌دهی، دکمه زیر را بزنید."
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("پاسخ", callback_data=f"reply_buy_{message.from_user.id}"))
        photo_id = message.photo[-1].file_id
        msg = bot.send_photo(ADMIN_ID, photo_id, caption=caption, reply_markup=markup)
        payment["msg_id"] = msg.message_id
        payments = get_payments()
        payments[-1]["msg_id"] = msg.message_id
        save_data(PAYMENTS_FILE, payments)
        bot.send_message(message.chat.id, "✅ رسید شما ارسال شد، منتظر تایید مدیر باشید.")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_buy_"))
def reply_to_buy(call):
    user_id = int(call.data.split("_")[2])
    bot.send_message(call.message.chat.id, "پیام خود را جهت ارسال به کاربر وارد کنید:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: admin_reply_buy(m, user_id))

def admin_reply_buy(message, user_id):
    bot.send_message(user_id, f"📩 پاسخ مدیر: {message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما به کاربر ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_wallet_"))
def pay_wallet(call):
    product_id = int(call.data.split("_")[2])
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    user = get_user(call.from_user.id)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if user["wallet"] >= product["price"]:
        user["wallet"] -= product["price"]
        user["purchases"] += 1
        set_user(call.from_user.id, user)
        bot.send_message(call.message.chat.id, f"✅ خرید با کیف پول با موفقیت انجام شد.\n\nمحصول: {product['name']}")
        bot.send_message(ADMIN_ID, f"🔔 خرید از کیف پول توسط {user['name']}\nمحصول: {product['name']}\nموجودی باقی‌مانده: {user['wallet']:,} تومان")
    else:
        bot.send_message(call.message.chat.id, "❌ موجودی کیف پول شما کافی نیست.")

# ------------------------ حساب کاربری --------------------------
@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def show_profile(message):
    user = get_user(message.from_user.id)
    if user:
        bot.send_message(message.chat.id, f"👤 نام: {user['name']}\n📱 شماره: {user['mobile']}\n📆 تاریخ عضویت: {user['joined']}\n🛒 تعداد خرید: {user['purchases']}\n💰 موجودی کیف پول: {user['wallet']:,} تومان")
    else:
        bot.send_message(message.chat.id, "اطلاعات حساب شما یافت نشد.")

# ------------------------ تیکت پشتیبانی --------------------------
@bot.message_handler(func=lambda m: m.text == "📨 تیکت پشتیبانی")
def support_ticket(message):
    bot.send_message(message.chat.id, "پیام خود را برای پشتیبانی ارسال کنید:")
    bot.register_next_step_handler(message, handle_support)

def handle_support(message):
    user = get_user(message.from_user.id)
    ticket = {
        "user_id": message.from_user.id,
        "name": user["name"],
        "text": message.text,
        "status": "pending",
        "msg_id": None
    }
    add_support(ticket)
    caption = (
        f"🎫 تیکت پشتیبانی\n"
        f"کاربر: {user['name']}\n"
        f"پیام: {message.text}\n"
        f"برای پاسخ‌دهی، دکمه زیر را بزنید."
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("پاسخ", callback_data=f"reply_ticket_{message.from_user.id}"))
    msg = bot.send_message(ADMIN_ID, caption, reply_markup=markup)
    ticket["msg_id"] = msg.message_id
    supports = get_supports()
    supports[-1]["msg_id"] = msg.message_id
    save_data(SUPPORT_FILE, supports)
    bot.send_message(message.chat.id, "✅ پیام شما به پشتیبانی ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_ticket_"))
def reply_to_ticket(call):
    user_id = int(call.data.split("_")[2])
    bot.send_message(call.message.chat.id, "پاسخ خود را برای کاربر وارد کنید:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: admin_reply_ticket(m, user_id))

def admin_reply_ticket(message, user_id):
    bot.send_message(user_id, f"📩 پاسخ پشتیبانی: {message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما به کاربر ارسال شد.")

# ------------------------ شارژ حساب --------------------------
@bot.message_handler(func=lambda m: m.text == "💳 شارژ حساب")
def charge_account(message):
    bot.send_message(message.chat.id, f"برای شارژ حساب، مبلغ مورد نظر را به شماره کارت زیر واریز کرده و رسید را ارسال کنید:\n\n{CARD_NUMBER}")
    bot.register_next_step_handler(message, receive_charge_receipt)

def receive_charge_receipt(message):
    if message.photo:
        user = get_user(message.from_user.id)
        payment = {
            "user_id": message.from_user.id,
            "name": user["name"],
            "type": "charge",
            "status": "pending",
            "msg_id": None
        }
        add_payment(payment)
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("پاسخ", callback_data=f"reply_charge_{message.from_user.id}"))
        photo_id = message.photo[-1].file_id
        msg = bot.send_photo(ADMIN_ID, photo_id, caption=f"💸 درخواست شارژ حساب از {user['name']}\nبرای پاسخ‌دهی دکمه زیر را بزنید.", reply_markup=markup)
        payment["msg_id"] = msg.message_id
        payments = get_payments()
        payments[-1]["msg_id"] = msg.message_id
        save_data(PAYMENTS_FILE, payments)
        bot.send_message(message.chat.id, "✅ رسید شارژ ارسال شد و منتظر تایید مدیر باشید.")
    else:
        bot.send_message(message.chat.id, "❌ لطفاً تصویر رسید را ارسال کنید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_charge_"))
def reply_to_charge(call):
    user_id = int(call.data.split("_")[2])
    bot.send_message(call.message.chat.id, "مبلغ شارژ را برای کاربر وارد کنید (فقط عدد):")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: admin_charge_user(m, user_id))

def admin_charge_user(message, user_id):
    if message.text.isdigit():
        user = get_user(user_id)
        user["wallet"] += int(message.text)
        set_user(user_id, user)
        bot.send_message(user_id, f"💰 حساب شما به مبلغ {int(message.text):,} تومان شارژ شد.")
        bot.send_message(message.chat.id, "✅ شارژ کاربر انجام شد.")
    else:
        bot.send_message(message.chat.id, "لطفاً فقط مبلغ را به عدد وارد کنید:")
        bot.register_next_step_handler(message, lambda m: admin_charge_user(m, user_id))

# ======================= پنل مدیریت ویژه ادمین =========================
@bot.message_handler(func=lambda m: m.text == "پنل مدیریت 👑" and is_admin(m.from_user.id))
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("لیست اعضا 👥"))
    markup.add(telebot.types.KeyboardButton("شارژ مستقیم کاربر ➕"))
    markup.add(telebot.types.KeyboardButton("پیام همگانی 📢"))
    markup.add(telebot.types.KeyboardButton("بازگشت 🔙"))
    bot.send_message(message.chat.id, "🎛 پنل مدیریت:", reply_markup=markup)

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
    bot.register_next_step_handler(message, lambda m: admin_charge_user_do(m, target_user["id"]))

def admin_charge_user_do(message, target_id):
    if message.text.isdigit():
        amount = int(message.text)
        user = get_user(target_id)
        user["wallet"] += amount
        set_user(target_id, user)
        bot.send_message(message.chat.id, f"کیف پول کاربر به مبلغ {amount:,} تومان شارژ شد.")
        bot.send_message(target_id, f"💰 کیف پول شما توسط ادمین به مبلغ {amount:,} تومان شارژ شد.")
    else:
        bot.send_message(message.chat.id, "فقط عدد وارد کنید:")
        bot.register_next_step_handler(message, lambda m: admin_charge_user_do(m, target_id))

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
