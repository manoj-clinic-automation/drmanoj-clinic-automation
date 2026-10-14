# S554_PHYSIO_BACKFILL — brief for the build runner (Agent SDK, the API credits)

*Written 14-Oct-2026 by the parent (session 313). Kit **S554** claimed on the board `_numbers` (v410 → v411) with its PLANNED line. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S554_PHYSIO_BACKFILL`.*

## 0 · For the owner (2 plain lines in the report)
Bhati can now enter the physiotherapy slips and home visits of **every day from 1 October**, not only the last week. Your report matches every day from 1 October against reception, and his duty line names the oldest October day still not entered or not agreeing, until he has caught up.

## 1 · The owner's word
14-Oct 06:17 IST: *"i want him to backfill from 1st october"* — after S552 (the Physio register, live 05:29) and S553 (Bhati's duty line, live 05:59; it counts from 14-Oct and the register allows only today and the six days before).

## 2 · Pins (read `claude_code_briefs/REPORT_S552.md` and `REPORT_S553.md` for the live TO md5s; read each live file and check its md5 = that TO; a different byte = STOP that file and report)
- `/root/finance/physio_book.py` (S552's TO).
- `/root/finance/aaj_duties.json` (S553's TO) — the `bhati.physio_register` duty's floor date.
- Anything else S552/S553 touched that holds the 14-Oct floor or the 7-day window — find every place in the code (grep `14`, `2026-10-14`, `7`, `timedelta(days=`, the report's *"before the register"* rule) and list them in the report before editing.

## 3 · The change
- **One floor date for the whole register: 01-Oct-2026**, held once (a setting `physio_book.from` = `2026-10-01`, default when absent), read by every rule below. No other date is hard-coded.
- **Clinic tab:** the day picker reaches every day from the floor to today (newest first; a compact picker if a row of buttons would be too long), and a slip may be entered for any day from the floor to today. Today stays the default.
- **Home tab:** a visit or a *Payment received* may be dated any day from the floor to today (and not before the course's start if the course records one — if it does, allow the start to be back-dated to the floor when the course is created).
- **Report:** every day from the floor is matched (✓ / the difference / *"Reception ne abhi nahi likha"*-equivalent in English). *"before the register"* is shown only for days **before the floor**.
- **Duty line `bhati.physio_register`:** counts days from the floor (01-Oct) up to yesterday, exactly as now otherwise. It will be due at once after the install (1–13 Oct are not yet entered) — that is intended: it is his backfill list.
- Nothing else changes: the slip rules, the void rule, the switch, reception's table (never written), the accountants' pack (untouched).

## 4 · Walk and norm (`BUILD_NORM_v1.md`)
Made-up database: a slip dated 02-Oct accepted; a slip dated 30-Sep refused; a home visit and a payment dated 05-Oct accepted; the report matches 01-Oct (✓ and a difference case); a day before the floor shows *before the register*; the duty is due with `{since}` = the oldest unmatched October day and clears when it matches; the floor read from the setting (change it in the walk → the rules follow). Negative control: the old files refuse 02-Oct. Installer order rehearsed (green, ALREADY INSTALLED, red-after-placing restores); SUMS; `.gitignore` (`*.json` blocked — ship `.json.kit` with the exact-path exception as S553 did); the number gate as PUBLISH runs it.

## 5 · Install, publish, report
Gates → pins → rebuild from the live bytes (counted edits) → walk (DRY stops) → `.bak_S554_<from8>` → place → setting written (INSERT OR IGNORE) → restart only `clinic-finance` (and whatever S553 found serves the list) → health → as `manoj`: the register's clinic tab offers 01-Oct; the report shows October's days matched; `/finance/aaj?as=bhati` shows the duty line → the undo line. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (CLAUDE.md). `claude_code_briefs/REPORT_S554.md` — 2 plain lines on top, then the proof. Append the install line to the board's `_numbers` claims if reachable; otherwise say so in the report.

**NEVER:** write `clinic_physio_day` or any physio row as data; print a phone number; spell the name "Bharti".
