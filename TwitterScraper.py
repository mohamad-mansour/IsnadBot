import logging
import random
import time
from datetime import datetime, timedelta, timezone
import pytz
from typing import List
from fastapi import BackgroundTasks, FastAPI, HTTPException,File, Depends, UploadFile, Header,Query
from account import Account
from scraper import Scraper
from fastapi.security import APIKeyHeader
from fastapi.responses import JSONResponse,PlainTextResponse,HTMLResponse
from fastapi.background import BackgroundTasks
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)


description = """

## Isnad Scrap - Util API <img src=\'https://flagcdn.com/24x18/ps.png\'> 🔻🔻🔻


Isnad scrap is a powerful tool designed to streamline interactions with the Twitter platform automatically.

The following APIs provide various services for managing user cookies, handling target user IDs, and reading file contents.

**Key Features:**

- **Upload Main User Cookies:**
    Upload the main Twitter user cookies responsible for actions like replying to or liking tweets. 
    The uploaded file should follow the format: `auth_token_value|ct0_value|username`, with each record on a new line.

- **Upload Scrap Cookies:**
    Update the list of scrap Twitter user cookies, specifically used for searching recent tweets. 
    The file format should match that of main user cookies.

- **Upload Target User IDs:**
    Maintain a list of target Twitter user IDs, exclusively used for searching recent tweets. 
     Each line in the uploaded file should represent a Twitter user ID.

- **Read File Content:**
    Retrieve the content of a specified file, providing each line in a proper format. 
    Ideal for accessing stored information or logs.

**Authentication:**
    
Access to these services is protected by an API key mechanism. Users must provide a valid API key in the request header for authentication.

**How to Use:**
    
- To upload main user cookies: Use the `/upload-reply-cookie/` endpoint with the appropriate API key.
    
- To upload scrap cookies: Utilize the `/upload-scrap-cookie/` endpoint with the correct API key.
    
- To upload target user IDs: Use the `/upload-target-ids/` endpoint, ensuring the provided API key is valid.
    
- To read file content: Access the `/read-file-content/` endpoint, specifying the file name and providing the API key for authentication.

    



**Obtaining an API Key:**
    
For users requiring an API key, please contact `M Mansour` for assistance.

"""

app = FastAPI(title="Isnad Bot" ,
    description=description,
    summary="Isnad Scrap - Util API.",
    version="0.0.1",swagger_ui_parameters={"defaultModelsExpandDepth": -1}
)

# Configure logging to a file
logging.basicConfig(filename="app.log", level=logging.INFO)

# Variable to control the task execution
is_task_running = False

API_KEY_ADMIN = "your-secret-key-admin"  # Replace with your secret key

reply_cookie_file_path = 'twitter_reply_cookies.txt'
scrap_cookie_file_path = 'twitter_scrap_cookies.txt'
target_ids_file = 'target_user_ids.txt'


# Define a dictionary to store the mapping of userid to api_key
user_api_key_map = {
    "user1": "api_key_1",
    "user2": "api_key_2",
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
    return {"Isnad ": "Scrapper🔻🔻🔻"}


@app.on_event("startup")
async def startup_event():
    print('Node Scrapper Server started---- :', datetime.now())


# Define a function to check if the file is a text file
def is_text_file(file: UploadFile):
    if not file.content_type.startswith("text/"):
        raise HTTPException(
            status_code=400,
            detail="Only text files are allowed",
        )


@app.get("/read-file-content/", response_class=PlainTextResponse)
async def read_file_content(
    file_name: str = Query(..., title="File Name", description="Name of the file to read."),
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
        with open(file_name, "r") as file:
            content = file.read()
        logging.info(f"User: {api_key} - read file {file_name}")
        return content
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File '{file_name}' not found.",
        )

# reply_cookie_file_path = 'twitter_reply_cookies.txt'
@app.post("/upload-reply-cookie/")
async def upload_reply_cookie(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key),
    replace_existing: bool = Query(default=False, description="Whether to replace existing content in twitter_reply_cookies.txt"),_: bool = Depends(is_text_file),):

    """
    Upload main user Cookies

    Update the list the main Twitter user cookies, who will reply/like the tweets.

    - **file**: List of main Twitter user cookies, the format should be auth_token_value|ct0_value|username, one record in each line. 
    - **api_key**: API key for authentication.
    - **replace_existing**: Whether to replace existing content in twitter_reply_cookies.txt.

    """
    
    contents = await file.read()

    # Decode contents and split it into lines
    lines = contents.decode("utf-8").splitlines()

    # Open file in append mode or write mode based on replace_existing flag
    mode = "w" if replace_existing else "a"

    # Append or replace content in the existing file "twitter_reply_cookies.txt"
    with open("twitter_reply_cookies.txt", mode, encoding="utf-8") as offline_file:
        for line in lines:
            if line.strip():  # Ignore empty lines
                offline_file.write(line + "\n")

    action = "Replaced" if replace_existing else "Appended"
    logging.info(f"User: {api_key} - File content {action} in twitter_reply_cookies.txt")
    return JSONResponse(content={"message": f"File content {action} in twitter_reply_cookies.txt"}, status_code=200)


