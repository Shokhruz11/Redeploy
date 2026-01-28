Notepad++ v8.9.1 regression fixes, bug-fixes & new improvements:

 1. Fix EOL duplication regression when playing back old recorded macros.
 2. Remedy search failure for pasted text containing trailing invisible EOL character.
 3. Fix customized context menu regression where separator (id="0") escapes FolderName submenu.
 4. Fix issue where a single undo reverted multiple changes after macro execution.
 5. Fix visual glitch when dragging dockable dialogs on a 2nd monitor.
 6. Fix inconsistent automatic search mode switching (RegEx to Extended) in Find dialog.
 7. Fix incorrect URL parsing caused by Unicode special spaces.
 8. Update to Boost 1.90.0.
 9. Improve update themes feature: fix JavaScript.js edge case.
10. Update javascript.js to better match javascript (embedded) in all themes.
11. Function List: enhance for Perl & PHP; add for Nim.
12. Fix comments and highlighting in TCL.
13. Update perl keywords and autocomplete for 5.42.
14. Improvement: display Find dialog status message with invisible characters warning.



Get more info on
https://notepad-plus-plus.org/downloads/v8.9.1/


Included plugins:
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

