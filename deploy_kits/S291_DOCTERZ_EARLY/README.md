# S291_DOCTERZ_EARLY

**One line on the VPS:**

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S291_DOCTERZ_EARLY/install_S291_DOCTERZ_EARLY.sh
```

**What was found.** The Docterz export lands in `D:\Downloads` on the owner's PC; the S239 auto-pickup runs the tracker within about five minutes and the day sheet is on Drive seconds later — 22:25 on 14-Sep, 04:50 on 16-Sep, 05:05 on 17-Sep (the PC was switched off right after the export on the 15th and 16th, so those ran at boot). The server's reader still started at 09:30, a schedule written when the sheet used to arrive by 09:20.

**What changes.** Root's crontab only: the four `S238_DOCTERZ_SCHEDULE` lines become one line, the same command every 10 minutes, all day. The Docterz Revenue screen and the morning match then show the day about ten minutes after the pickup runs. Drive stays the one source; `docterz_ingest.py` is untouched; the job pulse counts the new line by itself.

**Undo:** `crontab /root/finance/crontab.bak_S291`

**Proof offline.** The editor on the 17-Sep crontab capture: exactly four lines out, one in, nothing else moved; a second run refuses. Parsing: the three real day sheets on the PC (12, 14, 15 Sep) give byte-for-byte the totals, counts and line counts already in `finance.db`.
