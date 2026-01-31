# -*- coding: utf-8 -*-
"""
Super Talaba (soddalashtirilgan, barqaror versiya)

Funksiyalar:
- Gemini (google-generativeai) orqali matn generatsiyasi
- Slayd (PPTX) yaratish
- Referat / mustaqil ish (DOCX)
- Kurs ishi (DOCX)
- /ai orqali oddiy AI bilan suhbat

To'lov, chek, balans hozircha O'CHIRILGAN (test rejim).
"""

import os
from datetime import datetime

import telebot
from telebot import types

import google.generativeai as genai

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

from docx import Document

# ============================
#      ENV SOZLAMALAR
# ============================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN topilmadi! Railway Variables ichiga qo'ying.")
if not GEMINI_API_KEY:
    print("❌ GEMINI_API_KEY topilmadi! Gemini kalitini qo'ying.")

bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

# Gemini sozlash
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        print("✅ Gemini modeli tayyor.")
    except Exception as e:
        print("❌ Gemini modelini yaratishda xato:", e)
        gemini_model = None
else:
    gemini_model = None

# Fayllar saqlanadigan papka
FILES_DIR = "generated_files"
if not os.path.exists(FILES_DIR):
    os.makedirs(FILES_DIR)

# Foydalanuvchi holati (oddiy xotirada)
user_state = {}   # chat_id -> "slayd_topic" / "slayd_pages" / "ref_topic" ...
user_data = {}    # chat_id -> dict{work_type, topic, pages}


# ============================
#    YORDAMCHI FUNKSIYALAR
# ============================

def ask_ai(prompt: str) -> str:
    """Gemini'dan matn olish."""
    if not gemini_model:
        return "AI hozircha sozlanmagan. Admin GEMINI_API_KEY ni tekshirishi kerak."

    try:
        resp = gemini_model.generate_content(prompt)
        text = getattr(resp, "text", "") or ""
        text = text.strip()
        if not text:
            return "AI javob qaytara olmadi. Boshqa mavzu bilan urinib ko'ring."
        return text
    except Exception as e:
        print("Gemini xatosi:", repr(e))
        return "AI xizmatida kutilmagan xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."


