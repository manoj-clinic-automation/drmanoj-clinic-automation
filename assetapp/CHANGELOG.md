# CHANGELOG — Asset Register

All notable changes. Newest first. Deploy rule: **full-file replacement of `app.py` only — never touch `assets.db` or `uploads/`.**

---

## v1.4.2 — 13 Aug 2026 (Session 173) — *Grouped index (Phase C)*

**Changed**
- `/assets` is now a **grouped, collapsible index**: primary **Entity** (Dr Manoj Clinic / NK Pathology / Personal) headers with counts -> nested **Zone** groups -> the assets. Pure `<details>`/`<summary>` (no JS). Search filters within groups; unclassified assets group last so they are never hidden. Manager scope preserved (owner-only entities never appear).
- Only `assets_list()` changed; the rest of the file is byte-identical to v1.4.1.

**Tests:** 74/74.

---

## v1.4.1 — 13 Aug 2026 (Session 173) — *Admin: password reveal + secret masking*

**Added**
- **Set & reveal** password: set a user's password (typed, or *generate strong*); the value is shown **once** (passwords remain one-way hashed — they cannot be read back; the reveal is how you always control every login).
- WhatsApp **API token masked** behind a *Show API token* collapse (no longer printed on page load) + a **Rotate token** button.

**Tests:** 67/67.

---

## v1.4.0 — 13 Aug 2026 (Session 173) — *Taxonomy backbone + migration (Phase A)*

**Added**
- **3 owning entities** (`entities`: Dr Manoj Clinic, NK Pathology, Personal — each carries a default visibility) x **per-entity zones** (`zones`, 24 seeded). `assets.entity_id` + `assets.zone_id` columns.
- Idempotent seeding in `init_db()` (runs on every import; guarded by COUNT).
- **Backfill CLI** `python3 asset_register.py --migrate-taxonomy [--apply]` — dry-run by default, idempotent, **fail-loud** (refuses to apply if any live location is unmapped). Old location -> Entity/Zone via `LOC_TAXONOMY_MAP`. Old `location`/visibility kept as shadow (nothing lost; trivial rollback).
- Live migration applied: 49 assets -> Dr Manoj Clinic/Unassigned 37, NK Pathology/Unassigned 11, Personal/Dr Manoj 1.

**Tests:** 61/61.

---

## v1.3.0 — 13 Aug 2026 (Session 173) — *Shared, super-functional scanner (Stage 1A)*

**Added**
- Scanner extracted from the inline template into a **reusable, config-driven `scanner_widget.js`** served from disk (cache-busted by mtime; edit-and-drop, no restart). `/scan/<entity>/<id>` is now a thin shell that injects `window.SCANNER_CONFIG` and mounts the widget. Same widget is intended for Casepack next (`uploadUrl`/`uploadFields`/`nameBase`/`backUrl` config).
- Features: **multipage PDF**; **JPEG->PDF** via multi-select gallery import + "add whole image (no crop)"; **per-app default filename** (editable); **per-page delete** + retake; **ID-card mode** (front+back composed onto one A4 page); **batch mode** (each scan = its own auto-named, renamable file, stays in scanner).
- Carried verbatim from v1.2.0: live camera + device picker, edge/corner handles, magnifier loupe, Heckbert homography warp, jsPDF + JPEG fallback.

**Tests:** 52/52. New `/scan/widget.js` route (public, inert code).

---

## v1.2.0 — early Aug 2026 (reconstructed from code; not previously changelogged) — *Live camera, drafts, OCR groundwork, SSO*

*Reconstructed at the S173 close from the live source, since this version shipped between sessions without a CHANGELOG entry. Entrypoint was renamed `app.py` -> `asset_register.py` (the systemd unit runs `asset_register:app`; `app.py` is now dead and should be git-removed).*

**Added**
- Scanner v2: **live camera** (`getUserMedia`) + device picker (works on desktop webcams), **round-corner + square-edge handles** with device-pixel-aware hit zones, **magnifier loupe**, shaded crop preview, reset-outline. Fixed the unreliable corner dragging of v1.1.0.
- **Drafts**: scan/upload first -> `drafts` table -> "Create asset ->" promotes into an asset with the doc auto-attached. `/scan/draft/0`.
- **OCR groundwork**: `attachments.document_text` + `ocr_status` columns; `digitise_document()` **stub** (returns skipped/pending; the real Sarvam Doc-AI async job flow is planned). Document text is searchable (search reads `document_text`); sensitive docs are searchable-but-never-displayed.
- **Clinic SSO** (Session 158): accepts a valid portal `clinic_sso` cookie as login (doctor->owner, manager->manager); falls back to native `/login` if the SSO modules are absent.
- `/api/due?token=` JSON feed for the WhatsApp cron.
- `init_db()` now runs on every import (gunicorn only imports the module) so schema/migrate never silently skip on an existing DB.

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
