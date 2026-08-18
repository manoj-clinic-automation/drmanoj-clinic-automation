# The Advance Pool — random advances, automated recovery (D329 candidate · S189)

**Design decided at S189 on the owner's directive: "ideate and decide and make such system."
Status: DESIGN, awaiting the owner's OK. Becomes the signed contract for the D3/B6 build.**

## The problem, in the owner's words

Darpan draws advances from the medical cash **randomly**. Later the accumulated amount is
"portioned off into instalment repayment", and a month's repayment "is foregone on request."
The advances are now logged (kit `S189_E1b`); what's missing is everything after the logging:
how they reach the salary system, how they are recovered month by month despite the randomness,
and how the month-end reconciles — with maximum automation.

## What already exists, read before designing (F-137's rule)

- **Finance** logs each advance structurally: `category_fixed='salary_advance'`, server-attributed,
  and approval marks it `PENDING_LEDGER_WIRING` — a slot built at S188 waiting for exactly this.
- **The Staff Ledger** (D258: one home per rupee) already runs monthly recovery with skips: the
  D250 loan — `min(instalment, everything owed)`, waterfall interest → interest-bearing →
  interest-free, skip button max 2/Indian-FY. **July's close proved it live to the rupee.**
- **The decisive constraint:** the waterfall recovers interest-free money LAST. A new ₹20,000
  advance folded into the loan would be recovered after ₹3.59 lakh of loan principal — years away.
  **Therefore advances get their own stream, parallel to the loan, not inside it.**

## The five decisions

**1 · ONE POOL, NO CEREMONY.** Every approved medical salary-advance joins Darpan's open
**Advance Pool** automatically. There is no manual "consolidation" step — the pool IS the
consolidation. "Portioning off" collapses into a single checker-set number (decision 2). The
randomness of when he draws stops mattering, because the pool absorbs any pattern.

**2 · RECOVERY = min(pool, advance_instalment) at every monthly close**, a second deduction line
beside the loan's, in the workbook's deduction order. `advance_instalment` is a **checker-only
setting** (proposed default ₹5,000/month), changeable at any time, every change logged as its own
ledger row — the doctor turns one dial, the engine does the rest.

**3 · THE RELAXATION, MIRRORED — and "foregone" gets both meanings.**
- **Advance-Skip** (checker-only button): this month recovers nothing, pool unchanged, **max 2 per
  Indian FY** — the loan's relaxation, mirrored exactly, but with **no ₹1,000 capitalisation**,
  because the pool is interest-free.
- **Advance-Waive** (checker-only): forgives an amount outright — the pool shrinks without
  recovery. No FY cap, but never silent: its own ledger row, with a required reason.
Loan skips and advance skips are **separate counters**; using one never consumes the other.

**4 · THE BRIDGE (B6), finally wired — push on approval, stage-style.** When the doctor approves a
finance day containing salary-advance expenses, finance pushes each to a new scoped ledger
endpoint (the D325 pattern: a dedicated token, one path only, generated ON THE BOX into both
systemd units — a token never transits chat, D328). The ledger row is written **approved with
provenance** (finance day + expense id) because the pressing finger was already the checker's,
seconds earlier. **Idempotent by finance expense id** — a re-push cannot double-enter. Finance
sets `ledger_posted=1 + ledger_ref` only on a confirmed reply; a failed push stays pending,
retries on the next approval, and is visible in the reconciliation card — fail-soft, never
fail-silent.

**5 · THE MONTH-END RECONCILIATION CARD**, shown in the ledger before every close:

```
opening pool  +  advances this month (each linked to its finance day)
              −  recovery to be deducted   −  waived
              =  closing pool
UNMATCHED: finance-pending rows with no ledger row  ·  manual ledger rows with no finance link
```

Unmatched items offer one-tap **LINK** (marry a manual ledger entry to its finance expense) —
which is precisely how the first-run case is handled: **the ₹20,000 you enter by hand gets LINKED
to its finance row, not re-posted.** The bridge never auto-posts anything that might already
exist; linking is the doctor's tap.

## The opening state — clean, because today made it clean

The Apr–Jun ₹40,000: recovered in the workbook era, **verified today, stays OUT**. The pool opens
at exactly the currently-unrecovered amount — after the 17 Aug entries, **₹20,000** — and every
rupee in it is traceable to a finance day with scans.

## Build plan (kits, D317 chain throughout)

| kit | system | contents |
|---|---|---|
| `S190_SL1` | staff_ledger.py | pool categories (issue/recovery/skip/waive/link), the `advance_instalment` setting, close-engine integration in the deduction order, the reconciliation card, the receive endpoint (scoped token, fail-closed if unset), statement view rows |
| `S190_F1` | finance_app.py | push-on-approval with confirm/retry, LINK support, `ledger_posted` truthfully set at last |
| token | both systemd units | generated on-box by the installer; never printed, never in chat |

Order: SL1 → token → F1. Each rehearsed offline (the rehearsal ledger given the live file's SHAPE
— F-140), projections written before measuring, exact integration read from the live ledger bytes
at build time, not assumed from this document.

## What this closes and what it explicitly does not

Closes: the `PENDING_LEDGER_WIRING` slot (S188) · the double-count hazard named in the E1a note ·
the "random advances" problem as a class. Does NOT touch: the D250 loan engine (proven, frozen in
behaviour) · the ₹10,000-style salary settlements (they are expenses, not recoverables — the menu
already separates them) · other staff (the pool is per-staff by construction; only Darpan's is
active, per the owner's ruling).

*Design S189 · becomes D329 on the owner's OK · builds as S190_SL1 + S190_F1.*
