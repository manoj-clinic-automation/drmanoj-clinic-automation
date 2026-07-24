# DOSSIER — Asset Register

**System name:** Asset Register
**Version:** v1.1.0
**Status:** Live in production
**Created:** 23–24 July 2026
**Owner:** Dr Manoj (personal Google account for backups; VPS-hosted)
**URL:** https://assets.dr-manoj.in
**Repo path:** `drmanoj-clinic-automation/assetapp/`

---

## 1. Purpose

Single register for **owned equipment and its contracts** across NK Pathology, the clinic, and personal/household — plus **staff records with their documents and expiry dates**.

The system exists for two reasons:

1. **Renewal awareness** — nothing (warranty, AMC, CMC, contract) should expire unnoticed.
2. **Continuity through personnel change** — physical asset files live in cabinets accessible to the current manager and the accountant. If the manager leaves, institutional knowledge leaves with him. A system holds it independently of any one person.

---

## 2. Scope boundaries (important — prevents dual-truth drift)

| In scope | Out of scope |
|---|---|
| Owned equipment (lab, medical, IT, electrical, appliances, furniture, vehicles) | Personal identity documents (DL, passport, etc.) — these stay in the **existing GAS document system** |
| Consumables with replacement cycles (batteries, inverters) | Patient data of any kind (PHI never enters this system) |
| AMC / CMC / warranty contracts | Pharmacy or lab inventory (Marg ERP / Labmate own these) |
| Staff records + appointment documents + tracked expiries | Payroll and salary (Salary_System_2026) |
| Invoices and contract scans attached to records | — |

**Ruling made 24 Jul 2026:** Dr Bhawna's driving licence was entered here in error during set-up. It belongs to the GAS document system. Personal identity documents are not asset-register items.

---

## 3. Architecture

- **Single-file Flask app** (`app.py`), SQLite database, server-side rendered HTML. No build step, no JS framework, no external runtime dependencies beyond Flask + gunicorn.
- **Storage is VPS-primary.** Database and uploaded files live on the VPS, inside the app's permission gates. Google Drive is used for **backup only** (encrypted archive), never for live file storage.
  - *Rationale (24 Jul 2026):* storing live files in Drive would place them outside the app's role system — Drive links are reachable by anyone holding them, defeating the `hide_price` rule. Google's durability is obtained through backup, not through live storage.
- **Roles are designed in, not retrofitted.** Two roles (`owner`, `manager`), three user identities.
- **Generic expiries + attachments schema.** Any entity type can carry dates-to-watch and files. Assets and staff use it today; future modules attach without schema rework.

### Files and paths

| Item | Path |
|---|---|
| App | `/root/assetapp/app.py` |
| Database | `/root/assetapp/assets.db` |
| Uploaded files | `/root/assetapp/uploads/` |
| Service unit | `/etc/systemd/system/assetapp.service` |
| Local backups | `/root/backups/assetapp_YYYY-MM-DD.tar.gz` (14-day retention) |
| Bind address | `127.0.0.1:8030` (behind OpenLiteSpeed reverse proxy) |
| gunicorn binary | `/usr/local/bin/gunicorn` |

### Environment overrides (optional)
`ASSETS_DB`, `ASSETS_UPLOADS` — default to paths beside `app.py`. Used by the smoke test to run against a temp database.

---

## 4. Users and permissions

| Username | Display | Role |
|---|---|---|
| `manoj` | Dr Manoj | owner |
| `bhawna` | Dr Bhawna | owner |
| `manager` | Manager | manager |

Seeded passwords (`change-me-*`) were **changed at first login on 24 Jul 2026** and must be treated as burned — they appeared in a chat transcript.

**Owner can:** everything, everywhere — including delete, password resets for all users, adding locations, viewing the API token, and "sign out all devices".

**Manager can:** view and add assets in *general* locations, edit them, log services, upload and scan documents, view renewals, create and edit staff records.

**Manager cannot:** see or reach anything in owner-only locations, see assets flagged `hidden`, see prices or invoices on assets flagged `hide_price`, delete anything, access `/admin`.

**Audit trail:** every asset, staff record, service log and file upload stores `created_by` / `uploaded_by`. Service logs display "Entered by" in the UI. This is why three identities exist rather than one shared login — a shared login would have given no attribution.

---

## 5. Visibility model

Visibility is **attribute-based**, not per-row ticking, so nothing depends on someone remembering to flag a record.

**Location classes** (`locations.visibility`):
- `general` — NK Path, Clinic
- `owner_only` — Personal – Dr Manoj, Personal – Dr Bhawna, Home (Shared)

Managers' queries never touch owner-only rows: they are absent from lists, search, dashboard and the asset detail route (403 on direct URL).

**Per-row overrides** (owner-set, on top of location class):
- `hidden` — hides the whole asset from the manager even in a general location.
- `hide_price` — asset remains visible, but purchase price, contract cost and service-log costs are suppressed.

