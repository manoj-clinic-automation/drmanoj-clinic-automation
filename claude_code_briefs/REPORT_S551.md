# REPORT S551_SORTING_DESK — the sorting desk (built, walked, rehearsed; NOT installed, NOT published)

## Fix round 1 (S551_FIX1, 14-Oct-2026)

**For Dr Manoj (plain English):**
- The desk now keeps a patient's paper off every list and count except *Kept apart*, including a challan you set aside
  there, such as AINDOS 1952.
- If you mark an already-accepted paper as a *Challan*, it now waits so that its bill can pick it up later.
- Shavez can never see or join one of your Personal challans.
- The installer now also checks that the desk itself has started, and puts everything back if it has not.
- Every check passed again on a copy of your data, and the new checks fail on the old files. **Nothing is installed or
  published yet.**

### For the chat

**Run.** The brief `S551_FIX1.md` was read, together with brief v4 `S551_SORTING_DESK.md` (md5 read:
`5996dfd44d4bca9cc9a5eab3ecba5c6d`, = 5996dfd4), the first report, the review `S551_KIT_REVIEW_K1.md` and all 13 kit files.
The kit was revised in place. The kit number is unchanged.
- FROM pins were read on the box at **07:16:00 IST**. All 7 files equal the brief, and `/root/assetapp/sorting_desk.py`
  is absent: `asset_register.py` 3d5a36e3 · `clinic_papers.py` 5b197fb5 · `scanner_widget.js` 1143c77b · `claude_reader.py`
  3894dc23 · `claude_reread.py` 47548ab9 · `scan_checks_s441.py` b9ba6839 · `packs.py` d86d351a.
- The last box read was at 07:18 IST (from the box's clock). This section was written after 07:18:52 IST (from the
  Windows clock).
- No build lock was taken, because nothing was placed.

**What changed, item by item.**

| item | file | change |
|---|---|---|
| C1 | `install_s551.sh` | After restart and healthz 200, `/desk` must answer 302 or 200, polled up to `S551_HEALTH_TRIES` times. Anything else prints "/desk answered N: the desk did not mount" and runs `restore()`. |
| C1 | `rehearse_s551.sh` | The stand-in also serves `desk`. A new **outcome 4** removes it, so health is 200 but `/desk` gives 404, and requires the restore. |
| C2 | `sorting_desk.py` | `awaiting_challans()` excludes `subgroup='patient_paper'`. That one change covers the cards, the covers box, the Waiting "covers" reason, the supplier note and *Paid on challan*. Bills awaited's final-paper query also excludes patient papers. The Month's "challans waiting" count (`nwait`) excludes them. `waiting()` skips a patient's paper, so "papers still to sort" leaves it out; *Open B-____* still opens it. The section totals already filtered by subgroup. |
| C3 | `sorting_desk.py` `_doc_kind` | A Save as Challan whose state is `awaiting` on an `approved` paper sets status to `draft` on the clinic lane, or to `_lane_kind_status(lane)` on other lanes. It writes **`desk_challan_reopened`** `{status_from, status, lane, challan_state, via:"desk"}` by the person. This also applies when the paper was already an awaiting challan that the old heal had accepted. `approved_by`/`approved_at` are kept as history. |
| C4 | `sorting_desk.py` | `awaiting_challans(db, owner)` drops `subgroup='personal'` for a non-owner. `covers()`, `supplier_note()`, `waiting()`'s `sup_wait`, `awaited()` and **Save's `offered` set** all use it. So a manager's join of a Personal challan is refused on the server (400, nothing saved). |
| N2 | `walk_s551.py` H2 | H2 seeds a made-up row `Z-2031-H2R` and fetches `/bills?q=Z-2031-H2R`. It requires the row and its link to `/bills/<id>`, and no `<select name=lane`. It is now red on the old files. |
| N3 | `walk_s551.py` | `--expect-red` exits 0 only if every check in `MUST_RED` is RED. Those are **W2, S3, W3, C2, R2, V1, H2, FC2, FC3, FC4, FN5, FN6**: the desk route, the new SUB sections, the challan-not-accepted rule, the Personal guard, the seeded list and the fix checks. A check that is green or never reached fails the control. The control prints a `CONTROL must-be-red:` line, and the installer echoes it. W3 now also asserts that the three keys are in `SUB` and not in `SECTION_KEYS`. |
| N4 | `sorting_desk.py` | New `ensure_at_mount(path, tries=3, wait=1.0, timeout=3)`. A "database is locked" error is retried, then ignored with one stderr line, so `init()` still registers the routes. Any other error still raises. |
| N5 | `sorting_desk.py` `ledger` | A `closed` challan shows as "Challan (closed)" and owes nothing. |
| N6 | `sorting_desk.py` `month_data` | "Rate before" is read per section. The three consumables sections read only the consumables groups (`procedure`, `xray*`, `others`) on the clinic lane. Implant stock and Clinic equipment read only their own subgroup on the clinic lane. Construction reads its own subgroup on clinic or other_doc, never owner_expense. Personal, personal-expense and patient papers can never feed it. |
| — | `sorting_desk.py` | `VERSION` `S551.1` → **`S551.2`**. W2 asserts it. |

