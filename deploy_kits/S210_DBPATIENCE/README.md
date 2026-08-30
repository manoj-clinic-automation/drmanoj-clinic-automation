# S210_DBPATIENCE — the Apply 500 was "database is locked"

Journal, 30-Aug 18:35 IST, twice: `sqlite3.OperationalError: database is locked` at
`con.commit()` in `api_marg_push_apply`. Gunicorn runs several workers; the owner's retry
click landed on a second worker while the first held the write lock, and sqlite's default
5-second patience ran out on a long multi-day apply. The new page surfaced it honestly —
the old page called this "network".

**Fix — one anchored change in `db()`:** `connect(timeout=30)` + `PRAGMA busy_timeout=30000`.
A connection meeting a locked database now WAITS instead of erroring; contention becomes a
queue. No schema change, no journal-mode change (WAL is a separate owner decision — it
changes what `finance_backup.sh` must copy; recorded, not smuggled in).

Nothing was corrupted: a failed commit leaves the books consistent, and F-155 kept the
push pending exactly so it can be re-applied.

Selftest 16/16 (three newest finance_app copies: patch, compile, no-op rerun, refusals).

## Install — VPS, one line at a time

```
git -C /root/deploy/repo fetch --depth 1 origin main && git -C /root/deploy/repo reset --hard origin/main
```
```
/root/wa/venv/bin/python3 /root/deploy/repo/deploy_kits/S210_DBPATIENCE/patch_finance_app_dbpatience.py /root/finance/finance_app.py
```
```
systemctl restart clinic-finance.service && sleep 3 && systemctl is-active clinic-finance.service
```

Then Apply the 28/29-Aug report ONCE and wait for its popup — a multi-day apply can take
a minute now instead of failing; the popup at the end tells you what loaded.

*S210 · 30-Aug-2026 · root cause from the journal, not guessed.*
