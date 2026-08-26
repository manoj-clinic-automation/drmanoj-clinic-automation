# S202_D349B — D349: one lane rule, one place

**Session 202 · the first build under D349 · `staff_ledger.py` `eaa305cb…` → `9e764f80…`**

## The fault, in the owner's own words first

> *"why is darpan drawer assoc ledger not updated"* — and while answering that, the served
> statement page was read, and it said something that was not true.

`/ledger/statement` described Darpan's Rs 20,000 SPECIAL as **"recovers in full at the 2026-08
close"**. It does not. The close's **schedule lane** runs first and takes **Rs 8,000**, then
4,000 × 3. Meanwhile `/ledger/advances` showed the correct 8/4/4/4.

**Two pages, same advance, opposite answers about the owner's next payroll.**

## Why it happened — and why no test caught it

The test for *"is this a quota advance"* existed **twice**:

```python
close_month()   line  913     against_month AND not interest AND instalment == amount
/statement      line 2474     against_month AND not interest AND instalment == amount
```

Identical — which is exactly why it was wrong. **In the close, the schedule check is implicit in
the ORDERING:** the schedule lane runs first and *removes* its advances from the working set, so by
the time the quota test runs it can no longer see a scheduled advance. The display had no ordering.
It copied the condition faithfully and inherited none of the protection.

**The close was always tested.** The SL6 selftest even builds an advance with Darpan's exact shape
(Rs 20,000 as 8,000 + 4,000 × 3) and asserts the lane collects 8,000. **The display was never
tested at all** — F-181's lesson, one screen over: *the defect lived in a dimension no assertion
described.*

## The fix

One function, `advance_lane()`, defined once beside `advance_schedule()`. `close_month()` partitions
by it; the statement card describes it.

**Precedence deliberately matches the close, schedule before interest** — because this function must
describe what the code *does*, not what would be tidier. A scheduled loan is collected by the
schedule lane today, and the function says so.

A scheduled advance now renders its real plan:

> by agreed schedule — 2026-08: Rs 8000 → 2026-09: Rs 4000 → 2026-10: Rs 4000 → 2026-11: Rs 4000
> (it does NOT wait behind the loan, and it does NOT recover in full this month)

## No behaviour change to the close. None.

The partition is provably identical: the schedule lane already ran first, so the quota test could
never see a scheduled advance. **Only words on a page change.** No rupee moves either way — this was
always a display fault. Darpan's August deduction was going to be Rs 8,000 before this kit and is
Rs 8,000 after it.

## Proven before delivery

- **Offline selftest 294 → 301, +7 exactly.** The projection was written down before measuring.
- **The 7 new checks were run against the UNFIXED file and went RED** on the exact sentence that was
  wrong (`check 256 FAILED: the statement NEVER says a scheduled advance recovers in full`). They
  are not vacuous.
- **Selftest isolation proven with a canary data directory** — nothing was written outside it,
  honouring S200's rule that *a selftest which writes a live store is itself a live event*. The
  installer probes the new file with `LEDGER_DIR` pointed at a throwaway before touching anything.
- **The install gate was tested both ways**: it accepts a real 301 run and refuses a 294 one. It
  matches on ASCII only, because the pass line contains an em dash and a gate that refuses on an
  encoding quirk is a false alarm, not a safeguard (the `sqlite3` lesson from `S202_DARPAN20K` v1,
  earlier the same session).

## Install

```
cd /root/deploy/repo && git pull && cd deploy_kits/S202_D349B && bash install_d349b.sh
```

Expect `[5/8] new file selftest: 301 ✓ (was 294)` and `GREEN`.

Then open `https://followup.dr-manoj.in/ledger/statement?staff=Darpan` — the Rs 20,000 card must
show the schedule and must no longer say *"recovers in full"*.

## Reverse

```
cp -f /root/staff_ledger.py.bak_S202_D349B_<stamp> /root/staff_ledger.py && systemctl restart staff-ledger.service
```

## Still owed under D349

**S202_D349A** — the finance side: the same one-rule treatment for what a day's *difference* means,
the exceptions card rebuilt as the owner's inline reconciliation table (no page hopping), and the
four genuinely-unexplained old rows (12-Jun −8,487 · 3-May 34,245 · 2-Jun 690 · 9-May 665) separated
from the five that are merely unattributed bills.
