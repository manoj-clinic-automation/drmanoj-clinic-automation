# S416 — THE CASE PACK ENQUIRY v2 — the plan (D880) — written at the S416 close, 09-Nov-2026, the parent

**The build is session 418's, as ONE kit.** Owner's mock-ups, all approved in his words of 10:36 – 13:32 IST 09-Nov:
- the Enquiry screen v4 — `https://claude.ai/artifact/PNrgan7RNL6Fko4oncFzAs` (source `03_WORKING_PAPERS\S416\mockups\S416_casepack_enquiry_v4_mock.html`)
- the fracture templates — `https://claude.ai/artifact/BLxVkAJ2qt1yZGkUqeQFCE` (`S416_fracture_templates_mock.html`)
- the package seeding page — `https://claude.ai/artifact/GGyUJWvbHM5fpR91wJpczS` (`S416_package_seeding_mock.html`), approved "the format looks okay"; the charge groups (below) approved "OK" 13:27 IST.

## 1 · What is wrong today (read from the live bytes: `casepack_page.html` f95d186d, `casepack_portal.py` cbbd392d)

1. `#estPbQ` (Link patient) carries a 2 px blue border; the procedure search `#q` is plain below it — the eye goes to the wrong box.
2. Cash packages (`dma_cash_v1`), the estimate log (`dma_estlog_v1`) and the case context live in **localStorage** — one list per device, nothing on the server; "Saves on this device only" in the page's own words.
3. The foot buttons *Case pack · Records · Build / manage* say nothing of what they do.
4. The stepper says 3 · Surgery done and 4 · Money are "parked (CP-3/CP-4)" though the IPD case (S680 – S682) exists; stage 2 opens on the OT list, not the consent (`cpSetStage(2)` → `caseBtn.onclick`, default pane `ot`).
5. Private room (`state.room='pvt'`) is the default everywhere.
6. The Ayushman data: 138 SB rows = HBP 2022, Tier 2 (Y), the right tier for Bareilly; implants separate at the fixed HBP figure (TKR SB039A ₹41,300 + ₹55,000 checked against the published list); no duplicate codes; SB054 and SB073 absent (not orthopaedic). The TPA set: 10 insurers from DTH's own sheets, 8 HIGH, **FHPL 2025 and PARAMOUNT LOW** (handwritten / skewed scans, most rows unpriced) — ask DTH for clean copies; one unpriced row each in IFFCO (Trigger finger), Max Bupa (Menisectomy), Aditya Birla (Implant removal).

## 2 · The rulings (D880), in his words and order

