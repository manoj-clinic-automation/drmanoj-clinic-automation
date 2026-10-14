# REPORT S557_MACHINE_PAGES — the machine pages and the leftovers (built, walked, rehearsed; NOT installed, NOT published)

## Fix round 1 (S557_FIX1, 14-Oct-2026) — rebuilt, re-walked, re-rehearsed; NOT installed, NOT published

**For Dr Manoj (plain English):**
- The review found one real fault. If you deleted the newest machine and then made a new one, the new machine could show the
  old machine's parts and cover. It could also change one of the app's own reminders. A deleted bill could do the same: its
  number could pass to the next scanned bill.
- That is fixed. Each part, cover and bill link now remembers exactly which machine and which bill it was made with. If
  that machine or bill is gone, the link is set aside. It is kept, never deleted, and never shown on the wrong machine.
- The checks pass on a copy of your data, and the same checks fail on the previous version. Nothing is installed yet.

**For the chat:**

*What changed.* `asset_machine.py` only. `asset_register.py` and `sorting_desk.py` and their TO pins are unchanged
(9e94b11c / 91a04674, rebuilt again on the box to those pins).
1. **Fingerprints (BL1, C1):**
   - `asset_part` and `asset_cover` gain `asset_created_at` and `bill_created_at`; `service_logs` gains `bill_created_at`.
     All are additive (in the `CREATE` for the new tables, plus guarded `ALTER`s that tolerate the two-worker race).
   - All are written in the same request that makes the link (`part_add`, `cover_add`, `spend_add`, `spend_paper`).
   - Every read filters on them: the cover line, the totals, the three folds, the reminders' `_wanted`, `part_remove` /
     `cover_void`, `_paper_view` and `linked()` (part / cover / spend).
   - `strays()` + `detach()` run first in `heal()` (at each start and when Renewals opens):
     - a part or cover whose machine is gone, or is now a different machine → `asset_id = -asset_id`, `expiry_id = NULL`;
     - a paper link whose paper is gone, or is now a different paper → `bill_id = NULL`, `bill_created_at = NULL`.
   - Each detach is one `desk_audit` row (`machine_detached` / `machine_paper_detached`, with what it was). Nothing is deleted.
   - A NULL fingerprint is never filled later. It counts as unmatched (none exist before install).
2. **A reminder is S557's own only by all three tests (BL1):**
   - Its id is the row's `expiry_id`.
   - It is `entity='asset'` with `entity_id` = the row's machine.
   - Its label starts with one of `OWN_PREFIXES` = *AMC — · CMC — · Warranty — · Insurance — · Other — · Cover — ·
     Part warranty —*. This is one constant, built from `KINDS`.

   Anything else is never updated or resolved: the row lets go of it (audited as `machine_reminder_let_go`) and a fresh
   reminder is made. The adoption step applies the same three tests.
3. **Report §9 corrected (C2):** see §9 below.
4. **Walk:** three new checks, F1a, F1b and F1c. Each sets up a real id re-issue and asserts it as a precondition: the
   deleted row was the newest, and the new row got its id. The app's own doors are used: `POST /assets/<id>/delete`,
   `POST /assets/new` with a warranty date, `POST /bills/<id>/delete`, and the old *Add service* form with a part warranty.
   W3 now asserts the fingerprint columns. A `--must-red LIST` option was added for the second control.

**New pin:** `asset_machine.py` NEW → **`66c37197ae7c0d63874e213d52e7b9e5`** (was `ec874720`). `PIN_TO_asset_machine.txt`,
`SUMS.md5` (15 lines, 0 mismatches), `README.md` and `KIT_ID.txt` were all updated. `install_s557.sh`, `make_s557.py` and
`rehearse_s557.sh` are byte-unchanged (08316fe2 / da35abb4 / 96227cfb). The new walk is `140d8742`.

**Pins re-read on the box at 11:12:28 IST** (box clock), all equal to the brief:
- `asset_register.py` 7ac38664, `sorting_desk.py` 7e16fd80;
- `clinic_papers.py` 058c9bcb, `claude_reread.py` d9b75e78, `claude_reader.py` 3894dc23, `scanner_widget.js` 1143c77b;
- no `asset_machine.py`, no `bak_S557`, no build lock.
- The schema the fix relies on: `assets.created_at` and `bills.created_at` are `NOT NULL DEFAULT datetime('now')`, 0 empty.

