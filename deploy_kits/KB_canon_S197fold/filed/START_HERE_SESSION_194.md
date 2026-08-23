# START HERE — SESSION 194 (Dr Manoj clinic automation)

Continuing the clinic-automation project. I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced
Orthopaedic Surgery Centre / Sanjeevni Medicos, Bareilly. Solo practice, older Hindi-first
semi-urban patients. Working protocol unchanged (plain language; ONE step at a time, wait for my
OK; full-file replacements or fail-loud in-place patches; mask patient numbers to last-4 and never
print secrets; nothing live rebuilt without my OK; manual workflow stays as fallback; build/test
offline → `py_compile` → I install; VPS python `/root/wa/venv/bin/python3` for the ledger).

## Phase 0 — verification before work (do FIRST)
1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · linchpin) and **verify every row by md5** (hash-compare, all tiers). A mismatched row halts work until reconciled (D172/D188). **NOTE:** the S193 close did not finish the manifest/Register/Archive md5 fold (they are too large to rewrite in-session) — the authoritative S193 state is in `HANDOFF_RUNBOOK …Session193close_v129`, `S193_Close_Summary_and_Pins.md`, and this file. Reconcile the canon fold as an early task if the owner wants the manifest clean.
2. Read into context Tier 0 only: the manifest, this START_HERE, the **KB Register**, the
   **HANDOFF_RUNBOOK v129**, `S193_Close_Summary_and_Pins.md`, and any open incident. Open Tier 1
   on demand.
3. Confirm the FINAL LIVE PINS (from `S193_Close_Summary_and_Pins.md`):
   - `finance_app.py` `4c0a2d19734e3860ed3d172191b2e7ff`
   - `finance_approvals.html` `8ce3fabd3f712d99456d60ddbf6f4e1c`
   - `marg_report.py` `6411a57d4517e0a06a02e1045b354138`
   - `finance_ingest.py` `a4e9663f9be1c138293d6dd8311577d0`
   - `staff_ledger.py` `acd7b538ec9476f86e243c73eec3d3fd`
4. Then confirm, and ask which backlog item to start (HANDOFF_RUNBOOK §2 = the live backlog).

## Next-free numbers
**D334 · F-160 · A-D25 · Session 194.**

## The backlog (HANDOFF_RUNBOOK v129 §2 is authoritative)
1. **Daily Sale v2 page** — build the APPROVED prototype at a NEW route; current `/finance/entry`
   stays as fallback. Flow + live `POST /finance/api/day` contract in
   `S193_Daily_Page_v2_and_Backlog.md`.
2. **Home-medicine bills** from Marg (need: how they're marked in Marg).
3. **Cash/UPI reclassification tracker** (`mode_change_log` in `ingest_day`).
4. **Record Bhawna/Manoj hand-overs** as `cash_movement`s (owner starting soon → reserve goes live).
5. **Ping-pong email query agent** (need: owner Gmail app password).
Carried: ⭐0 signed-application scan vs advance `0cc0b26b38c5` (clock — before the August close);
July salary close; the August month-end first run on the new machinery.

## Connected sources
Google Drive (`drmka.ortho@gmail.com`) · Gmail · Notion (Clinic HQ) · GitHub
(`drmanoj-clinic-automation`, read) · ClickUp parked (D17).

## Delivery mechanism (works)
Build offline → kit tarball → SendUserFile → `device_commit_files` to
`D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\` → `device_bash` extract (trash to REPO
ROOT `_to_delete/`, gitignored) → owner PUBLISH_ALL.bat → box `git pull` → run installer.
Installers: currency-gate (against the FILE on disk, not a rendered snapshot), measured ZERO-delta
smoke, rollback on red.

---
*START_HERE_SESSION_194 · regenerated at the S193 close · evergreen protocol lives in the project
custom instructions (START_HERE_PROMPT v5).*
