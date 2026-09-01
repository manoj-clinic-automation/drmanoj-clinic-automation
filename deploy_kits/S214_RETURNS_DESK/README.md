# S214_RETURNS_DESK — the counter return flow, "Vaapsi Desk" (kit 1 of 2)

**STAGED, NOT INSTALLED.** Design signed by the owner 01-Sep-2026
(`03_WORKING_PAPERS\S214\S214_COUNTER_FLOW_DESIGN_DRAFT.md` — his rulings +
six defaults, all built as stated). Supersedes the S187 D-R stage design
where the two differ; the owner's 01-Sep rulings win.

## What it is

A Hindi, tap-first counter screen at **`/finance/returns/desk`** where named
reception staff take medicine returns in under a minute: find the patient →
the WHOLE purchase history (never just the last bill) → tick items →
item-wise verdicts (GREEN accept · YELLOW accept-as-courtesy + silent flag ·
RED refuse at counter: expired / opened-damaged / not ours) → close by CASH
(payer named) or ADJUST into the new sale → printed slip in plain Hindi.
**Everything is filed, refusals included** — today a refused return leaves no
trace. Flags (late >60d · bill not traced · qty over bought · frequent
returner ≥3/30d · refund ≥ ₹2,000 · staff override) are internal only.

Server-authoritative verdicts (the S213 lesson): the page proposes,
`returns_desk.py` re-judges every line from the database before saving.

## What it deliberately does NOT do (kit 2, already designed)

No Marg write, no money-ledger write. The refund is logged on the slip; the
money reaches the books through the credit note Amir enters in Marg later
(same day preferred). Kit 2 pairs slips ↔ CNs at the next export and flags
both orphans to the owner's panel. Every slip is stored `match_state=open`
ready for it.

## Pieces

| file | role |
|---|---|
| `returns_desk.py` | blueprint; `init(app, db, require, unit)` — the S208 stock_app pattern; owns `return_visit`/`return_line` (additive, lazy) |
| `returns_desk.html` | the counter page + print-format slip |
| `seed_desk_roles.py` | idempotent `unit_role` rows: alisha/shivani/shavez get role `viewer` on medical — the schema's CHECK allows only maker/checker/viewer, and no other finance route accepts viewer, so it grants the desk and nothing else; darpan (maker) and manoj (checker) already pass |
| `patch_finance_app_returns_desk.py` | guarded mount into the live finance_app.py — exact anchors, singleton checks, backup, py_compile with restore-on-red |
| `selftest_returns_desk.py` | 20 invariant checks, synthetic db, real routes |
| `WALK_returns_desk.py` | the live-shape walk on a THROWAWAY COPY of a real finance.db (refuses the real book by name); 11 checks |

## Proof so far

Selftest **22/22** (sandbox; v2 — the unit_role CHECK is now IN the synthetic schema and the seeder is exercised against it, after the first install was rightly refused by that constraint). Walk **11/11 on the restored 31-Aug backup**:
real patient with 16 bills, full history with lines, mixed slip saved
(GREEN accepted + opened RED refused and FILED), source db untouched.

## Install

`INSTALL_ONE_PASTE.txt` — one line on the VPS: pin-check the live
finance_app (`e19c3f19…`), copy, selftest on the box, seed roles, mount,
walk on a /tmp copy, restart, print the new pins. Rollback: the patcher's
timestamped `finance_app.py.bak_S214_desk_*`; the desk tables are additive
and inert without the mount.
