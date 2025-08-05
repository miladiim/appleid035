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
    {"id": 1, "name": "جیمیل 2018 قدیمی", "price": 77000, "stock": 9},
    {"id": 2, "name": "جیمیل 2025 جدید (کیفیت بالا)", "price": 77000, "stock": 12},
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
    return load_data(ACCOUNTS_FILE, {"1": [], "2": [], "3": []})

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
        # کم کردن موجودی محصول
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
        "لطفاً تعداد اکانت‌ها را انتخاب کنید:"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    for i in range(1, min(product["stock"], 5)+1):
        markup.add(telebot.types.InlineKeyboardButton(f"{i}", callback_data=f"buyqty_{product_id}_{i}"))
    bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("buyqty_"))
def choose_qty(call):
    _, product_id, qty = call.data.split("_")
    product_id = int(product_id)
    qty = int(qty)
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    user = get_user(call.from_user.id)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    price = product["price"] * qty
    if product["stock"] < qty:
        bot.send_message(call.message.chat.id, "❌ تعداد موردنظر موجود نیست.")
        return
    text = (
        f"📌 اطلاعات سرویس:\n"
        f"🛒 سرویس: {product['name']}\n"
        f"💰 قیمت هر اکانت: {product['price']:,} تومان\n"
        f"🔢 تعداد انتخابی: {qty}\n"
        f"💳 موجودی شما: {user['wallet']:,} تومان\n"
        f"💰 قیمت کل: {price:,} تومان\n"
        "------\n"
        "روش پرداخت را انتخاب کنید:"
    )
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("💳 کارت به کارت", callback_data=f"pay_card_{product_id}_{qty}"),
        telebot.types.InlineKeyboardButton("💰 کیف پول", callback_data=f"pay_wallet_{product_id}_{qty}")
    )
    bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_wallet_"))
def pay_wallet(call):
    _, _, product_id, qty = call.data.split("_")
    product_id = int(product_id)
    qty = int(qty)
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    user = get_user(call.from_user.id)
    total = product["price"] * qty
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    if product["stock"] < qty:
        bot.send_message(call.message.chat.id, "❌ موجودی این محصول کافی نیست.")
        return
    if user["wallet"] >= total:
        user["wallet"] -= total
        user["purchases"] += qty
        set_user(call.from_user.id, user)
        sent_count = 0
        for _ in range(qty):
            account = give_account(product_id, call.from_user.id)
            if account:
                bot.send_message(call.message.chat.id, f"✅ خرید موفق!\n\n📧 ایمیل: `{account['email']}`\n🔑 پسورد: `{account['pass']}`", parse_mode="Markdown")
                sent_count += 1
            else:
                bot.send_message(call.message.chat.id, "❌ موجودی اکانت این محصول به پایان رسیده.")
                break
        bot.send_message(ADMIN_ID, f"🔔 خرید با کیف پول توسط {user['name']}\nمحصول: {product['name']}\nتعداد: {sent_count}\nموجودی باقی‌مانده: {product['stock']:,} عدد")
    else:
        bot.send_message(call.message.chat.id, "❌ موجودی کیف پول شما کافی نیست.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_card_"))
def pay_card(call):
    _, _, product_id, qty = call.data.split("_")
    product_id = int(product_id)
    qty = int(qty)
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        bot.answer_callback_query(call.id, "محصول یافت نشد")
        return
    text = (
        f"💳 برای خرید {qty} عدد {product['name']} به مبلغ {product['price']*qty:,} تومان:\n"
        f"۱. مبلغ را به شماره کارت زیر واریز کنید:\n\n{CARD_NUMBER}\n\n"
        f"۲. سپس رسید پرداخت را ارسال کنید."
    )
    bot.send_message(call.message.chat.id, text)
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: receive_receipt(m, product, qty))

def receive_receipt(message, product, qty):
    if message.photo:
        payment = {
            "user_id": message.from_user.id,
            "name": message.from_user.first_name,
            "product": product["name"],
            "amount": product["price"] * qty,
            "qty": qty,
            "type": "buy",
            "status": "pending",
            "msg_id": None
        }
        add_payment(payment)
        caption = (
            f"🆕 رسید خرید\n"
            f"کاربر: {message.from_user.first_name}\n"
            f"محصول: {product['name']}\n"
            f"تعداد: {qty}\n"
            f"مبلغ: {product['price']*qty:,} تومان\n"
            f"برای پاسخ‌دهی، دکمه زیر را بزنید."
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("تحویل اکانت و تایید خرید", callback_data=f"reply_buy_{message.from_user.id}_{product['id']}_{qty}"))
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
    _, _, user_id, product_id, qty = call.data.split("_")
    user_id = int(user_id)
    product_id = int(product_id)
    qty = int(qty)
    sent_count = 0
    for _ in range(qty):
        account = give_account(product_id, user_id)
        if account:
            bot.send_message(user_id, f"✅ خرید موفق!\n\n📧 ایمیل: `{account['email']}`\n🔑 پسورد: `{account['pass']}`", parse_mode="Markdown")
            sent_count += 1
        else:
            bot.send_message(user_id, "❌ موجودی اکانت این محصول به پایان رسیده.")
            break
    bot.send_message(call.message.chat.id, f"اکانت‌ها ارسال شد (تعداد: {sent_count})")

