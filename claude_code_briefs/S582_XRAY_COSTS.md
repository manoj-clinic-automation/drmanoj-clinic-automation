# S582_XRAY_COSTS — brief for the build runner (Agent SDK, the API credits)

*Written 18-Oct-2026 by the Scan App project (session 323). Kit **S582** and **D736** claimed on the board `_numbers`
(v480 -> v481) with its PLANNED line. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S582_XRAY_COSTS`.*

**The owner's word, 13:03 IST 18-Oct**, on B-0163 (500 X-ray envelopes, moved at his word to *Stationery & packaging*):
*"But it needs to be also under the xray expenses section, so that I can assess expenses of the xray department also."*
D736: a paper keeps its ONE group (bills.subgroup, D664) **and** may also be counted for the **X-ray department**. An
owner-only **X-ray expenses** page adds, month by month, everything the X-ray department costs — each rupee once.

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** The kit goes in
`deploy_kits\S582_XRAY_COSTS\`, the report in `claude_code_briefs\REPORT_S582.md`; then stop. Nothing live is placed or
restarted and no live row is written. CLAUDE.md's "install and publish without asking" is overridden for this run.

## 1 · Read first
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md` (D704) — every rule binds (real cause, counted edits on md5-pinned live
  bytes, a walk on made-up rows with a negative control that must go red, the installer's order, a rehearsal on a made-up
  root, SUMS, `.gitignore` last-match-wins, the number gate with `SANJ_CONFIG_STORE`).
