# KB — Asset Register (v1.10.3)

**Status:** LIVE, deployed and confirmed working by owner (S176 — all installs uploaded to VPS).
**Supersedes:** `KB_Asset_Register_v1_8_1.md` (and all earlier Asset Register KB entries).
**KB standard:** evidence-only; `ASSUMED:` flags where not directly verified this session; risk section lists only actionable items.

---

## 1. What it is
A single-file Flask + SQLite web app that tracks the clinic/hospital/personal **asset estate** (~54 rows live, incl. a few owner test rows to prune), their locations, service history, warranty/AMC renewals, attached documents, and a **purchase-bill ledger** with **Sarvam OCR** auto-fill, a **reception scan-first intake**, **maker-checker approval**, and a **vendor directory**.

- **URL:** https://assets.dr-manoj.in
- **Access model:** login-gated, three roles:
  - **owner** (full; = SSO `doctor`) — sees everything incl. purchase ledger, admin, prices.
  - **manager** (general-visibility; = SSO `manager`) — no owner-only assets/locations, no admin; **can now open + approve Consumable bills** (checker), cannot approve Asset-kind bills.
  - **reception** (= SSO `staff`) — **fail-closed, whitelist-contained**: can reach ONLY the intake screen + its own slips; every other route 403s server-side; dashboard redirects to `/intake`. Unknown SSO roles get **no access** (login redirect).

## 2. Where it runs (verified)
- **VPS dir:** `/root/assetapp/`
- **App file:** `asset_register.py` (v1.10.3)
- **DB:** `assets.db`
- **Service:** `assetapp.service` (systemd), gunicorn `-w 2`, bound to `127.0.0.1` behind the web server.
- **Runtime:** the **system `python3`** (gunicorn shebang `#!/usr/bin/python3`) — **NOT** the `/root/wa` venv (rule F-53). Verified S176: `sarvamai` imports in `/usr/bin/python3`; gunicorn runs `/usr/bin/python3`.
- **Shared module:** `sarvam_ocr.py` — loader checks `/root/shared/` first (via `SHARED_LIB_DIR`), falls back to the app's own dir; currently resolved from `/root/assetapp/`. `ASSUMED:` not yet relocated to `/root/shared/`.
- **Sarvam key:** `SARVAM_API_KEY` present in the running service environment (verified S176 via `/admin` "Sarvam key configured: yes" and a live extract). Read at module import; not in code. **Sarvam OCR is confirmed working end-to-end** (see §7).
- **SSO:** accepts the portal `clinic_sso` cookie (HMAC, scoped `.dr-manoj.in`). Shim maps portal role → app role: `doctor→owner`, `staff→reception`, `manager→manager`; anything else → fail-closed (no access). Reception reaches the app from the portal's **"Scan Purchase"** tile (portal.py, S176).

## 3. Feature map at v1.10.3 (routes)
- `/` dashboard · `/assets` index · `/assets/new` · `/assets/<id>` · `/assets/<id>/edit` · `/assets/<id>/service` · `/assets/<id>/delete`
- `/renewals` (warranty/AMC + **consumable expiry**, grouped, owner) · `/drafts` (scan-first) · `/staff` register + service entries
- **`/assets` index:** grouped by **LOCATION**, collapsible sections with counts + due badges; columns **Name · Category · Serial · Supplier · Purchased · Status · Contract**; cascading facets (Entity→Zone→Category/Kind/Status) + search (name/vendor/serial/document-text). Service **contacts render inline** on the asset page (from the vendor directory, provider preferred).
- **Reception intake (A-D21/22/23):**
  - `/intake` — one screen: **📷 Take a photo** (camera-capture) + **📁 choose photo/PDF** fallback, both proper labelled buttons with a filename confirmation (A-D22); "Recent stamped submissions" list; reception sees ONLY its own.
  - `/intake/submit` — stores a **draft** bill + scan instantly, assigns a **monotonic stamp** (`B-0001…`, never reused even after reject), launches the background Sarvam fill, returns the **stamp slip**.
  - `/intake/slip/<bid>` — big stamp number + submitter + IST time (handwrite on the paper bill).
- **Purchase ledger / maker-checker (A-D21/23):**
  - `/bills` list (search + kind filter + **status filter** + **pending badge** + OCR marker) — **open to checker (manager 200)**.
  - `/bills/new` (dynamic line-item blocks; blanks ignored) · `/bills/<id>` detail · `/bills/<id>/edit` ("Complete / edit") · `/bills/<id>/delete`.
  - `/bills/<id>/approve` — **server-side lane guard**: Consumable → manager|owner; **Asset-kind → owner (doctor) ONLY**; **blank bill (no vendor/total/items) requires explicit `confirm_blank`** (A-D23).
  - `/bills/<id>/reject` — void (stamp + reason kept; stamp never reused).
  - `/bills/<id>/reread` — **A-D23**: re-run Sarvam on the stored scan (non-clobber; drafts AND approved; recovers a read lost to a restart/race).
  - `/bills/<id>/file` — serves the stored scan (open to checker).
  - `/purchases` (per-item rate-drift, period consumption, expiring-soon) — **owner-only**; only **approved** bills feed it.
