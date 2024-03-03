import datetime
import logging
import os
import random
import re
import time
from logging.handlers import RotatingFileHandler
from typing import List, Optional, Tuple

import telegram
from fastapi import (BackgroundTasks, Depends, FastAPI, File, Header,
                     HTTPException, Path, Query, UploadFile)
from fastapi.responses import JSONResponse, PlainTextResponse
from telegram import (InlineKeyboardButton, InlineKeyboardMarkup,
                      ReplyKeyboardMarkup, ReplyKeyboardRemove, Update)
from telegram.ext import (CallbackContext, CallbackQueryHandler,
                          CommandHandler, ContextTypes, ConversationHandler,
                          Filters, MessageHandler, Updater, filters)

# configure the log format
formatter  = logging.Formatter('%(asctime)s - %(message)s')


handler = RotatingFileHandler('app.log', maxBytes=1024*1024*10, backupCount=5)
handler.setFormatter(formatter)
# set the logging level to INFO
logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)

# add the handler to the logger
logger = logging.getLogger(__name__)
logger.addHandler(handler)

description = """

## Isnad Scrap - Util API <img src=\'https://flagcdn.com/24x18/ps.png\'> 🔻🔻🔻


Isnad scrap is a powerful tool designed to streamline interactions with the Twitter platform automatically.

The following APIs provide various services for managing user cookies, handling target user IDs, and reading file contents.

**Key Features:**

- **Update Quotes list:**
    Upload file of the quotes, to be presented to the Bot's users. 
    The uploaded file should follow the have the valid name and use `=-*=-*` as a seperator between sentences.

- **Read File Content:**
    Retrieve the content of a specified file, providing each line in a proper format. 
    Ideal for accessing stored information or logs.

**Authentication:**
    
Access to these services is protected by an API key mechanism. Users must provide a valid API key in the request header for authentication.

**How to Use:**
    
- To read file content: Access the `/read-file-content/` endpoint, specifying the file name and providing the API key for authentication.    
 
- To upload ISDNAD Quotes messages: Use the `/update-quotes-list/` endpoint, providing an the required file and ensuring the provided API key is valid.

- To display logs: Access the `/logs/` endpoint.
    



**Obtaining an API Key:**
    
For users requiring an API key, please contact `M Mansour` for assistance.

"""

app = FastAPI(title="Isnad Bot",
              description=description,
              summary="Isnad Scrap - Util API.",
              version="0.0.1", swagger_ui_parameters={"defaultModelsExpandDepth": -1}
              )



API_KEY_ADMIN = "iSLgvYQMFbExJGIVpJHEOEHnYxyzT4Fcr5xfSVG2Sn0q5FcrylK72Pgs3ctg0Cyp"


# Define a dictionary to store the mapping of userid to api_key
user_api_key_map = {
    "user1": "Hw1MXuWmKwsG4UXlRITVvS3vku64a71Thj7Z9lXPvXZ5tuUEsTGAfqT8m8AnNGuo",
    "user2": "ERGZdjZqumtfZccYmpKUGF7KFkRrqATioi6OUXQI8iiVZtG3xiKBfGgPjqgMwdvw",
    "user3": "WbpClFZ2HnsNgbYBwsoYeVFK5iApa71fgSFHA9xE7ca8zjKFw1rOQzohwVOKX",
    "user4": "wRkBnrIMx20TPYRduKsq3SXfc8WkXh0Pj3H0hGYGJsdgSXXxYMzTMk4JUqkyMsl",
    "user5": "AfIZUKMWVNoSDFXCVinHqaFIZnDgEWzDBw2PgubmffcQzUj9Lh5WaTz3ilzFx8Dp",
    "user6": "XQ5ihKJl2GqUvMM8O0Fs06UmZy6d0EeF4u3QLAMVbppzJETTul90PhQh7vI9oC4R",
    "user7": "fEpvjfO0oZr4fb3nc545GdOc3SEhlKfBiNa8ZXFZHTly2duw20C44QZHBCf",
    "user8": "fKrFNeOwapEe7XZXCTRl9ufMZXCYpemjb2VVkS8Z40fYVtgQMC46A26K7o",
    "user9": "wJkclhGS7ROCfZXCcA6ZXCZXOp7sdK5iAp9oZXCZXCYxbA94Xj8EEnTqIEDq",
    "user10": "RpnNbdW9sN8zVddnuZXCFG0I2VMzY2VBI5tnrHhYqVrXiBNkpwjSwyyJf",
    "user11": "SedkImeAadZCloPajo4ekQohXe5yWAi7aZXCVOeYqvI464Uj9cVXhjoVF",
    "user12": "onHGZ9U57aYeRWUiwoIbGCQLO6xZXCHXtW4SimPtas3j8f4K6OPpTVCEh",
    "admin": API_KEY_ADMIN
    # Add more users and their corresponding api keys
}

