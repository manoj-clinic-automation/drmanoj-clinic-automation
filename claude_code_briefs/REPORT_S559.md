# REPORT S559_ONE_ROAD — one easy road through the scan app (built, walked, rehearsed; NOT installed, NOT published)

## Fix round 1 (S559_FIX1, 14-Oct-2026) — the reviewer's blocker and two scanner corrections

**For Dr Manoj (plain English):**
- **Shavez keeps his sorting page.** While the desk is switched off for him, *Change / Open it* on the papers page still opens
  his sorting page for that paper, as it does today. Before this fix it would have opened the old bill page, where he cannot set
  where a paper goes. You still go straight to the desk.
- **Two more ways to get a second stamp at reception are closed.** First: tapping *Save* just as *Adjust* starts. Second:
  deleting an earlier page while adjusting a later one. Each case now saves one paper with the right pages, once.
- Every check passes on a copy of your data. The same checks fail on the first version of this kit. **Nothing is installed yet.**

### For the chat — the proof

**Run.** All times are IST, read from the box clock unless marked.
- FROM pins read on the box at **14:48:04**. All seven equal the brief: asset_register `9e94b11c`, sorting_desk `91a04674`,
  clinic_papers `058c9bcb`, asset_machine `66c37197`, scanner_widget `1143c77b`, claude_reread `d9b75e78`, claude_reader `3894dc23`.
