# REPORT S555_DESK_CORRECTIONS — the sorting desk's corrections (built, walked, rehearsed; NOT installed, NOT published)

**For Dr Manoj (plain English):**
- **On the laptop desk:**
  - The green *Save — next paper* button now always stays on screen; the boxes above it scroll.
  - Every date reads like 21-08-2025. You can type a date as 21-08-2025, 21-8-25, 21/08/2025 or 2025-08-21. A date that
    makes no sense is refused with one line, and nothing is saved.
  - A bill up to about a year old, such as Shri Ram B-0001, is no longer called "date looks misread".
- **When the supplier box holds your own name** (B-0010, B-0011, B-0012), the desk says so. It offers what Claude read
  instead: one tap fills the box, and nothing is saved until you press Save.
- **Under each box** (supplier, bill number, date, amount), a small grey "Claude read: … — use it" line appears whenever
  Claude read something different. Shavez never sees one on your Personal papers.
- **The Purchases list** names each lane in one word. Claude never reads a patient's paper.
- **It works:** every check passed on a copy of your data, and the same checks fail on today's files. Nothing is installed or
  published yet: the Scan App chat checks it, then you publish and paste one server line.

---

## For the chat — the proof

**Run:** 14-Oct-2026.
- FROM pins were read on the box at **08:46:40 IST**.
- Dev walk and control: 08:58:10–08:58:15 IST. L4 proof and rehearsal: 08:58:42–08:59:21 IST. Server scratch removed at
  09:00:56 IST. All box clock.
- This report was started at 09:01:16 IST (Windows clock).
- No build lock was taken, because nothing was placed. The lock was absent when read at 08:46.

