import telebot
from telebot import types

# =========================
#   SOZLAMALAR
# =========================

BOT_TOKEN = "8086850400:AAHUpWbBtn9Bl_PMQgYOlf5OlmC-NBB2z30"  # @BotFather dan olingan tokenni shu yerga yozing

ADMIN_ID = 5754599655  # xohlasang keyin o'zingning Telegram ID'ingni qo'yamiz

bot = telebot.TeleBot(BOT_TOKEN)


# =========================
#   YORDAMCHI FUNKSIYALAR
# =========================

def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("🧾 Slayd")
    btn2 = types.KeyboardButton("📚 Referat")
    btn3 = types.KeyboardButton("📝 Mustaqil ish")
    btn4 = types.KeyboardButton("📄 Esse / Insho")
    btn5 = types.KeyboardButton("ℹ️ Yordam")
    markup.add(btn1, btn2)
    markup.add(btn3, btn4)
    markup.add(btn5)
    return markup


# =========================
#   HANDLERLAR
# =========================

@bot.message_handler(commands=['start'])
def start(message):
    text = (
        "Assalomu alaykum! 👋\n\n"
        "Bu bot orqali quyidagi xizmatlardan foydalanishingiz mumkin:\n"
        "🧾 Slayd tayyorlash\n"
        "📚 Referat / Mustaqil ish\n"
        "📄 Esse / Insho va boshqalar.\n\n"
        "Kerakli xizmat turini tanlang 👇"
    )
    bot.send_message(message.chat.id, text, reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "ℹ️ Yordam")
def help_handler(message):
    text = (
        "ℹ️ *Yordam bo‘limi*\n\n"
        "1) Xizmat turini tanlang (Slayd, Referat, Mustaqil ish, Esse).\n"
        "2) Bot sizdan mavzu va bet / slayd sonini so‘raydi.\n"
        "3) Ma'lumotlaringiz admin ga yuboriladi.\n"
        "4) Tez orada siz bilan bog‘lanamiz.\n\n"
        "_AI orqali avtomatik matn generatsiya qilish keyingi bosqichda qo‘shiladi._"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text in ["🧾 Slayd", "📚 Referat", "📝 Mustaqil ish", "📄 Esse / Insho"])
def service_selected(message):
    service = message.text
    bot.send_message(
        message.chat.id,
        f"{service} xizmati tanlandi ✅\n\n"
        "Iltimos, mavzuni yozib yuboring.\n\n"
        "Masalan:\n"
        "\"Oila psixologiyasida nizolarni bartaraf etish usullari\"",
    )
    bot.register_next_step_handler(message, ask_pages, service)


def ask_pages(message, service):
    topic = message.text.strip()

    if len(topic) < 5:
        bot.send_message(message.chat.id, "Mavzu juda qisqa, biroz batafsilroq yozing.")
        return bot.register_next_step_handler(message, ask_pages, service)

    msg = bot.send_message(
        message.chat.id,
        "Necha bet/slayd bo‘lishi kerak?\n\n"
        "Masalan: 8 bet yoki 15 slayd."
    )
    bot.register_next_step_handler(msg, finish_order, service, topic)


def finish_order(message, service, topic):
    pages = message.text.strip()

    # Foydalanuvchiga tasdiq
    confirm_text = (
        "✅ Buyurtmangiz qabul qilindi!\n\n"
        f"Xizmat turi: {service}\n"
        f"Mavzu: {topic}\n"
        f"Bet/Slayd soni: {pages}\n\n"
        "Tez orada admin siz bilan bog‘lanadi. Rahmat! 🙌"
    )
    bot.send_message(message.chat.id, confirm_text, reply_markup=main_menu())

    # Admin'ga yuborish (agar ADMIN_ID to'g'ri qo'yilgan bo'lsa)
    try:
        admin_text = (
            "📥 *Yangi buyurtma!*\n\n"
            f"Foydalanuvchi: {message.from_user.first_name} (@{message.from_user.username})\n"
            f"User ID: `{message.from_user.id}`\n\n"
            f"Xizmat: {service}\n"
            f"Mavzu: {topic}\n"
            f"Bet/Slayd soni: {pages}"
        )
        if ADMIN_ID != 111111111:
            bot.send_message(ADMIN_ID, admin_text, parse_mode="Markdown")
    except Exception as e:
        print("Admin'ga yuborishda xato:", e)


@bot.message_handler(func=lambda m: True)
def fallback(message):
    """
    Boshqa har qanday xabar uchun.
    """
    bot.send_message(
        message.chat.id,
        "Kerakli xizmat turini tugmalardan tanlang 👇",
        reply_markup=main_menu()
    )


print("Bot ishga tushdi (Railway)...")
bot.polling(none_stop=True)
