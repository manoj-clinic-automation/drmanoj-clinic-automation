# REPORT S431_COUNT_STATEMENT — the count of 06-09-2026 as one statement, section by section (27-Sep-2026, installed 21:58 IST)

## For the owner
- **The statement is live:** https://followup.dr-manoj.in/finance/stock/page/statement?count=1 — the whole count of 6th September in three
  sections, **Medicines · Consumables · Orthotics**, every one of the 373 counted lines once (the 186 lines that matched sit folded under
  "Matched" in each section). Each line shows Marg stock, physical stock, the confirmed swap, the shortage or excess after swaps, its value at
  **selling price** (with where the price came from), and what became of it. Buttons at the top give the **PDF** and **Excel**; "Freeze this
  statement" keeps a dated copy the hub then links to. Bhawna can read it; staff cannot.
- **Medicines** — 285 lines, 163 differ: short **₹1,06,780.26** on 134 lines, excess **₹49,426.82** on 29 lines, net **₹57,353.44**; 1 line
  without a price (CORTIRI). **Consumables** — 19 lines, 9 differ: short **₹6,109** on 7 lines, excess **₹88,650** on 2 lines, net **−₹82,541**.
  **Orthotics** — 69 lines, 15 differ: short **₹6,860** on 13 lines, excess **₹1,349.69** on 2 lines, net **₹5,510.31**; 2 lines without a price
  (FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S — name their prices and they will value themselves).
