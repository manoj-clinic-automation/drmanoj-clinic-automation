# REPORT_S568 — S568_STATIONERY_STOCK (built, walked, rehearsed; finished by S568_RESUME)

**For Dr Manoj (plain English):**
- The stationery kit is built, tested and ready in `deploy_kits\S568_STATIONERY_STOCK\`. **Nothing on the server was changed.**
- When installed: the sorting desk gets a fifth clinic button **"Stationery & packaging"**; your new **Stationery** page keeps the
  item list with rates and the stock (received, issued, in stock, low stock, Count); the staff screen **"Stationery diya"** stays
  OFF for managers until you switch it on (its mock-up, `MOCKUP_stationery_diya.html`, is in the kit for you to approve first).
- The desk can **add a paper from a file**, with one preset for the Aumni envelopes: a Sanjeevni pharmacy expense, paid by your card.
- The accountants' bundles will take **bills and invoices only**. On today's data this takes no paper out of any bundle (Aug–Oct).
- Every test is green (the new walk 11/11, the old file shows red 9 of 9, all earlier walks, the screen-layout walk 7/7, the
  install rehearsal 10 of 10 outcomes).

---

## Interrupted at 10:15:43 IST and resumed

**Found (read 10:29:58 IST on the box, nothing changed first):**
- The first run's log (`S568_STATIONERY_STOCK_20261016_0939.log`) ends at 10:15:43 (its last line and its file time) with no DONE line.
- Live pins **unchanged** = the brief's FROM pins: `sorting_desk.py a053a222…`, `clinic_papers.py 024464cc…`, `asset_register.py
  8b3c4551…`, `/root/finance/packs.py 048d2ad8…`; **no `/root/assetapp/stationery.py`**; no `*S568*` file in `/root/assetapp` or
  `/root/finance`. Read-only pins also unchanged (`asset_machine 7d4fdffc`, `scanner_widget.js 10a8bb29`, `claude_reader 3894dc23`,
  `claude_reread d9b75e78`, `scan_register 904f07b1`, `purchase_app 147201dd`). `assetapp` and `clinic-finance` active;
  `/healthz` 200, `/finance/healthz` 200.
- **The interrupted rehearsal had finished on its own** — `/tmp/s568dev/reh.txt` file time 10:19:31 IST, ending
  `REHEARSAL GREEN` (all ten outcomes); no S568 process was running.
- **The server build lock was free** (no `/root/deploy/.claude_code_build.lock`): the rehearsal uses a made-up lock path, and the
  first run never took the real one (it did not install). Nothing to release.
- The scratch kit was complete in code; missing or stale: **`SUMS.md5` absent**; **README and KIT_ID carried two stale TO pins**
  (`sorting_desk 252090ab` (23 edits) and `asset_register 8e30f789` (8 edits), taken before the run's last fix at 10:14 — the
  narrow-screen button CSS and the "paid by Dr MK's card" line); `deploy_kits\S568_STATIONERY_STOCK\` and this report did not exist.

**Redone / finished by this run:**
1. Rebuilt the TO files from the live bytes with the kit's `make_s568.py` (on the PC from the first run's copies of the live files,
   whose md5 = the live pins; and again on the box from the live files themselves): **every one equals the kit's PIN_TO** (below).
2. README and KIT_ID: the two stale pins and edit counts corrected by an anchored edit (each anchor once) to `cd6823f1` (24) and
   `e5356e0c` (9); README's `walk/` line made accurate (it holds the browser walk's results). Nothing else in the kit changed —
   no code file was touched (`make_s568.py`, `stationery.py`, `walk_s568.py`, `install_s568.sh`, `rehearse_s568.sh`,
   `lines_s568.py`, `count_s568_pack.py` are byte-identical to the first run's).
3. `SUMS.md5` written (31 files); the kit sent to `/tmp/s568dev2/kit` and `md5sum -c SUMS.md5` ok there before anything ran.
4. Re-ran on the box (10:32:14–10:36:36 IST, `/tmp/s568dev2` only): the rebuild, both-python compile, the walk, the control, the pack
   counts on a copy, and the **full rehearsal** to its end. Re-ran the PC browser walk (10:39:52–10:40:01 IST).
5. Placed the kit in `deploy_kits\S568_STATIONERY_STOCK\` (sums re-checked there: 31 of 31 equal); wrote this report.
6. Cleared `/tmp/s568dev*` on the box (below).

The walk / control results, counts and rehearsal below are **this run's**; the first run's were the same (walk 11/11, control 9/9
red, rehearsal GREEN, browser walk 7/7).

---

## The FROM pins as read (10:29:58 IST, srv1746119)
| file | FROM (live) | brief pin |
|---|---|---|
| `/root/assetapp/sorting_desk.py` | `a053a222ee0fa8b0026aa4fc2511e8a9` | same |
| `/root/assetapp/clinic_papers.py` | `024464cc3d3ab5e1ead1526540904d61` | same |
| `/root/assetapp/asset_register.py` | `8b3c455128663db69c48232bf26c0083` | same |
| `/root/finance/packs.py` (the parent's) | `048d2ad81abb0271a1cddd31134544bb` | same |
| `/root/assetapp/stationery.py` | absent | new |

## The counted edits (`make_s568.py`, each anchor matched exactly once on the live bytes)
- **sorting_desk.py — 24:** SD1 the mark · SD2 `CONS` (R1 C8) · SD3 the destination list · SD3b the fifth button's narrow-screen CSS
  (≤1300 px only) · SD4 its grey note · SD5 the switch tuple `stationery.issue_on` (C9) · SD6 The month's sections, after Others ·
  SD7 `bills.mixed` by the desk's own ensure (C12) · SD8 the rate-before branch (C8) · SD9 The month's pharmacy count leaves out
  'Pharmacy expense' (C6) · SD10 the switch's state · SD11 Kept apart: "Sanjeevni — pharmacy expenses" · SD12 "Add a paper from a
  file" on the desk · SD13 the mixed tick and the stationery panel · SD14–SD17 the desk script (opened, painted, Save body, S568's
  functions) · SD18 the page's Add address · SD19 one paper's panel / mixed / supplier-note count · SD20 the Save, one transaction ·
  SD21 the route · SD22 the S568 block. (23 labels, 24 anchors: one label carries two.)
- **clinic_papers.py — 13:** CP1 the mark · CP2–CP5 `SUB`, `GROUP_OF`, `CONSUMABLE`, `GROUPS` (Others' hint "the rest") · CP6–CP7 the
  papers page's chooser · CP8 the stationery words *suggest* the new group (R1 note 16) · CP9 the papers page's pharmacy count leaves
  out 'Pharmacy expense' (C6) · CP10 the consumables count · CP11 the old month page's group list · CP12 `supplier_history` skips a
  pharmacy expense (C5) · CP13 `auto_home` never moves one (C5).
- **asset_register.py — 9:** AR1 `_create_intake_bill(..., kind_over=None)` (C4) · AR2 the kind written before the first commit (C4)
  · AR3–AR4 the old edit page keeps the kind (C5) · AR5 the re-lane door refuses it for anyone but the owner (C5) · AR6 the owner's move
  audited (C5) · AR6b "paid by Dr MK's card" on its bill page (B1) · AR7 the menu (owner: Stationery; manager: Stationery diya with the
  switch ON) · AR8 the mark and the guarded mount of `stationery.py` after `sorting_desk.init` (C12).
- **packs.py — 1 (build_bundle only):** PK1 — the S560 line `xk_sql = " AND COALESCE(doc_kind,'bill') NOT IN ('receipt','statement')"`
  and the challan line under it become `xk_sql = " AND COALESCE(doc_kind,'bill')='bill'"` (R1 C3's exact wording). Nothing else.

## The TO pins (rebuilt on the box from the live bytes, 10:32 IST, = the kit's PIN_TO files)
| file | TO |
|---|---|
| `sorting_desk.py` | `cd6823f1f9a7f660ec7b16ff2cc0d3bf` |
| `clinic_papers.py` | `6db07c12a8ba5ab0123db2a5bee0fa7b` |
| `asset_register.py` | `e5356e0c75f564085b20a059f76a4b48` |
| `stationery.py` (new) | `3e5d532286f1152ed3dab9b537f09b99` |
| `/root/finance/packs.py` | `e46264b85f22563f3e0d8643597e1d58` |
All five compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`.

