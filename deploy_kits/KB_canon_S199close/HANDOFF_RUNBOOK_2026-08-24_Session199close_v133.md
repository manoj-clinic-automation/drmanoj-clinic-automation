# HANDOFF RUNBOOK — v133 (Session 199 · the salary-policy rebuild · 24 Aug 2026)

**Tier 0. §0 what happened · §1 mental models · §2 the live backlog · §3 install discipline · §4 the EOS automation boundary.**

---

## §0 — WHAT HAPPENED (Session 199 — FULL build EOS)

One owner instinct — *"the deduction logic seems too harsh"* — became a complete new salary
system, ruled clause by clause and live the same day, preview-tested on real July + August data.

1. **D336 — Salary Policy 2.0** (contract filed): progressive late pricing at each person's OWN
   salary minute-rate · 90 free min/month · the **Improvement Hold** (25% collect / 75% held,
   released on 30% improvement, waivable individual→all) · leaves symmetric full-day-rate, no
   ladder · dress/I-card ₹15 via Yes/No dropdowns · incentive → the **Diwali pot** (S163 kept) ·
   **every number a setting** (`salary_policy_settings.json`; recalibration never touches code) ·
   enforcement = `enforce_from`, preview until served.
2. **D337 — the Month-End Flow & Lock Desk** (contract filed): Sheet 1 attendance grid (punch
   times visible, today excluded, doors, staff own-view + remarks, windowed) · Sheet 2 money
   review (Darpan separate page + outstation; all fines/leaves/night-duty) · pack approval gates
   the lock · FINAL sheets only on an approved pack · the Lock Desk on the NEW engine — **refuses
   any non-enforced month** (F-150 structural), writes the hold ledger re-lock-safe.
3. **Seven kits installed GREEN** (SCEN1→SCEN3, SALFIX, FLOW1→FLOW3); final pins:
   `staff_register.py 124c6eb2…` v0.7 · `salary_policy.py 7f86cc87…` v1.3 ·
   `salary_engine.py bedd468e…` · `att_scenario.py 4dcd19bc…` v2.
4. **F-174…F-177 minted, all four closed same-session** (exclusion-mirror drift · checkbox
   polarity, August 88/74 → 0 migrated with backup · today-counted-absent · mislabeled scenario
   months). **No incident.**
5. **The one-time data look** (owner-ruled exception): the July sheet decoded and validated —
   machine raw-late = the owner's ₹1/min column to the minute, all ten staff; **Shivani's July
   row does not reconcile (≈₹4,575) — owner check owed**. Notice v3 + two-page salary print
   format drafted and owner-edited; playground workbook delivered owner-side.

---

## §1 — MENTAL MODELS (added this session)

- **Fairness is a rate, not a rupee.** The flat ₹1/min charged the lowest-paid ~3× their earned
  minute while charging the highest fair value. Pricing at each person's own salary minute-rate
  is what made "softer" also mean "juster".
- **A refundable stake beats a fine.** Money held in the staff member's own name, returned on
  measured improvement, motivates harder than the same money confiscated — and matches "deterrent,
  not punishment" exactly.
- **When a mirrored rule set grows, the fold sweeps the mirrors (F-174).** A drift guard that
  fires three sessions late is still the guard working.
- **A boolean input's polarity lives in its label (F-175).** Money never hangs on an unlabeled
  checkbox — and data that looks absurd (best staff "worst-dressed" 21/23 days) is a polarity
  question before it is a behaviour question.
- **A live view of an unfinished period excludes the unfinished unit (F-176).** A 6 AM "everyone
  absent today" teaches users to distrust the page.
- **Enforcement is a switch, never a side effect.** The lock refusing non-enforced months turns
  the F-150 lesson from a rule people remember into architecture nobody can forget.
- **Whole-function replacement must carry the decorators** — the harness ate two `@app.route`
  lines; the selftest's route-200 assertions caught it offline. Assert routes, not just functions.

---

## §2 — THE LIVE BACKLOG

**⭐0 — owner actions:**
- **Token rotation** (`FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN`) — exposed 21-Aug, STILL OPEN,
  highest severity, now four days old.
- **Shivani's July row** (≈₹4,575 gap: waiver or slip?) — before the July final working.
- **August advances data** (the July worksheet figures + August's + Darpan's pending ₹20,000
  SPECIAL `0cc0b26b38c5` approval with the signed application) — then the final working.
- Serving the notice (v3, Diwali wording) + setting `enforce_from` when ruled.
- The carried S198 items: item-wise Marg export sample · F-173 April-2025 bank check · staff PWA
  installs · forms upload · Auditor Monday triage.

**⭐1 — builder queue (in order, all owner-approved in principle):**
1. Lock-desk columns (Leaves, Absent) + "Absent fines (₹50/₹100)" rename + page legend.
2. **The Arjun threshold ruling** (fine threshold flat-3 vs per-staff allowed_offs) → one-line
   engine change once ruled.
3. Owner-advances entry on Sheet 2 (prefilled from the ledger, owner-typed where paper; audited;
   feeds Sheet 3) — the bridge until all advances live in the ledger.
4. Printable Sheet 2 (+ print buttons on the flow page).
5. **The selfie punch** — geotagged camera-only capture as EVIDENCE inside the D334
   present-request flow (auto-verify inside a geofence; the outstation tool). Mint as a decision
   first.
6. Hold-waiver UI (individual→all) on the lock desk / Sheet 2.

**⭐2 — the August close** = the first real run of the whole flow: pack → remarks → approvals →
enforcement decision → lock. Watch, don't assume.

**⭐3 — carried:** the S198 backlog (Purchase Portal = the standing flagship, Club C, B2 pack,
Club 4, expense-scan viewer, vehicle module, local-PC roadmap, casepack survey, repo mirror
refresh) — unchanged.

---

## §3 — INSTALL DISCIPLINE (updated)

The standing chain holds (hash-verified bases · offline pre-flight · currency gates · projections
before measuring · `bash -n` installers · probes print never judge · hashes transcribed never
typed). **Added:** route-200 selftest assertions accompany any whole-function edit of a Flask app
(the decorator-eater); a data migration ships with before/after counts printed and a DB backup
(the dress migration's shape); owner-side salary artefacts never enter the public repo — the
playground/notice/print drafts live in `D:\dr-manoj-git\` beside the July sheets.

---

## §4 — THE EOS AUTOMATION BOUNDARY (held)

The assistant executed the builds and the full close (Archive/Register/Fault bumps with mechanical
proofs, manifest, A8 pin list, A9 Notion, F-107 filing, project-knowledge swap). **Owner residual:
one `PUBLISH_ALL.bat` double-click, then on the box copy `live_pins_S199close.txt` →
`/root/deploy/live_pins.txt` and run `verify_live_pins.py` — expect GREEN; the old list would show
RED drift on the four moved/new files the box has right (the F-134 stale-list condition, not a
fault).**

---

*HANDOFF_RUNBOOK v133 · Session 199 close · supersedes v132. If §0, §2 or this end-marker is
absent, this file is truncated and must not be used as canonical.*