**Read first:**
- the S551 brief (v4) and REPORT_S551 (round 0 and fix round 1);
- all 13 files of `deploy_kits\S551_SORTING_DESK\`;
- `S551_KIT_REVIEW_K2.md` (N1 → item 7; N2 needs no change);
- `BUILD_NORM_v1.md`.

### 1 · FROM pins (read on the box, all equal to the brief)

| file | md5 read | brief | lines |
|---|---|---|---|
| `/root/assetapp/sorting_desk.py` | `bb28d8c8d95435b4a566d2929f473587` | = | 1744 |
| `/root/assetapp/asset_register.py` | `c107c6bbb3e6c0c0d0535c5ed094b6e4` | = | 4347 |
| `/root/assetapp/claude_reread.py` | `47548ab97c55a1f4fb8d5d1a608a1681` | = | 142 |
| `/root/assetapp/clinic_papers.py` (read only, **not edited**) | `058c9bcb5a4973f8a15984b645ff57d7` | = | 1596 |
| `/root/assetapp/claude_reader.py` (read only) | `3894dc2358abd875ee61ced7619e1e1b` | = | 417 |
| `/root/assetapp/scanner_widget.js` (never edited) | `1143c77b13ae62652d4d961a92b9a9ab` | = | — |

- **`clinic_papers.py` was not edited.** Item 4's own-name words are already reachable: `suggest()` matches
  `_hits(v, _words(db, "own_name"), whole=False)`, and the desk calls exactly that through `CP`. It is the same list,
  including any `d664.words.own_name` additions in settings, with no export and no second list.
- **Item 6's cause, found in the list's code** (`bills_list`, AR:2410-2411):
  - The rejected-row branch printed `LANES[..][0].split(' ')[0]` ("Clinic", "Pharmacy", "Lab", …).
  - The live-row branch printed `.split(' — ')[0]` ("Clinic bill", "Pharmacy purchase", "Lab purchase", …).
  - Old rows with no `lane` all showed "Clinic", even a Pharmacy-kind row.

### 2 · The counted edits (`make_s555.py`; each anchor matched exactly once, on Windows and on the box)

**`sorting_desk.py` bb28d8c8 → `7e16fd80d6bd2bfe0a6e5366848d8569` (18 counted edits)**

| edit | item | anchor → change |
|---|---|---|
| 1 | — | `VERSION = "S551.2"` line → adds `CORRECTIONS = "S555"`. **VERSION is kept at `S551.2`**, because S551's walk (W2) reads it. |
| 2 | 2 | `_dmy` / `_dm` → `%d-%m-%Y`. Adds `parse_date()` (dd-mm-yyyy, d-m-yy, dd/mm/yyyy, yyyy-mm-dd; a two-digit year is 20yy) and `typed_date()` (ISO out; a value left as shown stays; anything else → `DeskError` "The date “…” is not understood — type it as dd-mm-yyyy. Nothing was saved."). |
| 3 | 5 | `reading()` also returns `supplier`, `number`, `date`, `amount`. The keys are `claude_reader.clean`'s: `vendor`, `bill_no`, `bill_date` (else `date_as_read`, parsed as in item 2), `total_amount`. Only rows with `ok=1` count, and a missing table is tolerated (unchanged). |
| 4 | 3 | `misread_date` → flagged when the date is before 2015-01-01, after scan day + 7, or more than 400 days before the scan day. The scan day is `created_at`, else `today`; the function still takes `today`. |
| 5 | 4, 5 | Before `paper_json`: `OWN_LINE`, `own_name(db, vendor)` (CP's own list), `_numkey`, and `claude_lines(db, b, rd, owner)`. `claude_lines` gives nothing for a pharmacy paper or a Personal paper to a manager, never offers an own-name reading, and never returns `made_out_to`. |
| 6 | 2, 4, 5 | `paper_json`: `date` is shown dd-mm-yyyy; adds `claude` and `own_line`. |
| 7 | 2 | `_fields`: `bill_date` goes through `typed_date` (refused = 400, rolled back, nothing written). |
| 8 | 2 | `note_paid` (Bills awaited): `typed_date`. |
| 9 | 2 | `implants_pay`: `typed_date`. |
| 10 | 1 | CSS: `#right` becomes a column flex box with `overflow:hidden`. Adds `#panel` (column, `min-height:0`), `#fields{overflow:auto;flex:1;…}`, `#foot{flex:none;…}`, `#empty`, `.cr`, `.use`. |
| 11 | 1 | `<div id=panel style=…>` → `<div id=panel><div id=fields>`. |
| 12 | 1 | `<div id=pagebox` → `</div><div id=foot><div id=pagebox`. |
| 13 | 1 | The close after `savednote` gains one `</div>` (the foot). |
| 14 | 4, 5 | The four boxes each gain a grey line under them (`cr_vendor`, `cr_bill_no`, `cr_date`, `cr_amount`), plus `ownline`. |
| 15 | 4, 5 | `draw()` calls `crs(j)`. |
| 16 | 4, 5 | New JS `useb()` / `crs()` before `paint()`. |
| 17 | 4, 5 | The click handler's selector adds `[data-f]`. |
| 18 | 4, 5 | The data-f branch: one tap fills the box, with no request and no save. |

**`asset_register.py` c107c6bb → `7ac386641095cacbac79594356e7ec6d` (5 counted edits)**

| edit | item | change |
|---|---|---|
| 1 | 8 | `_s550_claude` docstring: a patient's paper is not sent. |
| 2 | 8 | `_s550_claude`: `in ("personal", "resume")` → `+ "patient_paper"`. |
| 3 | 6 | `bills_list` Lane column: both branches print `{{lane_word(b)}}`. |
| 4 | 6 | `bills_list` render call passes `lane_word=_lane_word_s555`. |
| 5 | 6 | After `KIND_LANE`: `LANE_WORD` (Clinic · Pharmacy · NK Pathology · Personal expense · Other document) and `_lane_word_s555(b)` (lane, else lane by kind). This is the one place. |

**`claude_reread.py` 47548ab9 → `d9b75e784c4a806e941f3d1a243990e1` (3 counted edits)**
- docstring;
- the selection SQL `NOT IN ('personal','resume','patient_paper')`;
- `to_fill` skips `patient_paper`.

