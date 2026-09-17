# S309_FRESHNESS_DOCTERZ

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S309_FRESHNESS_DOCTERZ/install_S309_FRESHNESS_DOCTERZ.sh
```

## Why (F-517)

The health page watches the Docterz figures by asking "how old is the newest row?". Its window was set to 200 hours back when the job was run by hand — so the page would say nothing for eight days even if the figures stopped arriving. The job has run on a timer since S238, and every ten minutes all day since S291.

## What changes

The window becomes **50 hours** and the note is rewritten to say why.

Not 26 hours, which the fault note first suggested: the leg watches the data, and a day sheet legitimately does not arrive over a closed Sunday or on a morning after the clinic PC was off overnight — the database shows quiet spells of 24.0 and 28.7 hours in the week to 17-Sep. 26 hours would cry wolf. The note says to tighten to 26 once a month of the ten-minute schedule has been seen.

The change is two strings in one leg of the legs file, with a backup beside it. No code, no service, no restart.

The installer also refuses to make the change if the data is **already** older than 50 hours — then the window is not the first thing to fix — and it prints the live cron lines for Docterz, the asset-app archive and the petty backup, with long values masked.

## Proof

`selftest_s309.py`, run by the installer on a **copy of the live file**: 21 checks — the window and note change, every other leg and every other byte untouched (two lines differ), the backup holds the original, a second run changes nothing, and it refuses a file without the leg, a window that is not 200, two notes in one leg, unreadable JSON, a missing file, and data that is already stale (with `--even-if-red` as the deliberate override). Negative controls: a 26 h window, the stale-data guard removed, and the defensive compare removed each turn it red.
