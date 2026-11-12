# S795_PART_EXPORT_GUARD — a part list may not retire the fuller report (12-Nov-2026, Sanjeevni session 434)

**The fault (found 12-Nov, on the owner's question about the scans).** On 11-Nov two bill-wise purchase reports of 1–11 Nov reached the server 15 seconds apart: 29 bills, then 4. The rule "same period, the later one wins" let the 4-bill list retire the 29-bill one. 25 of November's 29 bills stopped being effective, and the scan pairing said "no bill on the server yet" for bills that were there.

**The kit.**
1. `/root/finance/purchase_app.py` (54d27cd3 → the TO pin): in `api_push`, an incoming report with fewer than half the rows of the live, older report it would retire — and more than two rows short of it — is a part list. It is kept in `purchase_export`, marked as retired by the fuller report, and nothing is read from it (`reason: part_export`). `clinic-finance` is restarted.
2. `repair_s795.py`: the 11-Nov pair in `finance.db` — the 29-bill list live again, the 4-bill list marked retired by it, its 4 bills re-hung on the full list; the pairing's "seen" mark cleared. Bill lists only; the two old line-list pairs of 1 Sep–3 Oct are listed and left alone. The before-state is saved beside the database.

**Proof before it left the bench.** `walk_s795.py` GREEN on the built file, its control RED on the live file; `rehearse_s795.sh` 6/6 on a made-up root; the repair run on a copy of the 12-Nov database (device VM only): November 4 → 29 effective, September 86 and October 82 unchanged, effective lines unchanged, integrity ok.

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s795kit && cp -rp /root/deploy/repo/deploy_kits/S795_PART_EXPORT_GUARD /tmp/s795kit && bash /tmp/s795kit/install_S795_PART_EXPORT_GUARD.sh

**Undo:** the installer prints the one line. Off: none needed — the rule only sets a part list aside.
