# HANDOFF RUNBOOK — S226 close · 06-Sep-2026 · v158

*Supersedes v157 (S225 close). §0 what happened · §1 the models it earned · §2 the live backlog (the live list is `OWNER_TODO_LIVE.md`; this is the close-time snapshot) · §3 install discipline · §4 the boundary. Full narrative: Archive §S226. Pins: Register v5.75, `live_pins_S226close.txt`. The one document to read instead of the nine S226 papers: `S226_BUILD_BRIEF`.*

---

## §0 · WHAT HAPPENED

**One calendar day, 06-Sep 04:15 → 14:00 IST, ~10 attended hours, a model switch and one context compaction; thirteen kits, twelve installed by the owner from one line each and every VPS pin pasted back from the box the minute it landed.**

1. **The readiness header** (⭐1 item 1, `S226_READINESS`): the count and drift pages open with four data lines, frozen into `stock_check_readiness` at the seal. His first look found row counts where item counts belonged — **F-324**; `_feed_latest()` (`S226_DRIFT_TRUTH`), plus `/page/now` for *"where do I see the latest stock"*.
2. **The feeds made true before the count:** the unattended loop proven at 09:00:59 / 09:01:01 / 09:01:04 (⭐1 item 2 open). LACTOVAX +7 had two causes in `push_snapshot.py` — **F-325** (`S226_F322_SUBSET`); purchases stuck at 03-Sep because `push_expected.py` never read PURCHASE **BILL** ITEM WISE — **F-326** (`S226_PURCHASE_BILLITEM`); the *"373/373 agrees"* was a false agreement. Marg's closing stock cannot be back-dated; the count follows the day's purchase entry. Below-zero 13 → 12 (bills into Marg).
3. **THE COUNT — Darpan on the shelf, Amir at the keyboard — found the page's faults faster than any walk:** the search box (his ask) and behind it the S213 crash on every chip but *To do* (**F-327**, `S226_COUNT_SEARCH`) · *sent* forgotten on reload, time in UTC (**F-328**, `S226_SENT_STICKY`) · a counted item opening blank (`S226_REVISIT`) — **and that kit saved zero over a counted figure in silence (F-329)**, caught by him in twenty minutes, closed by `S226_ZEROFIX` · the silent store and its hoisting trap (**F-330**, `S226_SAFESTORE`). **NO count submitted through that window.** He moved the counters to an Excel pad and put the page on hold; it was hardened, walked (34 · 30 · 13) and cleared, and stays the second choice by his ruling.
4. **The result workbook previewed with him three times before code → D378.** Then **`S226_PAD_IMPORT`** — the sheet IS the count, never rejected (**D377**); parts join a family; issues resolve by the original row. Then at his ruling **`S226_PAD_ONPAGE`** — the flow ON the stock-check page: details → prefilled SHEET 1 → one-tap upload with a processing box → the next sheet → repeat (**D381**); the same file twice is the same count; **F-331** found on the way (the live reader had shipped without the column its walk proved). Then **`S226_STOCK_CLOSE`** — steps 1-2-3-4, sheets named SHEET 1 / SHEET N REMAINING / FINAL RESULT, **Close the stock check** only when the server verifies nothing is left, STOCK CHECK COMPLETED, no more sheets; the checker alone closes an abandoned count as it stands (**D382**). 169 checks at 390px; screens read by a sub-agent.
5. **Recorded from his words:** **D379** (explanations in tranches; delivery on the portal tiles; staff see rupees) · **D380** (*one coherent system* — spot checks anywhere are counts in the same ledger; the Excel is a phase). Amir's password set from the box (the joiner reset button is a stub, **F-333**). One F-233 breach (**F-332**).

**At close the counters are filling SHEET 1; nothing uploaded yet.** Live: `stock_app.py` `fdcdf873…` · `stock_check_live.html` `6fd3b7f9…` · `padwriter.py` `77c43e47…` · `padreader.py` `f617d7d5…` · `stock_drift.html` `daa40ee8…` · `stock_now.html` `91cdc56d…` · `stock_pad.html` `4b593dbb…`; manojz `push_snapshot.py` `03a84524…` · `push_expected.py` `a0e47a98…`.

**Canon:** Archive v1.72 (+14,130 → 1,168,805, prefix proven) · Register v5.75 · Fault v2.57 (F-324 … F-333) · this runbook · `START_HERE_SESSION_227` · `S226_BUILD_BRIEF` · `live_pins_S226close.txt`. **Next free D383 · F-334 · Session 227.**

---

## §1 · MENTAL MODELS THAT EARNED THEIR PLACE THIS SESSION

