# S282_LINE_OWNER — a purchase line with two possible owners goes to the one ITEMWISE names

**Session 262 (the Sanjeevni project's first) · 17-Sep-2026 · repairs F-494.**

## What was wrong

Marg numbers purchase bills **per vendor**, so two suppliers can share a bill number on one day.
**Bill 160 of 1 September exists twice** — DAANSHI PHARMA and KEDAR PHARMACEUTICAL. The BILL/ITEM WISE
export prints no supplier; its lines are placed by (bill number, date), and when that names two bills
the line cannot be placed. **Five lines, ₹17,776.68, sat in September's month total and on nobody's
payment sheet.** One occurrence in 1,551 lines; the other fifteen shared bill numbers resolve because
their dates differ (F-494).

## The witness that was already there

The ITEM WISE export **does** carry the supplier, and the same five lines are in it under their
owners — same bill number, same date, same item, same amount. Read from last night's database copy:

| line | item | ITEMWISE says |
|---|---|---|
| DENGEN PLUS | ₹6,400.80 | DAANSHI PHARMA (its bill: ₹5,377.00 net) |
| MEG QCS · ASTOFEN SP · PATOPAN DSR · TYRO BR | ₹12,400.00 | KEDAR PHARMACEUTICAL (its bill: ₹12,400.00) |

## The rule

**A line whose (bill, date) names more than one supplier is given to the ONE supplier the ITEMWISE
export names for that exact (bill, date, item, amount) — provided that supplier is among the
candidates.** None, two, or a stranger: the line stays unowned and is named in the output. A bill with
one owner is not this rule's business (rev 2 of `_redate_lines` already handles it).

## The change

One anchored line at the end of `_redate_lines()` — `_line_owner_s282(con, by_no)` — and one helper
appended to `purchase_app.py`. It runs after every purchase push, so the next collision heals itself.
`repair_f494_s282.py` is the same rule run once over `finance.db` for the five lines already stored,
so they do not wait for the next push.

## The proof

- **20 offline checks, 0 failed** (`selftest_s282.py`, run in two places against the live bytes
  `3535dc97…` from the 17-Sep nightly bundle): the fixture holds the F-494 shape plus five cases that
  must NOT move (no witness; two witnesses; a stranger witness; a one-owner bill; same item at a
  different amount) and one that must (NULL amounts on both sides); the patcher's anchor matches once,
  a wrong `--from` is refused with nothing written, the patched file compiles, a second run says
  ALREADY PATCHED, and **the helper lifted out of the patched file gives the same answers as the
  one-off script**.
- **Dry run on a copy of the 17-Sep nightly database, on manojz:** before 5 lines / ₹17,776.68 →
  placed 5, left 0 → after 0 / ₹0.00. Per vendor afterwards: DAANSHI 1 line ₹5,376.68, KEDAR 4 lines
  ₹12,400.00 — the bills' own amounts.
- **The installer rehearsed against a fake root:** patch → compile → rehearsal on a DB copy → backup →
  live pass → pins read back; the second run stops at ALREADY INSTALLED and places nothing.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S282_LINE_OWNER/install_S282_LINE_OWNER.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/purchase_app.py` | `3535dc978d4ec53846368c8772347a50` | `216a0cd95afad73eecbc484683892ca3` (predicted; the installer refuses if the read-back differs) |

Backups left on the box: `purchase_app.py.bak_S282_3535dc97` and `finance.db.bak_S282`. Keep both
until September's payment sheet has been checked and locked.

## What it does not do

It does not touch the ITEMWISE lines, the bills, the payment sheet's code, or any screen. It changes
no bytes on manojz. **The root cause — a table keyed as if a bill number were global — is not
redesigned here;** that is the sale-lines/one-store work (Book §11.4 3e), and this kit is the smallest
repair that puts the money on the right sheet now.

| file | what |
|---|---|
| `patch_line_owner_s282.py` | the anchored patch; refuses on any surprise; prints the read-back pin |
| `repair_f494_s282.py` | the one-off pass; `--dry-run` reports only |
| `selftest_s282.py` | the 20 checks |
| `install_S282_LINE_OWNER.sh` | pins, backup, patch, rehearsal, live pass, restart, roll back |
