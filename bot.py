import os
import logging
import requests
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
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

SHEET_URL = "https://script.google.com/macros/s/AKfycbyyK6i3ihFBBNiMMF94tX7h01U4Ymx5HZgydfCLN1jM0y7gwo-uU33s-E9eNVu0Xr0m/exec"

PHONE, NAME, AGE, HEIGHT, WEIGHT, SPORT, SESSIONS, GOAL = range(8)

user_profiles = {}

def get_profile_from_sheet(user_id: str) -> dict:
    try:
        response = requests.get(f"{SHEET_URL}?user_id={user_id}", timeout=10)
        data = response.json()
        if data.get("found"):
            return data.get("profile", {})
    except Exception as e:
        logger.error(f"Sheet read error: {e}")
    return {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()

    # دکمه اشتراک‌گذاری شماره
    phone_button = KeyboardButton(
        text="📱 اشتراک‌گذاری شماره تلفن",
        request_contact=True
    )
    reply_markup = ReplyKeyboardMarkup(
        [[phone_button]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await update.message.reply_text(
        "سلام! به باشگاه کودک المپیکی خوش اومدی! 🏅\n\n"
        "اینجا جایی‌ه که ورزشکارهای جوان مثل فرزند شما رشد می‌کنن و قوی‌تر می‌شن 💪\n\n"
        "✅ پروفایل ورزشی اختصاصی\n"
        "✅ برنامه تمرینی هوشمند\n"
        "✅ برنامه غذایی سالم\n"
        "✅ چالش‌های روزانه انگیزشی\n\n"
        "برای شروع، لطفاً شماره تماستون رو با ما به اشتراک بذارید 👇",
        reply_markup=reply_markup
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    # اگه از دکمه تلگرام شماره داد
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith('+'):
            phone = '+' + phone
        context.user_data['phone'] = phone
    # اگه دستی تایپ کرد
    elif update.message.text:
        context.user_data['phone'] = update.message.text
    else:
        phone_button = KeyboardButton(text="📱 اشتراک‌گذاری شماره تلفن", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("لطفاً شماره تماستون رو با دکمه زیر به اشتراک بذارید 📱", reply_markup=reply_markup)
        return PHONE

    await update.message.reply_text(
        "ممنون! 😊\n\nاسم و فامیل فرزندتون رو بنویسید 👤",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً اسم و فامیل فرزندتون رو تایپ کنید 👤")
        return NAME
    context.user_data['name'] = update.message.text
    await update.message.reply_text(f"{context.user_data['name']} چند سالشه؟ 🎂")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً سن رو تایپ کنید 🎂")
        return AGE
    context.user_data['age'] = update.message.text
    await update.message.reply_text(
        f"قد {context.user_data['name']} چقدره؟ 📏\nمثال: ۱۳۵ (سانتی‌متر)"
    )
    return HEIGHT

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً قد رو تایپ کنید 📏")
        return HEIGHT
    context.user_data['height'] = update.message.text
    await update.message.reply_text(
        f"وزن {context.user_data['name']} چقدره؟ ⚖️\nمثال: ۳۵ (کیلوگرم)"
    )
    return WEIGHT

async def get_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً وزن رو تایپ کنید ⚖️")
        return WEIGHT
    context.user_data['weight'] = update.message.text
    await update.message.reply_text(
        f"رشته ورزشی {context.user_data['name']} چیه؟ ⚽🥊🏊\n"
        "مثال: فوتبال، شنا، کاراته...\n"
        "(در صورت نداشتن رشته بنویسید: ندارد)"
    )
    return SPORT

async def get_sport(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً رشته ورزشی رو تایپ کنید ⚽")
        return SPORT
    context.user_data['sport'] = update.message.text
    await update.message.reply_text(
        f"{context.user_data['name']} چند روز در هفته تحرک جدی و ورزش داره؟ 🗓️\nمثال: ۳ روز"
    )
    return SESSIONS

async def get_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً تعداد روزها رو تایپ کنید 🗓️")
        return SESSIONS
    context.user_data['sessions'] = update.message.text
    await update.message.reply_text(
        f"هدف ورزشی {context.user_data['name']} چیه؟ 🎯\n"
        "مثال: قهرمانی، تناسب اندام، لذت از ورزش، حرفه‌ای شدن..."
    )
    return GOAL

async def get_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً هدف ورزشی رو تایپ کنید 🎯")
        return GOAL
    context.user_data['goal'] = update.message.text
    user_id = update.effective_user.id
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
            "phone": phone,
            "user_id": str(user_id),
            "child_name": name,
            "age": age,
            "height": height,
            "weight": weight,
            "sport": sport,
            "sessions": sessions,
            "goal": goal
        }
        requests.post(SHEET_URL, json=data, timeout=10)
    except Exception as e:
        logger.error(f"Sheet error: {e}")

    keyboard = [["👤 مشاهده پروفایل"]]
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

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    p = user_profiles.get(user_id)
    if not p:
        p = get_profile_from_sheet(str(user_id))
    if p:
        keyboard = [["👤 مشاهده پروفایل"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"🏅 پروفایل قهرمان کوچک\n"
            f"─────────────────\n"
            f"📱 شماره تماس: {p.get('phone', '-')}\n"
            f"👤 نام: {p.get('child_name', p.get('name', '-'))}\n"
            f"🎂 سن: {p.get('age', '-')} سال\n"
            f"📏 قد: {p.get('height', '-')} سانتی‌متر\n"
            f"⚖️ وزن: {p.get('weight', '-')} کیلوگرم\n"
            f"⚽ رشته ورزشی: {p.get('sport', '-')}\n"
            f"🗓️ روزهای ورزش: {p.get('sessions', '-')} در هفته\n"
            f"🎯 هدف: {p.get('goal', '-')}\n",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("هنوز پروفایلی نداری! /start بزن تا بسازیم 😊")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message and update.message.text:
        text = update.message.text
        if text == "👤 مشاهده پروفایل":
            await profile_command(update, context)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "لغو شد. هر وقت خواستی /start بزن! 😊",
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
            PHONE: [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT, get_phone),
            ],
            NAME: [MessageHandler(filters.ALL, get_name)],
            AGE: [MessageHandler(filters.ALL, get_age)],
            HEIGHT: [MessageHandler(filters.ALL, get_height)],
            WEIGHT: [MessageHandler(filters.ALL, get_weight)],
            SPORT: [MessageHandler(filters.ALL, get_sport)],
            SESSIONS: [MessageHandler(filters.ALL, get_sessions)],
            GOAL: [MessageHandler(filters.ALL, get_goal)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CommandHandler("start", start),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
