import random
import time
from datetime import datetime, timedelta, timezone

import pytz
from fastapi import BackgroundTasks, FastAPI, HTTPException

from account import Account
from scraper import Scraper


app = FastAPI()

# Variable to control the task execution
is_task_running = False

@app.get("/")
def read_root():
    return {"Welcome ": "Node1 - Scrapper..."}

@app.on_event("startup")
async def startup_event():
    print('Node1 Server started---- :', datetime.now())
    global is_task_running
    is_task_running = True
    main()

# Stop the main logic function at shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global is_task_running
    is_task_running = False

reply_cookie_file_path = 'twitter_reply_cookies.txt'
scrap_cookie_file_path = 'twitter_scrap_cookies.txt'
target_ids_file = 'target_user_ids.txt'

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
    # Run the function every hour
    while True:
        scraper = initialize_scraper()
        latest_entries_list = get_user_last_tweets(scraper, TweetEntry)
        # # Print details
        for index, entry in enumerate(latest_entries_list, start=1):
            # print(f"Entry {index}: rest_id: {entry.rest_id}, is_edit_eligible: {entry.is_edit_eligible} , created_at: {entry.created_at}")
            time_difference_minutes = get_time_difference_in_minutes(entry.created_at)
            print(f"Time difference: {time_difference_minutes}")
            # Tweet less than 5 minutes, means it's new, we will reply
            if time_difference_minutes < 10:
                print(f"Entry {index}: rest_id: {entry.rest_id}, is_edit_eligible: {entry.is_edit_eligible} , created_at: {entry.created_at}")
                send_reply( entry.rest_id)
        time.sleep(3600)  # Sleep for 1 hour (3600 seconds)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
