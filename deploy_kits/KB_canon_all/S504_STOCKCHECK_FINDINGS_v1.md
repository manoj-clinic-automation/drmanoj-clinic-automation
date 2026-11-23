# S504 — Stock check page: why "53 need a look" is mostly wrong (read 22-Nov-2026 18:50–19:10 IST, nothing built)

Owner's report (18:50 IST): the Stock check page shows 53 items needing a look; the shelf looks too high; the page's Marg figure does not match the item ledger's (MEG QCS). All confirmed from the live pages and the live code (stock_figure.py 8130315e, stock_check.py S930 v1.1, item_ledger.py).

## 1 · The main fault — a bill keyed in Marg after the morning print is counted on the shelf side only
- The page's **Marg** column = Marg's closing (as on 20-11, printed Sat 21-11 09:37) + the spine's movements dated AFTER 20-11 (sales of 21-11). stock_figure.marg().
- The **Shelf** column = the last count + every spine movement after it, purchases by their BILL DATE.
- Amir keyed the 20-11 bills on Saturday AFTER Shavez's 09:37 print (and some on Sunday): Kedar 250 (FLUXIC P 20, PRETOL 8 9, MEG QCS 30, FLEMCORT 6 20, PATOPAN DSR 40, TYRO BR 50 — "paper matches Marg"), Ess Kay 10403 (FERONES HD 30), and others. These bills are dated 20-11, so marg() does not add them (not after the closing day) and the closing print does not hold them (keyed later) — but the shelf has them. **Phantom surplus = the bill's quantity.**
- Verified against the ledger (which reads Marg's Sunday print): MEG QCS true gap +0:14 (page +30:14) · PATOPAN DSR 0 (page +40:0) · FERONES HD 0 (page +30:0) · FLUXIC P (page +20:0) · PRETOL 8 (page +9:0). Same shape, not yet opened: XYCAL K2 +20, NUCOXIA P +10, FLEXURA D +10, RYCOBAL D3 +10, JAKMAC 5 +8, JARDIANCE +4, RIFAGUT +3, BIO D3 MAX +9:5. Roughly 13 of the 26 named rows, including every big one.
- A **negative Marg figure** on the page (MEG QCS −9:11, PATOPAN −3:4) is the tell: Marg never printed a negative; the column is a closing carried through sales with a purchase missing.
- The code KNOWS this case: stock_figure.late_purchase() (R3-C6) existed for the retired drift page ("such an item is not judged against the shelf"); the item ledger has its own `_late` reading ("Marg's closing had not taken in bill 250 yet" / "took in … keyed late"). S930's page uses neither. Three readers, three answers — against the one-function rule.

## 2 · Two pages, two Marg closings
- Shavez's Sunday print was a SAME-DAY print (as on 22-11, ~09:xx). Under D740 a same-day print is a START capture: usable only after the next sale report covers its day (Monday morning) and its verification passes. So the Stock check falls back to Saturday's print (as on 20-11). The ledger reads sp_close directly and uses the Sunday print, labelled "Marg's closing of 22-11" (the print day, though it stands for the end of Saturday).
- Until Monday's sale report lands, the Stock check is a day behind the ledger by design. Saturday's print was "as on yesterday"; Sunday's "as on today" — the staff's choice of date in Marg decides which rule the print falls under.

## 3 · TYRO BR — the tap not tied to the bill
- Page: Marg 2:2, shelf 37:9, "+50 waiting for Marg — tapped 50:0, no bill read yet" (Kedar 20-11). Ledger: Marg (Sunday) 52:2; bill 250's TYRO-BR 50 is in Marg and the scan line is read and matched.
- So carried() (S583 rule) and bill_units() (S928) do not tie this tap to bill 250, while the ledger's path does. The delivery then sits on the shelf twice (as Marg's purchase and as a waiting tap); the page subtracts the waiting column from the core, so the gap does not double, but "3 deliveries waiting" is wrong by at least this one and S928's short-supply rule cannot speak for it. BIO D3 MAX (Gunina 20-11, "no bill read yet") is likely the same. Cause not yet traced (needs the order/arrival rows).
- TYRO BR's real position: Marg 52:2 vs the 12-10 evening count carried 37:9 → about −14:3, not +35:7; Marg's Batch Stock also says 14:1 of its stock is on no batch. Darpan's Monday count settles it (already first on his list).

## 4 · Smaller points
- VINBACTUM DS −25 pieces: a clinic consumable (the start-capture check already lists BLADE, GLOVES SURGICAL 7, VINBACTUM DS, VINTAZ P 4500 INJ, ZIG ZAG COTTON 500GM as "consume"); the page still judges them as shortages.
- The ledger's late-bill label can name the wrong bill when two bills carry the same quantity (TYRO BR: "bill 242 of 13-11" where it was 250 of 20-11) — cosmetic.
- PRETOL-4's note repeats "carried from …" fourteen times — cosmetic.
- Real-looking rows that stand: ZIBON EXTRA −15:3 (Darpan 18-11), KT ROS DT −6:11, ORICOX P +1:4 (Darpan 21-11), TRAMATEE P −2:12 (provisional), the sub-strip tail. The 19 orthotic rows not examined here.

## 5 · The repair, as decided (not built; for the owner's go)
1. One rule in stock_figure.marg(): a bill first seen in a purchase export stamped AFTER the closing's print is added to Marg's figure — the fact the ledger's `_late` already reasons from, read from sp_export instead of guessed by quantity. Page, ledger and count judgments all read it.
2. The item ledger on the one function (plan item 0, second half) — one Marg figure everywhere, labelled by the day whose END it stands for.
3. Trace and fix why carried()/bill_units() miss bill 250 for TYRO BR's tap.
4. Consumables marked as such; off the Need-a-look list.
5. The page says "Marg's figure is behind a bill" on such rows instead of a gap, and never prints a negative Marg.
