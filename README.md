# Survival (Suicide) Football Pick Utility

Make picks under the following assumptions:

* a team's likelihood of winning is a weighted average of the whole season (0.8) with the last 2 weeks (0.2)
* bump home teams by 5%
* take away visitors by 5%
* threshold at 95%

```
usage: picker.py [-h] [--sw STARTING_WEEK] [--ew ENDING_WEEK]
                 [--chosen CHOSEN] [--schedule SCHEDULE] [--season SEASON]
                 [--prune PRUNE] [--n N_BEST]

make picks for survival football

optional arguments:
  -h, --help           show this help message and exit
  --sw STARTING_WEEK   starting week (default = 1)
  --ew ENDING_WEEK     ending week (default = 17)
  --chosen CHOSEN      file containing list of teams already picked / wish to
                       save (default = chosen.txt)
  --schedule SCHEDULE  espn schedule as grid txt file (default = schedule.txt)
  --season SEASON      directory containing espn weekly scores [01.txt,
                       02.txt...] (default = season)
  --prune PRUNE        prune the pickset queue between weekly iterations
                       (default = False)
  --n N_BEST           number of picksets to show upon complettion (default =
                       10)
```
