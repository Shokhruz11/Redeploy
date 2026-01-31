import os
import telebot
import google.generativeai as genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@admin")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

bot = telebot.TeleBot(BOT_TOKEN)

# --- MENU ---
def main_menu():
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📊 Slayd", "📄 Insho")
    kb.row("📚 Referat", "📝 Kurs ishi")
    kb.row("💳 To'lov", "👥 Referal")
    kb.row("🛠 Yordam", "👨‍🏫 Professional jamoa")
    return kb

# --- START ---
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(
        message.chat.id,
        "Assalomu alaykum! 😊\n\n"
        "Men AI yordamchiman. Slayd, insho, referat va boshqa topshiriqlarni "
        "tez va sifatli tayyorlab beraman!",
        reply_markup=main_menu()
    )

# --- SLAYD ---
@bot.message_handler(func=lambda m: m.text == "📊 Slayd")
def slayd(message):
    bot.send_message(message.chat.id, "Slayd mavzusini kiriting:")
    bot.register_next_step_handler(message, create_slayd)

def create_slayd(message):
    topic = message.text
    response = model.generate_content(f"'{topic}' mavzusida 10 slayd tayyorla.")
    bot.send_message(message.chat.id, response.text)

# --- INSHO ---
@bot.message_handler(func=lambda m: m.text == "📄 Insho")
def insho(message):
    bot.send_message(message.chat.id, "Insho mavzusini yozing:")
    bot.register_next_step_handler(message, create_insho)

def create_insho(message):
    topic = message.text
    response = model.generate_content(f"{topic} bo‘yicha 1,5-2 betlik insho yozing.")
    bot.send_message(message.chat.id, response.text)

# --- YO'LMALARI ---
@bot.message_handler(func=lambda m: m.text == "🛠 Yordam")
def help_msg(message):
    bot.send_message(
        message.chat.id,
        "👋 Yordam bo‘limi\n\n"
        "Slayd — 📊\n"
        "Insho — 📄\n"
        "Referat — 📚\n"
        "Kurs ishi — 📝\n"
        "Admin: " + ADMIN_USERNAME
    )

# --- RUN ---
if __name__ == "__main__":
    print("🔥 Bot ishga tushdi!")
    bot.infinity_polling()
