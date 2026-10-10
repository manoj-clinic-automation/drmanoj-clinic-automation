# S507_FOLLOWUP_LOG_REACH — a follow-up log must reach the next call day

Session 304 (parent), 10-Oct-2026. The owner, 10-Oct morning: staff need a confirmation that **both** evening Docterz exports
(the consultation report and the follow-up log) are done, and a fallback when one is missed.

## What was found (22:30 IST)
Reception's *Aaj ka kaam* already carries both lines (S487): after 7 pm *"Jaane se pehle: aaj ki Docterz ki dono report
nikaliye"* while either is missing, and next morning a first-thing line if yesterday's is still missing. **But a file counted as
done the moment it arrived.** On Saturday 10-Oct the follow-up log covered **one day — Sunday 11-Oct** — so the tracker built a
call list for Sunday, and Monday's call list would have been empty while every line said done. (One-day logs on 6-Oct and 8-Oct
were fine: each covered the next call day, which is all the tracker loads.)

## What changes
- `docterz_pickup.py` records the due dates each follow-up log covers (two columns it adds itself; the logs already kept get
  theirs from their own stored bytes, on its next pass). A log whose last due date is before the **next call day** (the day
  after, Sunday skipped) is noted, and the owner's money page says so in a red line until a whole one arrives.
- `aaj_duties.json`: reception's evening line and morning line count such a log as **not done**.
- `aaj_seed.py`: the hint under those two lines (what reception reads): *"Follow-up log mein agle kaam ke din (Sunday
  chhodkar) tak ki date honi chahiye — Docterz ka default ek mahine wala export sabse sahi hai."*
- A re-export the next morning is already accepted (a newer file of the same day with more rows replaces the old one, here and
  in the tracker on the owner's PC, which re-runs the day within minutes) — unchanged.

## Install (his one line on the VPS, after PUBLISH_ALL)
    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S507_FOLLOWUP_LOG_REACH/install_S507_FOLLOWUP_LOG_REACH.sh

## Undo (the three files back; the two columns stay, unused)
    cd /root/finance && \cp -p docterz_pickup.py.bak_S507_b2dc5475 docterz_pickup.py && \cp -p aaj_duties.json.bak_S507_7aa29bef aaj_duties.json && \cp -p aaj_seed.py.bak_S507_e13d03d0 aaj_seed.py && systemctl restart clinic-finance
