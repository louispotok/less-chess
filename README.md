Instructions for use:
* `cp config.template config.py` and fill out the values.

Waiting on beeminder forum: https://forum.beeminder.com/t/error-creating-datapoints/7776

Note: if you switch timezones, this may screw up a bit. That seems okay.


Plan of attack:
[x] GET datapoints for goal (https://api.beeminder.com/#datapoint)
[x] find the latest
[x] fetch games since then
[] calc days since then
[] POST datapoints for each
[] authenticate to get 3x faster on lichess API
