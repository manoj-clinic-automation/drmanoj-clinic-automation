# START HERE — Session 181

Hi Claude. Continuing my clinic-automation project (**Session 181**).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

*(This is the session-specific entry point regenerated at the S180 close. The evergreen procedure is
`START_HERE_PROMPT_v5` = this project's custom instructions; follow it. This file only carries the
Phase-0 pointers current as of S180 and the S181 top task.)*

**Working protocol (follow strictly):** plain language, no assumed coding knowledge · ONE step at a
time, wait for my explicit confirmation · full-file replacements, never diffs · ALL-CAPS from me =
urgent · mask patient numbers to last-4 and never print secrets/tokens · nothing live is rebuilt
without my explicit OK, manual workflow always stays as fallback · build/test offline → `py_compile`
(I use `python`) → then I install · `/root/wa` scripts use `/root/wa/venv/bin/python3`; the **asset
app and the finance app use system `/usr/bin/python3`** (F-53).

---

## Phase 0 — do this FIRST (verification before work)

1. Open **`CANONICAL_MANIFEST.md`** (Tier 0 · the linchpin). STATUS should read **current at S180**.
2. **Verify every row by md5** (hash-compare only, all tiers). A row whose hash does not match halts
   work until reconciled (D172/D188).
3. Read into context only **Tier 0**: the manifest, the evergreen START-HERE, the **KB Register
   v5.2**, the **HANDOFF_RUNBOOK v114**, and any open incident (none open). Open Tier 1 on demand.
4. Confirm, then ask me which backlog item to start (HANDOFF_RUNBOOK §2 is the live backlog).

> **⚠ THREE ROWS ARE CLOSED AS LOST — this is NOT drift, and must NOT halt Phase 0 (D316).**
> Seven rows were unreachable at the S180 Phase 0. A hash-based search of my drives recovered four
> and established that three are gone:
>
> | Row | Status |
> |---|---|
> | `KB_Register` v5.0 (S178) | **LOST-SUPERSEDED** — v5.1 verified present; nothing depends on it; no action |
> | `KB_History_Archive` v1.26 (S178) | **LOST-SUPERSEDED** — v1.27 verified present; no action |
> | `KB_Asset_Register` v1.11.0 | **LOST-RECONSTRUCTABLE** — Tier-1 CURRENT. Rebuild from the recovered v1.10.3 + Archive §S173–§S177. Backlog item, not a blocker |
>
> The manifest lists them as closed with their pinned md5 kept for provenance. **A closed row is not
> drift.** Only a row listed as *present* that fails its hash halts work.
>
> **Recovered and back in the set:** `Fault_Action_Register` v2.16 · `Staff_Daily_Register_Dossier`
> v1.1 · `KB_Asset_Register` v1.10.3 · `KB_Register` v4.6.

## Where the truth lives (read the manifest for hashes; don't hard-code them here)
- **`CANONICAL_MANIFEST.md`** — doc set, tiers, hashes. WINS on "what is canonical / current." (S180)
- **KB Register v5.2** (Tier 0) — what is true NOW: live-file table (six finance entries changed or
  added at S180), decisions through **D316**, findings through **F-89**, lineage.
- **KB History Archive v1.28** (Tier 1) — every session narrative verbatim; §S180 is the last
  section (pure append, prefix byte-identical to the v1.27 pin, +25,910 chars).
- **HANDOFF_RUNBOOK v114** (Tier 0) — §0 what happened · §1 mental models · §2 live backlog.
- **`S179_Finance_LIVE_State`** (Tier 1) — the finance subsystem's live-state reference. **Its md5s
  are now partly stale; the KB Register's live-file table wins.**
- **S180 companions** (project knowledge, `claude/`): `S180_Marg_Feed_Request_and_Flow` ·
  `S180_Marg_Action_Register` · `S180_Marg_Sample_Findings` · `S180_Marg_Feed_Feasibility` ·
  `Marg_Report_Requirement_Sanjeevni` (the vendor-facing document).

## ⭐ S181 TOP TASK — my choice between two, ask me which

**(a) CLINIC + LAB finance modules** — the starred S180 task, still not started. A replication of
medical onto the same `clinic-finance` app; per-unit isolation already in the schema;
`reception`/`labstaff` makers and `manoj`/`bhawna` checkers already seeded. Needs a forensic read of
the clinic + lab tabs of the source Sheet and their Forms, and the clinic decision: **day-revenue
patient-wise from the follow-up tracker** (procedure entry only enriching the procedure name) vs
typed entry. Lab mirrors medical once one real Labmate export is mapped.

**(b) FINISH THE MARG CHAIN** — U5 reception return page · U7 discount deduction at return
(**medium, not small: the discount is not stored anywhere yet**) · U8 Darpan's checker page ·
U9 flag engine · U12 transport.

**Housekeeping now unblocked (was blocked on the missing Fault Register):**
apply the **three owed Fault Register appends → v2.17** (F-82+F-83, F-84, F-85–F-89 — the register
is back and hash-verified) · **rebuild `KB_Asset_Register` v1.11.0** (D316) · ⭐ **take a cold kit
within 3–5 sessions and check the count at every close (F-89)** — nine sessions without one is what
lost three documents.

**Also open (mine to do):** send the vendor requirement to Marg · one export from **each** button,
checked before they are saved · ⭐ **one complete Button A export 01-Aug→date passing its GRAND TOTAL
check — this gates the August cutover** · is `ABL` a credit account · set the flag thresholds · the
return-reason vocabulary · **see the missing-day alarm fire** before trusting an unattended sweep ·
bill `A002783` (99.5% written off) · WABA go-live (F-82, vendor). *(Git kits were committed at the S180 close.)* Full list: HANDOFF_RUNBOOK §2.

**Connected sources:** Google Drive (`drmka.ortho@gmail.com`) · Gmail (clinic UPI mails) · Notion
("Clinic HQ") · GitHub (`drmanoj-clinic-automation`) · ClickUp parked (D17). Patient data is NOT in
this project.

**Next free: D317 · F-90 · A-D25 · Session 181.**

*START_HERE_SESSION_181 — regenerated at the S180 close. Supersedes START_HERE_SESSION_180.*
