import os
import time
import sqlite3
from datetime import datetime

import telebot
from telebot import types
from openai import OpenAI
from pptx import Presentation
from docx import Document

# ============================
#    ENV SOZLAMALAR
# ============================

BOT_TOKEN = os.getenv("8552375519:AAGH-yowxaHPeVn8wyjOYCGvv-KsYF0NkgE")  
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_ID = os.getenv("5754599655")
CARD_NUMBER = os.getenv("4790920018585070")
CARD_OWNER = os.getenv("Qo'chqorov Shohruz")
ADMIN_USERNAME = os.getenv("Shokhruz11")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env o'zgaruvchisi topilmadi")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY env o'zgaruvchisi topilmadi")

client = OpenAI(api_key=OPENAI_API_KEY)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ============================
#      BAZA SOZLASH
# ============================

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            userid INTEGER,
            balance INTEGER DEFAULT 0,
            created TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ============================
#  FOYDALANUVCHI YARATISH
# ============================

def get_or_create_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE userid=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users(userid, balance, created) VALUES (?, ?, ?)",
                       (user_id, 0, datetime.now()))
        conn.commit()

    conn.close()


# ============================
#       ASOSIY MENU
# ============================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🖼 Slayd", "📄 Referat")
    markup.add("📘 Mustaqil ish", "📑 Essay")
    markup.add("🧪 Test tuzish", "📚 Kurs ishi")
    markup.add("👨‍💻 Professional jamoa", "ℹ Yordam")
    markup.add("💳 To‘lov", "👤 Profil")
    return markup


# ============================
#      START COMMAND
# ============================

@bot.message_handler(commands=['start'])
def start(msg):
    get_or_create_user(msg.from_user.id)

    bot.send_message(
        msg.chat.id,
        f"Assalomu alaykum, <b>{msg.from_user.first_name}</b> 👋\n"
        "Ushbu bot orqali slayd, referat, mustaqil ish, esse va boshqa topshiriqlarni osongina yaratishingiz mumkin!",
        reply_markup=main_menu()
    )


# ============================
#  AI ORQALI MATN YARATISH
# ============================

def generate_text_ai(prompt):
    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        return response.output_text
    except Exception as e:
        return f"Xatolik: {e}"


# ============================
#      MENU HANDLER
# ============================

@bot.message_handler(func=lambda m: True)
def menu_handler(msg):

    # ---------------- Slayd ----------------
    if msg.text == "🖼 Slayd":
        bot.send_message(msg.chat.id, "Slayd mavzusini kiriting:")
        bot.register_next_step_handler(msg, create_slide)
        return

    # ---------------- Referat ----------------
    if msg.text == "📄 Referat":
        bot.send_message(msg.chat.id, "Referat mavzusini kiriting:")
        bot.register_next_step_handler(msg, create_referat)
        return

    # ---------------- Kurs ishi / Admin link ----------------
    if msg.text == "📚 Kurs ishi":
        bot.send_message(msg.chat.id, f"Kurs ishi buyurtma uchun admin: {ADMIN_USERNAME}")
        return

    if msg.text == "👨‍💻 Professional jamoa":
        bot.send_message(msg.chat.id, f"Pro jamoa bilan bog‘lanish: {ADMIN_USERNAME}")
        return

    if msg.text == "ℹ Yordam":
        bot.send_message(msg.chat.id,
                         "Yordam uchun admin bilan bog‘laning:\n"
                         f"{ADMIN_USERNAME}")
        return

    # ---------------- To‘lov ----------------
    if msg.text == "💳 To‘lov":
        bot.send_message(msg.chat.id,
                         f"💳 To‘lov uchun karta:\n"
                         f"<b>{CARD_NUMBER}</b>\n"
                         f"{CARD_OWNER}")
        return

    # ---------------- Profil ----------------
    if msg.text == "👤 Profil":
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE userid=?", (msg.from_user.id,))
        bal = cursor.fetchone()[0]
        conn.close()

        bot.send_message(msg.chat.id,
                         f"👤 Profil:\n"
                         f"ID: <code>{msg.from_user.id}</code>\n"
                         f"Balans: <b>{bal} so‘m</b>")
        return

    else:
        bot.send_message(msg.chat.id, "❗ Iltimos, menyudan tanlang.")
        return


# ============================
#     SLAYD YARATISH
# ============================

def create_slide(msg):
    topic = msg.text.strip()
    bot.send_message(msg.chat.id, "⏳ Slayd yaratilyapti...")

    text = generate_text_ai(f"{topic} mavzusi bo‘yicha 10 slaydlik matn tuzib ber")

    file = f"slayd_{msg.chat.id}.pptx"
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    title = slide.shapes.title
    title.text = topic

    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Mazmuni"
    slide.placeholders[1].text = text

    prs.save(file)
    bot.send_document(msg.chat.id, open(file, "rb"))
    os.remove(file)


# ============================
#     REFERAT YARATISH
# ============================

def create_referat(msg):
    topic = msg.text.strip()
    bot.send_message(msg.chat.id, "⏳ Referat yaratilmoqda...")

    text = generate_text_ai(f"{topic} bo‘yicha 4-5 betlik referat yozing.")

    file = f"referat_{msg.chat.id}.docx"
    doc = Document()
    doc.add_heading(topic, level=1)
    doc.add_paragraph(text)
    doc.save(file)

    bot.send_document(msg.chat.id, open(file, "rb"))
    os.remove(file)


# ============================
#       BOTNI ISHGA TUSHIRISH
# ============================

print("Bot ishga tushdi!")
bot.polling(none_stop=True)

