from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

import datetime
import os
import random
import re
import logging
import time
from typing import List, Optional, Tuple

import telegram
from fastapi import BackgroundTasks, FastAPI, HTTPException
from telegram import Update
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (CallbackContext, CommandHandler, ConversationHandler,
                          ContextTypes, Filters, MessageHandler, Updater,
                          filters)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(title="Ask Isnad Bot")


@app.on_event("startup")
async def startup_event():
    print('Main Server started---- :', datetime.datetime.now())
    global is_task_running
    is_task_running = True
    try:
        main()
        pass
    except telegram.error.Conflict as e:
        print(f"Telegram Conflict Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Define your welcome message and options
welcome_message = "أهلا بك في بوت *إسناد.* \n\n برجاء إختيار إحد الخيارات التالية .\n\n"



def read_text_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        text = file.read()
    return text

def detect_language(text):
    # Check if the text contains any Arabic characters
    if any('\u0600' <= c <= '\u06FF' for c in text):
        return 'Arabic'
    # Check if the text contains any Hebrew characters
    elif any('\u0590' <= c <= '\u05FF' for c in text):
        return 'Hebrew'
    else:
        return None

def get_pairs(text):
    pairs = []
    current_pair = []

    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line == '-----------------------------------------------------------':
            if current_pair:
                pairs.append(current_pair)
            current_pair = []
            continue

        current_pair.append(line)

    if current_pair:
        pairs.append(current_pair)

    return pairs
def get_random_msg(file_name):
    file_path = file_name + '.txt'
    text = read_text_file(file_path)
    pairs = get_pairs(text)

    random_pair = random.choice(pairs)
    language = detect_language(random_pair[0])

    result = {}
    if language == 'Hebrew':
        result['Hebrew'] = '\n'.join(random_pair[0:len(random_pair)//2])
        result['Arabic'] = '\n'.join(random_pair[len(random_pair)//2:])
    elif language == 'Arabic':
        result['Arabic'] = '\n'.join(random_pair[0:len(random_pair)//2])
        result['Hebrew'] = '\n'.join(random_pair[len(random_pair)//2:])

    return result

    

# Define a function to handle the /start command
def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message with options when the command /start is issued."""
    keyboard = [
        [InlineKeyboardButton("💥 عبارات معارضة لنتنياهو", callback_data='option1')],
        [InlineKeyboardButton("🎗️ عبارات متضامنه مع الأسرى وأهاليهم", callback_data='option2')],
        [InlineKeyboardButton("🕊️ عبارات ضد الحرب", callback_data='option3')],
        [InlineKeyboardButton("🧑‍🦽 عبارات متضامنه مع الجنود القتلى", callback_data='option4')],
        [InlineKeyboardButton("🐷 عبارات ضد بنغفير واليمين المتطرف", callback_data='option5')],
        [InlineKeyboardButton("📚 تعبيرات لمواقف متنوعة", callback_data='option6')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=update.effective_chat.id,text=welcome_message, reply_markup=reply_markup,  parse_mode= 'Markdown')

# Define a function to handle button clicks
def button_click(update: Update, context: CallbackContext) -> None:
    """Respond to button clicks."""
    query = update.callback_query
    query.answer()
    option = query.data
    if option == 'option1':
        keyboard = [
            [InlineKeyboardButton("🪖 عبارات ضد نتنياهو بسبب الفشل العسكري", callback_data='sub_option1_1')],
            [InlineKeyboardButton("💰 ضد نتنياهو لأسباب اقتصاديه", callback_data='sub_option1_2')],
            [InlineKeyboardButton("👎 ضد نتنياهو لأسباب أخرى", callback_data='sub_option1_3')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("✅ يرجي إختيار نوع العبارات المطلوبة", reply_markup=reply_markup)
    elif option == 'option2':
        keyboard = [
            [InlineKeyboardButton("👨‍👩‍👧‍👦 عبارات متعاطفة مع أهالي الأسرى", callback_data='sub_option2_1')],
            [InlineKeyboardButton("♾️ عبارات تدعو للتظاهر لتحرير الأسري", callback_data='sub_option2_2')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("يرجي إختيار نوع العبارات المطلوبة:", reply_markup=reply_markup)
    elif option == 'option3':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة",  callback_data='option3')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)
        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'option4':
        keyboard = [
            [InlineKeyboardButton("🧑‍🦽 عبارات متضامنه مع الجنود القتلى", callback_data='option4')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'option5':
        keyboard = [
            [InlineKeyboardButton("🐷 عبارات ساخرة من بنغفير أو سموتريتش", callback_data='sub_option5_1')],
            [InlineKeyboardButton("🐽 عبارات موضوعية ضد توجهات بنغفير وسموتريتش", callback_data='sub_option5_2')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        query.message.reply_text("✅ يرجي إختيار نوع العبارات المطلوبة:", reply_markup=reply_markup)
    elif option == 'option6':
            keyboard = [
                [InlineKeyboardButton("📖 عبارات عامة", callback_data='sub_option6_1')],
                [InlineKeyboardButton("📕 تعبيرات قصيرة لمواقف متنوعة", callback_data='sub_option6_2')],
                [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            query.message.reply_text("✅ يرجي إختيار نوع العبارات المطلوبة:", reply_markup=reply_markup)
    elif option == 'back':
        start(update, context)  # Redirect to main options
    elif option == 'sub_option1_1':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة",  callback_data='sub_option1_1')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'sub_option1_2':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة",  callback_data='sub_option1_2')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)

    elif option == 'sub_option1_3':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة",  callback_data='sub_option1_3')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'sub_option2_1':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='sub_option2_1')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'sub_option2_2':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='sub_option2_2')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)

    elif option == 'sub_option5_1':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='sub_option5_1')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'sub_option5_2':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='sub_option5_2')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'sub_option6_1':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='sub_option6_1')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    elif option == 'sub_option6_2':
        keyboard = [
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='sub_option6_2')],
            [InlineKeyboardButton("◀️ العودة للقائمة الرئيسية", callback_data='back')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        result = get_random_msg(option)

        query.message.reply_text(result['Hebrew'])
        query.message.reply_text('*الترجمة العربية:* \n '+ result['Arabic'], reply_markup=reply_markup)
    else:
        query.message.reply_text("Sorry, I didn't understand that.")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater("6828911861:AAHE4LOUYtkMrm0RXkgvIykLa7-7ADAXee4")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register the handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_click))
        # Every time the back button is pressed, the main_menu fucntion is triggered and the user sees the previous menu
    dispatcher.add_handler(CallbackQueryHandler(button_click, pattern='back'))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    # updater.idle()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

