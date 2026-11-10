# START HERE — SESSION 424 — written at the S422 close (the parent), 10-Nov-2026 14:5x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work is F-1236 — the 36 X-ray pictures still waiting for staff** (his word 13:01 IST: "I do not want to leave any work for staff in Check karein as much as possible"). Then F-1226 (the calling list) if he has added the tracker's program folder.

*FIRST ACT: take session 424 from `board/_numbers` (RESERVED for the parent at the S422 close, v1191).* Counters at this close: **D888 · F-1238 · A-D25 · kit S777 · session 425 next.** Take a kit number BEFORE a scratch folder is named — and check the board's last lines first: the Sanjeevni chat took S771, S773 and S775 while S422 worked (F-1235).

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`. **Ask him in one line to add** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker` (F-1226) if it is not connected.

Standing rules: never run `git` in the device shell (F-511, F-1202); **a device commit is read back by staging it from the PC by md5 — the device VM's view of `D:\` can be stale (F-1237)**; the device VM's `/sessions` disk is full — work in `/tmp`; a database copy stays in the device VM, counts only come out (D656); read the clock before every write (F-510); kit scripts with `python -B` (F-1234). Work in `03_WORKING_PAPERS\S424\`.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713)**. The day page: the 11-Nov bundle should CONFIRM `/root/finance/records.py` bae45d82 and `/root/finance/xray_filmdate.py` f8ef85fd (DECLARED-PENDING at S422) and show the crontab line `# S772 X-ray film date`. The 08:00 health mail and the Sheet tracker's mail.

**B · F-1236 — THE PARKED X-RAYS.**
- Unpack `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz` (11-Nov) into the device VM's `/tmp`; the live `records.py` from the 11-Nov code bundle (bae45d82).
- For every `xray_filing` row still `check`: the file's name shape (a 1–3-digit number; two numbers; none), its film's dates and IDs (`xray_filmdate`), the X-ray patients and visitors of the film's day, why S752 / S772 (`_s772_day`) / S776 (`_s776_more`, `_s776_ok`) leave it — counts only. Also the same-name pairs on one day (identical films? same film date, same size).
- Expected kit on bae45d82: a 1–3-digit number in the name that is not an X-ray patient of the film's day is not an ID (the photo's sequence number); a second upload of the same film to duplicates. Walk with a control; cold review with a made-up wrong-patient probe (as S772, S776); the box proof; his install line.
- Then his one word on **unmatched pictures older than 7 days — off staff's list, onto his X-ray page only** (D887, proposed).
- With the kit: remove `/root/s770_probe/` (the probe and its ~370 MB venv).
- His page (read-only sub-agent, as manoj): `https://followup.dr-manoj.in/finance/records/xray-check` — at S422 14:3x: filed 79 · waiting 36 (Sep 20, Oct 13, Nov 3) · no-slip 1 · lab 42.

**C · F-1226 — the calling list's two rules** — exactly as `START_HERE_SESSION_422` §B (read `processor.py` WHOLE first; the 10-Nov list's 16 already-visited → 0; a CONTROL keeps them).

**D · Then the list:** Runbook §2A items 4 onward (the Patients plan's go first).

**Owner-side (board):** the publish of this close (records only) · the tracker's program folder · his word on unmatched > 7 days (after B) · his go on the Patients plan · the packs page passwords and shops · finger 20 and Arjun Dev's finger · MyOperator's written cause.

**Standing owner rulings:** as in `START_HERE_SESSION_418.md` (rules 1–92), D884, plus **D887**: a parked X-ray picture is filed by the date and clinic ID printed on its film (or its ID's one open X-ray day) only when the patient is confirmed; older copies and wrong-patient copies go to duplicates, never deleted; leave as little as possible for staff in Check karein; an X-ray with no slip goes to his no-slip list.

**Learned at S422:**
- **A rule that files to a patient needs a cold review with a wrong-patient probe** — three such cases were found in S772 and S776 before he installed.
- **The film carries what the file name lacks:** its date and the clinic ID (RapidOCR read 24/25 dates right); fresh exports carry no picture time.
- **Read the board's last lines before naming a kit folder** — two chats were minting kit numbers within minutes of each other.

*Written at the S422 close, 10-Nov-2026.*
