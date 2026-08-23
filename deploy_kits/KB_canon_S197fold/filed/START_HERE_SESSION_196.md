# START HERE — Session 196

Hi Claude. Continuing the clinic-automation project (**Session 196**). I'm Dr. Manoj
Agarwal, orthopaedic surgeon, Bareilly. Solo practice, older Hindi-first semi-urban
patients. Working protocol unchanged (plain language; one step at a time; full-file
replacements; mask patient numbers to last-4 and all tokens; nothing live rebuilt without
my OK; build/test offline → py_compile → pyflakes → I install).

## Phase 0 — verification before work (D247)

1. Open `CANONICAL_MANIFEST.md` (Tier 0 · linchpin). Verify every row by md5.
2. **Heads-up — known canon debt (from S195):** the canonical Register / History Archive /
   manifest are folded only to **S192**. Sessions **193, 194, 195** are standalone
   `S19x_*` docs not yet folded, and `live_pins.txt` is stale against them. A manifest row
   that mismatches for those is *expected*, not an incident — see
   `S195_Close_Summary_FINAL.md` §"Canon fold-in debt". **If this session is meant to be
   the fold-in, that IS the task (EOS-light).**
3. Read Tier 0 only: this file, KB Register, HANDOFF_RUNBOOK, and the S195 close docs
   (`S195_Close_Summary_FINAL.md` is the anchor; `S195_Medical_Watcher_LIVE_Reference.md`,
   `S195_Bank_Statement_Chain.md`, `S195_Credit_Note_Sign_Fault.md` as needed).

## The live pins to trust (S195 close)

- finance_app.py `df75024392e31ae99bb3fde9fab24062` (smoke 654)
- portal.py `ff08980737c107c3babb78b0c5c169c2`
- email_agent.py `e535c4f8116abd2fe60b7fda334f33ec`
- Marg `margpull/signatures.json` `1b21f3bf582d9f19fb8959a5336b0ba0` (5 types)

## This session's priorities (owner-set at S195 close)

1. **Attendance / salary part** — owner flagged as important; **start here.** (Scope to be
   given by owner at session open — attendance system + staff-ledger/salary interplay.)
2. **Portal health tile — renewals line** (Task #8): personal GAS pushes the
   within-N-days renewals list to a VPS endpoint (VPS_Push_UPI token pattern) → the
   `/finance/health` page shows "N renewals inside 30 days · nearest: …". Kit-sized.
3. **Auditor** — start it in its OWN background chat from `AUDITOR_SEED_v1.md`; slice 1
   (cash trail) is the calibration run. Triage findings to owner; weekly unattended after.

## Carry-overs (owner actions + smaller builds)

- **Token rotation** — `FINANCE_MARG_TOKEN` + `FINANCE_CRON_TOKEN` (cron also in GAS
  Script Properties of "UPI Reconciliation"). Exposed in chat during the 401 crisis.
  **Highest-severity open item.** Owner action.
- **17-Aug ₹20,000 → Staff Ledger** — only against a **written, scanned application from
  Darpan** (owner ruling). Drawer reads ₹175,201 only after. Owner action + scan.
- **Medical delivery** — owner will install **Google Drive for Desktop** on the medical PC;
  then wire a local copy `Drive ToMedical → D:\SendToClinic\FROM_CLINIC` (the puller build
  is dropped in favour of this). Until then, Amir's Sanjeevni statements sit in Drive.
- **Labmate** router signature — one sample from the lab PC (last Club-3 type).
- **`portal.py`** — render the `accuracy` block on Darpan's tile (API already returns it).
- **PUBLISH reminder** — repo is current as of S195 (margpull/ published). Nothing pending.

## Next-free numbers

Decisions: continue the D-series (last used ~D330s range — confirm from Register before
assigning). Faults: continue F-series (last ~F-134 — confirm from Fault_Action_Register).

## Connected sources

Google Drive (`drmka.ortho`), Gmail, Notion (Clinic HQ), GitHub
(`drmanoj-clinic-automation`), plus the manojz/medical device bridge (Tailscale). ClickUp
parked (D17).

*START_HERE_SESSION_196 — generated at S195 close, 23-Aug-2026.*
