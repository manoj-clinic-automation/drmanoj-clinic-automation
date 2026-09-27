# S429_MONTHLY_PIN_GUARD — session 284 (parent), 27-Sep-2026

**F-649.** `/root/state_backup/clinic_state_backup.py` ships the encrypted state to a monthly slot on the first good night of each month and pins that revision "keep forever". The slot's description `month=YYYY-MM` is what marks the month as done — and it was written even when the pin failed or no revision was listed, so such a month would never be retried and could end with no pinned copy.

**Change.** One anchored edit, FROM `ede26d98a6aaf36188a797d732f4a4d7` (S424, live) → TO `0e841f3569f6e00f92fdc99031ed1242`: the description is written only when the pin is confirmed; otherwise the log says the month stays open and the next night ships and pins it again. Nothing else in the file changes. Cron-run (01:50), no restart.

**Proof.** `walk_s429.py` runs the file's own monthly block against a fake Drive: pin confirmed → closed; pin refused → open + warning; no revision → open + warning; upload not verified → unchanged; month already closed → nothing done. The same walk run on the old bytes is RED on the two failure cases (5/7) — the defect, shown.
