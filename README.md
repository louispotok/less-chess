Instructions for use:
* `cp secrets.template secrets.py` and fill out your secrets

To do:
* Connect to beeminder API
* make sure to deal with duplicates

Plan of attack:
[] GET datapoints for goal (https://api.beeminder.com/#datapoint)
[] find the latest
[] fetch games since then
[] calc days since then
[] POST datapoints for each
