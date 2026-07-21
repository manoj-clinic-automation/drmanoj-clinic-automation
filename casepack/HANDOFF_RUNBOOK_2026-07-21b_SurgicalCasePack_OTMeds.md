# HANDOFF RUNBOOK — Surgical Case Pack / OT Medicines
**Date:** 2026-07-21 (session b — second session this date)  **Track:** Surgical Case Pack (website project)
**Predecessor:** HANDOFF_RUNBOOK_2026-07-21_SurgicalCasePack_Phase1j-v4layout.md

---

## §0 — What happened this session

**Theme:** OT medicine list overhaul + Ayushman package completeness audit. All work in `casepack_page.html` (PC file only, per doctor — phone copy NOT produced this session). **Final file: md5 `82e412307030d52b3d3afa39c7956693`, 274,374 bytes. NOT yet deployed.**

### The 10 changes shipped (one cumulative file)

1. **Mephentine/Termin duplicate fixed** — both were mephentermine; kept `Termin ×1`, dropped Mephentine from `OT_GA`. GA extras now 6 items.
2. **Two-slot antibiotic scheme** replaced the old single 5-option pick (Vinbactum/Amikacin/Tazar/Genticyn/Acrovin all removed as a list):
   - `OT_ABX1` = Inj Vinbactum DS / Inj Vintaz 4.5 g
   - `OT_ABX2` = Inj Amikacin 500 mg / Inj Vintob 80 mg
   - Both render as rows 6–7 (after IV set), ×1 each. Copy/WA/Print headers now read "Antibiotics: X + Y". Two dropdowns on screen (`ot_abx1`, `ot_abx2`).
