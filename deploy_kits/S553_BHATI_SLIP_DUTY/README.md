# S553_BHATI_SLIP_DUTY — kit S553 (14-Oct-2026) · brief `claude_code_briefs/S553_BHATI_SLIP_DUTY.md`

**The owner, 14-Oct 05:43 IST:** *"I have opened it for Bhati ... And also ... his daily slip entry goes on his staff duty list."*

## What it does

- **Bhati's *Aaj ka kaam*** gets one line under *Aaj*: **"Physio slips register mein likhiye — reception ke hisaab se nahin mil rahi"**.
  It is there when a day **D** with **14-Oct-2026 ≤ D < today (IST)** has reception's physio figures (`clinic_physio_day`, cash + UPI > 0)
  and Bhati's live clinic slips for D (`physio_session` of a `physio_course` of kind `clinic`, `voided_at = ''`) do not equal reception's
  cash and UPI **mode by mode**. The button opens his register's clinic tab on the oldest such day: `/finance/physio/book?day=<day>`.
  It leaves by itself when his entries agree. So the earliest it can appear is the morning of 15-Oct, for 14-Oct.
- **The owner's console** reads it as *"Bhati: physiotherapy slips of <day> not entered in his register, or not agreeing with reception"*,
  with the count of such days. No Needs-you line (the duty has a door on Bhati's own home).
- **His panel line** `bhati.physio_register`: *Aaj*, switched on, opens the Physiotherapy tile. Nobody else's lines are touched;
  `bhati.physio_tick` (the petty book's *Theek hai*) is not changed — it now overlaps and is the owner's to switch off on his panel.
- **Why the staff wording has no day in it:** `aaj_kaam.py` shows a panel line's words exactly as written (it fills `{since}` only into
  the owner's English and into the door), so the brief's `{since}` stays in the duty's own `hi`/`en` and the button carries the day.

## Files

| live file | from → to | what |
|---|---|---|
| `/root/finance/aaj_duties.json` | 2d6d30eb → cb8ac36a | 1 counted edit: the `extra` duty `bhati.physio_register` (kind `sql`; one read-only SELECT) after `bhati.petty_cash_match` |
| `/root/finance/aaj_seed.py` | 156ded1e → a97cd07b | 2 counted edits: `ENGINE['bhati.physio_register']` = the door with the day; Bhati's panel line, on |

Shipped as `aaj_duties.json.kit` and `aaj_seed.py`; `make_s553.py` rebuilds both on the box from the live bytes and the installer refuses
unless they are byte for byte the kit's. Read beside them, pinned and not edited: `aaj_kaam.py` cd232b1c, `physio_book.py` 74513016.
**Data step** (`cfg_s553.py`, idempotent): only if the owner has SAVED a panel for bhati (table `aaj_cfg`) — the line is appended to it,
switched on (aaj_kaam would otherwise add it switched OFF, marked new); a line he took off stays off. On 14-Oct `aaj_cfg` did not exist,
so it changes nothing and the seed's line shows by itself. Restarts `clinic-finance` only (aaj_kaam imports aaj_seed there).
**Never:** `clinic_physio_day` or any physio table written; another person's list changed; a line switched off.

## Proof (on the box, scratch copies only)

`walk_s553.py` — made-up rows dated March 2031, found by key: the duty's SQL as shipped at a fixed clock (its floor and its `now` each
replaced once) — agrees → not due; no entries → due (the oldest day); cash agrees, UPI differs → due; a voided slip and a home visit
ignored; reception's 0 → not due; before the floor → never; today → never; the clock and the floor moved one day to show both
exclusions bite. Then the REAL finance app on the copy, header sign-in for that process only: bhati's own list shows the line with
`/finance/physio/book?day=2031-03-11`; manoj's `?as=bhati` shows it; alisha, shivani, reception, shavez, darpan, sukhveer, amir, manoj
do not; the console item n = 2; **staff-eye**: bhati's portal home (real `portal.py` + grants) carries Physiotherapy, the door page shows
the day's *Farq*; a saved panel predating the line shows it OFF until the data step, which puts it on (second run: 0 changed; a line the
owner removed stays off); with the entries made to agree the line leaves. 26 checks.
**Negative control:** the same walk on the old two files — 10 of 17 red, 7 of them the line checks.
`rehearse_s553.sh` runs the installer on a made-up root with a stand-in service (the real app on port 18553): red after placing restores
both files byte-identically, green installs, a second run says ALREADY INSTALLED.

## Install — one line on the VPS

`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S553_BHATI_SLIP_DUTY/install_S553_BHATI_SLIP_DUTY.sh`

`DRY=1` before `bash` runs every gate and the walk and writes nothing.

## Undo

`\cp -p /root/finance/aaj_duties.json.bak_S553_2d6d30eb /root/finance/aaj_duties.json && \cp -p /root/finance/aaj_seed.py.bak_S553_156ded1e /root/finance/aaj_seed.py && systemctl restart clinic-finance`

(If the data step added the line to a saved panel, the old seed does not know the id and aaj_kaam drops it — nothing to undo there.
The database backup `finance.db.bak_S553_<stamp>` is for reversing data only and is not needed for the undo.)
