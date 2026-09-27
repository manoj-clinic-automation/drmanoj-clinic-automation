# S422_GAS_REPORT_HEALTH — F-595 closed · session 284 · 27-Sep-2026

**The fault (F-595):** `gas_export.py` compares every Apps Script project in Google with the repository copy every Sunday at 02:20 — and wrote its answer only to `/root/state_backup/gas_export.log`, which nothing reads. Twice (13-Sep, 20-Sep) it correctly reported the copy was behind, and nobody heard.

**Now it has two readers:**
1. **The health page** (`https://followup.dr-manoj.in/finance/health`) gets one row, *Apps Script vs the repository*: **ok** when every exported project matches; **info** naming the files when Google holds something newer (the assistant's to copy into `GAS_CURRENT` — never a job for the owner); **warn** when the comparison has not run for more than 8 days. `finance_app.py` gains one self-contained block before the `B2` marker — the file was **read whole this session** (13,046 lines; dead 0; drift reset to 0).
2. **The freshness table** gets one leg, *Apps Script weekly comparison* — `file_mtime` on `_DRIFT.json`, 200 h (the job writes that file only when a comparison succeeds, so a failing Sunday goes stale on its own).

Restarts `clinic-finance`. Backups `finance_app.py.bak_S422_<from>` and `freshness_legs.json.bak_S422_<from>`. RED after placing → both restored.

**Proof:** `walk_s422.py`, 12 checks on copies of the live bytes: the only change to `finance_app.py` is the block; it compiles; a second apply changes nothing; every other leg byte-identical and the box's own `freshness.py` accepts the new one; the row in every state — never run, clean (whitespace-only and no-copy ignored), findings, 9 days stale, unreadable result, no conf.

## Install — one line on the VPS (after the publish)
```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S422_GAS_REPORT_HEALTH/install_S422_GAS_REPORT_HEALTH.sh
```
