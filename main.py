"""
Daily report on how much time you spent playing lichess

The overall approach:
* get the last beeminder datapoint
* pull all games starting 2 days before that
* calculate daily time spent
* use beeminder's requestid (idempotency key) as the date, we only ever want one datapoint per date and the latest will be the most accurate.
"""
from datetime import datetime as dt 
import requests
import json
from collections import defaultdict
import config
import pytz

API_BASE = f"https://www.beeminder.com/api/v1/users/{config.BEEMINDER_USERNAME}/goals/{config.BEEMINDER_GOAL_NAME}/"
DATAPOINTS_API = API_BASE + "datapoints.json"
DATAPOINTS_BULK_API = API_BASE + "datapoints/create_all.json"


DATE_STR_FORMAT = "%Y%m%d"

def main():
    datapoints = get_datapoints()
    latest_dp = max([d['daystamp'] for d in datapoints])
    games = get_games(latest_dp)
    daily_times = calc(games)
    datapoints = dts_to_dps(daily_times)
    resp = post_datapoints(datapoints)
    return resp


def post_datapoints(datapoints):
    payload = {"auth_token": config.BEEMINDER_AUTH_TOKEN, "datapoints": datapoints}
    return requests.post(DATAPOINTS_BULK_API, json=payload)


def dts_to_dps(dts):
    vals = []
    for k, v in dts.items():
        vals.append({
            "value": int((v / 60) < config.DAILY_LIMIT_MINUTES),
            "daystamp": k.strftime(DATE_STR_FORMAT),
            "requestid": k.strftime(DATE_STR_FORMAT),
            "comment": f"{v/60:0.2f} minutes. Added by less-chess API"
            })
    return vals

def get_games(first_day):
    """
    first_day: 'YYYYMMDD' string
    """
    start_time = get_start_time(first_day)
    params = {"since": start_time, "moves": False}
    resp = requests.get(
        f"https://lichess.org/api/games/user/{config.LICHESS_USER_NAME}",
        params=params,
        headers={"Accept": "application/x-ndjson"},
    )
    if resp.status_code == 200:
        games = [json.loads(g) for g in resp.text.splitlines()]
        return games
    else:
        print("error!")


def get_datapoints():
    url = f"{DATAPOINTS_API}?auth_token={config.BEEMINDER_AUTH_TOKEN}"
    return requests.get(url).json()

def calc(games):
    result = defaultdict(lambda: 0)
    for g in games:
        day = to_day(g["createdAt"])
        duration = (g["lastMoveAt"] - g["createdAt"]) / 1000
        result[day] += duration
    return result


def to_day(ts):
    return dt.fromtimestamp(ts / 1000, tz=pytz.timezone(config.TIMEZONE)).date()


def dt_to_micro(d):
    return int(dt.timestamp(d)) * 1000

def get_today_midnight():
    return dt_to_micro(dt.now().replace(hour=0, minute=0, second=0, microsecond=0))


def get_start_time(first_day=None):
    """
    first_day: 'YYYYMMDD' string
    """
    ONE_DAY_MICRO = 24 * 3600 * 1000
    if first_day is None:
        return get_today_midnight() - (ONE_DAY_MICRO * 7)
    else:
        return dt_to_micro(dt.strptime(first_day, DATE_STR_FORMAT)) - (ONE_DAY_MICRO * 2)

if __name__ == '__main__':
    main()
