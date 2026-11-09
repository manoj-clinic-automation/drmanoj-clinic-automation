# S764_CASEPACK_V2 — the Case Pack enquiry v2 (D880)

**The owner, 09-Nov-2026 10:36–13:32 IST:** his FINAL on three mock-ups — the Enquiry screen v4 (`PNrgan7RNL6Fko4oncFzAs`), the fracture
templates (`BLxVkAJ2qt1yZGkUqeQFCE`), the package seeding page (`GGyUJWvbHM5fpR91wJpczS`, "the format looks okay"; the charge groups
"OK" 13:27) — *"build in a fresh session, as ONE kit"*. The plan: `S416_CASEPACK_V2_PLAN.md` (canon).

**Why.** His cash packages, the estimate log and the case context lived in each browser's localStorage — one list per device, the page's own
words "Saves on this device only"; the patient-link box carried the blue border while the procedure search sat plain below it; stages 3 and 4
said "parked" though the IPD case has existed since S680; private room was the default everywhere; a package quoted a 50%-of-surgery
"share" that was not his rule.

**What changes.**

| where | what he sees and does |
|---|---|
| the page top | the **procedure / bone / code search leads**; the patient link is a quiet line above it (optional, can be done later); the payer segment Cash · Ayushman (HBP 2022 · Tier 2) · TPA (10 insurers) |
| **DTH rates** (fold) | ONE per-day list — wards (General, Semi-private, Private, Deluxe, ICU), daily (doctor visit, nursing), optional per day (high-risk care). Edit a figure, add a row, delete a row, **Save rates** — on the server, dated, the old list kept in `cp_history/`. Never repeated inside an estimate. |
| **Build an estimate** (fold) | blank: surgery ₹, implant ₹, stay; small / medium / major fills anaesthesia · OT meds · ward meds (3,000·2,000·1,000 / 5,000·3,000·2,500 / 6,000·10,000·5,000); general ward and the basic implant the defaults |
| **My packages** | the server's list, grouped by region (shoulder girdle · arm, elbow · forearm · wrist, hip · thigh, knee · leg · ankle, knee arthroscopy, also common, other packages). Tap one → it opens in place as the estimate sheet at general ward. A fixation he has no package for shows as a dashed template row (its SB code and HBP implant note); tap → Build opens prefilled with the fracture and stay, figures blank. |
| **the sheet** | **every line a fold** opening its heads in place: Surgery + OT (20%) · anaesthesia / OT meds / ward meds / admission / C-arm / investigations / other · room × days + visits + nursing (+ optional) · implant + grade (Basic SS ×1 · Premium Ti ×1.6 · Imported ×2.4) · discount. **Estimate to patient** big; **only you · my net** (purple) = estimate − admission − (anaesthesia + OT meds + ward meds + implant + investigations) − discount, × his share (50%, a private setting). Buttons: **Give estimate** (saved under the patient: date, figures, who gave it) · WhatsApp · Print / PDF · **Save changes to this package** (on a quoted one) · **Save as a new package**. |
| the foot bar | **Next: Consent →** (the template feeds the consent's opening, the body part and bone, the OT list's procedure) · **Estimates given** (the server's list — date, patient, package, total, who; *Taken up / Not / Copy / Use again*) · **Manage packages** (the seeding page) |
| the stepper | **1 Estimate → 2 Consent → 3 OT & orders → 4 IPD case** — all four live; 2 opens the Case Pack on the Consent pane, 3 on the OT list, 4 is *Continue to IPD case* (needs a linked patient) |
| **Manage packages** = `/portal/casepack/seed` | the defaults strip (ward, implant grade, admission, C-arm, investigations, **his share %**); the **charge groups** (Small bone / percutaneous · Single plate / nail, upper limb · Complex upper limb · Hip fixation · Hemiarthroplasty · Long bone, lower limb · Complex lower limb · Arthroscopy; THR, THR revision, Potts spine on their own) — surgery ₹, stay and size ONCE per group, every linked member follows, *linked* unticked keeps a row's own figures (**differs** marked); one row per fixation with the Ayushman code, rate and implant provision on the left and his figures on the right, the total at general ward and his net; suggested figures dashed amber until he types; **Save all packages** (pinned by version — a save from another device first is refused and reloaded, nothing lost); **Clear suggestions**; **Import this device's saved packages** (the old localStorage list, merged by name, once per device); rename, retire, add a group, add a package |

**On the server (`casepack_v2.py`, behind the Case Pack's owner-only guard, files in `/root/wa/casepack/`, the PHI store, in the encrypted
nightly — D270):** `cp_packages.json` (seeded ONCE on his first open from his 15 live packages — the page's own list — plus one *suggested*
package per catalogue option without one; 12 of his 15 map to the catalogue, THR revision / Potts spine / the unnamed one stand alone),
`cp_rates.json`, `cp_estimates.jsonl` (append-only; a *mark* is a new line), `cp_settings.json` (share %), `cp_history/` (every previous
file, dated). Writes are atomic and under a lock; this module is their sole writer; nothing is ever deleted (a retired package is hidden,
not removed). **Suggested packages are never quoted from the enquiry list** until he makes them his (Save as a new package, or Save all on
the seeding page).

**Not touched:** the consent, the OT list, the pre/post-op orders and the OT note (S216 · S684 · S685), the saved cases and the ledger, the
Ayushman and TPA data and panes, the IPD case (`surgery_cases.py`), `portal.py`. The old on-device package list (`dma_cash_v1`) is read
only by the seeding page's Import button.

**Proof.** `walk_s764.py` — 38 checks on a made-up store (the seed, the worked example 54,700 → 35,000 → 17,500, premium / high-risk /
discount arithmetic, pinned saves and 409s, empty and duplicate refusals, group flow to linked members, history kept, rates guards,
estimates append / list / mark, import, templates, both pages served, the removed builder gone, the consent code intact) — green on the
kit's files, **red at check 1 on the live files**. `browser_s764.py` — 46 checks in Chromium at 1366 and 390 px against a live harness
(cloud-side evidence): the owner's whole road. The installer rehearsed: DRY · install · already-installed · undo · changed-live STOP ·
a red journal line and a door leaking 200 after the restart both put every file back.

**Install** (after the publish), one line on the server — `DRY=1` first:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s764kit && cp -rp /root/deploy/repo/deploy_kits/S764_CASEPACK_V2 /tmp/s764kit && DRY=1 bash /tmp/s764kit/install_S764_CASEPACK_V2.sh
```
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s764kit && cp -rp /root/deploy/repo/deploy_kits/S764_CASEPACK_V2 /tmp/s764kit && bash /tmp/s764kit/install_S764_CASEPACK_V2.sh
```
Undo: `bash /tmp/s764kit/install_S764_CASEPACK_V2.sh --undo` (the cp_* stores are kept).
