from typing import List, Tuple
import datetime
import os
import random
import re
import time
from typing import Optional, List

import telegram
from fastapi import BackgroundTasks, FastAPI, HTTPException
from telegram import Update
from telegram.ext import (CallbackContext, CommandHandler, Filters,
                          MessageHandler, Updater)

from account import Account

app = FastAPI()

# Variable to control the task execution
is_task_running = False

bot_token = '6828911861:AAE-BrDA6_HpF3iLbzwunke3CXC529K9SbY'

@app.get("/")
def read_root():
    return {"Welcome ": "IsnadTWitterBot..."}

@app.on_event("startup")
async def startup_event():
    print('Main Server started---- :', datetime.datetime.now())
    global is_task_running
    is_task_running = True
    # while is_task_running:
    
    # time.sleep(10)  # Sleep for 10 seconds between iterations
    try:
        main()
        pass
    except telegram.error.Conflict as e:
        print(f"Telegram Conflict Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")



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

class TweetResult:
    def __init__(self, user: str, tweet_url: Optional[str] = None, error_message: Optional[str] = None):
        self.user = user
        self.tweet_url = tweet_url
        self.error_message = error_message

class MediaObject:
    def __init__(self, file_id, file_type, messages):
        self.file_id = file_id
        self.file_type = file_type
        self.messages = messages

class TwitterCookiesManager:
    def __init__(self, cookies_file_path: str):
        with open(cookies_file_path, 'r') as cookies_file:
            self.twitter_cookies = [line.strip().split('|') for line in cookies_file]

        self.used_messages = {}
        self.un_used_messages = {}
        self.used_users = set()

    def get_random_twitter_cookies_group(self, media_objects: List[MediaObject]) -> List[List[Tuple[str, str, str]]]:
        groups_count = len(media_objects)
        random_twitter_cookies = random.sample(self.twitter_cookies, len(self.twitter_cookies))

        twitter_cookies_groups = []
        start_index = 0

        for i, media_object in enumerate(media_objects):
            # print('media_object enum:',media_object.file_id)
            if i == groups_count - 1:
                group = random_twitter_cookies[start_index:]
            else:
                group_size = len(random_twitter_cookies) // groups_count
                group = random_twitter_cookies[start_index:start_index + group_size]
                start_index += group_size

            twitter_cookies_groups.append(group)

        return twitter_cookies_groups
    
    def get_random_message(self, media_object: MediaObject, user: str) -> str:
        if not self.un_used_messages:
            self.un_used_messages = list(media_object.messages)

        random_message = random.choice(self.un_used_messages)
        self.un_used_messages.remove(random_message)
        return random_message


# Set to keep track of processed TaskIds
processed_task_ids = set()
media_groups: List[Update] = []

def handle_new_message(update: Update, context: CallbackContext) -> None:
    # This function will be called when a new message is received in the specified channel
    global media_groups
    if update.channel_post.text:
        # Text message
        print('Task here text:',update.channel_post.text_html)
        text_message = update.channel_post.text_html
        start_task = text_message.find('/start')
        if start_task != -1:
            context.bot.send_message(chat_id=-1001998206357, text='Task started. Send media or use /finish to finish.')
        else:
            context.bot.send_message(chat_id=-1001998206357, text='Task will proceed soon, we will notify you once finished. Thank you!')
            # Process the media group here
            process_media_group(media_groups,context)

            # Clear the media group information after processing
            media_groups = []

    elif update.channel_post.photo:
        media_groups.append(update)
    
    elif update.channel_post.video:
        media_groups.append(update)
  
