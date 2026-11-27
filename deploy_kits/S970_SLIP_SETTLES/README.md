# S970_SLIP_SETTLES — the slip alone settles the morning match

**The parent, S531, 27-Nov-2026 · his "YES" 12:46 IST.**

## His question (12:45)

"ONLY SLIP OF THIS DRESSING ALSO SETTLES THE MATCH OF MORNING CASH WITH SLIPS, EVEN IF DOCTERZ ISNT UPDATED, AS UPDATING BACK DATE DOCTERZ I WANT TO AVOID?"

## Before this kit

When Shavez makes the late slip, the staff's "patient not found" line goes. The slip then moves to his list, "Slips not in Docterz". The money is placed, but the day is not "all matched" until he taps **Not entering in Docterz** on that list.

## What this kit does

- **The answer, by itself.** Before register_push judges a day (on the register's Save, and every 5 minutes from 08:00 to 21:55 for the last 7 days), it looks at the rows of his back-date list.
  - A row whose money the register holds (the day check's `placed` row) is answered **Not entering in Docterz**, as the login `auto`.
  - The day then matches with no tap and no back-dated Docterz entry.
- **His list.** The answer shows with "auto" and its time, and keeps its **Undo**.
- **An Undo is final.** A row anyone has answered or undone before is never answered again.
- **Docterz later.** If Docterz carries the slip later, the row leaves his list by itself and takes the answer with it. Nothing is counted twice.
- **What the auto answer never touches:**
  - a row whose money the register does not hold, or holds only in part (a slip of two lines, one held);
  - today's day (the evening list is still the staff's);
  - a free line or a cancelled slip;
  - a part-billed line.
- **The day check's note** reads "kept outside Docterz automatically (the slip was made)", or in Hindi "Docterz ke bahar, apne aap (parchi bani)".
- **Switch.** `REGPUSH_AUTO_OUTSIDE=0` turns this off.

## Files

| file | from | to |
|---|---|---|
| /root/finance/register_push.py | a4e2549e (S968) | 9b1fbc29 |
| /root/finance/day_check.py | b8007892 (S968) | 946f0408 |

No cron change: the 5-minute check `# S968_REGISTER_PUSH` does it.

## Proof

- **Cold review fixes:** a part-held row stays his; an old 'outside' answer whose row has left his list (Docterz's clinical report knows the visit) no longer hides the staff card.
- **Walk A:** 15/15 on the made-up day checks, and red on the FROM files (the control).
- **Walk B:** 14/14 with the real modules on a copy of the 27-Nov database. It adds a made-up Rs 100 dressing slip and Rs 100 in the register, then checks:
  - the slip is answered by itself;
  - the day's "left" is unchanged;
  - his money page reads it as outside Docterz;
  - no staff card;
  - Undo is final;
  - when Docterz carries the slip later, nothing is counted twice;
  - a two-line slip with one line held is left for him;
  - an OPD answer made stale by Docterz's clinical report brings the staff card back.
- **The install sweep on the real last week:** 3 rows answered by themselves, 0 errors.
- **Rehearsal:** 10/10.

## Install (his server line)

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s970kit && cp -rp /root/deploy/repo/deploy_kits/S970_SLIP_SETTLES /tmp/s970kit && bash /tmp/s970kit/install_S970_SLIP_SETTLES.sh

Undo: `bash /tmp/s970kit/install_S970_SLIP_SETTLES.sh --undo`. Both files go back. The answers already given stay on his list, each with its Undo.
