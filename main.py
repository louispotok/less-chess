"""
Daily report on how much time you spent playing lichess

The overall approach:
* get the last missing beeminder datapoint
* pull all games starting 2 days before that
* calculate daily time spent
* use beeminder's requestid (idempotency key) as the date, we only ever want one datapoint per date and the latest will be the most accurate.

TODO: There is a bug where
* we start from the last day without games
* we default to 0 minutes during `calc`.
* we fill in too far back

So we end up wiping lots of days.
"""
from datetime import datetime as dt 
from datetime import timedelta as td 
import requests
import json
import logging
from collections import defaultdict
import config
import pytz

API_BASE = f"https://www.beeminder.com/api/v1/users/{config.BEEMINDER_USERNAME}/goals/{config.BEEMINDER_GOAL_NAME}/"
DATAPOINTS_API = API_BASE + "datapoints.json"
DATAPOINTS_BULK_API = API_BASE + "datapoints/create_all.json"


DATE_STR_FORMAT = "%Y%m%d"

def main():
    datapoints = get_datapoints()
    dates = sorted([dt.strptime(dp['daystamp'], DATE_STR_FORMAT).date() for dp in datapoints])
    day_start = get_first_missing_date(dates)
    games = get_games(day_start)
    daily_times = calc(games)
    daily_times = fill_in(daily_times, dates)
    datapoints = dts_to_dps(daily_times)
    resp = post_datapoints(datapoints)
    logging.info(f"{resp.status_code}: {resp.text}")
    return resp

def fill_in(daily_times, dates):
    curr = min(dates)
    while curr < dt.now().date():
        daily_times[curr] += 0
        curr += td(days=1)
    return daily_times


def get_first_missing_date(dates):
    val = dates[-1]
    prev = dates[0]
    for d in dates[1:]:
        if d - prev > td(days=1):
            return prev
        else:
            prev = d
    return val

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
    logging.info(f"getting games since {start_time}")
    params = {"since": start_time, "moves": False}
    resp = requests.get(
        f"https://lichess.org/api/games/user/{config.LICHESS_USER_NAME}",
        params=params,
        headers={"Accept": "application/x-ndjson"},
    )
    if resp.status_code == 200:
        games = [json.loads(g) for g in resp.text.splitlines()]
        logging.info("fetched games")
        return games
    else:
        logging.error(f"ERROR: could not get games: {resp.text}")


def get_datapoints():
    """ Beeminder datapoints"""
    url = f"{DATAPOINTS_API}?auth_token={config.BEEMINDER_AUTH_TOKEN}"
    j = requests.get(url).json()
    return j

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


def get_start_time(first_day):
    """
    first_day: datetime.date
    """
    ONE_DAY_MICRO = 24 * 3600 * 1000
    return dt_to_micro(dt.combine(first_day,dt.min.time())) - (ONE_DAY_MICRO * 2)

if __name__ == '__main__':
    logging.basicConfig(filename="./less-chess.log", level=logging.INFO, format="%(asctime)s %(message)s")
    main()