# Function to process the media group
def process_media_group(updates: List[Update], context: CallbackContext) -> None:
    # Create an instance of TwitterCookiesManager
    twitter_cookies_manager = TwitterCookiesManager(cookies_file_path='twitter_cookies.txt')

    # List to store MediaObject instances
    media_objects = []

    # Process the media group here
    # You can iterate through updates and handle them as needed
    for update in updates:
        if update.channel_post.photo:
            # Image message
            text_message = update.channel_post.caption
            file_id = update.channel_post.photo[-1].file_id  # get the file id of the last photo in the message
            file = context.bot.get_file(file_id) # get the file object
            file.download(f"image_{file_id}.jpg") # download the file to a local file with the same name as the file id

            file_type = 'image'

            # Extract caption messages
            messages = extract_caption_messages(text_message)

            # Create a MediaObject instance and add it to the list
            media_object = MediaObject(file_id, file_type, messages)
            media_objects.append(media_object)

        elif update.channel_post.video:
            # Video message
            text_message = update.channel_post.caption
            file_id = update.channel_post.video.file_id  # get the file id of the last video in the message
            file = context.bot.get_file(file_id) # get the file object
            file.download(f"video_{file_id}.MP4") # download the file to a local file with the same name as the file id
            file_type = 'video'

            # Extract caption messages
            messages = extract_caption_messages(text_message)

            # Create a MediaObject instance and add it to the list
            media_object = MediaObject(file_id, file_type, messages)
            media_objects.append(media_object)

    twitter_cookies_manager = TwitterCookiesManager(cookies_file_path='twitter_cookies.txt')

    random_twitter_cookies_group = twitter_cookies_manager.get_random_twitter_cookies_group(media_objects)
    # Create an empty list to store TweetResult objects
    tweet_results_list = []
    # Initialize an empty string to store the results
    results_message = ""
    for group, media_object in zip(random_twitter_cookies_group, media_objects):
        for user in group:
            random_message = twitter_cookies_manager.get_random_message(media_object, user[2])
            # print(f"media_object  {media_object} with file_type: {media_object.file_type}")
            # print(f"Sending tweet for user {user[2]} with message: {random_message} and media file: {media_object.file_id}")
            filename = ''
            # Known filename in the current directory
            if media_object.file_id:
                if media_object.file_type =='image':
                    filename = os.path.join(os.getcwd(), f"image_{media_object.file_id}.jpg")
                else:
                    filename = os.path.join(os.getcwd(), f"video_{media_object.file_id}.MP4")
            tweet_result = send_tweet(user[0], user[1], f"{random_message}",user[2],filename)
            tweet_results_list.append(tweet_result)
            # Append the result to the results_message
            if tweet_result.tweet_url:
                results_message += f"Success! User {tweet_result.user} tweeted. URL: {tweet_result.tweet_url}\n"
            elif tweet_result.error_message:
                results_message += f"Error! User {tweet_result.user}, {tweet_result.error_message} \n"
            # Introduce random delays between API requests
            random_delay = random.uniform(25, 50)
            time.sleep(random_delay)
        if media_object.file_id:
            os.remove(filename)

    # Notify the User about the results of the task  
    context.bot.send_message(chat_id=-1001998206357, text=f"Task finsihed, and the results:\n\n{results_message}")
    media_groups.clear()
    media_objects.clear()



def extract_caption_messages(text_message: str) -> List[str]:
    # Use regex to find the pattern "MessageX:" and extract the text following it
    pattern = re.compile(r'Message\d+:(.*?)(?=Message\d+|$)', re.DOTALL)
    messages = pattern.findall(text_message)

    # Remove leading and trailing whitespaces from each message
    messages = [message.strip() for message in messages]

    return messages

def extract_rest_id_and_format_url(response):
    try:
        rest_id = response["data"]["create_tweet"]["tweet_results"]["result"]["rest_id"]
        formatted_url = f"https://twitter.com/itdoesnotmatter/status/{rest_id}"
        return formatted_url
    except KeyError:
        return None  # Handle the case where the required key is not present in the response

# Function to send tweets using auth_token_value, ct0_value, and plain_text
def send_tweet(auth_token_value, ct0_value, random_message, user, filename) -> TweetResult:
    hashtags = ["#BringThemHomeNow", "#Bringthemhome", "#WeWillNotStopUntilTheyAreAllBack" ,
                "#captured_oct7", "#Israel", "#hostages", "#MeTooUNlessYoureAJew",
                "#BringThemAllHomeNow", "#HamasTerrorists", "#BringThemHome",
                "#100Days", "#KfirBibas", "#KfirOneYear"]
    tweet_content = f"{random_message} {random.choice(hashtags)} {random.choice(hashtags)}"
    try:
        account = Account(cookies={"ct0": ct0_value, "auth_token": auth_token_value})
        if filename:
            tweet_result = account.tweet(tweet_content,media=[{'media': filename, 'alt': random_message}])
        else :
            tweet_result = account.tweet(tweet_content)
        pass
        tweet_url = extract_rest_id_and_format_url(tweet_result)
        # return f"{user} finsihed, URL {tweet_url} \n"
        return TweetResult(user=user, tweet_url=tweet_url)
    except Exception as e:
        print(f"Exception in send_tweet Error: {e}")
        # return f"Task failed for user: {user}, Error details {e} \n"
        return TweetResult(user=user, error_message=f"{e}")
        # raise HTTPException(status_code=500, detail="Internal server error")


def main():
    # Create the Updater and pass it your bot's token
    updater = Updater(bot_token, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))

    # Register message handler for all messages in the specified channel
    dp.add_handler(MessageHandler(Filters.chat(-1001998206357), handle_new_message))

    # Start the Bot
    updater.start_polling(timeout=600)

    # Run the bot until you send a signal to stop it
    # updater.idle()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
