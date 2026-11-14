# S824_REVISED_BILL_SETASIDE — a dealer's revised bill that was set aside as a "second scan" still settles its return (14-Nov-2026, Sanjeevni session 455) · F-1378

**The fault.** Janta's bill JP21965 of 2 October: the paper read ₹4,450 with a ₹1,245 return written on it; Marg holds ₹3,205. The dealer's revised bill (scan **B-0271**, ₹3,205 = ₹4,450 less ₹1,245) was set aside at 11:39 IST on 8 Nov as a duplicate of B-0118 after a "same paper" answer at the scanner. S740's revised-bill road reads only captured scans, so the return settled at 09:05 and reopened at 13:11. October's purchase month has shown it pending since.

**The kit.** `/root/finance/scan_register.py` (9262c5dc → the TO pin; rebuilt on the box from the live bytes by `make_s824.py`, exact counted anchors):
- a new read-only reader `s824_set_aside()` — the pharmacy scans the scan app set aside as a second scan of another bill (`status='rejected'`, `dup_of` set, not a page of a bill);
- `_s740_revised` reads them **only when no captured scan settles the return**, by the same rules as a captured scan: the same dealer and bill number, the amount = the paper less the return within `_s740_tol`, and more than ₹1 off the paper — so a true double (B-0264, ₹4,450) never settles anything — and **only when Marg already holds the revised figure** (a set-aside scan never outranks a credit note, and Amir is never told to change Marg from a paper he cannot open);
- a set-aside scan is named in the words ("scan B-0271") but not offered as a link (the scan door serves captured scans only).
Nothing else changes; no database change; no staff screen gains a line.

**Proof before placing (on the box, read-only):** the returns read with the live file and with the new file on the live `finance.db` and `assets.db`; placed only if Janta 21965 is settled by B-0271, every other return reads exactly as before, and B-0264 settles nothing (`PROOF S824: PROVEN`).

**Bench.** `walk_s824.py` (S740's made-up root, steps 1–4 unchanged + step 5): 18 S824 checks green on the new file, 7 red on the live file (the control); S740's own walk reads the same on both (its two standing wording reds). Cold review by a second reader: SAFE AFTER FIXES — the must-fix built (step 7 reads the old file's returns again just before its compare: the live data moves during an install) and two should-fixes built (the Marg condition above). Left and said so: the proof is one read before the tracker's own sync; it has not run on the real assets store (a different reading there blocks the install, safely). The proof run on the 14-Nov database copy with a made-up assets store: PROVEN; B-0264 settles nothing.

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s824kit && cp -rp /root/deploy/repo/deploy_kits/S824_REVISED_BILL_SETASIDE /tmp/s824kit && bash /tmp/s824kit/install_S824_REVISED_BILL_SETASIDE.sh

**Undo:** the installer prints the one line.
