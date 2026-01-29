import os
import sqlite3
from datetime import datetime

import telebot
from telebot import types
from openai import OpenAI

# ============================
#      SOZLAMALAR
# ============================

# ⚠️ O'ZINGIZNING KALITLARINGIZNI QO'YING ⚠️
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"           # @BotFather dan olingan token
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY_HERE" # OpenAI API kaliti

# Kontaktlar
KURS_ISHI_ADMIN = "@Shokhruz11"
PROFESSIONAL_TEAM = "@Shokhruz11"           # foydalanuvchi iltimosiga ko'ra ikkalasi ham shu
TALABALAR_CHAT = "@Talabalar_xizmati"       # xohlasangiz almashtirasiz

# To'lov ma'lumotlari
CARD_NUMBER = "4790920018585070"
CARD_OWNER = "Qo'chqorov Shohruz"
SERVICE_PRICE = 5000  # so'm, 20 listgacha

# OpenAI mijozini tayyorlab qo'yamiz
client = OpenAI(api_key=OPENAI_API_KEY)

# Bot obyektimiz
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Foydalanuvchi holatlari (session) uchun xotira
user_states = {}  # {chat_id: {"mode": "slayd/esse/kurs", "step": 1}}


# ============================
#      MA'LUMOTLAR BAZASI
# ============================

DB_NAME = "bot_data.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Foydalanuvchilar jadvali
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            free_used INTEGER DEFAULT 0,
            total_requests INTEGER DEFAULT 0
        )
        """
    )

    # Buyurtmalar tarixi
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            req_type TEXT,
            created_at TEXT
        )
        """
    )

    conn.commit()
    conn.close()


def get_or_create_user(user):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT user_id, free_used, total_requests FROM users WHERE user_id = ?", (user.id,))
    row = c.fetchone()

    if row is None:
        c.execute(
            """
            INSERT INTO users (user_id, username, first_name, free_used, total_requests)
            VALUES (?, ?, ?, 0, 0)
            """,
            (user.id, user.username, user.first_name),
        )
        conn.commit()
        free_used = 0
        total_requests = 0
    else:
        free_used = row[1]
        total_requests = row[2]

    conn.close()
    return {"free_used": free_used, "total_requests": total_requests}


def mark_request(user_id: int, req_type: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        "UPDATE users SET total_requests = total_requests + 1 WHERE user_id = ?",
        (user_id,),
    )
    c.execute(
        "INSERT INTO requests (user_id, req_type, created_at) VALUES (?, ?, ?)",
        (user_id, req_type, datetime.now().isoformat(timespec="seconds")),
    )

    conn.commit()
    conn.close()


