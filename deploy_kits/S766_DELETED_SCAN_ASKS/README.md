# S766_DELETED_SCAN_ASKS — a deleted scan is no longer asked for

**Session 417 (the Sanjeevni chat), 09-Nov-2026. The owner, 17:55 IST:** check the 8 *Dobara scan karo* left on Alisha's list after S765.

**Found:** the scans B-0274 … B-0289 are no longer in the Scan App. They were deleted, and every page of theirs answers 404. By the look of it they were the untagged first scans of the dealers' summaries, done again as B-0290 … B-0304. The server's asking (S736) walks only the scans assets.db still holds, so it never withdrew its own ask on a deleted scan, and reception was asked for ever.

| file | from → to | what |
|---|---|---|
| `/root/finance/porders_s454.py` | `903df714` (S765) → `cd2feeb3` | `s736_plan` withdraws its own open ask on a scan assets.db no longer holds. A scan that was rescanned (a newer scan names it in `rescan_of`) is left for its rescan to close as done. An ask a person sent stays. With assets.db unreachable, nothing is withdrawn. |

**Proofs:** `walk_s766.py` 9/9 green on made-up facts. The CONTROL on the live file: the 2 S766 checks red, the 7 old checks green. S765's summary rule stands. `rehearse_s766.sh` 5/5. `proof_s766.py` (on the box) shows the server's open asks on deleted scans and that the kit's file would withdraw every one, while the rest of the asking stays the same as the live file's.

**Install (the owner's paste; DRY first):**
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s766kit && cp -rp /root/deploy/repo/deploy_kits/S766_DELETED_SCAN_ASKS /tmp/s766kit && DRY=1 bash /tmp/s766kit/install_S766_DELETED_SCAN_ASKS.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s766kit && cp -rp /root/deploy/repo/deploy_kits/S766_DELETED_SCAN_ASKS /tmp/s766kit && bash /tmp/s766kit/install_S766_DELETED_SCAN_ASKS.sh
```
**Undo:** the installer prints the one line: `porders_s454.py.bak_S766_903df714` put back, and finance restarted.
