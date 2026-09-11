# S238_DOCTERZ_SCHEDULE — the Day Revenue reader looks more often

**The owner, 11-Sep-2026:** "Add extra runs, every 10 minutes till 12 noon, then at 1.40 pm and 7.40 pm."
Then: "The bank MPR of the day's transactions arrives not before 9.30 am next day, so a first run before that
is not very useful; subsequent runs are to capture the bank MPR."

**Now:** the reader that loads the Docterz day sheet from Drive into the Day Revenue screen runs:
- every 10 minutes from 09:30 to 12:00 IST;
- again at 13:40 and 19:40 IST.

The Docterz sheet usually reaches Drive by 09:20, so the 09:30 run picks it up. The bank MPR reaches the box
by its own hourly push and shows on the day page as soon as it lands. Repeated runs are cheap and safe: an unchanged sheet is skipped, and a lock stops two runs
overlapping.

This replaces the single 09:25 line from S223. No other scheduled job is touched: the installer counts
them before and after, and puts the old schedule back if anything does not match.

**Proven offline:** the installer walk covered green, a re-run, a crontab write failure (restored),
and a server clock that is not IST (refused).

```
bash /root/deploy/vps_deploy.sh S238_DOCTERZ_SCHEDULE
```
