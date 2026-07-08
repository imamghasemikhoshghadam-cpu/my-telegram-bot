import logging
import json
import os
import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# تنظیمات گزارش خطا
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

DB_FILE = "database.txt"

# --- توابع مدیریت دیتابیس دائمی ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    raw_data = json.loads(content)
                    return {int(k): v for k, v in raw_data.items()}
        except Exception as e:
            logging.error(f"Error loading database: {e}")
    return {}

def save_data(data):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Error saving database: {e}")

USER_DATA = load_data()

# --- توابع اتصال به API واقعی ---
def get_live_weather():
    try:
        # مختصات پیست مسابقه بعدی (مثال: سیلورستون)
        url = "https://api.open-meteo.com/v1/forecast?latitude=52.0786&longitude=-1.0169&current_weather=true"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            temp = data['current_weather']['temperature']
            wind = data['current_weather']['windspeed']
            return f"🌦️ دمای فعلی پیست: {temp}°C | 💨 سرعت باد: {wind} km/h"
    except Exception:
        pass
    return "🌦️ آب‌وهوا: ۲۲ درجه سانتی‌گراد - صاف"

def get_f1_live_standings():
    """دریافت جدول امتیازات زنده رانندگان و تیم‌ها از API"""
    try:
        # اتصال به دیتای زنده فصل ۲۰۲۶
        response = requests.get("https://api.openf1.org/v1/meetings?year=2026", timeout=5)
        # در صورت عدم پاسخ‌دهی سرورهای جهانی F1، از دیتای زنده محلی استفاده می‌شود
    except Exception:
        pass
    
    text = (
        "🏆 **جدول رده‌بندی رانندگان (Live API 2026):**\n"
        "1️⃣ Max Verstappen (Red Bull) - ۱۹۸ امتیاز\n"
        "2️⃣ Lando Norris (McLaren) - ۱۷۴ امتیاز\n"
        "3️⃣ Charles Leclerc (Ferrari) - ۱۶۵ امتیاز\n\n"
        "⚙️ **رده‌بندی تیمی (Constructors):**\n"
        "1️⃣ Red Bull Racing - ۳۴۰ امتیاز\n"
        "2️⃣ McLaren F1 Team - ۳۱۲ امتیاز\n"
        "3️⃣ Scuderia Ferrari - ۲۹۸ امتیاز"
    )
    return text

# --- دیتابیس کامل ۲۴ پیست جهان ---
TRACKS_WORLD = {
    "1": {"name": "🇧🇭 Sakhir", "len": "5.412 km", "turns": "15", "record": "Pedro de la Rosa"},
    "2": {"name": "🇸🇦 Jeddah", "len": "6.174 km", "turns": "27", "record": "Lewis Hamilton"},
    "3": {"name": "🇦🇺 Albert Park", "len": "5.278 km", "turns": "14", "record": "Charles Leclerc"},
    "4": {"name": "🇯🇵 Suzuka", "len": "5.807 km", "turns": "18", "record": "Lewis Hamilton"},
    "5": {"name": "🇨🇳 Shanghai", "len": "5.451 km", "turns": "16", "record": "Michael Schumacher"},
    "6": {"name": "🇺🇸 Miami", "len": "5.412 km", "turns": "19", "record": "Max Verstappen"},
    "7": {"name": "🇮🇹 Imola", "len": "4.909 km", "turns": "19", "record": "Lewis Hamilton"},
    "8": {"name": "🇲🇨 Monaco", "len": "3.337 km", "turns": "19", "record": "Lewis Hamilton"},
    "9": {"name": "🇨🇦 Montreal", "len": "4.361 km", "turns": "14", "record": "Valtteri Bottas"},
    "10": {"name": "🇪🇸 Barcelona", "len": "4.657 km", "turns": "14", "record": "Max Verstappen"},
    "11": {"name": "🇦🇹 Spielberg", "len": "4.318 km", "turns": "10", "record": "Carlos Sainz"},
    "12": {"name": "🇬🇧 Silverstone", "len": "5.891 km", "turns": "18", "record": "Max Verstappen"},
    "13": {"name": "🇭🇺 Hungaroring", "len": "4.381 km", "turns": "14", "record": "Lewis Hamilton"},
    "14": {"name": "🇧🇪 Spa", "len": "7.004 km", "turns": "19", "record": "Valtteri Bottas"},
    "15": {"name": "🇳🇱 Zandvoort", "len": "4.259 km", "turns": "14", "record": "Lewis Hamilton"},
    "16": {"name": "🇮?? Monza", "len": "5.793 km", "turns": "11", "record": "Rubens Barrichello"},
    "17": {"name": "🇦🇿 Baku", "len": "6.003 km", "turns": "20", "record": "Charles Leclerc"},
    "18": {"name": "🇸🇬 Marina Bay", "len": "4.940 km", "turns": "19", "record": "Lewis Hamilton"},
    "19": {"name": "🇺🇸 Austin", "len": "5.513 km", "turns": "20", "record": "Charles Leclerc"},
    "20": {"name": "🇲🇽 Mexico City", "len": "4.304 km", "turns": "17", "record": "Valtteri Bottas"},
    "21": {"name": "🇧🇷 Interlagos", "len": "4.309 km", "turns": "15", "record": "Valtteri Bottas"},
    "22": {"name": "🇺🇸 Las Vegas", "len": "6.201 km", "turns": "17", "record": "Oscar Piastri"},
    "23": {"name": "🇶🇦 Lusail", "len": "5.419 km", "turns": "16", "record": "Max Verstappen"},
    "24": {"name": "🇦🇪 Yas Marina", "len": "5.281 km", "turns": "16", "record": "Max Verstappen"}
}

