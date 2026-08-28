# S208_STOCK_LEDGER — the stock register, and the fix that makes it close

**Staged, not installed. The VPS was not touched.**

```
expected (Marg)  ->  counted (staff)  ->  difference  ->  cause  ->  closed
```

## What it is for

Stock leaves the shop by several doors. It is **sold** or **returned to a vendor** — Marg records
those two well. It is also **issued** for clinic use, thrown away **expired**, **broken**,
**received and never entered**, or **sold and never billed**. Those leave no trace at all until a
physical count finds the hole, and by then nobody remembers which door.

So: capture the difference **the day it is found**, name the door while the memory is fresh, and
keep it open until Marg's own numbers agree again.

## Why this kit exists and S207_STOCK_VPS does not

**The S207 kit could not have worked, and would not have said so.**

`push_snapshot.py` sent the **Marg** token in the **Cron** header — two different secrets — to
`/stock/api/snapshot`, a path the Marg token was not allowed to open. The app's fail-closed front
gate refuses that **401, before the route runs**. Counts would have been recorded correctly and
**every difference would have stayed open forever**, with the only evidence a line on a console
nobody reads.

Neither proof the kit carried could see it:

| proof | why it passed anyway |
|---|---|
| `push_snapshot.py --dry-run` | returns **before** the network call |
| `selftest_stock_app.py` (37) | drives the routes inside a bare app that **has no gate** |

**Two sound halves, and nothing testing the join.** That is the same shape as the fault already
recorded in `_gate()` itself — pipeline-status added at S202 and never allow-listed, refused 401 for
every pull since.

## The three changes

1. **The front gate** lets the sender's token open **one more path**, `/stock/api/snapshot`, exactly
   as it already opens `/finance/api/marg-push`. **Not the Cron token** — that one opens every path
   with no identity; handing it to manojz would trade a narrow sender for a master key.
2. **`push_snapshot.py` sends `X-Finance-Marg`**, and gains `--verify`, which proves the server
   accepts this machine on this path **by sending an empty body — it writes nothing**.
3. **`api_snapshot` accepts the token itself**, re-checked in the handler as `api_marg_push` does.
   The token returns **no identity and no role**: it cannot submit a count, name a cause, or read
   the losses. `selftest_gate_join.py` proves each of those refusals.

**Also fixed while here:** `/api/open` and `/api/losses` had no role check of their own. Behind the
front gate they were never public, but "protected by something else" is how a route ends up open the
day it is mounted somewhere else.

## The rules that matter, unchanged from S207

**A count with no bill number is refused.** Not warned — refused. A count that is not pinned to a
sale bill cannot be reconciled later.

**The expected quantity is copied into the count, never re-read.** A difference measured against a
number the counter never saw is not a difference, it is an argument.

**Naming the cause is the checker's job.** `UNEXPLAINED` is the default and is **meant to be used**.

**A difference closes only on an exact match**, and it closes **by itself** when the next export
agrees — recording which export agreed. A manual "mark as done" is the step that stops being done in
week three.

**A surplus is never netted off a shortage.** Five found here and ninety-four missing there is two
errors, not one small one.

## Proven

```
selftest_stock_app.py      44 checks   the real routes, throwaway database
selftest_gate_join.py      14 checks   real header -> real gate -> real route,
                                       including the S207 failure reproduced
patch on the real file     finance_app.py 11,395 lines: applies, compiles,
                                       and reverts md5-identical
the patcher refuses        on the older finance/finance_app.py copy, by design
```

## Install

```
bash /root/deploy/vps_deploy.sh S208_STOCK_LEDGER
```

Then, **on manojz**: `python push_snapshot.py --verify` → expect **GREEN**.

The installer measures the existing smoke suite **before** it touches anything and restores the old
file if that suite loses a single check, if the service does not come back, or if the route answers
404.

*S208_STOCK_LEDGER · 28-Aug-2026 · nothing live was touched by the session that built it.*
