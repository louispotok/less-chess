A library for people who want to use beeminder to play less chess on lichess.

It assumes you have a "do more" goal on beeminder, structured as "days with `<N` minutes of chess".

Instructions for use:
* `cp config.template config.py` and fill out the values.
* run `run.sh` periodically (I have a cron job run it every day).

Bug reports welcome!

Note: I didn't think very hard about how timezones are handled.

TODO:

[ ] authenticate to get 3x faster on lichess API
[ ] fix bug described in main.py


---

New Approach 2021-06-26: Go backwards until it matches.

"days" are determined by config.TIMEZONE.
get beeminder datapoints
call lichess API for yesterday (midnight->midnight in TIMEZONE)
if the value in the comment matches (2 decimal places) -> stop
else -> update and do the same for previous day