- The browser walk ended at **14:53:50** (the PC log file's time).
- On the box: the rebuild, walk and L8/J3 control ran **14:56:10 → 14:56:18**; the rehearsal ran **14:56:24 → 14:57:53**.
- The live state was re-read at **14:58:09**, and the box's `/tmp` was cleaned at **14:58:15**.
- No build lock was taken, because nothing was placed. The lock was absent at 14:48 and at 14:56.

**Read first:** the S559_ONE_ROAD brief, this report, the kit, and the review `S559_KIT_REVIEW.md` (B1, C1, C2, the six notes).

**What changed in the kit (`make_s559.py`; each anchor exactly once, on Windows and on the box, on both pythons):**

| Finding | Change |
|---|---|
| **B1** | CP edit 5, line 177: the reviewer's exact template expression. The link goes to `s559_href(p.b)` only when it is a `/desk` link; otherwise it goes to `url_for('d664_paper', bid=…)`. |
| **C1** | `var lastQS559 = null, adjGenS559 = 0;`. `stageCloseS559()` and `clearSrc()` bump it. `adjustOpen` takes `var genS559 = ++adjGenS559;`, and its `onload` returns first if `genS559 !== adjGenS559 \|\| !pageSrc[i]`. |
| **C2** | `dropSrc(i)`: `… if (adjustIdx === i) adjustIdx = -1; else if (adjustIdx > i) adjustIdx--;`. `adjustDone()`: `if (i >= pages.length) { stageCloseS559(); return; }` placed before `pages[i] =`. |

- The widget now has **9 counted edits**, up from 5. Every new line carries an `S559` mark. The only old lines replaced are the
  first build's two, plus `dropSrc` and `clearSrc`.
- All three widget changes sit in S523 code. Only the intake reaches it: `dropSrc`/`clearSrc` are called only under `cvScanOn`,
  and `adjustOpen`/`adjustDone` only from the intake's Adjust path.
- The three helpers are in the same function scope as `adjustDone`: one IIFE, lines 61–1639.

**Pins: FROM → TO, rebuilt on the box from the live bytes (equal to the Windows build).**

| file | FROM | first build | **FIX1 TO** |
|---|---|---|---|
| `asset_register.py` | `9e94b11c` | `20ef7bc6` | `20ef7bc6b44079f3181d9c52519e8b94` (unchanged) |
| `sorting_desk.py` | `91a04674` | `a59fa38d` | `a59fa38d7c7f145c8fefa52bad5676d1` (unchanged) |
| `clinic_papers.py` | `058c9bcb` | `e0c13eeb` | **`80e3cd8d2ef8e8953b2ae3fec3f85203`** |
| `asset_machine.py` | `66c37197` | `0caec41e` | `0caec41e655cfd51c2eaf9176ee33365` (unchanged) |
| `scanner_widget.js` | `1143c77b` | `552effcd` | **`1128ac975ba2543e1fe9edf7c721d4f8`** |

- The clinic_papers pin **reproduces the reviewer's measured `80e3cd8d2ef8e8953b2ae3fec3f85203` exactly.**
- The four Python files compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`, and both pythons build the same bytes.

**Syntax check of the widget.** `node --check` could not be run: there is no `node` on this PC or on the box (S555's report found
the same). In its place, browser check **V** has V8 (Chrome's JavaScript engine, the one node uses) compile the whole widget with
`new Function(src)`, without running it. Result: **GREEN**. The check can fail: on a copy with one brace removed it went
**RED** with `SyntaxError: Unexpected token ';'`.

**The walk (`walk_s559.py`, on the box, isolated as before).** It now has **43 checks**: the first build's 41, plus L8 and J3.
J1 was updated for four replaced old lines.
- **L8:** the papers page's *Change / Open it*.
  - A manager with the desk off gets `/papers/<id>`.
  - The owner gets `/desk?open=<id>`.
  - The manager with `desk.on` switched on gets `/desk?open=<id>`.
- **J3:** C1 and C2 are present in the code, in the right order.

The log, as printed (on the box inside the rehearsal's installer, and again standalone):
- **Walk on the built files: `43 checks: 43 GREEN, 0 RED`.**
- `SIZES home 7923 B (29 ms) . desk 21335 B (12 ms) . All papers 51524 B . the bar 1481 B`.
- **Control on the live (S557) files: `43 checks: 7 GREEN, 36 RED`.**
  - `CONTROL must-be-red: W2, M1–M6, H1, H2, O1–O4, L1–L6, B1–B3, F1, F2, N1, N3, K2, Z1, D1, C1, R1, P1, J1, J2, L8, J3 -- all RED`.
  - The 7 that stay green are unchanged: W1, W4, K1, L7, N2, T1 and T2.
- **Control on the first S559 build's files** (the new walk; the FIX1 build, with the first build's `clinic_papers.py e0c13eeb`
  and widget `552effcd` swapped in): **`43 checks: 40 GREEN, 3 RED (L8, J1, J3)`**.
  - L8's red shows the blocker exactly: `{'manager, desk off': '/bills/164', 'owner': '/desk?open=164', 'manager, desk on': '/desk?open=164'}`.
  - The id 164 is a made-up walk row in the scratch copy.

**The three earlier walks, on the FIX1 files (inside the rehearsal's installer):**
- S557: `41 checks: 41 GREEN, 0 RED`.
- S555: `19 checks: 19 GREEN, 0 RED`.
- S551 (through `s551_lines_s559.py`, unchanged): `87 checks: 87 GREEN, 0 RED`.

**The browser walk (`walk/`, headless Chrome on the PC): `20 browser checks: 20 GREEN, 0 RED`.**
- The widgets: OLD = the live `1143c77b`, **PREV = the first S559 build `552effcd`** (the new `--prev` argument), NEW = `1128ac97`.
- OpenCV is the live `ff1e10e7`. The photos are made up, and the walk itself answers every upload.

| Check | Result |
|---|---|
| **V** | The widget compiles (above). |
| **A, A', B, C, D** | As in the first round, with the same results. NEW: one paper, adjusted, the stage closed. The live widget's control still shows two stamps. |
| **E (C1)** | Adjust is tapped, and its image is made to load 700 ms late (a slow phone). *Save* is tapped while it loads. NEW: **one** paper (the page as it was), and the late image does **not** reopen the stage. Her next tap adds 0 pages; a second *Save* queues nothing. |
| **E' control on PREV** | The late image reopens the stage (*"✔ Theek hai — page 1"*), her tap makes a page, and *Save* queues it: **two papers, two stamps**. |
| **F (C2)** | Three pages; page 2 is being adjusted; page 1 is deleted; *Save*. NEW: `adjustIdx` 0 after the delete, and **one** paper holding `[page2-adjusted, page3]`: two different pages, once each. |
| **F' control on PREV** | `adjustIdx` stays 1, and the paper holds **`[page2, page2-adjusted]`**: page 2 twice, page 3 lost. |
| The live widget, for the record | E is red (two papers). F saves `[page2, page3]` un-adjusted and leaves the stage open. |
| **S × 7** | The finance app's five surfaces and the asset page load and save **exactly as before**: the DOM is identical, there is no error, the smart path is off, there is no S559 mark, and the upload (fields, file name, type, size, bytes) and the way back are the same. The intake's DOM is identical, OpenCV is ready, and `S559.1` is present. |
| **W × 3** | The bar: 1 line at 1366 px (11 items, 1342 px); 3 lines at 390 px with no sideways scroll. The pages were measured on the first run's page dumps, because `asset_register.py` and `sorting_desk.py` are byte-for-byte the same in this round. |

How scene F sees the pages: the walk page has no PDF library. Without one, the widget would save page 1 only as a JPEG. For scene F
only, the harness puts in a stand-in `jspdf` that records each page handed to it, so the saved paper's exact pages are read.

**The rehearsal (`rehearse_s559.sh`, made-up root `/tmp/s559dev/root`): `REHEARSAL GREEN`.**

| Outcome | Result |
|---|---|
| 1 | DONE. The rebuild equals the pins (`0caec41e a59fa38d 80e3cd8d 1128ac97 20ef7bc6`). Walk 43/43; control 36 RED, all named; S557 41/41; S555 19/19; S551 87/87. Backups are present, and the undo line starts `\cp -p`. |
| 2 | ALREADY INSTALLED. |
| 3 | Forced red: restored to `66c37197 91a04674 058c9bcb 1143c77b 9e94b11c`. |
| 4 | `/desk` 404: restored. |
| 5 | `/desk` 200: restored. |

**After (14:58:09):**
- The 7 live files are at the FROM pins, and there are 0 `bak_S559` files.
- `assetapp` is active, `/healthz` 200, `/desk` 302.
- `/tmp/s559*` is removed (14:58:15).

**The kit and the gates.**
- `deploy_kits\S559_ONE_ROAD\` has 25 files, all LF; the file set is unchanged.
- Changed in this round: `make_s559.py`, `walk_s559.py`, `walk/harness.js`, `walk/run_browser_walk.py`, `walk/walk_results.txt`,
  `PIN_TO_clinic_papers.txt`, `PIN_TO_scanner_widget.txt`, `README.md`, `KIT_ID.txt` and `SUMS.md5`.
- `install_s559.sh`, `rehearse_s559.sh`, `s551_lines_s559.py` and `s559_ar_block.txt` are not changed (install `fc17b181`,
  rehearse `b7ea537b`).
- **Byte-identical to what ran:** the box's md5 of all 21 executed or pinned kit files equals the repository copy, 0 differ.
  This includes make `5a3c5e07`, walk `94bbb712`, harness `f7e84709` and run_browser_walk `d233bcc4`. README, KIT_ID, SUMS and
  `walk_results.txt` were written after the run; they are not executed.
- **SUMS.md5:** 24 lines, 0 mismatches.
- **`.gitignore` (last match wins):** `git check-ignore -v --non-matching` over the 25 kit files, this brief and this report gives
  27 lines and **0 ignored**. This used GitHub Desktop's git, read only; `git` is not on this shell's PATH.
- **Contact-number gate,** as PUBLISH_ALL runs it, over the same 27 files with this report in its final words:
  `NO_PHONE_NUMBERS: clean -- 27 staged file(s) checked (numbers and credentials).`

**The six review notes: seen, not changed.**
1. Widget scope: confirmed inert outside the intake. Seen, not changed (FIX1's three changes keep to the same rule).
2. (a)/(b)/(c) hold. Seen, not changed.
3. Cache-bust by the widget's mtime, with restore/undo by `cp -p`. Seen, not changed.
4. Installer order and safety, including the minor wording of a half-moved state ("another kit moved it"). Seen, not changed.
5. Items 1–9 present and permission-correct. Seen, not changed.
6. Small: (i) an old-record AMC/CMC reads as live, because its own "Contract renewal" due date is not consulted; (ii) a manager
   with the desk off sees *Bills awaited (N)*, whose page says the desk is off. Seen, not changed.

**Calls I made, with the reason for each:**
- **The widget's mark stays `S559.1`.** The first build was never installed, so no phone holds an `S559.1` that differs.
  Keeping it leaves the installer, walk K2 and browser check S unchanged.
- **C2's adjustDone guard closes the stage** (`stageCloseS559()`), rather than leaving it open with no page under it.
- **Scene E makes the load slow on purpose.** Only the one image `adjustOpen` creates starts loading 700 ms late, so *Save*
  lands inside the load every time, not by chance.

**Not done, and seen outside the brief (not touched):**
- **Not installed and not published,** as the brief says.
- `node --check` was not run, because there is no node on either machine. The V8 check stands in for it (above).
- **The permission list refused one command.** It was a compound ssh line that began by clearing a `/tmp` folder with
  `rm -rf`. I did not respell it: I used a fresh `/tmp/s559fix1b` folder instead and cleaned my own scratch with a plain `rm -r`
  at the end.
- **My first box script made an empty snapshot.** The service does not carry `ASSETS_DB` in its unit environment, and my script
  lacked the installer's fallback to `/root/assetapp/assets.db`. The walk opened only that empty `/tmp` copy, and nothing else
  was touched. The script was fixed, and the run above is the fixed one. The kit's installer already had the fallback.
- **Seen in the widget, not changed:** after C2 shifts `adjustIdx`, the stage's button label still names the old page number
  (adjusting page 2, then deleting page 1, still reads *"Theek hai — page 2"*). This is cosmetic only: the right page is saved.

**Cost:** about **US$4** of API credit for this round, read from this session's budget meter when this section was written.

**Nothing installed, nothing published.**

---

## The first build (S559_ONE_ROAD) — its report as written

**For Dr Manoj (plain English):**
- **From the portal tile to a sorted paper, click by click:** tap *Asset Register* → the scan app's home opens with one card,
  *"14 papers waiting — Open the sorting desk"* → tap it → the desk opens on the newest paper → choose where it goes → *Save* →
  the next paper opens. That is the whole road.
- **Every page of yours now has the same menu at the top, the desk's pages too:** *Sorting desk (N) · The month · Bills awaited (N)
  · Implant ledger · Machines · Renewals · All papers · Vendors · Admin*. *Drafts* and *Staff* moved off the menu: *Drafts* is on
  the Assets page, *Staff* is on Admin.
- **Any paper you click opens on the desk:** in *All papers* (the old *Purchases*), the papers list, Bills awaited, the implant
  ledger, The month, or a machine page. A pharmacy paper still opens its old page. The old page now shows the scan at the top,
  a button *Open on the sorting desk*, and a true word: *Waiting / Filed / Accepted / Set aside*.
- **Reception's scanner fixed (one paper, one stamp):** tapping *Save* while adjusting a page now saves that one paper, adjusted,
  and closes the adjust box, so a second tap cannot make a second stamp. Reception's screen looks and works the same otherwise.
  Shavez gets the desk items once you switch *Sorting desk for Shavez* ON.
- Every check passed on a copy of your data, and the same checks fail on today's files. **Nothing is installed yet.**

---

## For the chat — the proof

**Run:** 14-Oct-2026, all times IST, read from the box clock unless marked.
- FROM pins read on the box at **13:50:21**.
- Browser walk ended **14:25:03** (the PC's file time).
- Rehearsal ran **14:26:20 → 14:27:50**.
- Box `/tmp` cleaned and the live state re-read at **14:29:00**.
- No build lock was taken, because nothing was placed. The lock was absent at 13:50 and at 14:26.

**Read first:** the S551 v4, S555 and S557 briefs and S557_FIX1, REPORT_S557, all of `deploy_kits\S557_MACHINE_PAGES\` (the
shape copied), S545's kit and its browser walk (the seven surfaces), and `BUILD_NORM_v1.md`.

### 1 · Pins (read on the box, all equal to the brief)

| file | live md5 = brief | TO (rebuilt on the box = Windows build) |
|---|---|---|
| `asset_register.py` | `9e94b11c1a55eee6fdb22b9862b6db44` | **`20ef7bc6b44079f3181d9c52519e8b94`** |
| `sorting_desk.py` | `91a04674e27de3fbfc7602403403c821` | **`a59fa38d7c7f145c8fefa52bad5676d1`** |
| `clinic_papers.py` | `058c9bcb5a4973f8a15984b645ff57d7` | **`e0c13eebd65ddaf3354ce869bae4eb2c`** |
| `asset_machine.py` | `66c37197ae7c0d63874e213d52e7b9e5` | **`0caec41e655cfd51c2eaf9176ee33365`** |
| `scanner_widget.js` | `1143c77b13ae62652d4d961a92b9a9ab` | **`552effcdd3d984a1e460c3ebeb2ddb44`** |
| `claude_reread.py` (read only) | `d9b75e784c4a806e941f3d1a243990e1` | — |
| `claude_reader.py` (read only) | `3894dc2358abd875ee61ced7619e1e1b` | — |

The four Python files compile on `/usr/bin/python3` and `/root/wa/venv/bin/python3`. **No database change.** The installer still
takes a backup-API copy of the database as a safety copy.

### 2 · The counted edits (`make_s559.py`; each anchor exactly once, on Windows and on the box) — 61 in all

**`asset_register.py` (34 edits plus the helpers block `s559_ar_block.txt`, appended after S557's block)**

| Item | What changed |
|---|---|
| 1 | `BASE`: `{% if s559bar %}{{s559bar}}{% elif …old header… %}`. `page()` passes `_s559_bar(u)`. Reception and the login page get `''`, so the old header renders byte for byte. |
| 2 | The dashboard begins with `{{s559home}}`. |
| 9 | Zone: `_s559_zone_once` gives one option per name, and the filter becomes `zone_id IN (…)`. |
| 9 | Renewals: a `Kind` column from `_s559_kind(label, contract_type)`; due and expiry dates use `s559_dmy`. |
| 9 | The machine page: dd-mm-yyyy for purchased, the dates to watch, parts, files, the service log and next due. `From bill` goes to `s559_href`. The PM sentence sits behind `s559pm` (`_s559_pm`). |
| 1, 6, 7, 8, 9 | All papers: retitled; *N waiting on the desk →*; the four filter words (with `value=`); ONE link to The month (the owner's second link is gone); row links go to `s559_href`; dd-mm-yyyy; `_flow("All papers", url_for("dashboard"))`. |
| 5 | The bill page: the four badges, *← All papers*, *Open on the sorting desk* (`_s559_desk_href`), and the iframe card. |
| 1 | *← Purchases* becomes *← All papers* (3 places). |
| 1 | Admin gains a *Staff* card. |

The helpers in the block: `_s559_bar`, `_s559_items`, `_s559_desk_n`, `_s559_awaited_n`, `_s559_home`, `_s559_paper_href`,
`_s559_desk_href`, `_s559_pm`, `_s559_kind`, `_s559_zone_once`, `_s559_dmy`. The Jinja globals are `s559_bar`, `s559_href`,
`s559_kind`, plus the filter `s559_dmy`. The mark is `ROAD_S559`.

**`sorting_desk.py` (11 edits)**
- The mark `ROAD = "S559"`.
- The bar on the OFF page, the desk (inside `#app`), and `PAGE_HEAD` (which covers Bills awaited, the ledger and The month).
- `?open=`: `_s559_open` (by id or by stamp, through `_visible`), `cfg.open`, `loadList(C.open||0)`, and the grey line.
- Three row links go to `s559_href`.

**`clinic_papers.py` (7 edits)**
- The papers list: the old month and challans links hidden while the desk is mounted; *The month →* points to `/desk/month`.
- The picture, the stamp and *Open it* go to the desk.
- The *Where each paper stands* row and the paper page's *Bills awaited* link go to `/desk/awaited`.

**`asset_machine.py` (4 edits)**
- The mark `ROAD`.
- *Its paper* goes to `AR._s559_paper_href`.
- `cover_line` reads the old record.
- `live_amc()`.

**`scanner_widget.js` (5 edits, item 10)**
- `doSave`'s inlineStamp branch calls `adjustDone()` first when `cvScanOn && adjustIdx >= 0`, then `stageCloseS559()`.
- `addPage` and `addWhole` return on `staleS559()` (`cvScanOn && autoPage && adjustIdx < 0`). On the intake the stage is only
  ever an Adjust stage, so a leftover never makes a page. The stage is also closed.
- `enqueue`: the same pages within 10 s are queued once.
- The helpers and `window.__scannerS559 = {version:"S559.1"}` (set only when `inlineStamp`) sit inside the S441 block.
- Walk J1 proves that every changed line is S559's and that exactly two old lines were replaced.

### 3 · The walk (`walk_s559.py`, on the box, isolated as S557's)

**Isolation, as S557's walk:**
- A backup-API snapshot of the database; scratch import with `__file__` asserted.
- The environment set before import: `ASSETS_DB`, `ASSETS_UPLOADS`, the made-up key and URL, `CLINIC_PORTAL_DIR`,
  `FINANCE_LOCAL_URL`, `SHARED_LIB_DIR`. `SARVAM_API_KEY` and `ANTHROPIC_API_KEY` are unset.
- Made-up logins `walk_own_2031` and `walk_mgr_2031`, so no real name is used.
- Made-up papers `Z-2031-S901…S911`, with suppliers differing in their first two words. Today is made up as 15-Jun-2031.
- Walk and control each run in their own process.

**Log (the installer inside the rehearsal, 14:26–14:27):**
- **Walk on the built files: `41 checks: 41 GREEN, 0 RED`.**
- `SIZES home 7923 B (21 ms) . desk 21335 B (8 ms) . All papers 51524 B . the bar 1481 B`.

| Checks | What they prove |
|---|---|
| K1 | Reception's intake and its own list are byte for byte the live files' HTML, except the widget's `?v=<file time>` stamp (it changes because the widget changed). There is no bar and no desk link. |
| M1 | The owner's bar is on all 14 pages, in the brief's order. |
| M2 | Desk N = `/desk/api/list` total = `len(waiting)`, and Bills awaited N = `len(awaiting_challans)`, on every page. |
| M3 | Drafts and Staff are absent from the menu, and both pages answer 200 (reached from Assets and Admin). |
| M4 | For a manager, *Sorting desk* is hidden while `desk.on` is off. Switched on, he sees HIS count: the owner's count minus a Personal paper. |
| M5 | The bar is inside the desk's full-height frame, and it is the same markup on desk and app pages. |
| M6 | Each item goes to its named door. |
| H1, H2 | The home card is above everything, with *Bills awaited N · Implant ledger · The month*. At 0 it reads *No paper waiting.* A manager whose desk is off gets no card. |
| O1–O4 | `?open=<id>` and `?open=B-xxxx` are handed to the desk. Pharmacy and unknown ids open the desk normally with the grey line. A Personal paper is refused for a manager and opened for the owner. |
| L1–L7 | Rows go to `/desk?open=`: All papers in all 5 filters (pharmacy goes to `/bills/<id>`), the papers list (picture, stamp, *Open it*), Bills awaited, the ledger, The month, and a machine's paper. A manager whose desk is off keeps the old page. |
| B1–B3 | The iframe sits at the top with *Open the file*. The desk button shows on a clinic paper and not on pharmacy. The badges read Waiting / Filed (Other document and pharmacy) / Accepted / Set aside. |
| F1, F2 | *N waiting on the desk →*; the four filter words. |
| N1–N3 | No old route in any menu, toolbar or the home page, and one link to The month. The three old pages answer 200 with their banners. BACK goes to `/scanapp/`. |
| K2 | The served widget carries S559.1. |
| Z1, D1, C1, R1, P1 | Item 9: Zone once, and it filters both Unassigned zones. dd-mm-yyyy. *Covered (old record): AMC — WALKOLD SERVICES*. Kind: Warranty / AMC / CMC / Licence / Insurance / Other. The PM sentence shows for a live AMC and for an old-record AMC, and not for a lapsed AMC or no cover. |
| J1, J2 | The widget's lines, as described in §2. |
| W1, W2, W4, T1, T2 | Isolation, the marks, under 2 s, and the scratch copy only. |

- **Control on the live (S557) files: `41 checks: 7 GREEN, 34 RED`.**
  - `CONTROL must-be-red: W2, M1, M2, M3, M4, M5, M6, H1, H2, O1, O2, O3, O4, L1, L2, L3, L4, L5, L6, B1, B2, B3, F1, F2, N1, N3,
    K2, Z1, D1, C1, R1, P1, J1, J2 -- all RED`.
  - The 7 that stay green test what must not change: W1, W4, K1, L7, N2, T1 and T2.

### 4 · The three earlier walks, on the new files (inside the installer)

**S557: `41 checks: 41 GREEN, 0 RED`.** Its unchanged-pages baseline is dumped from the S559 build **without**
`asset_machine.py`, and not from the live files. S559 changes every page's menu by design. K1 then still proves the switch rule:
with `machine.on` off, a manager's machine page is exactly the page the app gives without the module.

**S555: `19 checks: 19 GREEN, 0 RED`.**

**S551: `87 checks: 87 GREEN, 0 RED`.** It runs from a `/tmp` copy made by `s551_lines_s559.py`, which changes three lines. The
installer refuses unless each is found exactly once. The frozen S551 kit is not edited.
1. Its S555 date line, as S557 already did.
2. H2's row link: `/bills/<id>` becomes `/desk?open=<id>` (S559 item 4).
3. H3: the second link *"Consumption — now The month"* must now be absent (S559 item 7). H3 still asserts the one link to
   `/desk/month`.

My first run showed these as the only reds. A third red, H1 (the header title), was fixed in the bar itself: the title is kept
bold, so `Scan app &amp; assets</b>` holds.

### 5 · Item 10 in a real browser (`walk/`, headless Chrome on the PC; the box has no browser)

The setup:
- OpenCV is `ff1e10e7`, the live copy.
- OLD is the live `1143c77b`; NEW is `552effcd`.
- The photos are made up, and the walk itself answers every upload.

**Result: `15 browser checks: 15 GREEN, 0 RED`** (`walk/walk_results.txt`).

**A — Save while adjusting.**
- NEW: exactly one paper is queued, holding the adjusted page (its hash equals B's adjusted page and differs from the capture).
  The stage is closed and the label is back to *✔ Add this page*. Her next tap on the old button adds nothing, and a second Save
  queues nothing.
- **Control A' on OLD** reproduces the reported fault exactly:
  - the un-adjusted page is queued;
  - the stage stays open with *"✔ Theek hai — page 1"*;
  - the next tap makes a new page from it;
  - Save queues it: **two papers, two stamps**.

**B — Adjust → Theek hai → Save:** one paper, adjusted. The adjusted page is identical to what OLD makes.

**C — the page under adjustment deleted, the stage left on screen:** NEW adds nothing on a tap; OLD adds a page.

**D — the same pages twice within 10 s:** NEW queues them once; OLD queues them twice. A different paper straight after is queued
(NEW 1 then 2; OLD 2 then 3).

**The seven surfaces:**
- The finance app's five and the asset page each load with their own `SCANNER_CONFIG`:
  - the DOM is identical, with no error;
  - the smart path is off and there is no S559 mark;
  - the save path (choose photo → Add → Save) sends **the same upload**: fields, file name, type, size and bytes all equal, and
    the way back is the same.
- The intake's DOM is identical, OpenCV is ready, and `S559.1` is present.

**The bar's fit** (on the account, desk and month pages, with a 20-character name and 3-digit counts):
- At 1366 px the 11 items sit on one line beside the title (bar 1342 px wide).
- At 390 px it wraps to 3 lines with no sideways scroll.

### 6 · Installer and rehearsal

**`install_s559.sh`** (S557's order; `S559_*` variables). Its steps, in order:
1. Gates.
2. FROM pins of the 5 files and the 2 readers. ALREADY INSTALLED when all 5 are at TO.
3. Rebuild from the live bytes.
4. TO pins.
5. Compile on both pythons.
6. One snapshot, then: baseline, walk, control, S557 baseline (no `asset_machine`), S557, S555, S551. `DRY=1` stops here.
7. `.bak_S559_<from8>` beside the 5 files, plus `assets.db.bak_S559_<time>`.
8. Place, then read the md5 back.
9. Restart `assetapp` only.
10. `/healthz` 200, `/desk` **302 only**, and the served widget carries `S559.1`.
11. The plain lines and the undo line in `\cp -p` form (printf `'\\cp -p'`).

Any red after placing restores all 5 files. There is no data step: a database change would have stopped the build, and none was
needed.

**`rehearse_s559.sh`** (a made-up root under `/tmp/s559dev/root`):
- It refuses `/root/`, `systemctl` and port 8030.
- The stand-in answers `/healthz` 200 and `/desk` 302, then 404, then 200, and serves the placed widget.
- Result: **`REHEARSAL GREEN`**.

| Outcome | Result |
|---|---|
| 1 | DONE. Rebuilt = pins. Walk 41/41, control 34 RED all named, S557 41/41, S555 19/19, S551 87/87. Backups present. The undo line starts `\cp -p`. |
| 2 | ALREADY INSTALLED. |
| 3 | Forced red: restored to `66c37197 91a04674 058c9bcb 1143c77b 9e94b11c`. |
| 4 | `/desk` 404: restored. |
| 5 | `/desk` 200: restored. |

**After (14:29:00):**
- All 7 live files are at the FROM pins, with no `bak_S559` file.
- `assetapp` is active, `/healthz` 200, `/desk` 302.
- `/tmp/s559*` is removed.

### 7 · The kit and the gates

**`deploy_kits\S559_ONE_ROAD\`, 25 files, all LF:**
- `KIT_ID.txt`, `README.md`, `install_s559.sh`, `make_s559.py`, `s559_ar_block.txt`, `walk_s559.py`, `s551_lines_s559.py`,
  `rehearse_s559.sh`;
- 5 `PIN_FROM_*`, 5 `PIN_TO_*` and 2 `PIN_READ_*`;
- `walk/` (`run_browser_walk.py`, `harness.js`, `fit.js`, `walk_results.txt`);
- `SUMS.md5`.

There is no `.json`, no database, no copy of a live file and no `__pycache__`.

**Byte-identical to what ran on the box:**
- The box's md5 of every kit file at 14:27:50 equals the repository copy: install `fc17b181`, make `7d6e8128`, block `929b46ef`,
  walk `047d5fef`, s551 lines `c934ec3d`, rehearse `b7ea537b`, the 12 PIN files, and the `walk/` scripts.
- README, KIT_ID, SUMS and `walk_results.txt` were written after the run; they are not executed.

**Gates:**
- **SUMS.md5:** 24 lines, 0 mismatches.
- **`.gitignore`:** `git check-ignore -v --non-matching` (last match wins) shows all 25 kit files and the brief as not ignored.
- **Contact-number gate,** as PUBLISH_ALL runs it: `NO_PHONE_NUMBERS: clean -- 26 staged file(s) checked`. It is re-run on this
  report below.

### 8 · Today's Variety Stationers papers at reception (read only, from the box; nothing changed)

| Stamp | Scanned (IST) | Pages | Lane | Status | Supplier on the paper |
|---|---|---|---|---|---|
| **B-0162** | 13:36:07 | 1 | Other document | captured | another name was read |
| **B-0163** | 13:36:10 | 1 | Clinic | approved | VARIETY STATIONERS |

B-0163 is today's only paper read as Variety Stationers. B-0162 was stamped **3 seconds earlier**, from the same scanning
session. This fits the path the brief describes: the un-adjusted first page, then the adjusted one. The two files differ
(different picture fingerprints and different upload tokens), as two captures of one paper would.

**For the owner:** open B-0162 on the desk (`/desk?open=B-0162` once installed, or *Open B-____* today). If it is the same
challan, set it aside. The tool did not touch either paper.

### 9 · Calls I made (the brief left room), each with its reason

1. **Shavez while the desk is off.**
   - *Sorting desk* is hidden from him, as the brief says. *The month*, *Bills awaited* and *Implant ledger* stay in his menu and
     go to `/desk/…`, as the brief says. They open the desk's one-line "switched on by Dr Manoj" page, which now carries the bar.
   - His paper rows, the bill page's desk button and the *waiting on the desk* header are not switched to the desk until he can
     use it. While off, he keeps the old bill page and the old *N pending* badge. The alternative would send him into a page
     that only says "off".
   - The live `desk.on` is absent (OFF), so this is what Shavez sees on install day.
2. **Renewals had no Kind column.** It had *What*, showing each reminder's label, and all 12 live reminders are labelled
   "Warranty" (the asset form's own row). I added a *Kind* column, decided in one helper (`_s559_kind`). A *Contract renewal*
   takes the machine's contract type. Live data will still read Warranty on every row, because that is true today.
3. **The PM sentence** counts an old-record AMC/CMC when the cover history is empty, so a machine that reads *Covered (old record):
   AMC* still shows it. A lapsed or voided AMC in the history does not.
4. **The bill page's item links to `/purchases?item=…` stay.** The month has no per-item place to link to. The brief says "if it
   has one; otherwise they stay".
5. **The bar's *account* item** shows the person's own name, as the old menu did. The title links home, since *Dashboard* is not
   in the brief's order.
6. **The stale-stage guard** treats any `addPage`/`addWhole` on the intake with nothing under adjustment as a leftover. On the
   intake (smart outline + auto page) the stage is only ever an Adjust stage. The leftover stage is also closed; no page is
   added.
7. **Reception's intake HTML** changes in exactly one place: the widget's own `?v=<file time>` stamp. That is how phones fetch
   the new widget. K1 asserts it is the only difference.

### 10 · Not done, and seen outside the brief

**Not done:**
- **Not installed and not published**, as the brief says.
- The four browser scenes ran on made-up photos in desktop Chrome, not on reception's phone. The first real Adjust → Save after
  install is the real proof.

**Seen outside the brief (not touched):**
- Deleting a page whose index is *before* the page being adjusted leaves `adjustIdx` pointing at the wrong page. This is in the
  widget's S523 code. It is rare and was not reported.
- A manager reaches `/staff` only by its address now, because Admin is the owner's page. The brief chose this.
- The DUTY_MAP is untouched; the brief forbids it. The kit adds no staff duty: the desk's door for Shavez is unchanged and
  switched by the owner.

**FOR THE PARENT:** rename the portal tile *"Asset Register — Clinic assets & AMC"* to **"Scan app & assets"**.

### 11 · Cost

About **US$14** of API credit for this run, read from this session's budget meter when this report was written.

**Nothing installed, nothing published.**