- The procedure / bone / code search is the lead control; the patient link a quiet one-liner above it (can be done later).
- **Cash packages, the DTH rates and the estimates given are saved on the server** — the same list on his phone, the clinic PC and Shavez's PC; quick retrieval during an enquiry; on-the-spot editing while negotiating.
- **DTH rates: ONE separate editable list**, only the core per-day rates (wards: General, Semi-private, Private, Deluxe, ICU; daily: doctor visit, nursing; optional per day: high-risk care). Edit a figure, add a row, delete a row, **Save rates** (dated; the old list kept). Never repeated inside an estimate — the estimate's room line only picks a ward and the days.
- **General ward is the default everywhere**; the **basic (SS) implant grade** is the default; Premium (Ti) and Imported are grades of the same package.
- **Build an estimate** is its own fold-out: blank — surgery ₹, implant ₹, stay, case size (small / medium / major fills anaesthesia · OT meds · ward meds: 3,000 · 2,000 · 1,000 / 5,000 · 3,000 · 2,500 / 6,000 · 10,000 · 5,000), room, discount.
- **Every estimate line is its own fold** and opens its heads in place: Surgery + OT (20%) · anaesthesia / OT meds / ward meds / admission / C-arm / investigations · room × days + visits + nursing (+ optional) · implant + grade · discount. No separate "adjust heads".
- **"Save as a new package" on every estimate**; "Save changes to this package" when it started from one; "Give estimate" records it under the patient (date, figures, who gave it) and it shows on the IPD case later.
- Foot buttons: **Next: Consent → · Estimates given · Manage packages.** Stepper: **1 Estimate → 2 Consent → 3 OT & orders → 4 IPD case** (stage 4 = the existing *Continue to IPD case*).
- **Fracture templates**, by region (shoulder girdle · arm; elbow · forearm · wrist; hip · thigh; knee · leg · ankle; knee arthroscopy & ligaments; the "also common" set he says yes or no to): each fixation he does is a template that opens the estimate prefilled (cash package / Ayushman code with its **implant provision** / the TPA row), the consent, the OT list and the orders carrying the bone and operation. Spine, hand and foot left out for now. The list as on the fracture-templates mock-up (20 fractures / 46 options + knee: meniscus, ACL, PCL, multi-ligament, synovectomy, HTO), with proximal tibia unicondylar / bicondylar, patella TBW / patellectomy and pilon named as he asked.
- **Charge groups** (approved): surgery ₹, stay and case size set ONCE per group; **implant ₹ per fixation**; a member can be unlinked and keep its own figures; his 12 existing packages join their groups with their own figures kept and marked where they differ. The starting groups: Small bone / percutaneous · Single plate / nail, upper limb · Complex upper limb · Hip fixation · Hemiarthroplasty · Long bone, lower limb · Complex lower limb · Arthroscopy; THR, THR revision and Potts spine on their own.
- **The seeding page** (first fill, later price revisions): defaults strip (ward, implant grade, visit, nursing, admission, C-arm, investigations); one row per fixation with the Ayushman rate and implant provision on the left and the cash figures on the right; suggested figures (dashed amber) copied from the nearest existing package, "Clear suggestions"; the **package total at general ward** and **his NET**.
- **His net** (his eyes only): package total − admission (the hospital keeps it in a package case) − the outgoings paid from the lump sum (anaesthesia, OT meds, ward meds, implant, investigations) = the shareable amount; **his share 50%** (a private setting); the assistant's payment comes off on his side; the implant surplus left aside. Worked example, PFN general ward 2 days: total ₹54,700 → shareable ₹35,000 → net ₹17,500.
- **Post-discharge revenue is NOT in the case value** (his word 13:25 IST, capitals). The analysis of 13:08 (≈₹4,000 of clinic follow-up vs ≈₹2,000 at the hospital; a cash discount costs him 50%) stays in the Archive §S416, not on any screen.

## 3 · The build (session 418) — the parent's own files

- **Server (`/root/portal/casepack_portal.py` cbbd392d):** owner-guarded routes under `/portal/casepack/`: `packages` GET / POST (the list with groups, grades, implant per fixation, version history), `rates` GET / POST (the DTH list, dated history), `estimates` GET / POST (an estimate given — patient link, figures, who, when; readable by the IPD case), `templates` GET (the fracture catalogue with its SB codes and TPA names). Store: small JSON files beside `tr_dict.json` in `CASEPACK_DIR` (PHI dir; estimates carry patient names) — in the encrypted nightly (`clinic_state_backup.py` carries `/root/wa/casepack/` whole already, D270).
- **Page (`/root/wa/casepack/casepack_page.html` f95d186d, 470 KB — READ WHOLE FIRST, drift 4 since S216: S579, S680, S684, S685):** the Enquiry stage rebuilt as v4 (search first, payer segment, DTH rates fold-out, Build an estimate fold-out, My packages by fracture group, the foot bar, the stepper); the cash renderer reads the server list (localStorage only as an offline cache); `recordEstimate` → the server; the Ayushman and TPA panes unchanged in data, the fracture search matching templates; `cpSetStage(2)` opens on the Consent pane; stages 3 and 4 live.
- **A seeding page** (owner-only, `/portal/casepack/seed`) as mocked; the first seed from his 12 packages + the groups; walked on a made-up store.
- **Not touched:** the consent, OT list and orders code (S216, S684, S685) beyond the feed-forward of the chosen template; the IPD case (`surgery_cases.py`); the TPA/Ayushman data.
- **Walk:** made-up store, control on the live page red; Chromium at 1366 and 390 px; the net arithmetic by a pure function against the worked example; cold review; installer DRY / install / undo; his publish and one server line.

## 4 · Open for him (not blocking)
- Clean re-scans of the FHPL and Paramount TPA sheets from DTH.
- The "also common" set (supracondylar / lateral condyle humerus in a child, elbow dislocation): yes or no.
- The surgery ₹ per group on the seeding page — his figures replace the suggestions.

*S416_CASEPACK_V2_PLAN · the parent · 09-Nov-2026 13:4x IST.*
