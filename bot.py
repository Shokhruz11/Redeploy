import telebot
from telebot import types
import sqlite3
import os

# AI kutubxona (Google Gemini)
try:
    import google.generativeai as genai
except ImportError:
    genai = None

# =========================
#   SOZLAMALAR
# =========================

BOT_TOKEN = "8086850400:AAHUpWbBtn9Bl_PMQgYOlf5OlmC-NBB2z30"  # @BotFather dan olingan tokenni shu yerga yozing
ADMIN_ID = 5754599655          # O'zingizning Telegram ID'ingizni qo'ying

CARD_NUMBER = "4790920018585070"
CARD_OWNER = "Qo'chqorov Shohruz"

DB_NAME = "talaba_bot.db"

bot = telebot.TeleBot(BOT_TOKEN)

# =========================
#   DATABASE (SQLite)
# =========================

def init_db():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            orders_count INTEGER DEFAULT 0
        )
        """
    )
    conn.commit()
    return conn


conn = init_db()


def register_order(user_id: int):
    """
    Foydalanuvchi buyurtma berganda chaqiriladi.
    1-buyurtma bepul, keyingilari pullik.
    return: (is_free: bool, total_orders: int)
    """
    cur = conn.cursor()
    cur.execute("SELECT orders_count FROM users WHERE user_id = ?", (user_id,))
    row = cur.fetchone()

    if row is None:
        # Birinchi buyurtma
        cur.execute(
            "INSERT INTO users (user_id, orders_count) VALUES (?, ?)",
            (user_id, 1),
        )
        conn.commit()
        return True, 1
    else:
        count = row[0] + 1
        cur.execute(
            "UPDATE users SET orders_count = ? WHERE user_id = ?",
            (count, user_id),
        )
        conn.commit()
        return False, count


# =========================
#   AI (Gemini) SOZLAMALARI
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if genai and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print("Gemini modelini yaratishda xato:", e)
        gemini_model = None
else:
    gemini_model = None


def generate_ai_content(kind: str, topic: str, amount: str) -> str:
    """
    AI orqali matn generatsiya qilish.
    kind: 'slayd', 'referat', 'mustaqil', 'esse', 'test'
    topic: mavzu
    amount: son (slayd, bet, test savol soni)
    """
    if not gemini_model:
        return (
            "⚠️ AI xizmati hozir sozlanmagan.\n"
            "Admin GEMINI_API_KEY ni o'rnatishi kerak. Hozircha buyurtma qo'lda bajariladi."
        )

    try:
        if kind == "slayd":
            prompt = (
                f"Mavzu: {topic}\n"
                f"{amount} ta slayd uchun prezentatsiya kontenti tuz.\n"
                "Har bir slayd uchun:\n"
                "- Slayd sarlavhasi\n"
                "- 3–5 ta bullet-point\n\n"
                "Natijani quyidagi formatda yoz:\n"
                "1-slayd: ...\n"
                "- ...\n"
                "- ...\n"
                "2-slayd: ... va hokazo.\n"
                "Til: o'zbek tilida, talaba uchun sodda va tushunarli."
            )
        elif kind in ("referat", "mustaqil"):
            prompt = (
                f"Mavzu: {topic}\n"
                f"Talaba uchun {kind} ish matnini yoz.\n"
                f"Taxminan {amount} betga mos hajmda yoz, lekin real bet sonini o'zing hisoblamaysan.\n"
                "Tuzilishi: Kirish, 2–3 ta asosiy bob, xulosa.\n"
                "Akademik, sodda, plagiatsiz, o'zbek tilida yoz."
            )
        elif kind == "esse":
            prompt = (
                f"Mavzu: {topic}\n"
                "Talaba uchun insho/esse matnini yoz.\n"
                f"Taxminan {amount} bet hajmda, lekin betni o'zing hisoblamaysan.\n"
                "Til: o'zbekcha, emotsional, lekin adabiy va savodli, xulosa bilan yakunla."
            )
        elif kind == "test":
            prompt = (
                f"Mavzu: {topic}\n"
                f"{amount} ta test savol tuz.\n"
                "Har bir savol uchun 4 ta variant (A, B, C, D) bo'lsin, faqat bitta to'g'ri javob.\n"
                "Natijani quyidagi formatda chiqargin:\n"
                "1) Savol ...\n"
                "A) ...\nB) ...\nC) ...\nD) ...\n"
                "Javob: C\n\n"
                "2) Savol ... va hokazo.\n"
                "Til: o'zbek tilida."
            )
        else:
            prompt = f"Mavzu: {topic}\nBu mavzu bo'yicha o'quv matni tayyorla."

        resp = gemini_model.generate_content(prompt)
        text = resp.text or "AI javobi bo'sh qaytdi."
        return text

    except Exception as e:
        print("AI xatolik:", e)
        return (
            "⚠️ AI orqali matn generatsiya qilishda xato yuz berdi.\n"
            "Buyurtma ma'lumotlari adminga yuborildi, qo'lda bajariladi."
        )


# =========================
#   YORDAMCHI FUNKSIYALAR
# =========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🧾 Slayd")
    btn2 = types.KeyboardButton("📚 Referat")
    btn3 = types.KeyboardButton("📝 Mustaqil ish")
    btn4 = types.KeyboardButton("📄 Esse / Insho")
    btn5 = types.KeyboardButton("🧪 Test")
    btn6 = types.KeyboardButton("📘 Kurs ishi")
    btn7 = types.KeyboardButton("👨‍💻 Professional jamoa")
    btn8 = types.KeyboardButton("ℹ️ Yordam")
    markup.row(btn1, btn2)
    markup.row(btn3, btn4)
    markup.row(btn5)
    markup.row(btn6, btn7)
    markup.row(btn8)
    return markup


def slayd_design_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    d1 = types.KeyboardButton("🎨 1-dizayn (Oddiy)")
    d2 = types.KeyboardButton("🌈 2-dizayn (Rangli)")
    d3 = types.KeyboardButton("📐 3-dizayn (Minimal)")
    d4 = types.KeyboardButton("📊 4-dizayn (Grafikli)")
    d5 = types.KeyboardButton("💼 5-dizayn (Biznes)")
    d6 = types.KeyboardButton("⭐ 6-dizayn (Premium)")
    back = types.KeyboardButton("◀️ Ortga")
    markup.row(d1, d2)
    markup.row(d3, d4)
    markup.row(d5, d6)
    markup.row(back)
    return markup


def price_text(is_free: bool) -> str:
    if is_free:
        return (
            "🎁 *Birinchi buyurtmangiz bepul!* (20 bet/slaydgacha)\n"
            "Keyingi buyurtmalarda 5000 so'mdan hisoblanadi."
        )
    else:
        return (
            "💰 *Xizmat haqqi:* 5000 so'm (20 bet/slaydgacha).\n"
            f"To'lov uchun karta: `{CARD_NUMBER}`\n"
            f"Ega: *{CARD_OWNER}*\n\n"
            "To'lovni amalga oshirgach, chekni rasm qilib yuboring va */chek* buyrug'ini bosing."
        )


# =========================
#   /start
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "Assalomu alaykum! 👋\n\n"
        "Ushbu bot orqali quyidagi topshiriqlarni *AI avtomatik* bajaradi:\n\n"
        "🧾 Slayd (PPTX uchun kontent)\n"
        "📚 Referat (DOC uchun matn)\n"
        "📝 Mustaqil ish (DOC uchun matn)\n"
        "📄 Esse / Insho (DOC uchun matn)\n"
        "🧪 Test savollar\n\n"
        "📘 Kurs ishi va diplom ishi esa faqat admin bilan kelishiladi.\n\n"
        "❕ *Tariflar:*\n"
        "• 1-buyurtma – *TEKIN* (20 bet/slaydgacha)\n"
        "• 2-buyurtmadan boshlab – 5000 so'm (20 bet/slaydgacha)\n\n"
        "Kerakli xizmat turini pastdagi menyudan tanlang 👇"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())


# =========================
#   YORDAM / INFO
# =========================

@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_handler(message):
    text = (
        "ℹ️ *Yordam bo‘limi*\n\n"
        "✅ Xizmatlar:\n"
        "• Slayd, referat, mustaqil ish, esse/insho, test – barchasini AI generatsiya qiladi.\n"
        "• Kurs ishi va diplom ishi – faqat admin bilan kelishiladi.\n\n"
        "💳 *To‘lov ma’lumotlari:*\n"
        f"Karta: `{CARD_NUMBER}`\n"
        f"Ega: *{CARD_OWNER}*\n\n"
        "🎁 *Tariflar:*\n"
        "• 1-buyurtma – bepul (20 bet/slaydgacha)\n"
        "• Keyingi buyurtmalar – 5000 so'm (20 bet/slaydgacha)\n\n"
        "👨‍💻 *Kurs ishi va diplom ishi admini:*\n"
        "@Shokhruz11\n\n"
        "🤖 *Chat bot va tezkor aloqa:*\n"
        "@Talabalar_xizmati\n\n"
        "🧾 *To‘lov chekini yuborish:*\n"
        "Chekni rasm qilib yuboring va */chek* buyrug'ini bosing – admin tekshiradi.\n\n"
        "📌 AI fayl yaratmaydi, lekin tayyor matn va reja beradi. Siz uni Word/PPTga ko'chirib ishlatasiz."
    )
    bot.send_message(
        message.chat.id,
        text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# =========================
#   /chek - to'lov cheki
# =========================

@bot.message_handler(commands=['chek'])
def chek_start(message):
    text = (
        "🧾 *Chek yuborish bo‘limi*\n\n"
        "Iltimos, hozir *to‘lov chekini rasm yoki fayl* ko‘rinishida yuboring.\n"
        "Chek yuborilgach, biz uni ko‘rib chiqamiz va buyurtmangizni tasdiqlaymiz."
    )
    msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, receive_chek)


def receive_chek(message):
    bot.send_message(
        message.chat.id,
        "✅ Chekingiz qabul qilindi. Tez orada admin tekshiradi. Rahmat!",
        reply_markup=main_menu()
    )
    try:
        if ADMIN_ID != 111111111:
            bot.forward_message(ADMIN_ID, message.chat.id, message.message_id)
    except Exception as e:
        print("Chekni admin'ga yuborishda xato:", e)


# =========================
#   KURS ISHI / PROFESSIONAL JAMOA
# =========================

@bot.message_handler(func=lambda m: m.text == "📘 Kurs ishi")
def kurs_ishi_handler(message):
    text = (
        "📘 *Kurs ishi / Diplom ishi bo‘yicha buyurtmalar* 🔝\n\n"
        "Bu turdagi yirik ilmiy ishlar *faqat admin bilan kelishiladi*.\n\n"
        "👉 Admin: @Shokhruz11\n\n"
        "Yozayotganda quyidagilarni yuboring:\n"
        "• Yo‘nalishingiz\n"
        "• Mavzu\n"
        "• Bet soni\n"
        "• Muddat\n"
        "• Qo‘shimcha talablar"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "👨‍💻 Professional jamoa")
def team_handler(message):
    text = (
        "👨‍💻 *Professional jamoa yordam bo‘limi* 💼\n\n"
        "Kurs ishi, diplom ishi, katta ilmiy loyihalar va murakkab topshiriqlar "
        "faqat admin orqali kelishiladi.\n\n"
        "👉 Admin: @Shokhruz11\n"
        "📩 Yozing, hammasi tez va sifatli bajariladi!"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())


# =========================
#   SLAYD XIZMATI
# =========================

@bot.message_handler(func=lambda m: m.text == "🧾 Slayd")
def slayd_start(message):
    text = (
        "🧾 *Slayd xizmati*\n\n"
        "Quyidagi 6 ta dizayndan birini tanlang:\n"
        "🎨 1-dizayn (Oddiy)\n"
        "🌈 2-dizayn (Rangli)\n"
        "📐 3-dizayn (Minimal)\n"
        "📊 4-dizayn (Grafikli)\n"
        "💼 5-dizayn (Biznes)\n"
        "⭐ 6-dizayn (Premium)\n\n"
        "Kerakli dizaynni pastdan tanlang 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=slayd_design_menu())


@bot.message_handler(func=lambda m: m.text in [
    "🎨 1-dizayn (Oddiy)",
    "🌈 2-dizayn (Rangli)",
    "📐 3-dizayn (Minimal)",
    "📊 4-dizayn (Grafikli)",
    "💼 5-dizayn (Biznes)",
    "⭐ 6-dizayn (Premium)"
])
def slayd_design_chosen(message):
    design = message.text
    text = (
        f"{design} tanlandi ✅\n\n"
        "Endi slayd mavzusini yozib yuboring.\n\n"
        "Masalan:\n"
        "\"Oila psixologiyasida nizolarni bartaraf etish usullari\""
    )
    bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(message, slayd_ask_pages, design)


def slayd_ask_pages(message, design):
    topic = message.text.strip()

    if len(topic) < 5:
        bot.send_message(message.chat.id, "Mavzu juda qisqa, iltimos, biroz batafsilroq yozing.")
        return bot.register_next_step_handler(message, slayd_ask_pages, design)

    msg = bot.send_message(
        message.chat.id,
        "Necha ta slayd kerak?\n\n"
        "Masalan: 10 ta slayd."
    )
    bot.register_next_step_handler(msg, slayd_finish_order, design, topic)


def slayd_finish_order(message, design, topic):
    slides = message.text.strip()

    is_free, total_orders = register_order(message.from_user.id)
    tariff_info = price_text(is_free)

    # AI slayd kontenti
    ai_text = generate_ai_content("slayd", topic, slides)

    confirm_text = (
        "✅ Slayd bo‘yicha buyurtmangiz qabul qilindi!\n\n"
        f"Dizayn: {design}\n"
        f"Mavzu: {topic}\n"
        f"Slaydlar soni: {slides}\n\n"
        f"{tariff_info}\n\n"
        "📌 Quyida slaydlar uchun AI tomonidan tayyorlangan kontent beriladi.\n"
        "Uni PowerPoint (PPTX) ga ko‘chirib ishlatishingiz mumkin."
    )
    bot.send_message(message.chat.id, confirm_text, parse_mode="Markdown", reply_markup=main_menu())
    bot.send_message(message.chat.id, ai_text)

    # Admin'ga yuborish
    try:
        if ADMIN_ID != 111111111:
            status = "BEPUL (1-buyurtma)" if is_free else "PULLIK (5000 so'm)"
            admin_text = (
                "📥 *Yangi slayd buyurtmasi!*\n\n"
                f"Foydalanuvchi: {message.from_user.first_name} (@{message.from_user.username})\n"
                f"User ID: `{message.from_user.id}`\n"
                f"Buyurtmalar soni: {total_orders}\n"
                f"Tarif statusi: *{status}*\n\n"
                f"Dizayn: {design}\n"
                f"Mavzu: {topic}\n"
                f"Slaydlar soni: {slides}"
            )
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print("Slayd buyurtmasini admin'ga yuborishda xato:", e)


# =========================
#   REFERAT / MUSTAQIL ISH / ESSE
# =========================

@bot.message_handler(func=lambda m: m.text in ["📚 Referat", "📝 Mustaqil ish", "📄 Esse / Insho"])
def text_services_handler(message):
    service = message.text
    bot.send_message(
        message.chat.id,
        f"{service} xizmati tanlandi ✅\n\n"
        "Iltimos, ish mavzusini yozib yuboring."
    )
    bot.register_next_step_handler(message, text_service_topic, service)


def text_service_topic(message, service):
    topic = message.text.strip()
    if len(topic) < 5:
        bot.send_message(message.chat.id, "Mavzu juda qisqa, iltimos, biroz batafsil yozing.")
        return bot.register_next_step_handler(message, text_service_topic, service)

    msg = bot.send_message(
        message.chat.id,
        "Necha bet bo‘lishi kerak?\n\n"
        "Masalan: 8 bet yoki 12 bet."
    )
    bot.register_next_step_handler(msg, text_service_finish, service, topic)


def text_service_finish(message, service, topic):
    pages = message.text.strip()

    is_free, total_orders = register_order(message.from_user.id)
    tariff_info = price_text(is_free)

    # Qaysi tur?
    kind = "referat"
    if service == "📝 Mustaqil ish":
        kind = "mustaqil"
    elif service == "📄 Esse / Insho":
        kind = "esse"

    ai_text = generate_ai_content(kind, topic, pages)

    confirm_text = (
        "✅ Buyurtmangiz qabul qilindi!\n\n"
        f"Xizmat: {service}\n"
        f"Mavzu: {topic}\n"
        f"Bet soni: {pages}\n\n"
        f"{tariff_info}\n\n"
        "📌 Quyida AI tomonidan tayyorlangan matn beriladi.\n"
        "Uni Word (DOC/DOCX) hujjatiga ko‘chirib ishlatishingiz mumkin."
    )
    bot.send_message(message.chat.id, confirm_text, parse_mode="Markdown", reply_markup=main_menu())
    bot.send_message(message.chat.id, ai_text)

    try:
        if ADMIN_ID != 111111111:
            status = "BEPUL (1-buyurtma)" if is_free else "PULLIK (5000 so'm)"
            admin_text = (
                "📥 *Yangi matnli ish buyurtmasi!*\n\n"
                f"Foydalanuvchi: {message.from_user.first_name} (@{message.from_user.username})\n"
                f"User ID: `{message.from_user.id}`\n"
                f"Buyurtmalar soni: {total_orders}\n"
                f"Tarif statusi: *{status}*\n\n"
                f"Xizmat: {service}\n"
                f"Mavzu: {topic}\n"
                f"Bet soni: {pages}"
            )
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print("Matnli ish buyurtmasini admin'ga yuborishda xato:", e)


# =========================
#   TEST XIZMATI
# =========================

@bot.message_handler(func=lambda m: m.text == "🧪 Test")
def test_start(message):
    bot.send_message(
        message.chat.id,
        "🧪 *Test tuzish xizmati*\n\n"
        "Iltimos, test mavzusini yozing.",
        parse_mode="Markdown"
    )
    bot.register_next_step_handler(message, test_ask_count)


def test_ask_count(message):
    topic = message.text.strip()
    if len(topic) < 5:
        bot.send_message(message.chat.id, "Mavzu juda qisqa, iltimos, biroz batafsil yozing.")
        return bot.register_next_step_handler(message, test_ask_count)

    msg = bot.send_message(
        message.chat.id,
        "Necha ta test savol kerak?\n\n"
        "Masalan: 20 ta savol."
    )
    bot.register_next_step_handler(msg, test_finish, topic)


def test_finish(message, topic):
    count = message.text.strip()

    is_free, total_orders = register_order(message.from_user.id)
    tariff_info = price_text(is_free)

    ai_text = generate_ai_content("test", topic, count)

    confirm_text = (
        "✅ Test bo‘yicha buyurtmangiz qabul qilindi!\n\n"
        f"Mavzu: {topic}\n"
        f"Savollar soni: {count}\n\n"
        f"{tariff_info}\n\n"
        "📌 Quyida AI tomonidan tuzilgan test savollari beriladi.\n"
        "Ularni Word yoki boshqa faylga ko‘chirib ishlatishingiz mumkin."
    )
    bot.send_message(message.chat.id, confirm_text, parse_mode="Markdown", reply_markup=main_menu())
    bot.send_message(message.chat.id, ai_text)

    try:
        if ADMIN_ID != 111111111:
            status = "BEPUL (1-buyurtma)" if is_free else "PULLIK (5000 so'm)"
            admin_text = (
                "📥 *Yangi test buyurtmasi!*\n\n"
                f"Foydalanuvchi: {message.from_user.first_name} (@{message.from_user.username})\n"
                f"User ID: `{message.from_user.id}`\n"
                f"Buyurtmalar soni: {total_orders}\n"
                f"Tarif statusi: *{status}*\n\n"
                f"Mavzu: {topic}\n"
                f"Savollar soni: {count}"
            )
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print("Test buyurtmasini admin'ga yuborishda xato:", e)


# =========================
#   ORTGA VA DEFAULT
# =========================

@bot.message_handler(func=lambda m: m.text == "◀️ Ortga")
def back_to_menu(message):
    bot.send_message(message.chat.id, "Asosiy menyu 👇", reply_markup=main_menu())


@bot.message_handler(func=lambda m: True)
def fallback(message):
    bot.send_message(
        message.chat.id,
        "Kerakli xizmat turini pastdagi menyudan tanlang 👇",
        reply_markup=main_menu()
    )


print("Bot ishga tushdi (Railway, AI va to'lov tizimi bilan)...")
bot.polling(none_stop=True)
