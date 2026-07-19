# GutLog v3 - Deployment Runbook

The whole deploy is **swap one file, restart one service**. v3 keeps the same
folder, filename (`app.py`), venv, and port (8020) as v2, so there is nothing
new to provision on the existing box.

## Server facts (as deployed)
| Thing | Value |
|---|---|
| Host | Hostinger VPS `srv1746119`, CyberPanel / OpenLiteSpeed |
| App folder | `/root/gutlog` |
| Virtualenv | `/root/gutlog/venv` |
| systemd unit | `gutlog.service` |
| Run command | `gunicorn -w 2 -b 127.0.0.1:8020 app:app` |
| Public URL | https://health.dr-manoj.in (OpenLiteSpeed reverse-proxy -> 127.0.0.1:8020) |
| Database | `/root/gutlog/health3.db` (auto-created & seeded on first run) |
| Uploads | `/root/gutlog/uploads/` |
| Session key | `/root/gutlog/health3.db.secret` (auto-created, chmod 600) |
| Python | 3.9 (venv) - code is verified 3.9-safe |

## First-time deploy / upgrade (WinSCP + SSH)
1. **WinSCP:** drop the new `app.py` into `/root/gutlog`, overwrite when asked.
2. **SSH - confirm the right file landed:**
   ```bash
   grep -c "health3.db\|seeded_v3" /root/gutlog/app.py && wc -l /root/gutlog/app.py
   ```
   Expect `2`+ and ~1710 lines.
3. **SSH - libraries (already present from v2, this just guarantees it):**
   ```bash
   /root/gutlog/venv/bin/pip install flask gunicorn werkzeug
   ```
4. **SSH - restart & check:**
   ```bash
   systemctl restart gutlog
   systemctl status gutlog     # want green "active (running)"; q to exit
   ```
   If it fails: `journalctl -u gutlog -n 30 --no-pager`
5. **Browser:** open https://health.dr-manoj.in. On a fresh DB it shows a
   **Create password** screen (8+ chars). All 87 foods + presets load
   automatically. Log a test day to confirm writes.

## Fresh database, no migration
v3 uses a **new** file `health3.db`. The old v2 `health.db` is untouched -
leave or rename it. There is no data migration; v2 held negligible data.

## Automatic schema migration
On every start, `_migrate()` runs idempotent `ALTER TABLE ... ADD COLUMN`
statements for columns added after a DB was first created (currently
`vitals.temp`). Existing data is preserved; the column is simply added if
missing. This is how the temperature field reached an already-live DB
without a rebuild or password reset.

## Rebuilding on a brand-new server
```bash
mkdir -p /root/gutlog && cd /root/gutlog
python3 -m venv venv
venv/bin/pip install flask gunicorn werkzeug
# copy app.py into /root/gutlog
cp deploy/gutlog.service.example /etc/systemd/system/gutlog.service
systemctl daemon-reload && systemctl enable --now gutlog
# then reverse-proxy health.dr-manoj.in -> 127.0.0.1:8020 in OpenLiteSpeed
```

## Backups (see deploy/backup_gutlog.sh)
Back up three things, all in `/root/gutlog`: **`health3.db`**, **`uploads/`**,
**`health3.db.secret`**. Losing the secret only logs sessions out (no data
loss). Install the provided script + a 1 a.m. cron line.
