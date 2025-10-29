from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import json
import os

DATA_FILE = "data.json"

users = {}
admins = set()

# ------------------ مدیریت فایل داده ------------------
def load_data():
    global users, admins
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            users = data.get("users", {})
            admins = set(data.get("admins", []))

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump({"users": users, "admins": list(admins)}, f, ensure_ascii=False, indent=2)

# ------------------ شروع ربات ------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users[user_id] = {"step": "name", "data": {}}
    save_data()
    await update.message.reply_text(
        "به ربات رزرو غذای موسسه سلامت خوش آمدید.\n\nلطفاً نام و نام خانوادگی خود را وارد کنید:"
    )

# ------------------ دریافت نام ------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text.strip()

    if user_id not in users:
        await update.message.reply_text("برای شروع، دستور /start را بزنید.")
        return

    step = users[user_id]["step"]

    # گام ۱: دریافت نام
    if step == "name":
        users[user_id]["data"]["name"] = text
        users[user_id]["data"]["term"] = "ترم دو پرستاری"
        users[user_id]["step"] = "day_selection"
        save_data()

        days = [["شنبه", "یک‌شنبه"], ["دوشنبه", "سه‌شنبه"], ["چهارشنبه", "پنج‌شنبه"], ["جمعه"]]
        markup = ReplyKeyboardMarkup(days, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text("روز مورد نظر برای رزرو را انتخاب کنید:", reply_markup=markup)

    # گام ۲: انتخاب روز
    elif step == "day_selection":
        users[user_id]["data"]["current_day"] = text
        users[user_id]["step"] = "meal_selection"
        save_data()

        meals = [["ناهار", "شام"], ["هر دو"]]
        markup = ReplyKeyboardMarkup(meals, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(f"برای {text} کدام وعده را می‌خواهید؟", reply_markup=markup)

    # گام ۳: انتخاب وعده
    elif step == "meal_selection":
        day = users[user_id]["data"]["current_day"]
        meal = text
        if "choices" not in users[user_id]["data"]:
            users[user_id]["data"]["choices"] = {}
        users[user_id]["data"]["choices"][day] = meal

        users[user_id]["step"] = "next_action"
        save_data()

        markup = ReplyKeyboardMarkup([["انتخاب روز دیگر"], ["پایان رزرو"]], resize_keyboard=True)
        await update.message.reply_text("انتخاب شما ثبت شد. می‌خواهید ادامه دهید یا رزرو را تمام کنید؟", reply_markup=markup)

    # گام ۴: ادامه یا پایان
    elif step == "next_action":
        if text == "انتخاب روز دیگر":
            users[user_id]["step"] = "day_selection"
            save_data()

            days = [["شنبه", "یک‌شنبه"], ["دوشنبه", "سه‌شنبه"], ["چهارشنبه", "پنج‌شنبه"], ["جمعه"]]
            markup = ReplyKeyboardMarkup(days, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text("روز بعدی را انتخاب کنید:", reply_markup=markup)

        elif text == "پایان رزرو":
            users[user_id]["step"] = "done"
            save_data()

            summary = "خلاصه رزرو شما:\n"
            for d, m in users[user_id]["data"]["choices"].items():
                summary += f"- {d}: {m}\n"

            await update.message.reply_text(summary + "\nرزرو شما با موفقیت ثبت شد. سپاس از همکاری شما.")
        else:
            await update.message.reply_text("گزینه نامعتبر است. لطفاً از دکمه‌ها استفاده کنید.")

# ------------------ نمایش فهرست برای ادمین ------------------
async def list_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in admins:
        await update.message.reply_text("فقط ادمین‌ها می‌توانند فهرست را ببینند.")
        return

    if not users:
        await update.message.reply_text("هیچ رزروی ثبت نشده است.")
        return

    msg = "فهرست رزروها:\n\n"
    for uid, info in users.items():
        if "data" not in info or "choices" not in info["data"]:
            continue
        name = info["data"].get("name", "نامشخص")
        msg += f"نام: {name}\n"
        for d, m in info["data"]["choices"].items():
            msg += f"  {d}: {m}\n"
        msg += "\n"

    await update.message.reply_text(msg)

# ------------------ افزودن ادمین ------------------
async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("مثال: /addadmin 123456789")
        return

    admin_id = context.args[0]
    admins.add(admin_id)
    save_data()
    await update.message.reply_text(f"کاربر {admin_id} به عنوان ادمین اضافه شد.")

# ------------------ ریست داده‌ها ------------------
async def reset_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in admins:
        await update.message.reply_text("فقط ادمین‌ها می‌توانند داده‌ها را ریست کنند.")
        return

    for uid in users:
        users[uid]["step"] = "name"
        users[uid]["data"] = {}
    save_data()
    await update.message.reply_text("تمام رزروها ریست شد. کاربران می‌توانند دوباره رزرو کنند.")

# ------------------ اجرای ربات ------------------
def main():
    load_data()
    TOKEN = "توکن_ربات_خودت_را_اینجا_بگذار"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_all))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("reset", reset_data))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("ربات فعال است...")
    app.run_polling()

if __name__ == "__main__":
    main()
