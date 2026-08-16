# START HERE — Session 180

Hi Claude. Continuing my clinic-automation project (**Session 180**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(This is the session-specific entry point regenerated at the S179 close. The evergreen procedure is
`START_HERE_PROMPT_v5` = this project's custom instructions; follow it. This file only carries the
Phase-0 pointers current as of S179 and the S180 top task.)*

**Working protocol (follow strictly):** plain language, no assumed coding knowledge · ONE step at a
time, wait for my explicit confirmation · full-file replacements, never diffs · ALL-CAPS from me =
urgent · mask patient numbers to last-4 and never print secrets/tokens · nothing live is rebuilt
without my explicit OK, manual workflow always stays as fallback · build/test offline → `py_compile`
(I use `python`) → then I install · `/root/wa` scripts use `/root/wa/venv/bin/python3`; the **asset
app and the finance app use system `/usr/bin/python3`** (F-53).

---

## Phase 0 — do this FIRST (verification before work)

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin). STATUS should read **current at S179**.
2. **Verify every row by md5** (hash-compare only, all tiers). A row whose hash does not match halts
   work until reconciled (D172/D188).
3. Read into context only **Tier 0**: the manifest, the evergreen START-HERE, the **KB Register
   v5.1**, the **HANDOFF_RUNBOOK v113**, and any open incident (none open). Open Tier 1 on demand.
4. Confirm, then start the S180 top task (or ask me which backlog item — HANDOFF_RUNBOOK §2 is the
   live backlog).

## Where the truth lives (read the manifest for hashes; don't hard-code them here)
- **`CANONICAL_MANIFEST.md`** — doc set, tiers, hashes. WINS on "what is canonical / current." (S179)
- **KB Register v5.1** (Tier 0) — authority on what is true NOW: live-file table (now incl. the
  clinic-finance subsystem), decisions index through **D313**, findings through **F-84**, lineage.
- **KB History Archive v1.27** (Tier 1) — every session narrative + full decision text, verbatim;
  §S179 is the last section. History only; opened on demand.
- **HANDOFF_RUNBOOK v113** (Tier 0) — §0 what happened last (finance live) · §2 live backlog.
- **Fault_Action_Register v2.16** (Tier 1) — F-82+F-83 append owed → v2.17; **F-84 append owed**
  (`Fault_Register_append_F84_S179.md`).
- **`S179_Finance_LIVE_State`** (Tier 1) — the SOLE live-state reference for the clinic-finance
  subsystem; companions: the build contract v2, migration analysis, B1 reconciliation, Marg analyses.

## ⭐ S180 TOP TASK — CLINIC + LAB finance modules (a replication of medical)

Medical (Sanjeevni) is live and streamlined. Clinic and lab now migrate onto the **same
`clinic-finance` app** (per-unit isolation is already in the schema; `reception`/`labstaff` makers +
`manoj`/`bhawna` checkers already seeded). Needs a forensic read of the clinic + lab tabs of the
source Sheet and their Google Forms, the reception/lab-staff logins, and the clinic decision:
**clinic reads day-revenue patient-wise from the follow-up tracker** (procedure entry only enriches
the procedure name) vs typed entry; lab mirrors medical (Labmate export primary once one real export
is mapped). All three stay separate for accounts. Manual workflow stays fallback; Forms retire per
unit only after a clean parallel run.

**Also open (owner actions / carried):** commit `gitkit_S179.zip` (**`.gitignore` the finance PHI
paths in the same commit, before `git add` — F-31/F-49**) · the 30-Jul deposit question (gates the
August cutover) · one test scan through Daily Sale · off-box backup destination · accountant-pack
name toggle · Marg-feed adapter decision · WABA go-live (F-82, vendor) · S177 asset git kit + token
rotations. Full list: HANDOFF_RUNBOOK §2.

**Connected sources:** Google Drive (`drmka.ortho@gmail.com`) · Gmail (clinic UPI mails) · Notion
("Clinic HQ") · GitHub (`drmanoj-clinic-automation`) · ClickUp parked (D17). Patient data is NOT in
this project.

**Next free: D314 · F-85 · A-D25 · Session 180.**

*START_HERE_SESSION_180 — regenerated at the S179 close. Supersedes START_HERE_SESSION_179.*
