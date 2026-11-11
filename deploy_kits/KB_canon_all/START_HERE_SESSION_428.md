# START HERE — SESSION 428 — written at the S427 close (the parent), 11-Nov-2026 06:5x IST

**Project: Dr Manoj Clinic — Systems & Automation (the parent).** Open it in a fresh chat in this project, linked to manojz.
1. Follow `OPEN_ROUTINE_v1` (from the clone: `deploy_kits/KB_canon_all/OPEN_ROUTINE_v1.md`). The custom instructions are `COMMON_START_HERE_PROMPT_v1`.
2. **The first work is the Patients section (part 2)** on his console. Then **the Call Console's older follow-ups** and **the PC set-up kits kept current** — his notes of 06:47 IST 11-Nov (D899).

*FIRST ACT: take session 428 from `board/_numbers` (RESERVED for the parent at the S427 close).* Counters at this close: **D900 · F-1255 · A-D25 · kit S786 · session 429 next.** Take a kit number BEFORE a scratch folder is named — and read the board's last lines first (the Sanjeevni chat mints kits too).

*Connected folders:* `D:\Downloads`, `D:\dr-manoj-git`, `F:\ClinicBackup`.

Standing rules: never run `git` in the device shell (F-511, F-1202); a device commit is read back by staging it from the PC by md5 (F-1237); in the device VM keep database copies in `/tmp` with `TMPDIR=/tmp/...` (F-1248) and **write every script and part to `03_WORKING_PAPERS\S428\` as it is made — the VM's /tmp can vanish (F-1249)**; a database copy stays in the device VM, counts only come out (D656); read the clock before every write (F-510); kit scripts with `python -B` (F-1234). **If the device shell answers "Failed to create bridge sockets" (F-1250):** the file tools still work — build code-only in the cloud on an empty-schema database (with the live UNIQUE indexes, F-1251) and made-up patients; the box's installer re-runs every walk on a live copy.

## 0 · THE WORK — in order

**A · THE OPEN.** The board; **remind him of the packs page (D713)**. The day page. **The parent's DECLARED-PENDING is 4 until the 12-Nov bundle** (records.py 794cb87f, check_screens.py c259e6a2 — S782; portal.py 34750b24, owner_console.py 1a3d4fd4 — S785) + 2 standing rows. The two daily mails.

**B · THE PATIENTS SECTION — part 2 (D884, D894).** The mock-up `https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA` v4 on his console, fed by `dx_visit` (2,395 visits · 1,138 patients · 1,695 with a diagnosis at the 11-Nov copy) and the visit / follow-up data; the one-tap list of the unknown terms (29) — `dx_feed.unknown_terms()`, a tap writes `dx_term_map` and runs `dx_feed.reclassify()`. `owner_console.py` is now 1a3d4fd4 (S785 added a Needs-you line) — read its section code and finance_app's registration first (drift). He judges the screen, not the build.

**C · THE CALL CONSOLE — the older follow-ups (D899).** His words: from the grace period onwards, each older follow-up shows when the patient was **last called successfully**, and from there the **outcome, the call recording and the call transcript — all on his page**; the **recording only on the staff page** (no transcript), so the caller knows the last conversation, its outcome and when the patient was last reached. Read `/root/portal/calls_console.py`, the ring outcome and recording stores, and memory `areas/call-console.md` first. A mock-up for his look, then the kit.

**D · THE PC SET-UP KITS STAY CURRENT (D899).** The System tile's PC set-up files go stale although S723 (`pc_kits_current.py`, nightly) was built to repack what is behind: read its code and `PC_KITS_CURRENT_LATEST.txt`, find why, close it.

**E · Remove `/root/s770_probe/`** (~370 MB) in the next server kit (owed by F-1236's).

**F · Then the list:** Runbook §2A items 6 onward.

**Owner-side (board):** the publish of this close (records only) · the packs page passwords and shops · finger 20 and Arjun Dev's finger · MyOperator's written cause · reception's third evening export (the Clinical data report), once part 2 shows it.

**Standing owner rulings:** as in `START_HERE_SESSION_418.md` (rules 1–92), D884, D887, D893, D894, plus **D895** (X-ray pictures parked more than 7 days: off reception's Check karein — the owner's and Shavez's) · **D896** (filing order: the file name, then the slips and Docterz, then the film's own date / ID; names matched allowing the usual spelling — by sound; that day's patients closest first) · **D897** (the search box takes a clinic ID, a name or a mobile; the full mobile is shown on the match) · **D898** (his X-ray page: the portal tile and the Needs-you line) · **D899** (the Call Console's older follow-ups; the PC set-up kits).

**Learned at S427:**
- **A name rule that files to a patient must compare whole words by sound — letter likeness took ANIL for SUNIL** (caught by S776's own walk; four cold-review rounds closed eight more).
- **A walk's made-up patients must not collide with real IDs on the live copy** (F-1251 — the installer stopped safely).
- **The device VM's /tmp is not a store** (F-1249); **the device shell can fail while the file tools work** (F-1250) — the cloud fallback finished the job.
- **He needs to SEE where a page lives** — a page reachable only through a folded section is lost to him (S785).

*Written at the S427 close, 11-Nov-2026.*
