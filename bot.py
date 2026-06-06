import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        f"سلام {user.mention_html()} عزیز! 🌟\n\n"
        "به باشگاه قهرمانان کوچک خوش اومدی! 🏆⚽🥊\n\n"
        "اینجا جایی‌ه که ورزشکارهای جوان مثل تو رشد می‌کنن و قوی‌تر می‌شن! 💪🔥\n\n"
        "یادت باشه:\n"
        "🌠 هر قهرمان بزرگی یه روز مثل تو شروع کرد!\n"
        "🎯 تمرین کن، تلاش کن، قوی بشو!\n"
        "😄 از ورزش لذت ببر!\n\n"
        "برای دیدن راهنما دستور /help رو بزن 👇"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 راهنمای ربات:\n\n"
        "/start — شروع و خوش‌آمدگویی 👋\n"
        "/help — نمایش این راهنما 📖\n"
        "/about — درباره این ربات ℹ️\n\n"
        "هر پیامی هم بفرستی، بهت جواب می‌دم! 😊"
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "ℹ️ درباره ربات:\n\n"
        "این ربات برای ورزشکارهای جوان ۶ تا ۱۳ ساله طراحی شده! 🏅\n"
        "هدف ما اینه که ورزش رو برات جذاب‌تر و شادتر کنیم! 🎉"
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(update.message.text)

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
