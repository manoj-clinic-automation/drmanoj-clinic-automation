# ⚠ DO NOT INSTALL THIS KIT — its gate is RED on purpose

**S209 · 30-Aug-2026 · decided under the owner's delegation ("you decide").**

This kit's `SUMS.md5` fails, and it is **the only red gate left in `deploy_kits`**
(168 gates · 167 green · this one). It has been left red deliberately. Making it
green would delete the only warning attached to these bytes.

## What was measured

| what | md5 |
|---|---|
| this kit's own SUMS row demands | `6617ec6fac43d8b342b7970492cbd899` |
| the `finance_app.py` actually in this folder | `e1791014cf0d311137f319d6b391aa6b` |
| the live VPS file (owner's paste, S208 close) | `8427c82e…` |

Three different values. So this is **not** a kit lagging behind live — it is a kit
whose contents no longer match what it shipped with.

**And neither `6617ec6f…` nor `e1791014…` appears anywhere in the KB Register or the
History Archive.** The pin record has never carried either value. The row cites a hash
nothing ever pinned, and the folder holds a third the record never pinned either.

## Why that matters more than a red tick

`finance_app.py` is the clinic's money application. Installing this kit would copy
**unidentified bytes** over live financial code. Nothing installs from here today, so
there is no live risk — the risk is a future session treating a stale folder as a
source of truth, which is exactly what **D188** exists to prevent: *a filename is not
provenance.*

## What would resolve it

One of:
- a VPS backup (`/root/finance/finance_app.py.bak_*`) that hashes to either value,
  which would date and identify it; or
- the owner's ruling to declare both **UNIDENTIFIED** and retire the kit.

Do **not** repair the row to match the file. That would certify bytes nobody can
account for.

**Candidate F-244.**
