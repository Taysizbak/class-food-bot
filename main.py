import logging
import os
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    ConversationHandler, # در صورت استفاده از مکالمات چند مرحله ای
)

# --- تنظیمات اولیه ---
# تنظیم لاگ برای مشاهده دقیق‌تر جزئیات در محیط Render
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- تعریف وضعیت‌های مکالمه (اگر از ConversationHandler استفاده می کنید) ---
# اگر از ربات ساده استفاده می کنید، این بخش را می توانید نادیده بگیرید.
RESERVATION_FLOW, FOOD_CHOICE, CONFIRMATION = range(3) 

# --- توابع هندلر (Handler Functions) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر برای دستور /start"""
    user = update.effective_user
    logger.info(f"دستور /start توسط {user.first_name} اجرا شد.")
    await update.message.reply_html(
        f"سلام {user.mention_html()}! ربات رزرو غذا آماده به کار است.",
        # اگر ربات پیچیده تری می خواهید، می توانید اینجا دکمه های شروع را اضافه کنید.
    )
    # return RESERVATION_FLOW # اگر می خواهید بلافاصله وارد مکالمه شوید

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر برای دستور /help"""
    await update.message.reply_text("برای شروع، دستور /start را ارسال کنید.")

# --- تابع اصلی برنامه ---

async def main() -> None:
    """نقطه ورود اصلی برنامه و اجرای پولینگ."""
    
    # 1. استخراج توکن از متغیر محیطی Render
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
    if not TELEGRAM_TOKEN:
        logger.error("خطا: متغیر محیطی TELEGRAM_TOKEN در Render تنظیم نشده است.")
        return

    # 2. ساخت Application با builder 
    # توجه: این خط، همان خطی است که در اجرای قبلی شما خطا می داد.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # 3. اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    # --- مثال برای اضافه کردن ConversationHandler (برای ربات های پیچیده) ---
    # اگر از ربات پیچیده تری مانند رزرو غذا استفاده می کنید، این بخش را فعال کنید:
    # conv_handler = ConversationHandler(
    #     entry_points=[CommandHandler("reserve", start_reservation)], # تابع شروع مکالمه
    #     states={
    #         RESERVATION_FLOW: [CommandHandler("food", food_choice)],
    #         FOOD_CHOICE: [CommandHandler("confirm", confirm_reservation)],
    #     },
    #     fallbacks=[CommandHandler("cancel", cancel)],
    # )
    # application.add_handler(conv_handler)

    # 4. اجرای پولینگ با سینتکس ناهمزمان (Async) برای رفع مشکل Updater
    # این مهمترین تغییر برای حل مشکل شماست.
    logger.info("شروع اجرای ربات از طریق Polling...")
    await application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    # استفاده از asyncio.run برای اجرای تابع ناهمزمان main()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("برنامه با دریافت سیگنال قطع شد (Ctrl+C).")
    except Exception as e:
        logger.error(f"یک خطای غیرمنتظره در اجرای اصلی رخ داد: {e}")
