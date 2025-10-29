import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# =====================================================================
# تنظیمات (Settings)
# =====================================================================
# توکن ربات باید از متغیر محیطی Render خوانده شود
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
# ADMIN_ID را با آیدی عددی ادمین جایگزین کنید
ADMIN_ID = 7498956077  # !!! REPLACE THIS WITH YOUR ACTUAL ADMIN ID !!!

# مسیر دیتابیس برای سازگاری با Render (استفاده از فضای موقت)
DB_PATH = "/tmp/food_reservations.db"

# ثابت‌ها
NURSING_TERM = "ترم ۲ پرستاری"
MEALS = ["ناهار", "شام"]
DAYS_OF_WEEK = ["شنبه", "یکشنبه", "دوشنبه", "سه شنبه", "چهارشنبه"]

# =====================================================================
# مدیریت دیتابیس (Database Management)
# =====================================================================

def init_db():
    """Initialize SQLite database and create tables."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # جدول کاربران برای ذخیره نام و نام خانوادگی
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT
            )
        """)
        
        # جدول رزروها
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day TEXT,
                meal_type TEXT,
                term TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# =====================================================================
# توابع کمکی (Utility Functions)
# =====================================================================

def get_user_data(user_id):
    """Get user's registration status and name."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT first_name, last_name FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result

def register_user(user_id, first_name, last_name):
    """Register or update user details."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # استفاده از INSERT OR REPLACE برای ثبت نام اولیه و به‌روزرسانی‌های بعدی
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, first_name, last_name) 
        VALUES (?, ?, ?)
    """, (user_id, first_name, last_name))
    conn.commit()
    conn.close()

def save_reservation(user_id, day, meal_type):
    """Save a single reservation entry."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reservations (user_id, day, meal_type, term) 
        VALUES (?, ?, ?, ?)
    """, (user_id, day, meal_type, NURSING_TERM))
    conn.commit()
    conn.close()

def get_all_reservations():
    """Fetch all reservations for the admin view."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # JOIN با جدول کاربران برای نمایش نام‌ها
    query = """
        SELECT 
            u.first_name, 
            u.last_name, 
            r.day, 
            r.meal_type,
            r.term
        FROM reservations r
        JOIN users u ON r.user_id = u.user_id
        ORDER BY r.day, r.meal_type
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return results

def reset_reservations():
    """Delete all reservations for the next week."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reservations")
    conn.commit()
    conn.close()
    return True

# =====================================================================
# وضعیت‌های کاربر (User States)
# =====================================================================
REGISTRATION, DAY_CHOICE, MEAL_CHOICE = range(3)
user_data_storage = {} # برای نگهداری موقت داده‌های رزرو کاربر

# =====================================================================
# هندلرها (Handlers)
# =====================================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    
    # ۱. بررسی وضعیت ثبت‌نام
    user = get_user_data(user_id)
    
    if user:
        await update.message.reply_text(
            f"به ربات رزرو غذای هفتگی خوش آمدید.\n"
            f"ترم انتخابی شما: {NURSING_TERM}\n"
            f"برای شروع رزرو، /reserve را ارسال کنید."
        )
        return REGISTRATION # در حالت ثبت نام نیستیم، از ابتدا شروع می‌کنیم
    else:
        # شروع فرآیند ثبت نام
        await update.message.reply_text(
            f"به ربات رزرو غذای هفتگی خوش آمدید.\n"
            f"لطفاً نام خود را به فارسی وارد کنید (مثال: علی احمدی)."
        )
        context.user_data['state'] = REGISTRATION
        return REGISTRATION

