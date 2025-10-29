# -*- coding: utf-8 -*-
import telebot
from telebot import types
import os

# 🔹 گرفتن توکن از Environment Variables
TOKEN = os.environ.get("TOKEN")
bot = telebot.TeleBot(TOKEN)

# ✅ آیدی عددی ادمین‌ها
ADMIN_IDS = [7498956077]

# دیکشنری برای ذخیره انتخاب‌های کاربران
user_data = {}

# روزهای هفته (شنبه تا پنج‌شنبه)
days = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه"]

# شروع ربات
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, u"سلام! لطفاً نام و نام خانوادگی خود را وارد کنید 👇")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text.strip()
    user_data[message.chat.id] = {'name': name, 'choices': {}}
    show_day_menu(message)

def show_day_menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for day in days:
        markup.add(day)
    markup.add(u"پایان ✅")
    bot.send_message(message.chat.id, u"روز مورد نظر برای انتخاب غذا را بزن 👇", reply_markup=markup)
    bot.register_next_step_handler(message, choose_day)

def choose_day(message):
    day = message.text.strip()
    if day == u"پایان ✅":
        show_summary(message)
        return
    if day not in days:
        bot.send_message(message.chat.id, u"روز نامعتبر است ❌ لطفاً یکی از روزهای هفته را انتخاب کنید.")
        show_day_menu(message)
        return
    user_data[message.chat.id]['current_day'] = day
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add(u"ناهار 🍛", u"شام 🍲", u"هردو ✅")
    bot.send_message(message.chat.id, f"برای {day} چه غذایی می‌خوای؟", reply_markup=markup)
    bot.register_next_step_handler(message, choose_meal)

def choose_meal(message):
    choice = message.text.strip()
    day = user_data[message.chat.id]['current_day']
    if u"هردو" in choice:
        user_data[day] = [u"ناهار", u"شام"]
        user_data[message.chat.id]['choices'][day] = [u"ناهار", u"شام"]
    elif u"ناهار" in choice:
        user_data[message.chat.id]['choices'][day] = [u"ناهار"]
    elif u"شام" in choice:
        user_data[message.chat.id]['choices'][day] = [u"شام"]
    else:
        bot.send_message(message.chat.id, u"لطفاً یکی از گزینه‌های مشخص‌شده را انتخاب کنید ❌")
        choose_day(message)
        return
    bot.send_message(message.chat.id, f"✅ انتخاب برای {day} ثبت شد!")
    show_day_menu(message)

def show_summary(message):
    choices = user_data[message.chat.id].get('choices', {})
    summary = "Summary of your selections:"
    for day in days:
    meals = choices.get(day, [])
    if meals:  # فقط روزهایی که انتخاب شده
        summary += f"{day}: {', '.join(meals)}\n"
"
    bot.send_message(message.chat.id, summary)
    bot.send_message(message.chat.id, u"✅ ثبت نهایی انجام شد. ممنون 🌸")

# دستور فقط ادمین برای دیدن کل لیست
@bot.message_handler(commands=['list'])
def full_list(message):
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, u"⛔️ فقط ادمین‌ها می‌توانند این دستور را اجرا کنند.")
        return

    if not user_data:
        bot.send_message(message.chat.id, u"فعلاً هیچ کاربری انتخابی ثبت نکرده 💤")
        return

    text = u"📋 لیست انتخاب‌های کل کلاس:

"
    for uid, info in user_data.items():
        text += f"👤 {info['name']}:
"
        for day, meals in info.get('choices', {}).items():
            text += f"  • {day}: {', '.join(meals)}
"
        text += "
"
    bot.send_message(message.chat.id, text)

# دستور /reset فقط برای ادمین
@bot.message_handler(commands=['reset'])
def reset_data(message):
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, u"⛔️ فقط ادمین می‌تواند این دستور را اجرا کند.")
        return
    user_data.clear()
    bot.send_message(message.chat.id, u"✅ همه انتخاب‌ها پاک شد. آماده هفته‌ی جدید هستیم!")
    bot.send_message(message.chat.id, u"همه‌ی دانش‌آموزان لطفاً دوباره /start را بزنید و انتخاب غذا را انجام دهید 🍽")

print("ربات در حال اجراست...")
bot.infinity_polling()
