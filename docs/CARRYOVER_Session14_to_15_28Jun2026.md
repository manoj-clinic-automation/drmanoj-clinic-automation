# Carryover — Session 14 → Session 15 (28 Jun 2026)

**One-liner:** Deep vetting session. The phone **360° patient lookup** server function is **built** (`lookupPatient360` in `WebApp.gs`, not deployed — card UI pending). The **revenue reconciliation** problem is fully mapped, spec locked (D11). Living docs updated to Master KB v1.2 + Umbrella v1.2 + runbook v12.

## Done this session
- **Verified corrections** (KB §14a): AKEY_11–16 LIVE (accountability on); dashboard Apps Script is **multi-file** & the repo `dashboard/` folder is **incomplete** (missing `MyOperator.gs` + CFG file); `Patient_Master` columns confirmed; `Clinic_Specific_Id` = clean 4-digit key (100% filled), `Patient_UID` = opaque.
- **`lookupPatient360` built** into `WebApp.gs` (md5 `312de4b3…`; pure append — first 1411 lines byte-identical to live `42b8762d…`; node --check clean). Phone-first, read-only, 3 modes (mobile/clinicid/name), freshness-stamped, tier-aware. **NOT deployed.**
- **Revenue reality mapped** (KB §14c): tracker's `/finance*`, `/lab`, `/procedure` web views ALREADY EXIST (trapped on C: drive). Consultation/X-ray/Procedure live; Lab manual+empty; **Marg = corroboration only, NOT revenue yet**; 20-Jun Clinic-ID-suffix feature confirmed; Labmate 1Apr-18Jun = ₹3,50,130 invisible to /finance.
- **Reconciler spec locked** (KB §14d, D11): two-era matching, name+date fuzzy for the historical backlog, **Unclassified** fallback (no rupee dropped), per-patient review list for doubtful.
- **Migration lane M1–M6** captured.

## Decisions locked
- **D11:** revenue reconciliation — map maximum CORRECT revenue from 1 April; never drop a rupee; doubtful → review; unmatchable → Unclassified; two eras (Clinic-ID-suffix clean vs pre-suffix fuzzy); the /finance views already exist (goal = phone-reachability, not rebuild).

## Top of the backlog (pick a lane)
**A.** Finish the 360° card UI in `Dashboard.html` (server half done) → deploy + test.
**B.** Build `reconcile_revenue.py` (fuzzy engine first, prove on Labmate ₹3.5L).
Then: export MyOperator.gs+CFG to repo · one-line mirror fix · /finance phone-reachable · WA token rotation (Lokesh) · self-hosted ntfy · doctor.py · de-id→NotebookLM.

## Watch-outs
- Repo `dashboard/` is incomplete — don't assume 2 files = whole project.
- Reconciler must never force-assign revenue to the wrong patient — ambiguous → review/Unclassified.
- Re-upload the live tracker folder when working B/migration (June snapshot may be stale).
