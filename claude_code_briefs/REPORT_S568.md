# REPORT_S568 — S568_STATIONERY_STOCK (built, walked, rehearsed; finished by S568_RESUME; fix round 1 by S568_FIX1)

## Fix round 1 (S568_FIX1, 16-Oct-2026, 11:06–11:30 IST)

**For Dr Manoj (plain English):**
- The three corrections from the independent kit check are made in the same kit. **Nothing on the server was changed.**
- **Stock follows the paper.** If a stationery paper is later moved to another group, another lane, or thrown out as blank, its
  items stop counting in your stock straight away (and come back if it is moved back). Old figures correct themselves.
- **"Stationery diya" now looks like your mock-up:** *Kya diya · Kitne · Kisko*, four big buttons (Lab, Reception, Sanjeevni,
  Clinic), one Save, then "Ho gaya — A4 paper 2 ream, Lab ko. Stock mein ab 7." It is built for a phone first.
  `MOCKUP_stationery_diya.html` in the kit is now a picture of the real built screen on a phone, for you to approve.
- **"Add a paper from a file" takes only a PDF or a photo;** a Word file is refused with one line and nothing is saved.
- Every test is green (the walk 14 of 14, all earlier walks, both screen walks, the install rehearsal); each new test goes red on
  the old kit, as it must.

**For the chat.**

*What changed (only the TO files; the FROM pins and every anchor are the same live bytes).*
1. **K1 CORRECTION 1 — `stationery.py`.** One rule for the stock's read and the desk's panel (`_paper_sql`): a paper's matched lines
   count only while the paper is a live paper in Stationery & packaging (`COALESCE(lane,'clinic')='clinic' AND
   COALESCE(subgroup,'')='stationery'`, not a second scan) — a challan / estimate while live (`status<>'rejected'`, `page_of IS NULL`,
   not joined) or while **joined** (`page_of` set, or `challan_state` joined / deleted) into a paper that is itself live in Stationery &
   packaging; a bill as before (not set aside, not a page, no challan / estimate joined into it). Computed when read — no data step.
   `paper_counts` uses the same rule (the panel asks it "as if saved here", since it shows only with Stationery & packaging chosen) and
   says why a paper does not count.
2. **K1 CORRECTION 2 — `stationery.py`.** `DIYA_TPL`: title "Stationery diya"; labels "Kya diya", "Kitne", "Kisko"; the four places
   as radio buttons drawn as large buttons in a 2 × 2 grid (56 px tall; one tap picks); one Save (52 px, full width); the form one
   column, at most 420 px wide. After Save the flash is `done_line`: "Ho gaya — <item> <qty> <unit>, <place> ko. Stock mein ab <N>."
   (N = the stock after the issue). The Ginti card (R1 C9) stays as the one addition. `MOCKUP_stationery_diya.html` replaced: the
   built screen exactly as the walk rendered it (after one Save, made-up items), shown in a 390 × 844 phone frame, with a note.
