"""
Daily report on how much time you spent playing lichess
"""
from datetime import datetime as dt 
import requests
import json
from collections import defaultdict
import secrets

def main():
    start_time = get_start_time()
    params = {"since": start_time, "moves": False}
    resp = requests.get(
        f"https://lichess.org/api/games/user/{secrets.LICHESS_USER_NAME}",
        params=params,
        headers={"Accept": "application/x-ndjson"},
    )
    if resp.status_code == 200:
        games = [json.loads(g) for g in resp.text.splitlines()]

        daily_times = calc(games)
        return daily_times
        print(daily_times)
    else:
        print("error!")


def calc(games):
    result = defaultdict(lambda: 0)
    for g in games:
        day = to_day(g["createdAt"])
        duration = (g["lastMoveAt"] - g["createdAt"]) / 1000
        result[day] += duration
    return result


def to_day(ts):
    return dt.fromtimestamp(ts / 1000).date()


def get_today_midnight():
    return int(dt.timestamp(
            dt.now().replace(hour=0, minute=0, second=0, microsecond=0)
            )) * 1000


def get_start_time():
    ONE_DAY_MICRO = 24 * 3600 * 1000
    return get_today_midnight() - (ONE_DAY_MICRO * 7)

if __name__ == '__main__':
    main()