# scrap_cookie_file_path = 'twitter_scrap_cookies.txt'
@app.post("/upload-scrap-cookie/")
async def upload_scrap_cookie(
    file: UploadFile = File(...,title="Scrap Twitter Accounts", description="List of scrap Twitter user cookies, who will only be used for searching recent tweets."),
    api_key: str = Depends(get_api_key),
    replace_existing: bool = Query(default=False, description="Whether to replace existing content in twitter_scrap_cookies.txt"),_: bool = Depends(is_text_file),):

    """
    Upload scrap Cookies

    Update the list of scrap Twitter user cookies, who will only be used for searching recent tweets.

    - **file**: List of scrap Twitter user cookies, the format should be auth_token_value|ct0_value|username, one record in each line. 
    - **api_key**: API key for authentication.
    - **replace_existing**: Whether to replace existing content in twitter_scrap_cookies.txt.

    """
        
    
    contents = await file.read()

    # Decode contents and split it into lines
    lines = contents.decode("utf-8").splitlines()

    # Open file in append mode or write mode based on replace_existing flag
    mode = "w" if replace_existing else "a"

    # Append or replace content in the existing file "twitter_scrap_cookies.txt"
    with open("twitter_scrap_cookies.txt", mode, encoding="utf-8") as offline_file:
        for line in lines:
            if line.strip():  # Ignore empty lines
                offline_file.write(line + "\n")

    action = "Replaced" if replace_existing else "Appended"
    logging.info(f"User: {api_key} - File content {action} in twitter_scrap_cookies.txt")
    return JSONResponse(content={"message": f"File content {action} in twitter_scrap_cookies.txt"}, status_code=200)


# target_ids_file = 'target_user_ids.txt'
@app.post("/upload-target-ids/")
async def upload_target_ids(
    file: UploadFile = File(..., description="Upload a text file containing reply cookies for Twitter."),
    api_key: str = Depends(get_api_key),
    replace_existing: bool = Query(default=False, description="Whether to replace existing content in target_user_ids.txt"),_: bool = Depends(is_text_file),):

    
    """
    Upload target ids

    Update the list of target Twitter Ids, who will only be used for searching recent tweets.

    - **file**: List of target Twitter user Ids, the format should be twitter user id in each line
    - **api_key**: API key for authentication.
    - **replace_existing**: Whether to replace existing content in target_user_ids.txt.

    """


    contents = await file.read()

    # Decode contents and split it into lines
    lines = contents.decode("utf-8").splitlines()

    # Open file in append mode or write mode based on replace_existing flag
    mode = "w" if replace_existing else "a"

    # Append or replace content in the existing file "target_user_ids.txt"
    with open("target_user_ids.txt", mode, encoding="utf-8") as offline_file:
        for line in lines:
            if line.strip():  # Ignore empty lines
                offline_file.write(line + "\n")

    action = "Replaced" if replace_existing else "Appended"
    logging.info(f"User: {api_key} - File content {action} in target_user_ids.txt")
    return JSONResponse(content={"message": f"File content {action} in target_user_ids.txt"}, status_code=200)