- **The walk proves the kit; the counter proves the join.** Six kits went live during a count and the counters found a fault in four of them within minutes — every one on a path the walk had not driven (a revisit, a reload, a second tap, a chip). The walk now drives the failure paths and every chip, and a fix installed during live use is walked on the path that produced the complaint before it ships.
- **A screen that opens a record never writes it.** F-329's whole cause. `calc(false)` on open, `calc(true)` on input, and a figure on record is never opened as a blank.
- **A store that can fail says so, loudly and permanently.** Read-back after write; a backup beside the record; the unreadable set aside before anything else is written; the warning at the top of the page, not in a hidden section.
- **An append-only table is read by its newest row per key, never by its sum** (F-324). And **two totals that agree prove nothing when they share an input** (F-326's false 373/373).
- **A Marg report name is read to the letter** — PURCHASE ITEM WISE and PURCHASE BILL ITEM WISE are different reports, and only the second carries the bill date per line.
- **The sheet is the entry.** Transcribing 373 items into a screen is not *"a few minutes"* however fast the screen; the pad the counters already filled is the count, and the server hands back only what is still to do. The Excel is a phase (D380) — but it is the phase that got the first count done.
- **A closed count is closed.** No sheet joins it, however it arrives; a fresh SHEET 1 starts a new count; the checker's *close as it stands* is the only way an abandoned count reaches the analysis.
- **The walk imports the file the kit ships, from the kit folder** (F-331). `SUMS.md5` green on the wrong bytes is the F-45 family in a kit.

---

## §2 · THE LIVE BACKLOG (snapshot; `OWNER_TODO_LIVE.md` is the live truth)

**⭐0 — the owner's own actions:** let the count finish on the page loop; a Marg backup (7 days old at the heartbeat); the 12 below-zero items = bills into Marg; the wall-card reprint (F-310) once the revision lands; the August advances on the ledger; one word on the S182 tiles; FINALISE September and August; the delete lists (`_to_delete_S224\` · `_S225\` · `_S226\` per drive root, the stale locks, the close transfer scratch).

**⭐1 — build next, in his order (the next layer, `S226_FINDING_REPORT_SPEC`):**
1. **The finding on screen** to the workbook's layout, reading a count and all its parts, the frozen *Read first* lines on top, Download PDF; explanations optional, in tranches (*"12 of 27 explained"*); on the portal tiles for him, Darpan and Amir (D379). A closed count (`stock_count_close.how`) is the unit it runs on; on-screen counts (sealed at send) as before.
2. **The item ledger** — from any difference: every purchase (vendor, bill, date, quantity), every sale bill, every credit note, Marg's closing figure day by day against ours, the bill scan once scanning starts.
3. **The unexplained-movement detector** on the ledger — a day where Marg's stock moved by an amount no document accounts for (the BIO D3 MAX shape).
4. **Fold the spot checks in** (D380): a spot check from Darpan's page or the medicine page is a count in the same ledger, marked *spot*, on the same finding pages; `stock_spot_check` retired into it.
5. **Retire the Excel** once the staff pages have earned it with real feedback — server-side autosave for the on-screen count first (its one weakness is the count living in one browser).
6. **The server-side computation** (`S226_EXPECTED_ON_SERVER`, ⭐1 item 2 of S225 — the gate is open: the loop proved 09:00:59 / 09:01:01 / 09:01:04).
7. **The S208 kit revision** (F-319 wording · F-323 the bounded token read; F-322 is answered by `S226_F322_SUBSET`) · the wall card revision (three pages → one; BILL ITEM WISE naming trap; *enter a bill the day it arrives*; the two-day note) · the joiner page's reset-password route (F-333) · the count page's Google Fonts dependency.
8. **Then, unchanged from S225:** Marg pending (SALT WISE signature · scan pre-fill) · the 17 bank-only stockists' numbers · the NEFT files · the loans PWA view · procedures (D373) · the S223 dawn specs in his order · the tracker parser fix, then the diagnosis upload.

**Parked by him:** the bank-name dropdown · attendance under the main domain. **The spot-count bridge is no longer parked — it is item 4 above (D380).**

**Standing holds:** NEFT — readiness work may proceed, nothing is SENT without his word · the hub's shape is not reopened · **the on-screen count path is on hold as the staff route** until the Excel phase has been evaluated.

---

## §3 · INSTALL DISCIPLINE — what S226 added

- **Every kit's walk runs at phone width (390px), taps every chip, drives the reload, the revisit and the failure path, and is run FROM the kit folder importing the kit's own files** (F-331). Sums are computed from that folder after the walk.
- **`python3 -B` / `PYTHONDONTWRITEBYTECODE=1` for every run in the mounted trees; `find -name __pycache__` before a publish — never `git`** (F-332; the gate refused twice this session, correctly).
- **A kit that changes the counting page ships the three regression walks** (search 34 · submit 30 · safestore 13) beside its own, and its evidence names all four.
- **A screen is read by a sub-agent before packaging**; its findings are fixed before the kit is committed (three this session).
- **One-line installs guard BOTH live pins they replace** (`stock_app.py` and the page), back each file up as `.bak_S226<kit>_<date>`, compile to `/tmp`, restart, print the sums, and roll back by themselves on failure.
- All of S225's, S224's and S223's rules stand.

---

## §4 · THE BOUNDARY

- **The publish is the owner's double-click**: `D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`
- **Patient data is not in this project. No number in the repository (F-185).** The count sheets carry item names, staff names and bill numbers only.
- **Nothing here ever writes to Marg, sends to a bank or a vendor, or leaves the server** (D325).
- Nothing live is rebuilt without his explicit OK; the manual workflow stays as fallback — **and this session it was the fallback that got the count done.**
- **ClickUp is parked (D17).**

---
*HANDOFF_RUNBOOK v158 · S226 close · 06-Sep-2026 14:00 IST.*
