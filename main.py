import requests
import os
from dotenv import load_dotenv
from datetime import date, timedelta, datetime
import time
import numpy as np

import pandas as pd
load_dotenv('cookies.env')
NYT_COOKIE = os.getenv('NYT_COOKIE')

# Open a completed mini crossword page and open DevTools Network Tab, turn on disable cache and filter by term "svc/c"
# Select the json file with just the puzzle id, usually five numbers "22222.json"
# Locate the Cookie header from DevTools, copy the whole string after "cookie:"
# Save in env variable if using publicly
# Cookies seem to last a day or so, so long as the initilal browser used is kept open
COOKIE_HEADER = NYT_COOKIE

BASE_MINI_DATE = datetime.strptime('2023/01/01', "%Y/%m/%d")
BASE_PUZZLE_ID = 20818 # I Just chose 2023-01-01 as the base it increments by 1 each time so it should be fine 


# Here choose your start and end date following the format 'YYYY/MM/DD'
mini_start_date = '2023/01/01'
mini_end_date = '2023/12/31'


# getting starting puzzle id's  
mini_start_date = datetime.strptime(mini_start_date, "%Y/%m/%d")
mini_end_date = datetime.strptime(mini_end_date, "%Y/%m/%d")
mini_dates_delta = (mini_end_date - mini_start_date).days + 1


starting_mini_id = BASE_PUZZLE_ID + (mini_start_date - BASE_MINI_DATE).days



def get_time(dt,pid):
    url = f"https://www.nytimes.com/svc/crosswords/v6/game/{pid}.json"
    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
            "Referer": f"https://www.nytimes.com/crosswords/game/mini/{dt}",
            "Cookie": COOKIE_HEADER,
        },
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    solved = data['calcs'].get('solved')
    time = data["calcs"].get("secondsSpentSolving")
    return [solved,time,dt,pid]


def list_puzzles(date_start, date_end, publish_type):
    url = "https://www.nytimes.com/svc/crosswords/v3/36569100/puzzles.json"
    req_limit = 50  # days per request (inclusive chunk below uses 49)

    all_results = []
    cur_start = date_start

    while cur_start <= date_end:
        cur_end = cur_start + timedelta(days=req_limit - 1)
        if cur_end > date_end:
            cur_end = date_end

        r = requests.get(
            url,
            params={
                "publish_type": publish_type,
                "date_start": cur_start.strftime("%Y-%m-%d"),
                "date_end": cur_end.strftime("%Y-%m-%d"),
            },
            headers={"Accept": "application/json"},
            timeout=20,
        )
        r.raise_for_status()

        data = r.json()
        all_results.extend(data.get("results", []))

        cur_start = cur_end + timedelta(days=1)

        if cur_start <= date_end:
            time.sleep(1)

    return all_results


#list_puzzles("2023-01-01", "2023-01-10", "mini")

current_date = mini_start_date
current_ids = list_puzzles(mini_start_date, mini_end_date, "mini")
id_by_date = {p["print_date"]: p["puzzle_id"] for p in current_ids}

times = []


for i in range(mini_dates_delta):
    dt_str = current_date.strftime("%Y/%m/%d")
    api_date = current_date.strftime("%Y-%m-%d")   

    pid = id_by_date[api_date]                   
    res = get_time(dt_str, pid)

    print(res)
    times.append(res)                             
    current_date += timedelta(days=1)
    time.sleep(1)



df = pd.DataFrame(times, columns= ['solved', 'time', 'date', 'puzzle_id'])
df.to_csv('times.csv')