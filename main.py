"""
Daily report on how much time you spent playing lichess

The overall approach:
* "days" are determined by config.TIMEZONE.
* get beeminder datapoints
* call lichess API for yesterday (midnight->midnight in TIMEZONE)
* if the value in the comment matches (2 decimal places) -> stop
* else -> update and do the same for previous day

* use beeminder's requestid (idempotency key) as the date, we only ever want one datapoint per date and the latest will be the most accurate.
"""
from datetime import datetime as dt 
from datetime import date
from datetime import timedelta as td 
import requests
import json
import logging
import config
import pytz
import typing
from dataclasses import dataclass

API_BASE = f"https://www.beeminder.com/api/v1/users/{config.BEEMINDER_USERNAME}/goals/{config.BEEMINDER_GOAL_NAME}/"
DATAPOINTS_API = API_BASE + "datapoints.json"
DATAPOINTS_BULK_API = API_BASE + "datapoints/create_all.json"


DATE_STR_FORMAT = "%Y%m%d"

@dataclass
class Day:
    """
    This represents a single day in "local" time as defined by config.TIMEZONE.
    Start and end are timestamps in milliseconds.
    """
    local_date: date
    start: int
    end: int

    def formatted_date(self):
        return self.local_date.strftime(DATE_STR_FORMAT)

    def previous(self):
        return Day(
                local_date = self.local_date-td(days=1),
                start = self.start - (24 * 3600 * 1000),
                end = self.start
                )




@dataclass
class Game:
    """timestamps in milliseconds"""
    created_at: int
    last_move_at: int

    def duration_seconds(self):
        return (self.last_move_at - self.created_at) / 1000


def main():
    # call beeminder API
    existing_datapoints = convert_datapoints(get_datapoints())
    curr = make_yesterday()
    day_games = get_games(curr)
    while beeminder_is_wrong(curr, existing_datapoints, day_games):
        logging.info(f"updating for {curr}")
        update_datapoint(curr,day_games)
        curr = curr.previous()
        if curr.local_date < config.START_DATE:
            return
        day_games = get_games(curr)



    return

def convert_datapoints(datapoints: list) -> typing.Dict[str, dict]:
    return_val = {}
    for d in datapoints:
        k = d['requestid']
        if k in return_val:
            raise ValueError(f"duplicate requestid {k} in beeminder datapoints")
        return_val[k] = d
    return return_val

def make_yesterday() -> Day:
    """
    Whatever today is in TIMEZONE, return the previous day.
    Probably fails weirdly for DST, don't care.
    """
    now = dt.now(pytz.timezone(config.TIMEZONE))
    yesterday = now - td(days=1)
    start = dt_to_milli(to_midnight(yesterday))
    end = dt_to_milli(to_midnight(now))
    return Day(local_date=yesterday.date(),start=start, end=end)


def to_midnight(dt_to_replace: dt) -> dt:
    return dt_to_replace.replace(hour=0,minute=0,second=0,microsecond=0)


def get_games(day: Day) -> typing.List[Game]:
    """
    """
    start_time = day.start
    end_time = day.end
    logging.info(f"getting games between {start_time} and {end_time}")
    params = {"since": start_time, "until": end_time, "moves": False}
    resp = requests.get(
        f"https://lichess.org/api/games/user/{config.LICHESS_USER_NAME}",
        params=params,
        headers={"Accept": "application/x-ndjson"},
    )
    if resp.status_code == 200:
        games = [json.loads(g) for g in resp.text.splitlines()]
        games = [Game(created_at=g['createdAt'], last_move_at=g['lastMoveAt']) for g in games]
        logging.info("fetched games")
        return games
    else:
        logging.error(f"ERROR: could not get games: {resp.text}")
        return []

def beeminder_is_wrong(
        curr: Day,
        existing_datapoints: typing.Dict[str,dict],
        games: typing.List[Game]
        ):
    """
    1. calculate duration for day_games
    2. compare to value from existing_datapoints
    """
    actual_duration = sum([g.duration_seconds() for g in games])

    rel_dp = existing_datapoints.get(curr.formatted_date(), None)
    if not rel_dp:
        logging.info(f"missing datapoint for day {curr}")
        return True

    beeminder_duration = float(rel_dp['comment'].split()[0])
    is_wrong = not is_close(beeminder_duration, actual_duration)
    if is_wrong:
        logging.info(
                f"discrepancy between {beeminder_duration} (beeminder) and {actual_duration} (lichess) for {curr}"
                )
    return is_wrong


def is_close(a,b,tol=.01):
    return abs(a-b) < tol



def update_datapoint(curr: Day, day_games: typing.List[Game]) -> None:
    duration_minutes = sum([g.duration_seconds() for g in day_games]) / 60
    payload = {
            "auth_token": config.BEEMINDER_AUTH_TOKEN,
            "value": int(duration_minutes < config.DAILY_LIMIT_MINUTES),
            "daystamp": curr.formatted_date(),
            "requestid": curr.formatted_date(),
            "comment": f"{duration_minutes:0.2f} minutes ({len(day_games)} games.) Added by less-chess API"
            }
    logging.info(f"posting {payload} for {curr}")
    #resp = requests.post(DATAPOINTS_API, json=payload)
    #logging.info(f"request for {curr} returned {resp.status_code}")


def get_datapoints() -> list:
    """ Beeminder datapoints"""
    url = f"{DATAPOINTS_API}?auth_token={config.BEEMINDER_AUTH_TOKEN}"
    j = requests.get(url).json()
    return j



def dt_to_milli(d: dt) -> int:
    return int(dt.timestamp(d)) * 1000



if __name__ == '__main__':
    logging.basicConfig(filename="./less-chess.log", level=logging.INFO, format="%(asctime)s %(message)s")
    main()