# target_ids_file = 'tweets_replies_list.txt'
@app.post("/tweets-replies-list/")
async def upload_tweets_replies(
    file: UploadFile = File(..., description="Upload a text file containing the list of replies."),
    api_key: str = Depends(get_api_key),
    replace_existing: bool = Query(default=False, description="Whether to replace existing content in tweets_replies_list.txt"),_: bool = Depends(is_text_file),):

    
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

    # Open file in append mode or write mode based on replace_existing flag
    mode = "w" if replace_existing else "a"

    # Append or replace content in the existing file "tweets_replies_list.txt"
    with open("tweets_replies_list.txt", mode, encoding="utf-8") as offline_file:
        for line in lines:
            if line.strip():  # Ignore empty lines
                offline_file.write(line + "\n")

    action = "Replaced" if replace_existing else "Appended"
    logging.info(f"User: {api_key} - File content {action} in tweets_replies_list.txt")
    return JSONResponse(content={"message": f"File content {action} in tweets_replies_list.txt"}, status_code=200)



# Log viewer
@app.get("/logs", response_class=PlainTextResponse)
async def read_logs(api_key: str = Depends(get_api_key)):
    """
    View Application Logs

    Displays the application logs.

    Returns logs.
    """
    try:
        with open("app.log", "r") as file:
            content = file.read()
        return content
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"File app.log not found.",
        )


def start_scrap_background():
    global is_task_running
    is_task_running = True
    main() 

@app.get("/start-scrap")
async def start_scrap(background_tasks: BackgroundTasks,api_key: str = Depends(get_admin_api_key)):
    background_tasks.add_task(start_scrap_background)
    return {"message": "Scrapper will start in the background..."}


@app.get("/stop-scrap")
async def start_scrap(background_tasks: BackgroundTasks,api_key: str = Depends(get_admin_api_key)):
    global is_task_running
    is_task_running = False
    return {"message": "Scrapper will stop now..."}


def get_time_difference_in_minutes(tweet_created_at):
    # Convert the tweet's creation time to a datetime object without timezone
    tweet_time_naive = datetime.strptime(tweet_created_at, '%a %b %d %H:%M:%S +0000 %Y').replace(tzinfo=None)

    # Set the timezone for the tweet's creation time to UTC
    tweet_time_utc = tweet_time_naive.replace(tzinfo=timezone.utc)

    # Get the current UTC time
    current_time_utc = datetime.now(timezone.utc)

    # Calculate the time difference
    time_difference = current_time_utc - tweet_time_utc

    # Calculate the time difference in minutes
    time_difference_minutes = time_difference.total_seconds() / 60

    return time_difference_minutes


class TweetEntry:
    def __init__(self, entry):
        self.rest_id = entry['content']['itemContent']['tweet_results']['result']['rest_id']
        self.created_at = entry['content']['itemContent']['tweet_results']['result']['legacy']['created_at']
        # Extract is_edit_eligible values
        is_edit_eligible1 = extract_is_edit_eligible(entry['content']['itemContent']['tweet_results']['result']['edit_control'])
        self.is_edit_eligible = is_edit_eligible1

def extract_is_edit_eligible(obj):
    if 'is_edit_eligible' in obj:
        return obj['is_edit_eligible']
    elif 'edit_control_initial' in obj and 'is_edit_eligible' in obj['edit_control_initial']:
        return obj['edit_control_initial']['is_edit_eligible']
    else:
        return None



# Initialize used_user_rest_ids as an empty set
used_user_rest_ids = set()

def get_user_last_tweets(scraper, TweetEntry):
    # Read user_rest_ids from a text file
    with open(target_ids_file, 'r', encoding='utf-8') as file:
        user_rest_ids = [line.strip() for line in file]

    # Shuffle the list to get a random order
    random.shuffle(user_rest_ids)

    latest_entries = []

    for user_rest_id in user_rest_ids:
        # Check if user_rest_id has already been used
        if user_rest_id not in used_user_rest_ids:
            try:
                tweetsScrap = scraper.tweets([user_rest_id])
                
                # Check for rate limit exceeded error
                if 'errors' in tweetsScrap and tweetsScrap['errors'][0]['code'] == 88:
                    print(f"Rate limit exceeded. Unable to retrieve tweets for user_rest_id: {user_rest_id}")
                    break  # Stop the script when rate limit exceeded

                is_pin_included = len(tweetsScrap[0]['data']['user']['result']['timeline_v2']['timeline']['instructions'])

                if is_pin_included == 3:
                    for entry in tweetsScrap[0]['data']['user']['result']['timeline_v2']['timeline']['instructions'][2]['entries']:
                        if entry['content']['entryType'] in {'TimelineTimelineItem'}:
                            tweet_entry = TweetEntry(entry)
                            if tweet_entry.is_edit_eligible:
                                latest_entries.append(tweet_entry)
                                # Mark user_rest_id as used
                                used_user_rest_ids.add(user_rest_id)
                                break  # Break the loop after processing one user_rest_id
                else:
                    for entry in tweetsScrap[0]['data']['user']['result']['timeline_v2']['timeline']['instructions'][1]['entries']:
                        if entry['content']['entryType'] in {'TimelineTimelineItem'}:
                            tweet_entry = TweetEntry(entry)
                            if tweet_entry.is_edit_eligible:
                                latest_entries.append(tweet_entry)
                                # Mark user_rest_id as used
                                used_user_rest_ids.add(user_rest_id)
                                break  # Break the loop after processing one user_rest_id
            except Exception as e:
                print(f"An error occurred while processing user_rest_id {user_rest_id}: {str(e)}")
                

    return latest_entries

