# S237_LEDGER_STATEMENT — the staff ledger with the noise taken out

**Built 10-Sep-2026 for the August salary close. It reads. It cannot write.**

---

## THE PROBLEM YOU DESCRIBED, AND WHAT IT ACTUALLY IS

The ledger is append-only — nothing is ever edited, and a correction is made by posting a **contra**
that reverses the original. So a corrected advance appears three times: the wrong one, the contra,
and the right one. That alone is hard to read.

**But there is a second reason, and it is the real mess.** The field `contra_of` means **two
different things**:

| on this kind of row | `contra_of` means |
|---|---|
| a **contra** | "this **reverses** row X" |
| an **instalment, interest charge, skip or capitalisation** | "this **belongs to** advance X" |

So **every monthly instalment, every interest charge and every skip carries a `contra_of` and looks
like a reversal.** On a loan running eight months that is eight rows that appear to be contras and
are nothing of the kind. That is why Darpan's and Surendra's ledgers look like a mess.

**This tool separates the two.** A row counts as a reversal only if it genuinely reverses something —
same category, opposite amount, approved — which is the same test the ledger's own `open_advances()`
uses.

## WHAT IT SHOWS YOU

Per person: each advance still owed, what has been recovered month by month, any interest added for a
skipped month, and **what is still owed** — then what that month's close took off the salary.

Advances already cleared are counted and hidden, so only live money is on screen.

**The arithmetic is not reinvented** — it is copied from `staff_ledger.py` itself:
`balance = amount + capitalised − recovered`. It cannot disagree with your own page.

## RUN IT — one line

```
bash /root/deploy/vps_deploy.sh S237_LEDGER_STATEMENT
```

That places the reader, proves it, and **prints the August statement for every member of staff.**

Afterwards, whenever you like:

```
/usr/bin/python3 /root/ledger_statement.py --file /root/staff_ledger/ledger.jsonl --month 2026-08 --staff Darpan
```

```
/usr/bin/python3 /root/ledger_statement.py --file /root/staff_ledger/ledger.jsonl --month 2026-08 --csv /root/advances_2026-08.csv
```

## WHAT IT WILL NOT DO

No `--write`, no `--fix`, no option that changes a byte. It opens the ledger, reads it, prints, and
stops. **Pending rows are held apart and counted in nothing**, and named, because they will move
these numbers the moment a checker decides them.

## PROVEN

`py_compile` clean · **41 selftest checks, 0 failures** · and a walk against a ledger built to be as
messy as yours — a contra'd-and-re-entered advance, a cleared advance, an interest-bearing loan with
a skipped month and capitalised interest, a pending request and a rejected row. Full output in `WALK_PROOF.md`,
and the fixture regenerates itself with `_proof/make_fixture.py` — **the kit carries no `.json` or
`.jsonl` file at all**, because the repository blocks them (F-300).

---
*S237_LEDGER_STATEMENT · 10-Sep-2026 · standard library only, read-only.*
