# S285_SUPPLIER_CHECK — a bill under the wrong supplier is caught on Amir's own screen

**Session 262 (Sanjeevni project) · 17-Sep-2026 · the owner's ask of this morning, built the same hour.**

## The fault it is for

In August Amir entered a purchase under the wrong supplier. It was found later, by a person, and
corrected by hand. Nothing in the system could have seen it: Marg is consistent with such a mistake —
the bill-wise, supplier-wise and item-wise exports all faithfully repeat the wrong name, and the
month's cross-checks all pass. **The only witness is history:** 1,551 purchase lines since April, and
for almost every item exactly one supplier has ever supplied it. In the owner's words, *"another
supplier supplying the same item is extremely rare."*

## The rule

For each bill still waiting for his *Theek hai / Theek nahi*, for each item on it: **if this supplier
has never supplied the item before, and another supplier has supplied it on two or more earlier
bills, the bill carries a warning** naming the item, the usual supplier and how many bills. A
never-bought item raises nothing (the new-item list already does). A genuine second source trips once;
after he marks it *Theek hai* that pair is history and it never trips again. Only live exports count,
for the bill's items and for the history.

**Measured on the 17-Sep nightly database: of 226 bills July–September, 5 would have warned** — one in
July, three from L.K. DRUG HOUSE in August (14, 21, 24-Aug), one in September. That is the noise level:
about one bill in forty-five, and at least some of those are the real thing.

## Where he sees it, in his words

On the bill itself, in step 4, above *Theek hai*, in Hindi:

> ⚠ **TYRO BR** pehle hamesha **KEDAR PHARMACEUTICAL** se aaya hai (8 bill). Is bill par **DAANSHI
> PHARMA** likha hai — Marg mein bill dekh lijiye.

Under *Theek nahi* one more reason: **Supplier galat likha.** It is not a claim for Darpan to chase —
the vendor owes nothing; it is Amir's own correction in Marg — so it is deliberately not in
`CLAIM_REASONS`. He corrects the bill in Marg, re-exports, and:

## The clear — the part that had never worked

A corrected bill comes back under the right supplier in the next export, and the wrong one is gone
from Marg. Until now the wrong one **stayed on his list for ever**: its export row lives on,
superseded, and the list never asked whether a live export still carried the bill. It asks now. The
corrected bill appears as a new one; the wrong one disappears by itself, with its flag. A bill first
seen in an older export and still in the live one keeps its earlier *seen* day, so *pichhla baaki*
still means what it meant. (The selftest proves this against the untouched file: before, the vanished
bill haunted the list; after, it is gone and nothing else moved.)

## The change

Five anchored edits and one helper in `amir_day.py`: the reason; the live-export condition in
`_bills()`; the warning computed for today's and carried bills (never for flagged ones); the warning
rendered in `_bill_block()`; one stylesheet rule. No table, no setting, nothing on manojz.

## The proof

- **36 offline checks, 0 failed** (`selftest_s285.py`): the patcher's five anchors, refusal, compile,
  idempotence; then **both the untouched and the patched module driven as code** over one fixture —
  the seven bill shapes in the file's own docstring, the new reason saved and raising no claim, the bill
  moving to flagged, a superseded history line not counting, no `purchase_line` table not crashing.
- **Rehearsed on the 17-Sep nightly database, on manojz:** the list is identical before and after
  (every September bill is answered, so nothing vanished — no bill exists today only in a dead export),
  and the warning rate is the 5 of 226 above.
- **The installer rehearsed against a fake root**; ALREADY INSTALLED on the second run.

## Install — one line on the VPS

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S285_SUPPLIER_CHECK/install_S285_SUPPLIER_CHECK.sh
```

| pin | from | to |
|---|---|---|
| `/root/finance/amir_day.py` | `a9f2062267ebac59e02fdb0f88e775de` (S246) | `b3c20319c4808ebc64bec197c951468c` (predicted; refused if the read-back differs) |

Backup on the box: `amir_day.py.bak_S285_a9f20622`. Rolling back is copying it over and restarting
`clinic-finance`; the one new reason already saved on a bill, if any, reads back as its code.

| file | what |
|---|---|
| `patch_supplier_check_s285.py` | the five anchored edits + helper; refuses on any surprise |
| `selftest_s285.py` | the 36 checks (needs flask importable — it drives the real module) |
| `install_S285_SUPPLIER_CHECK.sh` | pins, backup, patch, compile, restart, roll back |
