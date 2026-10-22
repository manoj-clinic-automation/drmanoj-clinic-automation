# S630_SET_ASIDE_SCANS — a set-aside scan is never offered "Send back", never named twice

**Project:** Sanjeevni (session 339, 22-Oct-2026). Built IN THE CHAT. **Why:** the owner asked (19:01 IST) what happens to the rejected
pharmacy scans already present. Read live after S629 (19:0x IST): B-0159 — set aside by the scan app as a copy of B-0157
(`https://followup.dr-manoj.in/scanapp/bills/159`) — was offered *Send back for rescan* on the order list (the server refuses it: 409
`set_aside`) and named with B-0208 under *The same paper scanned twice*. Clutter, no harm, no data touched.

**The rule now:** a scan the scan app set aside (status rejected, or a copy: dup_of) is never offered Send back — the card offers the tied scan
itself when that one is not set aside, else nothing — and never appears in *The same paper scanned twice*. The fuller copy still feeds the order
list's "on bill" note (S628). Everything else about set-aside scans is unchanged: never counted, never learnt from, not on the redo list or the
every-scan list.

| file | FROM | TO |
|---|---|---|
| /root/finance/order_track.py | 4edfef6b (S629) | see TO_PINS.md5 |
| /root/finance/porders_s454.py | 0ce83525 (S629) | see TO_PINS.md5 |

finance.db is not written. One restart of clinic-finance. Walk: `walk_s630.py` lays its own second copy (W630-1) of a set-aside scan's paper;
NEW green, OLD (S629's files) red on all four controls (159 offered; 159 named with W630-1; Shavez's page the same; the server refuses 159).

## Install (the owner's one server line, after his publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S630_SET_ASIDE_SCANS/install_S630_SET_ASIDE_SCANS.sh
```
**Undo:** the line the installer prints (both `.bak_S630_<from8>` back, one restart).
