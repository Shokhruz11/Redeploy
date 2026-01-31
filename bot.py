# -*- coding: utf-8 -*-
import os
import telebot
from telebot import types
import google.generativeai as genai

# ============================
#     ENV SOZLAMALAR
# ============================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if not BOT_TOKEN:
    print("⚠️ BOT_TOKEN topilmadi. Railway Variables ichiga qo'yishni unutmang!")
if not GEMINI_API_KEY:
    print("⚠️ GEMINI_API_KEY topilmadi. Gemini kalitini qo'yishni unutmang!")

# Telegram bot obyektini yaratamiz
bot = telebot.TeleBot(BOT_TOKEN) if BOT_TOKEN else None

# Gemini modelini sozlash
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        print("❌ Gemini modelini yaratishda xatolik:", e)
        model = None
else:
    model = None


# ============================
#      YORDAMCHI FUNKSIYA
# ============================

def ask_gemini(prompt: str) -> str:
    """
    Foydalanuvchi matnini Gemini'ga yuborib, javobini qaytaradi.
    Xatolik bo'lsa, foydalanuvchiga tushunarli xabar qaytaradi.
    """
    if not model:
        return ("⚠️ AI hozircha sozlanmagan.\n"
                "Iltimos, admin Gemini kalitini tekshirsin.")

    try:
        resp = model.generate_content(prompt)
        text = getattr(resp, "text", "") or ""
        text = text.strip()
        if not text:
            return "AI javob qaytara olmadi. Boshqa mavzu bilan urinib ko'ring."
        return text
    except Exception as e:
        print("❌ Gemini xatosi:", repr(e))
        return "⚠️ AI xizmatida kutilmagan xatolik yuz berdi. Birozdan so'ng qayta urinib ko'ring."


# ============================
#        MENYU
# ============================

def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📝 Slayd", "📄 Mustaqil ish / Referat")
    kb.row("🎓 Kurs ishi", "🤖 AI bilan suhbat")
    kb.row("❓ Yordam")
    return kb


# ============================
#      HANDLERLAR
# ============================

if bot:

    @bot.message_handler(commands=["start"])
    def start(message):
        bot.send_message(
            message.chat.id,
            "Assalomu alaykum!\n\n"
            "Bu test versiya bot. Hozircha quyidagilar ishlaydi:\n"
            "• Menyu tugmalari\n"
            "• 🤖 AI bilan suhbat (Gemini)\n\n"
            "Boshlash uchun biror tugmani bosing yoki /ai buyrug'idan foydalaning.",
            reply_markup=main_menu()
        )

    @bot.message_handler(commands=["ai"])
    def ai_command(message):
        bot.send_message(
            message.chat.id,
            "Mavzu yoki savolingizni yuboring. Masalan:\n"
            "\"O'zbekiston tarixi bo'yicha 5 ta savol tuzib ber\""
        )
        bot.register_next_step_handler(message, ai_chat_step)

    def ai_chat_step(message):
        user_text = message.text.strip()
        bot.send_chat_action(message.chat.id, "typing")
        answer = ask_gemini(user_text)
        bot.send_message(message.chat.id, answer)

    @bot.message_handler(func=lambda m: m.text == "🤖 AI bilan suhbat")
    def menu_ai(message):
        ai_command(message)

    @bot.message_handler(func=lambda m: m.text == "❓ Yordam")
    def help_handler(message):
        bot.send_message(
            message.chat.id,
            "Bot imkoniyatlari:\n"
            "• Slayd / mustaqil ish / kurs ishini keyinchalik qo'shamiz.\n"
            "• Hozircha asosiy funksiya – 🤖 AI bilan suhbat.\n\n"
            "AI bilan gaplashish uchun /ai buyrug'ini yuboring."
        )

    # Hozircha qolgan menyu tugmalari faqat xabar qaytaradi
    @bot.message_handler(func=lambda m: m.text in ["📝 Slayd",
                                                   "📄 Mustaqil ish / Referat",
                                                   "🎓 Kurs ishi"])
    def coming_soon(message):
        bot.send_message(
            message.chat.id,
            "Bu bo'lim hali ishlab chiqilmoqda.\n"
            "Hozircha faqat 🤖 AI bilan suhbat bo'limidan foydalaning."
        )

    @bot.message_handler(func=lambda m: True)
    def fallback(message):
        # Agar oddiy matn yuborsa, avtomatik AI ga yuboramiz
        user_text = message.text.strip()
        if not user_text.startswith("/"):
            bot.send_chat_action(message.chat.id, "typing")
            answer = ask_gemini(user_text)
            bot.send_message(message.chat.id, answer)
        else:
            bot.send_message(
                message.chat.id,
                "Noma'lum buyruq. Menyudan foydalaning yoki /ai ni yozing."
            )

    # Botni ishga tushirish
    if __name__ == "__main__":
        print("✅ Bot ishga tushdi (Gemini bilan).")
        bot.infinity_polling(skip_pending=True)
else:
    print("❌ BOT_TOKEN bo'lmagani uchun bot ishga tushmadi.")
