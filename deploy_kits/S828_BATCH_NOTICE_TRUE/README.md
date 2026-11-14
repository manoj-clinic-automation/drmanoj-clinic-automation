# S828_BATCH_NOTICE_TRUE — the "Amir's work" message tells the batch fixes as Amir's card does (Sanjeevni session 457, 14-Nov-2026)

**What happened (14-Nov):** the owner's phone said *"Batch fixes: 0 done today, 18 left"* at ~09:01, when Amir's purchase reports arrived. Amir's card said *8 fixed, 5 left*. The Batch Stock (06:51) had been read at 07:0x, but its Issues can be judged only once the day's sales are in; that judgement came at the 09:05 run. The message also counted every open voucher row, not what the card shows.

**The kit:** `/root/finance/owner_notice.py` 471859b3 → the TO pin, rebuilt on the box from the live bytes by `make_s828.py` (two exact replacements, in `_part_amir` and SETTINGS only):
- while a batch row waits for the day's sales (*issue pending*), the "Amir's work ✓" message waits too — at most **owner_notice.batch_hold_min** (180 minutes, a setting) after his reports; past that it goes and says the check is still waiting;
- the numbers are Amir's card's own (`expiry_watch.fixes_rows`): fixed in the last 24 hours, and the rows judged in the last 24 hours still to do — *"Batch fixes: 8 fixed, 5 still to do (as on Amir's card)"*.
Nothing else changes; no database change beyond the one new setting row.

**Bench:** `walk_s828.py` on a copy of the database: 8/8 green on the new file; its control on the live file 5 red.

**Install (the VPS, one line):**

    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s828kit && cp -rp /root/deploy/repo/deploy_kits/S828_BATCH_NOTICE_TRUE /tmp/s828kit && bash /tmp/s828kit/install_S828_BATCH_NOTICE_TRUE.sh

**Undo:** the installer prints the one line (backup `owner_notice.py.bak_S828_471859b3`).
