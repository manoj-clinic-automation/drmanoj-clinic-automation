# S628_ONE_NAME_LIST — the one name list, and the order list made right (D761)

**Project:** Sanjeevni (session 339, 22-Oct-2026). Built IN THE CHAT (no API runner). Brief: `claude_code_briefs/S628_ONE_NAME_LIST.md` (v2).
**The owner's words (S338):** the order list said medicines "did not come" that came, and put them back on the dealer's next order by itself.

## What changes, for whom
- **The owner (and Shavez) — `https://followup.dr-manoj.in/finance/porders/s454/track`:** THIO Q AP, ZUPRINOR 5 and POWERGESIC 100 PATCH read
  *came* (POWERGESIC: *came from Janta (bill 23672)*); LINVIZ 600 reads *short 7 strips — 36 tablets came on the bill (another pack size)*;
  their wrong carries drop by themselves, LINVIZ's becomes 7. Every scan on an order card has *Send back for rescan* (or *sent back ✓ — Withdraw*);
  the asks carry *Withdraw*; *Saved under another dealer* has one button *Change dealer to …* (read from the paper by the server); *The same paper
  scanned twice* names B-0150 / B-0154; "came X of Y" the right way; English only on the owner's pages; an arrival with nothing on it says so.
  The owner alone gets the name questions (*X on Deepam's bill A000678 = Y? Yes / No*) — none at the build: both Marg pairs were sure.
- **`https://followup.dr-manoj.in/finance/porders/s454/scans`:** a folded *Every pharmacy scan · last 14 days*, each with Send back.
- **Staff screens (reception, Darpan, Amir): unchanged** — walked page by page; only their counts follow the corrected lines.

## Files (FROM → TO)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_figure.py | 8c66b6b1 | a0008c14 |
| /root/finance/porders.py | b1736494 | 3209d0a2 |
| /root/finance/order_track.py | a8c46700 | 4edfef6b |
| /root/finance/porders_s454.py | 53ef850f | 0ce83525 |
| /root/finance/med_names.py | NEW | a7439e3f |

Full md5s: `TO_PINS.md5`. Read only: order_sheet.py, stock_watch.py, purchase_app.py, scan_register.py, /root/shared/scan_quality.py.
**Not touched:** `/root/assetapp/asset_register.py` and `/root/shared/scan_checks_s441.py` (the Scan App chat's) — the independent read (R1) showed
that B-0159 was set aside by the owner's own S441 answer, so the rule "the clearer scan is kept" belongs in both of those files: passed to the
Scan App chat on the board. On the pharmacy side the order list already reads the clearer scan of every duplicate family.

## How
- **med_names.py** — table `med_name` (kind 'marg': two Marg items that are one medicine; kind 'scan': a dealer's printed spelling) and
  `med_name_seen`. `learn()` (at most once in 10 minutes; `names.learn_gap_min`) from the orders (marg) and from every linked, Claude-read scan
  (scan — the September seed: 68 sure spellings on the 22-Oct copy). Sure only by the strict rules (pack words TAB/CAP/STRIP/`\d+T` only; never
  a `N*M` size, a strength, a tablet/capsule clash or a variant word — FORTE, PLUS, DSR, SR …; prices within 5 %; packings both strips); else
  asked once. A substitute is never sure (D760).
- **stock_figure.py** — `arrival_forms()` (printed_forms + the partners) read ONLY by `_line_forms` (bill line ↔ order line); `printed_forms`,
  closings, counts and splits unchanged (R1-1). `_carried` reads the partners' keys too; `own_only` (the order's own dealer first, R1-6);
  rule (b) also counts lines credited to another dealer (R1-6). The stock figure of all 1,045 spine items is byte-identical before and after
  (walked); arrivals in transit lose THIO Q AP and LINVIZ 600 (Marg has them under the partner items).
- **porders.detect_supplies** — learn first; packs by tablets when the bill's packing differs (`billed_units`); a billed line below its packs read
  again by rule (a), own dealer only, raised never lowered (F-990); then other dealers' bills within `names.window_days` (7) of the order day,
  orders since `order.track_since` only (F-991): columns `other_supplier, other_bill_no, other_date, other_qty`.
- **order_track.py** — the 'other' state (came), the tablets note, carries follow the short (`resized`), the partners count in "already on
  Marg's order" / "re-ordered", the loosened scan-name test, the clearer scan of a family (`head`), `paper_dealer`, `same_paper`.
- **porders_s454.py** — the pages above; POST `/finance/porders/api/s454/name_answer` (owner only) and `/finance/porders/api/s454/dealer_fix`
  (owner + porders.rescan_askers): `s454_scan_answer(vendor)` + `purchase_scan_state.chosen_vendor` (no alias learnt), the tie moves to the paper
  dealer's untied order of the week before (else removed), then `purchase_app._rematch`.

## Install (the owner's one server line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S628_ONE_NAME_LIST/install_S628_ONE_NAME_LIST.sh
```
Gates → lock → pins → rebuilt from the box's bytes → walk NEW (green) + OLD (`--expect-red`) on copies → backups (files and finance.db) →
placed + read back → one restart of clinic-finance → healthz → the first pass on the live database (facts printed) → lock released.
**Undo:** the line the installer prints (the four `.bak_S628_<from8>` back, med_names.py removed, one restart). The new tables and columns are
inert without the code; the order lines the first pass corrected stay corrected (they are Marg's facts), so a re-install after an undo finds its
negative control green on them and stops -- put back `finance.db.bak_S628_<stamp>` first if a re-install is ever wanted (rehearsed).

## The walk
`walk_s628.py` — 69 checks, 27 controls, green on the new files; the negative control (`--expect-red`) red on all 25 controls on the old.
S619's own walk on the new files: red only on the four checks that asserted the false shorts and their carries, and on its PDF check (red on
the old files too in the offline scratch: the archive is not there).
