import telebot

BOT_TOKEN = "8086850400:AAHUpWbBtn9Bl_PMQgYOlf5OlmC-NBB2z30"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Assalomu alaykum! Bot ishga tushdi!")

@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, message.text)

bot.polling(none_stop=True)