# Dependency to get the userid based on the provided api_key
async def get_api_key(api_key: str = Header(..., description="API key for authentication")):
    """
    Get User ID

    Retrieves the userid based on the provided API key.

    - **api_key**: API key for authentication.

    Returns the corresponding userid.
    """
    for userid, key in user_api_key_map.items():
        if key == api_key:
            return userid
    raise HTTPException(
        status_code=401,
        detail="Invalid API key",
        headers={"WWW-Authenticate": "Bearer"},
    )

# Dependency to check the admin API key


def get_admin_api_key(api_key: str = Header(..., description="Admin API key for authentication")):
    if api_key != API_KEY_ADMIN:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin API key",
        )
    return api_key


@app.get("/", include_in_schema=False)
def read_root():
    return {"Isnad Quotes": "✌️ 🇵🇸🔻🔻🔻"}



# Define a function to check if the file is a text file
def is_text_file(file: UploadFile):
    if not file.content_type.startswith("text/"):
        raise HTTPException(
            status_code=400,
            detail="Only text files are allowed",
        )



# Log viewer
@app.get("/logs", response_class=PlainTextResponse)
async def read_logs(api_key: str = Depends(get_api_key)):
    """
    View Application Logs

    Displays the application logs.

    Returns logs.
    """
    try:
        with open("app.log", "r", encoding="utf-8") as file:
            logs = file.readlines()

        # Reverse the order of logs to get the most recent entries first
        logs.reverse()

        content = "".join(logs)
        return content
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File app.log not found.",
        )



@app.get("/read-file-content/", response_class=PlainTextResponse)
async def read_file_content(
    file_name: str = Query(..., title="File Name",
                           description="Name of the file to read."),
    api_key: str = Depends(get_api_key),
):
    """
    Read File Content

    Reads the content of the specified file and responds with each line in proper format.

    - **file_name**: Name of the file to read, including the extension, ex: .txt.
    - **api_key**: API key for authentication.

    Returns the content of the file as plain text.
    """
    try:
        with open(file_name, "r", encoding='utf-8') as file:
            content = file.read()

        logger.info('Request from UserID: ' +
                    str(api_key) + '- read file '+file_name)
        return content
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File '{file_name}' not found.",
        )

@app.post("/update-quotes-list/")
async def upload_quotes_replies(
        file: UploadFile = File(...,
                                description="Upload a text file containing the list of replies."),
        api_key: str = Depends(get_api_key)):

    """
    Upload tweets replies

    Update the list of replies, which will be used to reply to the recent tweets of targeted users.

    - **file**: List of tweets replies, the format should be one reply in each line
    - **api_key**: API key for authentication.
    - **replace_existing**: Whether to replace existing content in tweets_replies_list.txt.

    """

    contents = await file.read()

    # Decode contents and split it into lines
    lines = contents.decode("utf-8").splitlines()
    replace_existing = False
    # Open file in append mode or write mode based on replace_existing flag
    mode = "w" if replace_existing else "a"

    # Append or replace content in the existing file "tweets_replies_list.txt"
    with open("tweets_replies_list.txt", mode, encoding="utf-8") as offline_file:
        for line in lines:
            if line.strip():  # Ignore empty lines
                offline_file.write(line + "\n")

    action = "Replaced" if replace_existing else "Appended"
    logger.info('Request from UserID: '+api_key +
                ' - File content '+action+' in tweets_replies_list.txt')
    return JSONResponse(content={"message": f"File content {action} in tweets_replies_list.txt"}, status_code=200)




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


# Global dictionary to store used messages for each file
used_messages = {}

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

        if line == '=-*=-*':
            if current_pair:
                pairs.append(current_pair)
            current_pair = []
            continue

        current_pair.append(line)

    if current_pair:
        pairs.append(current_pair)

    return pairs

def get_random_msg(file_name):
    global used_messages

    # Check if used_messages dictionary has an entry for the given file
    if file_name not in used_messages:
        # If not, initialize it with an empty list
        used_messages[file_name] = []

    file_path = file_name + '.txt'
    text = read_text_file(file_path)
    pairs = get_pairs(text)

    # Shuffle the pairs to ensure randomness
    random.shuffle(pairs)

    # Try to find an unused pair
    for pair in pairs:
        if pair not in used_messages[file_name]:
            # If found, mark it as used and return it
            used_messages[file_name].append(pair)
            return {
                'Hebrew': '\n'.join(pair[0:len(pair)//2]),
                'Arabic': '\n'.join(pair[len(pair)//2:])
            }

    # If all pairs are used, start over
    used_messages[file_name] = []
    # Call the function recursively to get a new pair
    return get_random_msg(file_name)


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
            [InlineKeyboardButton("🔄 رسالة جديدة", callback_data='option4')],
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
        query.message.reply_text("برجاء إختيار إحد الخيارات من القائمة الرئيسية")


def main() -> None:
    """Run the bot."""
    # Create the Updater and pass it your bot's token
    updater = Updater("6845309288:AAH-XFFL1bzWalLeyT2EMS3JkDyUjrjVO1s")

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
