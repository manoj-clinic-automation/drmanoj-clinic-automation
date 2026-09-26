# Claude Code brief — S417_DAY_ONE_FIXES (four corrections from the owner's first day on S403–S414: units on the orders page,
the card shelf, the Yes Bank balance tile with a provisional NEFT, one item-name check)

Written 26-Sep-2026 by the Sanjeevni chat (S283). Read `CLAUDE.md` first. **Kit S417 · fault F-636** (claimed on the System Board).
Four small, independent corrections in one kit; each with its own anchored patch and walk checks. Read every FROM pin live (S414 was the
last to move `finance_approvals.html`; S412 `packs.py`/`stmt_shelf.py`; S409/S410 `purchase_app.py`/`porders.py`).

## 1 · Stock in the item's own unit on the orders pages (Sanjeevni)
The owner: "the orders page shows the stock in tablets and the order in strips — confusing." On `/finance/purchase/page/orders`,
`/page/staff`, the Purchase orders screen (`porders`) and the owner's section: **Stock now** in the same unit as the order — strips + loose
(`12 strips + 4`) using the item's `pack_size` (`stock_snapshot.pack_size`/`packing`, the spine's reading), pieces for orthotics, bottles /
tubes / units for non-strip packings (the packing text decides; when the pack size is unknown, show the raw count with its unit word,
never a bare number). Quantities in the WhatsApp text stay as they are (D-decided format). Every place that prints stock beside an order
qty is covered — list them in the report.

## 2 · The card shelf (PARENT-owned S408/S412; declared)
On `/finance/packs` today: (a) `All_Transactions.xlsx` sits in "Unplaced files — which account?" as "not a readable PDF" — it must never be
asked about: an `.xlsx` in the Credit Card Statements root is the running Excel (`folder='all_txn'`, filed, shown on the pack row 4 as the
attachment); (b) the three card cells read "tail not learned yet · empty" and pack row 4 says "no decrypted statement on the shelf" although
the Decrypted folder holds every month's statement (S408 fetched 38): the card PDFs are placed "by the card folder" but their **statement
period / date and card tail are never read**, so no month cell fills. Read them from the decrypted PDF text (statement date, period, the
masked card number inside; the ICICI Amazon card changed number in Feb 2026 — both forms one card), learn the tail, fill the month cells,
and make pack row 4 find the month's three decrypted statements. A locked original whose decrypted twin exists is "duplicate of decrypted";
a month whose decrypted twin is missing shows "decrypted copy not yet made" (the owner's personal script makes them in batches).

## 3 · The Yes Bank balance tile and a provisional NEFT (Sanjeevni; S378 tile, S405/S407 event)
The owner tapped "NEFT done" for August; the Yes Bank tile on `/finance/approvals` Bank section did not move. Rule: when a
`purchase_neft_event` is provisional (owner-tapped or SMS-confirmed) and no statement debit has confirmed it, the tile shows
`− ₹X provisional NEFT (awaiting statement)` as a separate line under the balance and the headline balance includes it, marked
"incl. provisional"; the moment the statement confirms (S407), the line disappears and nothing is double-counted. Read-only on the tile;
no new table. The same figure on Amir's board card if it shows a balance (check; do not add one).

## 4 · One item name: JIARDIANCE (facts only, no rename)
The owner saw an item on his page printed as "GRDIANS 25 MG" (his reading) and says the product is **JIARDIANCE 10 mg**. Find every stock /
sale / purchase name that matches JARDIAN / JIARDIAN / GRDIAN (spelling-tolerant), with strength, packing, supplier(s), last purchase and
last sale, and put the list in the report — **change nothing**; the owner decides, and a rename then goes the D620 way (Amir in Marg, the
rename memory follows). If a 10 mg and a 25 mg both exist, say so plainly.

## 5 · Pins — read live: purchase_app.py, porders.py, porders.html (Sanjeevni); packs.py, stmt_shelf.py (parent, declared);
finance_ui/finance_approvals.html (parent, declared — the Bank tile line and any unit display it carries); sanjeevni_approvals.py (the
bank view API; Sanjeevni). Restart `clinic-finance` only.

## 6 · Walk (scratch copies; own rows)
Strips + loose renders from crafted pack sizes (10 → `12 strips + 4`; orthotic → `3 pcs`; unknown → raw with unit word) on every listed
page · the xlsx lands as all_txn and never in the unplaced list · crafted decrypted card PDFs for two months fill the three cells and pack
row 4; the locked twin reads "duplicate of decrypted"; a missing twin says so · the tile: a crafted provisional event shows the line and
adjusts the headline; a crafted confirming statement debit removes it, no double count; no event → tile byte-identical · the name search
returns the crafted matches with their fields · S403–S414 walks re-run green (S404 on the 14:04 backup as S414 did).

## 7 · Done means
Kit `deploy_kits\S417_DAY_ONE_FIXES\` · installed · published · `claude_code_briefs\REPORT_S417.md` — owner lines first: what the
orders page now shows, what the packs page shows for the cards, what the Yes Bank tile reads for August, and the JIARDIANCE findings as
a short table; ending with `https://followup.dr-manoj.in/finance/purchase/page/orders`, `https://followup.dr-manoj.in/finance/packs`
and `https://followup.dr-manoj.in/finance/approvals`.
