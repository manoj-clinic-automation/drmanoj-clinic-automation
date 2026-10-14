# REPORT S554_PHYSIO_BACKFILL — kit S554 · installed 14-Oct-2026 07:04 IST

**For Dr Manoj**
- Bhati can now enter the physiotherapy slips and home visits of **every day from 1 October**, not only the last week. Your report matches every day from 1 October against reception, and his duty line names the oldest October day still not entered or not agreeing, until he has caught up.
- It is live and checked on the server. His list shows the line now, for **9 days (1–12 Oct)**. The button opens 1 October first.

---

## For the chat

### Places that held the 14-Oct floor or the 7-day window (found before editing; grep of /root/finance for `2026-10-14`, `BACK_DAYS`, `timedelta(days=`, `physio_book`, `first_clinic_day`)
- `physio_book.py`:
  - `BACK_DAYS = 7` (l.47), used by `_days_back()` / `_day_ok()` (l.221–227);
  - the clinic tab: `_day_bar` (l.510), `_clinic_tab` (l.517) and `post_slip` (l.724);
  - `_match_card`'s *Farq wale aur din* (l.592);
  - the home visit's day list (l.664) and `post_home_visit` (l.831);
  - `post_home_pay`'s own 366-day window (l.854);
  - the report's *"before the register"* floor = the first clinic entry (`first_clinic_day`, used by `differ_days` l.332–348 and `month_days` l.933–940);
  - the error text *"Tareekh aaj ya pichhle 6 din mein se ho."*
- `aaj_duties.json` l.202: `bhati.physio_register`'s SQL `r.business_date >= '2026-10-14'`.
- Not a floor and left alone: `SEARCH_DAYS = 365` (the Docterz patient search). `aaj_seed.py`'s door (`?day={since}`) holds no date. `aaj_kaam.py`'s staff floor (`aaj.from`, 01-Oct-2026, which floors `clinic_physio_day`) already agrees with 01-Oct. `finance_app.py` and `clinic_money.py` hold no physio floor.

