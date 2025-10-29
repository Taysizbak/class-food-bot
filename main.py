import telebot
from telebot import types

# 🟢 توکن ربات خودت رو اینجا بذار
TOKEN = "token inja neveshte shavad"
bot = telebot.TeleBot(TOKEN)

# 📦 ذخیره‌ی اطلاعات کاربران در حافظه
users = {}

days = ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه"]

# 🟣 شروع ربات
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    bot.send_message(user_id, "سلام! 👋 لطفاً نام و نام خانوادگی خود را وارد کنید:")
    bot.register_next_step_handler(message, get_name)

# 🟢 دریافت نام و فامیل
def get_name(message):
    user_id = message.chat.id
    users[user_id] = {"name": message.text, "choices": {}}
    bot.send_message(user_id, "خیلی خب، حالا روز مورد نظر را انتخاب کن:", reply_markup=day_keyboard())

# 🟡 صفحه انتخاب روز
def day_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for d in days:
        markup.add(types.KeyboardButton(d))
    markup.add(types.KeyboardButton("📋 پایان و مشاهده انتخاب‌ها"))
    return markup

# 🔹 دریافت روز انتخابی
@bot.message_handler(func=lambda msg: msg.text in days)
def select_day(message):
    user_id = message.chat.id
    day = message.text
    users[user_id]["current_day"] = day
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🍛 ناهار", callback_data="ناهار"))
    markup.add(types.InlineKeyboardButton("🍲 شام", callback_data="شام"))
    markup.add(types.InlineKeyboardButton("✅ ناهار و شام هر دو", callback_data="هر دو"))
    bot.send_message(user_id, f"برای روز {day} چی میل داری؟", reply_markup=markup)

# 🟢 ثبت انتخاب غذا
@bot.callback_query_handler(func=lambda call: call.data in ["ناهار", "شام", "هر دو"])
def choose_meal(call):
    user_id = call.message.chat.id
    day = users[user_id]["current_day"]
    users[user_id]["choices"][day] = call.data
    bot.answer_callback_query(call.id, "ثبت شد ✅")
    bot.send_message(user_id, f"انتخاب {call.data} برای روز {day} ثبت شد ✅")
    bot.send_message(user_id, "روز بعدی رو انتخاب کن یا دکمه پایان رو بزن:", reply_markup=day_keyboard())

# 🔸 پایان انتخاب‌ها و نمایش خلاصه
@bot.message_handler(func=lambda msg: msg.text == "📋 پایان و مشاهده انتخاب‌ها")
def finish(message):
    user_id = message.chat.id
    name = users[user_id]["name"]
    choices = users[user_id]["choices"]

    summary = f"📋 انتخاب‌های {name}:
"
    for d in days:
        if d in choices:
            summary += f"• {d}: {choices[d]}\n"
        else:
            summary += f"• {d}: ❌ انتخاب نشده\n"

    bot.send_message(user_id, summary)
    bot.send_message(user_id, "✅ ثبت نهایی انجام شد. سپاس 🌸")

# 🔹 دریافت لیست کامل کلاس (فقط ادمین)
@bot.message_handler(commands=['list'])
def full_list(message):
    result = "📜 لیست کامل کلاس:\n\n"
    for user_data in users.values():
        name = user_data['name']
        result += f"👤 {name}\n"
        for d in days:
            meal = user_data['choices'].get(d, "❌ انتخاب نشده")
            result += f"  - {d}: {meal}\n"
        result += "\n====================\n"
    bot.send_message(message.chat.id, result)

print("🤖 Bot is running...")
bot.infinity_polling()
