# NEXT BUILD — Asset Register (as of Session 173 close, 13 Aug 2026)

The complete, self-contained resume-point for the Asset Register redesign. Read this first;
it is the authoritative pickup for the next build session.

---

## 0. Where we are (live state)

| Piece | State | md5 (code-only) |
|---|---|---|
| `asset_register.py` | **v1.4.2** LIVE (`asset_register:app` on :8030) | `3e18ed304f861c7fc2d10fc44a246163` |
| `scanner_widget.js` | LIVE (disk-served, cache-busted) | `9b1444ac60db6ddcc63b9b81c877ac5a` |
| `smoke_test.py` | 74/74 checks | `b9d2bc7cede789d20897170ae1ebe9be` |
| `app.py` | **DEAD** (v1.1.0) — git-remove it | — |

- **Host:** `assets.dr-manoj.in` :8030, gunicorn (system python, `/usr/local/bin/gunicorn`), OpenLiteSpeed proxy, systemd `assetapp.service`. Dir `/root/assetapp/`. DB `/root/assetapp/assets.db` (49 assets, 1 draft, 44 attachments). Nightly local backup 02:30 (14-day).
- **Data classified:** all 49 assets have `entity_id`/`zone_id` (Clinic 37 / NK Path 11 / Personal 1, all in "Unassigned" except the 1 Personal). Old `location_id` kept as shadow.
- **Rollbacks on VPS:** `asset_register.py.bak-S173` (pre-scanner) · `.bak-S173-phaseA` · `.bak-S173-v141` · `.bak-S173-v142`.

## 0.1 Non-negotiable engineering rules (this project)
- **Build from the live/verified file, never memory** (D160/D188). Confirm live md5 before editing.
- **Full-file replacements only.** Surgical patches proven by assert-once anchors; prove untouched regions are byte-identical.
- **Offline gates before install:** `python3 -m py_compile` with the **system** python (F-53) + `python3 smoke_test.py` (must stay green) + `node --check scanner_widget.js`.
- **Install discipline:** `.new` upload -> md5 verify -> py_compile -> `.bak` -> `mv` -> restart -> serve-check -> **owner tests on the Samsung Fold** (UI can only be verified on-device).
- **Data migrations are dry-run-first + fail-loud** (see A.1 in DEPLOY). Schema auto-applies on restart (`init_db()` on import, idempotent).
- **Never** touch `assets.db` / `uploads/` / secrets in the repo (F-31/F-49). `.gitignore` covers them.
- One writer per store (D235). Serve inert widget JS publicly; gate everything else.

---

## 1. The agreed target design (signed off S173)

Data model reframe: from one flat axis (`location`) to **Kind -> Entity -> Zone -> Category/Heading**,
all cascading dropdowns, plus an **Asset-vs-Consumable** split.

```
KIND ──▶ ENTITY ──▶ ZONE ──▶ CATEGORY / HEADING ──▶ item
        (owner)    (per entity) (per kind)
```

- **KIND:** Asset (durable; serial/warranty/AMC) or Consumable (recurring bill; a heading; no serial/warranty).
- **ENTITY (live already):** Dr Manoj Clinic · NK Pathology · Personal. Carries default **visibility** (Personal = owner-only; Clinic/Pathology = general), per-item override kept. *Open Q:* if Pathology gets its own manager later, scope visibility per-entity.
- **ZONE (live already, seeded):** per-entity list, admin-editable. Clinic: Reception/Consultation/X-ray/Imaging/Minor OT/Physio/Pharmacy/Waiting/Power-Backup/IT. Pathology: Sample collection/Lab bench/Reagent store/Reception/Power-Backup/IT. Personal: Dr Manoj/Dr Bhawna/Home/Vehicle/Devices/Documents.
- **CATEGORY (durable):** the existing list stays valid. **HEADING (consumable):** Lab Chemicals/Reagents · X-ray/Ray Films · Medical Disposables · Printing/Stationery · Housekeeping · Maintenance/Spares · Other.

### Entry flow (max dropdowns, min typing)
1. Cascading dropdowns Kind -> Entity -> Zone -> Category.
2. **Dates = Month + Year dropdowns** (day optional) — kills the clunky native date field.
3. **Contract engine (no date typing):** contract type (None/Warranty/AMC/CMC) -> **Period** dropdown (6mo/1/2/3/5yr/Custom) -> renewal/expiry date **computed** from start+period, shown read-only, feeds the existing `expiries` reminder + `/api/due` machinery unchanged.
4. **Vendor & provider = managed growing dropdowns** ("+ add new" inline). Name/serial stay free text.
5. **Payment block (record-only, D-locked):** `Cash · Bank · Credit Card`; Bank -> {ICICI, YES, SBI, +add}; Credit Card -> {ICICI, HDFC, +add} + optional **EMI** (instalment count · per-instalment ₹ · start Mon/Yr, with a computed end-date **for reference only** — no schedule, no reminders). Banks/cards are one managed admin-editable list (typed bank vs card). Applies to Assets **and** Consumable bills.
6. **Quantity / bulk:** a qty field or "add N identical" (real need — live data has 10x/7x/5x duplicate rows).

### Display
- **Grouped index LIVE (v1.4.2):** Entity -> Zone -> assets, collapsible. Next: add **due-soon badges** per group + a per-entity renewals view.
- **Consumables/Bills:** separate lightweight track (own table): Entity · Zone · Heading · month/year · amount · vendor · attach-the-bill (reuses the scanner). Grouped Entity -> Heading -> this-month, with a spend total.

