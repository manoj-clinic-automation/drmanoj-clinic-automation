# Dr. Manoj Agarwal Clinic — Automation Handoff Runbook v12
**Session 14 close · 28 Jun 2026 (IST) · for Session 15**

Read in this order:
1. **`docs/Clinic_Master_KB_SystemsRegister_v1.2.md`** — canonical Systems Register. **This file wins.** New this session: **§14** (patient lookup + revenue reconciliation + verified corrections).
2. **`Dr_Manoj_Clinic_Umbrella_Architecture_v1.2_28Jun2026.md`** — the "why/shape" (now incl. decision **D11** = revenue reconciliation strategy).
3. This runbook (state + how-to-work).
4. `START_HERE_PROMPT.md` — paste at the top of the next chat.
Older runbooks/docs are in `prev_runbooks/`.

---

## 0. HOW TO WORK WITH THE DOCTOR (strict — do not drift)
- **Plain language.** No assumed coding knowledge. Terminal = "black window".
- **Full-file replacements**, never diffs/partial edits.
- **One step at a time**, wait for confirmation before the next.
- **ALL-CAPS from the doctor = urgent.**
- **Never print real tokens, secrets, or patient phone numbers** — always mask. **The uploaded stack contains real PHI + a service-account JSON — never print patient rows; headers/shapes/sums only.**
- **Never rebuild live components.** Manual workflow always stays as fallback.
- **Large files: deliver as downloads** (present_files).
- **VPS terminal MANGLES large pastes** ⇒ install via **WinSCP → md5 verify → py_compile → restart**. `\cp -f` to overwrite.
- **Apps Script deploys:** keep the URL stable — **edit the existing deployment → New version**. NEVER new deployment.
- **VET before you build.** This session repeatedly avoided building the wrong thing by reading the real files first. Keep doing that.
- **Terminology:** the people we serve are **patients**, never "leads."

## 1. WHAT THIS PROJECT IS
Clinic automation for an orthopaedic surgeon (Bareilly; older, Hindi-first, semi-urban). Stack: **MyOperator IVR + WhatsApp Business API** + **Google Apps Script dashboard** + **Hostinger VPS (Flask relays)** + **Google Sheets** spine. EMR (**Docterz**) is closed — CSV export only. Modules talk through DATA (the Sheet); one join key (**Clinic ID**); one writer per table; degrade-to-fallback.

## 2. WHERE WE ARE (one line)
Dashboard **v17.1 LIVE**. Session 14 was a deep **vetting + planning** session: spec'd the phone 360° lookup (server fn built, card UI pending) and fully mapped the **revenue reconciliation** problem (the next real build).

## 3. WHAT HAPPENED THIS SESSION (Session 14) — mostly discovery, two artifacts
- **Verified corrections (now in KB §14a):** AKEY_11–16 are **LIVE** (accountability on); the dashboard Apps Script is **multi-file** and the **repo `dashboard/` folder is incomplete** (missing `MyOperator.gs` + the CFG file — export them next commit); `Patient_Master` columns confirmed; `Clinic_Specific_Id` is the clean 4-digit key (100% filled).
- **ARTIFACT 1 — `lookupPatient360` built** into `dashboard/WebApp.gs` (new md5 `312de4b3…`; first 1411 lines byte-identical to live `42b8762d…`; `node --check` clean). Phone-first, read-only, 3 search modes, freshness-stamped, tier-aware. **NOT deployed** (needs the `Dashboard.html` card UI first).
- **ARTIFACT 2 — revenue reconciler SPEC locked (KB §14c/d, Umbrella D11).** The tracker's **`/finance*` views already exist** (trapped on C: drive). Real external revenue files examined: **Marg 20-Jun** (Clinic-ID-suffix feature, 80% mobile / 52% both) and **Labmate 1Apr-18Jun** (pre-suffix, ₹3,50,130, needs name+date fuzzy match). Two-era matching strategy agreed; **Unclassified** fallback so no rupee is dropped.
- **Migration lane M1–M6 captured** (C: drive → structured homes).
- **Living docs updated:** Master KB → **v1.2**, Umbrella → **v1.2** (D11), this runbook → **v12**.

## 4. THE TWO THINGS HALF-DONE (pick up here)
**A. Phone 360° "Who is this?" card** — server fn done; **needs the `Dashboard.html` UI** (3 search boxes: Mobile/Clinic ID/Name → stacked phone-first result card: who · last visit (+ago) · diagnosis · pending · one-tap Call; freshness stamp; revenue Doctor-only later via M6). Then paste BOTH files, deploy New version, test.

**B. `reconcile_revenue.py`** — the next real build. Spec in KB §14d. **Build fuzzy engine first** (1-Apr historical backlog), prove on the **Labmate file** (real Date+Net, ₹3.5L), then the clean Clinic-ID engine for Marg 20-Jun-on. Name normalisation: strip honorifics → token-set match. Output: one durable Source-tagged ledger + `revenue_review.csv`. Dry-run summary before writing.

## 5. LIVE COMPONENTS — DO NOT REBUILD
Dashboard (Apps Script, v17.1) · Inbound WA receiver (8095) · WhatsApp send relay (8096) · Click-to-call relay (8097) · wa-notifier · daily converter · follow-up ingest. The tracker's `/finance*` + `/lab` + `/procedure` web views (on the clinic PC) also already exist — surface, don't rebuild.

## 6. OPEN BACKLOG (pick a lane)
- **Finish A (360° card UI)** and/or **build B (revenue reconciler)** — the two natural next steps.
- Export `MyOperator.gs` + CFG file into the repo (the dashboard project is bigger than the 2 committed files).
- One-line mirror fix: push both 4-digit Clinic ID and opaque UID to `Patient_Master`.
- Make tracker `/finance` phone-reachable (migration lane).
- WA token rotation (HIGH risk, Lokesh) · self-hosted ntfy (rollout step 4) · supervisor `doctor.py` · de-id→NotebookLM · revenue MIS · HR lane · website cheap wins.

## 7. KIT MAP (what's in this zip)
- `docs/` — **Master KB v1.2** (read first) + the five staff documents (carried forward).
- `dashboard/` — `WebApp.gs` (v17.1 + `lookupPatient360`, md5 `312de4b3…`) + `Dashboard.html` (unchanged `72b19ed4…`). **NOTE: project also has `MyOperator.gs` + a CFG file not yet in the repo.**
- `revenue_reconciliation/source_samples/` — the **Marg 20-Jun** + **Labmate 1Apr-18Jun** real export files (for building the reconciler).
- `Dr_Manoj_Clinic_Umbrella_Architecture_v1.2_28Jun2026.md` — strategy (D11).
- `api/`, `obd/`, `vps_core/`, `vps_relay/`, `wa-call/`, `notifier/`, `converter/`, `token_rotation/`, `context/` — carried forward unchanged.
- `prev_runbooks/` — every earlier runbook/carryover + the v1.1 KB/Umbrella snapshots + runbook v11.
- `START_HERE_PROMPT.md` — paste into the next chat.

## 8. THE BIG C-DRIVE STACK (not in this zip — it's 144 MB with PHI)
The full clinic stack (`clinic_automation_stack_28_june_2026.zip`: follow-up tracker, ClinicSalary, IVR KB kit with recordings/transcripts, pull_recordings) lives on the owner's machine. It contains **real PHI + the service-account JSON** — keep it OFF Git. Re-upload the tracker folder when working the reconciler or migration so code is read from the live copy, not a June snapshot.

*End of runbook v12.*
