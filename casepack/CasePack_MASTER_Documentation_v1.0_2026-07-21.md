# SURGICAL CASE PACK — MASTER DOCUMENTATION
**Version:** 1.0 · **Date:** 2026-07-21 · **Status of live artifact:** `casepack_page.html` md5 `82e412307030d52b3d3afa39c7956693` (274,374 bytes) — **deployment pending**

> **Supersession notice.** This document REPLACES AND SUPERSEDES all prior incremental documentation for this track, including `HANDOFF_RUNBOOK_2026-07-20_SurgicalCasePack_Phase1j.md` and `HANDOFF_RUNBOOK_2026-07-21_SurgicalCasePack_Phase1j-v4layout.md`. Those files remain useful only as historical change records; every current-state fact lives here. Future sessions should read THIS file first, then only the newest runbook.

---

## 1. What this system is

A single self-contained HTML tool (`casepack_page.html`) that handles the complete pre-surgical paperwork workflow for Dr. Manoj Agarwal's practice at Dhanwantari Tomer Hospital, Bareilly. One patient case flows through five modules on one page: cost estimate (three payer types) → OT medicine list → pre-op / post-op / op-note templates → Hindi surgical consent (print-ready) → case save/record. It runs fully offline (all data embedded, state in localStorage) and is served on the clinic PC by `casepack_app.py`, which requires the exact filename `casepack_page.html`.

## 2. Files, deployment, verification

**Single source of truth:** `casepack_page.html`. A phone copy, when wanted, is a byte-identical duplicate under a different name — currently **deferred by the doctor; PC file only is maintained** (decision of 2026-07-21b).

**Deploy protocol:** full-file replacement only, done by the doctor; never partial pastes. After replacing: hard refresh (Ctrl+Shift+R).

**Post-deploy verification (30 seconds):**
1. Ayushman payer → search "metaphyseal fractures" → SB009A ₹19,200 appears (proves plural-search fix AND fresh deploy).
2. OT tab → Ayushman + THR → two antibiotic dropdowns, Infiltration-kit tick-box, "Gloves ortho No.7 — 6", both Chromics.
3. OT tab → Upper limb or Clavicle → Lox ADR + Anawin plain present; Anawin Heavy + LP needle absent.
4. Consent → generate any THR → Ctrl+P (untick "Headers and footers") → 3-line letterhead repeats page 2 onward, clean last page.

**Stale-deploy history:** on 2026-07-21 the doctor observed items "missing" (Ethibond, ortho gloves) that the project-knowledge file contained — evidence the server copy had fallen behind. Check #1 above settles freshness every time.

## 3. Module reference (current state)

### 3.1 Case header
Fields `c_name / c_age / c_side / c_part / c_bone` feed every module's output header and the print filename (`docBaseName()` → Name_ClinicID_Date).

### 3.2 Estimate finder — three payers
- **Cash:** 16 bundled packages (Distal radius CRIF, Potts spine, Implant removal, THR, THR revision, one unnamed placeholder, Tibia plate, Tibia ILN, PFN, Clavicle plate/nail, Olecranon, Proximal tibia 1/2-plate, Modular bipolar imported) with per-head cost breakdown; room upgrade (General 2000 / Semi-pvt 3000 / Private 4000 / Deluxe 5000 / ICU 5000 per day) and high-risk ₹1300/day riders. Device-level package edits persist in localStorage; "Reset" restores originals.
- **Ayushman:** **141 SB packages — verified complete and rate-accurate on 2026-07-21** against `Ayushman_dec_2022_ortho.pdf` (pdfplumber full-table extraction, zero mismatches). **Rate convention (LOCKED): PDF column 3** ("Tier-3 rate" on cards). SB054A and SB080A intentionally appear twice (8–10 vs >10 screws variants of compound PDF cells). Ten non-ortho PDF rows (PM041A pain block; SC001–SC005 head-neck oncology) deliberately excluded. Multi-select builds a combined quote.
- **TPA:** embedded `TPA Network Tariffs — Dhanwantari Tomer Hospital` dataset (10 insurers: IFFCO Tokio, Max Bupa, FHPL, Paramount, SBI General, Aditya Birla, Bajaj Allianz, Reliance General, Star Health, Religare Grameen), verified 2026-06-30 by page-level visual re-read; per-row confidence flags and [UNREADABLE]/[PARTIAL] markers preserved.
- **Search (all three):** AND-of-words substring match, **plural-tolerant since 2026-07-21b** — any word >3 chars ending in "s" also matches its singular. New Ayushman entries must populate the lowercase `q` haystack field.