- **Bill OCR (Phase E / A-D16):** `/bills/extract` — upload → `sarvam_ocr.extract()` → tolerant `_map_bill()` → pre-filled `/bills/new`. Background intake fill uses the same `_bg_extract()` path.
- **Vendor directory (A-D21):** `/vendors` list · `/vendors/<id>` (add/deactivate contacts) — owner + manager. `vendors` + `vendor_contacts` (multi-person: engineer/service-manager/sales/accounts/other, active flag).
- **API:** `/api/due` (token-gated) for the WhatsApp due-digest cron.
- **Scanner widget** (`scanner_widget.js`): in-browser camera + **Document mode** (integral-image shadow-flatten `enhanceGray()`). *(Intake uses the plain camera input, not this widget — a future enhancement.)*
- **Admin:** users/passwords, managed pick-lists, locations, `/api/due` token (masked + rotate), screen palette, **"Sarvam key configured" readout**.

## 4. Data model (key tables)
- `assets` (location_id → `locations`; category, purchase_date, price, vendor, serial_no, status, contract fields, hide_price, entity_id/zone_id/kind overlay, **`bill_id`** back-ref from A-D20 bridge, …).
- `locations` (flat, UNIQUE name, general/owner_only) — populated for every asset; basis of index grouping. `entities` + `zones` = hierarchical overlay.
- `expiries` (warranty/AMC/contract + consumable item-expiry → renewals + due badges).
- `attachments` (files + extracted `document_text` for search).
- **`bills`** — kind, vendor, bill_no, bill_date, total_amount, notes, source_stored/source_orig **+ workflow cols:** `stamp_no`, `status` (draft/approved/rejected, DEFAULT `'approved'` grandfathers old bills), `submitted_by`, `submitted_at`, `approved_by`, `approved_at`, `reject_reason`, `vendor_phone`, `vendor_email`, **`ocr_status`** (NULL / reading / read / empty / failed — A-D23).
- **`bill_items`** — item_name, pack_size, quantity, rate, amount, make, model, serial_no, batch, expiry, hsn, **`asset_id`** (A-D20 bridge).
- **`vendors`** (name UNIQUE, phone, email, address, gstin, notes) + **`vendor_contacts`** (vendor_id, person_name, role, phone, email, active). 18 vendors auto-seeded on the A-D21 install.
- All dates stored **ISO on save** via `_norm_date()` (A-D20); idempotent startup `normalise_dates()` self-heal.

## 5. Decisions (asset-app scope)
- **A-D16** — Sarvam extraction is a shared VPS service (`sarvam_ocr.py` on `sys.path` via `SHARED_LIB_DIR`, default `/root/shared`); SDK-based; graceful-skip.
- **A-D17 v2** — bill schema = asset+consumable superset across `bills`+`bill_items` (analytics, not just form pre-fill).
- **A-D18** — scanner enhancement = integral-image local-mean shadow-flatten (`enhanceGray()`).
- **A-D19** — `/assets` index grouped by location, with Serial/Supplier/Purchased columns.
- **A-D20** (v1.9.0) — **Date-normalisation keystone**: tolerant `_norm_date()` stores ISO on save (bill dates + item expiries), idempotent `normalise_dates()` self-heal; **bill→asset bridge** ("+ asset" per line, two-way `asset.bill_id ↔ bill_item.asset_id`, seeds item-expiry renewal); consumable expiry in owner `/renewals`; from-bill backlink on the asset page. Smoke 236/0.
- **A-D21** (v1.10.0) — **Reception scan-first intake** (SSO `staff`→fail-closed `reception`; stamp slips `B-0001…`; instant draft+scan; background Sarvam fill, non-clobber); **maker-checker bills** (status; Consumable→manager, Asset→doctor ONLY, server-side lane guard; reject=void); **vendor directory** (`vendors`+`vendor_contacts`, seeded + grows on approval + Sarvam header; inline service contacts on the asset page). Only approved bills feed analytics/renewals/bridge. Smoke 293/0; 18 vendors seeded.
- **A-D22** (v1.10.1→v1.10.2) — **Intake camera fix**: the single `image/*,.pdf` input silently suppressed the phone camera; split into a dedicated camera-capture control + a photo/PDF fallback, rendered as proper labelled buttons (camera/folder icons) with a filename confirmation. Smoke 300/0 → 301/0.
- **A-D23** (v1.10.3) — **OCR no longer silent**: bills carry `ocr_status` (reading/read/empty/failed) shown on the draft and the Purchases list; **"Re-read with Sarvam"** button re-runs extraction on the stored scan (non-clobber; drafts + approved; recovers reads lost to a restart/race); **blank-bill approval requires explicit confirm** (server-enforced). Smoke 315/0.
- **Next-free:** **A-D24.**

