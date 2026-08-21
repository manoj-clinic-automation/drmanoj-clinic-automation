# S195_NCSCAN — Daily Sale v2: no-payment bills + per-bill scan

Restores the no-payment bills (home medicine / procedure / other) the v2 rewrite
dropped, adds a per-bill scan with a loud ✓, a compact mobile layout, a prominent
live drawer figure, and a submit screen that lists every attachment.

Backend (finance_app.py, mirrors the proven expense-scan):
- day_noncash_bill gains a nullable `noncash_uid`; new `noncash_attachment` table
  keyed on (day_entry_id, noncash_uid) — both created lazily (additive DDL).
- POST /finance/api/day captures a stable uid per bill and stores it.
- Day-read returns each bill's `uid` + `has_file`.
- New: `POST /finance/api/day/<d>/noncash-scan/<uid>` (upload) and
  `GET /finance/scan-noncash/<d>/<uid>` (the shared scanner host page).

Page (finance_ui/finance_daily.html): compact, Day+Sale merged, live drawer strip,
per-bill 📎 Scan bill + ✓, Save→✓ Saved, Submit lists attachments, Transfer at bottom.

Safety: currency-gated to S194E (d2863c30); backs up BOTH files; runs the app's
own --selftest (all-green + not shrunk); restarts clinic-finance; auto-rolls-back
BOTH on any red. New finance_app.py md5: f25ed48923a5647ba1f6111bad0737d3 .

Install:
  cd /root/deploy/repo && git pull
  cd deploy_kits/S195_NCSCAN && bash install_s195_ncscan.sh
