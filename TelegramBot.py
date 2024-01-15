import logging
import os
import time
import datetime
from fastapi import FastAPI, BackgroundTasks
from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)
from twitter.account import Account

app = FastAPI()

# Variable to control the task execution
is_task_running = False
# Set up logging
# logging.basicConfig(level=logging.ERROR)
# logger = logging.getLogger(__name__)

bot_token = '6875496830:AAE0TKZjtA2xYzsochdmALHGW1_j6RCqrlk'

@app.get("/")
def read_root():
    return {"Hello": "World!!!--------****-"}

@app.on_event("startup")
async def startup_event():
    print('Main Server started---- :', datetime.datetime.now())
    global is_task_running
    is_task_running = True
    # while is_task_running:
    main()
    # time.sleep(10)  # Sleep for 10 seconds between iterations



def background_task(background_tasks: BackgroundTasks):
    while is_task_running:
        # Your background task logic goes here
        # You can use existing functions like get_user_last_tweet or tweet_one_hour
        background_tasks.add_task(main)
        time.sleep(10)  # Sleep for 10 seconds between iterations


# Stop the main logic function at shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global is_task_running
    is_task_running = False

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Hello! This is your bot again.')


# Set to keep track of processed TaskIds
processed_task_ids = set()

def handle_new_message(update: Update, context: CallbackContext) -> None:
    # This function will be called when a new message is received in the specified channel
    file_id = ''
    if update.channel_post.text:
        # Text message
        text_message = update.channel_post.text_html
        # print(f"Text message: {text_message}")

    elif update.channel_post.photo:
        # Image message
        text_message = update.channel_post.caption
        # print(f"Image caption: {text_message}")
        file_id = update.channel_post.photo[-1].file_id # get the file id of the last photo in the message
        file = context.bot.get_file(file_id) # get the file object
        file.download(f"image_{file_id}.jpg") # download the file to a local file with the same name as the file id
        
    # Extract TaskId from the message
    task_id_start = text_message.find('TaskId:')
    if task_id_start != -1:
        task_id_end = text_message.find('\n', task_id_start)
        if task_id_end != -1:
            task_id = text_message[task_id_start + len('TaskId:'):task_id_end].strip()
            # Check if TaskId has been processed before
            if task_id not in processed_task_ids:
                # Extract the plain text line after the id
                text_start = task_id_end + 1
                plain_text = text_message[text_start:].strip()

                # Process the plain text as needed
                print(f"New TaskId: {task_id}, Plain Text: {plain_text}")
                
                # Add the TaskId to the set of processed TaskIds
                processed_task_ids.add(task_id)

                # Add new tweets using the task
                   # Now, read Twitter cookies from 'twitter_cookies.txt' and send a tweet for each set of cookies
                with open('twitter_cookies.txt', 'r') as cookies_file:
                    for line in cookies_file:
                        auth_token_value, ct0_value, user = line.strip().split('|')
                        filename = ''
                        # Known filename in the current directory
                        if file_id:
                            filename = os.path.join(os.getcwd(), f"image_{file_id}.jpg")

                        # Assuming you have a function to send tweets
                        send_tweet(auth_token_value, ct0_value, plain_text,user,task_id,filename)

                        # Sleep for 10 seconds between each set of cookies
                        time.sleep(10)
                if file_id:
                    os.remove(filename)


# Function to send tweets using auth_token_value, ct0_value, and plain_text
def send_tweet(auth_token_value, ct0_value, plain_text,user,task_id,filename):
    account = Account(cookies={"ct0": ct0_value, "auth_token": auth_token_value})
    if filename:
        account.tweet(plain_text,media=[{'media': filename, 'alt': plain_text}])
    else :
         account.tweet(plain_text)
    # print(f"New TaskId: {task_id}, Finished for user: {user}")
    print(f"New TaskId: {task_id}, Finished for user: {user}")


def main():
    # Create the Updater and pass it your bot's token
    updater = Updater(bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))

    # Register message handler for all messages in the specified channel
    dp.add_handler(MessageHandler(Filters.chat(-1002145816659), handle_new_message))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you send a signal to stop it
    updater.idle()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