async def handle_registration(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    full_name = update.message.text.strip()
    
    try:
        first_name, last_name = map(str.strip, full_name.split(maxsplit=1))
    except ValueError:
        await update.message.reply_text("فرمت نام وارد شده صحیح نیست. لطفاً نام و نام خانوادگی خود را با فاصله وارد کنید (مثال: محمد حسینی).")
        return REGISTRATION

    register_user(user_id, first_name, last_name)
    
    await update.message.reply_text(
        f"ثبت نام شما با موفقیت انجام شد.\n"
        f"ترم ثابت رزرو: {NURSING_TERM}\n"
        f"اکنون می‌توانید با دستور /reserve رزرو خود را شروع کنید."
    )
    context.user_data['state'] = -1 # پایان فرآیند
    return -1

async def reserve_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user = get_user_data(user_id)
    
    if not user:
        await update.message.reply_text("لطفاً ابتدا با دستور /start خود را ثبت نام کنید.")
        return REGISTRATION

    # پاکسازی رزروهای قبلی در جلسه جاری (اگر کاربر از وسط کنسل کرده باشد)
    if 'current_reservation' in context.user_data:
        del context.user_data['current_reservation']
        
    # ساخت کیبورد انتخاب روز
    keyboard = [
        [InlineKeyboardButton(day, callback_data=f"day_{day}")] for day in DAYS_OF_WEEK
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"ترم شما: {NURSING_TERM}\n"
        "لطفاً روزی را که می‌خواهید رزرو کنید، انتخاب نمایید:",
        reply_markup=reply_markup
    )
    context.user_data['state'] = DAY_CHOICE
    return DAY_CHOICE

async def select_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    data = query.data.split('_')[1] # روز انتخاب شده
    user_id = query.from_user.id
    
    # ذخیره روز در داده‌های موقت کاربر
    context.user_data['current_reservation'] = {'day': data}
    
    # ساخت کیبورد انتخاب وعده
    keyboard = [
        [InlineKeyboardButton(meal, callback_data=f"meal_{meal}")] for meal in MEALS
    ]
    # افزودن گزینه "هر دو" به عنوان یک دکمه جدا
    keyboard.append([InlineKeyboardButton("هر دو (ناهار و شام)", callback_data="meal_both")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text=f"روز {data} انتخاب شد.\nلطفاً وعده مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    context.user_data['state'] = MEAL_CHOICE
    return MEAL_CHOICE

async def select_meal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    day = context.user_data['current_reservation']['day']
    meal_data = query.data.split('_')[1]
    
    meals_to_save = []
    if meal_data == "both":
        meals_to_save = MEALS
    else:
        meals_to_save.append(meal_data)
        
    # ذخیره نهایی در دیتابیس
    for meal in meals_to_save:
        save_reservation(user_id, day, meal)
        
    user_data = get_user_data(user_id)
    full_name = f"{user_data[0]} {user_data[1]}" if user_data else "کاربر"
    
    await query.edit_message_text(
        text=f"✅ رزرو برای {full_name} در روز {day} برای وعده {'و '.join(meals_to_save)} با موفقیت ثبت شد.\n\n"
             f"برای رزرو روز دیگر، دوباره دستور /reserve را ارسال کنید."
    )
    
    # بازگشت به حالت اصلی پس از ذخیره موفق
    context.user_data['state'] = -1
    return -1

async def admin_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش لیست نهایی رزروها برای ادمین."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی لازم برای اجرای این دستور را ندارید.")
        return

    await update.message.reply_text("در حال تهیه لیست نهایی رزروها...")
    
    reservations = get_all_reservations()
    
    if not reservations:
        response = "لیست رزروهای این هفته خالی است."
    else:
        # گروه‌بندی برای نمایش بهتر (روز -> وعده -> نام)
        grouped = {}
        for first_name, last_name, day, meal_type, term in reservations:
            if day not in grouped:
                grouped[day] = {}
            if meal_type not in grouped[day]:
                grouped[day][meal_type] = []
            
            grouped[day][meal_type].append(f"{first_name} {last_name}")

        response_lines = [f"**لیست رزروهای ترم {term}**\n"]
        
        # مرتب سازی روزها بر اساس ترتیب DAYS_OF_WEEK
        sorted_days = DAYS_OF_WEEK
        
        for day in sorted_days:
            if day in grouped:
                response_lines.append(f"🗓️ **{day}:**")
                for meal in MEALS:
                    if meal in grouped[day]:
                        names = "\n  - ".join(grouped[day][meal])
                        response_lines.append(f"  - **{meal}:**\n  - {names}")
                response_lines.append("-" * 20)

        response = "\n".join(response_lines)

    await update.message.reply_text(response, parse_mode='Markdown')

async def admin_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ریست کردن لیست رزروها توسط ادمین."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("شما دسترسی لازم برای اجرای این دستور را ندارید.")
        return
        
    if reset_reservations():
        await update.message.reply_text(
            "✅ لیست رزروهای هفتگی با موفقیت ریست (پاک) شد. آماده برای رزروهای هفته آینده."
        )
    else:
        await update.message.reply_text("❌ خطایی در هنگام ریست کردن دیتابیس رخ داد.")


async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاسخ به پیام‌هایی که در حالت خاصی نیستند."""
    state = context.user_data.get('state')
    
    if state == REGISTRATION:
        await handle_registration(update, context)
    elif state == DAY_CHOICE:
        await update.message.reply_text("لطفاً از دکمه‌های زیر برای انتخاب روز استفاده کنید.")
    elif state == MEAL_CHOICE:
        await update.message.reply_text("لطفاً از دکمه‌های زیر برای انتخاب وعده استفاده کنید.")
    else:
        await update.message.reply_text(
            "منظور شما را متوجه نشدم. برای شروع رزرو، از دستور /reserve استفاده کنید."
        )


def main() -> None:
    """Run the bot."""
    if not TELEGRAM_TOKEN:
        print("FATAL ERROR: TELEGRAM_TOKEN not found in environment variables.")
        return
        
    if not init_db():
        print("FATAL ERROR: Database initialization failed.")
        return
        
    # ساخت اپلیکیشن
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # هندلرهای دستورات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reserve", reserve_command))
    application.add_handler(CommandHandler("adminlist", admin_list))
    application.add_handler(CommandHandler("adminreset", admin_reset))

    # هندلرهای کال‌بک (دکمه‌های اینلاین)
    application.add_handler(CallbackQueryHandler(select_day, pattern='^day_'))
    application.add_handler(CallbackQueryHandler(select_meal, pattern='^meal_'))

    # هندلر عمومی برای مدیریت ورودی‌های متنی در حین فرآیند (Fallback)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler))

    # اجرای ربات (استفاده از پولینگ برای اجرای محلی)
    # در Render، معمولاً از Webhook استفاده می‌شود، اما برای تست محلی Polling مناسب است.
    # برای Render، فقط کافیست اجرای این خط را در .render.yaml مدیریت کنید.
    print("Bot started polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