## The walk and the control (box, 10:32:14–10:32:18 IST, a backup-API copy of the database, made-up rows only)
- **walk_s568.py on the TO files: 11 checks: 11 GREEN, 0 RED** (W1, W2, I1–I8, Z1). Counts printed:
  - I1: the save 200; Stationery section 790.0 (before 0.0); sections add 1200.0 = month_total 1200.0.
  - I2: owner page 200, manager page 403; manager's add 403.
  - I3: challan saved → A4 5, register 4, pen 10; re-saved as is 5 (no double); re-saved with 6 → 6 (voided lines kept 4); **its bill
    joining it → A4 still 6**; estimate slip counted; lone bill counted; "rate ₹250 — list ₹240" and "unit differs" flagged; a
    no-quantity matched line refused 400 with nothing saved.
  - I4: owner issue 302 (A4 9 → 7); **above stock saved 302** (pen −5, flagged); **manager, switch absent: issue 403; switch ON: 302**;
    reception 403 / 403.
  - I5: register 6 → **first count 6 (opening)** → issued 1 → 5 → **second count 3 (not accounted for −2)**; manager's count (switch ON)
    on Stationery diya; the row shows stock, received, issued by place, last rate, low.
  - I6: mixed papers this month 1 → 2; the supplier note says it; an estimate's tick ignored.
  - I7: **two Aumni presets**: pharmacy lane, `kind 'Pharmacy expense'`, doc_kind bill, captured; **commits seen showing a preset as
    'Pharmacy': 0**; payment rows 0, audit "paid / card / Dr MK's card" 2; **all four Sanjeevni readers** (scan_register 1 query,
    purchase_app 4, porders 1, order_sheet 1 — run read-only on the copy) hold no preset and do hold the made-up Marg-type scan (7 of
    7); auto_home moved nothing; S441 kept the two presets apart; The month's line "2 · ₹1,820 · paid by Dr MK's card", pharmacy
    count unchanged (42 = 42), month_total = sections; old edit keeps the kind; re-lane manager 403, owner 302 (audited).
  - I8: before — 8.1 = LB, LE, LF, LN · 8.2 = OB, OE · 8.4 = CB; **after — 8.1 = LB, LN · 8.2 = OB · 8.4 = CB** (the made-up
    estimate slips LE / OE and the final challan LF leave; a no-kind paper LN stays; the preset is in none).
