# HANDOFF RUNBOOK — v134 (Session 200 · THE GO-LIVE SESSION · 25 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 200 — FULL build EOS)

**🔒 JULY 2026 LOCKED: ₹59,163 · by manoj · 2026-08-25 07:16:48 — the first month the system
carried end to end.** The owner's "⭐0 salary items" pick became the graduation run: every July
question ruled, the engine upgraded to his final shape, the whole flow walked on real data,
twelve kits shipped in one session.

1. **Nine decisions minted (D338–D346)** — full text Archive §S200: the past-day presence
   correction (D338) · the fix-absents desk + undo (D339/b) · the Sunday reckoning (D340 half-day
   → D341 DERIVED weight + D341b roster gated to 2099) · the suspended hold with the COLLECT limb,
   Arjun fully outside the loop, half-for-pay/whole-for-deterrent (D342a-c) · divisor 30.5 +
   Amir-off-biometric (D343) · **Darpan folded in + AUGUST = GO-LIVE for all staff** (D344) ·
   the ramp fine (D345/b) · the go-live engine kit (D346).
2. **THE VERDICT** (the owner's own metric): old system as paid vs the finalised system, same
   July — **all eleven staff gain, ₹5,384.37 more in staff hands**; late money ₹6,846 → ₹1,011
   collected + ₹3,034 suspended; ramp fines ₹660; Diwali accrual ₹524.59. Bilingual staff PDF +
   the owner workbook (CASH top-ups ₹4,519) delivered owner-side.
3. **The PWA unified**: /register AND /ledger now under the followup origin (append-only vhost —
   the LIVE file had drifted from the repo mirror: never full-replace it); portal tiles
   same-origin; approve-where-you-read on the sheets; the retired old ledger salary lock DISARMED.
4. **Final pins:** `staff_register.py f85a4b06…` v0.12 · `salary_policy.py 7c0cfb94…` v1.7 ·
   `att_month_report.py 0184cb13…` v2.7 · `staff_ledger.py eaa305cb…` v3.4 (**R9 on-box GREEN
   owed — verify**) · `portal.py 24ea2c0b…` · box data `manual_advances_2026-07.json` (deducts).
5. **F-178 minted OPEN** (the mid-duty punch blindsight). **Darpan's ₹3.55L confirmed real.**
   **Pravesh resigns 31-Aug.** The Staff Console / app / task-board design filed
   (`S200_StaffApp_Design_Candidate.md`, D347 candidate). No incident.

---

## §1 — MENTAL MODELS (added this session)

- **A capability the owner cannot complete in one pass is only half built** (D338 → D339).
- **A required field the user cannot see when pressing the button is a silent failure, not a
  validation** (D339b — the empty Reason box ate a whole batch invisibly).
- **The register records facts; pay conventions live in the money layer** — and state the UNITS
  before comparing two counts (the Sunday reckoning began as whole-days vs half-weighted counts).
- **Practice outranks the written setting when they disagree** — reconcile against what was
  actually paid (divisor 30.5 matched 8/10 real payments; the setting said 30).
- **A selftest that writes a live store is itself a live event** — snapshot and restore (R5b
  nearly left a forced 0.5 Sunday weight in live settings).
- **Kits carry code; money data travels outside git** — and the publish guard that refuses IS
  the discipline working (R7's manual-advances json).
- **A run-through on real data is the only auditor that presses every door** — one walk found
  the armed retired lock, Darpan's filter-hidden tranches, the 404'd ledger doors, and a
  signature sheet ₹55,030 from the truth.

---

## §2 — THE LIVE BACKLOG

> **The maintained copy is `OWNER_TODO_LIVE.md` (project knowledge, un-manifested by design —
> it edits as we work). The list below is the close-time snapshot.**

**⭐0 — owner actions (before the August close):**
- **TOKEN ROTATION** (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`; cron token also in the
  "UPI Reconciliation" GAS Script Properties) — exposed 21-Aug, highest severity.
- **Darpan's ₹20,000 SPECIAL** `0cc0b26b38c5`: signed application → upload → approve → enter
  17-Aug ₹20,000 (re-verify the S198 drawer figure at entry — his ledger now carries the ₹3.55L).
- **Pravesh exits 31-Aug**: advance position now; full & final at exit.
- **July cash top-ups ₹4,519** per the CASH SETTLEMENT tab · **Surendra ₹516 gap** (HELD) ·
  **Arjun's actual-paid figure** · **Shivani's August items** (recover ₹3,724.55 + the parked
  ₹3,000 advance).
- 18-Aug bills (8, ₹4,577, attribution only) · the correction-checklist day + 4 UPI/bank days ·
  auditor Monday report → triage.
- Staff comms: comparison PDF → portal Forms · staff acceptance of INTEREST terms · staff-phone
  PWA installs · clinic forms upload · Medical-PC Drive for Desktop (F-168) · Club-4 answers ·
  Club-3 samples.

**⭐1 — builder queue:**
1. **Ledger kit (owner-ordered):** cover/OT evening AUTO-DETECT suggestion queue · retire/link
   the old `/ledger/settings` page · cover-duty rate from `extra_duty_rs`.
2. **F-178** — punch-sequence surfacing + mid-duty-gap flag.
3. **The Staff Console (Phase 0, D347 candidate)** — after the owner's four rulings (leaver
   hold+pot disposition · probation numbers · task-media retention · managers-create-tasks).
4. **काम — the voice-first task board** (Phase A) → money views → requests → selfie-GPS punch.
5. PWA holdouts: the bare Attendance tile + assets.dr-manoj.in. · Purchase Portal (D335) stands
   as the other flagship. · Verify R9 on the box (grouped Advances page).

**⭐2 — THE AUGUST CLOSE = the first fully LIVE, ENFORCED run.** Carries: a leaver (Pravesh) ·
Darpan's SPECIAL + ₹3.55L schedules · three staff's ledger advances auto-recovering · Shivani's
two items · **the first suspended-charge cancel/collect cycle** (July's holds are armed). Watch,
don't assume.

**⭐3 — carried:** the S198 backlog (Purchase Portal flagship, Club C, B2 pack, Club 4,
expense-scan viewer, vehicle module, local-PC roadmap, casepack survey, repo mirror refresh).

---

## §3 — INSTALL DISCIPLINE (updated)

The standing chain holds (hash-verified bases · offline pre-flight · currency gates · projections
before measuring · `bash -n` installers · probes print never judge · hashes transcribed never
typed · route-200 selftests on whole-function Flask edits · data migrations with counts+backup).
**Added at S200:** the followup vhost is APPEND-MANAGED — the live file is drifted from the repo
mirror and must never be full-file replaced from it · selftests that touch a live store must
snapshot-and-restore · kits carry code only — money data goes to the box by paste (the publish
guard enforces it) · give the owner every VPS command as ONE full copy-paste block (standing
instruction) · publish BEFORE pull (an unpublished kit makes the VPS run a silent no-op).

---

## §4 — THE EOS AUTOMATION BOUNDARY (held)

The assistant executed the builds, the July lock support, and the full close (Archive/Register/
Fault appends with mechanical proofs, manifest, A8 pin list, A9 Notion, project swaps). **Owner
residual: one `PUBLISH_ALL.bat`, then on the box copy `live_pins_S200close.txt` →
`/root/deploy/live_pins.txt` and run `verify_live_pins.py` — expect GREEN (the S199 list would
show drift on the five moved files the box has right — F-134 shape, not a fault). Plus the R9
verification above.**

---

*HANDOFF_RUNBOOK v134 · Session 200 close · supersedes v133. If §0, §2 or this end-marker is
absent, this file is truncated and must not be used as canonical.*
