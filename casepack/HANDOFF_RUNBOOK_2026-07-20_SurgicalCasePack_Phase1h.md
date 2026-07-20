# HANDOFF RUNBOOK — 2026-07-20 — Surgical Case Pack (Phase 1e → 1h)
*Project: Website/SEO/Content (tools track). Predecessor: HANDOFF_RUNBOOK_2026-07-15_SurgicalEstimate_Phase1d.md (now superseded).*

## §0 — What happened this session

**Phase 1e — Case pack added to the finder** (`Surgical_Estimate_Finder_Phase1e.html`)
- New "Case pack" modal beside the untouched estimate engine: OT medicine list, consent, pre-op / post-op / surgery-note templates. Shared patient header.
- OT list built from `ORTHO_PACK_2023.xlsx` (23 sheets evaluated, ~20 medicine lists de-duplicated): base spinal kit + payer tier (Ayushman lean / Paying / TPA rich) + procedure add-ons (THR, TKR, arthroscopy/ACL, clavicle, limbs, implant removal) + GA cluster + viral-positive kit. Antibiotic = pick-one (default **Vinbactum DS**; Supacef 750 THR-local-infiltration only). All quantities editable; write-in blanks for implants + case-specific OT prep (structured catalogue deferred).

**Consent vetting** (`Consent_Library_Phase1.docx`)
- Doctor's real consents extracted from Consents.zip → format learned: flowing first-person Hindi narrative, no clause-stack. Skeleton doc built (23 procedure consents + 7 add-on blocks + 2 signature variants) and **vetted by doctor**, then treated as skeleton for the tool.

**Phase 1f — Consent engine v2** (`Surgical_Estimate_Finder_Phase1f.html`)
- Old clause-stack module deleted. New generator: ~30-procedure library in the doctor's own idiom, softened non-alarming register (कभी कभी / किसी किसी मरीज में / reassurance line / care-assurance after mortality clause). Variables + comorbidity ticks (8 → auto-composed high-risk para with mortality clause) + add-on ticks (8: खुली चोट, Ayushman implant limit, uncontrolled sugar, detailed anaesthesia, delay, blood, minor, emergency authority). Choice dropdowns where surgery has options (clavicle rod/plate; radial head plate/excision/replacement). Output fully editable, Variant-B signature blanks, print/copy.

**Phase 1g — "the vitals-app way"** (`surgical_casepack_v1g.zip`)
- Pattern copied from D:\clinic_writer (vitals_app.py): `casepack_app.py` Flask on **127.0.0.1:5058** (tracker 5000 · vitals 5057), reads tracker `patient_master.csv` + `patient_diagnosis.csv` **read-only** (one-writer-per-file law), writes only inside `D:\surgical_casepack\`.
- Patient search (Clinic ID / name / mobile fragment / UID) → header autofill incl. age + sex (sex pre-sets हमारे/हमारी).
- **Save case** → `case_ledger.csv` (C-YYYY-NNNNNN) + `case_archive\YYYY\UID\date_caseid_bundle.json` (frozen: latest estimate record w/ line-item detail + OT list + consent-as-edited + peri-op notes) + standalone printable `_consent.html`. Offline/phone: same page works file-opened; Save downloads JSON for `case_archive\inbox\`.
- End-to-end tested with synthetic CSVs (search, double save, ledger, archive tree, consent file).

**Phase 1h — English-in, Hindi-out** (`Surgical_Estimate_Finder_Phase1h.html`, `surgical_casepack_v1h.zip`) ← **CURRENT**
- Side / Body part / कब से converted to English dropdowns emitting fixed Hindi (13 body parts; each with "Other — type…" free-text escape). Bone stays free-text by design.
- Name transliteration at Generate: online Google Input Tools (1.5 s timeout) → offline rule-based fallback (tested: विमला देवी, रमेश कुमार, मुन्नी देवी, सिंह correct; अगरवल-class misses are edit-and-fix). Applies to patient + पिता/पति names; Hindi input passes through.

**Decisions locked (D-series candidates)**
- D-CP1: Saved cases (diagnosis-laden consents) live **outside** all Drive-synced paths — `D:\surgical_casepack\` local-only.
- D-CP2: Estimate snapshot in a case bundle = **full line-items frozen** at save (what the family was quoted).
- D-CP3: OT antibiotic is a per-case pick (5 options), not a fixed line.
- D-CP4: OT tiers are payer-based: Ayushman lean / Paying / TPA rich.
- D-CP5: Case pack port **5058**; one-writer-per-file honoured; tracker + vitals untouched.
- D-CP6: Consent library evolution ships as full-file page replacements (no on-device template editor).
- D-CP7: Transliteration is a convenience layer with offline fallback — never a dependency.
- (Per doctor instruction: the mid-session income/share estimates are **excluded** from KB and this runbook.)

## §1 — Mental models to carry forward
- The finder is now a two-headed tool: estimate engine (verified, frozen) + case pack (evolving). All evolution happens by full-file replacement of `casepack_page.html` / the standalone HTML — never partial edits.
- Consent v2 composes: opening (procedure template + variables) → choice para → risk para (proc risks + standard closers) → high-risk para (from ticks) → add-on paras → closing → signature blanks. Wording lives in `CONSENT_LIB` / `CS_*` constants in one block — fine-tuning = edit those strings, re-ship file.
- Vitals-app deployment pattern is the house standard for PC tools: bat-loop launcher, own port, read-only sources, own ledger + archive.

## §2 — Open backlog (next session starts here)
1. **Consent fine-tuning (deferred by doctor, top item):** on-device trial across real cases → wording corrections to CONSENT_LIB entries; possibly per-procedure risk additions. Doctor edits arrive as spoken corrections → ship as new full file.
2. OT list verification on device: base-kit skim vs pharmacy; **"Termin" full brand name still pending**; tier deltas (Ayushman drops / TPA adds) confirmation.
3. Structured implant catalogue (Economy SS / Premium Ti / Imported per assembly) to replace the write-in blank; case-specific OT-prep presets.
4. Peri-op templates enrichment once doctor shares real pre-op/post-op order sheets + op-note samples (blueprint open input #4).
5. Tracker-side "Cases" page in `app.py` reading `case_ledger.csv` (belongs to **Clinic Systems & Automation** project; deploy rule: replace .py only, never data\).
6. Transliteration polish if online path unavailable at clinic (add name-exceptions map only if real misses annoy).
7. Consent print letterhead variant (logo header) if wanted.
8. Deferred from earlier phases: month-projector idea (dropped unless re-asked); VPS hosting of the tool (deferred — offline-first for now).

## Install state (as of EOS)
- `D:\surgical_casepack\` install: **pending/partial** — doctor was mid-testing; v1h zip is the correct kit (overwrite `casepack_page.html` if v1g was copied).
- Phone standalone: use `Surgical_Estimate_Finder_Phase1h.html`.

## Four-destination routing for this session's files
- Local + Drive backup + NotebookLM + GitHub: runbook, Consent_Library_Phase1.docx, Phase1h html, casepack zip (code files).
- GitHub path suggestion: `casepack\` new subfolder in `drmanoj-clinic-automation`.
- **Not** for cloud: nothing this session (no PHI in deliverables; test data synthetic).

## Project-knowledge swaps
- DELETE: `HANDOFF_RUNBOOK_2026-07-15_SurgicalEstimate_Phase1d.md`, `Surgical_Estimate_Finder_Phase1d.html`, `00_Consent_Generator.html`
- UPLOAD: this runbook, `Surgical_Estimate_Finder_Phase1h.html`, `Consent_Library_Phase1.docx`