- **Negative control (same walk on the FROM files, `--expect-red`): 11 checks: 2 GREEN, 9 RED — MUST_RED W2, I1, I2, I3, I4, I5, I6,
  I7, I8 — all RED.**

## The earlier walks (rehearsal outcome 1, on the TO files, scratch copy)
S566 **12/12** · S563 **17/17** + its tidy fetch (102 answers each side, **none differing**) · S560 **37/37** · S560 pack **9/9** (P2 / P8
in S568's form — the intended pack-fix change, R1 C3; adapted in a `/tmp` copy only by `lines_s568.py s560pack`) · S548 **8/8** · S559
**43/43** · S557 **41/41** · S555 **19/19** · S551 **87/87** (through `s551_lines_s559.py`). Lines adapted only in `/tmp` copies, each
named: S563 F4 and S559 O3/O4 in S566's form, S560 K2 and S559 J1/J3 in S563's form (all inherited from the earlier kits), S560 pack
P2/P8 (S568: the pack fix).

## The browser walk (the PC's headless Chrome, 10:39:52–10:40:01 IST)
S560's frozen desk-layout walk with one line in S568's form (`lines_s568.py browser560`: 15 → 16 destination buttons), on the final
build's desk pages (sorting_desk `cd6823f1`, clinic_papers `6db07c12`, asset_register `e5356e0c`; made-up rows; saved on the box at
10:14:58 by the first run): **7 browser checks: 7 GREEN, 0 RED** — every destination with the new button fits on 1366 × 768 (and 1366
× 620, the real laptop area), nothing scrolls. Kept in the kit as `walk/walk_results_s568.txt` (the first run's identical 7/7).

## The pack fix on a copy of the live data (counts per bundle only)
`count_s568_pack.py`, both databases by the backup API into `/tmp/s568dev2/packcount` (removed by the script at its end):
| month | 8.1 lab | 8.2 Dr Manoj | 8.3 Dr Bhawna | 8.4 construction |
|---|---|---|---|---|
| 2026-08 | 3 → 3 | 0 → 0 | 0 → 0 | 0 → 0 |
| 2026-09 | 3 → 3 | 0 → 0 | 0 → 0 | 0 → 0 |
| 2026-10 | 1 → 1 | 1 → 1 | 0 → 0 | 0 → 0 |
**No real paper leaves any bundle** in these months (none of them is an estimate slip or a final challan today).

## The rehearsal (made-up root `/tmp/s568reh/root`, 10:32:18–10:36:36 IST) — `REHEARSAL GREEN`
1 fresh install green (all walks above; backups; database backed up before the data step; shape grown by exactly four tables, one
index and `bills.mixed`, no row changed; lock released) · 2 the same line again → ALREADY INSTALLED · 3 a forced red after placing →
every file restored (stationery.py removed), both healths 200 · 4 `/desk` 404 → restored · 5 `/desk` 200 (gate open) → restored (302
only) · 6 `/stationery` 404 → restored · 7 a live file moved → REFUSED before placing · 8 a read-only file moved → REFUSED · 9 a
foreign `stationery.py` → REFUSED · 10 `packs.py` moved by another kit → that file STOPPED, the rest installed and said,
clinic-finance not restarted.

## Calls made where the brief left room (with reasons)
- **This run did not take the server build lock**: CLAUDE.md takes it "before the install step" and this run installs nothing; the
  rehearsal uses its own made-up lock. The kit's installer takes the real lock when it is run.
- **No code was rebuilt or redesigned** — the brief: "do not redesign anything that is done and green". Only README / KIT_ID text
  and the new SUMS changed.
- **The browser walk was re-run on the first run's saved final pages** rather than re-taking them: the pages were taken at 10:14:58
  from the final build (pins `cd6823f1 / 6db07c12 / e5356e0c`, unchanged since), so re-taking would add nothing.
- From the first run (kept): CP8 the stationery words suggest the new group (a suggestion only — R1 note 16); SD3b a two-line fifth
  button only under 1300 px wide; the desk's paper field named `stk` (S560 already uses `st`, its walk caught the clash); AR6b the
  card line on the old bill page (R1 B1).
- **DUTY_MAP not changed:** "Stationery diya" is an on-demand screen, switched OFF for managers, with no state that makes it *due*;
  there is no duty for a `due_sql`. If the owner later wants issuing as a scheduled duty, that needs a DUTY_MAP entry in a new kit.

## Not done, and why
- **Not installed, not published** (the brief). No live file placed, no service restarted, no live row written.
- **Cost of the first run: not stated in its own log** — the log ends at 10:15:43 without its `DONE · cost` line (the PC restarted).
  **This run's cost** is written by the runner at the end of its own log, `D:\Downloads\_kbtools\agent_build\logs\S568_RESUME_20261016_1028.log`.

## Box scratch
Removed after placing the kit: `/tmp/s568dev` (the first run's) and `/tmp/s568dev2` (this run's) — no live data in them (the walk's
database copy inside was made-up rows on a backup-API copy, now gone); also this run's read-only probe `/tmp/s568resprobe`. Left, named:
`/tmp/s568probe` (the first run's pins probe, one script) and `/tmp/s568reh` (the rehearsal's made-up root, emptied by the rehearsal
itself) — outside `/tmp/s568dev*`, which is what the brief names.

## Seen outside the brief (not touched)
- R1 note 14: a lab supplier paid on challan with no bill ever will no longer appear in 8.1 (the owner's ruling 5 covers it); none in
  Aug–Oct's live data today.
- R1 note 15: Variety's and Elegans' next papers will still auto-sort to *Others* until a person sorts one into the new group.

## Gates
- `.gitignore` (last match wins): `git check-ignore -v --no-index` over the 32 kit files and this report — **none ignored** (exit 1);
  no nested `.gitignore`, no `__pycache__` / `.pyc` in the kit.
- Contact-number gate (`NO_PHONE_NUMBERS.py --files-from`, run from a copy in `_scratch`, `SANJ_CONFIG_STORE` as before: the default
  store) over the same 33 files: **`NO_PHONE_NUMBERS: clean -- 33 staged file(s) checked (numbers and credentials).`**
- `deploy_kits\S568_STATIONERY_STOCK\SUMS.md5`: 31 of 31 equal, on the PC and (before the runs) on the box.

**nothing installed, nothing published.**