**Rule: `hide_price` extends to files.** An invoice *is* a price disclosure. Files uploaded to a `hide_price` asset are automatically marked `sensitive`, and sensitive files are excluded from the manager's file list and return 403 on direct download. The manager can scan an invoice *in* and then cannot retrieve it — deliberate, and covered by tests.

**Manager edit safety:** when a manager edits a `hide_price` asset, the price fields are absent from his form. The app re-applies the stored values instead of writing NULL — a manager edit can never silently erase a hidden price. Regression-tested (Step 5).

**Staff records** carry `hidden` (owner-only record) and per-document `sensitive` (owner-only document).

---

## 6. Expiries and reminders

- Amber when due within the threshold, red when overdue. Threshold is **60 days for everything** — warranties, AMC and CMC alike.
  - *Decision 24 Jul 2026:* an earlier proposal for 90 days on AMC/CMC was rejected — AMC renewal cycles are standard and predictable in this field, so one uniform number is simpler to hold in the head.
- `expiries.threshold_days` is per-row, so an individual item can override (e.g. batteries with a known short cycle).
- Dashboard shows all amber/red items for the signed-in user's visibility scope, assets and staff together.

**WhatsApp integration hook:** `GET /api/due?token=<token>` returns JSON of every amber/red item (all scopes — it is a server-to-server endpoint). Token is generated at first DB creation and displayed on the Admin page. Consumed by a cron job in the *Clinic Systems & Automation* project — **not yet wired as of 24 Jul 2026.**

---

## 7. Built-in scanner

Browser-native document scanner on every asset and staff record — no third-party scanner app, no account, no app-switching.

Flow: camera capture → four draggable corner handles → **perspective correction via Heckbert unit-square→quad homography with inverse sampling** → optional document mode (greyscale + 5th/95th-percentile contrast stretch) → multi-page accumulation → jsPDF assembly → direct upload to the record.

Design notes:
- **Corner placement is manual by design.** Automatic edge detection needs a heavy CV library that would slow every page load on phones; four drags take about five seconds and beat mis-detected edges.
- **CDN dependency with graceful degradation.** jsPDF loads from cdnjs. If unreachable, the scan is saved as a JPEG of page one rather than lost, with a message shown.
- **HTTPS is mandatory** — mobile browsers deny camera access over plain HTTP.
- Scanning on a `hide_price` asset sets the `sensitive` flag automatically.

Rejected alternatives: Google Drive scan (app-switching, staging-copy discipline required), Adobe Scan (extra account, own cloud, awkward share-out).

---

## 8. Testing

`smoke_test.py` — 9 steps, 41 checks, runs against a temporary database in `/tmp`, leaves production untouched.

Coverage: seeding and login, owner-only location isolation, manager creation rights and refusals, `hide_price` suppression, manager-edit price preservation, sensitive-file gating, dashboard scoping, API token auth, deletion rights, staff module, auth-epoch invalidation, scanner routes, and HTML-not-escaped structural check.

**Run before every deploy:** `python3 smoke_test.py` — expect `41 passed, 0 failed`.

---

## 9. Known limitations

- Attachment size is unbounded in code (relies on server limits) — revisit if large PDFs appear.
- No pagination on asset or staff lists — fine to a few hundred rows.
- No CSV export yet.
- Search covers name, vendor and serial only.
- Scanner corner detection is manual (see §7).
- `/api/due` returns all scopes regardless of visibility flags — acceptable because it is token-gated and server-consumed, but it must never be proxied to a browser session.

---

## 10. Decision log

| Date | Decision | Reason |
|---|---|---|
| 23 Jul | Google Sheet in personal Drive, not clinic account | register spans personal + business; clinic account is staff-accessible |
| 23 Jul | Build structure first, scan invoices incrementally | waiting for complete paperwork is how registers stay empty |
| 23 Jul | Notion holds one register row, not a parallel copy of the data | dual-entry registers drift apart |
| 24 Jul | Move from Sheet to Flask app | a designated operator (manager) doing routine entry changes the usage profile that justified a spreadsheet |
| 24 Jul | Three identities, two roles — not one shared login | shared login gives no audit trail; extra cost is one table row |
| 24 Jul | Roles designed in from schema day one | greenfield multi-user is cheap; retrofitting is not (GutLog lesson) |
| 24 Jul | Staff module built in v1, loaded with data later | the platform is for surviving manager transition; capability first, data when ready |
| 24 Jul | VPS-primary storage, Drive for encrypted backup only | live Drive files sit outside the app's access control |
| 24 Jul | Backups to **personal** Google Drive | matches ownership of the register; clinic account never touches this system |
| 24 Jul | Uniform 60-day threshold | AMC cycles are standard in this field; one number is easier to hold |
| 24 Jul | Built-in scanner over Drive scan / Adobe Scan | removes app-switching and third-party accounts from the manager's routine |
| 24 Jul | Backlog OCR via chat, not an API pipeline | one-time work does not justify a maintained integration |
| 24 Jul | Sarvam Vision named as the engine for future autofill (v1.3) | already a vendor for saaras transcription — no new dependency; Indic-first document model. Gated on trial, per the sarvam-105b lesson |
