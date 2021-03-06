A library for people who play too much lichess, and want to use [beeminder](https://www.beeminder.com/) to play less chess.

It assumes you have a "do more" goal on beeminder, structured as "days with `<N` minutes of chess".

Suggestions or bug reports welcome!

# How to use

Instructions for use:
* `cp config.template config.py` and fill out the values.
* Create a virtualenv from requirements.txt
* run `run.sh` periodically (I have a cron job run it every few hours).

# How it works

The basic approach is:
* Get all your beeminder datapoints for the goal
* For each day starting today 
  * Fetch games from lichess
  * Calculate total time played
  * See if the existing datapoint is accurate (storing exact minutes playing the beeminer `comment`, and update if not
* Then repeat, going backwards one day at a time, until you hit a "good" day.


## Complications 

This is robust against one kind of failure (if the job stops running for several days) but not robust if the job crashes halfway - imagine Monday/Tuesday/Wednesday are all wrong, we fix Wednesday then have a crash. Next time the job runs it will see that Wednesday is correct, and stop.

Another nuance surrounds the derail day. Suppose that you are at a do-or-die day, in other words that today is a day when you need to play <N minutes or you derail. The beeminder notifications that day are good: you are at a beemergency and should not derail. But once you have played N minutes that day you have already derailed, and additional notifications are not helpful. We do need the job to, at some point on that day, create a datapoint, so that if you succeed in playing `<N` minutes you don't derail, but the behavior is not ideal. Perhaps there's a better goal type to use.

Anything involving times and timezones is annoying. This assumes that you want your beeminder "days" to be in local time. If you switch your local time, you may have a day or two of wrong data.

Also, there will probably be some wrong data on daylight savings transitions.