- **The orthotic block** (top of its section, live from Darpan's Stock milaan): 2 lines still open with Darpan (the two unpriced items above),
  **10 answered by Darpan but awaiting your word** (Ankle Binder Bamboo L and M, Arm Sling XL, Cervical Collar Soft Hope L, Dyna Wrist Brace,
  Finger Cot M and M Tynor, L S Belt XXX, Rib Belt S Tynor, Shoulder Immobiliser M), 18 lines not yet on a voucher, 22 of 23 renames not yet
  verified. The statement only shows this; the deciding stays on the hub and Stock milaan.
- The shortage figures here are the **count-day shortage at selling price** — what the shelf lacked on 6th September after the confirmed swaps —
  so they are larger than the close's write-off (₹64,678.78 at MRP on 136 lines, which you closed at 12:58 today): the six lines you took back
  into store and the lines you explained are still shown as short on the count day, with "back in store" / your word written beside them.
- The old count report still opens, now reading "Closed … — see the statement"; the hub's first card carries the statement above the full report.

## For the chat
**Kit** `deploy_kits/S431_COUNT_STATEMENT/` (KIT_ID `kit id S431_COUNT_STATEMENT`). Installed on srv1746119 from `/tmp/s431kit` (byte-identical
to the repository kit — SUMS.md5 checked both sides) with `KITS=/root/deploy/repo/deploy_kits`; install log `/tmp/s431_install.log`; started 21:42:14,
DONE 21:58:50 IST (read from the log / `date`). Build lock taken 21:41 IST (`/root/deploy/.claude_code_build.lock/owner` = S431_COUNT_STATEMENT),
released after this report.

**Decision the brief left open:** a new module `stock_statement.py` (v1.0) mounted the S418 way — `stock_app.py` imports it defensively
(`STOCK_STATEMENT_OK`) and its routes delegate — rather than routes inside stock_app. The "doctor" role is the user `bhawna` (the medical unit's
viewer beside the owner), `stock_statement.DOCTORS`; widen it when the chat names another.

### Live files — FROM → TO, md5 read back on the box after placing
| file | FROM (pin in the brief, re-read live 20:51) | TO (built from the live bytes, read back 21:58) |
|---|---|---|
| /root/finance/stock_app.py | 0e0fc043c4bbae75c6f1fc8149547cb7 | 2a95e2543330b3efbdb0dc0106892bea |
| /root/finance/stock_hub.html | 74ea06997b900e9f55c47dca473a9232 | 38e0537cd7d1eb3fb40d1a5a0b7df0e5 |
| /root/finance/stock_report.html | bd750dc8a32c0ed6baf66f48d7114c90 | 610169c04c4de54724fb4e754d572eab |
| /root/finance/stock_statement.py (NEW) | — (gated: did not exist) | 85ec7619d79c7a9f311f7bed91eeabae |
| /root/finance/stock_statement.html (NEW) | — (gated: did not exist) | 175f4654a88e6bb81d0fd724be6d93c4 |

Read only, untouched: `section_map.py` 9bf9b98f, `stockmatch.py` df5501ea, `loss_piles.py` 3720b2e1, `qty_words.py`, `pad_receipt.py`, `padwriter.py`,
`finance_app.py`. `stock_app.py` edits (make_s431.py, every anchor exactly once): the S431 import block after the S428 import block; `statement`
in `_pad_report_data`'s links; `**_statement_links_safe(con, root)` in the hub's links; the statement routes after the S428 routes block
(`/page/statement`, `/api/statement/<cid>[.pdf|.xlsx]`, `POST /api/statement/<cid>/freeze`, `/api/statement/frozen/<sid>.pdf|.xlsx|.json`).
`stock_hub.html`: the first card's statement links (page · PDF · Excel · frozen "as at") above "The count — full report"; the status-card group
list gains `old` / `owner_use`. `stock_report.html`: the "N lines still need a word / Open the decision desk" block → "Closed on <date> by <who>
— see the statement" + the statement link; the tools gain the link.

### Backups made
- `/root/finance/finance.db.bak_S431_20260927_214214` (sqlite backup API, 26,312,704 bytes) — stays.
- `stock_app.py.bak_S431_0e0fc043`, `stock_hub.html.bak_S431_74ea0699`, `stock_report.html.bak_S431_bd750dc8` beside the files.
- Service restarted: `clinic-finance` only. After: active; `/finance/healthz` 200; `/finance/stock/page/statement` and `/finance/stock/page/hub`
  302 to plain curl (login gate, expected); journal shows only the restart's worker SIGTERM lines, nothing "NOT mounted", no traceback.
- **No data written by the install.** The `stock_statement` table is created on the first read; a freeze is the owner's tap (live: 0 frozen).

### The walk (install run, on scratch copies of the live database and the spine; crafted rows W431*, found by key)
```
   -- scratch: crafted W431 rows (an orthotic priced by the 0.30 rule, a S.RATE item, an MRP-only item, an unpriced item) on both copies and in the scratch spine
   -- NEW (the kit's files) on the scratch copies
     ok   the statement answers the owner; three sections in the order Medicines - Consumables - Orthotics
     ok   every one of the 373 counted lines of 06-09 appears exactly once (plus the 4 crafted): 377 rows, no duplicate, none missing
     ok   each line sits in the section of the owner's map (stock_item_section)
     ok   Medicines in count-sheet order (the differing lines, then the matched, each in the sheet's order)
     ok   the sections' line counts: Medicines 288, Consumables 19, Orthotics 70 (differing + matched = lines, matched never dropped)
     ok   every line carries Marg, physical and the words for both; a short line its shortage in words, an excess line its excess
     ok   a matched line has no shortage and no excess after the swaps; a differing line has one of the two
     ok   the live answers: 13 confirmed pairs, 2 not confirmed
     ok   every confirmed pair: both partners show the partner and the quantity taken out; shortage / excess = the count-day gap less the swap; a line wholly explained sits under Matched with its swap
     ok   ANKLE BINDER BAMBOO M (2 short on the count day, 1 swapped with ANKLE BINDER M TYNOR): 1 pc short after the swap, the partner named, Darpan's reason on the line
     ok   a line wholly explained by its confirmed swap sits under Matched with the swap shown, reading 'swap confirmed' / 'explained -- no loss' (20 such)
     ok   GEMCAL XT TABLETS (156 swapped with ZIBON EXTRA): the swap in strips + tabs, the partner named, no 'units'
     ok   a not-confirmed pair (LACTOVAX SYP / LINVIZ 600 / FEBUTAL) shows nothing: no swap, the whole count-day gap stands
     ok   the run's 122 lines read 'written off -- <group>' group by group: allowance 34, big 22, consume 5, old 6, owner_use 2, small 53
     ok   the close's totals as the statement counts them: 136 lines written off, Rs 64,678.78 at the desk's MRP (the run's 122 + 14 written off before the piles), 6 back in store, closed 27-Sep by manoj
     ok   the close's groups on the statement carry the run's counts (allowance 34, small 53, big 22, old 6, consume 5, owner's use 2) and the 14 earlier lines
     ok   the 6 back in store are named on their lines: CALAPTIN 40, DOLOGESIC SP, ETOZOX 90, GEMCAL XT TABLETS, HYORTH XL, TYCOB 1500
     ok   136 written-off lines on the Medicines + Consumables sections, each with its group title in words (allowance / small real gap / old stock / clinic consumption / owner's use / big loss / before the piles)
     ok   an excess medicine line says the vouchers corrected Marg -- never a loss (32 such lines)
     ok   the Medicines section's group line: the groups with their counts and rupees, back 6
     ok   every differing line is priced with a source tag or counted unpriced; a matched line carries no price
     ok   Medicines totals add up: short 10722026 = sum of the lines, excess 4942682 = sum, net = short - excess, unpriced 2 named
     ok   Consumables totals add up: short 610900 = sum of the lines, excess 8865000 = sum, net = short - excess, unpriced 0 named
     ok   Orthotics totals add up: short 886000 = sum of the lines, excess 134969 = sum, net = short - excess, unpriced 2 named
     ok   the overall totals are the three sections' sums
     ok   the price sources over the differing lines: spine S.RATE and spine MRP carry most; the rule and the rate fall-backs are tagged; the 'none' are the unpriced
     ok   crafted W431 KNEE BRACE L (orthotic, a purchase rate of Rs 700, no spine fact): priced by the 0.30 rule -> Rs 1,000 a pc, 2 short = Rs 2,000, tag 'rule 0.30'
     ok   crafted W431 MED TAB: the spine's S.RATE 120 a strip as on the count day (its 0.0 of 05-09 is no price; MRP 150 loses to S.RATE) -> Rs 12 a tab; 2 strips short = Rs 240
     ok   crafted W431 MRP TAB: only an MRP as on the count day (its S.RATE of 07-09 came after) -> Rs 20 a tab, 1 strip short = Rs 200, tag 'spine MRP'
     ok   crafted W431 NOPRICE PC: nothing prices it -> 'no price', named in the Medicines residue; its 2 pcs excess counted as a line, not a rupee
     ok   the orthotic section's totals at selling price stand apart: short 886000, excess 134969, net 751031 over 16 differing lines, 18 swaps
     ok   the price texts read 'Rs X a strip' / 'a pc'; every quantity in strips + tabs / pcs -- no 'unit(s)' anywhere in the statement
     ok   the block at the top of the orthotic section: lines still open (Darpan) 3, not yet on a voucher 18, renames unverified 22 of 23 -- read live from section_state
     ok   the block splits the open lines: Darpan's (no answer yet: 3) and the owner's (answered, still moving Marg without his word: 10); both kinds are marked 'open' on their lines and nowhere else; the crafted W431 KNEE BRACE L is Darpan's
     ok   a medicine the desk still holds open is marked 'open' too (the crafted W431 MED TAB and W431 MRP TAB, in a pile, not yet written off)
     ok   an orthotic line answered by Darpan carries his reason in English; one with the owner's word carries the word
     ok   nothing on the statement decides: no POST route but freeze; section_state was not changed by reading
     ok   the PDF (portrait, Darpan's-sheet style): one section a heading, totals first, then the lines, matched at the end
     ok   the PDF: medicines before consumables before orthotics, totals before lines, no 'unit(s)'
     ok   the XLSX: one sheet a section + Totals, in that order
     ok   the orthotic sheet carries the crafted brace with its rule tag and Rs 2,000
     ok   Freeze this statement (the owner): ONE stock_statement row -- frozen JSON with its md5, PDF and XLSX kept under pad_uploads/statements, dated, by manoj
     ok   the frozen totals equal the live ones at that moment (three sections + overall + the orthotic block)
     ok   the frozen copy serves: PDF (says 'Frozen ... fingerprint'), XLSX, JSON with the data
     ok   the audit log carries the freeze
     ok   a second freeze is a second row; the earlier stays listed; the page lists both, newest first
     ok   the hub's links carry the statement (page, PDF, Excel) and the latest frozen copy 'as at <time>' by manoj
     ok   the hub page: the first card gains 'The count statement -- section by section' above 'The count -- full report'; the status card names old stock and owner's use
     ok   the old report keeps its route and is closed: 'Closed on <date> -- see the statement', a statement link in its tools, NO 'Open the decision desk' pointer; its JSON links carry the statement
     ok   the statement page serves the owner with the Freeze button armed (can_freeze true); English; no 'unit(s)' in its source
     ok   the doctor (bhawna) reads the statement and its PDF, cannot freeze
     ok   bhati / darpan / shavez are refused on the page, the JSON, the PDF and the freeze
     ok   a count that does not exist answers 404; the hub without S431 would still answer (the links are defensive)
     ok   stock_statement.py is beside stock_app.py
   -- NEGATIVE CONTROL: the same scenario on the box as it is (must go red)
      old RED   the statement answers the owner; three sections in the order Medicines - Consumables - Orthotics
      old RED   sections -- the step ran        old RED   swaps -- the step ran        old RED   became -- the step ran
      old RED   prices -- the step ran          old RED   ortho -- the step ran        old RED   freeze -- the step ran
      old RED   the PDF (portrait, Darpan's-sheet style) ...   old RED   the PDF: medicines before consumables ...
      old RED   the XLSX: one sheet a section + Totals ...     old RED   the orthotic sheet carries the crafted brace ...
     ok   NEGATIVE: the old files go red (11 of 11 checks red): no statement route, no freeze, the decision-desk pointer still on the report, no statement link on the hub
     ok   NEGATIVE: the old box has no stock_statement.py
   WALK_S431 GREEN -- 56 of 56 passed
```
(The walk's "Medicines 288 / Orthotics 70" include its 4 crafted lines; live: 285 / 19 / 69 = 373. "Lines still open (Darpan) 3" includes the
crafted brace; live 2.) Dry runs before the real one: 48/54 → 53/55 → 56/56 (the reds were the walk's own assumptions — ANKLE BINDER BAMBOO M is 2
short not 1; a wholly-swapped orthotic line carries the owner's "explained — no loss"; excess lines the owner had explained needed the "never a
loss" text too; a back line wholly swapped sits under Matched; the price-source thresholds; the open-line split Darpan / owner).

### The earlier walks re-run on the patched files (same install run, each against its own pre-kit control)
- **S430** `walk_s430.py` (S430 kit) — control old430 = live + the five `.bak_S430_*`; database = `finance.db.bak_S430_20260927_121728` (12:17, before
  the owner's 12:58 close, the state S430's own walk ran in): **GREEN 42 of 42**.
- **S427** `walk_s427_s430.py` (S430 kit's adjusted copy) — control old427 = the seven `.bak_S427_*`, no qty_words/stock_watch; database =
  `finance.db.bak_S428_20260927_103804` (10:38): **GREEN 82 of 82**.
- **S428** `walk_s428_s430.py` (S430 kit's adjusted copy) — control old428 = the eight `.bak_S428_*`, no stock_watch; database = the 12:17 backup:
  **GREEN 73 of 73**.
- **S404** `walk_s404.py` (S404 kit) — control old404 = the five `.bak_S404_*` + spine_build/marg_take/portal backups as every kit since S404; database
  = `finance.db.bak_S412_20260926_140429`: **GREEN 65/65**.
Call made: S430's and S428's walks close the count / read the pre-close state, so they run on the 12:17 backup rather than today's live copy
(the live count is closed since 12:58); said here.

### The figures (figures_s431.py, read 21:58 IST on a fresh scratch copy through the live files)
```
ALL SECTIONS   373 lines (187 differ, 186 matched)  short Rs 1,19,749.26  excess Rs 1,39,426.51  net -Rs 19,677.25  without a price 3
MEDICINES      285 lines (163 differ, 122 matched)  short Rs 1,06,780.26 (134 lines)  excess Rs 49,426.82 (29 lines)  net Rs 57,353.44  swaps 8  without a price 1: CORTIRI
   price sources: spine MRP 121, spine S.RATE 41, none 1
   the close's groups here: Within the allowance 33 (Rs 8,635.85); Big loss 22 (Rs 29,657.97); Clinic consumption 2 (Rs 15,297.40); before the piles 14 (Rs 783.08);
   Old stock 4 (Rs 271.15); Owner's use 2 (Rs 2,989.39); Small real gap 52 (Rs 23,381.76); back in store 6           (all at selling price)
CONSUMABLES     19 lines (9 differ, 10 matched)  short Rs 6,109 (7 lines)  excess Rs 88,650 (2 lines)  net -Rs 82,541  swaps 0  without a price 0
   price sources: spine MRP 7, spine S.RATE 2
   the close's groups here: Within the allowance 1 (Rs 292.50); Clinic consumption 3 (Rs 3,250); Old stock 2 (Rs 1,653.38); Small real gap 1 (Rs 913.12)
ORTHOTICS       69 lines (15 differ, 54 matched)  short Rs 6,860 (13 lines)  excess Rs 1,349.69 (2 lines)  net Rs 5,510.31  swaps 18  without a price 2:
   FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S · price sources: spine S.RATE 7, spine MRP 6, none 2
   block: still open (Darpan) 2 (FINGER COT SPILNT REMEDE, SOFT COLLAR BODY AID S); awaiting the owner's word 10; not yet on a voucher 18; renames unverified 22 of 23
   largest: L S BELT CONT GRAY UNISON XXX 2 pcs Rs 2,780 (S.RATE); RIB BELT UNIVERSAL UNISON 1 pc Rs 690 (MRP); RIB BELT S TYNOR 1 pc Rs 650 (S.RATE); DYNA WRIST BRACE REVER LONG 1 pc Rs 595 (MRP)
the close (27-09-2026 12:58 IST by manoj): 136 lines written off, Rs 64,678.78 at the desk's MRP; 6 back in store; groups allowance 34 / small 53 / big 22 / old 6 / consume 5 / owner_use 2 / earlier 14
frozen copies: 0
```
No unpriced residue in Consumables; Medicines 1 (CORTIRI — old stock, no spine fact, no rate); Orthotics 2 (no spine fact, no purchase rate on record).

### Not done, and why
- No freeze was made by the install: "Freeze this statement" is the owner's tap (the brief: one tap, the owner). The hub shows the live links until he taps.
- The PDF was checked by content, order and word gate in the walk, not opened in a viewer (no viewer on the box; the page is login-gated from here).
- `finance_app.py`, `stockmatch.py/html`, `section_map.py`, `loss_piles.py` untouched (read only, as the brief lists them).

### Outside the brief, noticed
- **10 orthotic lines are answered by Darpan but await the owner's word** (named above) — the section stays OPEN until he rules on them on the hub /
  Stock milaan; 18 orthotic lines are not yet on a voucher and 22 of 23 renames are unverified (Amir). The statement shows this; nothing here decides it.
- **Two consumable lines carry ₹88,650 of excess at selling price** (Marg below the shelf) — the statement lists them; worth the owner's eye.
- The **Clinic consumption group** prices at ₹15,297.40 here (spine S.RATE / MRP) where the desk's MRP had ₹0 (unpriced at the desk) — the desk's
  figure was a gap in the desk's price sources, not a real zero; the write-off run's ₹64,678.78 is unchanged (frozen).
- The count's own `stock_count_close` row says closed **06-09-2026 14:43 by manoj (complete)** — that date is what the old report's "Closed on" now shows;
  the S427 write-off close of 27-Sep 12:58 is on the statement's close line. If the report should show the 27-Sep date instead, it is a one-line change (say so).
- The spine's S.RATE for 4 items is stored as `0.0` (treated as no price, falls to MRP) and 3 count items have no spine item at all (`section_map`
  names differ) — data, not touched.

### Publish
Published with `PUBLISH_ALL.bat` (kit + this report); the commit is named in the "After publish" section below.