### Capture -> process -> OCR pipeline (mostly scaffolded)
```
BATCH SCAN (retake/discard poor takes) -> DRAFTS  -> Sarvam Doc-AI (background, fail-soft)
   -> document_text filled -> SEARCHABLE  -> DRAFTS INBOX = processing queue
   -> open draft: doc preview + OCR text (+ optional auto-filled vendor/date/amount)
   -> cascading entry form -> SAVE -> asset created, doc attached, draft cleared
```
- Drafts inbox + promote-to-asset + scanner quality-gate (delete/retake) are **already live**.
- **New to build:** point batch mode at drafts (tiny config); the **real Sarvam Doc-AI worker** (cron ~5min over `ocr_status='pending'`, fail-soft, one writer) filling `document_text`; OCR at scan-time (not just at promote); drafts inbox upgraded to a queue with OCR status + text peek.
- **OCR text policy (locked):** **search + read-only peek on non-sensitive docs**. Sensitive docs (hide-price/owner-only) stay **search-only** (searchable-but-never-displayed). Editing/auto-fill = later optional phase.
- *Confirm Sarvam Doc-AI endpoints/limits live at build — do not hardcode from memory.*

### Governance (maker-checker + scope) — mirrors portal staff-register (D292)
- **Owner (manoj + bhawna) = full + Checker.** **Manager = Maker, scoped** to allowed entities (never Personal).
- Maker entries land **Pending** -> go live only after owner **Approve**. Add an approval status per entry, a **Pending queue** for the owner, and scope = a per-user entity list (clean generalisation of today's owner-only/general trick).
- Add an **audit log** (who created/edited/approved) once staff are makers.

---

## 2. Build queue (recommended order)

| # | Phase | What | Risk |
|---|---|---|---|
| ✅ | 1A | Shared super-scanner (multipage/JPEG/naming/delete/retake/ID-card/batch) | done |
| ✅ | A | Taxonomy backbone + migrate 49 rows | done |
| ✅ | admin | Password reveal/generate + token mask/rotate | done |
| ✅ | C | Grouped Entity->Zone index | done |
| ▶ | **B** | **Cascading entry form** + contract/period engine + payment block + month-year dates + vendor/provider dropdowns + **quantity** | medium (form rewrite; existing form is fallback) |
| | D | Consumables/Bills module (new table, headings, scanner reuse) | medium |
| | E | OCR pipeline (real Sarvam Doc-AI worker -> searchable; batch->drafts; drafts-as-queue) | medium (confirm Sarvam API) |
| | Gov | Maker-checker + per-user entity scope + audit log | medium |
| | F | OCR field pre-fill into the form (uncertain flags) | optional |
| | + | Due-soon badges per group · per-entity renewals view · QR sticker per asset (jumps to asset page) · dispose/retire workflow · asset photo thumbnail · per-entity CSV/PDF export · value/spend rollups | nice-to-haves |

**Next session top task: Phase B** (the cascading entry form — where zones finally get used and re-zoning happens).

## 3. Schema reference (current, post-S173)
- `entities(id, name UNIQUE, visibility, sort)` — 3 seeded.
- `zones(id, entity_id->entities, name, sort, UNIQUE(entity_id,name))` — 24 seeded.
- `assets(... , location_id->locations [shadow], category, ..., contract_type, provider, contract_cost, entity_id, zone_id, hidden, hide_price)`.
- `expiries(entity IN('asset','staff'), entity_id, label 'Warranty'|'Contract renewal', due_date, threshold_days, resolved)` — the reminder + `/api/due` source.
- `attachments(... , document_text, ocr_status)` · `drafts(...)` · `staff(...)` · `service_logs(...)` · `locations(...)` · `users(role owner|manager)` · `settings`.
- Constants: `ENTITY_SEED`, `ZONE_SEED`, `LOC_TAXONOMY_MAP` (backfill), `CATEGORIES`, `STATUSES`, `CONTRACT_TYPES`.

## 4. Gotchas discovered this session
- `init_db()` runs on **every import** (via `_load_secret`) — schema is idempotent, so restart = schema applied. Good; but that means data migrations must be a **separate explicit CLI**, never auto-on-import.
- The service runs **`asset_register.py`**, not `app.py` (repo `DEPLOY.md` had said `app:app` — now fixed). `app.py` (v1.1.0) is dead — **git-remove it**.
- Use the **system `python3`** for compile/migrate (gunicorn's interpreter), not `/root/wa/venv` (that venv belongs to the automation stack, F-53).
- Sensitive-doc search must stay "match reported, content never shown."
- **Security to close:** the WhatsApp `/api/due` token was visible on the admin page across several uploaded screenshots — **rotate it** (/admin -> Rotate token) and update the WhatsApp cron.

## 5. Repo hygiene owed at the commit
- Add `scanner_widget.js`, updated `asset_register.py`, `smoke_test.py`, refreshed `CHANGELOG/DOSSIER/DEPLOY`, this `NEXT_BUILD.md`.
- **`git rm app.py`** (dead entrypoint).
- Confirm `.gitignore` still excludes `assets.db`, `assets.db-journal`, `uploads/`, `*.tar.gz` (it does).
