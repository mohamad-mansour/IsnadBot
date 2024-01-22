import os
import time
import datetime
import random
from fastapi import FastAPI, BackgroundTasks, HTTPException

app = FastAPI()

# Variable to control the task execution
is_task_running = False



@app.get("/")
def read_root():
    return {"Welcome ": "IsnadTWitterBot Node1..."}

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


# Set to keep track of processed TaskIds
processed_task_ids = set()

def main():
    print(f"Now We check the Nodes")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
