# S310_FRESHNESS_LEGS_2

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S310_FRESHNESS_LEGS_2/install_S310_FRESHNESS_LEGS_2.sh
```

## What it does

Two more rows on the health page, from what the live crontab actually says:

1. **Asset register backup** — the row still said "weekly" with a 200-hour limit, from the days of a bare tar line. It has been nightly and self-verifying since S286, so the limit becomes **26 hours**.
2. **Bhati's bill photos** — nothing watched the 02:40 backup at all. A new row watches its log, which carries a line on every run even when no photo is new. Limit **26 hours**.

The photo backup's first run is at 02:40 tomorrow morning. Until that log exists the row would read NEVER and light the page red for no fault, so the kit **skips it and says so**. Running the same line again after 02:40 adds it. Running it when there is nothing left to do says ALREADY and writes nothing.

Data only: a backup is written beside the legs file, the result is compared leg by leg and read back. No code, no restart.

## Proof

`selftest_s310.py`, run by the installer on a **copy of the live file** with the watched things faked in /tmp: 25 checks — the window and note change, the new leg lands right after the asset row in the file's own indent, every other leg and line untouched, the backup holds the original, the second run adds the leg once its log appears, the third says ALREADY, and it refuses an archive already older than the new window, a stale log (not added), a window that is not 200, unreadable JSON, a missing file and a file without the leg. Negative controls: the stale guard, the compare guard and the not-there-yet guard each turn it red.