- The newest kit of this app to copy the SHAPE of: `deploy_kits\S575_BATTERY_SETUP\` (patcher, installer with FROM/TO
  pins and `.bak_S582_<from8>`, `ALREADY INSTALLED` on a second run, README with the undo line, walk, rehearse) and
  `deploy_kits\S571_BATTERIES\` (a new module mounted beside the app).

## 2 · Pins — read on the box first; a different byte = STOP and report
- **Edited:** `/root/assetapp/batteries.py` **`40eb8a916aee48ef5a49337d3c4cc81d`** (S575's TO) — two counted edits only:
  (a) at the end of `init(ar)`, a GUARDED import of `xray_costs` and `xray_costs.init(ar)` (a failure prints to stderr and
  the Batteries pages run exactly as before); (b) `menu_items(role)` appends `xray_costs.menu_items(role)` (guarded) after
  its own item — the owner sees **"X-ray costs"** in the one menu; nobody else sees anything.
  *Why batteries.py:* every module of this app is mounted from `asset_register.py` and the menu is built there, but
  `asset_register.py` and `sorting_desk.py` stand at drift 8 (F-836: the next kit that edits either must read it whole
  and consolidate first). This kit edits neither.
- **NEW:** `/root/assetapp/xray_costs.py` (the page, the marks, the sums).
- **Read only — never edited:** `asset_register.py` `c39c084eabf52daa0da9cc6720fc7aa7`, `sorting_desk.py`
  `110335eac5a9792ebe52620ee676a13c`, `clinic_papers.py` `6db07c12a8ba5ab0123db2a5bee0fa7b`, `asset_machine.py`
  `7d4fdffce01a28fd7e5cc2c4f2aeeb74`, `stationery.py` `d11d718392782d4a7a8b9c233363a526`, `scanner_widget.js`
  `10a8bb296944542278a06827c4d09c18`, the parent's `/root/finance/packs.py` `e46264b85f22563f3e0d8643597e1d58`, every
  finance and Sanjeevni file.
- **assets.db:** additive only — one new table (below). No data step on any existing row, except the seed rows of the
  new table.

## 3 · What to build
**The page** `/scanapp/xray` (route inside the app's prefix like `/batteries`), **owner only** (a manager or reception
gets 403; the menu item is owner-only). English, short, collapsible folds, the app's own look (copy batteries.py's page
frame and `AR.page`). Readable at 1366 × 768 with no sideways scroll.

1. **Header:** "X-ray expenses — <Month YYYY>", a month picker (previous / next, default the current month), and one
   line: *total this month · total since <first month with any X-ray cost>*.
2. **Folds, one per source, each with its month total and its rows** (date · what · supplier · amount · a link to the
   paper / machine / battery place):
   - **X-ray films** — the clinic consumables group `xray`, `xray_small`, `xray_11x14`. Read the rows and the money with
     **The month's own rule**: `sorting_desk._s566_paid_rows(db, key, subs, ym)` and `sorting_desk._s566_total(...)` for
     the section whose key is the X-ray films section in `sorting_desk.MONTH_SECTIONS` (read the code; never re-derive a
     different spend rule — receipts, statements, awaited challans, set-aside papers, second scans, patient papers and
     rejected papers count exactly as The month counts them). If `sorting_desk` is not mounted, the fold says so and
     shows 0.
   - **Papers marked for X-ray** — any non-pharmacy paper the owner marked (any lane, any group, e.g. B-0163 in
     *Stationery & packaging*), money by the same rule as The month for that paper's own section (a paper The month would
     not count as spend is listed with "not counted: <why>"), never a patient paper (D722) and never a pharmacy paper.
     A paper already counted in *X-ray films* is never counted twice.
   - **Machines marked for X-ray** — their **service and repair spends** (`service_logs.cost` by `log_date`) and their
     **covers** (`asset_cover.cost` by `from_day`, `voided_at=''`), as the machine page's own totals count them
     (`asset_machine.totals_line` — read it). A machine's purchase price is NOT an expense here (it is the asset).
   - **Batteries of the X-ray places** — `battery_fit.price` by `fitted_on` (`voided_at=''`) of the battery places marked
     for X-ray.
   - **Each rupee once:** a paper that is the bill of a counted spend, cover or battery fitting is shown under that row
     ("its paper B-xxxx") and not counted again as a marked paper or as a film paper. State the rule in the report.
3. **The marks — owner only, on this page:**
   - "+ Mark a paper for X-ray" — find by stamp (`sorting_desk._s566_stamp_form` normalises B-0162 / 162 / b162), the
     desk's visibility rules; "Unmark" on each marked row.
   - "Machines" fold: every machine with a tick "count for X-ray"; machines whose name or location mentions X-ray /
     X ray / FDR / CR / digitiser are listed FIRST as "looks like X-ray — tick to count", **never ticked by the system**
     (D664: the system never guesses where a cost belongs).
   - "Battery places" fold: every battery place with the same tick.
   - Marks never change the paper, the machine or the battery place (no write to bills, assets, battery_place,
     battery_fit) — only the new table. Every mark / unmark is audited in `desk_audit` (the app's `_audit` style).
4. **Table** `xray_mark(id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('paper','machine','battery_place')),
   ref_id INTEGER NOT NULL, ref_created_at TEXT NOT NULL DEFAULT '', by_whom TEXT, at TEXT, removed_at TEXT NOT NULL
   DEFAULT '', removed_by TEXT NOT NULL DEFAULT '')` — the `ref_created_at` fingerprint guards a re-issued SQLite id
   (S557 BL1: a mark never transfers to a new record that reuses a deleted one's id). Created by `xray_costs.init` with
   CREATE TABLE IF NOT EXISTS.
5. **Seed (the owner's own words only), idempotent at init:** mark the paper **B-0163** (by its stamp, with its
   fingerprint; if it is not found, seed nothing and print one line), and the battery places named exactly
   **"Digital X-ray"** and **"X-ray detector (FDR) battery"** (by name; if a name is absent, skip it). No machine is
   seeded. A seed that was unmarked by the owner is never re-marked (check the audit / removed rows).

## 4 · Never
- edit `asset_register.py`, `sorting_desk.py`, `clinic_papers.py`, `asset_machine.py`, `stationery.py`,
  `scanner_widget.js`, `packs.py` or any finance / Sanjeevni file;
- change what The month, the accountants' pack, the Batteries pages or the machine pages show (walk them before / after:
  byte-identical responses for a fixed made-up database, except the one new menu item for the owner);
- show the page, its menu item or a marked Personal paper to anyone but the owner;
- put a number of any kind into the repository (F-185); print a secret.

## 5 · The walk (made-up rows, a copy of the schema, no live data) — each check named, each with a control that is RED on
the FROM bytes (no `xray_costs.py`, batteries.py at `40eb8a91`):
films counted by The month's rule (a receipt and an awaited challan NOT counted) · a marked paper in *Stationery &
packaging* counted · the same paper not counted twice when it is also a film paper · a machine spend and a cover counted
in their month, the purchase price not · a battery fitting's price counted, a voided one not · a paper that is a battery
fitting's bill counted once · a manager gets 403 and no menu item · a Personal paper markable by the owner, never shown
to a manager · a re-issued id does not inherit a mark · the seed idempotent and never re-marks an unmarked seed · The
month, the Batteries page and a machine page byte-identical before / after · 1366 × 768 no sideways scroll (headless
browser) · the installer refuses a wrong FROM byte and says ALREADY INSTALLED on a second run.

## 6 · The installer (one server line, the owner's)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S582_XRAY_COSTS/install_s582.sh` —
under the build lock as the other kits; pins checked; `.bak_S582_40eb8a91` beside batteries.py; places
`xray_costs.py`; restarts **assetapp only**; reads back `/scanapp/healthz` (or the app's own health line) and the two
md5s; prints `S582_XRAY_COSTS: DONE` and the undo line. Box scratch under `/tmp/s582*` removed by the installer.

## 7 · The report `claude_code_briefs\REPORT_S582.md`
Pins FROM/TO, the counted edits, the walk counts (green / control red), the rehearsal, the each-rupee-once rule as built,
the seed result on the made-up database, anything seen-not-touched, and the cost line.
