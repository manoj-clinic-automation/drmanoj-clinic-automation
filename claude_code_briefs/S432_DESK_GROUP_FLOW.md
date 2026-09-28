# Claude Code brief — S432_DESK_GROUP_FLOW (the Loss desk made fast, and closed group by group the owner's way)

Written 28-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S432 · fault F-651** (claimed on the System Board). Runs AFTER
S431 (live 27-Sep 22:0x IST). **Owner-facing English; Sanjeevni-owned** (loss_piles.py, stock_loss.html, stock_app.py, stock_watch.py, the
06:30 job). No parent file. Restart `clinic-finance` only. Count #1 is closed; this kit serves count #2 onward and any line moved before it —
nothing in count #1's frozen run changes.

## 1 · The owner's words (27-Sep 13:2x IST, on the live desk)
"I select a group — a button to tick all — all ticked; I individually then untick some, and on unticking a change-pile menu appears: pile
changed, or the item stays in the same pile; the other ticked ones disappear on clicking the Clear-pile button." And: "The page opens real slow,
and each tick etc. takes a lot of time too."

## 2 · What exists and why it is slow (read live; REPORT_S427/S428/S430)
`loss_piles.classify()` runs on every read of `/api/loss/<cid>/piles` and after every `/pile/move|accept|recount|setting`: `allowance_for(item)`
reads the spine's sales per item (one query per line), the sales-after-count test runs per line, `stock_watch` runs the trace on every Big-loss
line "when the owner reads the desk, once per item per 30 days, at most 40 a read" and scores the watch list per read; the page then
re-renders the whole desk. Every tap = full recompute + full redraw.

## 3 · The build

### 3.1 Fast (F-651)
- **Piles computed once, stored:** a `stock_pile_cache` table keyed (count_id, diff_id) holding the classification, the group, the allowance,
  the price and the why, with a `stamp` (settings version + shelf-fix version + moves version + spine build time). The read serves the cache;
  a stale stamp recomputes **only the lines whose inputs changed** (a move, an accept-back, a recount, a new sales-test hit) or everything when
  a setting or the spine build changes — and that recompute runs once, in one transaction, with the spine sales fetched in ONE query for
  all items (not one per line).
- **The traces and the watch scoring leave the read path**: they run in the 06:30 job (`stock_watch` cron) and on demand from a "Refresh
  watch" button; the desk shows the stored results with their time. A Big-loss trace is opened by the close (once), not by reading.
- **The page updates in place:** a tick, a move, an accept-back changes that row and the four pile totals from the small JSON the door
  returns; no full redraw, no full re-fetch. Loading shows the totals first, the piles' lines lazily (each pile's list on open).
- Target, measured in the walk on the real count #1 copy: the piles JSON under 1 s and a move under 0.5 s on the box (print the numbers).

### 3.2 The close, group by group (the owner's flow)
Above the piles, a **Group** selector: *Within allowance · Small real gap · Old stock · Big losses · Clinic consumption · Owner's use · All*.
Picking one shows a compact list (name · short in strips/tabs · value · the one-line why) with a **Tick all** button; ticks are local only.
- **Untick a line** → a pile menu opens on that line (With me / Write off / Big losses / Consumption / Owner's use / system's choice);
  choosing writes the move (audited "owner") and the line leaves this list for its new pile; closing the menu leaves the line where it is,
  unticked. Unticking never writes.
- **Clear this group (N ticked)** → the ticked lines are written off NOW as that group (WRITE_OFF + closed, one `stock_writeoff_run` per clear,
  Amir's vouchers in rounds of ≤ `stock.voucher_batch`, audited); they disappear; the unticked stay open in their pile. Armed + 10-s confirm
  as the close is today. With-me lines are never in a group list.
- **The last clear closes the count**: when no open line remains outside With me, the count closes by itself — the staff block freezes from
  the union of the clears (one block, the same wording as S427), the S428 full-count points are written once, the leakage period line
  appears. The single **Close the count** button stays for whoever prefers one tap; it is the same code path (all groups at once).
- Every clear and the auto-close are shown in the record and the PDF as separate runs with their times.

### 3.4 FIRST, before 3.1 — the S431 statement's negative-Marg lines (found by the chat on the live page, 28-Sep 05:2x IST)
Marg holds a NEGATIVE stock on some items (the 11 known since S270: PRIME CAST 4"/5", PRIME PAD 4"/6", BELL CAST 5, ALCOXIB 120, DECA
INSTABOLIN, FLUPIVAMP 100, NEWTEL 40, GLI-ME SR1, TRAMEF P, CERVICAL COLLAR SOFT HOPE L …). The statement prints the Marg column through
`qty_words`, which has no sign, so "-24 pcs" reads "24 pcs" and the row looks impossible (Marg 24 · physical 0 · excess 24); and it values
that "excess" at selling price — the Consumables' Rs 88,650 excess is exactly PRIME CAST 4"/5" (Marg -24 / -45, shelf 0), a bookkeeping
negative, not goods; the Medicines' excess carries BELL CAST 5 (Rs 18,200), ALCOXIB, NEWTEL and the rest the same way. Fix: `qty_words`
gains the sign ("-24 pcs", Hindi "-24 nag"); a negative-Marg line is tagged **"Marg negative -- book correction, no goods"**, its quantity
to correct shown as such, and it is EXCLUDED from the section's excess money and counted in its own line under the section totals
("Marg negative: N lines, X pcs to correct"); the section and count totals, the PDF and the Excel follow. Also: BELL CAST 5 sits in
Medicines — move it to Consumables in `stock_item_section` by the seed (audited "S432, cast material"), and say in the report which other
lines the section map has in a section their name contradicts (a plain list, no other change). Re-state S431's walk assertions on the
new totals; every other S431 figure stays.

### 3.3 Settings — none new; `stock.voucher_batch` applies per clear.

## 4 · Pins — read live after S431: loss_piles.py 3720b2e1 (v2.1 → v2.2), stock_loss.html (S431's TO — read live), stock_app.py 2a95e254,
stock_watch.py 6a51e47b (v1.1 → v1.2: trace/watch out of the read path, into the job + a refresh door), stock_hub.html 38e0537c (only if a
label changes). Spine read-only. No parent file. Restart `clinic-finance` only.

## 5 · Walk (scratch copy of the live database + spine; crafted count W432 with ~150 lines)
Cache: first read builds it, second read serves it unchanged (stamp equal), a move recomputes one line only, a setting change recomputes all,
a spine rebuild stamp recomputes all; timings printed and under target · group list: Tick all ticks, untick opens the menu and writes
nothing; a move from the menu re-piles and drops the line from the list; Clear writes off exactly the ticked lines with one run and the
vouchers, the unticked stay open; Clear with nothing ticked refused; the 10-s arm; the last clear closes the count, one staff block, points
once, the period line; Close the count still works as one tap; count #1's frozen run untouched (md5 equal before/after) · traces/watch not
run by a read (a counter proves it), run by the job and by Refresh · bhati/darpan/shavez refused · S427 82/82, S428 73/73, S430 42/42, S431
56/56 re-run green (assertions adjusted only where this brief changes behaviour, each named) · negative control.

## 6 · Done means
Kit `deploy_kits\S432_DESK_GROUP_FLOW\` · installed · published · `claude_code_briefs\REPORT_S432.md` — owner lines first: the measured
open time and tick time before and after on the box, the group flow in four lines as he will use it at count #2; ending with
`https://followup.dr-manoj.in/finance/stock/page/loss?count=1`.
