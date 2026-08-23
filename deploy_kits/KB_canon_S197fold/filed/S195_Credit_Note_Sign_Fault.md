# S195 — The credit-note sign fault (18-Aug-2026)

**Kit:** `deploy_kits/S195_SIGN.tar.gz` (`902f783517fa41e0146505e1c0729f4b`)
`finance_app.py` `dfc0d19d3b1a32b26ff8aa4e374ff91f` · gate `WANT=af617bf043a2bdda562f88fc6893e906`
Built 22-Aug-2026. **Not yet installed.**

---

## What happened

18-Aug was entered as **23,879**. The counter's handwritten copy said **25,176**. The drawer
would not balance by **₹1,297**.

Mid-correction, the maker's mirror was consulted before filing, and it read:

```json
"marg": { "bills": 22, "state": "applied",
          "total": "23,879.00", "variance": "-1,297.00" }
```

That looked decisive — *the machine says 23,879, so the entry was right and the handwritten
copy is wrong*. The correction was stopped on the strength of it.

**It was wrong.** A fresh export of the same day, validated by the guard on the medical PC,
reported:

```
2026-08-18 | 30 bill(s) | NET 25176.00 | CASH 18627.00 | NON-CASH 6549.00
note: 1 credit note(s) totalling -1640.00 — kept, and carried through signed
```

Two separate faults were stacked on top of each other:

1. **The applied export was partial** — generated before the day finished, so only 22 of 30
   bills were in it. Real, and the reason the books were short.
2. **The mirror's arithmetic was wrong** — and it is this one that made the first look like
   proof of the opposite.

## The arithmetic

`finance_ingest` stores a credit note as a **magnitude plus a `_return` service**, because
`sale_item` carries a non-negative constraint. Two readers summed those rows with a plain
`SUM(amount_p)`, which **adds** the refund:

```
true net of the 22 loaded rows      20,599.00
what the screens displayed          23,879.00
overstated by                        3,280.00  =  2 × the 1,640 credit note
```

And the coincidence that made it so convincing: the inflated figure landed **exactly** on
the disputed declared total of 23,879. Two wrong numbers agreeing looks like corroboration.

The guard on the medical PC had it right all along — it said the credit note was *"carried
through signed"*. The server did not.

## The fix

One SQL expression, `marg_net_sql(alias)`, used by every reader:

| reader | who sees it |
|---|---|
| `api_day_mirror` | the maker's reveal — **the one that lied** |
| `/finance/api/workbench/<ym>` | the checker's month grid — same fault, other screen |
| `_marg_month_compare` (A4) | written correctly the same morning, but with its own inline copy — folded in |

The third mattered as much as the first two: A4 was *correct*, and leaving it as a private
copy is how a future change reaches two readers out of three. Same argument as
`MARG_VARIANCE_THRESHOLD_P`, which the code already reasons about in exactly these terms —
*two copies of a rule is how two screens come to disagree about the same day.*

**Not changed, deliberately:** a push whose `status` stays `'pending'` while `applied_at` is
set is **correct**, not a bug. It means part of the push landed and a day in it is still
unfiled, so the rest is still owed. I called it a bug before reading the code; it reads like
an inconsistency and is not one.

## Seven new selftests, two of which would have caught this

- The expression is exercised against the **real 18-Aug shape** (one 20,599 sale, one 1,640
  return) and asserted to net 18,959 — plus a day with no credit note unchanged, a row with
  a NULL service still counted, and an empty set netting 0 rather than NULL.
- A **source guard** refuses any unsigned `SUM` over `sale_item` coming back, and a check
  that every reader goes through the one expression.
- A cross-reader check: the month grid and the month comparison must agree to the rupee.

The source guard needed a second attempt. Written the obvious way, the literal search string
occurs in the source it is searching, so the check **found itself and failed forever**. The
needles are now assembled from fragments. Worth remembering for any future source-level
assertion.

## The standing lesson

The investigation was nearly abandoned on the word of a screen, against a physical document
held by the person who wrote it. The physical copy was right; the screen was wrong; and the
screen was *more* convincing because its wrong number matched another wrong number.

Where a hand-written record and a computed one disagree, the computation is not automatically
the arbiter — **go back to the source and regenerate it.** The fresh export settled in ninety
seconds what an hour of reasoning had got backwards.

## Deploy

```bash
R=$(find /root -maxdepth 4 -type d -name deploy_kits 2>/dev/null | head -1)
cd "$R/.." && git pull --ff-only && \
cd /root/finance && tar -xzf "$R/S195_SIGN.tar.gz" --overwrite && \
bash S195_SIGN/install_s195_sign.sh
```

## Left open on 18-Aug

**8 bills, ₹4,577, sit in the review queue** awaiting patient attribution — which is why
batch 126 reads `partial`. The guard predicted it: 9 bills with no clinic ID, and 2 with
non-4-digit IDs (764, 790) *"scored low so they go to review rather than to a possibly wrong
patient"*. The day's money is correct and approved; only the attribution is outstanding.
`/finance/approvals` → 18-Aug → the review list.