def create_pptx_from_text(topic: str, ai_text: str) -> str:
    """AI matnidan slayd (PPTX) fayl yaratish."""
    prs = Presentation()

    colors = [
        RGBColor(0, 102, 204),
        RGBColor(34, 139, 34),
        RGBColor(128, 0, 128),
        RGBColor(220, 20, 60),
        RGBColor(255, 140, 0),
        RGBColor(47, 79, 79),
    ]

    blocks = [b.strip() for b in ai_text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [ai_text]

    for i, block in enumerate(blocks):
        slide_layout = prs.slide_layouts[5]  # blank
        slide = prs.slides.add_slide(slide_layout)

        # fon
        bg = slide.shapes.add_shape(
            autoshape_type_id=1,
            left=Inches(0),
            top=Inches(0),
            width=Inches(13.3),
            height=Inches(7.5),
        )
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = colors[i % len(colors)]
        bg.line.width = 0

        tx = slide.shapes.add_textbox(
            left=Inches(0.7),
            top=Inches(1),
            width=Inches(12),
            height=Inches(5.5),
        )
        tf = tx.text_frame
        tf.word_wrap = True

        lines = block.split("\n")
        title = lines[0][:80]
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        p_title = tf.paragraphs[0]
        p_title.text = title
        p_title.font.size = Pt(36)
        p_title.font.bold = True
        p_title.font.color.rgb = RGBColor(255, 255, 255)
        p_title.alignment = PP_ALIGN.CENTER

        if body:
            p_body = tf.add_paragraph()
            p_body.text = body
            p_body.font.size = Pt(24)
            p_body.font.color.rgb = RGBColor(255, 255, 255)
            p_body.alignment = PP_ALIGN.LEFT

    filename = os.path.join(FILES_DIR, f"slayd_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx")
    prs.save(filename)
    return filename


def create_docx_from_text(title: str, ai_text: str, work_type: str) -> str:
    """AI matnidan DOCX (referat / kurs ishi) yaratish."""
    doc = Document()
    doc.add_heading(f"{work_type}: {title}", level=1)

    blocks = [b.strip() for b in ai_text.split("\n\n") if b.strip()]
    if not blocks:
        blocks = [ai_text]

    for block in blocks:
        doc.add_paragraph(block)

    filename = os.path.join(FILES_DIR, f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
    doc.save(filename)
    return filename


def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 Slayd", "📄 Mustaqil ish / Referat")
    kb.row("📚 Kurs ishi", "🤖 AI bilan suhbat")
    kb.row("❓ Yordam")
    return kb


# ============================
#        KOMANDALAR
# ============================

@bot.message_handler(commands=["start"])
def cmd_start(message):
    text = (
        "Assalomu alaykum!\n\n"
        "Bu bot orqali slayd, mustaqil ish / referat va kurs ishini tez va avtomatik tayyorlab olishingiz mumkin.\n\n"
        "Menyudan kerakli bo'limni tanlang yoki /ai orqali AI bilan suhbatlashing."
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.message_handler(commands=["help"])
def cmd_help(message):
    text = (
        "Yordam:\n\n"
        "- 📝 Slayd: mavzu va taxminiy slaydlar sonini kiriting, bot PPTX fayl beradi.\n"
        "- 📄 Mustaqil ish / Referat: mavzu va bet sonini kiriting, DOCX fayl beradi.\n"
        "- 📚 Kurs ishi: mavzu va bet sonini kiriting, DOCX fayl beradi.\n"
        "- 🤖 AI bilan suhbat: oddiy savol-javob, izoh, tushuntirishlar.\n"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.message_handler(commands=["ai"])
def cmd_ai(message):
    bot.send_message(message.chat.id, "Savol yoki mavzuni yozing. AI javob qaytaradi.")
    user_state[message.chat.id] = "ai_chat"


# ============================
#      MENYU BOSIMLARI
# ============================

@bot.message_handler(func=lambda m: m.text == "🤖 AI bilan suhbat")
def handle_ai_button(message):
    cmd_ai(message)


@bot.message_handler(func=lambda m: m.text == "❓ Yordam")
def handle_help_button(message):
    cmd_help(message)


@bot.message_handler(func=lambda m: m.text == "📝 Slayd")
def handle_slayd(message):
    chat_id = message.chat.id
    user_state[chat_id] = "slayd_topic"
    user_data[chat_id] = {"work_type": "slayd"}
    bot.send_message(chat_id, "Slayd mavzusini yozing:", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: m.text == "📄 Mustaqil ish / Referat")
def handle_referat(message):
    chat_id = message.chat.id
    user_state[chat_id] = "ref_topic"
    user_data[chat_id] = {"work_type": "referat"}
    bot.send_message(chat_id, "Referat / mustaqil ish mavzusini yozing:", reply_markup=types.ReplyKeyboardRemove())


@bot.message_handler(func=lambda m: m.text == "📚 Kurs ishi")
def handle_kurs(message):
    chat_id = message.chat.id
    user_state[chat_id] = "kurs_topic"
    user_data[chat_id] = {"work_type": "kurs ishi"}
    bot.send_message(chat_id, "Kurs ishi mavzusini yozing:", reply_markup=types.ReplyKeyboardRemove())


# ============================
#      STATE-BASED LOGIKA
# ============================

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) in ["slayd_topic", "ref_topic", "kurs_topic"])
def handle_topic(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id)
    data = user_data.get(chat_id, {})

    topic = message.text.strip()
    data["topic"] = topic
    user_data[chat_id] = data

    if state == "slayd_topic":
        user_state[chat_id] = "slayd_pages"
        bot.send_message(chat_id, "Nechta slayd kerak? (masalan, 10):")
    elif state == "ref_topic":
        user_state[chat_id] = "ref_pages"
        bot.send_message(chat_id, "Taxminan necha betlik referat kerak? (masalan, 10):")
    elif state == "kurs_topic":
        user_state[chat_id] = "kurs_pages"
        bot.send_message(chat_id, "Taxminan necha betlik kurs ishi kerak? (masalan, 25):")


@bot.message_handler(func=lambda m: user_state.get(m.chat.id) in ["slayd_pages", "ref_pages", "kurs_pages"])
def handle_pages(message):
    chat_id = message.chat.id
    state = user_state.get(chat_id)
    data = user_data.get(chat_id, {})
    work_type = data.get("work_type")
    topic = data.get("topic", "")

    try:
        pages = int(message.text.strip())
        if pages < 1:
            raise ValueError()
    except ValueError:
        bot.send_message(chat_id, "Iltimos, butun son kiriting (masalan, 10).")
        return

    bot.send_message(chat_id, "AI matn tayyorlayapti, biroz kuting...")

    if work_type == "slayd":
        prompt = (
            f"Mavzu: {topic}\n"
            f"{pages} ta slayd uchun matn tuzing. Har bir slayd uchun sarlavha va 3-6 ta punkt yozing.\n"
            "Har bir slayd matnini ikki bo'sh qator bilan ajrating."
        )
        answer = ask_ai(prompt)
        if answer.startswith("AI xizmatida") or answer.startswith("AI hozircha"):
            bot.send_message(chat_id, answer, reply_markup=main_menu())
        else:
            filename = create_pptx_from_text(topic, answer)
            with open(filename, "rb") as f:
                bot.send_document(chat_id, f, caption=f"Slayd tayyor!\nMavzu: {topic}")

    else:
        work_name = "Referat" if work_type == "referat" else "Kurs ishi"
        prompt = (
            f"Mavzu: {topic}\n"
            f"Taxminan {pages} betlik {work_name} matnini yozing.\n"
            "Kirish, asosiy qism va xulosani alohida bo'limlarda, ilmiy uslubda bayon qiling."
        )
        answer = ask_ai(prompt)
        if answer.startswith("AI xizmatida") or answer.startswith("AI hozircha"):
            bot.send_message(chat_id, answer, reply_markup=main_menu())
        else:
            filename = create_docx_from_text(topic, answer, work_name)
            with open(filename, "rb") as f:
                bot.send_document(chat_id, f, caption=f"{work_name} tayyor!\nMavzu: {topic}")

    # holatni tozalash
    user_state[chat_id] = None
    user_data[chat_id] = {}
    bot.send_message(chat_id, "Yana buyurtma berish uchun menyudan tanlang.", reply_markup=main_menu())


# ============================
#        AI CHAT /ai
# ============================

@bot.message_handler(func=lambda m: user_state.get(m.chat.id) == "ai_chat")
def handle_ai_chat(message):
    chat_id = message.chat.id
    text = message.text.strip()
    bot.send_chat_action(chat_id, "typing")
    answer = ask_ai(text)
    bot.send_message(chat_id, answer, reply_markup=main_menu())
    user_state[chat_id] = None


# ============================
#    DEFAULT HANDLER
# ============================

@bot.message_handler(func=lambda m: True, content_types=["text"])
def fallback(message):
    # Agar hech qanday state bo'lmasa
    if message.text.startswith("/"):
        bot.send_message(message.chat.id, "Noma'lum buyruq. /start yoki /help ni yozib ko'ring.")
    else:
        bot.send_message(
            message.chat.id,
            "Menyudan kerakli bo'limni tanlang.",
            reply_markup=main_menu()
        )


# ============================
#     BOTNI ISHGA TUSHIRISH
# ============================

if __name__ == "__main__":
    print("✅ Super Talaba (Gemini, soddalashtirilgan) ishga tushdi.")
    bot.infinity_polling(skip_pending=True)