**Pins (built on Windows and rebuilt on the box from the live bytes; `make_s551.py` is unchanged, cf0a3688):**

| file | FROM | TO |
|---|---|---|
| `asset_register.py` | 3d5a36e3f9dc398a948f70a87f12d513 | **c107c6bbb3e6c0c0d0535c5ed094b6e4** (unchanged, 19 counted edits) |
| `clinic_papers.py` | 5b197fb5718f8d28ed8de6c0cafc9ab0 | **058c9bcb5a4973f8a15984b645ff57d7** (unchanged, 12 counted edits) |
| `sorting_desk.py` (new) | — | **bb28d8c8d95435b4a566d2929f473587** (round 0 was 3daa1e3a) |

All three compile on `/usr/bin/python3` (3.9.25) and on `/root/wa/venv/bin/python3`.

**The walk, the control and the extra proof** (on the box under `/tmp/s551dev`, the same isolation as round 0; log
`_scratch\S551_SORTING_DESK\probe\dev_fix1.log`; the counts below are copied from that log):
- **Walk on the built files: `87 checks: 87 GREEN, 0 RED`.** That is round 0's 81 checks plus FC2, FC3, FC4, FN4, FN5 and
  FN6. H2 and W3 are stronger.
  - FC2: a challan saved as *A patient's paper* is off Bills awaited (data and page), off the covers box and off Waiting.
    The supplier's bill loses its "covers" reason. The Month's challan count drops by 1, and *Kept apart* rises by 1.
  - FC3: an approved clinic paper saved as Challan becomes `draft`/`awaiting`, with `desk_challan_reopened`
    (status_from approved, by the owner). It is then offered in the bill's covers box and joined (`page_of`, `joined`).
  - FC4: a Personal challan is absent from the manager's covers box, his supplier note, his Waiting reasons and his Bills
    awaited page. His join is refused (400; the challan stays awaiting and the bill stays draft). The owner sees it.
  - FN4: under another connection's EXCLUSIVE lock, `ensure_at_mount` returns False without an error. Unlocked, it makes the
    4 tables. Its one stderr line appears in the walk's log.
  - FN5: with a closed priced challan, owed is 100, not 1,000.
  - FN6: "Rate before" reads "₹50 (Apr)" from the April procedure paper. It ignores the May Personal, personal-expense and
    patient-paper rates.
- Sizes and times: desk 18,293 B (8 ms) · list 4,709 B (18 ms) · paper 487 B (3 ms) · **first load 29 ms** · `/desk/month`
  14,537 B · `/desk/awaited` 16,451 B · `/desk/implants` 8,001 B.
- **The control on the live (old) files: `87 checks: 7 GREEN, 80 RED`, and `CONTROL must-be-red: W2, S3, W3, C2, R2, V1,
  H2, FC2, FC3, FC4, FN5, FN6 -- all RED`** (exit 0). The 7 still green test nothing new: W1, W4, H6, L3, F8, R3, Z1.
- **Extra proof (beyond the brief):** the new walk was run with round 0's `sorting_desk.py` (3daa1e3a) and the same built
  files. Result: `87 checks: 80 GREEN, 7 RED (W2, FC2, FC3, FC4, FN5, FN6, FN4)`. So each new check fails on exactly the
  first round's behaviour:
  - FC2: the patient challan was still counted.
  - FC3: the paper stayed `approved`, and the join was refused.
  - FC4: the covers box held the Personal challan, and the note said "1 open challan".
  - FN5: owed was 1,000.
  - FN6: "Rate before" was ₹888 (May), a patient's paper.
