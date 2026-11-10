# START HERE — SESSION 422 — written at the S421 close (the parent), 10-Nov-2026 09:5x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work is F-1226 — the calling list's two rules** (his ask, 09:44 IST 10-Nov). Then ask him in one line for his go on the Patients plan (Runbook §2A item 3).

*FIRST ACT: take session 422 from `board/_numbers` (RESERVED for the parent at the S421 close, v1175).* Counters at this close: **D885 · F-1230 · A-D25 · kit S770 · session 423 next**. Take a kit number BEFORE a scratch folder is named (F-515).

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`, and (added by him at S421) `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker\data`. **Ask him in one line to add the program folder** `C:\followup_tracker_local_test_kit\local_test_kit\followup_tracker` — the S421 request through the access tool was refused by the session's safety check; he adds folders himself with *Add folder*. Do not retry the tool request unless he says yes.

Standing rules: never run `git` in the device shell (F-511, F-1202); a device commit under a new staged name, read back by md5 (F-1149); a database copy or a tracker CSV stays on manojz — counts only come out, never a name, number or ID (D656); read the clock before every write (F-510). Work in `03_WORKING_PAPERS\S422\`.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713)**. The day page (`--read`; before 05:30 IST its SSD line is falsely red, F-1227). Read the 08:00 health mail of the day ("last 24h" must show one day, else F-1212 reopens) and the Sheet tracker's 09:4x mail — S421 did not reach them.

**B · F-1226 — the tracker's two rules (`processor.py` on manojz).**
- Read `processor.py` WHOLE first — its follow-up matching (`find_called_in_and_due`, the visit↔follow-up join, "DIKHA CHUKE→RESOLVE") — and `push_followups_today.py`, which fills the Callback Tracker sheet's sections.
- Rule (a): a visit from **due − 3 days** closes the follow-up. Rule (b): a visit closes **every** open row of that patient (same patient ID; mobile-only and name-only matches stay as today — never close on a name).
- Prove on a COPY of the live data folder in the device VM: the 10-Nov list's 16 already-visited (12 early, 4 by rule b) drop to 0; no row closes without a same-ID visit; a CONTROL (the old code) keeps them. Then a cold review.
- Install the way he already runs the tracker (a copy block on manojz; the old file kept beside it); the staff's sheet and sections unchanged; the manual run the fallback. Read the next pushed list back.

**C · THE PATIENTS PLAN (D884, F-1225) — his go in one line, then part 1** (the diagnosis feed): the Docterz *Clinical data report* daily as reception's third export + one catch-up export 01-Jul → today; the server reads it (the parent's `/root/finance` side, beside the Docterz pickup — find the reader the consultation export uses and add the CLINICAL kind); his taxonomy (the project file `Orthopedic_Diagnosis_Taxonomy_Master.xlsx`) maps raw terms; unknown terms to a one-tap list. Parts 2 and 3 after his live read of part 1. The mock-up: `https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA` (v4). The figures to reproduce: `S421_RETURN_PATTERN_ANALYSIS.md` (canon).

**D · Then the list:** Runbook §2A items 4 onward.

**Owner-side (board):** the publish of this close (records only) · the tracker's program folder · his go on the Patients plan · reception's one catch-up Clinical data report export (01-Jul → today) once the plan is a go · the packs page passwords and shops · finger 20 and Arjun Dev's finger · MyOperator's written cause.

**Standing owner rulings:** as in `START_HERE_SESSION_418.md` (rules 1–92), plus **D884**: the Case Pack packages are all his and edited per package; the seeding page's search is parked; June's figures are unreliable — use the months from August and allow for festival weeks; the calling list shows only patients who have not visited.

**Learned at S421:**
- **A month's "within 30 days" figure is open until its last visit is 30 days old** — read the data to its last day and say "so far" (F-1228; he caught it in one line).
- **A system's own status is not the truth** — the tracker's "never came" hid 130 visits; count from the visits (F-1229).
- **The data he means is often on his PC, not the server** — the tracker's folder held diagnoses, visits, follow-ups and calls; ask for the folder in one line and keep everything on the PC.

*Written at the S421 close, 10-Nov-2026.*
