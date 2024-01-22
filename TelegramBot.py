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
    main()



def background_task(background_tasks: BackgroundTasks):
    while is_task_running:
        background_tasks.add_task(main)
        time.sleep(10)  # Sleep for 10 seconds between iterations


# Stop the main logic function at shutdown
@app.on_event("shutdown")
async def shutdown_event():
    global is_task_running
    is_task_running = False

# Set to keep track of processed TaskIds
processed_task_ids = set()

def main():
    print(f"Now We check the Nodes")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