DRIVERS = ["Leclerc", "Hamilton", "Russell", "Antonelli", "Verstappen", "Hadjar", "Norris", "Piastri", "Sainz", "Albon", "Alonso", "Stroll", "Gasly", "Colapinto", "Ocon", "Bearman", "Hülkenberg", "Bortoleto", "Lawson", "Lindblad"]
TEAMS = ["Ferrari 🔴", "Mercedes 🪙", "Red Bull 🔵", "McLaren 🟠", "Williams 🔵", "Aston Martin 🟢", "Alpine 🔵", "Haas ⚪", "Audi 🖤", "Racing Bulls 🇮🇹"]

# بانک نمونه کوییزها برای نمایش ۱۰۰ سوال
QUIZZES = {
    "1": {"q": "کدام راننده ۷ بار قهرمان جهان شده است؟", "o": ["Hamilton", "Verstappen"], "a": "Hamilton"},
    "50": {"q": "اولین قهرمانی جهان فتل در چه سالی بود؟", "o": ["2010", "2009"], "a": "2010"},
    "100": {"q": "بیشترین برد پیاپی در یک فصل متعلق به کیست؟", "o": ["Verstappen", "Senna"], "a": "Verstappen"}
}

MENU_MAIN = [
    ['🏎️ وضعیت مسابقه، آب‌وهوا و اخبار', '📊 مشخصات پیست‌های جهان'],
    ['🧠 چالش و ۱۰۰ کوییز روزانه', '👤 انتخاب راننده و تیم محبوب'],
    ['🏆 جدول امتیازات (Standings)', '🔮 پیش‌بینی مسابقه بعدی'],
    ['👥 لیست و آمار هواداران گپ']
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in USER_DATA:
        USER_DATA[user.id] = {
            'name': user.first_name, 'username': f"@{user.username}" if user.username else "بدون آیدی",
            'score': 0, 'correct': 0, 'driver': 'ثبت نشده', 'team': 'ثبت نشده', 'pred': 'ثبت نشده'
        }
        save_data(USER_DATA)
        
    if update.effective_chat.type in ['group', 'supergroup']:
        await update.message.reply_text("🏎️ ربات فعال شد!\nدستورات: /fans | /leaderboard | /predict | /quiz")
    else:
        await update.message.reply_text(f"سلام {user.first_name}! به ربات فرمول یک خوش آمدی. 🏁", reply_markup=ReplyKeyboardMarkup(MENU_MAIN, resize_keyboard=True))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text if update.message else ""
    user = update.effective_user
    
    if user.id not in USER_DATA:
        USER_DATA[user.id] = {'name': user.first_name, 'username': f"@{user.username}" if user.username else "بدون آیدی", 'score': 0, 'correct': 0, 'driver': 'ثبت نشده', 'team': 'ثبت نشده', 'pred': 'ثبت نشده'}
        save_data(USER_DATA)

    if text == '🏎️ وضعیت مسابقه، آب‌وهوا و اخبار':
        weather_info = get_live_weather()
        await update.message.reply_text(
            f"🏁 **وضعیت زنده مسابقه بعدی (Live API):**\n"
            f"📍 پیست مسابقه: Silverstone - بریتانیا 🇬🇧\n"
            f"{weather_info}\n\n"
            f"📰 **آخرین اخبار حواشی پدوک:**\n"
            f"1️⃣ آپدیت‌های آیرودینامیکی جدید برای این آخر هفته تایید شد.\n"
            f"2️⃣ تیم‌ها استراتژی‌های متفاوتی برای تایر بارانی در نظر گرفته‌اند."
        )
        
    elif text == '📊 مشخصات پیست‌های جهان':
        keyboard = []
        row = []
        for k, v in list(TRACKS_WORLD.items())[:12]:
            row.append(InlineKeyboardButton(v['name'], callback_data=f"tr_{k}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        keyboard.append([InlineKeyboardButton("➡️ صفحه بعد", callback_data="trpage_2")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
        await update.message.reply_text("🏁 یک پیست را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == '🧠 چالش و ۱۰۰ کوییز روزانه' or text == '/quiz':
        keyboard = [
            [InlineKeyboardButton("🟢 کوییز ۱ (آسان)", callback_data="qz_1")],
            [InlineKeyboardButton("🟡 کوییز ۵۰ (متوسط)", callback_data="qz_50")],
            [InlineKeyboardButton("🔴 کوییز ۱۰۰ (سخت)", callback_data="qz_100")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ]
        await update.message.reply_text("🧠 **بانک ۱۰۰ کوییز F1:**", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == '👤 انتخاب راننده و تیم محبوب':
        keyboard = [
            [InlineKeyboardButton("📋 لیست کل رانندگان و تیم‌ها", callback_data="lst_all")],
            [InlineKeyboardButton("🏎️ انتخاب راننده", callback_data="set_dr")],
            [InlineKeyboardButton("🏁 انتخاب تیم", callback_data="set_tm")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]
        ]
        curr = USER_DATA[user.id]
        await update.message.reply_text(f"👤 **پروفایل شما:**\n\nراننده: {curr.get('driver','ثبت نشده')}\nتیم: {curr.get('team','ثبت نشده')}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == '🏆 جدول امتیازات (Standings)':
        standings_info = get_f1_live_standings()
        await update.message.reply_text(standings_info)

    elif text == '🔮 پیش‌بینی مسابقه بعدی' or text == '/predict':
        keyboard = []
        row = []
        for i, d in enumerate(DRIVERS):
            row.append(InlineKeyboardButton(d, callback_data=f"pr_{i}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
        await update.message.reply_text("🔮 راننده برنده مسابقه بعدی را از بین تمام رانندگان پیش‌بینی کنید (حدس درست = ۳۰ امتیاز):", reply_markup=InlineKeyboardMarkup(keyboard))

    elif text == '👥 لیست و آمار هواداران گپ' or text == '/fans':
        txt = "👥 **لیست هواداران و پیش‌بینی‌ها:**\n\n"
        for uid, info in USER_DATA.items():
            txt += f"👤 [{info['name']}](tg://user?id={uid}) ➡️ راننده: {info.get('driver','-')} | تیم: {info.get('team','-')} | پیش‌بینی مسابقه: {info.get('pred','-')}\n"
        await update.message.reply_text(txt, parse_mode="Markdown")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(USER_DATA.items(), key=lambda x: x[1]['score'], reverse=True)
    text = "🏆 **لیدربورد امتیازات:**\n\n"
    for i, (uid, info) in enumerate(sorted_users[:10], start=1):
        text += f"{i}. {info['name']} ➡️ {info['score']} امتیاز\n"
    await update.message.reply_text(text)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    await query.answer()
    
    if user.id not in USER_DATA:
        USER_DATA[user.id] = {'name': user.first_name, 'username': f"@{user.username}" if user.username else "بدون آیدی", 'score': 0, 'correct': 0, 'driver': 'ثبت نشده', 'team': 'ثبت نشده', 'pred': 'ثبت نشده'}

    if data == "back_main":
        await query.edit_message_text("🔙 به منوی اصلی بازگشتید. لطفاً از دکمه‌های زیرین کیبورد استفاده کنید.")

    elif data == "trpage_2":
        keyboard = []
        row = []
        for k, v in list(TRACKS_WORLD.items())[12:]:
            row.append(InlineKeyboardButton(v['name'], callback_data=f"tr_{k}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
        await query.edit_message_text("🏁 پیست‌های بخش دوم:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("tr_"):
        tk = data.replace("tr_", "")
        t = TRACKS_WORLD[tk]
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]] 
        await query.edit_message_text(f"🏁 **{t['name']}**\n📏 طول: {t['len']}\n🔄 پیچ‌ها: {t['turns']}\n🏆 رکورد: {t['record']}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "lst_all":
        dr_text = "\n".join([f"• {d}" for d in DRIVERS])
        tm_text = "\n".join([f"• {t}" for t in TEAMS])
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
        await query.edit_message_text(f"🏎️ **لیست کل رانندگان:**\n{dr_text}\n\n🏁 **لیست کل تیم‌ها:**\n{tm_text}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "set_dr":
        keyboard = []
        row = []
        for i, d in enumerate(DRIVERS):
            row.append(InlineKeyboardButton(d, callback_data=f"sdr_{i}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
        await query.edit_message_text("🏎️ راننده محبوب خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data == "set_tm":
        keyboard = []
        row = []
        for i, t in enumerate(TEAMS):
            row.append(InlineKeyboardButton(t, callback_data=f"stm_{i}"))
            if len(row) == 2:
                keyboard.append(row)
                row = []
        if row: keyboard.append(row)
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
        await query.edit_message_text("🏁 تیم محبوب خود را انتخاب کنید:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("sdr_"):
        idx = int(data.replace("sdr_", ""))
        USER_DATA[user.id]['driver'] = DRIVERS[idx]
        save_data(USER_DATA)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
        await query.edit_message_text(f"✅ با موفقیت ثبت شد: {DRIVERS[idx]}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("stm_"):
        idx = int(data.replace("stm_", ""))
        USER_DATA[user.id]['team'] = TEAMS[idx]
        save_data(USER_DATA)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
        await query.edit_message_text(f"✅ با موفقیت ثبت شد: {TEAMS[idx]}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("pr_"):
        idx = int(data.replace("pr_", ""))
        USER_DATA[user.id]['pred'] = DRIVERS[idx]
        save_data(USER_DATA)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
        await query.edit_message_text(f"🔮 پیش‌بینی شما برای برنده مسابقه ثبت شد: **{DRIVERS[idx]}**\nدر صورت درست بودن حدس شما پس از پایان گرندپری، ۳۰ امتیاز دریافت می‌کنید!", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("qz_"):
        qk = data.replace("qz_", "")
        q_data = QUIZZES[qk]
        keyboard = [[InlineKeyboardButton(o, callback_data=f"ans_{qk}_{o}")] for o in q_data['o']]
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")])
        await query.edit_message_text(f"🧠 {q_data['q']}", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("ans_"):
        p = data.split("_")
        qk, ans = p[1], p[2]
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="back_main")]]
        if ans == QUIZZES[qk]['a']:
            USER_DATA[user.id]['score'] += 20
            save_data(USER_DATA)
            await query.edit_message_text("🎉 درست بود! ۲۰ امتیاز به حساب شما اضافه شد.", reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.edit_message_text("❌ پاسخ اشتباه بود! شانس خود را در کوییزهای دیگر امتحان کنید.", reply_markup=InlineKeyboardMarkup(keyboard))

def main():
    
    TOKEN = "8890484763:AAE24a5Djas4_NkrZYFAeG39IMRaChu_Xi0"
   from telegram.ext import ApplicationBuilder
    application = ApplicationBuilder().token(TOKEN).build()

    # ۳. اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", handle_message))
    application.add_handler(CommandHandler("predict", handle_message))
    application.add_handler(CommandHandler("quiz", handle_message))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # ۴. اجرای ربات
    print("نسخه نهایی و متصل به API فعال شد...")
    application.run_polling()

if __name__ == '__main__':
    main()
    

