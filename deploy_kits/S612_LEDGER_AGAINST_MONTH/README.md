# S612_LEDGER_AGAINST_MONTH — an advance against a later month's salary says so (S331, 22-Oct-2026)

**The owner, 22-Oct 05:47 IST:** Surendra's Rs 3,000 of 21 Oct *"was given to him against November salary"*.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S612_LEDGER_AGAINST_MONTH/install_S612_LEDGER_AGAINST_MONTH.sh

**What was wrong** — the ledger already had both November advances right (Surendra Rs 3,000 of 21 Oct, Darpan Rs 10,000
of 18 Oct: quota lane, against 2026-11, recovered in full at the November close). The S611 statement called them
"in full" and "open". Darpan's July loan correction read "Rs -1000 added to the loan".

**What it does** (`/root/staff_ledger.py` 6ee4283c → new, by 5 exact edits in `edits_s612.py`): an advance taken
against a month's salary reads "from November 2026 salary"; one waiting for a later month reads "to be cut in Nov
2026"; a negative capitalise row reads "Rs 1,000 taken off the loan of … (a correction)"; "Rs 1,000 of it interest".
Version → 4.1-S612-STATEMENT. No ledger or salary figure changes.

**Proven by:** the file's own selftest; `walk_s612.py` (all of S611's walk, plus the November advance and the
correction made up, and the live ledger and register on scratch copies). The S611 file goes RED.

**Undo:** `--undo` puts the S611 file back (`/root/s612_backup/`).
