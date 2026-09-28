# S432_DESK_GROUP_FLOW — the Loss desk made fast, and closed group by group the owner's way (F-651); the statement's Marg-negative lines

**Sanjeevni project · session 283 · 28-Sep-2026 · brief `claude_code_briefs/S432_DESK_GROUP_FLOW.md` · runs after S431.** Count #1 is closed;
this kit serves count #2 onward and any line moved before it — nothing in count #1's frozen run changes.

## What the owner said (27-Sep 13:2x IST, on the live desk)
"I select a group — a button to tick all — all ticked; I individually then untick some, and on unticking a change-pile menu appears: pile
changed, or the item stays in the same pile; the other ticked ones disappear on clicking the Clear-pile button." And: "The page opens real
slow, and each tick etc. takes a lot of time too."

## What was slow (measured on the box, 28-Sep 05:2x IST, a scratch copy, the test client)
A desk read took **6.5 s**: the S227 report composer `_pad_report_data` (2.8 s — one item-life walk per differing line) ran TWICE per read
(inside the sales-after-count test, then for the desk itself), and the watch scoring (`owner_view`, 0.9 s) ran on every read. `classify()`
itself takes 10 ms. Every tap paid the same again and then the page re-fetched everything (a move ≈ 2.2 s + a 6.5 s re-read).

## What was built
**3.1 Fast (F-651)** — `loss_piles.py` v2.2: `stock_pile_cache` (the classified lines of a count, keyed `(count_id, item)` with the line's
`diff_id` beside it — the item is the key every other desk table uses) + `stock_pile_cache_meta` (a STAMP of every input: the stock.*
settings, the spine file's build, the count's rows, the prices, the section map, the snapshot, the close; and the moves / shelf fixes /
words / sales tests / runs / shares by their newest id). `cached()` serves the rows; a stale stamp on a per-line part recomputes ONLY the
touched lines from their stored count-day inputs (`refresh_items`: the swap layer is stored, the word and the shelf fix are laid on again,
`_classify_one` runs the whole rule); a change of a setting / the spine build / a price / a count row rebuilds everything once, in one
transaction (`rebuild`: the report once, the sales test on it — a hit re-reads the report once — classify with `Spine.prefetch`: the spine's
sales for every item in ONE query). The sales-after-count test runs inside the full build (a spine rebuild changes the stamp), not on every
read. `desk_cached()` (`?lite=1`: totals, headers, close, block; `?pile=<key>`: one pile's lines; `?rebuild=1`). Taps (`move_patch`,
`accept_patch`, `_run`) recompute their lines at once and return a **patch** (the changed lines + the totals + the close + the group counts).
`stock_watch.py` v1.2: the watch is scored and STORED (`stock_watch_view`) by the 06:30 job and by `refresh_owner_view` ("Refresh watch");
the desk shows `stored_owner_view` with its time (built once, without traces, if nothing is stored yet). A Big-loss trace is opened by the
close and by a clear (`trace_big_losses` from `stock_app`), never by reading. `stock_loss.html`: the light read first, then the lines; the
piles are collapsed cards drawn when opened; a tick, a move, an accept-back, a clear or a close patch the page in place (`applyPatch`) — no
full redraw, no re-fetch; the cache's times are printed under the tally.

