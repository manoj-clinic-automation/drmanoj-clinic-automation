# CHANGELOG — Asset Register

All notable changes. Newest first. Deploy rule: **full-file replacement of `app.py` only — never touch `assets.db` or `uploads/`.**

---

## v1.1.0 — 24 July 2026 — *Built-in scanner*

**Added**
- Browser-native document scanner (`/scan/<entity>/<id>`) reachable from a 📷 **Scan document** button on every asset and staff record.
  - Camera capture, four draggable corner handles, perspective correction (Heckbert unit-square→quad homography, inverse-sampled), document mode (greyscale + percentile contrast stretch), multi-page accumulation, jsPDF assembly, direct upload.
  - Falls back to single-page JPEG if the jsPDF CDN is unreachable.
  - Scans on a `hide_price` asset are automatically flagged `sensitive`.
- `accept="image/*,.pdf,.doc,.docx"` on file inputs so mobile browsers offer camera and Drive pickers cleanly.

**Fixed**
- **P0 — HTML was being escaped.** `render_template_string` autoescaped the inner page body when nested into the base template, so pages rendered as visible markup text. Body is now wrapped in `Markup()`. Structural regression check added to the suite.

**Tests:** 34 → 41 checks (Step 9 added). All passing.

---

## v1.0.0 — 24 July 2026 — *Initial release*

**Added**
- Flask + SQLite single-file app; session-epoch auth (GutLog v3.1 pattern); three seeded users, two roles.
- Assets: 17 fields, service logs, attachments, warranty and contract-renewal expiries with per-row thresholds (default 60 days).
- Staff module: records, tracked expiries, documents with owner-only flag.
- Visibility: location classes (`general` / `owner_only`) plus per-asset `hidden` and `hide_price`; `hide_price` extends to invoice files.
- Manager-edit price preservation (a manager editing a `hide_price` asset cannot null out the stored price).
- Dashboard with amber/red renewal states across assets and staff.
- Admin page (owner): locations, password resets, API token display.
- `GET /api/due?token=` JSON endpoint for the WhatsApp reminder cron.
- `smoke_test.py` — 8 steps, 34 checks, runs against a temp database.

**Deployed:** 24 July 2026 — `assets.dr-manoj.in`, systemd unit `assetapp.service`, gunicorn 2 workers on 127.0.0.1:8030, OpenLiteSpeed reverse proxy, Let's Encrypt SSL, nightly local backup cron at 02:30 with 14-day retention.
