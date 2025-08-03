from flask import Flask, request
import telebot
import time
import threading
import json
import os

# ==== اطلاعات شخصی ====
API_TOKEN = '8255151341:AAGFwWdSGnkoEVrTOej0jaNUco-DmgKlbCs'
CHANNEL_ID = -1002891641618
CHANNEL_LINK = 'https://t.me/+Bnko8vYkvcRkYjdk'
ADMIN_ID = 368422936
ZARINPAL_URL = 'https://zarinp.al/634382'

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# مسیر فایل اپل‌آیدی‌ها
APPLEID_FILE = 'apple_ids.json'

# بارگذاری اپل‌آیدی‌ها از فایل
def load_apple_ids():
    if not os.path.exists(APPLEID_FILE):
        with open(APPLEID_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    with open(APPLEID_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# ذخیره اپل‌آیدی‌ها در فایل
def save_apple_ids(data):
    with open(APPLEID_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ==== کاربران و شماره موبایل‌ها را داخل دیکشنری ساده ذخیره می‌کنیم (در حافظه) ====
users = {}

@app.route('/', methods=['GET'])
def index():
    return 'Bot is running'

@app.route('/webhook', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data(as_text=True))
    bot.process_new_updates([update])
    return 'ok'

# ارسال منوی اصلی فارسی
def send_main_menu(chat_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('💳 پرداخت'), telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی'))
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

    bot.send_message(ADMIN_ID, f"""📥 کاربر جدید ثبت شد
آیدی: {user_id}
شماره: {phone}""")

    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('💳 پرداخت'), telebot.types.KeyboardButton('🎫 تیکت به پشتیبانی'))
    bot.send_message(message.chat.id, f"✅ شماره شما ثبت شد.\n\nتا دو دقیقه دیگر این پیام حذف می‌شود.\n\nبرای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}", reply_markup=markup)

    # حذف پیام پس از 120 ثانیه
    def delete_message_later(chat_id, message_id):
        time.sleep(120)
        try:
            bot.delete_message(chat_id, message_id)
        except:
            pass

    threading.Thread(target=delete_message_later, args=(message.chat.id, message.message_id)).start()

@bot.message_handler(func=lambda m: m.text == '💳 پرداخت')
def payment_link(message):
    bot.send_message(message.chat.id, f"💳 برای پرداخت، روی لینک زیر کلیک کنید:\n{ZARINPAL_URL}")

@bot.message_handler(commands=['add_appleid'])
def add_appleid(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ دسترسی ندارید.")
        return
    try:
        # فرمت: /add_appleid email password q1 q2 q3
        parts = message.text.split(' ', 6)
        if len(parts) < 6:
            bot.send_message(message.chat.id, "❗️ فرمت اشتباه است.\nفرمت صحیح:\n/add_appleid ایمیل رمز سوال۱ سوال۲ سوال۳")
            return
        email = parts[1]
        password = parts[2]
        q1 = parts[3]
        q2 = parts[4]
        q3 = parts[5]

        apple_ids = load_apple_ids()
        apple_ids.append({
            "email": email,
            "password": password,
            "q1": q1,
            "q2": q2,
            "q3": q3,
            "sold": False
        })
        save_apple_ids(apple_ids)
        bot.send_message(message.chat.id, "✅ اپل‌آیدی با موفقیت اضافه شد.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❗️ خطا در اضافه کردن اپل‌آیدی: {e}")

@bot.message_handler(commands=['stock'])
def stock(message):
    if message.from_user.id != ADMIN_ID:
        bot.send_message(message.chat.id, "❌ دسترسی ندارید.")
        return
    apple_ids = load_apple_ids()
    available = len([a for a in apple_ids if not a.get("sold", False)])
    bot.send_message(message.chat.id, f"📦 موجودی اپل‌آیدی‌ها: {available}")

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def ask_support(message):
    bot.send_message(message.chat.id, "📝 لطفاً پیام خود را بنویسید و ارسال کنید.")
    bot.register_next_step_handler(message, forward_to_admin)

def forward_to_admin(message):
    bot.send_message(ADMIN_ID, f"📩 پیام از {message.from_user.id}:\n{message.text}")
    bot.send_message(message.chat.id, "✅ پیام شما ارسال شد. منتظر پاسخ باشید.")

@bot.message_handler(commands=['admin'])
def admin_panel(message):
    if message.from_user.id != ADMIN_ID:
        return
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("📋 لیست کاربران", callback_data='list_users'))
    markup.add(telebot.types.InlineKeyboardButton("🟢 فعال‌سازی دستی", callback_data='confirm_user'))
    markup.add(telebot.types.InlineKeyboardButton("❌ حذف اشتراک", callback_data='remove_user'))
    markup.add(telebot.types.InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data='broadcast'))
    markup.add(telebot.types.InlineKeyboardButton("📦 موجودی اپل‌آیدی", callback_data='stock'))
    bot.send_message(message.chat.id, "🛠 پنل مدیریت:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "list_users":
        text = "📋 لیست کاربران:\n"
        for user_id, info in users.items():
            phone = info.get("phone", "-")
            active = "✅" if info.get("active", False) else "❌"
            text += f"{user_id} | {phone} | {active}\n"
        bot.send_message(ADMIN_ID, text or "❗️کاربری یافت نشد.")

    elif call.data == "confirm_user":
        bot.send_message(ADMIN_ID, "لطفاً آیدی عددی کاربر را بفرستید تا فعال شود.")
        bot.register_next_step_handler(call.message, confirm_user_step)

    elif call.data == "remove_user":
        bot.send_message(ADMIN_ID, "آیدی عددی کاربر برای حذف را بفرستید:")
        bot.register_next_step_handler(call.message, remove_user_step)

    elif call.data == "broadcast":
        bot.send_message(ADMIN_ID, "پیامی که باید به همه ارسال شود را بفرستید:")
        bot.register_next_step_handler(call.message, broadcast_step)

    elif call.data == "stock":
        apple_ids = load_apple_ids()
        available = len([a for a in apple_ids if not a.get("sold", False)])
        bot.send_message(ADMIN_ID, f"📦 موجودی اپل‌آیدی‌ها: {available}")

def confirm_user_step(message):
    try:
        user_id = int(message.text)
        if user_id in users:
            users[user_id]["active"] = True
            users[user_id]["timestamp"] = int(time.time())
            bot.send_message(user_id, f"✅ اشتراک شما فعال شد.\n\n📥 [عضویت در کانال VIP]({CHANNEL_LINK})", parse_mode='Markdown')
            bot.send_message(ADMIN_ID, "✅ کاربر فعال شد.")
        else:
            bot.send_message(ADMIN_ID, "❗️ کاربر پیدا نشد.")
    except:
        bot.send_message(ADMIN_ID, "❗️ مقدار اشتباه است.")

def remove_user_step(message):
    try:
        user_id = int(message.text)
        if user_id in users:
            users[user_id]["active"] = False
            bot.send_message(user_id, "❌ اشتراک شما لغو شد.")
            bot.send_message(ADMIN_ID, "✅ اشتراک لغو شد.")
        else:
            bot.send_message(ADMIN_ID, "❗️ کاربر پیدا نشد.")
    except:
        bot.send_message(ADMIN_ID, "❗️ مقدار اشتباه است.")

def broadcast_step(message):
    text = message.text
    count = 0
    for user_id, info in users.items():
        try:
            bot.send_message(user_id, text)
            count += 1
        except:
            pass
    bot.send_message(ADMIN_ID, f"پیام به {count} نفر ارسال شد.")

# شبیه‌سازی تایید پرداخت موفق (این قسمت را طبق سیستم پرداخت خودت کامل کن)
@bot.message_handler(commands=['paid'])
def handle_paid(message):
    user_id = message.from_user.id
    apple_ids = load_apple_ids()
    # پیدا کردن اولین اپل‌آیدی موجود
    appleid = None
    for a in apple_ids:
        if not a.get("sold", False):
            appleid = a
            break
    if appleid is None:
        bot.send_message(user_id, "❗️ متأسفانه اپل‌آیدی موجود نیست.")
        return

    # علامت گذاری اپل‌آیدی به عنوان فروخته شده
    appleid["sold"] = True
    save_apple_ids(apple_ids)

    # ارسال اپل‌آیدی به کاربر
    text = f"""🎉 پرداخت شما تایید شد!

ایمیل: {appleid['email']}
رمز عبور: {appleid['password']}
سوال امنیتی ۱: {appleid['q1']}
سوال امنیتی ۲: {appleid['q2']}
سوال امنیتی ۳: {appleid['q3']}

✅ از خرید شما سپاسگزاریم!"""
    bot.send_message(user_id, text)

    # فعال‌سازی اشتراک (مثلا عضویت در کانال VIP)
    users[user_id] = users.get(user_id, {})
    users[user_id]["active"] = True
    bot.send_message(user_id, f"📥 [عضویت در کانال VIP]({CHANNEL_LINK})", parse_mode='Markdown')

if __name__ == '__main__':
    # در صورت تمایل می‌توانید قبل از ست وب‌هوک حذفش کنید
    bot.remove_webhook()
    bot.set_webhook(url='https://appleid035.onrender.com/webhook')
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
