# START HERE — SESSION 427 — written at the S424 close (the parent), 11-Nov-2026 04:4x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work is F-1236 — the 36 X-ray pictures still waiting for staff** (his word 13:01 IST 10-Nov: "I do not want to leave any work for staff in Check karein as much as possible"). Then **the Patients section (part 2)** — its feed is live since S779.

*FIRST ACT: take session 427 from `board/_numbers` (RESERVED for the parent at the S424 close, v1204).* Counters at this close: **D895 · F-1249 · A-D25 · kit S781 · session 428 next.** Take a kit number BEFORE a scratch folder is named — and read the board's last lines first (the Sanjeevni chat mints kits too).

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`, `C:\followup_tracker_local_test_kit` (the tracker).

Standing rules: never run `git` in the device shell (F-511, F-1202); a device commit is read back by staging it from the PC by md5 (F-1237); **in the device VM work in `/tmp` and set `TMPDIR=/tmp/...` — its `/sessions` disk is full (F-1248)**; a database copy stays in the device VM, counts only come out (D656); read the clock before every write (F-510); kit scripts with `python -B` (F-1234). Work in `03_WORKING_PAPERS\S427\`.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713)**. The day page. The parent's DECLARED-PENDING is 0 from this close (+ 2 standing rows the bundle never carries: /root/portal/NotoSansDevanagari-Regular.ttf, /root/wa/vitals/vitals_page.html) (the 11-Nov bundle confirmed S422's and S779's files). The two daily mails.

**B · F-1236 — THE PARKED X-RAYS.**
- Unpack `D:\Downloads\_kbtools\vps_code\finance_nightly.db.gz` (11-Nov or newer) into the device VM's `/tmp`; the live `records.py` from the code bundle (bae45d82, CONFIRMED).
- For every `xray_filing` row still `check`: the file's name shape (a 1–3-digit number; two numbers; none), its film's dates and IDs (`xray_filmdate`), the X-ray patients and visitors of the film's day, why S752 / S772 (`_s772_day`) / S776 (`_s776_more`, `_s776_ok`) leave it — counts only. The same-name pairs on one day (same film date, same size).
- Expected kit on bae45d82: a 1–3-digit number in the name that is not an X-ray patient of the film's day is not an ID (the photo's sequence number); a second upload of the same film to duplicates. Walk with a control; cold review with a made-up wrong-patient probe; the box proof; his install line.
- Then his one word on **unmatched pictures older than 7 days — off staff's list, onto his X-ray page only** (D887, proposed). Remove `/root/s770_probe/` with the kit.
- His page (read-only sub-agent, as manoj): `https://followup.dr-manoj.in/finance/records/xray-check`.

**C · THE PATIENTS SECTION — part 2 (D884, D894).** The mock-up `https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA` v4 on his console, fed by `dx_visit` (S779: 2,395 visits · 1,138 patients · 1,695 with a diagnosis at the 11-Nov copy) and the visit / follow-up data; the one-tap list of the unknown terms (29) — `dx_feed.unknown_terms()`, a tap writes `dx_term_map` and runs `dx_feed.reclassify()`. Read `owner_console.py` and finance_app's registration first (drift). He judges the screen, not the build.

**D · Then the list:** Runbook §2A items 4 onward.

**Owner-side (board):** the publish of this close (records only) · his word on unmatched > 7 days (after B) · the packs page passwords and shops · finger 20 and Arjun Dev's finger · MyOperator's written cause · reception's third evening export (the Clinical data report), once part 2 shows it.

**Standing owner rulings:** as in `START_HERE_SESSION_418.md` (rules 1–92), D884, D887, plus **D893** (the calling list: a visit from half the advised period before due closes a follow-up, never the visit that prescribed it; one visit closes every open follow-up of that patient; the late side unchanged) and **D894** (the clinical report feeds the diagnoses; a clinical report he exports on manojz reaches the server by itself).

**Learned at S424:**
- **A "they already came" rule must skip the visit that created the obligation** — 184 of 825 follow-ups are prescribed 1–3 days ahead (F-1247).
- **A reader that knows reports by their columns must test the narrowest report first** — the clinical report carries the consultation report's columns (F-1246; found before it did harm).
- **He decides what he can see; the numbers behind it are ours** — "too complicated for me" (18:39): the assistant set the half-period rule and said so in one line.

*Written at the S424 close, 11-Nov-2026.*
