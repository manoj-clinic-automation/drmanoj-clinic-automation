# DEPLOY — Asset Register

Numbered steps. One action per step. ✓ marks a verification checkpoint.

---

## A. Routine update (replacing `app.py` with a new version)

1. Run the test suite locally first: `python3 smoke_test.py` → expect `74 passed, 0 failed`.
2. SSH: back up the database before touching anything —
   `cp /root/assetapp/assets.db /root/backups/assets_pre_update_$(date +%F).db`
3. WinSCP: drag the new `asset_register.py` (and `scanner_widget.js` when changed) into `/root/assetapp/`. **Full-file replacement only.** Compile-gate first: `python3 -m py_compile asset_register.py`. Keep a `.bak` of the old file.
4. SSH: `systemctl restart assetapp`
5. SSH: `systemctl status assetapp --no-pager` → ✓ **active (running)**
6. SSH: `curl -s http://127.0.0.1:8030/login | grep -o "Sign in"` → ✓ prints `Sign in` twice
7. Browser: load https://assets.dr-manoj.in, sign in, open one asset → ✓ page renders normally

**Never** upload or overwrite `assets.db` or anything in `uploads/`.

### A.1 Schema / data migrations (v1.4.0+)
- Schema (new tables/columns) auto-applies on restart — `init_db()` runs on import and is idempotent (`CREATE IF NOT EXISTS` + guarded `migrate()`). No separate `--init` needed.
- **Data** migrations are explicit and dry-run-first. Taxonomy backfill:
  - `cd /root/assetapp && python3 asset_register.py --migrate-taxonomy`  (dry-run, changes nothing — prints the plan)
  - `python3 asset_register.py --migrate-taxonomy --apply`  (commits; idempotent; refuses if any live location is unmapped in `LOC_TAXONOMY_MAP`)
- Use the **system `python3`** (the one gunicorn runs), not the `/root/wa` venv.

---

## B. First-time build (reference — completed 24 Jul 2026)

**Upload**
1. WinSCP → create `/root/assetapp/` → drop `app.py` in.

**Dependencies**
2. `pip3 install flask gunicorn` (add `--break-system-packages` if pip objects).
3. `which gunicorn` → note the path (this server: `/usr/local/bin/gunicorn`).

**Service** — `/etc/systemd/system/assetapp.service`:
```
[Unit]
Description=Asset Register
After=network.target

[Service]
WorkingDirectory=/root/assetapp
ExecStart=/usr/local/bin/gunicorn -w 2 -b 127.0.0.1:8030 asset_register:app
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```
4. `systemctl daemon-reload && systemctl enable --now assetapp`
5. `systemctl status assetapp --no-pager` → ✓ active (running)
6. `curl -s http://127.0.0.1:8030/login | grep -o "Sign in"` → ✓ twice

**DNS**
7. GoDaddy → dr-manoj.in → DNS → Add record: **A**, name `assets`, value `93.127.195.49`.
   Mobile deep link: `https://dcc.godaddy.com/manage/dr-manoj.in/dns` (use desktop-site mode if the editor hangs).
8. `ping -c 2 assets.dr-manoj.in` → ✓ resolves to 93.127.195.49

**Web server**
9. CyberPanel → Websites → Create Website → `assets.dr-manoj.in`.
10. Manage → **vHost Conf** → append at the very bottom (delete nothing):
```
extprocessor assetapp {
  type                    proxy
  address                 127.0.0.1:8030
  maxConns                100
  initTimeout             60
  retryTimeout            0
  respBuffer              0
}

context / {
  type                    proxy
  handler                 assetapp
  addDefaultCharset       off
}
```
11. Save → `systemctl restart lsws`
12. Manage SSL → Issue SSL (Let's Encrypt). DNS must resolve first.
13. ✓ https://assets.dr-manoj.in shows the Sign in page with a padlock.

**First login**
14. Sign in as each of `manoj`, `bhawna`, `manager` and change every password (min 8 chars).
15. As `manoj` → **Admin** → copy the API token into secure notes.
16. ✓ On a phone: open the site → any asset → 📷 Scan → camera opens. (Requires HTTPS.)

**Backup**
17. `mkdir -p /root/backups`
18. Install the nightly cron (02:30, 14-day retention):
```
(crontab -l 2>/dev/null; echo '30 2 * * * tar -czf /root/backups/assetapp_$(date +\%F).tar.gz -C /root assetapp/assets.db assetapp/uploads 2>/dev/null; find /root/backups -name "assetapp_*.tar.gz" -mtime +14 -delete') | crontab -
```
19. ✓ `crontab -l | tail -2` shows the new line.

---

## C. Restore from backup

1. `systemctl stop assetapp`
2. `cd /root && tar -xzf /root/backups/assetapp_YYYY-MM-DD.tar.gz`
3. `systemctl start assetapp`
4. ✓ Sign in and confirm a known asset and its files are present.

---

## D. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `systemctl status` says failed | wrong gunicorn path in unit | `which gunicorn`, correct `ExecStart`, `daemon-reload`, restart |
| CyberPanel default page instead of app | vHost block not applied | re-check the paste sits at the bottom of vHost Conf, then `systemctl restart lsws` |
| Certificate warning | SSL issued before DNS propagated | confirm `ping`, re-run Issue SSL |
| Camera does not open on phone | page loaded over HTTP | use the https:// address |
| Page shows raw HTML markup as text | autoescape regression (fixed in v1.1.0) | ensure body is wrapped in `Markup()`; run smoke test |
| Everyone logged out unexpectedly | auth-epoch was bumped | expected after "Sign out all devices"; simply sign in again |
