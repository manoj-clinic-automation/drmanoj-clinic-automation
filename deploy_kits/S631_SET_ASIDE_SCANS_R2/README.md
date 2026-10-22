# S631_SET_ASIDE_SCANS_R2 — S630 re-issued (the walk only)

**Project:** Sanjeevni (session 339, 22-Oct-2026). Built IN THE CHAT. What and why: `deploy_kits/S630_SET_ASIDE_SCANS/README.md` — a scan the scan app
set aside is never offered *Send back for rescan* and never named in *The same paper scanned twice* on the owner's order list.

**Why a new number:** S630 (published 71d09b9, 19:10:23 IST) was REFUSED by its own installer at [5/9] (lock 19:11:21 IST): its walk on the NEW
files was green, but on the live copy three of its four controls were green on the OLD files too — reception had rescanned B-0157 as B-0208, so
no order card is tied to the B-0157 / B-0159 family any more, and the OLD page offered no set-aside scan to catch. **Nothing was installed.**
S630 is frozen; this kit carries the SAME two built files (the same `make_s630.py` and TO pins) and `walk_s631.py`, which lays its OWN family:
an order of 'W631 PHARMA' tied to scan W631-A (no lines read), its fuller copy W631-B set aside as A's duplicate, and W631-C a second copy of B's
paper. NEW green (11 checks, 4 controls), OLD red on all four — walked with the B-0157 tie removed, as on the box. The harmless shell line of
S630's installer (`set -u, not set -e` read as a command) is gone.

| file | FROM | TO |
|---|---|---|
| /root/finance/order_track.py | 4edfef6b (S629) | 9010a012 |
| /root/finance/porders_s454.py | 0ce83525 (S629) | 647f2925 |

finance.db is not written. One restart of clinic-finance.

## Install (the owner's one server line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S631_SET_ASIDE_SCANS_R2/install_S631_SET_ASIDE_SCANS_R2.sh
```
**Undo:** the line the installer prints (both `.bak_S631_<from8>` back, one restart).
