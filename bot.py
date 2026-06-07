import os
import logging
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SHEET_URL = "https://script.google.com/macros/s/AKfycbxDM7E6L37hjloR6cIO9906YSIEU6Ru4n74XNpRLxQ-zrbNmh1a4xGpyDyOMLDaMiNX5w/exec"

NAME, AGE, SPORT, WEIGHT_HEIGHT, SESSIONS, GOAL = range(6)

user_profiles = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "سلام! به ربات کودک المپیکی خوش اومدی! 🏅\n\n"
        "بریم پروفایل ورزشی بسازیم 💪\n\n"
        "اسم بچه‌تون چیه؟"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f"چه اسم قشنگی! 🌟\n{context.user_data['name']} چند سالشه؟"
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text(
        f"رشته ورزشی {context.user_data['name']} چیه؟ ⚽🥊🏊\n"
        "مثال: فوتبال، شنا، کاراته..."
    )
    return SPORT

async def get_sport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['sport'] = update.message.text
    await update.message.reply_text(
        f"وزن و قد {context.user_data['name']} چقدره؟ ⚖️\n"
        "مثال: ۳۵/۱۳۵"
    )
    return WEIGHT_HEIGHT

async def get_weight_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['weight_height'] = update.message.text
    await update.message.reply_text(
        f"{context.user_data['name']} چند جلسه در هفته تمرین می‌کنه؟ 🗓️\n"
        "مثال: ۳ جلسه"
    )
    return SESSIONS

async def get_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['sessions'] = update.message.text
    await update.message.reply_text(
        f"هدف ورزشی {context.user_data['name']} چیه؟ 🎯\n"
        "مثال: قهرمانی، تناسب اندام، لذت از ورزش، حرفه‌ای شدن..."
    )
    return GOAL

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['goal'] = update.message.text
    user_id = update.effective_user.id
    parent_name = update.effective_user.full_name
    user_profiles[user_id] = context.user_data.copy()

    name = context.user_data['name']
    age = context.user_data['age']
    sport = context.user_data['sport']
    wh = context.user_data['weight_height']
    sessions = context.user_data['sessions']
    goal = context.user_data['goal']

    # ذخیره در Google Sheet
    try:
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": str(user_id),
            "parent_name": parent_name,
            "child_name": name,
            "age": age,
            "sport": sport,
            "weight_height": wh,
            "sessions": sessions,
            "goal": goal
        }
        requests.post(SHEET_URL, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Sheet error: {e}")

    await update.message.reply_text(
        f"✅ پروفایل ورزشی با موفقیت ساخته شد!\n\n"
        f"🏅 پروفایل قهرمان کوچک\n"
        f"─────────────────\n"
        f"👤 نام: {name}\n"
        f"🎂 سن: {age} سال\n"
        f"⚽ رشته ورزشی: {sport}\n"
        f"⚖️ وزن و قد: {wh}\n"
        f"📅 جلسات تمرین: {sessions} در هفته\n"
        f"🎯 هدف: {goal}\n"
        f"─────────────────\n\n"
        f"💪🌟 آفرین! {name} عزیز، مطمئنم یه روز قهرمان می‌شی!\n\n"
        f"برای دیدن پروفایل دوباره /profile بزن."
    )
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_profiles:
        p = user_profiles[user_id]
        await update.message.reply_text(
            f"🏅 پروفایل قهرمان کوچک\n"
            f"─────────────────\n"
            f"👤 نام: {p['name']}\n"
            f"🎂 سن: {p['age']} سال\n"
            f"⚽ رشته ورزشی: {p['sport']}\n"
            f"⚖️ وزن و قد: {p['weight_height']}\n"
            f"📅 جلسات تمرین: {p['sessions']} در هفته\n"
            f"🎯 هدف: {p['goal']}\n"
        )
    else:
        await update.message.reply_text(
            "هنوز پروفایلی نداری! /start بزن تا بسازیم 😊"
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("ثبت‌نام لغو شد. هر وقت خواستی /start بزن! 😊")
    return ConversationHandler.END

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            SPORT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sport)],
            WEIGHT_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_weight_height)],
            SESSIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_sessions)],
            GOAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_goal)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("profile", profile))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