All three compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`. They were rebuilt on the box from the live bytes to
the same TO pins: in the dev run and inside each rehearsal install.

### 3 · The walk (`walk_s555.py`, on the box, isolated exactly as S551's)

**Isolation:**
- The live database was copied once with the backup API (`mode=ro`). All modules were imported from one scratch folder,
  with `__file__` asserted.
- The environment was set before the import: `ASSETS_DB`, `ASSETS_UPLOADS`, the made-up key file, the made-up URL
  `made-up.invalid`, `CLINIC_PORTAL_DIR`, `FINANCE_LOCAL_URL=http://127.0.0.1:9`, `SHARED_LIB_DIR` (a copy) and
  `FINANCE_DB_FOR_SCANS` (absent). `SARVAM_API_KEY` and `ANTHROPIC_API_KEY` were unset.
- Walk and control each ran in their own `python3` process. Rows were made up, suppliers differ in their first two words,
  and today was set to 2031-06-15.
- The own-name check uses a made-up word added to `d664.words.own_name` **on the scratch copy only**. No real name is used
  or printed.
- Both readers were tested with a stub that only counts calls, so nothing went to the network.

**Log (`_scratch\S555_DESK_CORRECTIONS\probe\dev1.log`), copied from the run:**
- **Walk on the built files: `19 checks: 19 GREEN, 0 RED`** (walk exit 0).

| check | what it proves |
|---|---|
| W1, W2, W4 | Isolated import; `CORRECTIONS == "S555"` with VERSION still `S551.2`; shared modules from the copy; no finance database. |
| I1 | In the served `/desk`, `save`, `savednote`, `pagebox` and `blank` sit inside `#foot`, not `#fields`; the boxes, groups and flags sit inside `#fields`; `#foot` and `#fields` are children of `#panel`, inside `#right`; `#list` is inside `#left`. |
| I1b | CSS: `#right` is a column with no `overflow:auto`; `#panel` has `min-height:0`; `#fields` has `overflow:auto` and `flex:1`; `#foot` has `flex:none`; `#list` keeps `overflow:auto`; the no-page-scroll rule is kept. |
| I2a | The desk's JSON reads `10-06-2031`, `scanned 12-06-2031`, covers `08-06-2031` and supplier note "oldest 08-06-2031". |
| I2b | Bills awaited, the ledger, The month and the desk carry no `12-Jun` and no ISO date in their visible text; the ledger reads "checked up to 15-06-2031". |
| I2c | `21-08-2030`, `5-6-31`, `21/08/2030` and `2030-08-21` are stored as ISO; `paid_on` from `13/06/2031`; `implant_payment.day` from `7-6-31`. |
| I2d | `31-02-2031` and `not a date` are refused (400, one line); the bill, the audit and the payment count are all unchanged. |
| I3 | Not flagged: 358 and 400 days before, 7 after. Flagged: 401 before, 8 after, and 2014. A desk paper 358 days old shows no date flag. |
| I4 | Own-name line plus Claude's offered supplier; an own-name Claude reading is not offered; nothing changes on looking. `suggest()` gives its "addressed to you" note for the same vendor. |
| I4b | The Save with the offered supplier stores it, with `desk_fields` audited. |
| I5 | Only CX1's date differs (supplier first two words equal, number equal ignoring spaces and case, amount equal to the rupee). CX2 gets all four lines (`₹1,500` / fill `1500`; the date from `date_as_read`). An `ok=0` reading gives none. The four line elements are on the page. |
| I5b | `made_out_to` and its value never appear in the lines. A Personal paper: 403 for the manager, lines for the owner. A pharmacy paper gives `({}, "")`. Nothing is saved by looking. |
| I6 | One word per lane for live, rejected and old (lane NULL, by kind) rows of all five lanes. |
| I8a | `_s550_claude` never calls the reader for a `patient_paper` (on the clinic lane, to test the subgroup clause itself); an ordinary paper still calls it. |
| I8b | `claude_reread._run` (from the scratch folder) selects the ordinary paper but not the patient's paper; `to_fill` gives (False, True). |
| T1, Z1 | Desk 19,727 B (9 ms), list 3,388 B, paper 492 B, **first load 33 ms**. The made-up rows live in the scratch copy only. |