**Counts, printed in the log** (dev run 11:20:25–11:20:42 IST; `_scratch\S557_MACHINE_PAGES\fix1\dev_fix1_2.log`; the same
isolation as before: backup-API snapshot, scratch import, env set before import, separate processes):

| run | result |
|---|---|
| walk on the built files | **`41 checks: 41 GREEN, 0 RED`** (38 as before + F1a, F1b, F1c) |
| control on the live S555 files | **`41 checks: 7 GREEN, 34 RED`**; `CONTROL must-be-red: … F1a, F1b, F1c -- all RED` |
| **control 2:** the new app files + the PREVIOUS `asset_machine.py` ec874720 | **`41 checks: 37 GREEN, 4 RED (W3, F1a, F1b, F1c)`**; `CONTROL must-be-red: F1a, F1b, F1c -- all RED` |
| S555 walk on the new files | **`19 checks: 19 GREEN, 0 RED`** |
| S551 walk (1 date line in dd-mm-yyyy) on the new files | **`87 checks: 87 GREEN, 0 RED`** |

**Control 2 in the old file's own words** (the review's faults, reproduced):
- F1a: the new machine reads *Covered: AMC by WALKPROV DEL till 01-01-2032*, and the app's own `Warranty` row is not
  byte-equal (it was rewritten).
- F1b: the new paper's page reads *Linked to WALK S557 MACHINE A as part; … as cover*, and the desk note adds *… as spend*.
- F1c: the app's `Part warranty: WALK FAN FC` row was rewritten to *Warranty — WALKPROV FC*.

On the new file all three are green:
- the new machine reads *No cover*;
- both app rows are byte-equal;
- the old rows sit at `-asset_id` / `bill_id NULL`, with the row counts unchanged and 2 + 3 audit rows.

**Rehearsal** (`rehearse_s557.sh`, made-up root, ended **11:22:19 IST**): **`REHEARSAL GREEN`**.
- Outcome 1, fresh install: DONE. Rebuilt 66c37197 / 91a04674 / 9e94b11c = the pins. Walk 41/41; control 34 RED, all
  named; S555 19/19; S551 87/87. Tables `False False False` → `True True True`. `machine.on: absent`. The undo line starts
  `\cp -p`.
- Outcome 2: ALREADY INSTALLED.
- Outcome 3 (forced red): restored to 7e16fd80 / 7ac38664.
- Outcome 4 (`/desk` 404): restored.
- Outcome 5 (`/desk` 200): restored.

**Byte-identical to what ran:** the box's md5 of every kit file at 11:22:19 equals the repository copy: asset_machine
66c37197, walk 140d8742, install 08316fe2, make da35abb4, rehearse 96227cfb, PIN_TO_asset_machine 59df1faf. README,
KIT_ID and SUMS were rewritten after the run; they are not executed.

**After (11:22:33 IST):**
- All six live files are still at the FROM pins. There is no `asset_machine.py` and no `bak_S557` file.
- The live database has no `asset_part`, `asset_cover` or `service_logs.bill_id`, and `machine.on` is absent.
- `assetapp` is active, healthz is 200 and `/desk` is 302.
- `/tmp/s557kits`, `/tmp/s557dev` and `/tmp/s557_install_*` are gone. No lock was taken, because nothing was placed.

**Calls I made, and limits:**
- **The review's alternative (wrapping `asset_delete` / `bill_delete`) was not used.** The brief chose fingerprints. The
  heal detaches on the next start or the next Renewals visit. Before that, every read already ignores the stray row.
- **On detach the row's `expiry_id` is cleared too.** The id it held now belongs to someone else's reminder. The old value
  is in the audit row.
- **Fingerprint resolution is one second** (`datetime('now')`). Suppose the owner deletes the newest machine and a new
  machine is saved within the same second. Then the fingerprint would match. That cannot be done by hand through two
  forms. It is named here so it is not hidden.