def mark_free_used(user_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET free_used = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


# ============================
#      YORDAMCHI FUNKSIYALAR
# ============================

def create_main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    row1 = [
        types.KeyboardButton("📊 Slayd (PPTX)"),
        types.KeyboardButton("📝 Esse / referat"),
    ]
    row2 = [
        types.KeyboardButton("📄 Mustaqil ish / kurs ishi"),
        types.KeyboardButton("❓ Test tuzish"),
    ]
    row3 = [
        types.KeyboardButton("💼 Kurs ishi (admin)"),
        types.KeyboardButton("👨‍💻 Professional jamoa"),
    ]
    row4 = [
        types.KeyboardButton("💰 To'lov"),
        types.KeyboardButton("ℹ️ Yordam"),
    ]
    kb.row(*row1)
    kb.row(*row2)
    kb.row(*row3)
    kb.row(*row4)
    return kb


def split_message(text, chunk_size=4000):
    """Telegram 4096 belgidan oshsa bo'linib yuborish uchun."""
    for i in range(0, len(text), chunk_size):
        yield text[i : i + chunk_size]


def call_openai(mode: str, user_prompt: str, language: str = "uzb") -> str:
    """
    OpenAI dan javob olish.
    mode: 'slayd', 'esse', 'kurs', 'test'
    user_prompt: foydalanuvchi bergan ma'lumot (fan, mavzu, list soni va h.k.)
    """
    if language.lower().startswith("ru"):
        lang_instruction = "Yozuv tili: rus tilida."
    elif language.lower().startswith("en"):
        lang_instruction = "Yozuv tili: ingliz tilida."
    else:
        lang_instruction = "Yozuv tili: o'zbek tilida (lotin)."

    if mode == "slayd":
        task_instruction = (
            "Menga zamonaviy, mantiqan bog'langan, slaydga tayyor rejalar va asosiy punktlar yozib ber. "
            "Kerak bo'lsa, slaydlar uchun bo'limlarga bo'lib yoz. Matnni prezentatsiya uchun qulay shaklda yoz."
        )
    elif mode == "esse":
        task_instruction = (
            "Menga talaba uchun plagiats darajasi past, ilmiy-uslubiy, kirish-asosiy-qism-xulosa "
            "tuzilmasida esse/referat matni yozib ber."
        )
    elif mode == "kurs":
        task_instruction = (
            "Menga talaba uchun mustaqil ish yoki kurs ishi uchun batafsil, ilmiy-uslubda, "
            "reja asosida yozilgan matn tayyorlab ber. Kirishda dolzarblik, maqsad-vazifalar bo'lsin, "
            "asosiy qismda bandlar bo'yicha batafsil bayon qilinsin va oxirida xulosa yozilsin."
        )
    elif mode == "test":
        task_instruction = (
            "Menga 20 ta test savoli tayyorlab ber. Har bir savolda 4 ta variant bo'lsin (A, B, C, D). "
            "Har bir savoldan keyin javobni alohida ko'rsatib o't (masalan: Javob: C)."
        )
    else:
        task_instruction = "Foydalanuvchi so'rovi bo'yicha matn tayyorlab ber."

    system_msg = (
        "Siz talabalarga yordam beradigan o'qituvchi-assistent AIsiz. "
        "Matnlarni tuzishda imlo va uslubga e'tibor qarating, keraksiz takrorlardan qoching. "
        "Plagiat darajasi past bo'lishiga harakat qiling."
    )

    full_prompt = (
        f"{task_instruction}\n"
        f"{lang_instruction}\n\n"
        f"Foydalanuvchi bergan ma'lumot:\n{user_prompt}"
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": full_prompt},
        ],
        max_tokens=2000,
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()


def ask_details_for_mode(message, mode_key: str, nice_name: str):
    chat_id = message.chat.id
    user_states[chat_id] = {"mode": mode_key, "step": 1}
    bot.send_message(
        chat_id,
        f"✍️ {nice_name} uchun ma'lumotni yozing.\n\n"
        f"Masalan:\n"
        f"<i>Fan: Pedagogika\nMavzu: Ta'limning ko'rgazmali metodlari\nHajm: 15 slayd</i>",
    )


# ============================
#      HANDLERLAR
# ============================

@bot.message_handler(commands=["start", "menu"])
def handle_start(message):
    init_db()
    get_or_create_user(message.from_user)

    text = (
        "Assalomu alaykum! 👋\n"
        "Ushbu bot orqali siz quyidagi xizmatlardan foydalanishingiz mumkin:\n\n"
        "📊 Slayd (PPTX)\n"
        "📝 Esse / referat\n"
        "📄 Mustaqil ish / kurs ishi\n"
        "❓ Test savollari tuzish\n\n"
        "🎁 <b>Har bir yangi foydalanuvchi uchun 1 marta AI xizmati BEPUL!</b>\n"
        f"Keyingi buyurtmalar narxi: <b>{SERVICE_PRICE} so'm</b> (20 listgacha).\n\n"
        "Kerakli bo'limni menudan tanlang 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=create_main_menu())


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip()

    # Agar foydalanuvchi hozir biror rejimda bo'lsa (slayd, esse va h.k.)
    state = user_states.get(chat_id)

    # Avval menyu tugmalarini tekshiramiz
    if text == "📊 Slayd (PPTX)":
        ask_details_for_mode(message, "slayd", "Slayd (PPTX)")
        return

    if text == "📝 Esse / referat":
        ask_details_for_mode(message, "esse", "Esse / referat")
        return

    if text == "📄 Mustaqil ish / kurs ishi":
        ask_details_for_mode(message, "kurs", "Mustaqil ish / kurs ishi")
        return

    if text == "❓ Test tuzish":
        ask_details_for_mode(message, "test", "Test savollari")
        return

    if text == "💼 Kurs ishi (admin)":
        bot.send_message(
            chat_id,
            f"💼 Kurs ishi va diplom ishlar bo'yicha barcha masalalar bo'yicha admin bilan bog'laning:\n"
            f"{KURS_ISHI_ADMIN}\n\n"
            "Narx, muddat va boshqa shartlar admin bilan kelishiladi.",
        )
        return

    if text == "👨‍💻 Professional jamoa":
        bot.send_message(
            chat_id,
            "👨‍💻 Professional jamoamiz bilan bog'lanish uchun:\n"
            f"{PROFESSIONAL_TEAM}\n\n"
            "Slayd, kurs ishi, diplom ishi va boshqa topshiriqlarni kelishilgan holda bajarib beramiz.",
        )
        return

    if text == "💰 To'lov":
        bot.send_message(
            chat_id,
            "💰 <b>To'lov ma'lumotlari</b>\n\n"
            f"Karta raqami: <code>{CARD_NUMBER}</code>\n"
            f"Karta egasi: <b>{CARD_OWNER}</b>\n\n"
            f"Xizmat narxi: <b>{SERVICE_PRICE} so'm</b> (20 listgacha).\n\n"
            "To'lovni amalga oshirgach, chek skrinshotini adminga yuboring:\n"
            f"{KURS_ISHI_ADMIN}",
        )
        return

    if text == "ℹ️ Yordam":
        bot.send_message(
            chat_id,
            "ℹ️ <b>Yordam</b>\n\n"
            "1️⃣ Menudan kerakli bo'limni tanlang (slayd, esse, kurs ishi va h.k.).\n"
            "2️⃣ Bot sizdan fan, mavzu va taxminiy hajm haqida ma'lumot so'raydi.\n"
            "3️⃣ AI siz uchun tayyor matn/slayd rejasini tuzib beradi.\n\n"
            "🎁 1-marta foydalanish <b>bepul</b>, keyingi buyurtmalar uchun 5000 so'm.\n\n"
            "Admin / referal kontakt: "
            f"{KURS_ISHI_ADMIN}\n"
            "Talabalar uchun chat: "
            f"{TALABALAR_CHAT}",
        )
        return

    # Agar foydalanuvchi hozir biror rejimda bo'lsa (slayd, esse va h.k.)
    if state and state.get("step") == 1:
        handle_generation_request(message, state)
        return

    # Agar hech qanday holatda bo'lmasa, /start menyuga qaytaramiz
    bot.send_message(
        chat_id,
        "Kerakli bo'limni menudan tanlang yoki /start buyrug'ini bosing.",
        reply_markup=create_main_menu(),
    )


def handle_generation_request(message, state):
    """
    1-step: foydalanuvchi fan/mavzu/hajmni yozdi -> OpenAI orqali natija chiqaramiz.
    """
    chat_id = message.chat.id
    mode = state.get("mode")

    # Foydalanuvchi ma'lumotlari va limitini tekshiramiz
    user_info = get_or_create_user(message.from_user)
    free_used = user_info["free_used"]
    total_requests = user_info["total_requests"]

    user_prompt = message.text.strip()

    # Tilni avtomatik aniqlashga urinmaymiz, asosan o'zbek bo'ladi
    language = "uzb"

    # Bepul / pullik holat
    is_free_now = False
    header_text = ""

    if free_used == 0:
        # Birinchi marta - bepul
        is_free_now = True
        mark_free_used(message.from_user.id)
        header_text = (
            "🎁 <b>Birinchi buyurtmangiz bepul bajarildi!</b>\n"
            "Keyingi buyurtmalar uchun to'lov: "
            f"<b>{SERVICE_PRICE} so'm</b> (20 listgacha).\n\n"
        )
    else:
        header_text = (
            "💳 <b>Eslatma:</b> ushbu va keyingi buyurtmalar narxi "
            f"<b>{SERVICE_PRICE} so'm</b> (20 listgacha).\n"
            "To'lov haqida batafsil <b>💰 To'lov</b> bo'limida.\n\n"
        )

    bot.send_message(chat_id, "⏳ So'rovingiz AI orqali qayta ishlanmoqda, biroz kuting...")

    try:
        result_text = call_openai(mode, user_prompt, language=language)
    except Exception as e:
        bot.send_message(
            chat_id,
            "❌ Xatolik yuz berdi. Iltimos keyinroq yana urinib ko'ring.\n"
            f"Xatolik matni (admin uchun): <code>{e}</code>",
        )
        # Holatni tozalaymiz
        user_states.pop(chat_id, None)
        return

    # Buyurtmani bazaga yozamiz
    mark_request(message.from_user.id, mode)

    full_text = header_text + result_text

    for part in split_message(full_text):
        bot.send_message(chat_id, part)

    # Holatni tugatamiz
    user_states.pop(chat_id, None)

    # Oxirida menyuga qaytarish
    bot.send_message(
        chat_id,
        "✅ Tayyor. Yana xizmat kerak bo'lsa, menudan tanlang 👇",
        reply_markup=create_main_menu(),
    )


# ============================
#      ASOSIY QISM
# ============================

if __name__ == "__main__":
    # Dastlab DB ni tayyorlab olamiz
    init_db()

    print("Bot ishga tushdi...")
    bot.infinity_polling(skip_pending=True)
