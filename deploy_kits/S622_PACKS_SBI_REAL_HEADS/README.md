# S622_PACKS_SBI_REAL_HEADS — SBI read as SBI really prints it (S336, 22-Oct-2026, D755, F-975)

**Found on the live shelf at 09:18 IST.** The owner added his four 20-Oct SBI PDFs and typed their passwords. All four
opened; Dr Bhawna's savings was filed with its period, her loan was filed without one, and his own savings and loan stayed
unplaced. The real heads (read through the owner-only text door, numbers masked) differ from the made-up ones S621 was
proven on: the holder is printed to the left of *State Bank of India* on its line with no *Account Name* label, his name is
printed *MANOJ KUMARAGARWAL* (no space), and the loan statements (*Auto Loan*) print the period after *Statement :*.

**What it does** (`/root/finance/packs.py` 6ed8e18a → new, 3 edits; `/root/finance/packs.html` da0cbb8c → new, 2 edits,
all in `edits_s622.py`): the reader takes the holder from that line, reads KUMARAGARWAL / MANOJKUMAR as two words, takes
*Statement :* as a period label; the SBI files on the shelf are read once more at install (as the *re-read the shelf*
button does) and the installer prints where each went; a locked file added by hand gets a **Go to its password box** button.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S622_PACKS_SBI_REAL_HEADS/install_S622_PACKS_SBI_REAL_HEADS.sh

**Proven by:** `walk_s622.py` — made-up heads in SBI's real layout (savings, Auto Loan, Dr Bhawna's both, the HUF) and the
S621 layout still read; each filed by *Add statements* on its own account with its period; the locked one opens when its
password is typed; September's five quarterly cells full; the page's jump and script. On the box, a scratch copy of the
live database: every SBI file whose text reads is placed on an SBI account of its own kind, with its period. S621's own walk
stays green on the new files; the S621 files go RED.

**Undo:** `--undo` puts the S621 files back (`/root/s622_backup/`) and restarts clinic-finance.