3. **Infiltration-kit tick-box** (`ot_infil`, beside GA/Viral). Supacef 750 (local infiltration) removed from THR auto-list; ticking adds it (`OT_INFIL`) for any procedure. "Infil kit" flag prints in headers.
4. **Ayushman gloves** — `Gloves No.7 (white) ×4` → `Gloves ortho No.7 ×6` (same as Paying). Ayushman-lean otherwise unchanged (still drops Transpore 2" + Vicryl VP2352).
5. **Search plural fix** — `match()` (line ~476, shared by Cash/Ayushman/TPA finders) required every typed word as exact substring; "metaphyseal fracture**s**" therefore returned nothing. Each token >3 chars ending in 's' now also matches its singular. Verified: "metaphyseal fractures" → SB009A ✓.
6. **Ayushman completeness audit (finding: nothing was missing).** All 151 PDF rows extracted via pdfplumber from `Ayushman_dec_2022_ortho.pdf`; **all 141 orthopaedic SB packages already embedded; zero rate mismatches vs PDF column-3** (the tool's original rate tier — convention confirmed and locked). Only PDF rows absent from tool: PM041A (cancer-pain plexus) + SC001–SC005 (9 head-neck oncology rows) — deliberately excluded as non-ortho. SB054A / SB080A appear twice in the tool by design (8–10 vs >10 screws split of compound PDF cells).
7. **Add-item catalogue** — `ot_newi` input now has a `<datalist id="ot_cat">` built at init from the union of every OT data source (65 unique items). Pick-and-filter OR free-type items outside the database; add handler untouched.
8. **Upper limb anaesthesia logic** — adds `Inj Lox 2% ADR ×1` + `Inj Anawin (plain) ×1` (brachial block); drops `Anawin Heavy (spinal)` + `LP needle 26`. Implemented via new **procedure-level `drop` mechanism** in `otBuild()` (procs now support `drop:[...]` exactly like tiers).
9. **Chromic** — both sizes are defaults everywhere: base list now carries `Chromic 1-0 (RB) ×1` **and** `Chromic No.1 (RB) ×1`.
10. **Clavicle = upper-limb case** — same adds (Lox ADR + Anawin plain) and drops (Anawin Heavy + LP needle) as Upper limb; keeps its Ethibond No.5.

### Plumbing notes
- `otState` fields: `abx`→`abx1`+`abx2`; new `infil`. `caseBundle()` snapshot updated accordingly (save-only; no restore path exists, so old saved JSONs are unaffected).
- `OT_EXTRA` exists as an empty extension point for future catalogue-only items (Lox/Anawin-plain moved onto the upperlimb list, so catalogue picks them up from there).
- Every edit verified by `node --check` on the script block + node simulation of `otBuild()` per tier×procedure; diffs kept surgical.

### Stale-deploy suspicion (unresolved, likely)
Doctor's live page showed Ethibond missing on Ayushman+THR and "no gloves ortho" — the working file shows both, and the audit shows data complete. Strong indication the **deployed server copy is older** than project-knowledge copy. First deploy of this session's file settles it.

---

## §1 — Mental models to carry forward

- **PC file only this session.** Phone copy intentionally not maintained; regenerate as a byte-identical copy of the current PC file when the doctor asks.
- **Ayushman rate convention: PDF column 3** ("Tier-3 rate" on cards). Any future rate edits must use that column.
- **Anaesthesia logic is now procedure-contextual:** spinal kit (Anawin Heavy + LP needle 26) = Generic + all lower-limb procs (lowerlimb/THR/TKR/ACL/implant-removal); block pair (Lox 2% ADR + Anawin plain) = Upper limb + Clavicle. The `proc.drop` mechanism is the tool for future context tweaks.
- **Search = AND-substring with plural tolerance.** The `q` field on ayush entries is the lowercase haystack; new entries must populate it the same way.
- **casepack_page.html remains single source of truth**; deploy = full-file replacement by the doctor; `casepack_app.py` requires the exact filename.

---

## §2 — Open backlog / next steps

**Deploy + 30-second verification (doctor):**
- [ ] Replace live `casepack_page.html`, hard-refresh (Ctrl+Shift+R).
- [ ] Ayushman payer → search "metaphyseal fractures" → SB009A ₹19,200 appears.
- [ ] OT tab → Ayushman + THR → two antibiotic dropdowns, Infiltration-kit tick-box, "Gloves ortho No.7 — 6", both Chromics.
- [ ] OT tab → Upper limb / Clavicle → Lox ADR + Anawin plain present; Anawin Heavy + LP needle absent.

**Pending doctor decisions (carried / new):**
- [ ] **Attest redundancy** (carried from previous runbook): trim the inline "हस्ताक्षर/दिनांक" text now that the dashed dr-box exists? Wording change — awaiting OK.
- [ ] Rename `Termin` → `Termin (mephentermine)` on the printed list for OT-staff clarity? (Optional.)
- [ ] Should `Inj Anawin (plain)` also auto-add when the Infiltration-kit box is ticked (infiltration cocktail)? Raised, not decided.
- [ ] Phone file regeneration timing.

**Default-next candidates:**
- **Phase 1k** — extension-of-surgery consent clause (design + preview first).
- **HBP-2022 ingestion.**
- Further OT-list review via `OT_Medicines_Review_Preview.html` (note: preview predates changes 7–10; regenerate before reusing).

---

## Close-out checklist status (vs END_OF_SESSION_PROMPT)
1. Summary → done (§0).
2. Master KB → KB file not in this session's context; **ready-to-paste section supplied** (`KB_APPEND_2026-07-21b_OTMeds.md`).
3. Runbook → this file.
4. Umbrella Architecture → **no change** (no D-series decision, no module status change; all work internal to the existing Case-Pack module).
5. API Quick-Ref → **no change** (no API behaviour touched).
6. GitHub commit message → in chat + inside KB-append file.
7. Project-knowledge swaps → in chat.
8. Cold backup → session zip supplied (single-track session; contains this session's deliverables, not the full multi-track kit).

### GitHub commit message
```
Case-pack OT list overhaul + Ayushman audit (2026-07-21 session b)

- Fix GA duplicate: keep Termin, drop Mephentine (same drug)
- Antibiotics: two-slot scheme (Vinbactum DS/Vintaz 4.5g + Amikacin 500/Vintob 80)
  replacing single 5-option pick; headers now "Antibiotics: X + Y"
- New Infiltration-kit tick-box; Supacef 750 moved off THR auto-list
- Ayushman gloves -> Gloves ortho No.7 x6
- Search: plural-tolerant match() (fixes "metaphyseal fractures" zero results)
- Audit: all 141 Ayushman SB packages verified present, 0 rate errors vs PDF col-3
- Add-item box: 65-item catalogue datalist + free-text
- Upper limb & Clavicle: +Lox 2% ADR +Anawin plain; drop spinal kit
  (new procedure-level drop mechanism in otBuild)
- Base sutures: Chromic No.1 (RB) added alongside Chromic 1-0 (RB)
- caseBundle snapshot: abx -> abx1/abx2, + infil flag
- node --check clean; per-change otBuild simulations verified
- PC file only (md5 82e412307030d52b3d3afa39c7956693); phone copy deferred
```
