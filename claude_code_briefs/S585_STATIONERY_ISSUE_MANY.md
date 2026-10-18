# S585_STATIONERY_ISSUE_MANY — brief v2 for the build runner (Agent SDK, the API credits)

*Written 18-Oct-2026 by the Scan App project (session 323). Kit **S585** and **D738** claimed on the board `_numbers`
(v491 -> v492) with its PLANNED line. Run by `D:\Downloads\_kbtools\agent_build\run_build.py S585_STATIONERY_ISSUE_MANY`
(after S582_XRAY_COSTS; the two kits touch different files).*

**The owner's words, 14:41-15:10 IST 18-Oct:** *"develop a system where multiple items can be issued on one screen"*;
*"in Shavez folder there is an Excel file named stationery where you can find what all was issued, so you can populate
that also, and we can edit it later on if needed"*; his mapping of that sheet (below). His opening stock was entered at
~14:5x IST 18-Oct on the owner's Stationery page as the FIRST COUNT of nine items (`stationery_count.opening=1`).

**v2 — READ `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S323\S585_BRIEF_R1.md` (md5 `706779ce…`, 2 BLOCKER · 9 CORRECTION · 10 NOTE) WHOLE BEFORE BUILDING. Every BLOCKER and CORRECTION there is binding and its replacement wording REPLACES the text below where they differ.** In short: **B1** the one-item screen keeps a FROZEN four-place list (Lab · Reception · Sanjeevni · Clinic) so switch OFF stays byte-identical and S568's walk I4F stays green; X-ray appears on the new screen and the owner's tables only; **B2 / C9** ORDER: this kit is built and installed AFTER S582_XRAY_COSTS — its read-only pins for `batteries.py` (and the new `xray_costs.py`) are S582's TO pins, read from `deploy_kits\S582_XRAY_COSTS\` (PIN_TO files / README); if that kit is absent, STOP and report; the installer checks this kit's own FROM byte of stationery.py strictly and the read-only files against the pins it records; **C1** the `stationery.many` ON/OFF control sits on the OWNER'S STATIONERY PAGE (the Switches card in sorting_desk.py refuses unknown switches — never edit sorting_desk.py); **C2** the two hard-coded four-place texts (the stock table header, issue()'s error) are handled; **C4** the data step: one transaction with its done-key, Row factory, rollback if any stock figure changes, rehearsed first on the snapshot copy, run after the health check, undone by voiding its rows; **C5** no new column — the void columns exist; voiding a line from before the latest count does not change the stock (say so on the page); **C6** copy S575's installer and its full earlier-walks list, plus S582's walk; **C7** a separate POST endpoint for the many-items save, refused when OFF, rollback on any error, Save disabled after the first tap; **C8** the mock-up is in the repository: `claude_code_briefs\S585_MOCKUP_Main.dc.html` — build to it.

**C3, decided by the Scan App chat:** Shavez's sheet carries no dates and the owner gave none. The seven history rows keep `day` = the item's opening-count day and `ts` = that count's ts − 1 s (stock unchanged), but they are NOT counted in any "Issued this month" figure or per-place total: the owner's page lists them in their own fold, **"Earlier issues — from Shavez's sheet (no date)"**, each voidable; recognise them by `by_whom = 'history (Shavez sheet)'`.

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** The kit goes in
`deploy_kits\S585_STATIONERY_ISSUE_MANY\`, the report in `claude_code_briefs\REPORT_S585.md`; then stop. Nothing live is
placed or restarted and no live row is written. CLAUDE.md's "install and publish without asking" is overridden.

## 1 · Read first
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md` (D704) — every rule binds.
- `claude_code_briefs\S568_STATIONERY_STOCK.md` (v2), its R1 and `REPORT_S568.md` (with FIX1), and the kit
  `deploy_kits\S568_STATIONERY_STOCK\` — **copy that kit's shape exactly** (patcher with counted edits, installer with
  FROM/TO pins, `.bak_S585_<from8>`, `ALREADY INSTALLED` on a second run, README with the undo line, walk, rehearse, the
  on-box walk on a COPY of the live database, the earlier kits' walks, a database backup before the restart, the build
  lock `/root/deploy/.claude_code_build.lock`, health `http://127.0.0.1:8030/healthz`).
- The owner's mock-up: canvas artifact `https://claude.ai/artifact/26QBCc6CYjSN8VhRZZsREY` (`project/Main.dc.html`):
  the screen is built to it. If the runner cannot read it, the description in §3.1 is the specification.