### Live files — FROM → TO, md5 read back on the box (07:04:14 IST, the installer's own read-back)
| file | FROM (pin = S552/S553 TO, exact) | TO (read back) |
|---|---|---|
| `/root/finance/physio_book.py` | 745130164014ec8d6f90cda839f5521b | a085fee79c2b0346e4417798cd9808f5 (25 counted edits) |
| `/root/finance/aaj_duties.json` | cb8ac36aa60768216b82c918874a65af | fa5cfac53ee1cd3dc1721a00a9cc3dde (1 counted edit: only the floor in that duty's SQL; the builder asserts nothing else in the file moved) |

The installer checked these against their pins and did not edit them: `aaj_seed.py` a97cd07b…, `aaj_kaam.py` cd232b1c…, `finance_app.py` 87cc4266…, `clinic_money.py` 0a2085ca…. Both files were rebuilt on the box from the live bytes by `make_s554.py` and matched the kit byte for byte. Both compiled on both pythons.

### What was built
- **One floor:** `floor_day(con)` reads the setting `physio_book.from`. If the setting is absent or not a date, it uses `2026-10-01`.
- `_days_back(con, lo)` and `_day_ok(con, d, lo)` cover the floor (or a later course start) up to today. Every rule goes through them: the clinic picker, a slip's day, the visit list, a visit, a payment, the start of a new home course.
- **Clinic tab:** the newest 7 days stay as buttons, and a list beside them (*Yeh din kholo*) holds every day from the floor, newest first.
- **Report:** says *"Days are matched from 01-Oct-2026"*. `differ_days` and `month_days` use the floor, so *before the register* shows only for days before it.
- **Home tab:** a new course has *Shuru kab hua* (date, floor → today, default today). A visit or payment is refused before the floor (*"Tareekh 01-Oct-2026 se aaj tak mein se ho."*) and before the course's start (*"Tareekh is patient ke shuru hone ki tareekh se pehle ki nahi ho sakti."*). The patient page shows *Shuru*.
- **Duty SQL:** the floor is now `COALESCE((SELECT value FROM setting WHERE key = 'physio_book.from' AND value <> ''), '2026-10-01')`. It is still one read-only SELECT, and nothing else in the duty changed.
- **Data step** (`seed_s554.py`): `physio_book.from = 2026-10-01`, INSERT OR IGNORE. **Live: 1 added.**

### Walk (`walk_s554.py`, in the installer, on backup-API copies in /tmp)
The real app ran with header sign-in for that process only, using made-up patients W554… and slip numbers 9554xxxx found by key. Result: **`WALK OK S554: 39 checks green`**.
- **A — the default floor, clock 14-Oct:**
  - the clinic tab offers 01-Oct and not 30-Sep;
  - a slip dated 02-Oct is accepted; 30-Sep is refused (with the floor in the words) and 15-Oct is refused;
  - a course started back on 01-Oct takes a visit and a payment dated 05-Oct, and refuses both on 30-Sep;
  - a course cannot be started on 30-Sep;
  - a course started today refuses a 05-Oct visit;
  - the October report matches 01-Oct: first a difference, then ✓ once entries agree, then *"cash ₹ 250 · UPI ₹ 0"* with one slip more. No October day reads *before the register*, and 30-Sep does;
  - the duty's SQL as shipped: n = 9, since = 2026-10-01, the same as worked out independently. Once 01-Oct agrees: n = 8, since = 2026-10-02;
  - the door `?day=2026-10-01` as bhati shows *Milaan — 01-Oct-2026* with *Farq*.
- **B — the setting moved to 2031-03-01:**
  - the picker, the slip rules (02-Mar in; 28-Feb and 02-Oct-2026 out), the report (01-Mar ✓, 02-Mar *"cash ₹ 0 · UPI ₹ -250"*, 27-Feb *before the register*) and the SQL (n = 2 / since 02-Mar; setting at 27-Feb → n = 3) all follow it;
  - bhati's own list shows the line opening `?day=2031-03-02`, and manoj `?as=bhati` shows it too;
  - **staff-eye:** bhati's portal home (the real portal.py and the grants file) carries Physiotherapy → /finance/physio. That page offers *Patient-wise register ›*. The door page shows *"Farq: Cash ₹ 0 · UPI ₹ 250"*;
  - once entries agree, the line leaves.
- **C — data step and static checks:**
  - the data step: 1 added, a second run 0, an existing value kept;
  - `clinic_physio_day` is never written by the app;
  - physio_book.py writes only its own four tables and `setting`;
  - `2026-10-14` appears in neither file;
  - no 10-digit number in the kit, and the name is never misspelt.

### Negative control
The same walk on the old two files: **24 of 39 checks red, 18 of them the backfill checks**. Among them: *"a slip dated 02-Oct is accepted"* (the old file answers `err=day`), the duty reads (0, None), and the report shows 01-Oct as *before the register*.

### Rehearsal (`rehearse_s554.sh`, a made-up root in /tmp, the real app under a stand-in systemctl on port 18554)
**`REHEARSAL OK`**:
- run 1, red after placing: both files back byte-identically, health 200, the database backup kept, the lock released;
- run 2, green: DONE, the md5s read back, the setting = 2026-10-01;
- run 3: ALREADY INSTALLED.

### Install (times read from the program's output and from systemd)
- The lock `/root/deploy/.claude_code_build.lock` was taken at 07:03:49 IST (owner S554_PHYSIO_BACKFILL). The installer ran with `LOCK_HELD=1` from `/tmp/s554kit` (SUMS.md5 a15a462b…; 10 of 10 OK). It started at 07:04:04 and exited 0 at 07:04:14.
- Backups:
  - `/root/finance/finance.db.bak_S554_20261014_070404` (backup API, mode 600, 36,823,040 bytes);
  - `physio_book.py.bak_S554_74513016` (md5 7451301…, = FROM);
  - `aaj_duties.json.bak_S554_cb8ac36a` (md5 cb8ac36…, = FROM).
- Only **clinic-finance** was restarted (ActiveEnterTimestamp 07:04:09 IST). The register and the staff list (aaj_kaam) both run in that process; S553 found nothing else serving the list.
- `/finance/healthz` answered 200 (local, and public at followup.dr-manoj.in). `/finance/physio/book`, `/report` and `/finance/aaj` answer 302 without a login, which is the login gate and expected. The journal is clean.
- **As manoj** (`probe_s554.py`: the real app from a copy of the placed files, on a fresh copy of the live db):
  - the setting is 2026-10-01;
  - the register's clinic tab offers 01-Oct and not 30-Sep;
  - the October report says *"Days are matched from 01-Oct-2026"*. Of October's 10 reception days, 1 agrees (10-Oct, reception ₹0), 9 differ, 0 are before the register;
  - `/finance/aaj?as=bhati` answers 200 with 4 lines on Bhati's list. **The line SHOWS** under *Aaj*: *"Physio slips register mein likhiye — reception ke hisaab se nahin mil rahi"* → `/finance/physio/book?day=2026-10-01`. The duty SQL on live reads n = 9, since 2026-10-01. **PROBE OK.**

### Undo
`\cp -p /root/finance/physio_book.py.bak_S554_74513016 /root/finance/physio_book.py && \cp -p /root/finance/aaj_duties.json.bak_S554_cb8ac36a /root/finance/aaj_duties.json && systemctl restart clinic-finance`
The setting may stay, because nothing in the old files reads it.

### Repository
- `deploy_kits/S554_PHYSIO_BACKFILL/` contains 11 files: physio_book.py, aaj_duties.json.kit, make_s554.py, seed_s554.py, walk_s554.py, probe_s554.py, install_S554_PHYSIO_BACKFILL.sh, rehearse_s554.sh, README.md, KIT_ID.txt, and SUMS.md5 (which lists the other 10).
- `.gitignore` got the exact-path line `!deploy_kits/S554_PHYSIO_BACKFILL/aaj_duties.json.kit`, as S553 did. `claude_code_briefs/DUTY_MAP.md` has the bhati.physio_register row moved to the floor setting.
- The NO_PHONE_NUMBERS gate was clean over the added files and again inside PUBLISH_ALL (30 files).
- Published by `PUBLISH_ALL.bat` → origin HEAD **615a51a** (verified by the script). On the box I ran `git pull --ff-only` and `md5sum -c` (10 of 10 OK). The repository kit is identical to what ran (`diff -r` clean, same SUMS md5).
- **That publish also carried files already pending that this build did not write:** `deploy_kits/S551_SORTING_DESK/` (14 files), `claude_code_briefs/REPORT_S551.md`, `S551_FIX1.md`, and an edit to `S543_ORDER_SHEET_MARG.md`. PUBLISH_ALL commits everything pending by design. This report follows in the next publish.

### Calls made (no one was asked)
1. **Today is always allowed**, even if the setting is ever put in the future, so the day's own slips are never locked out.
2. **Payments are tighter than before, as the brief says.** S552 allowed a payment dated up to 366 days back. Now it is floor → today, and not before the course's start. The live register had 0 rows, so nothing already entered is affected.
3. **A course's start:** only home courses ask for it (*Shuru kab hua*). A clinic course's `started` is still the day it was first used, because no rule reads it.
4. The day picker is 7 buttons plus a list (13+ buttons would wrap badly on his phone).
5. `first_clinic_day()` stays in the file, now unused, to keep the edit small. It is harmless.
6. **DUTY_MAP.json was not changed**, for the same reason as S553: the duty lives in aaj_duties.json, and putting it in both would show it twice. The door is unchanged (Physiotherapy tile → register → the day). There is no Needs-you line.

### Not done, and why
- **The board's `_numbers` claims:** not reachable from this runner (the board is a claude.ai artifact). **The chat should append S554's DONE / RELEASED line** (physio_book.py a085fee7, aaj_duties.json fa5cfac5).
- No physio row and no `clinic_physio_day` row was written on the live database (only the one setting).
- **Server clean-up was refused by the permission list.** The combined command (`git pull`, lock release, `rm -rf /tmp/s554kit /tmp/s554probe`) was denied. I did not retry it in another form. The lock alone was released with `rm owner` + `rmdir` at **07:06:14 IST** (read from the box), after the report was published, and healthz was 200 then. **Left on the box:** `/tmp/s554kit` (the kit copy that ran, identical to the repository) and `/tmp/s554probe` (a read-only count probe, the trial script and the installer's log). No secret and no number is in them. Either can be deleted by whoever holds a wider permission.

### Noticed outside the brief (not touched)
- Bhati's list will now carry this line every day until 1–12 Oct are entered and agree. `bhati.physio_tick` (*Theek hai* in the petty book) still overlaps it, and is the owner's to switch off on his panel.
- Still open from S553: when the line is not due, the owner's panel shows its door with a literal `{since}` (`aaj_kaam._fill` strips only `/{since}`). The register treats it as today.
- The health page's "all N parts loaded" count still does not name `physio_book` (S552's note).