### 3.3 OT medicine list
Build order (fixed): base → antibiotics (rows 6–7) → gloves → tier extras → procedure extras → Infiltration kit (if ticked) → GA (if ticked) → Viral (if ticked) → apply tier drops AND procedure drops. Every quantity editable on screen; rows deletable; extras addable.

**Base (23 items, every case):** NS 1L plastic · DNS/RL 1L · Viggo 20 · Canofix · IV set · LP needle 26 · Anawin Heavy (spinal) · Syringe 10ml ×5 · Syringe 5ml ×5 · DW 5ml ×5 · Betadine scrub · Betadine lotion · Bandage 6" ×6 · Transpore 2" · Ethilon 3336 · Chromic 1-0 (RB) · **Chromic No.1 (RB)** · Vicryl VP2352 · Butrum 2mg · Tramazac 2ml · Dynapar · Periset · Mizolam.

**Antibiotics — two mandatory slots (replaced the old 5-option single pick on 2026-07-21b):** Slot 1 = Inj Vinbactum DS / Inj Vintaz 4.5 g; Slot 2 = Inj Amikacin 500 mg / Inj Vintob 80 mg. Output headers read "Antibiotics: X + Y".

**Gloves by tier:** Ayushman ortho ×6 · Paying ortho ×6 · TPA ortho ×8.

**Tiers:** Ayushman-lean drops Transpore 2" + Vicryl VP2352; Paying neutral; TPA-rich adds Iodrape/IO-drape large, Cling drape, Large sheet ×2, Ioban, Sterilium 500ml, Gown ×3.

**Procedures (adds / drops):**
- Generic — base only.
- Lower limb — +RL 1L extra.
- **Upper limb — +Inj Lox 2% ADR, +Inj Anawin (plain); DROPS Anawin Heavy + LP needle 26.**
- **Clavicle — +Ethibond No.5, +Inj Lox 2% ADR, +Inj Anawin (plain); DROPS Anawin Heavy + LP needle 26.**
- THR — +NS/RL extra, Romovac-16, Ethibond No.5, Ropivacaine (Themis) ×2, Hip U-drape, Stockinette 8cm, Cement gun, Pulse lavage, Ioban 22×17, Suction set, Skin stapler. (Supacef moved to Infiltration kit.)
- TKR — +Epidural kit 18, IO drape large, Romovac 16, Skin stapler, Vaccu suction, Ethibond No.5.
- Arthroscopy/ACL — +NS 3L irrigation ×3, TURP set, Camera cover, Cling drape, Ethibond No.5.
- Implant removal — base only.

**Toggles:** *Infiltration kit* → Supacef 750 (local infiltration) ×1, any procedure, "Infil kit" flag in headers. *Under GA* → Profol ×2, Glycopyrrolate ×5, Atropine ×5, Primacort 100 ×2, Avil ×2, **Termin ×1** (Mephentine removed 2026-07-21b — same drug). *Viral +ve* → barrier kit, Mops ×5, Plain sheet ×2, Plain towel ×2, Gown ×5.

**Add-item catalogue:** the Add box is a datalist of all 65 unique items from every source above — pick-and-filter, or free-type anything off-database. `OT_EXTRA=[]` is the extension point for future catalogue-only items.