- **Control on the live (S551) files: `19 checks: 6 GREEN, 13 RED (W2, I1, I1b, I2a, I2b, I2d, I3, I4, I5, I5b, I6, I8a,
  I8b)` and `CONTROL must-be-red: W2, I1, I2a, I2b, I2d, I3, I4, I5, I6, I8a, I8b -- all RED`** (exit 0).
  - Items 1–6 and 8 each have a named red.
  - The 6 that stay green test what already worked: W1, W4, I2c (the old `_norm_date` also read those four forms), I4b, T1
    and Z1.
  - The old files' own words:
    - I2a: `'2031-06-10', '12-Jun-2031', '08-Jun'`.
    - I2d: the bad date was saved (200, stored `not a date`).
    - I3: 358 days was flagged.
    - I6: `Clinic bill` / `Lab purchase` / `Pharmacy purchase`, and the old rows all `Clinic bill`.
    - I8a and I8b: the patient's paper was read.

### 4 · S551's walk re-run on the new files (as the brief asks)

**`87 checks: 86 GREEN, 1 RED (L4)`.** L4 requires the literal text `checked up to 15-Jun-2031` on the ledger page. Item 2
requires that date to read dd-mm-yyyy, so the two cannot both hold.

- **Proof that L4's only failure is that string:** a /tmp copy of `walk_s551.py`, with exactly 1 line changed
  (`15-Jun-2031` → `15-06-2031`), run on the same built files, gave `GREEN L4` and **`87 checks: 87 GREEN, 0 RED`** (log
  `probe\rehearse1.log`).
- The frozen S551 kit was not edited.
- **My call:** item 2 is specific ("every date the desk and its three pages show"), so I followed it. The single red
  S551 check is the corrected behaviour itself. If the chat wants S551's walk literally all green, the only route is to
  keep that one line in the old form, which item 2 forbids. I did not do that.

### 5 · The installer and the rehearsal

**`install_s555.sh`** uses S551's shape, with `S555_*` variables. Its steps, in order:
1. Gates: the box, root, the files.
2. Three FROM pins (ALREADY INSTALLED if all three are at TO).
3. `make_s555.py` from the live bytes.
4. TO pins.
5. Compile on both pythons.
6. Walk and control on a scratch copy (`DRY=1` stops here).
7. Three `.bak_S555_<from8>` backups, plus `assets.db.bak_S555_<time>` by the backup API. No database change is made; this
   is safety rule 6.
8. Place: desk, then re-read, then app. Read the md5 back.
9. Restart `assetapp` only.
10. `/healthz` 200 and **`/desk` 302 only** (item 7). Anything else restores and restarts.
11. The plain-English line, then the undo line.

**`rehearse_s555.sh`:**
- Runs on the made-up root `/tmp/s555dev/root`, with restart `true`.
- A stand-in python server answers `/healthz` 200 and `/desk` 302, then 404, then 200 by outcome.
- It refuses `/root/`, `systemctl` and port 8030.
- Log: `probe\rehearse1.log`. Result: **`REHEARSAL GREEN`**.

| outcome | result |
|---|---|
| 1 fresh install | DONE. Rebuilt 7e16fd80 / d9b75e78 / 7ac38664 = the pins. Walk `19 GREEN, 0 RED`; control `13 RED … all RED`; `/desk answers 302`. Backups beside all three. **The database's table schema was unchanged** (md5 of `sqlite_master` before and after). |
| 2 second run | `S555_DESK_CORRECTIONS: ALREADY INSTALLED` |
| 3 forced red after placing | restored to bb28d8c8 / 47548ab9 / c107c6bb; healthz 200; `NOT INSTALLED (restored…)` |
| 4 `/desk` 404 | "/desk answered 404, not 302" → restored to the FROM pins |
| 5 `/desk` 200 (item 7) | "/desk answered 200, not 302" → restored to the FROM pins |

- S551's installer accepted 200 (its line 127, `302|200`). Outcome 5 shows S555's does not.

