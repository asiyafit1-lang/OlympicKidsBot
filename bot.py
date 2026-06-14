import os
import logging
import requests
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    JobQueue,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

SHEET_URL = "https://script.google.com/macros/s/AKfycbxaGxiO4hWS66mEAmXiC14xrAvBA-gBtu21IJSQkkOdO_46LYu2n_8efUIn3gq31-iQPQ/exec"
GROQ_API_KEY = "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"

# مراحل ثبت‌نام
LICENSE, PHONE, NAME, AGE, HEIGHT, WEIGHT, SPORT, SESSIONS, GOAL = range(9)

# مراحل برنامه غذایی
ALLERGY, DISLIKED, NUTRITION_GOAL, MEALS, SUPPLEMENT, DIGESTION, FOOD_TYPE, DAIRY = range(9, 17)

# مراحل پیگیری روزانه
DAILY_SLEEP, DAILY_ACTIVITY, DAILY_FOOD, DAILY_SCORE = range(17, 21)

user_profiles = {}
nutrition_data = {}
daily_tracking = {}

def check_license(code: str, user_id: str) -> dict:
    try:
        response = requests.get(
            f"{SHEET_URL}?action=check_license&code={code}&user_id={user_id}",
            timeout=10
        )
        return response.json()
    except Exception as e:
        logger.error(f"License check error: {e}")
        return {"valid": False, "reason": "error"}

def get_profile_from_sheet(user_id: str) -> dict:
    try:
        response = requests.get(f"{SHEET_URL}?user_id={user_id}", timeout=10)
        data = response.json()
        if data.get("found"):
            return data.get("profile", {})
    except Exception as e:
        logger.error(f"Sheet read error: {e}")
    return {}

def get_nutrition_plan(profile: dict, nutrition: dict) -> str:
    try:
        prompt = f"""تو یک متخصص تغذیه کودک و نوجوان ورزشکار هستی با بیش از ۱۵ سال تجربه.
یک برنامه غذایی روزانه کامل، علمی و کاربردی برای این کودک ورزشکار طراحی کن:

اطلاعات جسمی:
- نام: {profile.get('child_name', 'نامشخص')}
- سن: {profile.get('age', 'نامشخص')} سال
- قد: {profile.get('height', 'نامشخص')} سانتی‌متر
- وزن: {profile.get('weight', 'نامشخص')} کیلوگرم
- رشته ورزشی: {profile.get('sport', 'نامشخص')}
- روزهای تمرین: {profile.get('sessions', 'نامشخص')} در هفته
- هدف ورزشی: {profile.get('goal', 'نامشخص')}

اطلاعات تغذیه‌ای:
- حساسیت غذایی: {nutrition.get('allergy', 'ندارد')}
- غذاهای ناپسند: {nutrition.get('disliked', 'ندارد')}
- هدف تغذیه‌ای: {nutrition.get('nutrition_goal', 'نامشخص')}
- تعداد وعده‌ها: {nutrition.get('meals', 'نامشخص')}
- مکمل‌ها: {nutrition.get('supplement', 'ندارد')}
- مشکل گوارشی: {nutrition.get('digestion', 'ندارد')}
- غذاهای مورد علاقه: {nutrition.get('food_type', 'نامشخص')}
- مصرف لبنیات: {nutrition.get('dairy', 'نامشخص')}

برنامه غذایی شامل:
🌅 صبحانه
🍎 میان‌وعده صبح
🍽️ ناهار
🍌 میان‌وعده بعدازظهر
🌙 شام

مواد غذایی ایرانی و در دسترس باشن. مقدار هر ماده رو ذکر کن. در آخر یه نکته تغذیه‌ای مهم بنویس."""

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500,
                "temperature": 0.7
            },
            timeout=30
        )
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"Groq error: {e}")
        return "متأسفانه مشکلی پیش آمد. دوباره تلاش کنید."

