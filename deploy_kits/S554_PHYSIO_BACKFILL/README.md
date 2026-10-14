# S554_PHYSIO_BACKFILL — kit S554 (14-Oct-2026) · brief `claude_code_briefs/S554_PHYSIO_BACKFILL.md`

**The owner, 14-Oct 06:17 IST:** *"i want him to backfill from 1st october"* — after S552 (the Physio register: a slip only for today and
the six days before) and S553 (Bhati's duty line: counted from 14-Oct).

## What it does

- **One floor date for the whole register: 01-Oct-2026**, held once — the setting `physio_book.from` (`2026-10-01`; the same default
  when the setting is absent or not a date). Every rule below reads it; no other date is written in the code.
- **Clinic tab:** the newest seven days stay as buttons; every day from the floor to today is in a list beside them
  (*Yeh din kholo*), newest first. A slip may be entered (and voided) for any day from the floor to today. Today stays the default.
  A day outside reads *"Tareekh 01-Oct-2026 se aaj tak mein se ho."*
- **Home tab:** a new home patient has *Shuru kab hua* (default today, back to the floor). A visit or a *Payment received* may be
  dated any day from the floor to today, and not before that course's start (*"Tareekh is patient ke shuru hone ki tareekh se pehle
  ki nahi ho sakti."*). The patient's page shows *Shuru*.
- **Report:** says *"Days are matched from 01-Oct-2026"*; every reception day from the floor is matched (✓ / the difference /
  *reception not written*); *before the register* only for days before the floor. The clinic tab's *Farq wale aur din* also
  lists from the floor.
- **Duty line `bhati.physio_register`:** its SQL counts days from the setting (`COALESCE((SELECT value FROM setting WHERE key =
  'physio_book.from' AND value <> ''), '2026-10-01')`) up to yesterday, otherwise as S553 built it. It is due at once after the
  install (1–13 Oct not yet entered): that is his backfill list; the button opens the oldest such day.
- **Unchanged:** the slip rules, the void rule, the switch, reception's table (never written), the accountants' pack, aaj_seed.py.

## Files

| live file | from → to | what |
|---|---|---|
| `/root/finance/physio_book.py` | 74513016 → a085fee7 | 25 counted edits (`make_s554.py`): `floor_day()`; `_days_back(con, lo)` / `_day_ok(con, d, lo)` from the floor; the day picker; the words; the report's floor; the home start date and the visit / payment checks |
| `/root/finance/aaj_duties.json` | cb8ac36a → fa5cfac5 | 1 counted edit: the floor in `bhati.physio_register`'s SQL (nothing else in the file changes — the builder proves it) |

Shipped as `physio_book.py` and `aaj_duties.json.kit`; the installer rebuilds both on the box from the live bytes and refuses unless
they are the kit's, byte for byte. Read beside them, pinned and not edited: `aaj_seed.py` a97cd07b, `aaj_kaam.py` cd232b1c,
`finance_app.py` 87cc4266, `clinic_money.py` 0a2085ca. **Data step** (`seed_s554.py`): `physio_book.from = 2026-10-01`,
INSERT OR IGNORE (a value already there is kept). Restarts `clinic-finance` only (the register and the staff list both run in it).

## Proof (on the box, scratch copies only)

`walk_s554.py` — the real finance app on a backup-API copy, header sign-in for that process only, made-up patients and slip numbers
found by key, the register's clock pinned. **A** (no setting, clock 14-Oct-2026): the clinic tab offers 01-Oct, not 30-Sep; a slip
dated 02-Oct accepted, 30-Sep and 15-Oct refused; a home course started back on 01-Oct takes a visit and a payment dated 05-Oct and
refuses 30-Sep; a course may not start on 30-Sep; a course started today refuses a 05-Oct visit; the October report matches 01-Oct
(the difference, then ✓ when entered to agree, then the difference again with one slip more), no October day *before the register*,
a September day *before the register*; the duty's SQL as shipped gives n = the disagreeing October days and since = 01-Oct (worked out
independently), and moves to the next day when 01-Oct agrees; the door `?day=2026-10-01` shows 01-Oct's *Farq*. **B** (the setting
moved to 01-Mar-2031): the picker, the slip rules, the report, *before the register* and the duty's SQL all follow it; bhati's own list
shows the line opening `?day=2031-03-02`, manoj `?as=bhati` too; **staff-eye**: bhati's portal home carries Physiotherapy →
/finance/physio, which offers *Patient-wise register ›*, and the door page shows the day's *Farq*; entered to agree, the line leaves.
**C**: the data step (once; second run 0; an existing value kept); clinic_physio_day never written; physio_book.py writes only its own
tables and the setting; 2026-10-14 nowhere; no 10-digit number. 39 checks.
**Negative control:** the same walk on the old two files must go red, among them *"a slip dated 02-Oct is accepted"*.
`rehearse_s554.sh` runs the installer on a made-up root with a stand-in service (the real app on port 18554): red after placing
restores both files byte-identically, green installs, a second run says ALREADY INSTALLED.

## Install — one line on the VPS

`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S554_PHYSIO_BACKFILL/install_S554_PHYSIO_BACKFILL.sh`

`DRY=1` before `bash` runs every gate and the walk and writes nothing.

## Undo

`\cp -p /root/finance/physio_book.py.bak_S554_74513016 /root/finance/physio_book.py && \cp -p /root/finance/aaj_duties.json.bak_S554_cb8ac36a /root/finance/aaj_duties.json && systemctl restart clinic-finance`

(The setting `physio_book.from` may stay: nothing in the old files reads it. Slips, visits and payments Bhati entered for 1–7 Oct stay
in the register and in the report; the old files simply no longer offer those days for new entries. The database backup
`finance.db.bak_S554_<stamp>` is for reversing data only and is not needed for the undo.)
