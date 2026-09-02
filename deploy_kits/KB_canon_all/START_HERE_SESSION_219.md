# START HERE — SESSION 219

Hi Claude. Continuing my clinic-automation project — **Session 219**.
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Evergreen rules: **`START_HERE_PROMPT_v8`** (custom instructions). This page carries S219 entry only.

## ⚠ WHAT CHANGED AT S217/218 (one marathon session, 01–02 Sep) — read first
`S218_BUILD_BRIEF.md` is the short complete path in. Headlines: the UPI fixture corruption
repaired · D356 deployed (patient sync hourly :20) · GAS v3 hourly MPR + 15:00 shout ·
**the owner's hub is FINAL** (English, alert bar, Walk, MPR card, staff-cards directory,
heal engine :*/30) · bank-truth corrections posted (drawer true at ₹8,817) · review queue
zero via the D355 backfill · old maker form retired · PUSH_TODAY.bat runs both legs ·
**Vaapsi Desk soft-launched + its portal tile live** (see next line).
**The hub is not reopened without a new ruling** (S218_CARDS_FINAL_CONTRACT rev2).

## ⚠ LATE-CLOSE ADDITIONS (after the briefs were written — do NOT re-derive)
- **`S218_PORTAL_TILE` v2 is LIVE.** portal.py moved 24ea2c0b → **16bfd590e2e422bb81bb8b6ad6e84eae**;
  it adds the 📦 Vaapsi Desk tile (roles staff+doctor) + its `_TILE_GROUP` entry, and
  retargets Daily Sale to /finance/daily. v1 503'd on the import-time group assert (portal
  line 383) — a runtime assert compile() can't catch; v2 is import-proven. Backup
  `portal.py.bak_S218_tile_20260902-102801`. **All nine live pins are in
  `live_pins_S218close_READBACK.md`** — that doc is the pin source for the fold; the portal
  pin is now the 9th row there.
- **Vaapsi Desk is soft-launched today** on the direct link
  `https://followup.dr-manoj.in/finance/returns/desk` (own logins; alisha/shivani/darpan/
  shavez). The portal PWA ("Clinic", scope /, start /portal) is the full-app install for
  later — all role-scoped tiles inside; the owner forwards `/portal` once he's ready.
- **`.gitignore` gained `!deploy_kits/*/cards_registry.json`** this session (registry is
  names+URLs, no PHI). Do NOT revert it — the S218 hub kit needs that file to publish.

## ⚠ CLOSE DEBT — do this at the S219 open, before new work
The marathon close deferred the heavy canon fold (precedent: S211). Owed:
**Archive v1.64 append (byte-proof) · Register v5.66 · CANONICAL_MANIFEST recompute ·
gen_live_pins run (using the READBACK pins, incl. the portal row) · cold kit + Cowork mirror
(F: write stall C-S216-8 still stands) · Notion log · F-candidate minting (7 from the
marathon, in the brief §roots).** FIRST: paste the owner's pin readback (OWNER_TODO ⭐0) —
finance_app AND portal.py changed by guarded hotfixes after their kits, so their md5s are
read from the box, never assumed (the readback already captured both).

## THE OWNER'S PLAN (his words, 02-Sep): MARG COMPLETELY FIRST
**Priority order for Marg jobs:**
1. **M1 · Marg auto-apply** — apply a pushed export the moment its day is filed; on apply
   render the short summary (bill range · total · UPI per Marg · CN count) and the
   **bill-range continuity check vs the previous export (gap ⇒ flag)**. MONEY WRITE:
   harvest live apply-path bytes first, offline rehearsal, own kit.
2. **M2 · Router signatures** — teach the two _UNKNOWN titles ('BILL/ITEM WISE PURCHASE
   STATEMENT…', 'SALE RETURN FROM…'); owner re-exports the missing full-month
   PURCHASE_BILLWISE for August (his one Marg action).
3. **M3 · Purchase capture through SCANNING** — purchase orders + purchase bills via the
   existing scanner/OCR (asset-app reuse); purchase tables on the VPS (PP0-lite; the NEFT
   portal itself WAITS, owner's word).
4. **M4 · Stocks** — first real count (owner clock item), then stock Phase B (batch push,
   PUSH_STOCK_DAILY revival).
5. **M5 · Purchase orders / reorder** — from stock + sale pace (orthotics pattern extended).
6. **M6 · Medical→VPS pipeline ALTERNATIVE leg** — direct upload from the medical PC
   (finalised earlier; build the leg), plus task-health shouts (the puller slept 46 min
   unnoticed — feeds must announce their own missed heartbeats).
7. **M7 · Returns build (Marg-side)** — stub-guard on verdicts (WALK-IN ⇒ never
   NEVER-BOUGHT; owner-caught bug CN00184) · auto-escalation of REAL flagged returns to
   owner+Darpan · full mobiles on the card · cn-detail r3.
**Unavoidable in-between (only these):** Docterz EMR export auto→VPS (approved Phase-1
watchers, S218_DOCTERZ_FEED_DESIGN) · **the processed follow-up-tracker report that feeds
the callback tracker must reach the VPS from the owner's PC** until the tracker itself is
hosted on the VPS (Phase 2 feed-inventory) · August staff close (Surendra ₹516.08 FIRST,
Pravesh ₹569) — still owed from S217's original plan · walk wording (approve-before-MPR
hint) · role-aware card links · portal tile contextual lines (PARKED) · **per-user app-scope
manager on the portal (S219_QUEUE #9, owner design)** · money-model v2 minting text ·
NEFT portal (WAITS).

## PHASE 0 — as v8, plus
Connections by name (D:\Downloads · D:\dr-manoj-git · F:\ClinicBackup · browser F-242) ·
manifest md5 (expect stale rows until the close-debt fold — reconcile there, don't halt on
the known debt) · Tier 0 · `D:\Downloads\ClaudeCowork\00_INDEX.md` → `03_WORKING_PAPERS\
S218\S218_BUILD_BRIEF.md`.

## STANDING RULINGS — v8 §rulings, plus new at S217/218
- **English on all owner surfaces and in chat; Hindi is staff-side only.**
- One fact shouts in one place; records that a feed can answer must heal themselves.
- A stub-attributed row never carries a corroboration verdict.
- Auto-apply summaries + bill-range continuity are part of any future ingest surface.
- The hub is final; changes need a new ruling.
- **The PWA umbrella name is "Clinic"** (Sanjeevni is one section under it) — owner ruled.

*START_HERE_SESSION_219 · written at the S217/218 marathon close, 02-Sep-2026;
late-close additions appended after the portal tile went live. Next free:
**D361 · F-269 · Session 219** (unchanged — minting owed at the open).*
