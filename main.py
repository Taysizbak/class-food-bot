import logging
import os
from telegram import Update
# ما ContextTypes را به طور خاص برای نوع‌دهی (Type Hinting) ایمپورت می‌کنیم
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes
)

# --- ۱. تنظیمات اولیه ---
# اطمینان از وجود توکن از محیط Render
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# تنظیم لاگ برای دیباگ کردن بهتر
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# --- ۲. توابع هندلر (Handler Functions) ---
# تمام توابع هندلر باید با 'async' تعریف شوند و ContextTypes را بپذیرند.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به دستور /start و استفاده از سینتکس مدرن."""
    user = update.effective_user
    await update.message.reply_html(
        f"سلام {user.mention_html()}! ربات شما با استفاده از Application Builder با موفقیت اجرا شد.",
        # این خط اطمینان می‌دهد که از جدیدترین قابلیت‌های API استفاده می‌شود
        # reply_markup=ForceReply(selective=True), 
    )

async def handle_all_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """این تابع جایگزین منطق اصلی شما برای پاسخ به پیام‌ها می‌شود."""
    
    # *** این قسمت را با منطق ربات خود جایگزین کنید ***
    # مثال: اگر پیام حاوی متن است، آن را تکرار کنید
    if update.message and update.message.text:
        received_text = update.message.text
        logger.info(f"پیام دریافت شده: {received_text}")
        
        # پاسخ دادن
        await update.message.reply_text(f"متن شما دریافت شد: '{received_text}'")
    # **************************************************

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """پاسخ به هر پیام یا دستوری که تعریف نشده است."""
    await update.message.reply_text("متأسفم، این دستور شناخته نشد.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """لاگ کردن هر خطایی که در حین پردازش رخ دهد."""
    logger.error(f'خطا در پردازش Update: "{update}"، خطا: {context.error}')


# --- ۳. تابع اصلی راه‌اندازی (Main Execution) ---

def main() -> None:
    """شروع به کار ربات و مدیریت استقرار."""
    
    if not TELEGRAM_TOKEN:
        logger.error("خطا: متغیر محیطی TELEGRAM_TOKEN در Render تنظیم نشده است.")
        return

    # ساخت شیء Application (جایگزین Updater)
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    
    # هندل کردن تمام پیام‌های متنی (به جز دستورات که توسط CommandHandler گرفته می‌شوند)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_all_text_messages))

    # هندل کردن هر چیزی که باقی می‌ماند (برای اطمینان از لاگ شدن خطاها)
    application.add_handler(MessageHandler(filters.ALL, unknown))
    
    # افزودن Error Handler عمومی
    application.add_error_handler(error_handler)

    # اجرای ربات با استفاده از Polling (روش اصلی اجرای ربات)
    logger.info("ربات در حال شروع به کار (Polling) است...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
