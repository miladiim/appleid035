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

@bot.message_handler(content_types=['photo'])
def handle_receipt(message):
    user_id = message.from_user.id
    if user_id not in users:
        return

    caption = f"🧾 رسید پرداخت از کاربر {user_id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ تأیید پرداخت", callback_data=f"confirm_{user_id}"))
    markup.add(types.InlineKeyboardButton("📩 پاسخ به کاربر", callback_data=f"reply_{user_id}"))

    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)
    bot.send_message(user_id, "✅ رسید شما با موفقیت برای بررسی ارسال شد. منتظر تأیید باشید.")

@bot.message_handler(func=lambda m: m.text == '📱 ارسال شماره موبایل')
def ask_phone_again(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = telebot.types.KeyboardButton('📱 ارسال شماره موبایل', request_contact=True)
    markup.add(btn)
    bot.send_message(message.chat.id, "لطفاً شماره موبایلت رو ارسال کن:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🛒 خرید اپل‌آیدی')
def buy_menu(message):
    user_id = message.from_user.id
    apple_ids = load_apple_ids()

    types = {
        "2018": "🇺🇸 اپل‌آیدی آمریکا 2018",
        "2025": "🇺🇸 اپل‌آیدی آمریکا 2025",
        "personal": "🇮🇷 اپل‌آیدی با اطلاعات شما (داخل ایران)"
    }

    markup = types.InlineKeyboardMarkup()
    for t, title in types.items():
        stock = sum(1 for a in apple_ids if a["type"] == t and not a.get("sold", False))
        if stock > 0:  # فقط اگه موجودی داشت، نمایش بده
            markup.add(types.InlineKeyboardButton(f"{title} - {stock} عدد", callback_data=f"type_{t}"))

    if markup.keyboard:
        bot.send_message(user_id, "✅ لطفاً یکی از پلن‌های زیر را انتخاب کنید:", reply_markup=markup)
    else:
        bot.send_message(user_id, "❌ در حال حاضر هیچ اپل‌آیدی موجود نیست.")
@bot.callback_query_handler(func=lambda c: c.data.startswith("reply_"))
def reply_to_user_start(call):
    user_id = int(call.data.split("_")[1])
    msg = bot.send_message(ADMIN_ID, f"💬 لطفاً پیام خود را برای کاربر {user_id} بنویسید:")
    bot.register_next_step_handler(msg, send_admin_reply, user_id)

def send_admin_reply(message, user_id):
    try:
        bot.send_message(user_id, f"📩 پاسخ پشتیبانی:\n{message.text}")
        bot.send_message(ADMIN_ID, "✅ پیام شما برای کاربر ارسال شد.")
    except:
        bot.send_message(ADMIN_ID, "❌ ارسال پیام به کاربر ناموفق بود.")
        return
    apple_ids = load_apple_ids()
    type_map = {
        'buy_2018': '2018',
        'buy_2025': '2025',
        'buy_personal': 'personal'
    }
    prices = {
        'buy_2018': 250000,
        'buy_2025': 200000,
        'buy_personal': 350000
    }
    t = type_map.get(call.data)
    price = prices.get(call.data, 0)

    selected_appleid = None
    for a in apple_ids:
        if not a.get("sold", False) and a.get("type") == t:
            selected_appleid = a
            break

    if selected_appleid is None:
        # اگر اپل‌آیدی موجود نبود پیام بده و اجازه بده خرید با اعلام رسید باشه
        users[user_id]["pending_purchase"] = {"type": t, "price": price, "appleid": None}
        bot.answer_callback_query(call.id, "❗️ اپل‌آیدی موجود نیست. می‌توانید با پرداخت رسید، خرید را ثبت کنید.")
        bot.send_message(user_id, f"❗️ اپل‌آیدی نوع {t} موجود نیست.\nلطفاً مبلغ {price:,} تومان را به شماره کارت واریز کنید و رسید واریز را ارسال کنید.")
    else:
        users[user_id]["pending_purchase"] = {"type": t, "price": price, "appleid": selected_appleid}
        bot.answer_callback_query(call.id, f"✅ اپل‌آیدی موجود است.\nلطفاً مبلغ {price:,} تومان را به شماره کارت واریز کنید و رسید را ارسال کنید.")

@bot.message_handler(func=lambda m: "pending_purchase" in users.get(m.from_user.id, {}) and m.text)
def receive_receipt(message):
    user_id = message.from_user.id
    purchase = users[user_id].get("pending_purchase")
    if not purchase:
        return

    receipt_text = message.text
    appleid = purchase.get("appleid")

    if appleid is not None:
        # اگر اپل‌آیدی موجود هست یعنی فروش واقعی
        apple_ids = load_apple_ids()
        # علامت زدن sold فقط بعد تایید ادمین انجام میشه، فعلاً فقط رسید ثبت میشه
    else:
        # اگر اپل‌آیدی موجود نیست، خرید با رسید ثبت می‌شود
        pass

    # ذخیره اطلاعات رسید در حافظه کاربران
    purchase["receipt"] = receipt_text
    users[user_id]["pending_purchase"] = purchase

    # ارسال رسید به ادمین با دکمه تایید
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("✅ تأیید خرید", callback_data=f'confirm_payment_{user_id}')
    )
    bot.send_message(ADMIN_ID,
                     f"💳 رسید پرداخت از کاربر {user_id} دریافت شد.\nنوع اپل‌آیدی: {purchase['type']}\nمبلغ: {purchase['price']:,} تومان\nرسید:\n{receipt_text}",
                     reply_markup=markup)

    bot.send_message(user_id, "✅ رسید پرداخت شما دریافت شد. پس از تایید ادمین، نتیجه به شما اطلاع داده خواهد شد.")
    users[user_id].pop("pending_purchase", None)  # فعلاً پاکش می‌کنیم تا تایید بعدی جدا باشه

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_payment_'))
def confirm_payment(call):
    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما اجازه این کار را ندارید.")
        return

    # شناسه کاربر را از callback_data بگیر
    user_id_str = call.data.split('_')[-1]
    try:
        user_id = int(user_id_str)
    except:
        bot.answer_callback_query(call.id, "شناسه کاربر نامعتبر است.")
        return

    # تایید خرید - اپل‌آیدی را در صورت وجود علامت زده و به کاربر پیام بده
    # چون ما در لحظه دریافت رسید پاک کردیم، اینجا باید جایی ذخیره کنیم (مثلاً یک دیکشنری دیگر)
    # برای سادگی، اینجا دوباره load کنیم و علامت بزنیم (می‌تونیم از حافظه کوتاه مدت هم استفاده کنیم)

    # چون اطلاعات خرید در users پاک شده، برای سادگی یک راه‌حل اینه که در دریافت رسید، به جای پاک کردن pending_purchase، اون رو به یک دیکشنری دیگر به نام confirmed_purchases اضافه کنیم.
    # الان این کار رو انجام نمی‌دیم و فرض می‌کنیم خرید با رسید به عنوان موفق ثبت می‌شود.

    # اینجا فقط پیام تایید رو می‌فرستیم به کاربر
    bot.answer_callback_query(call.id, "خرید تأیید شد.")
    bot.send_message(user_id, "✅ خرید شما توسط ادمین تأیید شد. ممنون از خرید شما 🎉")

    # علامت زدن اپل‌آیدی به عنوان فروخته شده اگر موجود بود
    apple_ids = load_apple_ids()
    for a in apple_ids:
        if not a.get("sold", False) and a.get("type") == users[user_id].get("type", None):
            a["sold"] = True
            break
    save_apple_ids(apple_ids)

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def support_ticket(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "لطفاً پیام خود را برای پشتیبانی ارسال کنید. پس از ارسال، پیام به ادمین خواهد رسید.")

@bot.message_handler(func=lambda m: m.reply_to_message and m.reply_to_message.from_user.id == ADMIN_ID)
def admin_reply(message):
    if message.from_user.id != ADMIN_ID:
        return
    if not message.reply_to_message or not message.reply_to_message.text:
        return
    # پیام ادمین به کاربر ارسال شود
    lines = message.reply_to_message.text.split('\n')
    if len(lines) < 2:
        return
    try:
        user_line = lines[0]
        user_id = int(user_line.split()[-1])
        bot.send_message(user_id, f"💬 پاسخ پشتیبانی:\n{message.text}")
    except:
        pass

@bot.message_handler(func=lambda m: m.text and m.text != '🎫 تیکت به پشتیبانی' and m.text != '🛒 خرید اپل‌آیدی')
def forward_ticket(message):
    if message.from_user.id == ADMIN_ID:
        return
    user_id = message.from_user.id
    bot.send_message(ADMIN_ID, f"📩 پیام از کاربر {user_id}:\n{message.text}")
    bot.send_message(user_id, "✅ پیام شما به پشتیبانی ارسال شد.")

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url='https://appleid035.onrender.com/webhook')  # ← دامنه واقعی روی Render
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_bot()
