import os
import logging
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
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

PHONE, NAME, AGE, HEIGHT, WEIGHT, SPORT, SESSIONS, GOAL = range(8)

user_profiles = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "سلام! به ربات کودک المپیکی خوش اومدی! 🏅\n\n"
        "بریم پروفایل ورزشی بسازیم 💪\n\n"
        "لطفاً شماره تماس والدین رو وارد کنید 📱\n"
        "مثال: ۰۹۱۲۱۲۳۴۵۶۷",
        reply_markup=ReplyKeyboardRemove()
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone'] = update.message.text
    await update.message.reply_text(
        "ممنون! 😊\n\n"
        "اسم و فامیل فرزندتون رو بنویسید 👤"
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        f"{context.user_data['name']} چند سالشه؟ 🎂"
    )
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text(
        f"قد {context.user_data['name']} چقدره؟ 📏\n"
        "مثال: ۱۳۵ (سانتی‌متر)"
    )
    return HEIGHT

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['height'] = update.message.text
    await update.message.reply_text(
        f"وزن {context.user_data['name']} چقدره؟ ⚖️\n"
        "مثال: ۳۵ (کیلوگرم)"
    )
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['weight'] = update.message.text
    await update.message.reply_text(
        f"رشته ورزشی {context.user_data['name']} چیه؟ ⚽🥊🏊\n"
        "مثال: فوتبال، شنا، کاراته...\n"
        "(در صورت نداشتن رشته بنویسید: ندارد)"
    )
    return SPORT

async def get_sport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['sport'] = update.message.text
    await update.message.reply_text(
        f"{context.user_data['name']} چند روز در هفته تحرک جدی و ورزش داره؟ 🗓️\n"
        "مثال: ۳ روز"
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
    weight = context.user_data['weight']
    height = context.user_data['height']
    phone = context.user_data['phone']
    sessions = context.user_data['sessions']
    goal = context.user_data['goal']

    try:
        data = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": str(user_id),
            "parent_name": parent_name,
            "child_name": name,
            "age": age,
            "sport": sport,
            "weight": weight,
            "height": height,
            "phone": phone,
            "sessions": sessions,
            "goal": goal
        }
        requests.post(SHEET_URL, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Sheet error: {e}")

    keyboard = [["📸 آنالیز بدنی"], ["👤 مشاهده پروفایل"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ پروفایل ورزشی با موفقیت ساخته شد!\n\n"
        f"🏅 پروفایل قهرمان کوچک\n"
        f"─────────────────\n"
        f"📱 شماره تماس: {phone}\n"
        f"👤 نام: {name}\n"
        f"🎂 سن: {age} سال\n"
        f"📏 قد: {height} سانتی‌متر\n"
        f"⚖️ وزن: {weight} کیلوگرم\n"
        f"⚽ رشته ورزشی: {sport}\n"
        f"🗓️ روزهای ورزش: {sessions} در هفته\n"
        f"🎯 هدف: {goal}\n"
        f"─────────────────\n\n"
        f"🌟 {name} عزیز، به کلاب کودک المپیکی خوش اومدی!\n"
        f"ما اینجاییم تا به تو کمک کنیم که بهترین خودت بشی 💪",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in user_profiles:
        p = user_profiles[user_id]
        keyboard = [["📸 آنالیز بدنی"], ["👤 مشاهده پروفایل"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"🏅 پروفایل قهرمان کوچک\n"
            f"─────────────────\n"
            f"📱 شماره تماس: {p['phone']}\n"
            f"👤 نام: {p['name']}\n"
            f"🎂 سن: {p['age']} سال\n"
            f"📏 قد: {p['height']} سانتی‌متر\n"
            f"⚖️ وزن: {p['weight']} کیلوگرم\n"
            f"⚽ رشته ورزشی: {p['sport']}\n"
            f"🗓️ روزهای ورزش: {p['sessions']} در هفته\n"
            f"🎯 هدف: {p['goal']}\n",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text(
            "هنوز پروفایلی نداری! /start بزن تا بسازیم 😊"
        )

async def body_analysis_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📸 آنالیز بدنی هوشمند\n\n"
        "برای اینکه بتونیم بهترین برنامه ورزشی رو برای فرزندتون طراحی کنیم، "
        "نیاز به ارزیابی بدنی داریم.\n\n"
        "🔒 حریم خصوصی: عکس‌ها فقط توسط مربی بررسی میشن و جایی ذخیره نمیشن.\n\n"
        "لطفاً ۳ عکس از فرزندتون بفرستید:\n"
        "1️⃣ از جلو\n"
        "2️⃣ از بغل\n"
        "3️⃣ از پشت\n\n"
        "👦 پسران: شلوارک و بدون لباس\n"
        "👧 دختران: شلوارک و نیم‌تنه ورزشی\n\n"
        "با فرستادن عکس، رضایت خود را برای آنالیز اعلام می‌کنید. ✅"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "📸 آنالیز بدنی":
        await body_analysis_info(update, context)
    elif text == "👤 مشاهده پروفایل":
        await profile(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "ثبت‌نام لغو شد. هر وقت خواستی /start بزن! 😊",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHONE: [MessageHandler(filters.TEXT, get_phone)],
            NAME: [MessageHandler(filters.TEXT, get_name)],
            AGE: [MessageHandler(filters.TEXT, get_age)],
            HEIGHT: [MessageHandler(filters.TEXT, get_height)],
            WEIGHT: [MessageHandler(filters.TEXT, get_weight)],
            SPORT: [MessageHandler(filters.TEXT, get_sport)],
            SESSIONS: [MessageHandler(filters.TEXT, get_sessions)],
            GOAL: [MessageHandler(filters.TEXT, get_goal)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
