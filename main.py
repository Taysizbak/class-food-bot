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
    bot.send_message(message.chat.id, "سلام! لطفاً نام و نام خانوادگی خود را وارد کنید 👇")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    name = message.text.strip()
    user_data[message.chat.id] = {'name': name, 'choices': {}}
    show_day_menu(message)

def show_day_menu(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for day in days:
        markup.add(day)
    markup.add("پایان ✅")
    bot.send_message(message.chat.id, "روز مورد نظر برای انتخاب غذا را بزن 👇", reply_markup=markup)
    bot.register_next_step_handler(message, choose_day)

def choose_day(message):
    day = message.text.strip()
    if day == "پایان ✅":
        show_summary(message)
        return
    if day not in days:
        bot.send_message(message.chat.id, "روز نامعتبر است ❌ لطفاً یکی از روزهای هفته را انتخاب کنید.")
        show_day_menu(message)
        return
    user_data[message.chat.id]['current_day'] = day
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("ناهار 🍛", "شام 🍲", "هردو ✅")
    bot.send_message(message.chat.id, f"برای {day} چه غذایی می‌خوای؟", reply_markup=markup)
    bot.register_next_step_handler(message, choose_meal)

def choose_meal(message):
    choice = message.text.strip()
    day = user_data[message.chat.id]['current_day']
    if "هردو" in choice:
        user_data[message.chat.id]['choices'][day] = ["ناهار", "شام"]
    elif "ناهار" in choice:
        user_data[message.chat.id]['choices'][day] = ["ناهار"]
    elif "شام" in choice:
        user_data[message.chat.id]['choices'][day] = ["شام"]
    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های مشخص‌شده را انتخاب کنید ❌")
        choose_day(message)
        return
    bot.send_message(message.chat.id, f"✅ انتخاب برای {day} ثبت شد!")
    show_day_menu(message)

def show_summary(message):
    choices = user_data[message.chat.id].get('choices', {})
    summary = "خلاصه انتخاب‌های شما:
"
    for day, meals in choices.items():
        summary += f"📅 {day}: {', '.join(meals)}
"
    bot.send_message(message.chat.id, summary)
    bot.send_message(message.chat.id, "✅ ثبت نهایی انجام شد. ممنون 🌸")

# دستور فقط ادمین
@bot.message_handler(commands=['list'])
def full_list(message):
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⛔️ فقط ادمین‌ها می‌توانند این دستور را اجرا کنند.")
        return

    if not user_data:
        bot.send_message(message.chat.id, "فعلاً هیچ کاربری انتخابی ثبت نکرده 💤")
        return

    text = "📋 لیست انتخاب‌های کل کلاس:

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

print("ربات در حال اجراست...")
bot.infinity_polling()
