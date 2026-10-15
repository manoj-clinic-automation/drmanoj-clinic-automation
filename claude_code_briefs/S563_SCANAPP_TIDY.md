# S563_SCANAPP_TIDY — brief for the build runner (Agent SDK, the API credits)

*Written 15-Oct-2026 by the Scan App project (session 318). Kit **S563** claimed on the board `_numbers` (v434 → v435);
its PLANNED line (D646, board v438) names the five files below. **v2** — every BLOCKER and CORRECTION of the
independent read `03_WORKING_PAPERS\S318\S563_BRIEF_R1.md` (md5 `e05fbfa4…`) is taken in below; read it too. The owner's word, 16:30 IST 15-Oct: "go ahead, but use the claude
api". This file is the whole scope. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S563_SCANAPP_TIDY`.*

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** Kit in
`deploy_kits\S563_SCANAPP_TIDY\`, report `claude_code_briefs\REPORT_S563.md`, then stop. Nothing live placed or
restarted; no live row written. CLAUDE.md's "install and publish without asking" is overridden for this run.

## 0 · What this kit is
The scan app's last tidy round: the leftovers of the five kits S551 · S555 · S557 · S559 · S560, one fault the owner
saw (F-902), two defects found while reading the code (NEW1, NEW2), and `clinic_papers.py` consolidated (drift 6).
**No new feature, no new page, no new switch.** Reception's intake screen behaves exactly as today — **item 10's two
Adjust-stage corrections excepted** (a late picture of a deleted page ignored; the stage button's page number right).

## 1 · Read first
- **`D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S318\S563_OPEN_NOTES.md`** (md5 `444097bf…`) — §1 is the FIX list with
  file, function, line numbers (on the S560 bytes), the effect and the intended fix. **§2 LEAVE items are NOT touched.**
- `claude_code_briefs\S560_RECEIPTS_STATEMENTS.md`, `S560_FIX1.md`, `S560_FIX2.md`, `REPORT_S560.md`;
  `S559_ONE_ROAD.md`, `S559_FIX1.md`, `REPORT_S559.md` (the widget walk and the seven surfaces); `REPORT_S557.md`;
  `deploy_kits\KB_canon_all\BUILD_NORM_v1.md`. Every rule and NEVER of those briefs still binds.
- **Copy `deploy_kits\S560_RECEIPTS_STATEMENTS\`'s kit shape exactly** (installer `S563_*` variables; the rehearsal's
  refusals and outcomes; the walk isolated before import; walk and control in separate `python3` processes; made-up rows
  only; injected `today`); and `deploy_kits\S559_ONE_ROAD\`'s browser walk on the PC's headless Chrome for the widget.

## 2 · Pins — FROM bytes, read on the box first; a different byte = STOP that file and report
- `/root/assetapp/sorting_desk.py` **`a4623438f068d8e691b797482bd942ab`** (S560)
- `/root/assetapp/clinic_papers.py` **`88963eacee217e051ae07091648a46d7`** (S560) — **read whole first**
- `/root/assetapp/asset_register.py` **`9daed9ea4f2a87e40b43711e472e701f`** (S560)
- `/root/assetapp/asset_machine.py` **`0caec41e655cfd51c2eaf9176ee33365`** (S559)
- `/root/assetapp/scanner_widget.js` **`1128ac975ba2543e1fe9edf7c721d4f8`** (S559.1) — **SHARED BY SEVEN SURFACES** (two
  scan-app, five finance-app)
- Read only, **never edited**: the parent's `/root/finance/packs.py` `048d2ad8…`, `claude_reader.py`, `claude_reread.py`,
  every finance-app and Sanjeevni file.

## 3 · What to build — the notes file's §1, in its order, with these decisions (binding)

1. **F-902 — Restore a set-aside paper.** On the desk, a paper with status `rejected` that is **not** a joined page
   (`page_of`) and **not** an S441 double scan (`dup_of`) shows one line **"Already set aside on dd-mm-yyyy — Restore?"**
   (the date from `bills.approved_at`, which every set-aside path writes; else `created_at`) and a **Restore** button.
   Restore sets the status `AR._lane_kind_status(lane)` gives a fresh paper (clinic `draft`, other lanes `captured`) and
   keeps lane, subgroup and kind as they are (D664); audited (who, when, from what); the server checks `_visible` (a
   Personal paper: owner only — for a manager it stays hidden as today). The desk then shows it as an ordinary paper to
   sort with the normal Save. It must **not** depend on `desk_fix_answered` (S560-N10). **One shared `_s563_restore`**
   serves both this line and the existing blank-fix restore; `fix_answer` stops reading `status_from`, and a blank-fix
   paper shows **one** Restore line, never two.
2. **S560-N3** — that same restore never returns a paper straight to `approved`; the normal accept (with
   `_dup_by_triple`) runs at the next Save. `approved_by` **and `approved_at`** are cleared on restore.
3. **NEW1 — the old Bills awaited page.** `clinic_papers.py` `challans_awaiting`, `challan_for_bill`, `challans_page`,
   `challans_count` — and the join candidates (:1281) and the `closed` list (:1287) — apply the **same two filters** as
   `sorting_desk.awaiting_challans`: no `subgroup='patient_paper'` for anyone; no `subgroup='personal'` for a non-owner.
   **Do not call the desk's helper** (it drops pharmacy challans, and this page must work with the desk off): give
   `challans_awaiting` an `owner` argument and filter in place, one helper inside `clinic_papers.py`.
4. **NEW2 (+ S557-K2-N2) — the owner's Delete of a paper** (`asset_register.py` `bill_delete`): in one transaction, void
   every live payment the paper proves — `_s560_void_own`, then `_s560_void_allocs`, reached through `sys.modules` (the
   desk module); **refuse the delete with a plain message if the desk module is not loaded** — so the bill a deleted
   receipt paid reads unpaid again; set `assets.bill_id` to NULL where it pointed at the paper; write one `paper_deleted`
   audit row. Nothing else changes in the delete.
5. **S560-N4** — a statement pays the invoices **that have a total** first (oldest first); an invoice with no total takes
   only what is left after them, and the Save message says so.
6. **S557-K1-N9** — `asset_machine.from_paper` re-checks "already a machine's purchase bill" inside the POST under
   `BEGIN IMMEDIATE` before the INSERT; a second tap gets the existing machine, never a new one.
7. **S557-K1-N6** — the stamp box's `asset_machine.paper_from_box` (**not** `refusal()`, which also drives three
   displays; `from_paper` already refuses both) refuses a paper with `dup_of` or `page_of`: "This paper is a copy / a page
   of B-xxxx — open B-xxxx instead."
8. **S559-K1-N6(i)** — with no S557 cover row, an old record whose own *Contract renewal* date is past reads **"… lapsed on
   dd-mm-yyyy"** (red), exactly as a lapsed new cover does. The renewal date is the latest `expiries` row labelled
   'Contract renewal'. The PM sentence (decided in `asset_register._s559_pm`, :4599, as well as `cover_line`) shows only
   while covered.
9. **S560-N2** — the receipt / statement words are matched on the vendor, the bill number and Claude's supplier / number
   only — **never on item names** — through a **new** words-only text helper used by `_s560_claude_kind`,
   `_s560_looks_receipt` and `_s560_looks_statement`; `_s560_text` stays as it is (it also feeds `_s560_prefill`). A "Receipt book" line on a stationery bill leaves its Bill pre-choice alone.
10. **S559-K2-N7 + the stage label — `scanner_widget.js`, ONLY inside the intake-only `cvScanOn` / `inlineStamp`
    branches:** `dropSrc` bumps the Adjust generation token (`adjGenS559++`) so a late `onload` of a picture whose page was
    deleted is ignored; after a delete shifts `adjustIdx`, the stage button names the page now under adjustment. The other
    six callers never set those branches — **walk all seven surfaces** as S559 did (the finance app's five byte-for-byte
    unchanged in behaviour), plus the delete-while-loading case in the PC's headless Chrome: NEW ignores the late picture;
    OLD adjusts the wrong page. Cache-bust as S559 (the widget's mtime).
11. **S560-N13** — the three "append-only" comments in `sorting_desk.py` say what the code does now. No behaviour.
12. **CP-TIDY — `clinic_papers.py` (drift 6: S531, S532, S544, S551, S559, S560).** After item 3: a current header
    docstring; one shared helper for the repeated tail of `_live`, `_live_sort`, `_live_sections` (keeping `_live_sort`'s
    own difference: it excludes only challans); `_inr` **stays** (not equivalent to `AR._inr`). **No behaviour change:**
    with the other four files at TO, the walk swaps only `clinic_papers.py` FROM <-> TO and fetches every
    `clinic_papers` route as owner and as manager on its made-up rows, on the same day (the module reads today's date);
    POST routes on fresh copies of the made-up database each time. The served bytes are identical except the pages item 3
    changes (named in the report).
13. **The box's scratch** — the installer, after its own run, removes `s560fix1a`, `s560fix1b`, `s560fix1probe`,
    `s560fix2a`, `s560fix2_pins.sh`, `s554kit`, `s554probe` under **`${S563_SCRATCH_ROOT:-/tmp}`** — each only if it holds
    no `*.db`, `*.sqlite`, `*.db-wal`, `*.db-shm` or `*.json` file (else left and named in the install log). **The
    rehearsal sets `S563_SCRATCH_ROOT` to a made-up folder with made-up copies** and never touches the real `/tmp` list.
    The runner itself only lists them.

## 4 · The walk, the controls, the rehearsal
- `walk_s563.py`: one named check per item 1-12 (F1/F2/F3 … as you choose), each **green on the TO files and red on the
  FROM files** (`--expect-red` with the MUST_RED list printed), except item 11 (comments) and item 12 (proven by the
  byte-identical fetch instead). Counts printed into the log.
- The browser walks on the PC's headless Chrome: S559's seven widget surfaces (20 checks) and S560's desk layout at
  1366 x 768 / 1280 x 720 / 1920 x 1080 (7 checks) — the desk gains a line, so every destination must still fit.
- The earlier walks green on the new files: S560 (37 + pack 9), S559 (43), S557 (41), S555 (19), S551 (87, through
  `s551_lines_s559.py`), S548 (8) —
  each in its own process, with any line a TO pin forces adapted in a copy in `/tmp`, never in the frozen kit.
- The installer: pins checked; `.bak_S563_<from8>` beside each replaced file and `assets.db.bak_S563_*`; **no data step
  and no new column** (if one turns out necessary, STOP and report); `systemctl restart assetapp` once;
  `/scanapp/healthz` 200; the walk on a copy of the database; the scratch removal (item 13); its undo line in the README.
  `clinic-finance` is **not** restarted (no finance file changes; the widget is a static file).
- The rehearsal on a made-up root, its refusals and outcomes as S560's.
- `.gitignore` last-match-wins and the contact-number gate clean (`SANJ_CONFIG_STORE` as before); SUMS, KIT_ID, README.

## 5 · NEVER (in addition to every earlier brief's)
- change reception's intake screen behaviour, the lane buttons or their words (item 10's two Adjust-stage corrections
  excepted);
- touch a LEAVE item, `packs.py`, any finance or Sanjeevni file, the portal, DUTY_MAP;
- guess a section or whose expense a paper is (D664); move a paper a person placed;
- copy a patient's file or a live database row into the kit, the report or the PC;
- install, restart or publish.

## 6 · The report
`REPORT_S563.md`: the FROM pins as read; every counted edit (anchor matched exactly once on the live bytes); the TO
pins; the walk and control counts; the seven-surface widget walk; the earlier walks; the rehearsal; the tidy's
byte-identical proof; calls you made where this brief left room, each with its reason; anything not done and why;
anything seen outside the brief (not touched); the cost from the runner's own log. Last line: **nothing installed,
nothing published.**

**If anything cannot be done as written, stop, write what was done and why, and end.**