- **Out of scope (not touched):**
  - The *purchase* link is the app's own `assets.bill_id`. `bill_delete` leaves it dangling, so a re-issued paper can read
    *Linked to X as purchase*. Fixing it would need a column on `assets` or an edit to `asset_register.py`; both are
    outside this brief.
  - In the same way, the app's own `bill_audit` rows of a deleted paper pass to a paper that re-uses the id.
  - `install_s557.sh`'s header comment still lists the additive change as "asset_part, asset_cover, service_logs.bill_id".
    The brief did not name the installer for change, and its data step makes the new columns all the same (outcome 1).
- Review notes N6, N7 and N9 (the stamp box accepting dup/page-of papers, the stamp-exists probe, the `from_paper`
  double-submit) were not in this brief, and were left.

**Gates:**
- **SUMS.md5:** 15 lines, 0 mismatches. The kit has 16 files, all LF, with no `__pycache__` or `.pyc`.
- **`.gitignore`:** `git check-ignore -v --non-matching` (last match wins) shows all 16 kit files, this report and the
  brief as not ignored.
- **Contact-number gate,** run as PUBLISH_ALL runs it, over those 18 files: `NO_PHONE_NUMBERS: clean -- 18 staged file(s)
  checked`. It was run again on this report after this line was written.
- Nothing was committed, pushed or published.

**Cost of this fix round:** about **US$3.5** of API credit, read from this session's budget meter when this section was
written.

---

## The first build (S557_MACHINE_PAGES, 09:29–09:52 IST) — as reported then; §9 corrected by fix round 1

**For Dr Manoj (plain English):**
- **Each machine's page** now opens with one line on its cover, for example *"Covered: AMC by … till 01-08-2032"*. The line
  turns amber in the last 30 days and red once the cover has lapsed. A second line gives what the machine cost, what has
  been spent on it since, and what its cover cost.
- **Below the details are three folds: Parts, Cover history and Spends.** Each row can carry its scanned bill (type its
  B-number). Every cover and every part warranty puts one reminder on Renewals.
- **To add a cover or a part,** open the machine and fill the small form at the foot of *Cover history* or *Parts*. A
  renewal is just the next cover. A part that is changed is marked *Replaced / removed* and is never lost.
- **A bill you file as Clinic equipment** shows *+ asset record*. One tap opens a new machine form, already filled in from
  that bill.
- **Shavez sees none of this until you switch on** *Machine pages for Shavez* on the Switches card. You have it at once.
  Every check passed on a copy of your data, and the same checks fail on today's files. Nothing is installed or published
  yet.

---

## For the chat — the proof

**Run:** 14-Oct-2026.
- FROM pins were read on the box at **09:29:09 IST**.
- The final dev walk and control ran at 09:48:41 IST. The final rehearsal ended at 09:50:56 IST. The live state was
  re-read and the server scratch removed at **09:52:13 IST**. All times are from the box clock.
- No build lock was taken, because nothing was placed. The lock was absent at 09:29 and again at 09:52.

**Read first:**
- the S551 v4 and S555 briefs, and REPORT_S551 and REPORT_S555;
- all of `deploy_kits\S555_DESK_CORRECTIONS\` (the shape copied);
- `S555_KIT_REVIEW.md` (B3 below);
- `BUILD_NORM_v1.md`.

### 1 · Pins (read on the box; all equal to the brief — S555 is installed)

| file | md5 read | brief | lines |
|---|---|---|---|
| `/root/assetapp/asset_register.py` | `7ac386641095cacbac79594356e7ec6d` | = | 4361 |
| `/root/assetapp/sorting_desk.py` | `7e16fd80d6bd2bfe0a6e5366848d8569` | = | 1846 |
| `/root/assetapp/asset_machine.py` | absent (NEW) | = | — |
| `clinic_papers.py` (read only) | `058c9bcb5a4973f8a15984b645ff57d7` | = | 1596 |
| `claude_reread.py` (read only) | `d9b75e784c4a806e941f3d1a243990e1` | = | — |
| `claude_reader.py` (read only) | `3894dc2358abd875ee61ced7619e1e1b` | = | — |
| `scanner_widget.js` (never edited) | `1143c77b13ae62652d4d961a92b9a9ab` | = | — |

**TO pins:**
- `asset_register.py` → **`9e94b11c1a55eee6fdb22b9862b6db44`**
- `sorting_desk.py` → **`91a04674e27de3fbfc7602403403c821`**
- `asset_machine.py` NEW → **`ec8747205b8c29dc6a03d5221d613572`**

All three were rebuilt on the box from the live bytes to these pins, in the dev run and inside each rehearsal install. They
compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`.