**Encoded anaesthesia logic:** spinal kit (Anawin Heavy + LP needle 26) belongs to Generic + all lower-limb procedures; brachial-block pair (Lox 2% ADR + Anawin plain) belongs to Upper limb + Clavicle. Procedure-level `drop:[...]` (added 2026-07-21b) is the mechanism for future context rules.

### 3.4 Peri-op templates
Editable pre-op orders, post-op orders, operative-notes templates; print prefixes the case tag.

### 3.5 Consent engine (v2 content · v4 print layout — LIVE since 2026-07-21a)
Hindi consent assembled from the doctor's own library: procedure-specific opening (tokens {NAME}{AGE}{RELM}{RELN}{RES}{SIDE}{PART}{BONE}{DUR}) + shared clauses (consultation, understanding, re-operation possibility, infection, anaesthesia, no-guarantee, physiotherapy, non-union where relevant) + closing + attestation. Print layout v4: 3-line repeating letterhead (title / credentials / patient-निवासी-date), no in-body title, borderless consent table, side-by-side dashed end-signature boxes, doctor's dashed signing box in attestation, auto "पृष्ठ X/Y". Title is print-only. **`CS_ATTEST` wording is LOCKED — text edits need explicit doctor OK.** `csLastMeta` carries `res` for the header.

### 3.6 Records & case save
"Save to record" keeps estimates in localStorage (CSV export). "Case save" posts `caseBundle()` JSON to `/save` when the local app is running, else downloads for `cases\inbox\`. **Schema note:** OT block fields are `abx1`, `abx2`, `infil` (since 2026-07-21b; formerly single `abx`). Save-only — no restore path — so older saved JSONs remain valid.

## 4. Locked decisions
1. Ayushman rates = PDF column 3, always.
2. `CS_ATTEST` wording locked.
3. Full-file deploys only; exact filename `casepack_page.html`.
4. Termin (not Mephentine) is the GA vasopressor label.
5. Two-slot antibiotic scheme is the standard; old 5-option list retired.
6. Non-ortho PDF rows stay out of the Ayushman finder.
7. PC file only until doctor requests phone regeneration.

## 5. Change history (condensed)
- **Phase 1e–1j (…→2026-07-20):** case-pack modules assembled around the original estimate finder; consent engine v2 built from doctor's library.
- **2026-07-21a (Phase 1j-v4layout):** v4 print layout ported into live tool; stale `Surgical_Estimate_Finder_Phase1d.html` identified for deletion. md5 `1db68fa0…`.
- **2026-07-21b (this consolidation):** ten OT/search changes — Termin duplicate fix; two-slot antibiotics; Infiltration-kit toggle; Ayushman gloves ortho ×6; plural-tolerant search; Ayushman completeness audit (141/141, 0 rate errors); 65-item add catalogue; upper-limb block logic + procedure-level drops; Chromic No.1 added to base; Clavicle as upper-limb case. Final md5 `82e41230…`.

## 6. Open backlog
- [ ] **Deploy** current file + run §2 verification.
- [ ] Attest redundancy: trim inline "हस्ताक्षर/दिनांक" text now the dashed box exists? (Wording change — doctor OK required.)
- [ ] Optional relabel "Termin (mephentermine)" for OT-staff clarity.
- [ ] Decide: auto-add Inj Anawin (plain) when Infiltration kit ticked?
- [ ] Phone-file regeneration timing.
- [ ] Phase 1k — extension-of-surgery consent clause (design + preview first).
- [ ] HBP-2022 ingestion.

## 7. Companion artifacts
- `OT_Medicines_Review_Preview.html` — read-only three-tier comparison of the OT data, regenerated 2026-07-21b to match this build exactly; use for future list reviews (tap rows → notes box → paste back).
- `Ayushman_dec_2022_ortho.pdf` — rate source of record.
- `TPA_Tariff_Master_Verified_v1.json` / `TPA_Verification_Ingestion_Brief_v1_0.md` — TPA data provenance.
- Historical runbooks (superseded, retained for archaeology only).
