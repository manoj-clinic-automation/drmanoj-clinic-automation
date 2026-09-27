# REPORT_S418: the Loss desk as four piles, one tap each (S418_LOSS_DESK_PILES, D631, F-641)

Installed on srv1746119 on 27-Sep-2026. The installer started at 05:42:17 IST (build lock and backup stamp) and restarted clinic-finance at 05:48:41 IST (journal). Kit: `deploy_kits\S418_LOSS_DESK_PILES\`.

## For the owner
- **Your Loss desk is now four piles on one page.** Every open line sits in one pile, and one tap settles each pile. Your page is in English.
- **1 · With me / back in store: 5 lines, Rs 17,431.** The first three are **ETOZOX 90 (Rs 7,546), HYORTH XL (Rs 7,002) and DOLOGESIC SP (Rs 2,609)**. The other two are CALAPTIN 40 and VINTAZ P 4500 INJ. Tap **Accept back** on a line and it closes as "it is here, not lost". Nothing else is asked.
- **2 · Write off as normal loss: 89 lines, Rs 29,496 at MRP (Rs 20,869 at cost).** It has three named groups:
  - within the allowance: 5 lines, Rs 430
  - small real gap under Rs 1,000: 73 lines, Rs 25,735
  - clinic consumables such as blades, gloves and syringes: 11 lines, Rs 3,330

  One tap, then **"Yes, write off 89 lines"** within 10 seconds, writes them all off and puts Amir's Marg vouchers on his board in the same tap. The allowance is set to **wide**, as you ruled.
- **3 · Pursue: 11 lines, Rs 6,959.** This is every gap of Rs 1,000 or more, plus 5 lines with no price on record. **Make the sheet for Darpan** gives him these lines. He answers on his Stock milaan, and each line stays open until you settle it.
- **4 · Recount: 32 lines, Rs 27,921.** These are counts that cannot be right, or are 50 or more units off; INTACOXIA-60 (+719) is here. **Ask Darpan to recount** puts them on his Stock milaan under "Phir se gino", with a box to type the count. His figure replaces the shelf figure, and the line moves to its right pile by itself.
- **Your desk and the hub now show the same figures:** Rs 81,806 still open, out of Rs 85,236 short at the count. Until now they disagreed: the desk said Rs 84,349 and the hub Rs 64,355. The hub is now a status card with links. Every rule above is a setting at the foot of the desk, and every change you make to one is recorded. It is installed and tested.

https://followup.dr-manoj.in/finance/stock/page/loss?count=1

## For the chat

### Pins: FROM (read live 27-Sep 05:03 IST, each = S404's TO) → TO (md5 read back on the box after placing)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py | 586ae78ae6437f806692c2a1e4eeeb37 | cf464882e49865f38153e1df6218301d |
| /root/finance/stock_hub.html (declared: the brief's §3a needs the hub's status card and step list) | 68d11419e7fb9a8e5fec74095b60b255 | bb8741fa7671399f9c495c75946d7c11 |
| /root/finance/stockmatch.py | d37c674b6b7435966f048503c40622df | d5f9392fea4247b37705e865e1c242cb |
| /root/finance/stockmatch.html | c5db7067fc18cf9a6bd29c48f4c1540d | 9a090e03c954bfda5a787e8d834f275c |
| /root/finance/stock_loss.html (whole page, shipped in the kit) | 0d77203482d668d8d00e5145682c841f | 16cdddaa6363ccc8da0278fa5d4635a3 |
| /root/finance/loss_piles.py (new) | (none) | 3b6554f86507509e0b1893129e748274 |

The four patched files were built on the box from the live bytes by `make_s418.py`. It makes anchored edits and requires every anchor to occur exactly once. The build matched the kit's pins, and all six files read back at them. `stock_amir.html` (c2ea41b2) was pinned but needed no change: the new voucher round shows on Amir's board like any other round. Not touched: `stock_diffs.html`, `stock_desk.html`, `claim_queue.py`, `pad_receipt.py` (used read-only for the PDF), `finance_app.py`, portal, cron.

### What changed
- **`loss_piles.py` (new)** holds the piles, the settings and the record.
  - `classify()` puts each desk line in exactly one bucket. Orthotic lines (section map or lane `ortho`) are left on S404's section.
  - For a shortage, the order is: the owner's move, then his word (PARKED → with_me, RECOVER → pursue, RECOUNT → recount), then the suggestion.
  - The suggestion order is: consumable → write off/consume; `recount` lane or ≥ `stock.recount_trigger` units → recount; within `_allowance_units()` × scale → write off/allowance; no price → pursue; under the small-gap ceiling → write off/small; otherwise pursue.
  - A recounted line skips the recount rules, and a recount answer newer than a move re-piles the line.
  - `totals_of()` is THE five totals: open = the four piles; back (valued at the count day); written off (by group); short = open + back + written off.
- **The shelf layer:** `apply_fixes()` runs from `_pad_report_data` after the swaps. It overlays `stock_shelf_fix` (Accept back = Marg's figure; Darpan's recount) at read time and keeps the count-day figures on the line. `stock_diff` quantities (the seal) are never touched.
- **`stock_app.py`:**
  - the guarded import;
  - the layer call;
  - `_voucher_pending` / `_voucher_make(..., items=None)`, so the write-off round carries exactly the pile's lines;
  - `_voucher_batch_size` reads `stock.voucher_batch` first;
  - `hub.desk` and `report.desk` come from `_desk_totals_safe`, the same function the desk and the PDF use;
  - routes `/api/loss/<cid>/piles`, `/pile/move`, `/pile/accept`, `/pile/writeoff` (arm → 10-s token → confirm), `/pile/pursue` (RECOVER + tick, then the unchanged `api_loss_share`, then the claim-queue sync), `/pile/recount`, `/pile/setting`, `/record.pdf`.
- **What each tap writes:**
  - Accept back: lane word + S221 decision `EXPLAINED`, `cause=FOUND`, `status=closed`, and a shelf fix.
  - Write off: `WRITE_OFF` + closed, a frozen `stock_writeoff_run` (groups item by item, rules in force, md5, voucher round).
  - Every tap is audited in `audit_log` (`stock_pile`, or `setting` for rule changes).
- **`stock_hub.html`:** a status card with the five totals and links (Loss desk, record PDF, Amir's board, Stock milaan). Steps 3–5 are replaced by one step, "The Loss desk — four piles". The rest are renumbered 2/4/5/6, and step 2's pointer to the vouchers now reads step 4.
- **`stockmatch.py/html`:** two new cards.
  - **Phir se gino**: blind count boxes (patte + goli), `recount_answer`; his own figure can be corrected within 10 minutes.
  - **Bina bill?**: live claims of the round, answered through `claim_queue.answer()` and audited.
  - The title is now "Stock milaan" (the text "Stock milaan" is kept for S404's page check).
- **Settings** (seeded only where absent, after the green restart): allowance_scale 2, pursue_floor_p 100000, recount_trigger 50, voucher_batch 6, accept_back_by owner, consume_auto 1, rolling_section_items 90, rolling_day Monday. small_gap_ceiling_p is left blank, which means it equals the floor.

### Calls I made (the brief left these open; each reason in one line)
- **Surplus lines:** a surplus in the `recount` lane or of ≥ 50 units starts in Recount; the other surpluses sit in the "Over — never a loss" note. This reconciles §3's note with §3b's recount trigger.
- **A shortage of ≥ 50 units starts in Recount before the value rules.** §3b lists it as a ruling; this is why large shortages such as ROSIKA FORTE (Rs 4,760) and TYRO BR (Rs 4,255) are in Recount, not Pursue. The owner can move any of them.
- **Order of rules:** parked lines go to With me before the recount trigger, which keeps ETOZOX 90 and DOLOGESIC SP there. Consumables go to write-off before the trigger (BLADE −100, per §3).
- **Unpriced shortages go to Pursue, not write-off** (a write-off is never blind). Unpriced consumables go with the consumption group.
- **The owner's move wins over his earlier RECOVER word.** Moving a pursued line to write-off withdraws its claim through the existing sync.
- **Write-off lines are closed** (`status=closed`), as `/api/diff/<id>/decision` does. RECOVER lines stay open.
- **The dial's preview shows the move into or out of "within the allowance".** Small gaps are written off either way, so on today's data no width moves a line into or out of the pile. Today: normal would take 4 lines out of the allowance (Rs 423); very wide would add 3 (Rs 172).
- **"The report" is served by `report.desk` and the new record PDF.** `stock_report.html` was not touched.

### The walk: `WALK_S418 GREEN -- 82 of 82` (install log; same result in the dry run just before it)
- **Gates:** bhati 302, darpan 403 and shavez 403 on the page, the piles, move, write-off, record and accept. The owner gets the four-pile page.
- **The piles:**
  - every line is in exactly one place; no orthotic line (31 counted as elsewhere);
  - the three named items are first in With me; INTACOXIA-60 is in Recount; the crafted W418 lines start in their piles and groups;
  - both identities hold; the open figure = the sum of the lines shown;
  - **the hub's and the report's totals equal the desk's**; the hub page has the status card and none of the three retired steps;
  - the settings are seeded as ruled.
- **Move:** W418 SMALL TAB → Pursue is recorded (move row + audit) and decides nothing; back to the system's choice works; an orthotic line is refused.
- **Accept back** on a crafted parked line:
  - EXPLAINED (word + decision), FOUND, closed; shelf = Marg's 40, nothing short; audited;
  - open −Rs 300 and back +Rs 300 exactly; no Marg voucher;
  - a repeat writes nothing, and a line outside With me is refused; the seal's quantity is unchanged.
- **The dial:** very wide's preview (4 lines into the allowance, 0 in/out of the pile) is exactly what moving it did. The crafted W418 DIAL TAB moves between small gap and allowance. Moving it decides nothing, is audited old → new and appears in the record; back to wide restores the piles; a bad value is refused.
- **Write off this pile:**
  - refused with no arm, after 11 s, and when the pile changed after the tap;
  - then all 92 lines of the pile (89 real + 3 crafted) → WRITE_OFF + closed, and nothing outside it touched;
  - voucher round = exactly those lines, ≤ 6 a voucher, on Amir's board; the run is frozen with its groups, rules and round;
  - a repeat does nothing twice, and a new tap on the empty pile is refused.
- **Pursue:** the S228 sheet is exactly the 12 unsent Pursue lines (the 11 real + W418 BIG TAB).
  - S227/D389 hold: md5 = the fingerprint, the PDF is there, a second tap is refused, the S228 board and the recovery door still work;
  - RECOVER is written and the line stays open; the claim is raised at once; Darpan answers it on Stock milaan (open → contacted, audited); the desk shows the answer.
- **Recount:** all 33 lines asked (the 32 real + W418 RECOUNT TAB).
  - They show on Stock milaan without the Marg figure or the first count. His 9 patte 5 goli (95 units) lands, audited.
  - The line re-piles to write-off / small gap (5 short, Rs 10). A repeat writes nothing; others are refused; an item not asked is refused.
- **The record PDF** carries the totals, the rules, each group item by item and the rule changes. The older routes and doors all still answer.
- **Negative control** (the same scenario on the box as it was, on its own scratch copy): **12 of 18 red**. There were no piles route, no four-pile page, no single figure, and no item filter on the voucher round. The 6 green ones are the kept-route checks and bhati's gate (302 either way).

### Earlier walks on the patched files
**S404: 65/65**, on `finance.db.bak_S412_20260926_140429` (the 14:04 backup, as S414/S417 ran it). **S403: 52/52**, on `finance.db.bak_S414_20260926_174505` (as S417 declared). The walks were not edited. Before placing, the whole installer ran once more with `DRY=1`, placing nothing; everything was green.

### Backups, restart, health
- `finance.db.bak_S418_20260927_054217` (backup API).
- `.bak_S418_<from8>` beside the five replaced files: stock_app 586ae78a, stock_hub 68d11419, stockmatch.py d37c674b, stockmatch.html c5db7067, stock_loss 0d772034. `loss_piles.py` is new, so undo removes it.
- `systemctl restart clinic-finance` only; it is active.
  - Local and public `/finance/healthz` answer 200.
  - `/finance/stock/page/loss`, `/finance/stockmatch` and `/finance/stock/page/hub` answer 302 (login gate, expected).
  - The journal shows only the restart's two "Worker was sent SIGTERM" lines.
- clinic-portal is untouched and active.
- The build lock was held by S418 from 05:42:17 IST until this report, then removed.

### After publish
- `PUBLISH_ALL.bat` produced commit `72a1127` (05:49:37 IST); the phone gate was clean and origin was verified.
- On the box, `git pull` brought HEAD to 72a1127.
  - `md5sum -c` on the repository kit gave 9/9 OK.
  - `diff -r` of the repository kit against the kit that ran said **IDENTICAL**.
  - The repository installer answered **ALREADY INSTALLED**.
- The kit ran from `/tmp/s418kit/` with `KITS=/root/deploy/repo/deploy_kits`, because it needs the S403/S404 kits beside it.

### Not done / outside the brief (noticed)
- **The publish swept four files not from this build:** `deploy_kits/GAS_CURRENT/ClinicCallbackTracker/Dashboard.html`, `.../WebApp.gs`, `deploy_kits/GAS_CURRENT/READ_ME.md` and `deploy_kits/GAS_CURRENT/SUMS.md5`. They were changed in the working tree by someone else during this build, and PUBLISH_ALL publishes everything pending by design (as in S414/S417). I did not open or change them; the clinic chat should confirm they were meant to go out.
- The server's repository clone has stray `__pycache__` folders in `deploy_kits/S413_SLIP_PICKER/` and `deploy_kits/S416_BUNDLE_ALLOWLIST/`. They are untracked, from earlier runs; I left them.
- `stock_diffs.html` (the cause chips) and `stock_desk.html` (the Decision desk) still exist and answer. They are only off the hub's step list, as ruled. The S228 tick/share routes are kept and used by the Pursue pile.
- `stock.accept_back_by` can include Darpan, but only through the desk's API. There is no Accept-back button on his Stock milaan yet; add one if the owner widens it.
- The Recount pile is large (32 lines): 10 surpluses and 22 shortages, 20 of which are there by the 50-unit trigger. If the owner wants the big shortages in Pursue instead, raising `stock.recount_trigger` on the desk re-piles them.
- `claim_line.short_qty` is in raw units, so Stock milaan's "Bina bill?" shows "36 kam" rather than strips.
- No permission prompt was hit; nothing was installed on the box beyond the six files and the settings.