**The names I relied on** (all found by text, as named in the brief):
- the existing tables: `expiries`, `service_logs`, `assets.bill_id`, `bill_items.asset_id`;
- the app's helpers: `asset_or_403`, `can_see_price`, `_backfill_asset_from_bill`, `entity_default_location_id`,
  `_audit_bill`, `_lane_word_s555` / `LANE_WORD`;
- the desk's tables and routes: `desk_audit`, `POST /desk/switch` and its `SWITCHES` tuple;
- Claude's reading: `claude_reading` (`ok=1`), whose items carry `make`, `model` and `serial`.

### 2 · The counted edits (`make_s557.py`; each anchor matched exactly once, on Windows and on the box)

**`asset_register.py` 7ac38664 → 9e94b11c (10 counted edits)**

| edit | item | anchor → change |
|---|---|---|
| 1 | B1 | `page()`, after `flow = ctx.pop(...)`: when a page passes `lanes=LANES` and the user is an owner or manager on the bill page, the lanes page or a papers page, it gets `LANES_SHORT_S557` (the same tuples with S555's one word first). |
| 2 | B1 | The `bill_lane` flash shows the one word. |
| 3 | B1 | The `lanes_admin` flash shows the one word. |
| 4 | A1 | `asset_view` template: `{{s557[0]}}` (the cover line and the totals) before the details grid. |
| 5 | A2–A4 | `asset_view` template: `{{s557[1]}}` (the three folds) after the details grid. |
| 6 | hook | `asset_view` render: `s557=_s557_machine(a)`. This is the machine page's one hook. |
| 7 | A5 | `renewals()`: `_s557_heal(db)` before the list is read. This is the renewals hook. |
| 8 | A6 | `bill_view` template: `{{s557_line}}` ("Linked to … as …" / "+ asset record"). |
| 9 | A6 | `bill_view` render: `s557_line=_s557_paper_line(b)`. |
| 10 | mount | After `# --- S551_SORTING_DESK end ---`: `LANES_SHORT_S557`, `_S557_SHORT_EPS`, the four guarded helpers, then the guarded `import asset_machine` / `init()`. |

**`sorting_desk.py` 7e16fd80 → 91a04674 (15 counted edits)**

| edit | item | change |
|---|---|---|
| 1 | — | Adds `MACHINE = "S557"`. `VERSION` (S551.2) and `CORRECTIONS` (S555) are kept, because the two older walks read them. |
| 2 | B2 | `import math` |
| 3 | A7 | `SWITCHES` gets `("machine.on", "Machine pages for Shavez")`. That tuple is `/desk/switch`'s allowed list. |
| 4 | A7 | `switch_states` gets `machine.on`. |
| 5 | B2 | `reading()`: an amount that is not finite → None. |
| 6 | B2 | `_qty`: a quantity that is not finite → "", and `OverflowError` is caught. |
| 7 | B2 | `_plain`: a value that is not finite → "". |
| 8 | B3 | `claude_lines`: the stored date is compared with `parse_date(..) or _iso(..)` (review N2). |
| 9 | A6 | Before `paper_json`: `_s557_machine`, `_s557_linked`, `_s557_add_to`. None of them calls `url_for`. |
| 10 | B1, A6 | `paper_json`: `"lane": AR._lane_word_s555(b)` and `"linked"`. |
| 11 | B1 | Bills awaited's line (challan row) uses the one word. |
| 12 | B1 | Bills awaited's line (final row) uses the one word. |
| 13 | A6 | `month_data`, Clinic-equipment row: `"add_to"` = ('machine', bill) or the old ('item', bill item). |
| 14 | A6 | The month template's `+ asset record` goes to `add_to`. |
| 15 | A6 | Desk JS: the Clinic-equipment note appends `j.linked`. This is the only JS added, one line. |

**`asset_machine.py` (NEW, 47 kB):**
- `ensure()` creates `asset_part` and `asset_cover` exactly as the brief, and adds `service_logs.bill_id`. It tolerates the
  two-worker race.
- `sync_asset()` / `heal()` manage the reminders. `heal()` writes only when something is out of line, then under
  `BEGIN IMMEDIATE`. It re-links a lost link to the machine's own reminder of the same label before it would ever insert.
- `sections()` builds the cover line, the totals and the three folds.
- Six POST routes and `GET|POST /bills/<id>/machine` (owner only).
- The stamp box goes through `find_paper` / `refusal`. The paper line comes from `linked` / `paper_line`.
- A `--ensure <db>` command line is the installer's data step.

### 3 · The walk (`walk_s557.py`, on the box, isolated exactly as S555's)

**Isolation:**
- The live database was copied once (backup API, `mode=ro`) to a snapshot. Every run copies from that snapshot.
- All modules were imported from one scratch folder, with `__file__` asserted.
- These were set before the import: `ASSETS_DB`, `ASSETS_UPLOADS`, the made-up key file and URL, `CLINIC_PORTAL_DIR`,
  `FINANCE_LOCAL_URL=http://127.0.0.1:9`, `SHARED_LIB_DIR` (a copy) and `FINANCE_DB_FOR_SCANS`. `SARVAM_API_KEY` and
  `ANTHROPIC_API_KEY` were unset.
- Rows were made up (machines `WALK S557 …`, suppliers and providers `WALK…`, which differ in their first two words; stamps
  `Z-2031-S7…`), with a made-up today of 15-Jun-2031.
- The baseline, the walk and the control each ran in their own `python3` process.

**Log (`_scratch\S557_MACHINE_PAGES\probe\dev3.log`, `rehearse2.log`):**
- **Walk on the built files: `38 checks: 38 GREEN, 0 RED`.**

| check | what it proves |
|---|---|
| W1–W4 | The import is isolated. `asset_machine` S557 is mounted, and the markers are kept. The schema matches the brief exactly, with `service_logs.bill_id`. |
| K1 | `machine.on` absent: a manager's machine page is **byte for byte** the live files' page (A7). |
| K2 | Reception's intake is **byte for byte** the live files' intake (B1). |
| A7a | With the switch absent, the owner has the sections at once; a manager's write gets 403 and nothing is written. |
| A1a–A1d | The cover line in each state: *No cover*; *Covered: AMC by WALKPROV ONE till 14-06-2032*; amber *Under warranty till 01-07-2031 — 16 days left*; red *… lapsed on 01-05-2031*. |
| A1e | The totals read exactly *Bought for ₹1,00,000 (01-02-2030) · Spent since ₹3,000 on 2 repairs/services · Cover paid ₹12,000*. |
| A1f | On a `hide_price` machine, a manager's page carries no ₹ figure; the owner's does. |
| A7b | The Switches card shows *Machine pages for Shavez*. `/desk/switch` wrote `machine.on`, audited. |
| A2a | A manager, with the switch on, adds a part with its paper. Dates are stored ISO and *by whom* is recorded. |
| A2b | Replaced / removed: the row is kept and moved to the removed list, its reminder resolved; the live part's reminder stays open. |
| A3a | A renewal resolves the older period's reminder; the new reminder is open with label, till and remind days. |
| A3b | Void: the row stays, struck through, and its reminder is resolved. |
| A3c | *From the old record: AMC — WALKOLD SERVICES · ₹5,000/yr* appears once. The machine row is byte-equal before and after, and no cover row was made from it. |
| A4a | A spend with its paper; per-year totals *2031 ₹2,500 · 2030 ₹800*. |
| A4b | The old *Add service* form still works, and a paper can be linked to its entry afterwards. |
| A5a | 6 reminder rows: 3 open (the AMC renewal, the warranty, the live part) and 3 resolved. |
| A5b | **Two re-imports change nothing.** A changed till date is updated in place. A nulled link is re-linked to the same row. The expiry ids are identical before and after. |
| A6a | The stamp box refuses a pharmacy paper, a patient's paper and a bad date. Nothing is written. |
| A6b | A manager's Personal paper is refused; the owner may link it. |
| A6c | The paper's own page reads *Linked to WALK S557 MACHINE A as part; … as cover*. |
| A6d | *+ asset record* appears on a Clinic-equipment paper's page and on The month. The form is pre-filled from the paper and from Claude's reading (name, supplier, date, amount, make, model, serial). |
| A6e | Save makes the machine with `bill_id` = the paper and the bill-item bridge set. The paper reads *as purchase*, the desk note reads *Linked to WALK ANALYSER as purchase.*, and the month no longer offers *+ asset record*. |
| A7c | Reception gets 403 on all 7 new routes. No login gets the redirect. The from-paper page is the owner's (a manager gets 403). |
| B1a–B1d | The bill page (owner and manager) reads *Lane: NK Pathology* and its move list is in one word each. The lanes page, a paper's *Lane: NK Pathology*, the challans row *· Clinic*, the desk JSON *Clinic* and Bills awaited all carry no long form. |
| B1e | Reception's slip keeps *Clinic bill* (unchanged by design). |
| B2 | A Claude amount of NaN or text, and a quantity of Infinity: the paper answers 200, strict JSON, with no amount line. |
| B3 | A stored date `2031-06-05 10:00` against Claude's `2031-06-05` gives no date line. |
| T1, Z1 | The machine page is 15,171 B and answers in 62–117 ms. Only the scratch copy is written. |

- **Control on the live (S555) files: `38 checks: 7 GREEN, 31 RED`.**
  - `CONTROL must-be-red: W2, A1a, A1b, A1c, A1d, A1e, A1f, A2a, A2b, A3a, A3b, A3c, A4a, A4b, A5a, A5b, A6a, A6b, A6c,
    A6d, A6e, A7b, A7c, B1a, B1b, B1c, B1d, B2, B3 -- all RED`.
  - The old files' own words:
    - B1a: `Lab purchase — NK Pathology`.
    - B1d: `Clinic bill`.
    - B2: the paper gave 500.
    - B3: a `date` line was shown.
  - The 7 that stay green test what must not change: W1, W4, K1, K2, B1e, T1 and Z1.
- **W3 is not in the must-be-red list.** It reads the database, and the rehearsal's outcome 3 showed that a copy taken
  after an earlier install already has the tables. That made the control falsely "not red" on W3 alone. A1–A7, B1 and B2
  are all still named.

### 4 · The S555 and S551 walks on the new files

These run inside the installer too, with `asset_machine.py` on `PYTHONPATH` so it is mounted.
- **S555's walk: `19 checks: 19 GREEN, 0 RED`.**
- **S551's walk: `87 checks: 87 GREEN, 0 RED`.** It ran on a `/tmp` copy with exactly 1 line changed (`checked up to
  15-Jun-2031` → `15-06-2031`, S555's agreed form). The installer refuses if that line is not found exactly once. The
  frozen S551 kit was not edited.
- **One fault this found, and its fix:** S551's walk calls `month_data` outside a request. My first cut built the
  *+ asset record* URL there and crashed (73 of 74 reached). The URL is now built in the template (`add_to`), and the walk
  is 87/87.

### 5 · The installer and the rehearsal

**`install_s557.sh`** (S555's shape, `S557_*` variables). Its steps, in order:
1. Gates.
2. FROM pins for the 2 edited files; `asset_machine.py` absent; the 3 readers at their pins (it refuses otherwise).
   ALREADY INSTALLED if all 3 files are at TO.
3. `make_s557.py` from the live bytes.
4. TO pins.
5. Compile on both pythons.
6. One backup-API snapshot, then: the baseline (live files) → the walk → the control → the S555 walk → the S551 walk.
   `DRY=1` stops here.
7. `.bak_S557_<from8>` beside the 2 files, plus `assets.db.bak_S557_<time>`.
8. Place, then read the md5 back.
9. The data step `asset_machine.py --ensure`.
10. Restart `assetapp` only.
11. `/healthz` 200 and `/desk` **302 only**.
12. Report `machine.on` (left absent).
13. The plain-English lines and the undo line, written `\cp -p` (printf `'\\cp -p'`).

Any failure after placing puts both files back, sets `asset_machine.py` aside (renamed, never deleted), restarts and
re-checks healthz.

**`rehearse_s557.sh`:**
- Runs on the made-up root `/tmp/s557dev/root`, with restart `true`.
- A stand-in answers `/healthz` 200 and `/desk` 302, then 404, then 200 by outcome.
- It refuses `/root/`, `systemctl` and port 8030.
- Result: **`REHEARSAL GREEN`**.

| outcome | result |
|---|---|
| 1 fresh install | DONE. Rebuilt ec874720 / 91a04674 / 9e94b11c = the pins. Walk 38/38; control 31 RED, all named; S555 19/19; S551 87/87. The tables went from `False False False` to `True True True`. `machine.on: absent`. The undo line starts `\cp -p`. |
| 2 second run | `S557_MACHINE_PAGES: ALREADY INSTALLED` |
| 3 forced red after placing | Restored to 7e16fd80 / 7ac38664; asset_machine.py set aside; healthz 200. |
| 4 `/desk` 404 | "answered 404, not 302": restored. |
| 5 `/desk` 200 | "answered 200, not 302": restored. |

**After everything (09:52:13 IST, box clock):**
- All six live files are still at the FROM pins. There is no `asset_machine.py` and no `bak_S557` file.
- The live database has no `asset_part`, `asset_cover` or `service_logs.bill_id`, and `machine.on` is absent.
- `assetapp` is active, healthz is 200 and `/desk` is 302.
- `/tmp/s557kits`, `/tmp/s557dev` and every `/tmp/s557_install_*` are gone.

### 6 · The kit and the gates

**`deploy_kits\S557_MACHINE_PAGES\`, 16 files, all LF:**
- `KIT_ID.txt`, `README.md`, `install_s557.sh`, `make_s557.py`, `asset_machine.py`, `walk_s557.py`, `rehearse_s557.sh`;
- 2 `PIN_FROM_*`, 3 `PIN_TO_*` and 3 `PIN_READ_*`;
- `SUMS.md5`.

There is no `.json`, no database, no copy of a live file and no `__pycache__`.

**Byte-identical to what ran on the box** (md5 compared before `/tmp` was removed): install 08316fe2, make da35abb4,
asset_machine ec874720, walk 667e9c59, rehearse 96227cfb, and all 8 PIN files. README and KIT_ID were written after the box
run; they are not executed.

**Gates:**
- **SUMS.md5:** 15 lines, 0 mismatches.
- **`.gitignore`:** `git check-ignore -v --non-matching` (last match wins) shows all 16 kit files and the brief as not
  ignored.
- **Contact-number gate,** run as PUBLISH_ALL runs it: `NO_PHONE_NUMBERS: clean -- 17 staged file(s) checked`.
- This report was checked with the same two gates after it was written: not ignored, and `clean -- 18 staged file(s)
  checked`.

### 7 · B3 — the S555 review's notes, one line each

| note | decision |
|---|---|
| C1 | **Fixed for this kit:** S557's undo line (README and installer) uses `\cp -p`, and rehearsal outcome 1 asserts it. S555's frozen kit is not edited. |
| N1 | **Fixed** (= B2): a non-finite amount or quantity is ignored in `reading()`, `_qty` and `_plain`. |
| N2 | **Fixed:** the date comparison accepts a stored date with a time part (walk B3). |
| N3 | **Handled, not a desk defect:** S551's walk is re-run with its one date line in S555's form, in `/tmp` and in the installer. The frozen kit is untouched. |
| N4 | **Left:** `LANE_WORDS_S544` is reception's intake word list; merging it would change the intake, which B1 forbids. B1 uses S555's `LANE_WORD` as the one helper. |
| N5 | **Fixed where it is an owner or manager page** (B1). The staff list, the slip and the scan screen keep their staff words by design. |
| N6 | **Left:** `Jun 2031` is a month name, not a date. |
| N7 | **Left:** a two-digit year as 20yy is accepted behaviour, and the misread flag catches 2099. |
| N8 | **Nothing to fix:** this run also worked only in `/tmp` and removed it (§5). |

### 8 · Calls I made (the brief left room), each with its reason

1. **B1 on the papers pages without editing `clinic_papers.py`.** The brief pins that file read-only. Its pages render
   through `AR.page(…, lanes=AR.LANES)`, so the one swap in `page()` (edit 1) gives them the one word. That swap applies only
   to an owner or manager, on 7 named endpoints. Reception's pages never match (K2 and B1e prove it).
2. **A6's line on the paper's page is a counted hook in `bill_view`** (edits 8–9). This goes beyond the brief's A-list
   (the mount, the machine page and renewals), because A6 requires the line there; B1 edits the same view. It is guarded,
   and gives nothing if the module is absent.
3. **The renewals hook is the heal**, run before the list is read. A start also heals.
4. **A machine from a paper is a short form of its own,** owner only (as the existing A-D20 bridge is).
   - It is filed under *Dr Manoj Clinic*, category *Dr MK Clinic Equipment*.
   - Make and model go into the notes (`assets` has no make or model column). The full *Edit* is there afterwards.
   - It uses `assets.bill_id`, the first unbridged `bill_items.asset_id`, and `_backfill_asset_from_bill` (which fills
     blanks only).
5. **Reminder labels always carry " — ".** *"AMC — WALKPROV ONE"*, *"Warranty — no provider named"*. This means they can
   never equal `asset_edit`'s own `Warranty` / `Contract renewal` rows, which that form deletes and re-creates.
6. **When the newest period of a kind is voided, the period before it becomes current again,** and its reminder reopens. A
   part's reminder uses 30 days, because `asset_part` has no remind-days column.
7. **A manager on a `hide_price` machine** sees no ₹ figure and no paper link: the app's "price & invoices hidden" rule.
   While `machine.on` is OFF, a manager also gets no paper line and no desk note.
8. **Audit:** machine actions go to S551's `desk_audit`. A linked paper also gets `bill_audit` `machine_link`. No new
   audit table was added, because the brief lists the schema.
9. **The 3 read-only readers are gated in the installer.** The walk imports them, so the proof holds only for those bytes.
   `scanner_widget.js` is only hashed.

### 9 · Not done, and why; seen outside the brief

**Not done:**
- **Not installed and not published,** as the brief says.
- **No real-browser look at 1366 × 768,** and no `node` check of the one JS line added (S10).
  - The folds use the app's own `.card`, `table` and `details` styles.
  - The chat's cold review, or the owner's first look, should confirm both.
- **No DUTY_MAP change.** The kit adds no staff duty (parts, covers and spends are optional entries with no due state),
  and the brief forbids the edit.

**Seen outside the brief (not touched):**
- `asset_delete` and `bill_delete` (owner) hard-delete rows. These are existing doors.
  - *(Corrected by fix round 1, review C2.)* The first build said a deleted machine's rows "stay as orphans" and a deleted
    bill's link "shows as no paper". Both were true only until SQLite re-issued the id: no table uses AUTOINCREMENT. The
    next machine or paper took that id and inherited the rows and links (review BL1 / C1, reproduced by control 2).
  - **What is true now (66c37197):**
    - A part or cover is shown only on the machine whose `created_at` it carries.
    - A part's, cover's or spend's paper is shown, and listed as *Linked to*, only while the paper's `created_at` matches.
    - At the next start or Renewals visit the heal detaches a stray row (`asset_id = -asset_id`, or `bill_id = NULL`),
      audited, never deleted. No reminder is re-created for it.
    - A reminder that is not S557's own (id, machine and label) is never changed.
  - The purchase link (`assets.bill_id`, the app's own) is still left dangling by `bill_delete`. That is outside S557.
- The papers page's and the old month page's section headings *"Pharmacy purchases — Sanjeevni"* / *"Lab purchases — NK
  Pathology"* (in `clinic_papers.py`) are plural section names, not lane labels. They are left as they are.
- **FOR THE PARENT, still standing:** S551's lines on `packs.py` (awaiting challans; the clinic lane's three set-apart
  sections), and the portal tile's name.

### 10 · Cost

About **US$9** of API credit for this run. That is read from this session's budget meter: US$8.45 when the gates finished,
plus this report.

**Nothing installed, nothing published.**
