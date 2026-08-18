# S189_G1a — F-130: the design is asserted, not just the ids

**One file. `finance_app.py`. Thirty-five lines, all of them inside the test
suite. Nothing your staff can see changes.**

## Why

S188 shipped a kit that rebuilt Darpan's page under the new design language
while deliberately preserving every single id — and **464 green checks could
not see the one thing it changed.** That is F-130. Until it is closed, any
page can silently revert to an older design and the whole suite stays green.

## What it adds

Four checks, made on the **real served routes**, holding each page to its
**recorded** design state:

| page | seat | Design Language v1? |
|---|---|---|
| `/finance/entry` | maker | **yes** — S188_D2a |
| `/finance/approvals` (the Hub) | checker | **yes** — S187_H1c |
| `/finance/workbench` | checker | **no** — S187_M1a, pre-v1 |
| `/finance/review` | checker | **no** — S179, pre-v1 |

The two **no** rows are asserted negatively on purpose. That way rebuilding
either page under the design language cannot land silently either — it has to
come back to this table and flip the flag.

## The thing worth reading — F-135

The backlog said *"add the assertions to approvals, workbench and review."*
I surveyed the three pages before writing a line, and:

```
approvals   4/4 markers    the instruction was right
workbench   0/4 markers    built BEFORE the design language existed
review      0/4 markers    the S179 page, untouched for nine sessions
```

**Two thirds of that instruction would have gone RED at its own gate.** It was
written at the S188 close without opening the files — the same shape as F-132's
*"already correctly scoped"*, this time in the record rather than in the code.

That is why the table above declares what the pages **are** rather than what
they were supposed to be. Bringing the workbench and the review page under the
design language is real work, and it is a separate build.

## Projection, written before measuring

| | before | after |
|---|---|---|
| offline rehearsal (seeded store) | 476 / 478 | **480 / 482** |
| your box | 478 / 478 | **482 / 482** |

Offline **measured 480/482 — held exactly.** The two offline failures are the
same two before and after and are artefacts of the seeded store, not of this
change. The offline check *total* (478) equals your box's total (478), which is
the only reason the rehearsal is worth anything.

The installer refuses unless the box shows **exactly +4 checks and zero
failures**, and restores on any red.

## Risk

None at runtime. The block runs only under `--selftest`, and it sits at line
6657 of 6710 — after every route in the file. No page, no query, no migration,
no data.

## To install

```
cd /root/deploy/repo && git pull
bash deploy_kits/S189_G1a/install_g1a.sh
```

Built on live `f06e139b7651329a72b08bbc5779077f`, ships
`16faf98caa720a662316fa235a4b35b9`.
