# S193_F6 — delivery note

**One kit, two payloads, one install run** (the "minimum runs" you asked for).
Closes **F-148** (the drawer→ledger bridge, F6) and **F-153** (the contra `against_month` fix).

## What it does

**F6 / F-148 — `finance_app.py` (the Staff-Ledger bridge).**
When the doctor **approves** a Sanjeevni (medical) day that carries a *salary-advance*
expense, the advance is now **posted to the Staff Ledger** as an `ADVANCE_ISSUE`,
attributed to that day's month, written **through the ledger's own writer** (not around it).
Approval is the post; entering the day is not. It is:

- **fail-loud** — if the ledger can't take it (e.g. the approver isn't a ledger checker, or
  the amount is above the ceiling with no signed application), the approval is **refused**,
  the day stays *submitted*, and nothing is committed. Money is never half-posted.
- **idempotent** — a re-approval never double-posts (`ledger_posted` is the guard).
- **ordered** — the ledger row is written first, then the finance row is stamped, so a crash
  leaves a *visible* ledger row to reconcile, never an invisible claim of a post that didn't happen.

**F-153 — `staff_ledger.py`.** `make_contra` now carries the original advance's
`against_month`, so a reversal nets *that* month's quota instead of leaking to the contra's
own entry month.

**F6b (the "drawer not touched until approval" question) needs no code** — per your ruling,
the drawer correctly reflects the cash the moment Darpan takes it; approval is what *sanctions*
and posts the advance.

## Verified offline (the F-87 remedy, done properly)

A seeded store was built to the **live shape** (`dev/`), the unmodified app baselined, and the
modified app **differentially** verified: **458/544 → 463/549 — exactly the 5 new F6 checks,
zero failures added.** Ledger selftest **287 → 289** (+2, F-153). Both `py_compile` clean.

## Install (one run)

Publish the repo (`PUBLISH_ALL.bat`), pull on the box, then on the box:

```
cd /root/deploy/repo/deploy_kits/S193_F6 && bash install_s193_f6.sh
```

The installer is self-gating and **rolls BOTH files back on any red**. Projections it checks:
ledger **287 → 289**, finance **550 → 555**.

### One thing to watch — step [6/9], the mapping preflight
The bridge posts *as the approving doctor*. That name must be a **checker in the ledger's own
`/root/staff_ledger/users.json`**. The installer prints, for each medical checker, whether he is
a ledger checker. If it prints **NO** for the doctor who approves Sanjeevni days, salary-advance
approvals will be **refused** (nothing breaks, the day just won't approve) until that ledger user
exists. If it prints YES, you're done.

## After GREEN
Pin the two new md5s into the KB Register (D321(d)):
- `staff_ledger.py` → `acd7b538ec9476f86e243c73eec3d3fd`
- `finance_app.py`  → `9b1afe4f13bec91bc9bb83e8f818a76b`

`dev/` (the reusable live-shape seed) closes the gap that blocked F6 at S192 — file it with the kit.