**After everything (08:59 IST, box clock):**
- The live files are still at the FROM pins (all six re-read). There are no `bak_S555` files in `/root/assetapp`.
- `assetapp` is active, healthz is 200 and `/desk` is 302.
- `/tmp/s555kit` and `/tmp/s555dev` were removed (confirmed at 09:00:56).
- Nothing was placed, restarted or written live.

### 6 · The kit and the gates

**`deploy_kits\S555_DESK_CORRECTIONS\`, 13 files:**
- `KIT_ID.txt`, `README.md`, `install_s555.sh`, `make_s555.py`, `walk_s555.py`, `rehearse_s555.sh`;
- 3 `PIN_FROM_*.txt` and 3 `PIN_TO_*.txt`;
- `SUMS.md5`.

They use LF throughout. There is no `.json`, no database, no copy of a live file and no `__pycache__`.

**Byte-identical to what ran on the box** (md5 compared with `/tmp/s555kit` before it was removed): install 1d57685a,
make 27121a1c, walk fc104635, rehearse 5c9df4de, and all six PIN files. README (61b6eb53) and KIT_ID (118f0ebc) were
written after the box run; they are not executed.

**Gates:**
- **SUMS.md5:** 12 lines, 0 mismatches.
- **`.gitignore`:** `git check-ignore -v --non-matching` (last match wins) shows all 13 kit files as not ignored. This
  report was checked the same way.
- **Contact-number gate,** run as PUBLISH_ALL runs it (`python -B deploy_kits\NO_PHONE_NUMBERS.py --files-from <list>
  <repo>`): `NO_PHONE_NUMBERS: clean -- 13 staged file(s) checked (numbers and credentials).` Run again with this report
  added: `clean -- 14 staged file(s) checked`. This report is not ignored.

### 7 · Calls I made (the brief left room), each with its reason

1. **VERSION stays `S551.2`; `CORRECTIONS = "S555"` marks the build.** S551's walk checks VERSION, and must stay green
   except for L4.
2. **The own-name offer also sits in the own-name line**, which spans the panel's width. The narrow line under the Supplier
   box is left empty in that case, so the offer is not shown twice. An own-name Claude reading is never offered.
3. **A typed date equal to what the box showed is kept as it is,** even when the stored date is not a clean date (an old
   OCR string). Untouched, it never blocks a Save. Anything changed must be understood, or it is refused.
4. **A two-digit year is 20yy.**
5. **Item 6 shows an old row with no lane by its kind.** That is the same rule the desk uses (`KIND_LANE`). Before, such
   rows always read "Clinic".
6. **I8a tests the subgroup clause on a clinic-lane patient's paper.** A paper on `other_doc` was already skipped, so it
   could not show the new clause.
7. **Rehearsal outcome 5 (`/desk` 200)** was added beyond the brief's four, to prove item 7.
8. **The database backup is taken even though nothing in the database changes** (safety rule 6).

### 8 · Not done, and why

- **Not installed and not published,** as the brief says.
- **No real-browser look at 1366 × 768.** This runner has no browser, and no `node` on either machine for a JS syntax check.
  - The layout is proven from the served HTML structure and CSS (I1, I1b).
  - The added JS (`useb`, `crs` and the click branch, 6 lines) was read through by eye after extraction.
  - The chat's cold review, or the owner's first look, should confirm both on the laptop.
- **No DUTY_MAP change:** the kit adds, moves and removes no duty, and the brief forbids the edit.
- **S551's walk L4** stays red on the new files by design (§4).

### 9 · Seen outside the brief (not touched)

- `claude_reader.py`'s `_date` keeps only 2015 … next year when it stores `bill_date`. A Claude date outside that range
  reaches the desk only through `date_as_read`, which the desk parses as in item 2. Nothing to change now.
- The S551 FOR-THE-PARENT lines (`packs.py` and the challans; the portal tile name) still stand.

### 10 · Cost

About **US$5** of API credit for this run, read from this session's budget meter when this report was written (US$4.80 at
09:01 IST, plus this report and the last gate).

**Nothing installed, nothing published.**
