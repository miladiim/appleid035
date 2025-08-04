from flask import Flask, request
import telebot
import time
import threading
import json
import os
from telebot import types

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
admin_replying_to = {}  # ذخیره وضعیت پاسخ ادمین

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

@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    user_id = message.from_user.id
    phone = message.contact.phone_number
    users[user_id] = {"phone": phone, "active": False, "timestamp": int(time.time())}
    bot.send_message(ADMIN_ID, f"📥 کاربر جدید ثبت شد\nآیدی: {user_id}\nشماره: {phone}")
    send_main_menu(message.chat.id)

@bot.message_handler(func=lambda m: m.text == '🛒 خرید اپل‌آیدی')
def show_appleid_menu(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        telebot.types.InlineKeyboardButton("🍎 اپل‌آیدی ساخت 2018 آمریکا (250,000 تومان)", callback_data='buy_2018'),
        telebot.types.InlineKeyboardButton("🍏 اپل‌آیدی ساخت 2025 آمریکا (200,000 تومان)", callback_data='buy_2025'),
        telebot.types.InlineKeyboardButton("🔐 اپل‌آیدی با اطلاعات شخصی (350,000 تومان)", callback_data='buy_personal')
    )
    bot.send_message(message.chat.id, "لطفاً نوع اپل‌آیدی مورد نظر خود را انتخاب کنید:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '🎫 تیکت به پشتیبانی')
def support_ticket(message):
    user_id = message.from_user.id
    bot.send_message(user_id, "لطفاً پیام خود را برای پشتیبانی ارسال کنید. پس از ارسال، پیام به ادمین خواهد رسید.")

@bot.message_handler(content_types=['photo'])
def handle_payment_receipt(message):
    user_id = message.from_user.id
    if user_id not in users or "selected_appleid" not in users[user_id]:
        bot.send_message(user_id, "لطفاً ابتدا نوع اپل‌آیدی را انتخاب کنید.")
        return

    fwd_msg = bot.forward_message(ADMIN_ID, user_id, message.message_id)
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💬 پاسخ بده", callback_data=f"reply_{user_id}")
    markup.add(btn)

    bot.send_message(ADMIN_ID, f"رسید پرداخت از کاربر: {user_id}", reply_markup=markup)
    bot.send_message(user_id, "✅ رسید پرداخت شما دریافت شد. پس از تایید، اپل‌آیدی برای شما ارسال خواهد شد.")

@bot.message_handler(func=lambda m: m.text and m.from_user.id != ADMIN_ID)
def forward_ticket_with_reply_button(message):
    user_id = message.from_user.id
    markup = types.InlineKeyboardMarkup()
    btn = types.InlineKeyboardButton("💬 پاسخ بده", callback_data=f"reply_{user_id}")
    markup.add(btn)

    bot.send_message(ADMIN_ID, f"📩 پیام از کاربر {user_id}:\n{message.text}", reply_markup=markup)
    bot.send_message(user_id, "✅ پیام شما به پشتیبانی ارسال شد.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('reply_'))
def callback_reply_to_user(call):
    user_id = call.from_user.id
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "شما اجازه پاسخ دادن ندارید.")
        return

    target_user_id = int(call.data.split('_')[1])
    admin_replying_to[user_id] = target_user_id

    bot.send_message(ADMIN_ID, f"لطفاً پاسخ خود را برای کاربر {target_user_id} ارسال کنید.\nبرای لغو پاسخ‌دهی /cancel را بفرستید.")
    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['cancel'])
def cancel_reply(message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID and user_id in admin_replying_to:
        del admin_replying_to[user_id]
        bot.send_message(ADMIN_ID, "❌ پاسخ‌دهی لغو شد.")

@bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID and m.text and m.from_user.id in admin_replying_to)
def send_admin_reply(message):
    admin_id = message.from_user.id
    if admin_id not in admin_replying_to:
        return
    target_user_id = admin_replying_to[admin_id]
    bot.send_message(target_user_id, f"💬 پاسخ پشتیبانی:\n{message.text}")
    bot.send_message(ADMIN_ID, "✅ پیام پاسخ ارسال شد.")
    del admin_replying_to[admin_id]

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def callback_buy_appleid(call):
    user_id = call.from_user.id
    if user_id not in users:
        bot.answer_callback_query(call.id, "ابتدا /start را بزنید و شماره موبایل خود را ارسال کنید.")
        return

    appleid_type = call.data
    prices = {
        'buy_2018': (250000, "1234-5678-9012-3456"),
        'buy_2025': (200000, "1234-5678-9012-3456"),
        'buy_personal': (350000, "1234-5678-9012-3456"),
    }
    if appleid_type not in prices:
        bot.answer_callback_query(call.id, "انتخاب نامعتبر است.")
        return

    price, card_number = prices[appleid_type]
    users[user_id]['selected_appleid'] = appleid_type

    text = (
        f"شما نوع اپل‌آیدی {call.message.text} را انتخاب کردید.\n"
        f"لطفاً مبلغ {price:,} تومان را به شماره کارت {card_number} واریز کنید.\n"
        f"پس از واریز، رسید پرداخت را با عکس ارسال کنید."
    )
    bot.send_message(user_id, text)
    bot.answer_callback_query(call.id, "انتخاب شما ثبت شد.")

def run_bot():
    bot.remove_webhook()
    bot.set_webhook(url='https://appleid035.onrender.com/webhook')
    app.run(host='0.0.0.0', port=5000)

if __name__ == '__main__':
    run_bot()
