# REPORT_S585 — many stationery items on one screen (S585_STATIONERY_ISSUE_MANY, D738) — built, walked and rehearsed; NOT installed, NOT published

**For Dr Manoj (plain English):**
- Shavez's **Stationery diya** screen can now show **every item on one screen**: he taps who it went to (Lab, Reception, Sanjeevni, Clinic or
  the new **X-ray**), taps + on each item he gave, and presses **one Save**. All the items go in together, or none if anything is wrong. It looks
  like your mock-up.
- It comes **switched OFF**. Until you tap **ON** on the new card at the top of your **Stationery** page, Shavez sees exactly today's screen.
- On your Stationery page: an **X-ray** column; a **Void** button on every issue line (a wrong line stays, struck through, and goes back into
  stock); a "Show all issues" fold for earlier months; and the **seven lines from Shavez's sheet** in a fold of their own. Those seven are dated
  before your opening count, so **your opening stock stays exactly as you entered it**.
- It has been fully tested on copies, with made-up entries only. Nothing on the live server has changed.
- Waiting for the Scan App chat's check. After that you publish and paste one server line (at the end of this report).

---

## For the chat

**Run:** 18-Oct-2026, 16:21–16:46 IST (times read from the box and PC clocks). Read whole: the brief (v2) and `S585_BRIEF_R1.md` (md5 read back
`706779cef15c89999fb6e51325380055` = the brief's pin), BUILD_NORM_v1, S568's kit, S582's kit and REPORT_S582, and the mock-up
`claude_code_briefs/S585_MOCKUP_Main.dc.html`. Every BLOCKER and CORRECTION was built as R1 words it, except C3: there the brief's own C3
decision was built (the sheet's lines keep the opening count's day and are kept out of every "this month" figure, in their own fold).
Box clock is IST (`timedatectl`: Asia/Kolkata).

### Order with S582 (B2 / C9)
S582 **was installed at 16:18 IST** (from `assets.db.bak_S582_20261018_161826` on the box), and its kit is in the repository. So this kit's
read-only pins for `batteries.py` / `xray_costs.py` are S582's TO pins, `775471e6` / `22e59f5a`, **not** the brief's `40eb8a91` (that one is
S582's FROM). The installer checks them against `deploy_kits/S582_XRAY_COSTS/PIN_TO_*.txt` and refuses if S582's kit is missing or S582 is not
installed (rehearsal outcome 10).

### Pins — read on the box at 16:21:30 IST, before building
| file | pin | live | role |
|---|---|---|---|
| `/root/assetapp/stationery.py` | d11d7183 (S568's TO) | **d11d7183** ✔ | edited (21 counted edits) |
| `asset_register.py` | c39c084e | c39c084e ✔ | read only |
| `sorting_desk.py` | 110335ea | 110335ea ✔ | read only |
| `batteries.py` | 775471e6 (S582's TO) | 775471e6 ✔ | read only |
| `xray_costs.py` | 22e59f5a (S582's TO) | 22e59f5a ✔ | read only |
| `clinic_papers.py` · `asset_machine.py` · `scanner_widget.js` | 6db07c12 · 7d4fdffc · 10a8bb29 | equal ✔ | read only |
| `claude_reader.py` · `claude_reread.py` | 3894dc23 · d9b75e78 | equal ✔ | read only |
| `/root/finance/packs.py` | e46264b8 | e46264b8 ✔ | read only |

**FROM → TO:** `stationery.py d11d718392782d4a7a8b9c233363a526 → 18268ff04b37af8143be1e3395ec5854`. This was rebuilt on the box from the
live bytes and read back after placing in the rehearsal's made-up root. **Live afterwards (16:45:15 IST):** stationery.py d11d7183, no
`.bak_S585_*`, 0 stationery moves, no `stationery.many` or `stationery.history_s585` key, lock free, healthz 200.

### The counted edits (make_s585.py; each anchor found exactly once)
E1 docstring · E2 marks `MANY="S585"`, `MANY_SWITCH`, `HISTORY_KEY`, `HISTORY_BY` (VERSION stays "S568", so S568's walk W2 holds) · E3 `PLACES`
gains `("xray","X-ray")`, `ONE_PLACES = PLACES[:4]` (B1) · E4 `HISTORY`, the seven lines · E5 `many_on()` · E6 `issue()`'s refusal now says "…,
Clinic ya X-ray chuno." (C2) · E7 `_issue_view()` · E8–E11 `inventory()`: this month's figures leave out the sheet's lines (C3); the display list
includes voided lines; earlier months; the sheet's own list · E12 the switch card at the top of the owner's Stationery page (C1) · E13 the stock
table header built from `places` (C2) · E14 This month's issues with Void, the "Show all issues" fold, and the "Earlier issues — from Shavez's
sheet (no date)" fold · E15 DIYA_TPL `{% if one %}<input type=hidden name=one value=1>{% endif %}`, rendered only while the switch is ON at
`?one=1`, so with the switch OFF the bytes are unchanged · E16 `MANY_TPL` (to the mock-up) + `GINTI_TPL` cut from DIYA_TPL itself · E17
`stock_page` passes the switch state · E18 `issue_page`: ON → many screen, `?one=1` → one-item screen, OFF → S568's screen · E19
`many_post` (`POST /stationery/diya/many`, checker + `may_issue`, refused while OFF, loops `issue()` then one commit, rolls back on
ValueError/sqlite3.Error — C7), `many_switch` (`POST /stationery/many`, owner, audited — C1), `void_post` (`POST /stationery/void`, owner,
audited `stationery_issue_voided` — C5), `history_step` / `history_void` · E20 three routes · E21 CLI `--history <db>` and `--history-void <db>`.
`menu_items` is unchanged. There is no DDL (C5). The Save button greys out on the first tap and the `pageshow` handler re-arms it (C7).

### The walk — walk_s585.py (made-up items on a scratch copy of the live assets.db; data step on schema copies)
**11 checks: 11 GREEN** — W1 (structural), W2, and M1–M9:
- **M1:** with the switch OFF, the screen is byte-identical. Owner, manager and `?one=1` pages were rendered from the FROM and TO files, each in
  a fresh process, and match. With the switch ON the TO page is the new screen. A one-word change is caught.
- **M2:** all 16 active items (13 live plus 3 made-up) are shown, each with its stock-book figure. There are 5 place buttons (48 px) and
  −/+ buttons (44 px). The Ginti card matches the one-item screen's byte for byte, and no retired item appears. The switch tap is audited, and
  a manager's switch POST gets 403.
- **M3:** one Save of 3 items wrote 3 moves with 3 audit lines. The over-stock line was saved and flagged. A forced database failure on the
  third issue wrote 0 moves and 0 audit lines. A retired item as the third wrote 0.
- **M4:** no place, no number, zeros, "abc" and an unknown place were each refused with nothing written. With the switch OFF the Save was
  refused. A manager with issue_on OFF got 403, and so did reception.
- **M5:** X-ray was saved as `xray`. The header reads "Issued this month (Lab · Reception · Sanjeevni · Clinic · X-ray)" and the cell shows
  "1 · 0 · 0 · 0 · 1". The one-item screen still has four places.
- **M6:**
  - The owner's Void kept the line (voided_by = the owner) with one audit line; stock went 8 → 10; the line shows struck through.
  - Voiding a line made before a later count left the stock at 7 and said "the count stands".
  - A second Void and an unknown id changed nothing. A manager got 403 on the page and on a forged POST; reception got 403.
- **M7:**
  - The data step wrote 7 rows: each 1 s before its opening count, with the count's day and NULL stock_before. The 9 stock lines were equal
    before and after, and the key was set.
  - A second run wrote nothing.
  - An absent item and an item without an opening count were skipped with one line each.
  - A line that would change the stock was rolled back, with no key written.
  - On the page the sheet's line is not in This month's issues or the per-place figures; it is in its fold with "no date" and can be voided.
- **M8:** `?one=1` works and returns to `?one=1`.
- **M9:** the staff page is 19,836 bytes and rendered in 0.019 s.

**Negative control** (`--expect-red`, the FROM files): **10 of 10 MUST_RED are red**. W1 is structural and green on both runs.

**Browser** (`walk/browser_many_s585.py`, PC headless Chrome): **4/4 GREEN**.
- V1, 390 × 844: places laid out 3 + 2; every − / + is ≥ 44 px and on screen; Save starts grey; tapping X-ray picks it; + + gives 2 with the
  row green, "Save karo (1)" and "→ X-ray"; "abc" greys Save; the first Save tap sends once and greys the button, a second tap sends nothing;
  nothing is wider than the phone.
- V2: the same at 1366 × 768.
- V3: the "Save ho gaya ✓ — …" line shows at 390.
- V4: the owner's page at 1366 × 768 with all folds open has no sideways scroll.
- Control (a 1900 px element) is RED.

A screenshot through a 390 px frame matched the mock-up. Full output: `deploy_kits/S585_STATIONERY_ISSUE_MANY/walk/walk_results_s585.txt`.

### The rehearsal — rehearse_s585.sh on a made-up root (/tmp/s585reh), 16:39:14–16:43:52 IST — **REHEARSAL GREEN**
Outcome 1 — fresh install, green:
- **Walks inside the installer, all green:** S585 11/11 + control 10/10 red · S582 14 (copy without `xray_mark`, see below) · S575 8 · S571 12 ·
  S568 14 (its one-item checks I4 / I4F unedited and green) · S566 12 · S563 17 + tidy fetch (102 = 102) · S560 37 + pack 9 · S548 8 · S559 43 ·
  S557 41 · S555 19 · S551 87.
- **Data step rehearsed on the scratch copy before any backup:** 7 written, then "already done" on the second run.
- **Backups and placing:** backups `stationery.py.bak_S585_d11d7183` and `assets.db.bak_S585_20261018_163916` were made before the restart;
  the file was placed and read back at its pin; /healthz 200; /stationery and /stationery/diya 302.
- **Database check:** only the 7 new moves (each exactly 1.000 s before its item's opening count, by `history (Shavez sheet)`), the key and
  one audit line were added; every other row of 39 tables was unchanged; `stationery.many` stayed absent; the backup equals the database
  before. A second data-step run said "already done".

The other outcomes:
- 2 said ALREADY INSTALLED, with the key read back as set.
- 3 (forced red), 4 (/stationery 404), 5 (/stationery 200) and 6 (/stationery/diya 404) each restored d11d7183, with healthz 200 and the
  database unchanged.
- 7 (forced red data step) restored the file, and nothing was written.
- 8 (wrong FROM byte), 9 (sorting_desk.py moved), 10 (S582 not installed) and 11 (packs.py moved) were each REFUSED before any backup.

End guard: the live program files were unchanged.

**The data step's printout on the rehearsal database (the copy of today's live data):**
```
history: wrote Register 72 pages 6 piece -> Reception (the OPD register); day 2026-10-18, 1 s before its opening count
history: wrote Register 104 pages 6 piece -> Reception (the lab register kept at reception); day 2026-10-18, 1 s before its opening count
history: wrote Register 192 pages 3 piece -> Lab (the lab register); day 2026-10-18, 1 s before its opening count
history: wrote Register 104 pages 6 piece -> Lab (the A/C register); day 2026-10-18, 1 s before its opening count
history: wrote Small notebook (copy) 2 piece -> Lab (the expense copy); day 2026-10-18, 1 s before its opening count
history: wrote Notebook (copy) 72 pages 6 piece -> Sanjeevni (Medical's daily detail); day 2026-10-18, 1 s before its opening count
history: wrote Small notebook (copy) 2 piece -> X-ray (X-ray); day 2026-10-18, 1 s before its opening count
stock: Cheque book folder (small clear bag) -- before 2, after 2
stock: Clear bag (economy) -- before 5, after 5
stock: Clear bag (premium) -- before 3, after 3
stock: Notebook (copy) 72 pages -- before 6, after 6
stock: Register 104 pages -- before 14, after 14
stock: Register 192 pages -- before 12, after 12
stock: Register 72 pages -- before 6, after 6
stock: Ring file RBU-400 -- before 1, after 1
stock: Small notebook (copy) -- before 4, after 4
history: 7 row(s) written; stationery.history_s585 set; the stock figures before = after (9 counted items)
```
Row by row (C3): all seven get `day` = 2026-10-18, the opening count's day; the sheet has no dates. They are kept out of This month's issues
and the per-place figures, and listed in "Earlier issues — from Shavez's sheet (no date)".

### R1 items, how each was met
- **B1:** `ONE_PLACES` (proved by M1 and by S568's I4F).
- **B2 / C9:** see "Order with S582".
- **C1:** the switch is on the Stationery page; sorting_desk.py is untouched.
- **C2:** both texts.
- **C3:** as the brief decided.
- **C4:** a–h, with the data step after health (g) and the undo by voiding (h).
- **C5:** no column; the page states the "count stands" sentence.
- **C6:** S582's installer shape and its full earlier-walks list, plus S582's walk.
- **C7:** separate endpoint, refused when OFF, rollback, Save disabled on the first tap.
- **C8:** built to the repository's mock-up.
- **N2:** one `stock_book` read on GET.
- **N6:** byte identity proven (M1).
- **N9:** the number gate was run (below).
- **N10:** the schema copies carry the seven exact names, an item with no count, and a second run.

### Found outside the brief (not touched)
1. **S582's frozen walk is red on today's database (Z1).** Since S582's install, `xray_mark` holds its 3 seed marks, and Z1 expects the mount
   to create an empty table. This kit ships `s582_copy_s585.py`, which drops the table and index in the /tmp copy given to S582's walk only;
   S582's walk is then 14/14. **Any later kit that runs S582's walk needs the same.**
2. `/root/finance/purchase_app.py` is now `60f2d846`. S582 recorded it as 98f7d9f0; the pin is 147201dd. It is a Sanjeevni file, only printed,
   as S575 and S582 did, and S568's walk ran green with it as it is.
3. The S582 X-ray costs page does not count issued stationery (the brief says so for this round): an issue "to X-ray" is a stock movement
   with no rupee.
4. The live stationery list has 13 active items. "A4 paper (75 gsm)", "File folder DC-217", "Token, plain" and "X-ray envelope" have no
   opening count yet, so the many-items screen shows "shelf pe 0" for them (A4 shows its received quantity).

### Not done, and why
- **Not installed, not published** — the brief overrides CLAUDE.md for this run. PUBLISH_ALL.bat was not run.
- **DUTY_MAP not changed.** Issuing stationery is an existing action of Shavez's with no due state; the kit changes the screen, not the duty
  (no stationery duty is in DUTY_MAP today). The staff-eye walk is covered by M2 / M4 / M9: the manager's own login renders the screen, and is
  refused while his switch is OFF.
- **The evidence note** in `ClaudeCowork\03_WORKING_PAPERS\_EVIDENCE\S585\` was not written, because CLAUDE.md forbids writing outside the
  repository. This report and `walk/walk_results_s585.txt` are the evidence.
- **Two commands were refused by the permission list:**
  - A PowerShell copy that included `Remove-Item -Recurse -Force` (for a `__pycache__` that never existed — everything ran with `-B`). Redone
    as a plain copy.
  - A PowerShell line containing a Python string with a NUL escape (the tool's path filter). Redone through a file.
- **Box /tmp left behind:** `/tmp/s585probe` holds my two read-only probe scripts, no data. The installer's cleanup removes it. `/tmp/s585dev`,
  `/tmp/s585kit` and `/tmp/s585reh` are removed.
- The rehearsal's made-up lock was used and the server lock was never taken, because nothing was installed.

### The server line (the owner's, after the chat's check and the publish)
`cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S585_STATIONERY_ISSUE_MANY/install_s585.sh`
It prints `S585_STATIONERY_ISSUE_MANY: DONE`, says where the switch is (a card at the top of his Stationery page, OFF), and gives the undo line.
**Undo:** `\cp -p /root/assetapp/stationery.py.bak_S585_d11d7183 /root/assetapp/stationery.py && systemctl restart assetapp`
To take the sheet's lines out, run this first, before the undo: `python3 -B /root/assetapp/stationery.py --history-void <assets.db>`. It voids
them and never deletes.

### Cost
About **US$ 7 of the run's US$ 40 budget**, read from the run's own budget counter when this report was written ($6.60 spent before this
line). The number gate (`NO_PHONE_NUMBERS.py --files-from`, 32 files: the kit and this report) is **clean**. The kit has no `__pycache__`,
and its `SUMS.md5` covers every file. The code that ran on the box (`/tmp/s585kit`) was checked md5 for md5 against the repository copy and is
byte-identical. `git check-ignore` was not run because git is not on this PC's PATH; the kit's file types are the same as S582's, which
published cleanly.
