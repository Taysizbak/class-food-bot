import telebot
from telebot import types

# 🔹 توکن ربات خودت رو از BotFather اینجا بنویس
TOKEN = "TOKEN_INJA_NEVESHTE_SHAVAD"

bot = telebot.TeleBot(TOKEN)

# ✅ آیدی عددی ادمین‌ها
ADMIN_IDS = [7498956077]

# دیکشنری برای ذخیره انتخاب‌های کاربران
user_data = {}

# روزهای هفته (شنبه تا پنج‌شنبه)
days = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه"]

# گزینه‌های ناهار و شام
meals = ["ناهار", "شام"]

# شروع گفتگو
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "سلام! لطفاً نام و نام خانوادگی خود را وارد کنید 👇")
    bot.register_next_step_handler(message, get_name)

# دریافت نام
def get_name(message):
    name = message.text.strip()
    user_data[message.chat.id] = {'name': name, 'choices': {}}
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for day in days:
        markup.add(day)
    bot.send_message(message.chat.id, "حالا روزی که می‌خوای غذا انتخاب کنی رو بزن 👇", reply_markup=markup)
    bot.register_next_step_handler(message, choose_day)

# انتخاب روز
def choose_day(message):
    day = message.text
    if day not in days:
        bot.send_message(message.chat.id, "روز نامعتبره ❌ دوباره یکی از روزهای هفته رو بزن.")
        return start(message)
    user_data[message.chat.id]['current_day'] = day

    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    markup.add("ناهار 🍛", "شام 🍲", "هردو ✅")
    bot.send_message(message.chat.id, f"برای {day} چی می‌خوای؟", reply_markup=markup)
    bot.register_next_step_handler(message, choose_meal)

# انتخاب ناهار یا شام
def choose_meal(message):
    choice = message.text
    day = user_data[message.chat.id]['current_day']

    if "ناهار" in choice and "شام" in choice:
        user_data[message.chat.id]['choices'][day] = ["ناهار", "شام"]
    elif "ناهار" in choice:
        user_data[message.chat.id]['choices'][day] = ["ناهار"]
    elif "شام" in choice:
        user_data[message.chat.id]['choices'][day] = ["شام"]
    else:
        bot.send_message(message.chat.id, "لطفاً یکی از گزینه‌های مشخص‌شده رو انتخاب کن ❌")
        return choose_day(message)

    bot.send_message(message.chat.id, f"✅ برای {day} ثبت شد!")
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for d in days:
        markup.add(d)
    markup.add("پایان ✅")
    bot.send_message(message.chat.id, "روز بعدی رو انتخاب کن یا دکمه پایان رو بزن 👇", reply_markup=markup)
    bot.register_next_step_handler(message, next_day)

# مرحله بعدی یا پایان
def next_day(message):
    if "پایان" in message.text:
        show_summary(message)
        return
    else:
        choose_day(message)

# خلاصه برای هر کاربر
def show_summary(message):
    choices = user_data[message.chat.id]['choices']
    summary = "خلاصه انتخاب‌های شما:
"
    for day, meals in choices.items():
        summary += f"📅 {day}: {', '.join(meals)}
"
    bot.send_message(message.chat.id, summary)
    bot.send_message(message.chat.id, "✅ انتخاب‌ها ثبت شد، ممنون!")

# فقط ادمین ببیند لیست کامل را
@bot.message_handler(commands=['list'])
def full_list(message):
    if message.chat.id not in ADMIN_IDS:
        bot.send_message(message.chat.id, "⛔️ فقط ادمین‌ها می‌تونن این دستور رو اجرا کنن.")
        return

    if not user_data:
        bot.send_message(message.chat.id, "فعلاً کسی چیزی انتخاب نکرده 💤")
        return

    text = "📋 لیست انتخاب‌های کل کلاس:

"
    for uid, info in user_data.items():
        text += f"👤 {info['name']}:
"
        for day, meals in info['choices'].items():
            text += f"  • {day}: {', '.join(meals)}
"
        text += "
"

    bot.send_message(message.chat.id, text)

print("ربات در حال اجراست...")
bot.infinity_polling()