- **The three papers of the plan** were unchanged from round 0: B-0001 (waiting, date flag, nothing pre-selected) · B-0015
  (Construction work, not waiting) · AINDOS 1952 = B-0125 (waiting, Challan from Claude's reading, nothing pre-selected).

**The rehearsal** (`rehearse_s551.sh`, made-up root `/tmp/s551dev/root`, restart `true`, stand-in health; log
`_scratch\S551_SORTING_DESK\probe\rehearse_fix1.log`; ended **07:17:12 IST**). `REHEARSAL GREEN`:

| outcome | result |
|---|---|
| 1 fresh install | DONE. Inside the installer: walk `87 checks: 87 GREEN, 0 RED` · control `87 checks: 7 GREEN, 80 RED` · `CONTROL must-be-red: … all RED` · placed and read back at c107c6bb / 058c9bcb / bb28d8c8 · "/desk answers 200 … the desk is mounted" · `desk.floor/desk.on/new tables = 2026-10-14/absent/4` |
| 2 second run | `S551_SORTING_DESK: ALREADY INSTALLED` |
| 3 forced red after placing | restored to 3d5a36e3 / 5b197fb5; healthz 200; `NOT INSTALLED (restored …)` |
| 4 (C1) healthz 200, `/desk` gives 404 | "/desk answered 404: the desk did not mount" → restored to the FROM pins; `NOT INSTALLED (restored …)` |

**The C1 control (red on the old installer):** round 0's installer (2b58ddfc, with sorting_desk 3daa1e3a) ran on its own
made-up root `/tmp/s551dev/root0`, with the same guards and `/desk` answering 404. It printed "/desk answers 404 …" and then
**`S551_SORTING_DESK: DONE.`** (07:17:49 IST). The old installer could not see a desk that failed to mount; the new one
restores.

**After everything (07:18 IST):**
- The live files are still at the FROM pins, and `sorting_desk.py` is absent.
- Live database: no desk table, no `desk.*` setting, 158 bills and no made-up row.
- `assetapp` is active and `/healthz` answers 200.
- `/tmp/s551dev`, `/tmp/s551probe` and the install temp folders were removed.
- Nothing was placed, restarted or written live.

**The kit and the gates:**
- **13 files**, LF throughout, with no `__pycache__`, `.json` or database. The installer, patcher, walk, module, rehearsal
  and PIN files are byte-identical to what ran on the box: install 12729f27 · make cf0a3688 · sorting_desk bb28d8c8 · walk
  2343b449 · rehearse 22158f96 · PIN_TO_sorting_desk 49a3061f.
- README (ed8e4ee2) and KIT_ID (8b42e872) were updated after the box run. `SUMS.md5` was rewritten, and every line matches.
- `.gitignore`: `git check-ignore -v --non-matching` (last match wins) shows all 13 kit files and this report as not
  ignored.
- The contact-number gate was run as PUBLISH_ALL runs it (`python -B deploy_kits\NO_PHONE_NUMBERS.py --files-from <list>
  <repo>`) over the 13 kit files and this report. Result: `NO_PHONE_NUMBERS: clean -- 14 staged file(s) checked (numbers
  and credentials).` It was run again after this line was added.

**Calls I made (the brief left room), with reasons:**
1. **C3's audit:** one `desk_challan_reopened` line carrying the old status. I read the brief's "`subgroup` / a
   `desk_challan_reopened` line" as "audited, e.g. by a line named so". The Save's usual `doc_kind`, `relane` and
   `subgroup` lines are still written as before.
2. **C2: a patient's paper is also dropped from Waiting** (and so from "papers still to sort"). This follows "it appears
   only in *Kept apart*". *Open B-____* still opens it for a change.
3. **C4: a manager's tap of *Paid on challan* does not finalise the owner's Personal challans** of that supplier. A
   manager's action never touches a Personal paper. The owner's own tap still does.
4. **N6:** consumables rows read all three consumables groups (an item bought under *Others* gives its earlier rate to
   *Procedure room*). Every other section reads only itself, as "the consumables groups and the same sections as the row".
5. **N4:** each try waits up to 3 s, with 3 tries 1 s apart, so at most about 12 s per worker at start-up.
6. The new checks are named **FC2–FC4 and FN4–FN6**, because the walk already had checks C1–C13.

**Not done, and why:**
- Not installed and not published, as the brief says.
- No real-browser look (unchanged from round 0).
- `claude_reread.py` and `packs.py` are unchanged: the FOR THE PARENT lines below still stand.

**Cost:** about **US$4** of API credit for this fix round, read from this session's budget meter when the report was written
(about $3.7 at 07:18 IST, plus the report and the gates).

**Nothing installed, nothing published.**

---

## Round 0 (the first run, 14-Oct-2026 06:15–06:47 IST) — kept as history; its pins and counts are superseded above

**For Dr Manoj (plain English):**
- **What you get:** one sorting desk on the laptop for you and Shavez.
  - The waiting papers are on the left and the scan is large in the middle.
  - On the right is what was read (correct anything) and one list, *Where does it go?*.
  - One **Save — next paper** files the paper, accepts it and opens the next one.
  - Beside it are three pages: **Bills awaited** (challans by supplier), the **Implant stock ledger** (owed, paid, balance)
    and **The month** (section by section).
  - The scan app's header reads **Scan app & assets**, and its front page has a **Switches** card.
- **Shavez:** the desk is installed switched OFF for him. You can use it at once, and you switch it on for him from the
  Switches card when you are ready.
- **Shri Ram B-0001** is on the Waiting list, with nothing chosen for you. It shows one amber line, "the date looks misread —
  check". When you press *A patient's paper — surgical case pack*, it leaves the clinic's totals.
- **Krishna Sales B-0015** is already under Construction work and is not on the list. Open it by its number to change it.
- **AINDOS 1952 (B-0125)** is on the Waiting list, already marked *Challan* from Claude's reading, with nothing chosen for you.
  - *Implant stock* keeps it in the ledger as a challan waiting for its bill.
  - *A patient's paper* sets it aside.
- **It works:** every check passed on a copy of your data, and the same checks fail on today's files, which proves they test
  something real. **Next steps:** the Scan App chat checks the kit, then you double-click the publish and paste one server
  line.

---

## For the chat — the proof

**Run:** 14-Oct-2026. FROM pins read on the box at 06:16 IST. The last box read was at 06:46 IST, after the scratch
folders were removed. The report was written at 06:47 IST (both times read from a clock). No build lock was taken: nothing
was placed (brief §0).

### 1 · FROM pins (read on the box, all equal to the brief)

| file | md5 read | brief |
|---|---|---|
| `/root/assetapp/asset_register.py` | `3d5a36e3f9dc398a948f70a87f12d513` | = |
| `/root/assetapp/clinic_papers.py` | `5b197fb5718f8d28ed8de6c0cafc9ab0` | = |
| `/root/assetapp/scanner_widget.js` (never edited) | `1143c77b13ae62652d4d961a92b9a9ab` | = |
| `/root/assetapp/claude_reader.py` (read only) | `3894dc2358abd875ee61ced7619e1e1b` | = |
| `/root/assetapp/claude_reread.py` (read only) | `47548ab97c55a1f4fb8d5d1a608a1681` | = |
| `/root/shared/scan_checks_s441.py` (read only) | `b9ba6839ec7979cb709909214d6a0b69` | = |
| `/root/finance/packs.py` (the parent's, read only) | `d86d351a46a1ba4da7d0e615da0deb1a` | = |

`/root/assetapp/sorting_desk.py` did not exist.

**The board's `_numbers`** cannot be read from this runner. I read `deploy_kits\KB_canon_all\START_HERE_SESSION_315.md`
and the newest reports (`REPORT_S553.md`, `REPORT_S552.md`). Neither has a PLANNED line on these three files newer than
S551's own (D722). The pins were exact. **The chat should append S551's DONE line to `_numbers` once installed.**

### 2 · The whole read: line counts, and real names that differ from the brief

**Line counts:**

| file | lines |
|---|---|
| `asset_register.py` | 4307 |
| `clinic_papers.py` | 1572 |
| `claude_reader.py` | 417 |
| `claude_reread.py` | 142 |
| `scan_checks_s441.py` | 620 |

`sarvam_ocr.py` was also read. It takes its key from the environment only.

**Names and lines.** Every name the brief relies on exists with the brief's name. The `AR:` line numbers have moved; the
`CP:` numbers are exact.

| name | live line | brief said |
|---|---|---|
| `checker_required` | 717 | 710 |
| `is_owner` | 731 | 724 |
| dashboard spend tile | 1268–1279 | 1264–1269 |
| bills list history links | 2400–2401 | 2393–2394 |
| bills list lane drop-down | 2410 | — |
| `BILLFORM_TPL` | 2417 (kind select 2430) | 2410 / 2427 |
| `_bill_form_page` | 2534 | — |
| `bill_view` (Month list 2690, `asset_edit?bill_item=` 2713) | 2650 | 2701 / 2697 |
| `_audit_bill` | 2920 | 2870 |
| `_lane_kind_status` | 2903 | 2853 |
| `_dup_by_triple` | 3042 | 2992 |
| `_mark_dup` | 3066 | 3016 |
| `_month_choices` / `_good_bill_month` | 3136 / 3156 | — |
| `_private_s544` | 3186 | 3136 |
| challan on pharmacy = kind `Challan` | 3384–3387 | 3334–3338 |
| `bill_edit` | 3536 | 3484 |
| `bill_approve` (Asset rule 3591) | 3583 | — |
| `bill_reread` | 3618 | 3566 |
| `bill_month_set` | 3663 | 3611 |
| `bill_lane` | 3681 | 3629 |
| `bill_dup` | 3717 | 3665 |
| `/purchases` | 3864 | 3812 |
| `_scan_cv_on` | 3989 | 3939 |
| `/admin` switch statements | 4131–4138 | — |
| the WSGI prefix middleware | 4259–4277 | 4178–4199 |
| the clinic_papers mount | 4286–4297 | 4207–4219 |

**Facts the build had to follow:**
- The `assetapp` unit's Environment carries no `ASSETS_DB` / `ASSETS_UPLOADS` (only a key's name was seen, never its value).
  So the database is `/root/assetapp/assets.db` by the app's own default. The installer resolves it the same way.
- `scan_checks_s441` reads `FINANCE_DB_FOR_SCANS`, which defaults to `/root/finance/finance.db`. The walk sets it to a
  path in the scratch folder that does not exist, so **finance.db was never opened**. W4 checks this.
- The live database has 158 papers and no challans (every `doc_kind` is NULL). It has `claude_reading` (S550). It has
  neither `desk.*` nor `read.claude` set.
- The old heal (`clinic_papers.heal`) accepts a grouped clinic challan, and `_page_ok` refuses an approved page. So before
  this kit, a sorted challan could never be joined. The new walk's control shows it: R2 is red on the old files.

### 3 · The counted edits (make_s551.py; each anchor matched exactly once on the live bytes, on Windows and on the box)

**`asset_register.py`: 19 edits.**

| edit | brief item | what changed (anchor) |
|---|---|---|
| A1 | 5a | the guarded mount after `# --- S464_CLINIC_PAPERS end ---` |
| A2 | 5b | `<title>Asset Register</title>` → *Scan app & assets* |
| A3 | 5b | `Asset Register</b> <span … v{{version}}` (the top bar) |
| A4 | 5c | the bills list's `<select name=lane … onchange=…>` form → a link to the paper |
| A5 | 5d | `BILLFORM_TPL` heading → *Edit bill* / *New bill* |
| A6 | 5d | the Kind select → a "kept" line when editing a Lab / Expense / Document / Pharmacy / Challan paper |
| A7, A8 | 5d | `_bill_form_page(..., editing=False)` and its render call |
| A9 | 5d | `bill_edit`'s kind line keeps the lane's own kind |
| A10 | 5d | `bill_edit` passes `editing=True` |
| A11 | 5e | `bill_view` uses `_bill_months_s551(b)` |
| A12 | 5e | `_bill_months_s551` and `_any_bill_month_s551`, placed before `_good_bill_month` (which is unchanged) |
| A13 | 5e | `bill_month_set` uses `_any_bill_month_s551` |
| A14 | 5h | `bill_reread` refuses `subgroup='patient_paper'` |
| A15 | 5g | the dashboard tile href → The month |
| A16 | 5f, 5g | the tile's text, plus the Switches card hook on the front page |
| A17 | 5g | the bills list's *Clinic consumables by month* → *The month* |
| A18 | 5g | the owner's *Consumption & rate history* link → The month |
| A19 | 5g | the `/purchases` banner *"Replaced by The month — open it"* |

**`clinic_papers.py`: 12 edits.**

| edit | brief item | what changed |
|---|---|---|
| C1 | — | `VERSION` → `S551` |
| C2 | 6 | `SUB` gains `implant_stock`, `clinic_equipment`, `patient_paper` |
| C3 | 6 | `APART_KEYS` added (not added to `SECTIONS`) |
| C4 | 6 | `month()`'s filter uses `APART_KEYS` |
| C5 | 6 | `stand()`'s count uses `APART_KEYS` |
| C6 | 6 | `_accept()` skips a challan unless it is final |
| C7 | 6 | `heal()` skips a non-final challan and `clinic_equipment` |
| C8 | 4 | `join_pages()` added: the join's loop moved out, verbatim, `_page_ok` kept, no commit, no flash |
| C9 | 4 | `join_page()` calls `join_pages()` |
| C10 | 6 | banner on `MONTH_TPL` |
| C11 | 6 | banner on `CHALLANS_TPL` |
| C12 | 6 | the papers page's links to the desk and its three pages |

**New: `sorting_desk.py`** (one module; routes are registered without `/scanapp`).

| route | what |
|---|---|
| `/desk` | the desk |
| `/desk/api/list`, `/desk/api/paper/<id>`, `/desk/api/find`, `/desk/api/save` | the desk's JSON routes |
| `/desk/awaited` (+ `/mode`, `/pay`) | Bills awaited |
| `/desk/implants` (+ `/pay`, `/void`, `/check`) | Implant stock ledger |
| `/desk/month` | The month |
| `/desk/switch` | the switches (owner only) |

- `ensure()` adds the 4 tables and 2 columns, and tolerates the two-workers race.
- `--ensure <db> --floor <day>` is the installer's data step.

### 4 · TO pins (built on Windows, rebuilt on the box, read back on the rehearsal root)

| file | TO md5 |
|---|---|
| `asset_register.py` | `c107c6bbb3e6c0c0d0535c5ed094b6e4` |
| `clinic_papers.py` | `058c9bcb5a4973f8a15984b645ff57d7` |
| `sorting_desk.py` (new) | `3daa1e3a60d8af0ff1f0dcfe244a409b` |

All three compile on `/usr/bin/python3` and on `/root/wa/venv/bin/python3`.

### 5 · The walk (`walk_s551.py`, on the box)

**Setup:**
- Isolated in `/tmp/s551dev/` and its own work folders.
- The live database was copied once with the backup API (`mode=ro`).
- Every environment value was set as the brief lists, plus `FINANCE_DB_FOR_SCANS` (see §2). `SARVAM_API_KEY` and
  `ANTHROPIC_API_KEY` were unset.
- The module files were asserted to come from the scratch folder.
- The walk and the control each ran in their own `python3`. The re-import is a fresh `python3` subprocess.

**Result: 81 checks, 81 GREEN, 0 RED.** By group:

| group | what the checks cover |
|---|---|
| W1–W4 | the import and isolation |
| H1–H8 | the header, the drop-down gone, the menus, the Switches card (owner only), the banners |
| S1–S8 | the switch OFF (manager gets the line; JSON and forms 403; the owner is allowed); a manager cannot switch; the owner's switch ON is written and audited; manager has no Personal button; reception 403 on all 14 new routes; no login → `/login` |
| D1–D20 | every destination and *Blank — discard*, read back (see below) |
| P1–P3 | Yuvika never pre-selected (control: the same items from another supplier are); Claude's `made_out_to='patient'` pre-selects *A patient's paper* with its line and saves nothing; a `suggest()` section is a grey hint only |
| C1–C13 | the challan modes and amber rules (see below) |
| L1–L4 | the ledger (see below) |
| F1–F8 | the D710 hold answered both ways; an S441 set-aside answered both ways; misread date and nothing-read flags |
| V1 | Personal hidden from the manager |
| R1–R4 | the fresh import moves nothing a person placed |
| M1–M3 | The month: kept apart, the own sections, the asset link |
| E1–E3 | the edit page, the month list, the re-read |
| T1 | the first load |
| Z1 | the made-up rows live in the scratch copy only |

**D1–D20, every destination read back** (lane, subgroup, status, kind, `pe_who`, `doc_kind`):
- D1–D5: the four consumables and Implant stock, all accepted.
- D6, D7: a manager's Clinic-equipment Save stays a draft ("Waiting for Dr Manoj's Save"); the owner's Save accepts it; no
  asset is created.
- D8: Construction work is left on other-document or personal-expense.
- D9, D10: Dr MK; Dr Bhawna; a section kept; a consumable group cleared and audited.
- D11: Personal, owner only.
- D12: Pharmacy equals `_lane_kind_status('pharmacy')`; a challan goes over as kind `Challan`.
- D13: NK Pathology. D14: Resumes and Miscellaneous.
- D15: an **approved** paper moved to *A patient's paper*: `captured`, out of the approved total, `relane` by the person
  with `via: desk`.
- D16: Blank.
- D17: a page joined through `join_pages`; an approved paper is refused as a page.
- D18: a pharmacy paper is never listed, opened or saved.
- D19: an approved paper's header is corrected with `bill_edit`'s normalisation and its items are untouched.
- D20: a bad amount rolls the whole Save back.

**C1–C13, challans:**
- C1–C5: monthly pre-ticks the month's challans; the spelling variant merges; Challan is pre-chosen from the supplier; the
  item compare reads "3 of 3 match · 1 extra · 0 missing"; joined through `join_pages`.
- C6, C7: now-and-then offers all challans unticked, oldest first, aged 45 days; waiting rule (d).
- C8, C9: the amber rules for all three modes and the 15-day default, against today = 15-Jun-2031, and the monthly edges.
- C10: the cards; pharmacy challans are not listed.
- C11: The month equals `/papers/month` for the three consumables groups.
- C12: paid-on-challan → final, audited, accepted, and it adds **exactly** its amount.
- C13: Note payment.

**L1–L4, the ledger:** a joined challan is counted once; owed 5,700 / paid 2,700 / balance 3,000 with a voided payment
ignored and a final paper's `paid_amount` counted (made-up figures); no patient paper; checked up to the made-up today.

**F1–F8, the flags:** the D710 hold is shown, not silent; a Save without the answer is refused; *same* →
`_mark_dup(desk)`; *keep* → `not_duplicate` + `d710_accepted_by_person`. The S441 set-aside is listed within 30 days
(older not); *same* → `desk_dup_same`; *restore* → `desk_dup_restored` with the old values. The misread-date flag respects
the floor; nothing-read is flagged; a saved flag leaves the list.

**V1, Personal hidden from the manager:** in the list, the file, the reading, the Open box, the button and the Save.

**R1–R4, the fresh import:** a fresh `python3` import (init, heal, auto_home) moves nothing a person placed. R4 includes a
paper the system's auto_home would otherwise send back; the old files move it. A grouped clinic challan stays a draft. A
manager's equipment Save still waits for the owner.

**M1–M3, The month:** a patient's paper is in no total and is counted under *Kept apart*; Implant stock, Construction work
and Clinic equipment are their own sections; "+ asset record" shows for the owner only.

**E1–E3:** the edit page keeps a Lab paper's kind and reads *Edit bill*; `bill_month_set` accepts 2025-08 (14 months
back) while `_good_bill_month` still refuses it; the reread is refused on a patient's paper.

