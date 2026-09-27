# S418_LOSS_DESK_PILES — the owner's Loss desk as four piles, one tap each (D631, F-641)

**Sanjeevni project · session 283 · 26/27-Sep-2026 · brief `claude_code_briefs/S418_LOSS_DESK_PILES.md` · runs after S417.**

## What the owner asked for
"These products were kept somewhere else and were not counted. Why make such a long path? I take it, it is there, it
should be accepted back into the system as it is. It is a very long list, very difficult to pursue ... it is not curated
for easy redressal for me." Small shortages after six months without a proper count are normal shop loss, written off
as a group, documented, never line by line.

## What was built
**`/finance/stock/page/loss` rebuilt** (`stock_loss.html`, English, phone-first). Every open line of the round
(medicines and consumables — the orthotics stay on S404's section) sits in exactly ONE pile; the system's suggestion is
the starting pile, the owner's **→ pile** menu moves any line (recorded, decides nothing):

1. **With me / back in store** — parked lines first (ETOZOX 90, HYORTH XL, DOLOGESIC SP head the list). One tap
   **Accept back** writes the same rows the older doors write: the lane word and the S221 decision `EXPLAINED` (note
   "owner: back in store"), `stock_diff.cause = FOUND` ("turned up later" — the existing vocabulary), the line closed,
   and a shelf fix = Marg's figure in `stock_shelf_fix`, audited. A repeat writes nothing.
2. **Write off as normal loss** — three documented groups: *within the allowance* (`_allowance_units()`, per item,
   turnover-related, × `stock.allowance_scale`), *small real gap* (beyond the allowance, under
   `stock.small_gap_ceiling_p`), *clinic consumption* (consumables, `stock.consume_auto`); plus *your choice* for a line
   he moves in. **Write off this pile** arms for 10 seconds ("Yes, write off N lines"); the second tap writes every line
   of the pile off (`WRITE_OFF`, closed), freezes the run (`stock_writeoff_run`: the groups item by item, the rules in
   force, an md5) and makes **Amir's Marg voucher round for exactly those lines** in the same call
   (`_voucher_make(..., items=...)`, at most `stock.voucher_batch` lines a voucher). A stale token, a pile that changed
   after the first tap, or a repeat writes nothing. The **allowance dial** (normal / wide / very wide) shows what each
   width would move between "small real gap" and "within the allowance" (and in or out of the pile); moving it decides
   nothing.
3. **Pursue** — every real gap of `stock.pursue_floor_p` (Rs 1,000) or more at MRP, unpriced lines, and what he moves
   in. **Make the sheet for Darpan** marks the unsent lines `RECOVER` (open) and ticks them, then calls the S228 sheet
   route itself (`api_loss_share`, unchanged: frozen JSON, md5, PDF); the claim queue follows at once, and Darpan
   answers on his Stock milaan (**Bina bill?**, the claim queue's own `answer()` door). The line stays open until settled.
4. **Recount** — the lines the count cannot be right on (the `recount` lane) and shortages or surpluses of
   `stock.recount_trigger` (50) units or more (INTACOXIA-60 +719 is here). **Ask Darpan to recount** puts them on his
   Stock milaan as **Phir se gino** with a count box (patte + goli), blind — no Marg figure, no first count. His figure
   is a shelf fix; the line re-piles itself by the same rules.

Over-on-shelf lines sit under a collapsed "Over — never a loss" note (→ Recount only). The lane names, causes and
decisions are never shown as vocabulary. The **record** at the foot lists the written-off groups item by item, each
write-off tap, back in store, every rule change and every tap on the desk; **the record PDF**
(`/api/loss/<cid>/record.pdf`, the estate's own stdlib writer in `pad_receipt.py`, used read-only) prints the same.

**THE five totals, defined once** (`loss_piles.totals`): *still open* = with me + write-off pile + pursue + recount;
*back in store / explained* (valued at the count day); *written off* (by group); *short at the count* = open + back +
written off. The desk, the hub's status card (`hub.desk`), the report API (`report.desk`) and the record PDF read the
same function (F-641: the desk said Rs 84,349 and the hub Rs 64,355 for the same count).

**The hub** (`stock_hub.html`) is a status card with links: the five totals, *Open the Loss desk*, the record, Amir's
board, Darpan's Stock milaan. Steps 3–5 (cut the next list, type Darpan's answers, the Decision desk) left the owner's
path — one step "The Loss desk — four piles" stands in their place; their routes are all kept for audit and reading.
The swaps, the vouchers, the proof, the claims and S404's orthotic section are unchanged (renumbered 2, 4, 5, 6).

**Every ruling is a setting** (the collapsed Settings card, owner-only, each with a hint; `setting` table; every change
audited old → new in `audit_log` and listed in the record): `stock.allowance_scale` (seeded 2 = wide),
`stock.pursue_floor_p` (Rs 1,000), `stock.small_gap_ceiling_p` (blank = the floor), `stock.recount_trigger` (50),
`stock.voucher_batch` (6; `_voucher_batch_size` reads it first), `stock.accept_back_by` (owner), `stock.consume_auto`
(on), `stock.rolling_section_items` (90) and `stock.rolling_day` (Monday) for S419. The piles re-compute on every read.

**The shelf layer** (`loss_piles.apply_fixes`, called from `_pad_report_data` after the swaps): a corrected shelf
figure is laid over the line at read time, the count-day figures kept on it — the count and its seal
(`stock_diff` quantities) are never touched, exactly like the S299 swaps.

## Pins (FROM read on the box 27-Sep-2026 05:03 IST → TO; built by `make_s418.py` from the live bytes, anchored edits)
| file | FROM | TO |
|---|---|---|
| /root/finance/stock_app.py (S404's TO) | 586ae78ae6437f806692c2a1e4eeeb37 | cf464882e49865f38153e1df6218301d |
| /root/finance/stock_hub.html (S404's TO) | 68d11419e7fb9a8e5fec74095b60b255 | bb8741fa7671399f9c495c75946d7c11 |
| /root/finance/stockmatch.py (S404's) | d37c674b6b7435966f048503c40622df | d5f9392fea4247b37705e865e1c242cb |
| /root/finance/stockmatch.html (S404's) | c5db7067fc18cf9a6bd29c48f4c1540d | 9a090e03c954bfda5a787e8d834f275c |
| /root/finance/stock_loss.html (whole page, in the kit) | 0d77203482d668d8d00e5145682c841f | 16cdddaa6363ccc8da0278fa5d4635a3 |
| /root/finance/loss_piles.py (new) | — | 3b6554f86507509e0b1893129e748274 |

Not touched: `stock_amir.html` (c2ea41b2 — the new rounds show on Amir's board as any round does), `stock_diffs.html`,
`stock_desk.html`, `claim_queue.py`, `pad_receipt.py` (used read-only), `finance_app.py`, `portal.py`, the cron.
Restarts `clinic-finance` only. `finance.db` is backed up first; the tables `stock_pile_move`, `stock_shelf_fix`,
`stock_recount_ask`, `stock_pile_arm`, `stock_writeoff_run` are additive; `seed_s418.py` writes the settings only where
absent, after a green restart.

## Proof
`walk_s418.py` — the REAL patched app over a SCRATCH copy of the live database, the real round 1, lines found by key,
crafted lines keyed W418*: the gates (bhati, darpan, shavez refused on every door) · every line in exactly one place, no
orthotic, the three named items first in With me, INTACOXIA-60 in Recount · the totals' identities, the hub's and the
report's totals equal to the desk's · the → pile menu moves and records, decides nothing · Accept back (EXPLAINED,
FOUND, closed, shelf = Marg, audited, totals move by exactly its value, no voucher, a repeat writes nothing) · the dial's
preview equals what moving it does, decides nothing, audited · the 10-s gate, a changed pile refused, the write-off of
every pile line and nothing else, WRITE_OFF + closed, the voucher round of exactly those lines ≤ 6 a voucher on Amir's
board, the frozen documented run, a repeat does nothing twice · the sheet for Darpan is the S228 sheet (md5, PDF, the
second tap refused, the S228 board and recovery door), the claim raised and answered on Stock milaan · recount lands on
Darpan's page blind, his figure re-piles the line, a repeat writes nothing, others refused · the record PDF · the older
doors kept. **Negative control:** the same scenario on the box as it is goes red. Then **S404's walk** (on the
14:04 backup of 26-Sep) and **S403's walk** (on the 17:45 backup) are re-run on the patched files.
`figures_s418.py` prints the desk as the owner will first see it (on a fresh scratch copy after the install).

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S418_LOSS_DESK_PILES/install_S418_LOSS_DESK_PILES.sh
```
Undo: put back the five `.bak_S418_<from8>` files, remove `/root/finance/loss_piles.py`, `systemctl restart
clinic-finance`, healthz 200. The seeded settings and the new tables are data and stay (the old code reads only
`stock.allowance_scale`, which then widens the old lanes' allowance — say so if it must go back to 1); the database
backup is used only if the owner says so.
