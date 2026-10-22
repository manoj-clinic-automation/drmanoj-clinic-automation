# S623_STATIONERY_CHALLAN_HISTORY — brief v2 for the build runner (Agent SDK, the API credits)

*Written 22-Oct-2026 by the Scan App project (session 323). Kit **S623** and **D756** claimed on the board `_numbers`
(v588 -> v589). Run by `D:\Downloads\_kbtools\agent_build\run_build.py S623_STATIONERY_CHALLAN_HISTORY`.*

**The owner's words:** board note 22-Oct 06:31 IST *"scanapp - populate all entries that are possible from the variety
challans and shavez excel files"*; his rulings 12:09 IST on the lines read by eye (below). His opening stock was entered
18-Oct ~14:5x IST as the FIRST COUNT of nine items; S585 entered Shavez's seven past issues one second before those counts.

**v2 — READ `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S323\S623_BRIEF_R1.md` (md5 `8cfeea39…`, 3 BLOCKER · 7 CORRECTION · 8 NOTE) WHOLE BEFORE BUILDING. Every BLOCKER and CORRECTION there is binding and its replacement wording REPLACES the text below where they differ.** In short: **B1** `ts` and the date are PER PAPER (save_lines gives a paper's lines its earliest stamp, voided rows included): each of the six papers gets ONE stamp = its challan date 12:00 IST, and B-0013's two existing lines are rewritten to that same stamp; every challan date is before the 18-Oct counts, so the nine counted stocks stand and October's 'Received this month' shows only B-0109, B-0114, B-0133, B-0163; **B2** each new line takes the line number of the paper's own reading, so the desk never offers the real line again for a double save (panel; sorting_desk.py:1748, :3167); **B3** every row the step writes carries a marker (by_whom = 'history (Variety challans, S623)' or the column the table has) and the kit ships `--undo`, which voids the new rows and restores B-0013's two old lines exactly; **C1** the step is a kit script with direct inserts (save_lines cannot take a chosen time); ALREADY INSTALLED = the done-key is set; no restart unless code changed; **C2** the four uncounted items are checked by their MOVE (A4 +21, File folder +3, X-ray envelope +500, Token −99), not by fixed totals; **C3** the token fix voids the one existing row (found exactly once) and inserts a new line of 1 — never an in-place edit; **C4** before writing a paper, check it is in Stationery & packaging (paper_counts) — else skip that paper and print it; **C5** each line takes its item's own unit; **C6** a missing or retired item skips only its row; **C7** the count is 13 new lines plus the token fix. Gates the installer reads on the box (R1 could not see the live database): B-0013's existing lines, each paper's group and status, the live item names, the current stocks.

**THIS RUN BUILDS, WALKS AND REHEARSES. IT DOES NOT INSTALL AND DOES NOT PUBLISH.** Kit in
`deploy_kits\S623_STATIONERY_CHALLAN_HISTORY\`, report `claude_code_briefs\REPORT_S623.md`; then stop. Nothing live is
placed or restarted, no live row written. CLAUDE.md's "install and publish without asking" is overridden.

## 1 · Read first
- `deploy_kits\KB_canon_all\BUILD_NORM_v1.md` (D704) — every rule binds.
- `deploy_kits\S585_STATIONERY_ISSUE_MANY\` and `claude_code_briefs\REPORT_S585.md` — **copy that kit's shape**, above all
  its keyed data step (done-key, one transaction, Row factory, rollback if a guarded stock figure moves, rehearsed on the
  snapshot copy first, run after the health check, undone by voiding/removing its own rows only), its installer (build
  lock `/root/deploy/.claude_code_build.lock`, health `http://127.0.0.1:8030/healthz`, DB backup, on-box walk on a COPY,
  the earlier kits' walks), and S568's stationery code: `stationery_line` (how a desk-matched challan line is stored:
  `bill_id`, `bill_created_at`, item, qty, unit, rate, `ts`, ...), `_counted_sql` (which lines count into stock), the
  desk panel (`save_lines`, `panel`, `read_lines`), `stock_book`, `rate_flag`.

## 2 · Pins — read on the box first; a different byte = STOP
- `/root/assetapp/stationery.py` **`18268ff04b37af8143be1e3395ec5854`** (S585's TO). Prefer NO code change: the history is
  data written exactly as the desk's own `save_lines` would write it (through its functions where possible). If a code
  change is truly needed, it is counted, walked, and named in the report.
- Read only: `asset_register.py`, `sorting_desk.py`, `batteries.py` `775471e6…`, `xray_costs.py` `22e59f5a…`,
  `clinic_papers.py`. **Never touch** `scanner_widget.js`, `asset_register.py`, `claude_reader.py`, `claude_reread.py`
  (the Sanjeevni chat's S618 PLANNED line stands on them).

## 3 · The data step (in the installer, idempotent, done-key `stationery.history_s623`)
Match these challan lines to these items (items by their EXACT live names — read them on the box; the two copy items were
renamed 22-Oct to the names below; if a name is absent, STOP that row and print it):

| paper | challan date | line as written | live item | qty | rate |
|---|---|---|---|---|---|
| B-0003 | 24-08-2026 | A4 Ream 75gsm | A4 paper (75 gsm) | 1 | — |
| B-0013 | 15-09-2026 | File DC-217 | File folder DC-217 | 1 | 240 |
| B-0013 | 15-09-2026 | Ring File RBU-400 | Ring file RBU-400 | 1 | 340 — **already matched; leave as it is** |
| B-0013 | 15-09-2026 | A4 long notebook 192p ("Ay lam N.Bom 192p") | Register 192 pages | 3 | — |
| B-0013 | 15-09-2026 | ITC Copy 72p | Copy — Classmate 72 pages (24 x 18 cm) | 6 | 40 |
| B-0013 | 15-09-2026 | Copy Anmol ("Copy Anvl/Annl") | Small copy — Anmol 96 pages (24 x 18 cm) | 4 | 40 |
| B-0013 | 15-09-2026 | Register 17x27 72p A4 | Register 72 pages | 6 | — |
| B-0013 | 15-09-2026 | Register 104 Anmol A4 | Register 104 pages | 12 | — |
| B-0013 | 15-09-2026 | Estimate Book NK Pathology | **not matched** (the lab's printed stationery) | — | — |
| B-0013 | 15-09-2026 | Token (R) Plain 100 | Token, plain (unit packet of 100) | **correct the existing line to 1** | 120 |
| B-0109 | 01-10-2026 | Register 192P Anmol | Register 192 pages | 6 | — |
| B-0109 | 01-10-2026 | Register 104 pag Anmol | Register 104 pages | 2 | — |
| B-0109 | 01-10-2026 | My Clear Bag | Clear bag (premium) | 2 | 44 |
| B-0114 | 03-10-2026 | Folder DC-217 | File folder DC-217 | 2 | 240 |
| B-0133 | 07-10-2026 | A4 Ream (Star) | A4 paper (75 gsm) | 20 | — |
| B-0163 | 14-10-2026 | Envelope 8.5 x 10.5 X-Ray | X-ray envelope 8.5 x 10.5 | 500 | — |

**The time rule (stock):** `stock_book` = last count + received after it − issued after it, by `ts`.
- An item that HAS an opening count (the nine): each of its new lines gets `ts` strictly BEFORE that item's first count
  (and before S585's history issues for it is not required); the nine stock figures must be exactly unchanged —
  Register 192 pages 12, Register 104 pages 14, Register 72 pages 6, Copy — Classmate 72 pages 6, Small copy — Anmol 96
  pages 4, Clear bag (economy) 5, Clear bag (premium) 3, Ring file RBU-400 1, Cheque book folder 2. Rollback otherwise.
- An item WITHOUT a count (A4 paper, File folder DC-217, X-ray envelope, Token): its lines get `ts` = its challan date
  12:00 IST; their stock becomes the received total — A4 paper 21, File folder DC-217 3, X-ray envelope 500, Token 1 —
  the installer prints these four before / after.
- Each line's `day`/date fields (if any) = its challan date. Where `ts` per line is the paper's "first stationery save",
  keep the paper's existing lines (B-0013 ring file, token) and give the new lines the rule above; say in the report how
  the desk then shows each paper (matched lines, 'into the stock').
- The papers themselves are NOT changed (no bills row written except what `save_lines` itself writes for a match; D664).

## 4 · Never
- change a counted stock figure; touch any file but `stationery.py` (and that only if unavoidable); write anything for a
  pharmacy paper; put a number of any kind into the repository (F-185 — the stamps and quantities in this brief are the
  owner's records, kept as data in the installer like S585's seven rows); print a secret.

## 5 · The walk (made-up rows on a schema copy, plus the snapshot copy) — each check with a control RED on the FROM state
the 14 lines written and matched on the right papers · the token line corrected to 1 · the nine counted stocks unchanged ·
the four uncounted stocks as above · a second run writes nothing · an absent item name stops only its row · the desk panel
of each paper shows its lines matched · the owner's Stationery page renders (received this month = only October's lines,
by challan date) · S585's, S568's, S582's walks still green (on /tmp copies as their reports say) · installer refuses a
wrong FROM byte, says ALREADY INSTALLED on a second run.

## 6 · Installer and report
One server line: `cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S623_STATIONERY_CHALLAN_HISTORY/install_s623.sh`
— prints each line written, the 13 stock figures before / after, `S623_STATIONERY_CHALLAN_HISTORY: DONE`, and the undo
line. Restart assetapp only if code changed. Report `claude_code_briefs\REPORT_S623.md` with the cost line.
