pyTelegramBotAPI==4.14.0
# UNIVERSAL TELEGRAM BOT (Slayd / Referat / AI)

import telebot
from telebot import types

BOT_TOKEN = "8086850400:AAHUpWbBtn9Bl_PMQgYOlf5OlmC-NBB2z30"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Assalomu alaykum! Bot muvaffaqiyatli ishga tushdi ✔")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, "Siz yozdingiz: " + message.text)

print("Bot ishga tushdi...")
bot.polling(none_stop=True)