**T1 — sizes and times (on the box):**

| page | size | time |
|---|---|---|
| desk | 18,230 B | 6 ms |
| list JSON | 4,412 B | 15 ms |
| one paper JSON | 487 B | 3 ms |
| desk first load (page + list + one paper) | — | 24 ms |
| `/desk/month` | 13,899 B | 19 ms |
| `/desk/awaited` | 14,375 B | 11 ms |
| `/desk/implants` | 7,671 B | 9 ms |

**The negative control (the same walk on the live, old files): 81 checks, 7 GREEN, 74 RED.**
- Red: W2, W3, H1–H5, H7, H8, S1–S8, D1–D20, P1–P3, C1–C13, L1, L2, L4, F1–F7, V1, R1, R2, R4, M1–M3, E1–E3, T1.
- R1 on the old files names three papers the old heal or auto_home moved: LB1, CF1, PMA.
- E2: the old page refuses the 14-months-back month. E3: the old reread starts reading a patient's paper.
- The 7 that stay green test nothing new: W1, W4, H6, L3, F8, R3, Z1.

**The three papers of the plan,** as the desk's own JSON (stamps and choices only):

| paper | waiting | now | status | pre-selected | kind | flags |
|---|---|---|---|---|---|---|
| B-0001 | yes | not sorted | accepted | nothing | bill (from Claude's reading) | date |
| B-0015 | no | Construction work | accepted | Construction work | bill (from Claude's reading) | none |
| AINDOS 1952 = B-0125 | yes | not sorted | not accepted yet | nothing | challan (from Claude's reading) | none |

Claude's reading of B-0001 is **not** "made out to a patient", so the desk does not pre-select it. The owner presses *A
patient's paper*. Saving it there moves an approved paper to `other_doc`/`captured` (as D15 proves on a made-up row).

### 6 · The rehearsal (`rehearse_s551.sh`, made-up root `/tmp/s551dev/root`)

- Every `S551_*` setting pointed at the made-up root. The restart was `true`. Health came from a stand-in
  (`python3 -m http.server` serving `healthz`).
- It refuses any path under `/root/`, a `systemctl` restart, or the live port. All three outcomes were as required:

| outcome | result |
|---|---|
| fresh install | green: the walk 81/81 and the control red inside the installer; backups made; placed at the TO pins and read back; data step left desk.floor `2026-10-14`, desk.on **absent** and the 4 tables |
| second run | `S551_SORTING_DESK: ALREADY INSTALLED` |
| forced red after placing | restored: the files back at `3d5a36e3` / `5b197fb5`, `sorting_desk.py` taken out, healthz 200, "NOT INSTALLED (restored …)" |

- **After everything,** the live files were still at the FROM pins, `/root/assetapp/sorting_desk.py` was absent, the live
  database had no desk table, no `desk.*` setting and no made-up row, `assetapp` was active, `/healthz` answered 200, and
  `/tmp/s551dev` and the install temp folders were removed.

### 7 · The kit and the repository gates

**Folder:** `deploy_kits\S551_SORTING_DESK\` (13 files):

| file | md5 |
|---|---|
| `KIT_ID.txt` | `1bb76407` |
| `README.md` | `e600c47b` |
| `install_s551.sh` | `2b58ddfc` |
| `make_s551.py` | `cf0a3688` |
| `sorting_desk.py` | `3daa1e3a` |
| `walk_s551.py` | `2f1f47ca` |
| `rehearse_s551.sh` | `a27f9975` |
| `PIN_FROM_asset_register.txt` | — |
| `PIN_FROM_clinic_papers.txt` | — |
| `PIN_TO_asset_register.txt` | — |
| `PIN_TO_clinic_papers.txt` | — |
| `PIN_TO_sorting_desk.txt` | — |
| `SUMS.md5` | — |

- No `.json`, no database, no copy of a live file, no `__pycache__`; LF line endings throughout.
- The installer, patcher, walk, module, rehearsal and PIN files are byte-identical to what ran on the box. README and
  KIT_ID were written after the rehearsal.
- **SUMS.md5:** every line verified.
- **.gitignore:** `git check-ignore -v --non-matching` (last match wins) reports all 13 kit files as not ignored.
- **Contact-number gate:** run as PUBLISH_ALL runs it (`python -B deploy_kits\NO_PHONE_NUMBERS.py --files-from <list>
  <repo>`). Result: "clean — 13 staged file(s) checked (numbers and credentials)". This report was then run through the
  same gate.

### 8 · Calls made in the build (the brief was silent or two readings existed), each with its reason

1. **Clinic equipment sets `kind='Asset'`.** The app's own approve door (`bill_approve`, owner only for Asset-kind) then
   agrees with the desk's rule.
2. **Kind for other clinic moves.** A paper already Asset-kind that a manager sorts into a consumable is accepted, exactly
   as `set_group` does today. I added no new rule.
3. **Yuvika: nothing is pre-selected at all, not even its current place.** Its current place shows as a grey "Now: …"
   line. This is the strict reading of §5 "pre-select anything for Yuvika".
4. **Pre-selection order:** the paper's own place, then Claude's *patient* reading, then a consumables `suggest()`.
5. **A held or set-aside paper must be answered before Save.** The Save is refused with "First answer: …". Otherwise the
   hold would be filed silently.
6. **"Not the same — bring it back"** without a destination puts the paper back on Waiting, unsorted.
7. **Paid-on-challan suppliers keep a card on Bills awaited** while they have a final paper unpaid, or paid in the last
   60 days. Without the card there is no place to note the payment.
8. **Setting a supplier to *paid* accepts its sorted clinic challans at once,** like a bill. Otherwise they would wait for
   the next restart's heal.
9. **Ledger:** a priced awaiting challan owes its amount ("bills and priced challans"). A *closed* challan is treated like
   an awaiting one.
10. **The menus' month link:** for a manager while the desk is OFF it stays on the old page, so he never meets the off
    line from the menu. The banners on the old pages show only to people who can open the new ones.
11. **`desk.floor` absent** means the floor rules list nothing. The installer sets it to the install day (IST).
12. **The Waiting JSON carries at most 300 rows;** the count shows the total.
13. **The installer has two rehearsal hooks:** `S551_HEALTH_TRIES` and `S551_FORCE_RED`. They are only read from the
    environment.
14. **`bills.doc_kind` now also holds `bill` / `estimate`.** Every reader in the asset app uses
    `COALESCE(doc_kind,'bill')` or `=='challan'`. The finance side reads only `subgroup` (`owner_console.py:1118`), checked
    by a read-only grep.
15. **The Switches card's "Claude reading →"** links to `/admin#claude-reads` (the S550 card's anchor).

### 9 · Not done, and why

- **Not installed and not published.** The brief (§0) says this run builds, walks and rehearses only.
- **No real-browser look at 1366 × 768.** This runner has no browser. The page is one 100vh flex layout with inner
  scrolling only, and T1 checks the no-page-scroll rule in the CSS. The chat's cold review, or the owner's first look,
  should confirm it on the laptop.
- **No independent cold review in this run.** The Scan App chat does it (§0).
- **`claude_reread.py` (read only, not in scope)** can still read a patient's paper in its background pass of older scans.
  It fills empty fields only. The brief's "never read again" was applied to the re-read door (`bill_reread`), as §3.0
  item 5h says.
- **Challans the old heal already accepted cannot be joined** (`_page_ok`). The desk offers only draft or captured
  challans. The live data has no challan today, so nothing is stuck now.
- **DUTY_MAP not touched** (brief §5).

### 10 · FOR THE PARENT

- **`packs.py` `build_bundle`** (packs.py:1777-1801) selects `lane=? AND status<>'rejected'` with no `doc_kind` filter.
  - It should exclude `doc_kind='challan' AND COALESCE(challan_state,'awaiting') <> 'final'`.
  - It should decide what a `final` paid-on-challan paper carries (its `paid_amount`, in rupees).
- **When the clinic lane enters a pack** (D710 (2)), it must exclude `subgroup IN ('implant_stock','clinic_equipment',
  'patient_paper')`.
- **A construction paper left on `owner_expense` is in 8.2 today.** The walk's D8 leaves one there by design: the desk
  never moves its lane.
- **The portal tile's name** should read *Scan app & assets*. The tile is the parent's, and this kit does not touch it.
- **No DUTY_MAP change in this kit.** When the owner switches the desk on, Shavez's sorting duty and its door
  `/scanapp/desk` belong in DUTY_MAP. The `due_sql` could be the Waiting count, with the list's own rule.
- **`claude_reread.py`** should skip `subgroup='patient_paper'` in its pass of older scans (a later kit).

### 11 · Cost

About **US$12.6** of API credit for the whole run, read from this session's budget meter at the time of writing.

**Nothing installed, nothing published.** The kit is at `deploy_kits\S551_SORTING_DESK\`, waiting for the Scan App chat's
check and the owner's publish.

---

**Fix round 1 ends as round 0 did: nothing installed, nothing published.**
