# S238_LEDGER_RECONCILE — the owner's record, made true in the staff ledger

**Built 10-Sep-2026 (S238) under D442: his record is the authority; the ledger is corrected to it.**

## WHAT IT DOES

It reads the live ledger, compares it line by line with `stated_record_2026-08.txt` (the August list
Dr Manoj confirmed against his physical records), and prints:

1. every line of the record — **ok**, **FIX**, or **HELD** (waiting for evidence or a decision);
2. each person's balance at 31-Aug: the record, the ledger now, and after the fix;
3. **what the September close would take from each person — today, and after the fix** — worked out
   by the ledger's own close, run on a throw-away copy;
4. what the fix takes off the August salary (which is not yet locked).

## HOW IT IS SAFE

- **The install line only prints.** It never writes to the ledger. Writing is a second, separate line.
- The write run re-reads the ledger and **refuses if one byte moved** since it was planned, takes a
  **dated backup**, writes every row through `staff_ledger.py`'s own `append_ledger()`, proves the file
  is the old file plus new lines, **re-checks**, and files a note in `/root/staff_ledger/corrections/`.
- It **never edits or deletes a row**, never runs a close, and refuses outright if August's salary is
  already locked or September's close has already run.
- A wrong advance is corrected the ledger's own way — a contra, then the right entry.
- The installer refuses unless `staff-ledger.service` runs `/root/staff_ledger.py` **and** that file is
  the pinned v3.6 rev 3 (`80257711…`) the tool was proven against.

## RUN — one line, it prints the dry run

```
bash /root/deploy/vps_deploy.sh S238_LEDGER_RECONCILE
```

## THEN, ONLY WHEN THE DRY RUN READS RIGHT — the write

```
/root/wa/venv/bin/python3 /root/staff_ledger_reconcile/ledger_reconcile.py --apply
```

A second run afterwards must say **0 corrections ready** — that is the proof it took.

## NO STAFF FIGURES FROM THE LEDGER ARE IN THIS KIT

The repository is public. The selftest runs on a **throw-away copy of the real ledger on the box**, and
the walk against the owner's 51 real rows lives only in `D:\Downloads\ClaudeCowork\` (not in git).

---
*S238_LEDGER_RECONCILE · 10-Sep-2026 · standard library only.*