3. **K1 CORRECTION 3 — `sorting_desk.py` (through `make_s568.py`'s SD22 block; SD1 gains the mark `STOCK_FIX = "S568_FIX1"`).**
   `add_page` reads the file's extension as the intake does and refuses anything not in pdf, jpg, jpeg, png, webp, heic **before the
   intake is called**: "That file cannot be taken — only a PDF or a photo (pdf, jpg, jpeg, png, webp, heic). Nothing was saved." The
   file field's `accept` lists the same types.
4. **Costs, read from each run's own log line** (`D:\Downloads\_kbtools\agent_build\logs\`): round 0
   (`S568_STATIONERY_STOCK_20261016_0939.log`) — **no cost line** (it ends 10:15:43, cut off); RESUME
   (`S568_RESUME_20261016_1028.log`) — **"10:41:48 DONE · cost $2.31 (paid from the API credits)"**; this run
   (`S568_FIX1_20261016_1106.log`) — its cost line is written by the runner when the run ends, after this report; read it there.

*Pins (rebuilt on the box from the live bytes, 11:15:27 IST; each anchor exactly once).*
| file | FROM (live, read 11:15:27 and again 11:28:06 IST) | TO round 0 | TO FIX1 |
|---|---|---|---|
| `sorting_desk.py` | `a053a222ee0fa8b0026aa4fc2511e8a9` | `cd6823f1` | **`695ba90b4b3652f0e087f29b7c25d706`** (24 edits) |
| `clinic_papers.py` | `024464cc3d3ab5e1ead1526540904d61` | `6db07c12` | `6db07c12a8ba5ab0123db2a5bee0fa7b` (13, unchanged) |
| `asset_register.py` | `8b3c455128663db69c48232bf26c0083` | `e5356e0c` | `e5356e0c75f564085b20a059f76a4b48` (9, unchanged) |
| `/root/finance/packs.py` | `048d2ad81abb0271a1cddd31134544bb` | `e46264b8` | `e46264b85f22563f3e0d8643597e1d58` (1, unchanged) |
| `stationery.py` (new) | absent | `3e5d5322` | **`d11d718392782d4a7a8b9c233363a526`** |
Read-only pins unchanged: `asset_machine 7d4fdffc`, `scanner_widget.js 10a8bb29`, `claude_reader 3894dc23`, `claude_reread d9b75e78`,
`scan_register 904f07b1`, `purchase_app 147201dd`. All five TO files compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`.
`PIN_TO_sorting_desk.txt`, `PIN_TO_stationery.txt`, `KIT_ID.txt`, `README.md` and `SUMS.md5` (33 files) updated.

*The walk and its controls (box, `/tmp/s568fix1`, a backup-API copy of the database, made-up rows only, 11:15:27–11:15:33 IST).*
- **`walk_s568.py` on the FIX1 TO files: 14 checks: 14 GREEN, 0 RED** (W1, W2, I1–I8, Z1 and the new I3F, I4F, I7F). The new counts:
  - **I3F:** folder stock before 0 · (a) a challan saved → 5, re-sorted to Others on the papers page (302) → **0**, back → 5 · (b) a
    challan saved → 8, re-laned to NK Pathology (302, lane `lab_purchase`) → **5** · (c) a challan saved → 9, Blank — discard on the
    desk (200, status rejected) → **5** · (d) a challan saved → 7, its bill joining it (challan rejected, page_of set) → **7** (still
    counts), the bill re-sorted to Others → 5, back → 7.
  - **I4F:** title `Stationery diya`; labels `Kya diya`, `Kitne`, `Kisko`; place buttons Lab, Reception, Sanjeevni, Clinic; 2 × 2 grid;
    min-height 56 px; one button `Save`; flash "Ho gaya — Walk A4 paper 2 ream, Lab ko. Stock mein ab 7." (= expected); after one more
    issue "Ho gaya — Walk Register 200 pages 1 piece, Clinic ko. Stock mein ab 5." (= expected).
  - **I7F:** a .docx and a .doc (on the preset) both answered 302 with the refusal line; papers 187 → 187; stored files 4 → 4.
  - The earlier counts are as round 0's (I1 790 / sections = month_total; I3 5 / 6 / join 6 / estimate / lone bill / refusal; I4 9 → 7,
    pen −5, manager 403 then 302, reception 403 / 403; I5 6 → 5 → 3 (−2), manager count 7; I6 1 → 2; I7 two presets, 0 commits as
    'Pharmacy', 0 payment rows, 7 of 7 Sanjeevni queries clean; I8 8.1 LB, LN · 8.2 OB · 8.4 CB).
- **Negative control on the live FROM files (`--expect-red`): 14 checks: 2 GREEN, 12 RED — "CONTROL must-be-red: W2, I1, I2, I3, I3F,
  I4, I4F, I5, I6, I7, I7F, I8 -- all RED".**
- **FIX1 control on the round-0 kit's TO files (`--expect-red-fix1`, built on the box from the live bytes with the round-0
  `make_s568.py`, pins `cd6823f1` / `3e5d5322`): 14 checks: 11 GREEN, 3 RED — "CONTROL must-be-red: I3F, I4F, I7F -- all RED".** Its
  counts: (a) re-sorted → stays 5, (b) re-laned → stays 8; labels `Kya diya?`, `Kitna?`, `Kisko diya?`, no 2 × 2 grid, flash "Save ho
  gaya — 2 ream …"; the .docx filed (papers 187 → 189, files 4 → 6). The old I4 words were made neutral ("Kya diya", "Kisko", "ho
  gaya") so I4 keeps testing the issue itself and I4F alone tests the mock-up; I4 is green on both kits.

*The earlier walks (the rehearsal's outcome 1, on the FIX1 TO files, scratch copy).* S566 **12/12** · S563 **17/17** + its tidy fetch ·
S560 **37/37** · S560 pack **9/9** (P2 / P8 in S568's form) · S548 **8/8** · S559 **43/43** · S557 **41/41** · S555 **19/19** · S551
**87/87** — the same `/tmp`-copy line adaptations as round 0, nothing new.

*The browser walks (the PC's headless Chrome; pages saved on the box from the FIX1 build, made-up rows).*
- **New: `walk/browser_diya_s568.py`, Stationery diya at 390 × 844 (11:17:42 IST): 2 browser checks: 2 GREEN, 0 RED** — D1 viewport
  390 × 844: the title, the three labels on screen, the four buttons in a 2 × 2 grid (56 px tall, 159 px wide, on screen), one tap on
  Sanjeevni picks it, one Save (52 px), nothing wider than the phone; D2 the "Ho gaya … Stock mein ab 5." line at the top. **Control
  on the round-0 page: D1 RED** (labels with "?", buttons 41 px in one row and a half, Save 40 px). Headless Chrome keeps its window
  at least ~500 px wide, so the page is measured inside a 390 × 844 frame (a first try in a bare window measured 518 px and was
  discarded; the check now also requires the viewport to be 390).
- **S560's desk-layout walk** (one line in S568's form) on the FIX1 desk pages (11:17:45–11:17:54 IST): **7 browser checks: 7 GREEN,
  0 RED** (nDest 16 everywhere). Both results are in the kit's `walk/`.

*The rehearsal (made-up root, `rehearse_s568.sh` unchanged).* First run 11:15:35–11:20:06 IST: all ten outcomes as intended, but its
end guard said **"REHEARSAL RED: the live finance folder changed during the rehearsal"** — the guard compares `packs.py`'s md5
(unchanged, `048d2ad8`) and the NAME list of `/root/finance`; the live finance app's own jobs were writing there in that window
(read-only probe: `bank_match.log` 11:15, `job_pulse*` 11:17, `salts_refresh.state.json` / `order_rules.log` / `patient_sync.log` 11:20,
`finance.db` 11:21 — a database journal file comes and goes with each write). Nothing of the rehearsal's is in that folder. **Re-run
unchanged with the folder's name list recorded before and after, 11:22:23–11:26:44 IST: `REHEARSAL GREEN`** (no name differed;
`packs.py` `048d2ad8`): 1 fresh install green (walk 14/14, control 12/12 red, every earlier walk green) · 2 ALREADY INSTALLED ·
3 forced red → restored · 4 `/desk` 404 → restored · 5 `/desk` 200 → restored · 6 `/stationery` 404 → restored · 7 a moved live file
→ REFUSED · 8 a moved read-only file → REFUSED · 9 a foreign `stationery.py` → REFUSED · 10 `packs.py` moved → that file STOPPED,
the rest installed and said.

*Kit identity.* The kit placed in the repository was copied to the box at the end (11:28:06 IST): `SUMS.md5` 33 of 33 ok; every code
file and PIN file byte-identical to what ran (`make_s568.py cb092f9e`, `stationery.py d11d7183`, `walk_s568.py 3afee313`,
`install_s568.sh 0e42b75c`, `rehearse_s568.sh 4b20f795`, `lines_s568.py`, `count_s568_pack.py`, the five PIN_TO files). Differing
from the copy that ran on the box: only `README.md`, `KIT_ID.txt`, `MOCKUP_stationery_diya.html`, `SUMS.md5`, the two `walk/` result
files, and `walk/browser_diya_s568.py` (the PC-only browser walk, whose final form is the one that produced the results above).
The installer and the rehearsal are unchanged (they read the new pins from the PIN files).

*Calls made where the brief left room.*
- **The joined-challan rule follows the brief's words** ("or is a challan joined into one"): a joined challan counts while the paper it
  is joined into is a live Stationery & packaging paper, and the challan itself is still there. K1's fix tested only the challan's own
  lane and group; with it, a joined challan kept counting after its bill was re-sorted out (walk case (d) proves the brief's form).
- **The flash's word order follows the brief and the mock-up's quoted line** ("<item> <qty> <unit>"), not K1's "{qty} {unit} {name}".
- **The owner's artifact could not be opened** (claude.ai shows only a sign-in shell to a fetch); the screen follows the brief's and
  K1's quotes of `Issue.dc.html`.
- **The refusal line names the six types** (one line, as before; the earlier "(jpg, png)" undersold the photo types).
- **The pack counts on the live data were not re-run:** `packs.py`'s FROM and TO are unchanged from round 0.
- **No build lock taken:** this run installs nothing (as round 0); the rehearsal uses its own made-up lock. The lock was free throughout.
- **DUTY_MAP not changed** (as round 0: Stationery diya is on demand, OFF for managers, with no state that makes it due).

*Box scratch.* Removed: `/tmp/s568fix1` (this run's kits, built files, walk work and the backup-API copies — made-up rows on a copy,
now gone) and `/tmp/s568reh` (the rehearsal's made-up root). Left, named: `/tmp/s568probe` (round 0's pins probe, not this run's).

*Seen outside the brief (not touched).* `finance.db.bak_S569_20261016_105712` in `/root/finance` and `_scratch\S569_PROOF_REACH_AND_TWO_LINES`
on the PC (10:59) — another build (S569) ran this morning; it did not hold the lock during this run. The rehearsal's end guard (name
list of the live finance folder) can trip on the finance app's own writes; a later kit could compare program files only.

*Gates (run last, finished 11:29:06 IST on the PC clock), over 38 files — the 34 kit files, this report and the three S568 briefs:*
- `.gitignore` (last match wins): `git check-ignore -v --no-index` — **none ignored** (exit 1); no nested `.gitignore`, no
  `__pycache__` / `.pyc` in the kit.
- Contact-number gate (`NO_PHONE_NUMBERS.py --files-from`, run from a copy in `_scratch\S568_FIX1`, the default store as before):
  **`NO_PHONE_NUMBERS: clean -- 38 staged file(s) checked (numbers and credentials).`**

**nothing installed, nothing published.**

---

## Round 0 and RESUME (kept as written)

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