## 2 · Pins — read on the box first; a different byte = STOP and report
- **Edited:** `/root/assetapp/stationery.py` **`d11d718392782d4a7a8b9c233363a526`** (S568's TO) — the only code file.
- **Read only, never edited:** `asset_register.py` `c39c084eabf52daa0da9cc6720fc7aa7`, `sorting_desk.py`
  `110335eac5a9792ebe52620ee676a13c` (both drift 8, F-836), `batteries.py` `40eb8a916aee48ef5a49337d3c4cc81d`,
  `clinic_papers.py` `6db07c12a8ba5ab0123db2a5bee0fa7b`, `asset_machine.py` `7d4fdffce01a28fd7e5cc2c4f2aeeb74`,
  `scanner_widget.js` `10a8bb296944542278a06827c4d09c18`, the parent's `packs.py` `e46264b85f22563f3e0d8643597e1d58`.
  If S582 has been installed before this kit, `batteries.py` and the new `xray_costs.py` are S582's — still read only.
- **assets.db:** additive only — the keyed data step of §3.4, and at most one new column if §3.3 needs it.

## 3 · What to build (all in stationery.py)
1. **Many items on one screen** — the staff page `/scanapp/stationery/diya` (Roman Hinglish, as today), when the new
   setting **`stationery.many`** is ON:
   - "1 · Kisko diya?" — one choice for the whole save: Lab · Reception · Sanjeevni · Clinic · **X-ray** (big buttons,
     ≥44 px).
   - "2 · Kya aur kitna diya?" — EVERY active item, one row each: its name, "shelf pe <stock> <unit>", a **−** button, the
     number, a **+** button (and the number box typeable for big quantities). Rows with a number are highlighted.
   - A line naming what will be saved, and ONE **Save karo (N)** button. Saving writes one issue per item with a number,
     through the existing `issue()` rules, in ONE transaction (all or none), then shows "Save ho gaya ✓ — <what was
     saved>" and clears the screen. No confirmation tap; a quantity above the shelf stock is saved and flagged on the
     owner's page as today. Nothing chosen, or no Kisko: the button stays grey and nothing is sent.
   - The **Ginti** (count) section stays exactly as it is, below.
   - `stationery.many` OFF (the default, absent = OFF): the page is exactly today's one-item screen. ON: the new screen;
     the one-item screen stays reachable at `/scanapp/stationery/diya?one=1` (the manual fallback). The switch is a row on
     the owner's Switches card the way `Stationery diya for managers` is (read how stationery.py exposes that switch and
     add a sibling; if the Switches card lives only in `asset_register.py`, put the ON/OFF control on the owner's
     Stationery page instead and say so — never edit `asset_register.py`).
   - Readable on a phone (390 px wide) and at 1366 × 768, no sideways scroll; under 2 s and 100 KB for the staff page.
2. **X-ray as a place** — `PLACES` gains `("xray", "X-ray")`; the owner's stock table, "This month's issues" and every
   place list show it. (The X-ray expenses page of S582 does NOT count issued stationery in this round — say so in the
   report; it counts purchase papers marked for X-ray.)
3. **Correct an issue later** — on the owner's Stationery page, each line of "This month's issues" (and a "show all
   issues" fold for older months) gets an owner-only **Void** (`stationery_move.voided_at / voided_by`, audited in
   `desk_audit` the app's way); a voided line is shown struck through and leaves the stock arithmetic (`stock_book`
   already ignores voided moves). A history line (§3.4) is marked "from Shavez's sheet". Managers see no Void.
4. **The history — a keyed data step in the installer, idempotent** (a settings key `stationery.history_s585` set when
   done; a second run writes nothing). Seven `stationery_move` rows from Shavez's Drive sheet `STATIONARY.xlsx`, by the
   owner's mapping of 15:10 IST 18-Oct, items found by their EXACT live names:

   | item (live name) | qty | place |
   |---|---|---|
   | Register 72 pages | 6 | reception (the OPD register) |
   | Register 104 pages | 6 | reception (the lab register kept at reception) |
   | Register 192 pages | 3 | lab (the lab register) |
   | Register 104 pages | 6 | lab (the A/C register) |
   | Small notebook (copy) | 2 | lab (the expense copy) |
   | Notebook (copy) 72 pages | 6 | sanjeevni (Medical's daily detail) |
   | Small notebook (copy) | 2 | xray |

   Each row: `day` = the day of that item's OPENING count; `ts` = that opening count's `ts` minus 1 second (strictly
   before it, so `stock_book` does not subtract it — the opening stock he gave stands exactly); `stock_before` NULL;
   `by_whom` = `history (Shavez sheet)`. An item that is absent, or has NO opening count, is skipped with one printed
   line (never written without a count after it). The installer prints the seven lines it wrote and the nine stock
   figures before and after — they must be equal.

## 4 · Never
- edit any file but `stationery.py`; change the Ginti section, the owner's count, the desk's stationery panel, or
  what stock a paper adds;
- install the new screen switched ON (`stationery.many` absent = OFF);
- write a history row that changes a stock figure;
- put a number of any kind into the repository (F-185); print a secret.

## 5 · The walk (made-up rows, a schema copy) — each check named, each with a control RED on the FROM bytes
switch OFF = byte-identical one-item screen · switch ON shows every active item with its stock · one save of three
items writes three moves in one transaction (a forced failure on the third writes none) · no Kisko / no number = nothing
sent · X-ray accepted as a place and shown on the owner's table · Void by the owner leaves the stock arithmetic, a
manager has no Void and a forged POST is refused · the data step writes 7 rows before the opening counts, the nine
stocks unchanged, a second run writes nothing, an item without an opening count is skipped · `?one=1` still works · the
staff page under 100 KB · 390 px and 1366 × 768 no sideways scroll (headless) · the installer refuses a wrong FROM byte
and says ALREADY INSTALLED on a second run.

## 6 · The installer and the report
One server line: `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S585_STATIONERY_ISSUE_MANY/install_s585.sh`
— under the build lock; pins checked; backups; the data step; restarts **assetapp only**; reads back the health line and
the md5; prints `S585_STATIONERY_ISSUE_MANY: DONE`, the switch's place, and the undo line. Report
`claude_code_briefs\REPORT_S585.md`: pins, counted edits, walk counts, rehearsal, the data step's printout on the
rehearsal database, seen-not-touched, the cost line.