def save_daily_tracking(user_id: str, data: dict):
    try:
        payload = {
            "action": "daily_tracking",
            "user_id": user_id,
            "date": datetime.now().strftime("%Y-%m-%d"),
            **data
        }
        requests.post(SHEET_URL, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Daily tracking error: {e}")

# ===== ثبت‌نام =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "🏅 باشگاه کودک المپیکی\n\n"
        "سلام به خانواده عزیز 👋\n\n"
        "ما اینجاییم تا با کمک هوش مصنوعی، بهترین مسیر ورزشی رو برای فرزند شما طراحی کنیم.\n\n"
        "🎯 برنامه تمرینی اختصاصی\n"
        "🥗 تغذیه سالم و علمی\n"
        "💪 چالش‌های روزانه انگیزشی\n"
        "📊 پیگیری پیشرفت مستمر\n\n"
        "لطفاً کد اشتراک خود را وارد کنید 🔑",
        reply_markup=ReplyKeyboardRemove()
    )
    return LICENSE

async def get_license(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً کد اشتراک را وارد کنید 🔑")
        return LICENSE

    code = update.message.text.strip()
    user_id = str(update.effective_user.id)

    await update.message.reply_text("⏳ در حال بررسی کد اشتراک...")

    result = check_license(code, user_id)

    if result.get("valid"):
        context.user_data['license'] = code
        phone_button = KeyboardButton(text="📱 اشتراک‌گذاری شماره تلفن", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text(
            f"✅ کد اشتراک تأیید شد!\n\n"
            f"خوش اومدی به باشگاه کودک المپیکی 🏅\n\n"
            f"بریم پروفایل فرزندتون رو بسازیم 💪\n\n"
            f"شماره تماستون رو با ما به اشتراک بذارید 👇",
            reply_markup=reply_markup
        )
        return PHONE
    else:
        reason = result.get("reason", "")
        if reason == "expired":
            msg = "❌ کد اشتراک شما منقضی شده!\n\nبرای تمدید با مربی تماس بگیرید."
        elif reason == "inactive":
            msg = "❌ کد اشتراک غیرفعال است!\n\nبرای فعال‌سازی با مربی تماس بگیرید."
        else:
            msg = "❌ کد اشتراک نامعتبر است!\n\nلطفاً کد را بررسی کنید یا با مربی تماس بگیرید."

        await update.message.reply_text(msg)
        return LICENSE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith('+'): phone = '+' + phone
        context.user_data['phone'] = phone
    elif update.message.text:
        context.user_data['phone'] = update.message.text
    else:
        phone_button = KeyboardButton(text="📱 اشتراک‌گذاری شماره تلفن", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("لطفاً شماره تماستون رو با دکمه زیر به اشتراک بذارید 📱", reply_markup=reply_markup)
        return PHONE
    await update.message.reply_text("ممنون! 😊\n\nاسم و فامیل فرزندتون رو بنویسید 👤", reply_markup=ReplyKeyboardRemove())
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
    await update.message.reply_text(f"قد {context.user_data['name']} چقدره؟ 📏\nمثال: ۱۳۵ (سانتی‌متر)")
    return HEIGHT

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً قد رو تایپ کنید 📏")
        return HEIGHT
    context.user_data['height'] = update.message.text
    await update.message.reply_text(f"وزن {context.user_data['name']} چقدره؟ ⚖️\nمثال: ۳۵ (کیلوگرم)")
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
    await update.message.reply_text(f"{context.user_data['name']} چند روز در هفته تحرک جدی و ورزش داره؟ 🗓️\nمثال: ۳ روز")
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

    keyboard = [
        ["👤 مشاهده پروفایل", "🥗 برنامه غذایی"],
        ["📊 پیگیری روزانه"]
    ]
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

# ===== برنامه غذایی =====
async def nutrition_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    p = user_profiles.get(user_id) or get_profile_from_sheet(str(user_id))
    if not p:
        await update.message.reply_text("اول باید پروفایل بسازی! /start بزن 😊")
        return ConversationHandler.END
    nutrition_data[user_id] = {}
    await update.message.reply_text(
        "🥗 برنامه غذایی اختصاصی\n\n"
        "چند سوال کوتاه میپرسم تا بهترین برنامه رو برات طراحی کنم 😊\n\n"
        "سوال ۱/۸:\n"
        "آیا فرزندتون حساسیت یا آلرژی غذایی داره؟ 🌾\n"
        "مثال: لاکتوز، گلوتن، آجیل...\n"
        "(اگه ندارد بنویسید: ندارد)",
        reply_markup=ReplyKeyboardRemove()
    )
    return ALLERGY

async def get_allergy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً جواب رو تایپ کنید 🌾")
        return ALLERGY
    nutrition_data[update.effective_user.id]['allergy'] = update.message.text
    await update.message.reply_text(
        "سوال ۲/۸:\n"
        "چه غذاهایی رو اصلاً نمیخوره؟ 🙅\n"
        "مثال: جگر، کلم، ماهی...\n"
        "(اگه همه چیز میخوره بنویسید: ندارد)"
    )
    return DISLIKED

async def get_disliked(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً جواب رو تایپ کنید 🙅")
        return DISLIKED
    nutrition_data[update.effective_user.id]['disliked'] = update.message.text
    keyboard = [["افزایش وزن"], ["کاهش وزن"], ["تناسب اندام"]]
    await update.message.reply_text(
        "سوال ۳/۸:\nهدف تغذیه‌ای فرزندتون چیه؟ 🎯",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return NUTRITION_GOAL

async def get_nutrition_goal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً هدف رو انتخاب کنید 🎯")
        return NUTRITION_GOAL
    nutrition_data[update.effective_user.id]['nutrition_goal'] = update.message.text
    keyboard = [["۳ وعده"], ["۴ وعده"], ["۵ وعده"]]
    await update.message.reply_text(
        "سوال ۴/۸:\nروزانه چند وعده غذایی میخوره؟ 🍽️",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return MEALS

async def get_meals(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً تعداد وعده‌ها رو انتخاب کنید 🍽️")
        return MEALS
    nutrition_data[update.effective_user.id]['meals'] = update.message.text
    await update.message.reply_text(
        "سوال ۵/۸:\n"
        "آیا مکمل یا ویتامین مصرف میکنه؟ 💊\n"
        "مثال: ویتامین D، امگا ۳...\n"
        "(اگه نه بنویسید: ندارد)",
        reply_markup=ReplyKeyboardRemove()
    )
    return SUPPLEMENT

async def get_supplement(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً جواب رو تایپ کنید 💊")
        return SUPPLEMENT
    nutrition_data[update.effective_user.id]['supplement'] = update.message.text
    await update.message.reply_text(
        "سوال ۶/۸:\n"
        "آیا مشکل گوارشی داره؟ 🫀\n"
        "مثال: یبوست، نفخ، رفلاکس...\n"
        "(اگه ندارد بنویسید: ندارد)"
    )
    return DIGESTION

async def get_digestion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً جواب رو تایپ کنید 🫀")
        return DIGESTION
    nutrition_data[update.effective_user.id]['digestion'] = update.message.text
    keyboard = [["گوشت قرمز"], ["مرغ"], ["ماهی"], ["سبزیجات"], ["همه چیز"]]
    await update.message.reply_text(
        "سوال ۷/۸:\nبیشتر چه نوع غذایی دوست داره؟ 🍗",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return FOOD_TYPE

async def get_food_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً نوع غذا رو انتخاب کنید 🍗")
        return FOOD_TYPE
    nutrition_data[update.effective_user.id]['food_type'] = update.message.text
    keyboard = [["بله"], ["خیر"], ["کم مصرف میکنه"]]
    await update.message.reply_text(
        "سوال ۸/۸:\nآیا لبنیات (شیر، ماست، پنیر) مصرف میکنه؟ 🥛",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return DAIRY

async def get_dairy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً جواب رو انتخاب کنید 🥛")
        return DAIRY
    user_id = update.effective_user.id
    nutrition_data[user_id]['dairy'] = update.message.text

    await update.message.reply_text(
        "✅ اطلاعات دریافت شد!\n\n"
        "🥗 در حال طراحی برنامه غذایی اختصاصی...\n"
        "چند ثانیه صبر کن ⏳",
        reply_markup=ReplyKeyboardRemove()
    )

    p = user_profiles.get(user_id) or get_profile_from_sheet(str(user_id))
    plan = get_nutrition_plan(p, nutrition_data[user_id])

    keyboard = [
        ["👤 مشاهده پروفایل", "🥗 برنامه غذایی"],
        ["📊 پیگیری روزانه"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        f"🥗 برنامه غذایی اختصاصی {p.get('child_name', '')}:\n\n{plan}",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ===== پیگیری روزانه =====
async def daily_tracking_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    p = user_profiles.get(user_id) or get_profile_from_sheet(str(user_id))
    if not p:
        await update.message.reply_text("اول باید پروفایل بسازی! /start بزن 😊")
        return ConversationHandler.END

    daily_tracking[user_id] = {}
    keyboard = [["۶-۷ ساعت"], ["۷-۸ ساعت"], ["۸-۹ ساعت"], ["بیشتر از ۹ ساعت"]]
    await update.message.reply_text(
        "📊 پیگیری روزانه\n\n"
        f"سلام! بریم امروز {p.get('child_name', '')} رو بررسی کنیم 😊\n\n"
        "سوال ۱/۴:\n"
        "دیشب چقدر خوابید؟ 😴",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return DAILY_SLEEP

async def get_daily_sleep(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً میزان خواب رو انتخاب کنید 😴")
        return DAILY_SLEEP
    daily_tracking[update.effective_user.id]['sleep'] = update.message.text
    keyboard = [["خیلی کم"], ["کم"], ["متوسط"], ["زیاد"], ["خیلی زیاد"]]
    await update.message.reply_text(
        "سوال ۲/۴:\n"
        "امروز چقدر فعالیت بدنی داشت؟ 🏃",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return DAILY_ACTIVITY

async def get_daily_activity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً میزان فعالیت رو انتخاب کنید 🏃")
        return DAILY_ACTIVITY
    daily_tracking[update.effective_user.id]['activity'] = update.message.text
    keyboard = [["خیلی بد"], ["بد"], ["متوسط"], ["خوب"], ["خیلی خوب"]]
    await update.message.reply_text(
        "سوال ۳/۴:\n"
        "تغذیه امروزش چطور بود؟ 🥗",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    )
    return DAILY_FOOD

async def get_daily_food(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً وضعیت تغذیه رو انتخاب کنید 🥗")
        return DAILY_FOOD
    daily_tracking[update.effective_user.id]['food'] = update.message.text
    keyboard = [["۱"], ["۲"], ["۳"], ["۴"], ["۵"], ["۶"], ["۷"], ["۸"], ["۹"], ["۱۰"]]
    await update.message.reply_text(
        "سوال ۴/۴:\n"
        "از ۱ تا ۱۰ چه نمره‌ای به امروزش میدی؟ ⭐",
        reply_markup=ReplyKeyboardMarkup(
            [["۱", "۲", "۳", "۴", "۵"],
             ["۶", "۷", "۸", "۹", "۱۰"]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )
    return DAILY_SCORE

async def get_daily_score(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not update.message or not update.message.text:
        await update.message.reply_text("لطفاً نمره رو انتخاب کنید ⭐")
        return DAILY_SCORE
    user_id = update.effective_user.id
    daily_tracking[user_id]['score'] = update.message.text

    save_daily_tracking(str(user_id), daily_tracking[user_id])

    sleep = daily_tracking[user_id].get('sleep', '-')
    activity = daily_tracking[user_id].get('activity', '-')
    food = daily_tracking[user_id].get('food', '-')
    score = daily_tracking[user_id].get('score', '-')

    keyboard = [
        ["👤 مشاهده پروفایل", "🥗 برنامه غذایی"],
        ["📊 پیگیری روزانه"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        f"✅ پیگیری امروز ثبت شد!\n\n"
        f"📊 خلاصه امروز:\n"
        f"─────────────────\n"
        f"😴 خواب: {sleep}\n"
        f"🏃 فعالیت: {activity}\n"
        f"🥗 تغذیه: {food}\n"
        f"⭐ نمره: {score} از ۱۰\n"
        f"─────────────────\n\n"
        f"آفرین! هر روز بهتر از دیروز 💪",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ===== پیام یادآور شبانه =====
async def send_daily_reminder(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    user_id = job.data
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text="🌙 سلام!\n\nوقت پیگیری روزانه فرزندتونه 😊\n\nدکمه 📊 پیگیری روزانه رو بزنید."
        )
    except Exception as e:
        logger.error(f"Reminder error: {e}")

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    p = user_profiles.get(user_id) or get_profile_from_sheet(str(user_id))
    if p:
        keyboard = [
            ["👤 مشاهده پروفایل", "🥗 برنامه غذایی"],
            ["📊 پیگیری روزانه"]
        ]
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
    await update.message.reply_text("لغو شد. هر وقت خواستی /start بزن! 😊", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main() -> None:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN environment variable is not set.")

    app = Application.builder().token(token).build()

    # مکالمه ثبت‌نام
    register_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LICENSE: [MessageHandler(filters.TEXT, get_license)],
            PHONE: [MessageHandler(filters.CONTACT, get_phone), MessageHandler(filters.TEXT, get_phone)],
            NAME: [MessageHandler(filters.ALL, get_name)],
            AGE: [MessageHandler(filters.ALL, get_age)],
            HEIGHT: [MessageHandler(filters.ALL, get_height)],
            WEIGHT: [MessageHandler(filters.ALL, get_weight)],
            SPORT: [MessageHandler(filters.ALL, get_sport)],
            SESSIONS: [MessageHandler(filters.ALL, get_sessions)],
            GOAL: [MessageHandler(filters.ALL, get_goal)],
        },
        fallbacks=[CommandHandler("cancel", cancel), CommandHandler("start", start)],
        allow_reentry=True,
    )

    # مکالمه برنامه غذایی
    nutrition_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🥗 برنامه غذایی$"), nutrition_start)],
        states={
            ALLERGY: [MessageHandler(filters.ALL, get_allergy)],
            DISLIKED: [MessageHandler(filters.ALL, get_disliked)],
            NUTRITION_GOAL: [MessageHandler(filters.ALL, get_nutrition_goal)],
            MEALS: [MessageHandler(filters.ALL, get_meals)],
            SUPPLEMENT: [MessageHandler(filters.ALL, get_supplement)],
            DIGESTION: [MessageHandler(filters.ALL, get_digestion)],
            FOOD_TYPE: [MessageHandler(filters.ALL, get_food_type)],
            DAIRY: [MessageHandler(filters.ALL, get_dairy)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    # مکالمه پیگیری روزانه
    daily_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^📊 پیگیری روزانه$"), daily_tracking_start)],
        states={
            DAILY_SLEEP: [MessageHandler(filters.ALL, get_daily_sleep)],
            DAILY_ACTIVITY: [MessageHandler(filters.ALL, get_daily_activity)],
            DAILY_FOOD: [MessageHandler(filters.ALL, get_daily_food)],
            DAILY_SCORE: [MessageHandler(filters.ALL, get_daily_score)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(register_handler)
    app.add_handler(nutrition_handler)
    app.add_handler(daily_handler)
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot is running.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
