# S975_STOCKCHECK_V10 — the Stock check page in three bands (D1106: mock-up v10, his "OK" 11:52 IST 28-Nov-2026)

**Board:** `_numbers` v2433 → v2434 (kit S975), PLANNED line v2435 (Sanjeevni's own files). Built in the Sanjeevni chat, session 542,
28-Nov-2026, by Opus, on `S540_STOCKCHECK_V10_DESIGN.md`. Every FROM is the 28-Nov bundle's (03:18 IST), each md5 checked (F-472).

**What he sees (his page only, PC first, no confirm dialog — the two-tap buttons as before):**
1. **Your write-offs — waiting for Amir** (first): one row per write-off of his that Marg's report does not hold yet — the loss register's
   open lines. Each row: written off · booked dd-mm · the card (`STOCK ISSUE · dd-mm`) and its state ("N days — not done", or
   "Kar diya dd-mm — the next report decides") · the 3-step track Booked → Amir keys it → In Marg · its cost. It folds open to its path
   (the count, his tap, the card, the closing rule), its voucher lines and its item ledger. Under the band: the month's cost and MRP and
   the full loss register's link. A row leaves the band by itself when Marg's Stock Issue report shows it.
2. **Today's counts — <counter>, <day>** (second): every count saved today, one plain verdict: agrees · more than Marg — never a loss
   (plus "likely a delivery not yet in Marg" when Marg's purchases reach an earlier day) · within your allowance (the group button) ·
   a loss since the last count (its own Write off / Pursue) · written off by you — above · waits for the day's sales. Any earlier count
   still waiting for his call stays visible under it with its buttons; this week's earlier counts are folded underneath.
3. **Waiting on others** (folded): other corrections on their way (box 2 less band 1) · old corrections re-judged (box 3) · count first
   (box 6, with its "all on Darpan's next list" button) · vouchers nobody asked for (box 4) · settled · not judged a loss · the rules.

**No row twice.** A band-1 item leaves the "on their way" fold, unless another correction of it is also on its way (an Expiry-watch batch
fix, say) — then it stays there, told "your write-off: band 1 above". A Withdraw (a later count agrees with Marg) moves onto the band-1 row.
Box 3's "today's gap" of an item he wrote off is told as band 1's, never red.

**F-1738** (`voucher_judge.py` v1.5): a fresh count with MORE on the shelf than in Marg is the whole-item verdict `surplus` — "more than
Marg — noted, never a loss; nothing waits for your call", grey in box 3 (CCM, 28-11, was red "today's gap — waits for your call"). Every
other reader of the verdict acts on it as it did on a fresh gap (voucher_inquiry closes only on settled / held). A whole-unit
item (CCM) is never judged on its stored figure: its fresh gap reads amber 'look' -- "this count cannot be judged yet" -- until the
record's pack is put right (second look 3, re-look B).

**F-1739** (`item_ledger.py`): CCM is on the desk's whole-unit list (`CCM = bottle`); Marg and the ledger count it by the bottle, but the
count screen stores a pack of the stock record's size (40) per bottle. The 28-11 count of ONE bottle read "40 bottles counted, 40 bottles
more". A whole-unit item's count that is whole packs now reads "1 bottle counted · 1 bottle more", the screen's stored figure kept in its
words; band 2 says "counted 1 bottle · Marg 0 bottles · +1 bottle". Every other count reads as before. **The root — the stock record's pack
for a whole-unit item — is not changed here** (it touches the stock record and Darpan's count screen): an F at the close, its own kit.

**Files.** Every change is an appended S975 block (re-binding, the established pattern), apart from these anchored edits:
`stock_check.py` two lines in box 3 (the tag colour of `surplus`, its whole-item line not 'now'); `item_ledger.py` the two count-line
renderings read the count's own words; `stock_check.html` the old `renderDesk` renamed `renderDeskV9(el)` (it draws band 3's folds and is
the fallback when the bands are missing), the new `renderDesk`, the CSS, one line in `render()` (a redraw for Marg's purchases-to day).
`make_s975.py` builds the four files from the FROM bytes and `blocks/`, each anchor found exactly once.

| file | FROM | TO |
|---|---|---|
| /root/finance/stock_check.py | 623c1052 (S971) | see TO_PINS.md5 (v1.9) |
| /root/finance/stock_check.html | 225af840 (S971) | |
| /root/finance/voucher_judge.py | 0a066f96 (S973) | v1.5 |
| /root/finance/item_ledger.py | 6735167f (S967) | |

The desk API keeps every box exactly as before (the desk's writes and kits S965–S973 read them) and ADDS `band1`, `band1_foot`, `band2`,
`earlier`, `week`, `way3`, `v10_totals`. No table, no setting, no staff screen is touched.

**Reviews.** Cold review NOT SAFE (1 MUST: a box-1 row with no buttons and a count over 7 days old dropped off the page) + 6 SHOULD,
all built in; second look SAFE, 6 SHOULD built in; re-look SAFE, 2 SHOULD built in.

**Proof (device VM).**
- `walk_s975.py` on kit B's made-up fixture: **44/44**, twice. Control on the live files: red (V1, B0, F1, F2, G1 …).
- The earlier walks on the new files, as on the live files apart from version lines: S973 (V1 v1.4), S971 (J4, R3), S969 (R3), S967 (W4, D13), S965 (C14c).
- Live shape, a copy of the 28-Nov 03:18 database: 6 write-offs in band 1 (Nov ₹2,057.52 = the loss register), 2 earlier allowance rows
  kept with the group button, way3 = box 2 less the 6; every box byte-equal to the old desk but box 3's relabel of a gap he wrote off.
- `dom_s975.js` (jsdom, the page's own script on that live-shape desk): **11/11**; the live page 2/11; without the bands the page draws the old boxes.
- Rehearsal on a made-up root: see `rehearse_s975.sh`.

**Install** (his publish, then one line on the server):

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s975kit && cp -rp /root/deploy/repo/deploy_kits/S975_STOCKCHECK_V10 /tmp/s975kit && bash /tmp/s975kit/install_S975_STOCKCHECK_V10.sh

**The way back:** `bash /root/deploy/repo/deploy_kits/S975_STOCKCHECK_V10/undo_s975.sh` — the four files back, the service restarted.
