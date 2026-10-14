# S553_BHATI_SLIP_DUTY — brief for the build runner (Agent SDK, the API credits)

*Written 14-Oct-2026 by the parent (session 313). Kit **S553** claimed on the board `_numbers` (v405 → v406) with its PLANNED line. This file is the whole scope. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S553_BHATI_SLIP_DUTY`.*

## 0 · For the owner (2–3 plain lines in the report)
Bhati's *Aaj ka kaam* list gets one new line: **the physiotherapy slips of a day are not in his register, or do not agree with reception's totals**. It appears the morning after such a day, opens his Physio register on that day, and leaves the list by itself when his entries agree with what reception wrote.

## 1 · The owner's word
- 14-Oct 05:43 IST: *"I have opened it for Bhati ... And also ... his daily slip entry goes on his staff duty list."* (S552_PHYSIO_REGISTER went live 05:29; he opened it for Bhati at about 05:4x.)
- Bhati's name is **Bhati** (login `bhati`). Never "Bharti".

## 2 · Pins and reads
- **FROM pins (read first; a different byte = STOP that file and report):** `/root/finance/aaj_duties.json` **2d6d30ebe73ff721d5591743c86eebb1** · `/root/finance/aaj_seed.py` **156ded1ee17b852b4a30e94be453ca61**.
- **Read whole before writing:** `aaj_kaam.py` (how an `extra` duty of `kind: "sql"` is read — the columns its SQL must return, `{since}`, `allowed_days`, `single`, `door`, `tile`; how a panel line in `aaj_seed.PEOPLE` switches a duty on; how `cfg_load` merges the owner's saved panel), `aaj_seed.py`, `aaj_duties.json`, and `physio_book.py` (S552: tables `physio_session` / `physio_course`, the clinic tab's day parameter, `clinic_physio_day`).
- Copy the shape of an existing extra `sql` duty exactly (e.g. `reception.docterz_consultation`), and an existing Bhati panel line (e.g. `bhati.petty_today`).
- `.gitignore` blocks `*.json` (last match wins, F-832): ship the duties file in the kit as `.json.kit` and add the exact-path exception line the way S487 and S507 did. No phone number of any kind (F-185).

## 3 · The duty
- **id** `bhati.physio_register`, **person** `bhati`, **kind** `sql`, group/period as the other daily Bhati lines.
- **Due** when there is a day **D** with **2026-10-14 ≤ D < today (IST)** where reception's row in `clinic_physio_day` has `cash_p + upi_p > 0` **and** Bhati's live clinic entries for D (`physio_session` joined to a `physio_course` of kind `clinic`, `voided_at = ''`) do not equal reception's cash and UPI **by mode**. The oldest such day is `{since}`; the count of such days is the number shown.
- **Wording** (Roman Hinglish for the line, English for the owner's panel): hi *"Physio slips register mein likhiye — {since} ki slips reception ke hisaab se nahin mil rahi"*; en *"Bhati: physiotherapy slips of {since} not entered in his register, or not agreeing with reception"*. **Door:** his register's clinic tab on that day (`/finance/physio/book` with the day parameter `physio_book.py` actually uses). **Tile:** the Physiotherapy tile.
- The panel line in `aaj_seed.PEOPLE['bhati']['lines']`: `when: 'day'`, `on: True`, opens the Physiotherapy tile. Do not touch any other person's lines (D690: never add to Amir's), and do not change or remove `bhati.physio_tick` — say in the report that it now overlaps and is the owner's to switch off on his panel.
- If the owner has already saved a panel for Bhati (`aaj_cfg`), make sure the new seed line appears on it switched on, as `cfg_load`/`_merge` do for a new seed line — prove it in the walk.

## 4 · Walk and norm (`BUILD_NORM_v1.md`)
Made-up database: a day where reception wrote ₹500 cash and Bhati entered ₹500 cash → not due; a day with no Bhati entries → due, `{since}` that day; cash agrees but UPI differs → due; a voided entry ignored; a day before 14-Oct → never due; today → never due; Bhati's list as `bhati` shows the line, and nobody else's list does. Negative control: the old two files show no such line. Then the installer's order, rehearsed on a made-up root (green, ALREADY INSTALLED, red-after-placing restores), SUMS, `.gitignore`, the number gate as PUBLISH runs it.

## 5 · Install, publish, report
Gates → the two FROM pins → rebuild from the live bytes (counted edits) → walk (DRY stops) → `.bak_S553_<from8>` → place → restart only what reads these files (find out from the code; `clinic-finance` if the list is served there) → health → as `manoj`: `/finance/aaj?as=bhati` shows the line or not as the data says (report which, and why, without names) → the undo line. Publish with `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat` (CLAUDE.md). Write `claude_code_briefs/REPORT_S553.md` — 2–3 plain lines on top for the owner, then the proof.

**NEVER:** write `clinic_physio_day` or any physio table; change another person's list; switch a line off; print a phone number.