# ------------------------ حساب کاربری --------------------------
@bot.message_handler(func=lambda m: m.text == "👤 حساب کاربری")
def show_profile(message):
    user = get_user(message.from_user.id)
    acc_text = ""
    if user and "accounts" in user and user["accounts"]:
        acc_text = "\n🟢 اکانت‌های دریافتی شما:\n"
        for i, acc in enumerate(user["accounts"], 1):
            prod = next((p for p in PRODUCTS if p["id"] == acc["product_id"]), None)
            acc_text += f"{i}. {prod['name']} | ایمیل: `{acc['email']}` | پسورد: `{acc['pass']}` | {acc['datetime']}\n"
    else:
        acc_text = "\nشما فعلاً اکانتی دریافت نکرده‌اید."
    bot.send_message(message.chat.id,
        f"👤 نام: {user['name']}\n📱 شماره: {user['mobile']}\n📆 تاریخ عضویت: {user['joined']}\n"
        f"🛒 تعداد خرید: {user['purchases']}\n💰 موجودی کیف پول: {user['wallet']:,} تومان"
        f"{acc_text}", parse_mode="Markdown")

# ------------------------ تیکت پشتیبانی و گزارش خرابی --------------------------
@bot.message_handler(func=lambda m: m.text == "📨 تیکت پشتیبانی")
def support_menu(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("باز کردن تیکت 🟢"))
    markup.add(telebot.types.KeyboardButton("لیست تیکت‌های باز 🗂"))
    markup.add(telebot.types.KeyboardButton("لیست چت‌ها 🗨️"))
    markup.add(telebot.types.KeyboardButton("ارسال گزارش 📝"))
    markup.add(telebot.types.KeyboardButton("بازگشت به منوی اصلی 🔙"))
    bot.send_message(message.chat.id, "برای ارتباط با پشتیبانی یا مشاهده تیکت‌ها، گزینه مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "باز کردن تیکت 🟢")
def open_ticket(message):
    supports = get_supports()
    user_id = message.from_user.id
    open_tickets = [t for t in supports if t["user_id"] == user_id and t["status"] == "open"]
    if open_tickets:
        bot.send_message(user_id, "شما یک تیکت باز دارید. ابتدا آن را ببندید یا ادامه دهید.")
        return
    bot.send_message(user_id, "موضوع تیکت را وارد کنید:")
    bot.register_next_step_handler(message, create_ticket)

def create_ticket(message):
    supports = get_supports()
    user = get_user(message.from_user.id)
    ticket_id = len(supports) + 1
    ticket = {
        "ticket_id": ticket_id,
        "user_id": message.from_user.id,
        "user_name": user["name"],
        "status": "open",
        "messages": [
            {"sender": "user", "text": message.text, "datetime": str(datetime.datetime.now())[:19]}
        ]
    }
    add_support(ticket)
    bot.send_message(ADMIN_ID, f"🎫 تیکت #{ticket_id} جدید از {user['name']}:\n{message.text}")
    bot.send_message(message.chat.id, f"تیکت شما با موفقیت ثبت شد. کد تیکت: #{ticket_id}")

@bot.message_handler(func=lambda m: m.text == "لیست تیکت‌های باز 🗂")
def list_open_tickets(message):
    supports = get_supports()
    user_id = message.from_user.id
    open_tickets = [t for t in supports if t["user_id"] == user_id and t["status"] == "open"]
    if not open_tickets:
        bot.send_message(user_id, "⛔️ تیکت بازی ندارید.")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    for t in open_tickets:
        markup.add(telebot.types.InlineKeyboardButton(
            f"تیکت #{t['ticket_id']} | {t['messages'][0]['text'][:20]}", callback_data=f"view_ticket_{t['ticket_id']}"
        ))
    bot.send_message(user_id, "🗂 تیکت‌های باز شما:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "لیست چت‌ها 🗨️")
def show_prev_chats(message):
    supports = get_supports()
    user_id = message.from_user.id
    tickets = [t for t in supports if t["user_id"] == user_id]
    if not tickets:
        bot.send_message(user_id, "هنوز چتی با پشتیبانی نداشتی!")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    for t in tickets:
        status = "باز" if t["status"] == "open" else "بسته"
        markup.add(telebot.types.InlineKeyboardButton(
            f"تیکت #{t['ticket_id']} ({status})", callback_data=f"view_ticket_{t['ticket_id']}"
        ))
    bot.send_message(user_id, "لیست چت‌ها:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("view_ticket_"))
def view_ticket(call):
    ticket_id = int(call.data.split("_")[2])
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if not ticket:
        bot.send_message(call.message.chat.id, "تیکت پیدا نشد.")
        return
    chat_history = ""
    for msg in ticket["messages"]:
        sender = "شما" if msg["sender"] == "user" else "پشتیبانی"
        chat_history += f"{sender}: {msg['text']}\n"
    markup = telebot.types.InlineKeyboardMarkup()
    if ticket["status"] == "open":
        markup.add(telebot.types.InlineKeyboardButton("ارسال پیام جدید", callback_data=f"reply_ticket_{ticket_id}"))
    bot.send_message(call.message.chat.id, chat_history, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("reply_ticket_"))
def reply_ticket(call):
    ticket_id = int(call.data.split("_")[2])
    bot.send_message(call.message.chat.id, "پیام خود را وارد کنید:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_ticket_reply(m, ticket_id))

def save_ticket_reply(message, ticket_id):
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if not ticket or ticket["status"] != "open":
        bot.send_message(message.chat.id, "تیکت معتبر نیست یا بسته شده.")
        return
    ticket["messages"].append({"sender": "user", "text": message.text, "datetime": str(datetime.datetime.now())[:19]})
    save_data(SUPPORT_FILE, supports)
    bot.send_message(ADMIN_ID, f"🔔 پیام جدید در تیکت #{ticket_id} از کاربر: {message.text}")
    bot.send_message(message.chat.id, "پیام شما ارسال شد.")

@bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text.startswith("تیکت #"))
def admin_view_ticket(message):
    ticket_id = int(message.text.split("#")[1].split()[0])
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if not ticket:
        bot.send_message(message.chat.id, "تیکت پیدا نشد.")
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
    bot.send_message(message.chat.id, chat_history, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_reply_"))
def admin_reply_ticket_call(call):
    ticket_id = int(call.data.split("_")[2])
    bot.send_message(call.message.chat.id, "پاسخ خود را وارد کنید:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_admin_reply(m, ticket_id))

def save_admin_reply(message, ticket_id):
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if not ticket or ticket["status"] != "open":
        bot.send_message(message.chat.id, "تیکت معتبر نیست یا بسته شده.")
        return
    ticket["messages"].append({"sender": "admin", "text": message.text, "datetime": str(datetime.datetime.now())[:19]})
    save_data(SUPPORT_FILE, supports)
    bot.send_message(ticket["user_id"], f"📩 پاسخ پشتیبانی: {message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما به کاربر ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("close_ticket_"))
def close_ticket(call):
    ticket_id = int(call.data.split("_")[2])
    supports = get_supports()
    ticket = next((t for t in supports if t["ticket_id"] == ticket_id), None)
    if ticket:
        ticket["status"] = "closed"
        save_data(SUPPORT_FILE, supports)
        bot.send_message(call.message.chat.id, "✅ تیکت بسته شد.")
        bot.send_message(ticket["user_id"], f"⛔️ تیکت #{ticket_id} شما توسط مدیریت بسته شد.")

@bot.message_handler(func=lambda m: m.text == "ارسال گزارش 📝")
def send_report(message):
    user = get_user(message.from_user.id)
    now = datetime.datetime.now()
    recent_accs = []
    if "accounts" in user:
        for acc in user["accounts"]:
            buy_time = datetime.datetime.strptime(acc["datetime"], "%Y-%m-%d %H:%M:%S")
            if (now - buy_time).total_seconds() <= 48*3600:
                recent_accs.append(acc)
    if not recent_accs:
        bot.send_message(message.chat.id, "شما هیچ اکانتی در ۴۸ ساعت اخیر خریداری نکردید.")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    for i, acc in enumerate(recent_accs, 1):
        markup.add(telebot.types.InlineKeyboardButton(
            f"{i}. {acc['email']}", callback_data=f"report_{acc['email']}"
        ))
    bot.send_message(message.chat.id, "کدام اکانت را برای خرابی انتخاب می‌کنید؟", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("report_"))
def handle_report(call):
    email = call.data.split("_")[1]
    bot.send_message(call.message.chat.id, "لطفاً توضیح خرابی را بنویسید:")
    bot.register_next_step_handler_by_chat_id(call.message.chat.id, lambda m: save_report(m, email))

def save_report(message, email):
    user = get_user(message.chat.id)
    bot.send_message(ADMIN_ID, f"🚨 گزارش مشکل اکانت\nکاربر: {user['name']} ({user['mobile']})\nایمیل: {email}\nتوضیح: {message.text}")
    bot.send_message(message.chat.id, "گزارش شما ارسال شد.")

@bot.message_handler(func=lambda m: m.text == "بازگشت به منوی اصلی 🔙")
def back_to_main(message):
    send_main_menu(message.chat.id)

# ------------------------ پنل مدیریت ویژه ادمین ------------------------
@bot.message_handler(func=lambda m: m.text == "پنل مدیریت 👑" and is_admin(m.from_user.id))
def admin_panel(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton("لیست اعضا 👥"))
    markup.add(telebot.types.KeyboardButton("شارژ مستقیم کاربر ➕"))
    markup.add(telebot.types.KeyboardButton("پیام همگانی 📢"))
    markup.add(telebot.types.KeyboardButton("مدیریت موجودی محصولات 🗃"))
    markup.add(telebot.types.KeyboardButton("بازگشت 🔙"))
    bot.send_message(message.chat.id, "🎛 پنل مدیریت:", reply_markup=markup)

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
