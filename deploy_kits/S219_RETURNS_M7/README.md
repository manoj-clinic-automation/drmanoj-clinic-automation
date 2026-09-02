# S219_RETURNS_M7 — the returns line: a stub pool cannot corroborate

**The finding is the owner's.** `CN00184`, 27-Aug-2026, ₹1,080 — a sale return
that reached Darpan's worksheet carrying the verdict **NEVER BOUGHT**. That is
an accusation about a patient. It was drawn from nothing.

## What was actually wrong

The return was attributed to `WALK-IN` — one `patient_ref` row, reserved by the
schema, that carries **2,116 sale rows and 121 return rows** belonging to no
one in particular. `audit_return()` looked for that "patient's" earlier
purchases of the item, found none in a pool that is not a person, and said so
in the loudest words it has.

The module already refused this exact mistake when a return had **no** patient
("never bought" would be a statement about nobody). A stub identity passes that
test while being the same mistake wearing a name.

## What the Marg register says — measured, 01-Apr → 02-Sep-2026

The owner exported the full sale-return list. 197 credit notes, ₹68,099.

| | count | value |
|---|---|---|
| **credit notes with NO patient name** | **0** | — |
| carrying a clinic ID | 70 | ₹31,564 |
| **carrying NO clinic ID** | **127** | **₹36,535 · 53.6% of the return money** |

There is no such thing as an unnamed credit note. Marg has known the name every
single time. What is missing is the **ID**, and the break is dated:

```
Apr 2026   ID   0   no-ID  43        the counter did not capture IDs at all
May 2026   ID   0   no-ID  36
Jun 2026   ID   2   no-ID  30
Jul 2026   ID  31   no-ID   8        <- capture begins
Aug 2026   ID  33   no-ID  10
Sep 2026   ID   4   no-ID   0
```

So the 109 ID-less returns before July are **structural, not a lapse**, and
chasing them would spend a hundred hours to fix a condition nobody caused. The
real lapses are the **18 from July onward — ₹4,614**, of which **8 carry a
mobile the system can resolve by itself**. The human worklist is **10 returns,
₹1,760**, plus four mistyped identity fields. That is one sitting, not a
project.

`CN00184` is in the recoverable eight: **a name and a mobile, no clinic ID** —
and the same mobile appears again on `CN00129`, 20-Jul. A repeat, identifiable
patient, called NEVER BOUGHT.

## What this kit changes

| file | change |
|---|---|
| `finance_returns_audit.py` | a stub-attributed return reads **"identity needed"**, never a money verdict · `_stub_identity()` (a lookup on the schema's own reserved value) · DISCOUNTED RETURN still fires on such a row, because gross-vs-net needs no patient · the full mobile when the column exists (D356) |
| `darpan_app.py` | "identity needed" joins the two verdicts already excluded from the flagged **count** — it stays on Darpan's desk as a question |
| `finance_approvals.html` | "identity needed" reads **amber**. The badge ladder's final else is red, so an unknown verdict arrived in exactly the colour this change exists to remove |
| `darpan_app.py` | **the cutover**: returns before `returns.act_from` (default 02-Sep-2026) keep verdict and money but raise no task and inflate no counter |
| `finance_app.py` | escalation: a **real** flagged return now reaches the **owner**, not only Darpan |
| `finance_returns_escalate.py` | *new.* One `recon_exception` per day. Never before the cutover. Never for "identity needed". Never re-opens a decision the owner made — unless the set of flagged bills has genuinely changed |

## THE PAST IS ACCEPTED — the owner's ruling, 02-Sep-2026

*"Bury the historical data and take it as accepted."* Nothing is deleted: every
one of the 197 returns keeps its verdict, its money and its place in the list,
because that history **is** the baseline any detector must be calibrated
against. What stops is the *work* — no task, no counter, no alarm for a day
before the line. The date lives in `setting['returns.act_from']`, so he can
move it without a code change.

## TWO CORRECTIONS TO THE RECORD, MADE THE SAME DAY

1. **Three-digit clinic IDs are REAL.** This kit's first draft called `104` and
   `523` "cut or mistyped". Docterz has *Chetna* for ID `104` and the books
   agree. The claim was inferred from 68 four-digit examples and never checked
   against the master — the same fault as F-208. Withdrawn.
2. **What the August check actually found is worse.** Five of 43 August returns
   (12%) carry an ID that belongs to **someone else** — `762` is Daljeet Singh,
   the return is Paramjeet Kour's; `638` is Saloni Shrivastav, the return is
   Samreen Rehman's. `finance_ingest.resolve_patient()` says so in its own
   docstring: *"Clinic ID first, name only as a hint."* The name is never
   compared, so a wrong ID attaches a stranger **silently**, and every audit
   afterwards judges her returns against his purchases with full confidence.
   WALK-IN at least announces that it does not know. **This kit does not fix
   that** — it is an ingest change on the money path and needs the owner's OK.
   It is the first item of the next session.

**No money moves. No row is hidden. Every return on a real patient is audited
exactly as before.** Only the verdict on a pooled identity changes — from an
accusation into a question.

## Proof

`selftest_returns_m7.py` — **55/55 green**. It does not test hand-written code:
it copies the live files, runs **this kit's own patchers** over them, imports
the result and exercises that. Every patcher is exact-once, backed up, compile-
checked with automatic restore, and idempotent.
