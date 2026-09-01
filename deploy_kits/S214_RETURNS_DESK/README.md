# S214_RETURNS_DESK — the counter return flow, "Vaapsi Desk" (kit 1 of 2, v2)

**v2 — the owner's live walk, same evening:** ITEM-FIRST. Staff never touch
bills: one picker of everything the patient ever bought, quantities in the
product's OWN units with the strip conversion shown, a stepper (१ मरीज →
२ दवाएँ → ३ पर्ची) with no dead ends, the selection always visible in a
fixed bottom bar, and the BACKEND allocating returned units to real bills
(newest purchase first — the allocation that favours the patient) behind a
प्रोसेस-हो-रहा-है prompt. Bills resurface only on the printed slip, as
evidence. Ruling (a): the slip carries decisions + refusal reasons only;
internal flags stay internal; a two-line policy footer states the 2-month
window (per medicine, from ITS OWN sale date) and the request to return
promptly from the latest purchase. समायोजन → "Adjust (नई ख़रीद में)".

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

Selftest **27/27** (sandbox; v2 — the unit_role CHECK is now IN the synthetic schema and the seeder is exercised against it, after the first install was rightly refused by that constraint). Walk **14/14 on the restored 31-Aug backup**: real patient, 14 medicines
aggregated and priced in the picker, the server allocated a real bill to
the return, mixed slip saved (GREEN accepted + opened RED refused and
FILED), source db untouched.

## Install

`INSTALL_ONE_PASTE.txt` — one line on the VPS: pin-check the live
finance_app (`e19c3f19…`), copy, selftest on the box, seed roles, mount,
walk on a /tmp copy, restart, print the new pins. Rollback: the patcher's
timestamped `finance_app.py.bak_S214_desk_*`; the desk tables are additive
and inert without the mount.
