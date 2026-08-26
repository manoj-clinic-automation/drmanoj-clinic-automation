# S203_MARG_CANON — a second store for the Marg / medical documents

**Made:** 26-Aug-2026, Session 203.
**Made by:** a preservation pass, copying documents OUT of the claude.ai Project knowledge and INTO
this repository. Nothing was deleted, moved or edited anywhere. No `git` command was run (F-131).

---

## What this folder is

Every document in this folder concerns **Marg, the pharmacy feed, or the MEDICAL PC**, and **existed
in exactly one store — the claude.ai Project — with no copy in this repository and none in the cold
kit.**

The S203 census (`S203_KB_CENSUS_PHASE12.md`, also copied here) established that **76 project
documents live in one store only**, and `S203_MARG_DOC_INVENTORY.md` (also here) identified **30 of
them as Marg/medical**. This folder is those documents, plus the current Marg reference set and the
S203 working documents, filed together so that **every one of them is recoverable from two
independent places instead of one.**

## Why it exists

This project has lost documents before, permanently:

- **F-89** — a nine-session backup lapse **permanently lost three canonical documents**.
- **The S131 stumps** — two more documents survived only because a cold backup had them; git and
  Drive did not.

The governing rule adopted at S203 is that **nothing is retired from project knowledge until it is
provably recoverable from TWO independent stores, by hash.** Before this folder existed, that rule
could not be satisfied for any Marg/medical document: there was one store.

**This folder is the safety net that makes the S203 KB consolidation safe to attempt.**

## What is in it

- The **current Marg reference set** — `MARG_PIPELINE_REFERENCE_v1`,
  `MARG_PIPELINE_MAINTENANCE_FLOW_v1`, `MARG_INGESTION_REFERENCE_v1`,
  `S195_Medical_Watcher_LIVE_Reference`, `Clinic_Source_Data_Retention_Policy_v1`.
- The **S203 working documents** — the inventory, the verification pass, the code truth map, the
  system map, the KB census, the pendency reconciliation, the consolidation plan, `START_HERE_SESSION_203`.
- The **S202** D350 transport contract and the pendency audit.
- The **whole S201 family** — the rebuild plan, the outbox finding, Parts 0/1/2-3-4, the xlsx
  dependency record, the A1FIX pin record, the completion audit, month-vs-Marg, the parked backlog,
  what's-left-for-you.
- The **S195 family** — the final pins, the close summary, the dbf-encryption finding, the email/guard
  build state, and `S195_medical_kit/` (six files: `SETUP_CHECK.bat`, `GUARD_AND_SEND.bat`,
  `marg_export_macro_v2.ahk`, `SETUP_S195_MARG.md`, `marg_report.py`, `guard_and_send.py`).
- The **S180 family** — the folder recon (the whole Marg data-layer analysis), the feasibility survey,
  the sample findings, the transport design, the feed request and flow, the daily-sale button
  settings, the action register.
- The **S179/S183 medical documents** — the Marg sale report analysis, the B1 medical reconciliation,
  the Sanjeevni medical module build contract v1, the S183 daily-cash design and Marg findings.
- `AUDIT_RUN_2026-08-24_slice1.md` (the Auditor's only run report, AF-1…AF-6 in full) and
  `AUDITOR_SEED_v1.md`.
- `OWNER_TODO_LIVE.md` — un-manifested by design in the project; a point-in-time copy is kept here.

## Provenance and how to check it

`SUMS.md5` lists every file in this folder with its md5. Verify with:

```
md5sum -c SUMS.md5
```

It must exit 0. **A filename is not provenance (D188)** — the hash is.

Each file was read from the Project with `project_read`, written byte-identically into a container,
and copied here; every file that landed was then re-hashed on this machine and compared against the
container copy before this README was written. Any mismatch would have been reported and the file
would not be listed as preserved.

## What this folder is NOT

- **Not a replacement for the Project.** Nothing was removed from project knowledge by this pass.
- **Not manifest-pinned.** These rows are not (yet) in `CANONICAL_MANIFEST.md`. Filing and pinning is
  the owner's, at a close. Until then Phase 0 does not verify them — `SUMS.md5` here is the only check.
- **Not a decision about retirement.** It is the precondition for one.

---
*S203 · preservation pass · copy only · nothing deleted, nothing moved, no git run, no token printed,
no patient identifier reproduced.*
