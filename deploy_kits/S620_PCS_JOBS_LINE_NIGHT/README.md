# S620_PCS_JOBS_LINE_NIGHT — the Clinic PCs page's jobs line stops crying wolf at night (S336, 22-Oct-2026)

**Found on the live page at 08:00 IST,** the morning S617 went in: the server card said *"The nightly check has not
reported for over three hours"*. False: the freshness check runs at 08:05 and then hourly 09:35 … 23:35, so between
23:35 and 08:05 its last run is up to 8 h 30 m old by design.

**What it does** (`/root/finance/setup_notes.py` 290722df → new, one exact edit in `edits_s620.py`): before 08:30 IST up
to 9 h 30 m is normal; from 08:30 on, 2 h 30 m. A check that really stops is still named.

**The one line (VPS):**

    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S620_PCS_JOBS_LINE_NIGHT/install_S620_PCS_JOBS_LINE_NIGHT.sh

**Proven by:** `walk_s620.py` (five clock times: 08:00 and 08:20 after 23:35 quiet; 10:40 after 08:05 and 08:45 after
23:35 warn; 15:10 after 14:35 quiet; on the box the real line reads); the S617 file goes RED. S617's own walk still green.

**Undo:** `--undo` puts the S617 file back (`/root/s620_backup/`) and restarts clinic-finance.
