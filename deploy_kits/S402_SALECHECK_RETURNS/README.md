# S402_SALECHECK_RETURNS — Bhati sees the day's sale returns at a glance

**Sanjeevni project · session 283 · 25-Sep-2026 · builds on S400 (live since 20:45 IST).**

## What the owner asked for
"Bhati should also be seeing the sales returns of the day ... collapsible, expandable: sale returns, their number, their total
amount; expand to the bill number, name, and amount. More granular details are not required in Bhati's app." Label: the
English words **Sale return** (never "Vaapsi").

## The change (Bhati's page only)
- **In a day:** right after the Marg bills, one block, **collapsed by default** — `− Sale return — 3 · ₹1,240` → tap → one row per
  return: **bill no · name as the system shows it · amount** (positive, whole rupees, Indian grouping). No medicine lines, batch,
  expiry or quantity for returns. A day with no return reads `Sale return — 0` and does not expand. This block replaces the S400
  returns line, so returns appear once. The figures are the owner's day panel's own (`sale_bill.is_credit_note` of that day).
- **On the card in the list:** `Sale return 3 · ₹1,240`, omitted when 0.
- Nothing else: no new write, no table, no change to the owner's pages, to access, or to anyone else.

## Pins (FROM → TO; built on the box by `make_s402.py` from the live bytes, anchored edits)
| file | FROM (S400) | TO |
|---|---|---|
| /root/finance/sale_check.py (v1.0 → v1.1) | 81cccad3c48a894298b3694a7b3b5118 | 92ca5cb2d3a4388bbf6a29e35af2d492 |
| /root/finance/sale_check.html | 4202d11baee4c9309a518e3aed8cf817 | 9c70af26456092285a9545083365bfff |

Restarts `clinic-finance` only. `finance.db` is backed up first by rule; nothing in it changes.

## Proof
`walk_s402.py` — 16 checks on a scratch copy of the live database, own rows 2099-12-05 (two credit notes, 300 + 200, one with
a medicine line) and 2099-12-06 (none): the block reads 2 · 500 with rows of exactly bill · name · amount and no item field; the
0 day reads 0 with no rows; the card carries the same count/total; the owner's panel reads the same for the walk day AND for the
real unapproved day; every S400 §6 refusal still holds. **Negative control:** the S400 files (a copy of the box) carry item fields
on a return row, no card line, no block. Then **S400's own walk (63 checks) is re-run on the patched files** against a rebuilt
pre-S400 control and must stay green — the installer does both.

## Run
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S402_SALECHECK_RETURNS/install_S402_SALECHECK_RETURNS.sh
```
Undo: put back `sale_check.py.bak_S402_81cccad3` and `sale_check.html.bak_S402_4202d11b`, restart `clinic-finance`.
