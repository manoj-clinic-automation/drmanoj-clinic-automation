# START HERE — SESSION 178

Paste this after the evergreen START_HERE (v5). Session-specific pickup for **S178**.

## Phase 0 (do first, every session)
1. Open `CANONICAL_MANIFEST.md` (**current at S177** — the S173–S176 fold debt is CLEARED); md5-verify every row. A mismatch halts work (D172/D188).
2. Read into context Tier 0 only: manifest · evergreen START_HERE · **KB_Register_v4_6_S177** · **HANDOFF_RUNBOOK_2026-08-14_Session177close_v111** · any open incident (none open). Open Tier 1 on demand.
3. **Expected manifest absences (NOT faults):** the base `Fault_Action_Register` file is not in project knowledge — its pin stays **v2.16 `1702b5a8…`** with the consolidated **F-82+F-83 append** (`Fault_Register_append_F82_F83_S177.md`) owed → v2.17 on owner apply. Superseded docs (Staff Daily Register v1.1, Salary System KB v1, KB_Asset_Register v1.8.1) are retained-historical rows.

## What closed last session (S177) — LIVE
- **Asset Register v1.11.0 (A-D24)** installed live, VPS smoke **342/0**: scanner-widget-led `/intake` (+ `/intake/scan_submit`, `/intake/slip/last`; `RECEPTION_OK` widened by exactly those endpoints) · `/purchases` spend analytics (`_inr()` Indian rupees, month/vendor bars, dashboard tile) · approved-bill → asset supplier/purchase-date backfill (non-clobber, idempotent).
- **Housekeeping closed:** `prune_backups.py` armed (manual, `/root/`) · shared `sarvam_ocr.py` verified single-copy at `/root/shared/` · test assets **#51–55 deleted** (54→49, zero orphans; undo backup `assets.db.predelete.2026-08-14_223751`). Rows #45–50 flagged for owner review, untouched.
- **Canon fold executed:** Archive → v1.25 (§S173–§S177 appended, prefix-hash proven) · Register → v4.6 · Estate Inventory → v1.1 · `KB_Asset_Register_v1_10_3` `07d01e80…` Tier-1 · manifest → S177.
- **Live md5 (asset):** `asset_register.py 0cd8fc3bfe8d39322c6162a41124bddf` · `smoke_test.py 6e72373325f808b1d7eaeb99f51a7b14` · `scanner_widget.js 4fe8c893…` · `/root/shared/sarvam_ocr.py b1cc567b…`. Clinic live files unchanged from S172/S176 (see Runbook §0).

## Live backlog (pick one — full list Runbook §2)
1. ⭐ **WABA go-live (F-82)** — still vendor-blocked (MyOperator HTTP 500). Probe `GET /chat/templates`; on 200: DRYRUN→"0" → restart → self-send → live. Coordinate with **Lokesh** before ANY token rotation.
2. **Owner action — commit `gitkit_S177.zip`** (assetapp v1.11.0 + tools + canonical-docs mirror). Repo currently at v1.10.3.
3. **Owner action — rotate** the asset-app + portal `/api/due` tokens (seen in screenshots).
4. **Asset rows #45–50** review (dup vendor practice entries) — keep or guarded-delete.
5. **A-D25 candidates:** durable OCR worker (F-83 fix) · consumption dashboards · Sarvam schema tuning · scanner-app shared-sarvam adoption.
6. Console w8/w9 · D223 gist tile · nightly `console_reviews.db` backup · F-81 dup rows · staff cockpit / reception-intake ideation (4 open decisions).

## Next-free numbers
- **Clinic:** **D313 · F-84.** **Asset-app:** **A-D25** (A-D24 = scanner-intake + spend + backfill, LIVE S177).

## Rules unchanged
Full-file replacements · build from md5-verified live source (D160/D188) · offline compile + smoke gate → `.new`-prenamed files → ONE &&-chained install block (md5 gate → `.bak` → `mv` → smoke gate → restart-or-rollback) · no pasted heredocs · one step at a time, wait for OK · mask patient numbers (last-4) + never print secrets · manual workflow stays as fallback.

> Asset app: **system `python3`** (F-53), `assetapp.service`, `/root/assetapp/`, `assets.db` (49 rows), roles owner/manager/reception (SSO doctor→owner · manager→manager · staff→reception fail-closed). Shared libs `/root/shared/` (`sarvam_ocr.py`, `SHARED_LIB_DIR`). Portal `/root/portal/portal.py` · `clinic-portal.service` · :8099. Clinic `/root/wa` scripts: `/root/wa/venv/bin/python3`.
