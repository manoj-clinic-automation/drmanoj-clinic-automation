# S665_EXPIRY_DAYTIME — the expiry watch catches up during the day · project Sanjeevni · session 359 · 27-Oct-2026

**For the owner, in two lines.** The expiry list (your Expiry watch box and page, Darpan's "sell first" block, Amir's card) now updates within about ten minutes of the morning's sales reaching the server, instead of waiting for 23:57. VOM L, whose last 3 strips sold on 26-Oct, leaves the list the moment this is installed.

## Why
The owner, 27-Oct-2026 11:58 IST: *"The expiry watch is showing stale stock of vom l medicine, as it's in the list to sold before 1st November, despite shavez exported his reports successfully in morning."*
**What happened.** The list of the night of 26-Oct (run 4, 23:57 IST) used Marg's Batch Stock of 26-Oct and sales up to 25-Oct. VOM L batch C1235 (expiry 11/26, Marg stops selling it on 1-Nov) held 3 strips. All 3 sold on 26-Oct, in five bills. Shavez's 09:35 IST export carried those sales, and the spine took them within ten minutes (`spine_build`, every ten minutes 08–23). But the watch is made only at 23:57 (`near_expiry.py`, S343's line), so it was right about last night and wrong about this morning. Nothing was wrong with Marg or with Shavez's export.

## Files
| live file | owner | FROM | TO | what |
|---|---|---|---|---|
| `/root/finance/spine/near_expiry.py` | Sanjeevni | c12284f3 | 41afc06e | 1 edit: `--if-newer`. The watch is made only when the spine holds a sale day newer than the newest run's `sales_to`, or there is no run yet; otherwise it exits silently. `newer()` is read-only. The 23:57 line (no flag) is unchanged. |
| the crontab | shared (PLANNED on the board v735) | — | + 1 line | `5-59/10 9-23 * * * cd /root/finance/spine && flock -n /tmp/spine.lock /root/wa/venv/bin/python3 -B near_expiry.py --if-newer >> /root/finance/spine/near_expiry.log 2>&1 # S665_EXPIRY_DAYTIME`. It runs under the spine's own lock, so it never reads the spine mid-build, and offset by five minutes from the spine's build. |

No service restart. `expiry_watch.py` is not touched, so every screen reads the newest good run exactly as before. A daytime run adds one row to `stock_expiry_run` (normally one a morning). The night's run still rolls the day over.

## Proven (`walk_s665.py`)
Offline (the device VM, the 27-Oct bundle and database copy; no spine copy exists off the box): **6 of 6 green**. The control gives **5 S665 red · 0 older red · 1 green**. On the box the walk adds two checks on copies of the live database and spine (the live shape): the line makes one whole good run reaching the spine's newest sale day, and the next tick makes none. That gives **8 of 8**, and the control **6 · 0 · 2**. The installer stops before placing anything if either is not so.
The installer was rehearsed on a made-up server three ways: red after placing restores the file and the crontab and releases the lock; green adds exactly one crontab line with every other line byte-for-byte unchanged; a second run reports ALREADY INSTALLED.

## Install (on the server, after the publish; the window is 08:02–23:30 IST so it never meets the 23:57 run)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s665kit && cp -rp /root/deploy/repo/deploy_kits/S665_EXPIRY_DAYTIME /tmp/s665kit && bash /tmp/s665kit/install_S665_EXPIRY_DAYTIME.sh
```
## Undo (the installer prints it with the exact backup names)
```
\cp -p /root/finance/spine/near_expiry.py.bak_S665_c12284f3 /root/finance/spine/near_expiry.py && crontab $(ls -t /root/deploy/crontab.bak_S665_* | head -1)
```