## 6. Canonical files + md5 (v1.10.3 — LIVE, verified S176)
| File | md5 | Notes |
|---|---|---|
| `asset_register.py` | `b30983710238863b6d98b8e773c6923c` | main app, **v1.10.3** |
| `smoke_test.py` | `65d6cd0e06d1e4fb9947175df5054152` | dev-only; **315 passed / 0 failed** |
| `scanner_widget.js` | `4fe8c89386a54ce90786823b53df55bc` | unchanged since v1.8.1 |
| `sarvam_ocr.py` | `b1cc567b70b5e67c8c021fa22590babf` | unchanged; shared OCR module |
| `portal.py` (cross-ref, `/root/portal/`) | `da4177091ba9f188be6a0ff3eaf25bd8` | "Scan Purchase" tile (staff+manager) |

Git kit (S176): `gitkit_S176.zip` (folder-wise: `assetapp/`, `portal/`, `COMMIT_MSG.txt`, `KIT_MANIFEST.txt`). Canonical code store: GitHub `manoj-clinic-automation/drmanoj-clinic-automation` (repo was pre-v1.8.1; this kit brings it to v1.10.3).

## 7. Verified this session (S176)
- **Sarvam OCR works end-to-end.** Ran directly on **B-0001**'s real 3 MB bill photo: `status: done` → vendor *Shri Ram Enterprise*, bill_no *SRE/737/2025-26*, total *₹1,30,003*, **5 line items**. Key present in service + `sarvamai` imports in the gunicorn interpreter.
- **B-0001 is the first real reception bill** (submitted by Shivani via `/intake`). It initially arrived **blank** — root cause F-83 (below), fixed by A-D23; **recoverable** by opening B-0001 → **Re-read with Sarvam** (non-clobber fills the 5 items). Do not delete B-0001.
- Reception intake live (stamp slip renders, draft+scan stored). 18 vendors auto-seeded. Portal "Scan Purchase" tile live for alisha/shivani (staff) + shavez (manager).
- Every install gated offline and re-verified in place by md5 before swap (F-66); each smoke suite green on the VPS (final 315/0).

## 8. Open items (actionable)
- **Owner:** commit the **S176 git kit** (repo is behind at pre-v1.8.1; kit brings it to v1.10.3). Rotate the `/api/due` WhatsApp token + update its cron. Rotate the `/api/due` token that appeared in earlier screenshots (portal `/admin`).
- **Recovery:** open **B-0001** → **Re-read with Sarvam** → confirm the 5 items + vendor + ₹1,30,003 populate and the badge flips to ✓ auto-read.
- **Housekeeping:** delete the stray owner **test assets** (rows ~51–55); relocate `sarvam_ocr.py` → `/root/shared/` (loader tolerates either).
- **Data:** Supplier/Serial/Purchased columns blank for legacy assets until edited/backfilled from bills.
- **Build (A-D24 candidates):** intake to adopt the full shadow-flatten scanner widget (currently plain camera input); Phase-3 doctor-only staff cockpit (separate); consumption dashboards; scanner-app to adopt shared `sarvam_ocr.py`.

## 9. Findings (asset-app scope)
- **F-83** (S176) — the reception intake's **background OCR fill is a fire-and-forget daemon thread**: it dies if the service restarts mid-read, and (before A-D23) only touched `status='draft'` bills, so a read could be **silently lost** with no trace (the `except: pass` swallowed everything). This is why B-0001 arrived blank (several restarts followed its submit for the v1.10.1 install). **Mitigated by A-D23**: the outcome is now visible (`ocr_status`) and recoverable (Re-read button, non-clobber, works on any status). Residual: re-read still uses a thread (owner chose "button only", **no cron**), so recovery of a mid-read restart is a manual tap — acceptable at a few bills/day.

## 10. Change log
- **v1.7.0 → v1.8.1:** A.4 punch-list + Phase D purchase ledger + Phase E Sarvam extract + scanner shadow-flatten; `/assets` grouped-by-location (A-D19); Sarvam schema-description fix; `_map_bill()` whitespace-collapse.
- **v1.8.1 → v1.9.0 (A-D20):** date-normalisation keystone + bill→asset bridge + consumable renewals. Smoke 236/0.
- **v1.9.0 → v1.10.0 (A-D21):** reception intake + maker-checker bills + vendor directory. Smoke 293/0; 18 vendors seeded.
- **v1.10.0 → v1.10.2 (A-D22):** intake camera fix + labelled buttons + filename feedback. Smoke 301/0.
- **v1.10.2 → v1.10.3 (A-D23):** visible OCR status + Re-read button + no-blank-approve guard. Smoke 315/0.
- **Portal (S176):** portal.py gained the config-driven "Scan Purchase" tile (staff+manager). `da4177091ba9f188be6a0ff3eaf25bd8`.