# Function to send tweets using auth_token_value, ct0_value, and plain_text
def send_reply(tweet_id):

    # Read tweets from a text file
    with open('tweets_replies_list.txt', 'r', encoding='utf-8') as file:
        replies = [line.strip() for line in file]

    # Shuffle the list to get a random order
    random.shuffle(replies)
    
    # Read cookies from the file
    with open(reply_cookie_file_path, 'r') as cookie_file:
        cookie_data = [line.strip().split('|') for line in cookie_file]

    # Shuffle the list to get a random order
    random.shuffle(cookie_data)
    
    hashtags = ["#BringThemHomeNow", "#Bringthemhome", "#WeWillNotStopUntilTheyAreAllBack" ,
                "#captured_oct7", "#Israel", "#hostages", "#MeTooUNlessYoureAJew",
                "#BringThemAllHomeNow", "#HamasTerrorists", "#BringThemHome",
                "#100Days", "#KfirBibas", "#KfirOneYear"]
    tweet_content = f" {random.choice(replies)}   {random.choice(hashtags)} {random.choice(hashtags)}"
    try:
        account = Account(cookies={"ct0": cookie_data[0][1], "auth_token": cookie_data[0][0]})
        account.reply(tweet_content, tweet_id=tweet_id)
        print(f"{cookie_data[0][2]} finsihed reply on tweet {tweet_id}")
        pass
    except Exception as e:
        print(f"Exception in send_tweet Error: {e}")
        account = Account(cookies={"ct0": cookie_data[1][1], "auth_token": cookie_data[1][0]})
        account.reply(tweet_content, tweet_id=tweet_id)




def initialize_scraper()-> Scraper:
    # Read cookies from the file
    with open(scrap_cookie_file_path, 'r') as scrap_cookie_file:
        scrap_cookie_data = [line.strip().split('|') for line in scrap_cookie_file]

    random.shuffle(scrap_cookie_data)
    # Loop over each pair of ct0 and auth_token
    for auth_token, ct0, user in scrap_cookie_data:
        try:
            print('user:'+user)
            scraper = Scraper(cookies={"ct0": ct0, "auth_token": auth_token})
            tweets = scraper.tweets_by_id([1749760475204554824])
            # Initialize a new scraper object in case of an error
            if 'errors' in tweets[0] :
                initialize_scraper()
            else:
                return scraper
        except Exception as e:
            print(f"Exception in initialize_scraper Error: {e}")


def main():
    # print('Run the function every hour')
    # Run the function every hour
    while is_task_running:
        scraper = initialize_scraper()
        latest_entries_list = get_user_last_tweets(scraper, TweetEntry)
        # # Print details
        for index, entry in enumerate(latest_entries_list, start=1):
            # print(f"Entry {index}: rest_id: {entry.rest_id}, is_edit_eligible: {entry.is_edit_eligible} , created_at: {entry.created_at}")
            time_difference_minutes = get_time_difference_in_minutes(entry.created_at)
            print(f"Time difference: {time_difference_minutes}")
            # Tweet less than 5 minutes, means it's new, we will reply
            if time_difference_minutes < 5:
                print(f"Entry {index}: rest_id: {entry.rest_id}, is_edit_eligible: {entry.is_edit_eligible} , created_at: {entry.created_at}")
                send_reply( entry.rest_id)
        time.sleep(3600)  # Sleep for 1 hour (3600 seconds)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