**3.2 The close, group by group** — above the piles: the group selector (Within the allowance · Small real gap · Old stock · Big losses ·
Clinic consumption · Owner's use · All), a compact list (name · short · value · why), **Tick all** / Untick all; ticks are local. An
**untick** opens the pile menu on that line (With me / Write off / Big losses / Consumption / Owner's use / back to the system's choice /
leave it here): a choice writes the move through the S418 door (audited by the owner) and the line leaves the list for its new pile;
closing the menu leaves it where it is, unticked. **Clear this group (N ticked)** → `POST /api/loss/<cid>/pile/clear {group, items}` arms
(10 s), `{token}` confirms: exactly the ticked lines → WRITE_OFF + closed, ONE `stock_writeoff_run` (kind `clear:<group>`), Amir's vouchers
in rounds of ≤ `stock.voucher_batch` (owner's use in its own round), audited; the unticked stay open. Nothing ticked / a wrong group / a
line no longer in the group → refused. **The last clear closes the count by itself**: when no open line remains outside With me, ONE staff
block is frozen from the UNION of every run since the previous block (how `auto`, the S427 wording), the S428 full-count points are written
once, the leakage period line follows (`count_periods`). **Close the count** stays: the same code path (`_run`, kind `close`, its block also
unions the clears before it). The record and the PDF list every run with its kind ("Clear this group — Big losses" / "Close the count") and
every close of the count with how it came (`stock_staff_block.how`).

**3.4 FIRST — the statement's negative-Marg lines** — `qty_words.py` v1.1: a negative quantity carries its minus ("-24 pcs", Hindi
"-24 nag"; every caller of a shortage / gap passes the absolute figure). `stock_statement.py` v1.1 (anchored): a line whose Marg balance is
below zero is tagged **"Marg negative -- book correction, no goods: N to correct"**, `neg_marg` / `correct_units` / `correct_text`, no
shortage, no excess, **no excess money**, not 'unpriced'; the section totals carry `neg_lines` / `neg_items` / `neg_text` and the overall
`neg_lines`; the PDF (a "Marg negative" line under each section's totals, the head line), the XLSX (a "Marg negative" column on Totals, the
row flagged) and the page (the totals' cell, the row's "N pcs to correct" tag, the section line) follow. `seed_s432.py`: **BELL CAST 5 →
Consumables** in `stock_item_section` (source owner, by "S432, cast material", audited).

**Calls made where the brief left room** (each said in the report): the cache is keyed by `(count_id, item)` with `diff_id` as a column
and an index (the item is the key of every other desk table; a crafted or re-imported line may have no diff row yet); the very first read
after the install builds the stored watch once (without traces) so the card is never empty; the sales test moved into the full build (its
only new input is the spine); the stamp reads the spine file's mtime + size, not its rows; a "Clear" on *All* is the one-tap close through
the clear door; the block of a tap close after clears unions the clears (one block, as the brief asks of the auto-close).

## Pins (FROM read live 28-Sep-2026 05:28 IST after S431 → TO; the whole files are the kit's, the three patched files are built by `make_s432.py`)
| file | FROM | TO |
|---|---|---|
| /root/finance/loss_piles.py (whole, v2.1 → v2.2) | 3720b2e1261fd83932b07e2a319a0687 | see SUMS.md5 |
| /root/finance/stock_watch.py (whole, v1.1 → v1.2) | 6a51e47b891b717fbb51b030d4a29f02 | see SUMS.md5 |
| /root/finance/stock_loss.html (whole) | ab60c341336c8c897699db18e830211d | see SUMS.md5 |
| /root/finance/qty_words.py (whole, v1.0 → v1.1) | 1e67a3e35ce815798ef6ebd606e5b972 | see SUMS.md5 |
| /root/finance/stock_app.py (anchored) | 2a95e2543330b3efbdb0dc0106892bea | see the installer's TO |
| /root/finance/stock_statement.py (anchored, v1.0 → v1.1) | 85ec7619d79c7a9f311f7bed91eeabae | see the installer's TO |
| /root/finance/stock_statement.html (anchored) | 175f4654a88e6bb81d0fd724be6d93c4 | see the installer's TO |

Pinned, read, NOT changed: `stock_hub.html` 38e0537c (no label changes). Read only: `section_map.py` 9bf9b98f, `stockmatch.py` df5501ea,
`pad_receipt.py`, `padwriter.py`, the spine. Restarts `clinic-finance` only; the 06:30 cron line is unchanged (the job now stores the watch).
Data: the seed (BELL CAST 5, the tables and two guarded columns `stock_writeoff_run.kind` / `stock_staff_block.how`, the warm-up).

## Proof
`walk_s432.py` — the REAL patched app over SCRATCH copies of the live database and the spine: count #1 with three crafted W432 lines (the
first read builds the cache — the report composed, the sales test once closing W432 SOLD TAB, no trace; the second read served from the
cache with counters 0/0/0/0 and its time printed against the 1 s target; the light read; one pile's lines), the stamps (a move recomputes ONE
line and answers with the patch under 0.5 s; a stale moves part recomputes only the touched line; a setting → everything once; a spine
rebuild → everything and the sales test once; the hub's totals = the desk's), the watch (two reads open no trace and score nothing;
Refresh watch traces the cached Big-loss line once and stores; the cron job stores), the GROUP FLOW on the crafted count W432 (#2, ~150
lines of count #1's sheet with fresh figures: Tick all / the untick menu's move leaves the list and writes no word / Clear refused with
nothing ticked, an unknown group, a line of another group / the 10-s arm / a moved line refuses the confirm / Clear writes off exactly the
ticked lines, one run kind clear:allowance, the vouchers in batches, the unticked stay open, the patch, the record; every group cleared in
turn — the LAST clear closes the count by itself: ONE block how auto from the union, the S428 points once, the period line 06-Sep → 20-Sep,
the Big-loss trace once, the audit, Close refused on the empty desk, Amir's rounds, the Hindi block on Stock milaan, the record PDF), Close
the count still one tap on count #1 (kind close, how tap, the trace once), count #1's frozen run untouched (md5 equal), 3.4 (PRIME CAST
4"/5" and BELL CAST 5 in Consumables as Marg-negative lines, "-24 pcs", 24 pcs to correct, Consumables' excess Rs 0 on 0 lines, Medicines'
8 and Orthotics' 1, the overall 12, the PDF, the XLSX, the page, qty_words' sign), the gates, the page's strings, the word gate.
**Negative control:** the same scenario on the box as it is goes red (no cache — the report on every read, counters > 0; no clear door;
no Marg-negative rule; no sign). Then **S430's** walk, **S427's** (the S430 copy, unchanged), **S428's** (one named adjustment: Refresh
watch before the traces are looked for), **S431's** (two named adjustments: the Marg-negative lines) and **S404's** walks re-run on the
patched files, each against its own pre-kit control. **S428's** and **S404's** re-runs carry one calendar adjustment each (both walks were
written and run on Sunday 27-Sep-2026 and hardcode that week: S428's "last Sunday" is yesterday on a Monday run and its crafted bills fall
outside the trace window; S404's crafted verification exports are dated 27..30-Sep, and an export dated before the tick day counts for
nothing — both go red on the live files as they are, nothing to do with this kit). `figures_s432.py` prints the measured times and the
statement's figures for the report.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S432_DESK_GROUP_FLOW/install_S432_DESK_GROUP_FLOW.sh
```
Undo: put back the seven `.bak_S432_<from8>` files, `systemctl restart clinic-finance`, healthz 200. The cache tables and the stored watch
are derived data (harmless to an older loss_piles); the two added columns are ignored by it; BELL CAST 5's section is the owner's word.
