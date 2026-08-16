# KB — Asset Register (v1.11.0-R · RECONSTRUCTED at Session 181)

> ## ⚠ PROVENANCE — READ THIS FIRST. THIS IS A RECONSTRUCTION, NOT A RECOVERY.
>
> **The original `KB_Asset_Register` v1.11.0 (md5 `1c147beb44ad4413d3b147ad70e43ea7`, written at
> S178) is GONE.** It was one of three canonical documents lost because the cold-backup cadence had
> lapsed for nine sessions — **F-89**. A hash-based recovery run at the S180 close hashed **26,745
> files** across the owner's drives — by md5 rather than filename (**D188**), and opening `.zip`
> archives — and did not find it; the three lost documents were confirmed absent on both `D:` and
> `C:`. It was closed under **D316** as **LOST-RECONSTRUCTABLE**: current, but rebuildable from a
> verified predecessor plus the Archive.
>
> **This file is that rebuild. It does NOT and CANNOT carry the lost md5.** Anything claiming to be
> v1.11.0 at `1c147beb…` is not this file. The suffix **-R** exists so the two can never be confused
> — a filename is not provenance (**D188**), so the version string itself carries the warning.
>
> **PRIMARY sources — both hash-verified at the S181 Phase 0, neither from memory (D172):**
> 1. **`KB_Asset_Register_v1_10_3.md`**, md5 `07d01e80a1d6a49884650d2e542205df` — the recovered
>    predecessor. Per the §S180 recovery table it was found in the git repo's `canonical-docs/`
>    (`D:\dr-manoj-git\drmanoj-clinic-automation\canonical-docs\`), matching its manifest pin exactly.
> 2. **`KB_History_Archive` v1.28 §S177**, md5 `0e8b4bd6b4e09fd2dcb6ce7fbf2c14ad` — the A-D24 wave,
>    the housekeeping, and the live md5s, as recorded at the S177 close.
>
> **SECONDARY sources, each flagged where used** — because a document that names two sources and
> quietly draws on five is doing the thing this project keeps catching (**D188**): Archive **§S173 /
> §S174** (the §5A decision index), **§S175** (the A-D16–A-D19 wording and the `settings`/`setting_or()`
> detail), **§S174/§S175** (the extra `assets` and `service_logs` columns in §4), **§S176** (F-83's
> status), and **§S180** (F-88, and the F-89 / D316 framing in this block).
>
> **This is the same recipe the lost original used.** Archive **§S178** states it in its own words:
> *"KB Asset Register refreshed v1.10.3 → v1.11.0 (…) — built from the hash-verified v1.10.3 base + §S177
> of this Archive (NOT memory): the A-D24 wave (scanner-widget-led `/intake` + `/intake/scan_submit`/
> `slip/last`; `/purchases` spend analytics via `_inr()`; approved-bill → asset supplier/purchase-date
> backfill), the housekeeping tools, the test-row cleanup (54 → 49), and next-free A-D25."* Every one
> of those items is present below. The rebuild is therefore faithful in **content**; it is not, and
> does not pretend to be, faithful in **bytes**.
>
> **What this reconstruction does NOT claim.** The lost file's exact wording is unrecoverable and is
> not guessed at. Where §S177 records a fact, it is stated. Where it does not, nothing is invented —
> **the correct entry is sometimes UNKNOWN (D166)**. Items carried forward unchanged from v1.10.3 are
> unchanged because the Archive records no change to them, not because anyone re-verified them
> against the live box this session. **Nothing here was re-probed on the VPS at S181** — the live
> system was not touched.
>
> *Reconstructed 15 Aug 2026, Session 181, under the D316 backlog item. Supersedes v1.10.3 as the
> Tier-1 CURRENT asset-app reference.*

---

**Status:** the APP is LIVE at **v1.11.0**, installed and VPS-smoke-gated **342/0** at S177. **This DOCUMENT is a S181 reconstruction** (see the provenance block above).
**Supersedes:** `KB_Asset_Register_v1_10_3.md` (and, as the readable stand-in for the lost bytes, the original v1.11.0).
**KB standard:** evidence-only; `ASSUMED:` flags where not directly verified; risk section lists only actionable items.

---

## 1. What it is
A single-file Flask + SQLite web app that tracks the clinic/hospital/personal **asset estate** (**49 rows live** — 54 at S176, reduced to 49 when the owner's five stray test rows were deleted at S177), their locations, service history, warranty/AMC renewals, attached documents, and a **purchase-bill ledger** with **Sarvam OCR** auto-fill, a **scanner-led reception intake**, **maker-checker approval**, **spend analytics**, and a **vendor directory**.

- **URL:** https://assets.dr-manoj.in
- **Access model:** login-gated, three roles:
  - **owner** (full; = SSO `doctor`) — sees everything incl. purchase ledger, spend analytics, admin, prices.
  - **manager** (general-visibility; = SSO `manager`) — no owner-only assets/locations, no admin; **can open + approve Consumable bills** (checker), cannot approve Asset-kind bills.
  - **reception** (= SSO `staff`) — **fail-closed, whitelist-contained**: can reach ONLY the intake screens + its own slips; every other route 403s server-side; dashboard redirects to `/intake`. Unknown SSO roles get **no access** (login redirect).

## 2. Where it runs (verified at S177 unless noted)
- **VPS dir:** `/root/assetapp/`
- **App file:** `asset_register.py` (**v1.11.0**)
- **DB:** `assets.db`
- **Service:** `assetapp.service` (systemd), gunicorn `-w 2`, bound to `127.0.0.1` behind the web server.
- **Runtime:** the **system `python3`** (gunicorn shebang `#!/usr/bin/python3`) — **NOT** the `/root/wa` venv (rule **F-53**). Verified S176: `sarvamai` imports in `/usr/bin/python3`; gunicorn runs `/usr/bin/python3`.
- **Shared module:** `sarvam_ocr.py` — loader checks `/root/shared/` first (via `SHARED_LIB_DIR`), falls back to the app's own dir. **RESOLVED at S177 (housekeeping 4b): it is already a single copy at `/root/shared/`**, md5 matching its pin and imports resolving there. *v1.10.3's `ASSUMED: not yet relocated` flag is CLOSED — there was nothing to move.*
- **Sarvam key:** `SARVAM_API_KEY` present in the running service environment (verified S176 via `/admin` "Sarvam key configured: yes" and a live extract). Read at module import; not in code. **Sarvam OCR confirmed working end-to-end** (see §7).
- **SSO:** accepts the portal `clinic_sso` cookie (HMAC, scoped `.dr-manoj.in`). Shim maps portal role → app role: `doctor→owner`, `staff→reception`, `manager→manager`; anything else → fail-closed (no access). Reception reaches the app from the portal's **"Scan Purchase"** tile (`portal.py`, S176).

## 3. Feature map at v1.11.0 (routes)
- `/` dashboard (**owner also sees a spend tile — A-D24b**) · `/assets` index · `/assets/new` · `/assets/<id>` · `/assets/<id>/edit` · `/assets/<id>/service` · `/assets/<id>/delete`
- `/renewals` (warranty/AMC + **consumable expiry**, grouped, owner) · `/drafts` (scan-first) · `/staff` register + service entries
- **`/assets` index:** grouped by **LOCATION**, collapsible sections with counts + due badges; columns **Name · Category · Serial · Supplier · Purchased · Status · Contract**; cascading facets (Entity→Zone→Category/Kind/Status) + search (name/vendor/serial/document-text). Service **contacts render inline** on the asset page (from the vendor directory, provider preferred).
- **Reception intake (A-D21/22/23, reshaped by A-D24a):**
  - `/intake` — **now LEADS with the full shadow-flatten scanner widget** (A-D18 `enhanceGray`), **doc-mode locked** (`allowIdCard` / `allowBatch` both false). The plain **📷 Take a photo** + **📁 choose photo/PDF** controls (A-D22) are **kept as a fallback inside a `<details>`**. "Recent stamped submissions" list; reception sees ONLY its own.
  - **`/intake/scan_submit`** — **NEW at A-D24a.** The scanner widget posts here; session-stashes the bill id and returns a bare 200, with `backUrl` → `/intake/slip/last`.
  - **`/intake/slip/last`** — **NEW at A-D24a.** Renders the slip for the just-stashed submission.
  - `/intake/submit` — the fallback upload path: stores a **draft** bill + scan instantly, assigns a **monotonic stamp** (`B-0001…`, never reused even after reject), launches the background Sarvam fill, returns the **stamp slip**.
  - `/intake/slip/<bid>` — big stamp number + submitter + IST time (handwrite on the paper bill).
  - Both creation paths share one helper, **`_create_intake_bill()`** (DRY — a single bill-creation path).
  - **Reception whitelist:** `RECEPTION_OK` deliberately gained `intake_scan_submit`, `intake_slip_last` and `scanner_widget_js` at A-D24. *(The new routes 403'd for reception on first build — the fail-closed guard working exactly as designed, not a fault.)*
- **Purchase ledger / maker-checker (A-D21/23):**
  - `/bills` list (search + kind filter + **status filter** + **pending badge** + OCR marker) — **open to checker (manager 200)**.
  - `/bills/new` (dynamic line-item blocks; blanks ignored) · `/bills/<id>` detail · `/bills/<id>/edit` ("Complete / edit") · `/bills/<id>/delete`.
  - `/bills/<id>/approve` — **server-side lane guard**: Consumable → manager|owner; **Asset-kind → owner (doctor) ONLY**; **blank bill (no vendor/total/items) requires explicit `confirm_blank`** (A-D23). **Also triggers the A-D24d supplier/purchase-date backfill.**
  - `/bills/<id>/reject` — void (stamp + reason kept; stamp never reused).
  - `/bills/<id>/reread` — **A-D23**: re-run Sarvam on the stored scan (non-clobber; drafts AND approved; recovers a read lost to a restart/race).
  - `/bills/<id>/file` — serves the stored scan (open to checker).
  - **`/purchases`** — **owner-only**; only **approved** bills feed it. Per-item rate-drift, period consumption, expiring-soon, **plus the A-D24b spend analytics: Total + this-month cards, spend-by-month bars, top-vendors bars**, rupees in **Indian format** via a new **`_inr()`** Jinja filter with **`_ym_human()`** for month labels.
- **Bill OCR (Phase E / A-D16):** `/bills/extract` — upload → `sarvam_ocr.extract()` → tolerant `_map_bill()` → pre-filled `/bills/new`. Background intake fill uses the same `_bg_extract()` path.
- **Vendor directory (A-D21):** `/vendors` list · `/vendors/<id>` (add/deactivate contacts) — owner + manager. `vendors` + `vendor_contacts` (multi-person: engineer/service-manager/sales/accounts/other, active flag).
- **API:** `/api/due` (token-gated) for the WhatsApp due-digest cron.
- **Scanner widget** (`scanner_widget.js`): in-browser camera + **Document mode** (integral-image shadow-flatten `enhanceGray()`), served from disk. **As of A-D24a it fronts `/intake`** — v1.10.3's "intake uses the plain camera input, a future enhancement" note is CLOSED.
- **Admin:** users/passwords, managed pick-lists, locations, `/api/due` token (masked + rotate), screen palette, **"Sarvam key configured" readout**.

## 4. Data model (key tables)
- `assets` (location_id → `locations`; category, purchase_date, price, vendor, serial_no, status, contract fields, hide_price, entity_id/zone_id/kind overlay, **`bill_id`** back-ref from the A-D20 bridge, `pm_count`, `pay_ref`, `pay_date`, …). **A-D24d:** blank `vendor` / `purchase_date` are filled from the linked **approved** bill — non-clobber, idempotent.
- `locations` (flat, UNIQUE name, general/owner_only) — populated for every asset; basis of index grouping. `entities` + `zones` = hierarchical overlay (mostly NULL on the live rows, which is why A-D19 regrouped the index by location).
- `expiries` (warranty/AMC/contract + consumable item-expiry → renewals + due badges).
- `attachments` (files + extracted `document_text` for search).
- `service_logs` (`svc_type`, `part_replaced`, `part_warranty`, `is_pm`, `report_att_id`).
- **`bills`** — kind, vendor, bill_no, bill_date, total_amount, notes, source_stored/source_orig **+ workflow cols:** `stamp_no`, `status` (draft/approved/rejected, DEFAULT `'approved'` grandfathers old bills), `submitted_by`, `submitted_at`, `approved_by`, `approved_at`, `reject_reason`, `vendor_phone`, `vendor_email`, **`ocr_status`** (NULL / reading / read / empty / failed — A-D23).
- **`bill_items`** — item_name, pack_size, quantity, rate, amount, make, model, serial_no, batch, expiry, hsn, **`asset_id`** (A-D20 bridge).
- **`vendors`** (name UNIQUE, phone, email, address, gstin, notes) + **`vendor_contacts`** (vendor_id, person_name, role, phone, email, active). 18 vendors auto-seeded on the A-D21 install.
- `settings` (incl. `palette`, read via the safe `setting_or()`).
- All dates stored **ISO on save** via `_norm_date()` (A-D20); idempotent startup `normalise_dates()` self-heal. **A-D24d adds a second startup sweep, `backfill_asset_supplier()`**, hooked into `init_db`.

## 5. Decisions (asset-app scope)

> **Index completeness note (S181).** This section lists **A-D16 … A-D24**. **A-D1 … A-D15 are NOT
> indexed here** — that gap was inherited from v1.10.3, not introduced by this reconstruction. Their
> record in **Archive §S173** (A-D1–A-D7) and **§S174** (A-D8–A-D15) is **one-liners only**; §S173
> places their **full text in the S173 git kit / `assetapp/NEXT_BUILD.md`** — `ASSUMED:` not verified
> this session. **§5A** below indexes all fifteen so this register stops being the only asset doc that
> cannot answer "what is A-D9?".

- **A-D16** — Sarvam extraction is a shared VPS service (`sarvam_ocr.py` on `sys.path` via `SHARED_LIB_DIR`, default `/root/shared`); SDK-based (`sarvamai` doc_ai), no hardcoded endpoints; graceful-skip.
- **A-D17 v2** — bill capture is a structured ledger: `bills` + `bill_items`, an asset+consumable **superset** schema, owner-only/403 — built for analytics, not just form pre-fill.
- **A-D18** — scanner enhancement = integral-image **local-mean shadow-flatten** (`enhanceGray()`), not a global stretch (preserves stamps and blue handwriting).
- **A-D19** — `/assets` index grouped by **location**, with Serial/Supplier/Purchased columns.
- **A-D20** (v1.9.0) — **Date-normalisation keystone**: tolerant `_norm_date()` stores ISO on save (bill dates + item expiries), idempotent `normalise_dates()` self-heal; **bill→asset bridge** ("+ asset" per line, two-way `asset.bill_id ↔ bill_item.asset_id`, seeds item-expiry renewal); consumable expiry in owner `/renewals`; from-bill backlink on the asset page. Smoke 236/0.
- **A-D21** (v1.10.0) — **Reception scan-first intake** (SSO `staff`→fail-closed `reception`; stamp slips `B-0001…`; instant draft+scan; background Sarvam fill, non-clobber); **maker-checker bills** (status; Consumable→manager, Asset→doctor ONLY, server-side lane guard; reject=void); **vendor directory** (`vendors`+`vendor_contacts`, seeded + grows on approval + Sarvam header; inline service contacts on the asset page). Only approved bills feed analytics/renewals/bridge. Smoke 293/0; 18 vendors seeded.
- **A-D22** (v1.10.1→v1.10.2) — **Intake camera fix**: the single `image/*,.pdf` input silently suppressed the phone camera; split into a dedicated camera-capture control + a photo/PDF fallback, rendered as proper labelled buttons (camera/folder icons) with a filename confirmation. Smoke 300/0 → 301/0.
- **A-D23** (v1.10.3) — **OCR no longer silent**: bills carry `ocr_status` (reading/read/empty/failed) shown on the draft and the Purchases list; **"Re-read with Sarvam"** button re-runs extraction on the stored scan (non-clobber; drafts + approved; recovers reads lost to a restart/race); **blank-bill approval requires explicit confirm** (server-enforced). Smoke 315/0.
- **A-D24** (v1.10.3 → **v1.11.0**) — **the S177 wave, three shipped sub-parts:**
  - **(a) Scanner-in-intake.** `/intake` leads with the full shadow-flatten scanner widget, doc-mode locked (`allowIdCard`/`allowBatch` false), posting to the new `/intake/scan_submit` (session-stashes the bill id, returns a bare 200) with `backUrl` `/intake/slip/last`; the plain upload kept as a `<details>` fallback; shared `_create_intake_bill()` helper so both paths create a bill exactly one way. `RECEPTION_OK` extended to the three new endpoints.
  - **(b) `/purchases` spend analytics.** Total + this-month cards, spend-by-month bars, top-vendors bars, Indian-format rupees via a new `_inr()` Jinja filter + `_ym_human()`; owner-only dashboard spend tile.
  - **(d) Supplier / purchase-date backfill.** `_backfill_asset_from_bill()` + a `backfill_asset_supplier()` startup sweep fill blank asset `vendor`/`purchase_date` from the linked **approved** bill — non-clobber, idempotent; hooked into `init_db`, `bill_approve`, and the asset-edit bridge.
  - **(c) is deliberately absent:** the fourth sub-part — the scanner app adopting the shared `sarvam_ocr` — **was already satisfied** by the A-D16 shared import, so nothing was built for it.
  - Smoke **315 → 342/0** (STEP 23 added: 27 checks, 23a–f). The gating VPS run used the **real** sarvam module — that run is the authoritative green.
- **Next-free:** **A-D25.**

### §5A — A-D1 … A-D15 index *(added at the S181 reconstruction; full text in Archive §S173/§S174)*

*These were minted in the asset sub-project's own close-out records and folded into the clinic Archive at S177. They have never been indexed in this register. **The Archive carries only these one-liners — it is NOT a fuller source.** §S173 states the A-series full text lives in the **S173 git kit / `assetapp/NEXT_BUILD.md`**, which was not opened this session (`ASSUMED:`). So the rows below are as complete as their source, not a pointer to something richer.*

| # | Session | One line |
|---|---|---|
| **A-D1** | S173 | **Entity replaces location as the top axis**; visibility rides on Entity (Personal = owner-only). |
| **A-D2** | S173 | Consumables are a **separate table** (headings), not assets. |
| **A-D3** | S173 | Dates are entered as **Month + Year**; renewals are **computed** from contract type → period. |
| **A-D4** | S173 | Payment is **record-only** (Cash/Bank/Card + optional EMI; computed end date for reference; no reminders). |
| **A-D5** | S173 | **Maker-checker**: owner (manoj + bhawna) = full + checker; manager = maker scoped to entities, never Personal; audit log. |
| **A-D6** | S173 | **OCR**: search + read-only peek on non-sensitive docs; sensitive documents stay search-only. |
| **A-D7** | S173 | `asset_register.py` is the entrypoint (`asset_register:app`); `app.py` is dead → git-remove. |
| **A-D8** | S174 | **Contextual contract** (None / Warranty only / AMC-CMC + PM count) drives computed warranty + renewal. |
| **A-D9** | S174 | **PM under AMC/CMC is free** — `svc_type` drives the cost gate and the PM counter. |
| **A-D10** | S174 | A **replaced part carries its own warranty** → its own reminder + a Parts-replaced card. |
| **A-D11** | S174 | **Due-soon badges** on the grouped index + a per-entity `/renewals` view, visibility-gated. |
| **A-D12** | S174 | Payment **expanded but still record-only** (incl. Unpaid; adds `pay_ref` / `pay_date`). |
| **A-D13** | S174 | The redesign is **stylesheet-only** — which is why the smoke went 139→161 and stayed green. |
| **A-D14** | S174 | A **service-report scan links back** via `service_logs.report_att_id`. |
| **A-D15** | S174 | Contextual **"work done" label** by visit type. |

## 6. Canonical files + md5 (v1.11.0 — LIVE, pinned at S177)
| File | md5 | Notes |
|---|---|---|
| `asset_register.py` | `0cd8fc3bfe8d39322c6162a41124bddf` | main app, **v1.11.0** (was `b30983710238863b6d98b8e773c6923c` at v1.10.3) |
| `smoke_test.py` | `6e72373325f808b1d7eaeb99f51a7b14` | dev-only; **342 passed / 0 failed** (was `65d6cd0e…` at 315/0) |
| `scanner_widget.js` | `4fe8c89386a54ce90786823b53df55bc` | **UNCHANGED** since v1.8.1 |
| `sarvam_ocr.py` | `b1cc567b70b5e67c8c021fa22590babf` | **UNCHANGED**; shared OCR module, confirmed single-copy at **`/root/shared/`** |
| `portal.py` (cross-ref, `/root/portal/`) | `da4177091ba9f188be6a0ff3eaf25bd8` | "Scan Purchase" tile (staff + manager) |

**Housekeeping tools installed at S177 (manual, no cron):**
| File | md5 | Notes |
|---|---|---|
| `/root/prune_backups.py` | `9dce8ea6dd61c5583f131f40fd4fec95` | dry-run default, `--apply`, keep-newest-2, 14-day age gate, live-file guard, `.backup` ≠ `.bak`, logs to `prune_backups.log`. VPS self-test **15/0**. |
| `delete_test_assets.py` | `24cc30d832d3497e9948bef204361692` | one-shot: hard-coded IDs + name-verify refuse-all guard, WAL-checkpointed DB backup, all-or-nothing transaction. Offline-gated **11/0**. |
| `inspect_assets.py` | *(not pinned in §S177)* | read-only inspection helper delivered alongside. `ASSUMED:` md5 never recorded — **UNKNOWN**, not guessed (D166). |

`.bak` files from the A-D24 install are retained in `/root/assetapp/`.

**Git:** the S176 kit (`gitkit_S176.zip`) was **committed by the owner before the S177 close — the repo is at v1.10.3.** A kit for the **v1.11.0 / A-D24 wave is therefore still owed** (see §8). Canonical code store: GitHub `manoj-clinic-automation/drmanoj-clinic-automation`.

## 7. Verified — S176 and S177
**At S176:**
- **Sarvam OCR works end-to-end.** Ran directly on **B-0001**'s real 3 MB bill photo: `status: done` → vendor *Shri Ram Enterprise*, bill_no *SRE/737/2025-26*, total *₹1,30,003*, **5 line items**. Key present in service + `sarvamai` imports in the gunicorn interpreter.
- **B-0001 is the first real reception bill** (submitted by Shivani via `/intake`). It initially arrived **blank** — root cause **F-83** (§9), fixed by A-D23; **recoverable** by opening B-0001 → **Re-read with Sarvam** (non-clobber fills the 5 items). **Do not delete B-0001.**
- Reception intake live (stamp slip renders, draft + scan stored). 18 vendors auto-seeded. Portal "Scan Purchase" tile live for alisha/shivani (staff) + shavez (manager).

**At S177:**
- **A-D24 installed live, VPS smoke 342/0** — the gating run used the real sarvam module.
- **`sarvam_ocr.py` confirmed single-copy at `/root/shared/`** (md5 matches its pin; imports resolve there). The v1.10.3 `ASSUMED:` relocation flag is **CLOSED — nothing to move.**
- **`prune_backups.py` self-test 15/0**; its first dry-run correctly pruned **nothing** (all 18 backups under the 14-day age gate).
- **Test-row cleanup: CLEAN DELETE ✓.** Assets **54 → 49**; target rows 0; **zero orphan** expiries / service_logs / attachments. Undo backup on the VPS: `assets.db.predelete.2026-08-14_223751`.
- Every install gated offline and re-verified in place by md5 before swap (**F-66**); install as a single &&-chained block with the smoke suite as the gate and auto-rollback on red.

## 8. Open items (actionable)
- **Owner — git: position UNKNOWN at S181 (D166), owner to confirm.** As at S177 the repo sat at **v1.10.3** and the **v1.11.0 / A-D24 kit was owed** (the S176 kit having been committed before the S177 close). §S180 then records git kits committed at that close, while its own loose-ends paragraph still carries a kit as outstanding. **The Archive is ambiguous, so this is not asserted either way** — check the repo rather than trust this line.
- **Owner — security:** rotate the `/api/due` WhatsApp token + update its cron; rotate the `/api/due` token that appeared in earlier screenshots (portal `/admin`). **Still open.**
- **Owner — data decision:** rows **#45–50** (duplicate manager-entered *"Gaurav scientific"* ×3 / *"Aastha medical"* ×4) were **flagged as possible practice-junk and deliberately NOT touched** at S177. **Owner's call, queued for review.**
- **Recovery, if not yet done:** open **B-0001** → **Re-read with Sarvam** → confirm the 5 items + vendor + ₹1,30,003 populate and the badge flips to ✓ auto-read.
- **Data:** Supplier / Serial / Purchased columns stay blank for legacy assets until edited or backfilled — **A-D24d now backfills vendor + purchase_date automatically from approved linked bills**, so this shrinks as bills are approved; **serial is still manual.**
- **Build (A-D25 candidates):**
  - **The F-83 durable fix** — replace the fire-and-forget OCR thread with a survivable path (queue + worker, or synchronous extract with a bounded timeout). *This is the one with a live finding attached.*
  - Phase-3 doctor-only staff cockpit (separate).
  - Consumption dashboards beyond the A-D24b spend view.
- **CLOSED at S177, recorded so they are not re-raised:** relocate `sarvam_ocr.py` → `/root/shared/` (was already there) · delete the stray owner test assets (done, 54 → 49) · intake to adopt the full shadow-flatten scanner widget (**shipped as A-D24a**) · scanner-app to adopt shared `sarvam_ocr` (**already satisfied by A-D16**).

## 9. Findings (asset-app scope)
- **F-83** (S176, **OPEN — mitigated**) — the reception intake's **background OCR fill is a fire-and-forget daemon thread**: it dies if the service restarts mid-read, and (before A-D23) only touched `status='draft'` bills, so a read could be **silently lost** with no trace (the `except: pass` swallowed everything). This is why B-0001 arrived blank — several restarts followed its submit during the v1.10.1 install. **Mitigated by A-D23**: the outcome is now visible (`ocr_status`) and recoverable (Re-read button, non-clobber, any status). **Residual:** the re-read still uses a thread (owner chose "button only", **no cron**), so recovery from a mid-read restart is a manual tap — acceptable at a few bills a day. **Durable fix owed — the leading A-D25 candidate.**
  *Clinic-numbered, asset-app located. Full text: **`Fault_Action_Register` v2.17 §7.1** — built at S181 from the long-owed `Fault_Register_append_F82_F83_S177` append; **delivered, but not yet re-pinned in `CANONICAL_MANIFEST.md`**, which still pins v2.16. Also Archive §S176.*
- **No finding was minted at S177.** Recorded explicitly because two things there could be mistaken for faults and are not: the new intake routes **403'd for reception on first build** — the fail-closed guard behaving exactly as designed — and the **owner's terminal corrupting a long heredoc paste**, which is an environment lesson, now a standing delivery rule (§11), not a system fault.

## 10. Change log
- **v1.7.0 → v1.8.1:** A.4 punch-list + Phase D purchase ledger + Phase E Sarvam extract + scanner shadow-flatten; `/assets` grouped-by-location (A-D19); Sarvam schema-description fix; `_map_bill()` whitespace-collapse.
- **v1.8.1 → v1.9.0 (A-D20):** date-normalisation keystone + bill→asset bridge + consumable renewals. Smoke 236/0.
- **v1.9.0 → v1.10.0 (A-D21):** reception intake + maker-checker bills + vendor directory. Smoke 293/0; 18 vendors seeded.
- **v1.10.0 → v1.10.2 (A-D22):** intake camera fix + labelled buttons + filename feedback. Smoke 301/0.
- **v1.10.2 → v1.10.3 (A-D23):** visible OCR status + Re-read button + no-blank-approve guard. Smoke 315/0.
- **v1.10.3 → v1.11.0 (A-D24, S177):** scanner-widget-led `/intake` + `/intake/scan_submit` + `/intake/slip/last` + shared `_create_intake_bill()`; `/purchases` spend analytics (`_inr()`, `_ym_human()`, owner dashboard spend tile); approved-bill → asset supplier/purchase-date backfill. Smoke **342/0**. Housekeeping: `prune_backups.py`, `sarvam_ocr.py` relocation verified already done, test rows deleted 54 → 49.
- **Portal (S176):** `portal.py` gained the config-driven "Scan Purchase" tile (staff + manager). `da4177091ba9f188be6a0ff3eaf25bd8`.
- **Document v1.11.0 → v1.11.0-R (S181):** the v1.11.0 *document* was lost (**F-89**) and is **reconstructed** here from the hash-verified v1.10.3 + Archive §S177, under **D316**. **No code changed; no version of the app changed.** **Four additions go beyond the lost original's stated recipe, each flagged where it appears:** the **§5A index of A-D1–A-D15** (a gap inherited from v1.10.3); the **§11 delivery rules** (minted at S177, previously living only in the Archive and the clinic runbook); the extra **§4 data-model columns** recovered from §S174/§S175; and the **enriched A-D16–A-D19 texts** from §S175. Every secondary source is named in the provenance block.

## 11. Delivery + install rules minted in this sub-project (standing, S177)
*Recorded here because they were minted during an asset-app session; they are now clinic-wide standing discipline and also live in `HANDOFF_RUNBOOK` §3.*

- Files for VPS install are delivered **pre-named `.new`**.
- The install is **ONE copy-paste &&-chained bash block** — `md5sum -c` → `cp live live.bak` → `mv .new → live` → **smoke suite as the gate** → restart **only** on green → **auto-rollback from `.bak` on red**. **Never numbered steps.**
- **Never paste long heredocs** — the owner's terminal corrupts them. DB and utility work ships as **uploadable script files** (§S177). *(The "in a zip with a folder" refinement is from `HANDOFF_RUNBOOK` §3, not S177-minted.)*
- *(Standing clinic rule, NOT minted at S177: a filename is not provenance — **trust the hash** (F-66 / D188). Carried in `HANDOFF_RUNBOOK` §3.)*
- *(Added by later sessions, noted here so this register is not read as complete on its own: an install kit must also state **which build it is** and refuse to run if stale — a checksum proves integrity, never currency — **F-88**, S180.)*

---

**END OF KB — ASSET REGISTER v1.11.0-R (reconstructed S181). §11 is the last section. If this marker is absent, the file is truncated and must not be used as canonical.**
