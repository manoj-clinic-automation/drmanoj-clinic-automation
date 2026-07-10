START-HERE — SESSION 134

Hi Claude. Continuing my clinic-automation project (Session 134).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

Working protocol as in `START_HERE_PROMPT_v4.md`. One step at a time. Full-file replacements
only. Plain language. Mask all secrets — every command, not most of them. Minimum manual
commands; script the guards.

════════════════════════════════════════════════════════════════════════════════
SESSION 133 SHIPPED FOUR THINGS AND BROKE NOTHING. THE PATTERN THAT WORKED: GUARDED
SCRIPTS THE OWNER BARELY TYPES INTO, AND EVERY RESULT VERIFIED FROM THE ARTEFACT.
════════════════════════════════════════════════════════════════════════════════

**D194 is LIVE** — the `Do_Not_Call` tab suppresses; proven on a real patient (122→121→122).
**Repo commit `84831b0`** closed F-17, F-27, F-30, F-31, verified from the GitHub tarball by hash.
**`wa_approve` is a systemd service** (gunicorn 8101) — the last bare nohup is gone.
**A-7's screenshot raised F-32 and F-33.**

> A grep, a path, and a filename all feel like evidence. None of them is an artefact.
> Read the file. Then say what it contains.

────────────────────────────────────────────────────────────────────────────────
PHASE 0 — VERIFY. Assert the md5, never the filename (D188, D201).
────────────────────────────────────────────────────────────────────────────────

| File | Bytes | Lines | md5 |
|---|---|---|---|
| `Clinic_Master_KB_SystemsRegister_v1_59.md` | 304,272 | 3,082 | `ff4e917a5126a25ac0eac29ec5bb51e6` |
| `HANDOFF_RUNBOOK_2026-07-11_Session133_v71.md` | 14,163 | 213 | `1e8b749a44be048a699cfdade2b43561` |
| `Dr_Manoj_Clinic_Umbrella_Architecture_v1_45.md` | 68,966 | 744 | `01895d8d1690f3f3b79f17ad894cea2c` |
| `Clinic_Callback_Tracker_AppsScript_Audit_v1_4.md` | 31,542 | 331 | `7131df6075a65ea03459f39d1b087e08` |
| `Fault_Action_Register_v2_1.md` | 19,797 | 289 | `fde74c496a00826b504dc77b0c0c6cf6` |
| `Diagnostics_Surveillance_System_Spec_v2_1.md` | 53,441 | 871 | `7a9e83b436c39fde08118437acbbfafe` |
| `Call_Console_Evolution_Spec_v2_0.md` | 55,148 | 737 | `81e73349bb1318bea2df4cadaaeb6c47` |
| `AI_Review_Layer_Design_Spec_v1_1_S131.md` | 28,249 | 505 | `ad45a3af65188ed41391dca36175ce91` |
| `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` | 42,301 | 503 | `dc8d134fa8011aa3707d112f906342e6` |

**Assert the ABSENCES** — gone from project knowledge: `..._v1_58.md` · `..._v70.md` · `..._v1_44.md`
· `START_HERE_SESSION_133.md`.

**The Apps Script export is CURRENT:** `Clinic_Callback_Tracker__4_.json`
`523ddcbecc34cfe2c9a7ed6c7b3179ed`, 15 files, `WebApp` `5173c3c7…`, `Dashboard` `a442bab5…` (v18.20).
**Build this session's Dashboard/Main/Health edits from THIS export.**

**Then assert the structure:** end-marker last non-blank line of all nine · CR 0 in every `.md`
· no document calls itself a delta (D202) · secret scan: no `/exec` id, no published-CSV url, no token.

**Live-artefact spot checks if touched:** PC `push_followups_today.py` = `7693a29a…` ·
repo `dashboard/WebApp.gs` = `5173c3c7…` · VPS `wa-approve` service active (do NOT ask the owner to
run anything for this — `Health.gs`'s 09:00 email arriving green is the check).

────────────────────────────────────────────────────────────────────────────────
PHASE 1 — READ, IN THIS ORDER
────────────────────────────────────────────────────────────────────────────────

1. `Clinic_Master_KB_SystemsRegister_v1_59.md` — canonical; WINS on any conflict.
   **Read §S133 in full (.0 through .7).** Next free decision: **D206.** Next free finding: **F-34.**
   ⚠️ The decisions index has never carried D1–D120 (**F-22**); nineteen are restored. A missing
   sub-D121 decision is missing from the KB, not from history. Say so; do not re-derive it.

2. `HANDOFF_RUNBOOK_..._v71.md` — §0 what happened, §2 the backlog, §3 the document state.

3. `Fault_Action_Register_v2_1.md` — §0.35 and §0.4 before trusting any "System does" cell.

4. `Call_Console_Evolution_Spec_v2_0.md` — the ONLY definition of D62, D66, D68, D69, D77, D78, D80,
   D81, D82, D97, D98.

5. `Clinic_Callback_Tracker_AppsScript_Audit_v1_4.md` — F-11's text before building A-4; F-2's sixteen
   catches are A-6.

6. `Frontend_Dashboard_Documentation_v1_S130.md` — **one version behind** (pre-Fix-B). v2 owed.

────────────────────────────────────────────────────────────────────────────────
PARKED BY OWNER — do not raise; the owner re-opens
────────────────────────────────────────────────────────────────────────────────

**The AI review layer sleeps (S133 directive):** A-00 (D78 vs D195) · A-0 (call script + closing
definition) · A-1 (the D34 question) · F-18 (`verdict_review.py`) · all Block A″ · the 32 referee
cards. **Rotation: PARKED** — no status check at open. **Health check: zero commands** — the 09:00
email's absence is the fault.

────────────────────────────────────────────────────────────────────────────────
THEN BUILD — ONE APPS SCRIPT PASS, from export `523ddcbe…`. No D34 waiver needed.
────────────────────────────────────────────────────────────────────────────────

1. **F-33 first (read-only):** the executions log for `runMorningReport`'s 14.29% error — classify
   before anything is edited.
2. **F-32 + A-5 together:** dedupe the 15 triggers (`runIntradayDigest` ≈8×, `runSummaryEmail` 3×) and
   close `removeTriggers` (`Main.gs`) + `removeHealthTrigger` (`Health.gs`). Same instrument; one
   deploy. Take a fresh Triggers screenshot after.
3. **A-3 remainder:** the L1128 `openThread` catch in `Dashboard.html`.
4. **F-11 / A-4:** sign-out button; strip `?k=` after reading; clear `clinicDashKey`. Client-side only.
   (Owner's parked interim step: clear `script.google.com` from shared-device browser history.)
5. **A-6 (analysis only, D180):** classify F-2's sixteen server `catch (e) {}` individually.
6. **Deploy discipline:** existing deployment → New version; feature-check, not build-stamp; fresh
   export after; Frontend Doc v2 from that export.

**Git, small:** commit `wa-approve.service` into `wa-approve/` · canonical docs v1.59/v71/v1.45.

**Design (session-start, half-session, when owner chooses):** D205 — the seen-today WABA section
(source = the **owner's** daily Docterz CSV; template + opt-out + dedupe + TEST wiring).

**Not yet:** Block C (make it cheap) precedes Block D (D185). Phase 2 auto-bounce stays shut.

────────────────────────────────────────────────────────────────────────────────
STANDING RULES
────────────────────────────────────────────────────────────────────────────────

The judge proposes. The doctor disposes. The staff act. **A false bounce costs one phone call. A false
settle is invisible.** A decision lives in the KB index, or it does not live (D202). No canonical
document may be a delta (D202). Detection and response are separate documents (D203). **No
auto-responder exists (D204).** Patient-facing WABA features are designed at session start (D205).
The record is a manifest **and** a disk (D201) — the assistant's file mirror is a snapshot; the search
index is live. A filename is not provenance (D188). A repo path is not a disk path. A check must be
calibrated to its artefact (D177). Expected values come from the artefact, never memory (D172). A count
without its scope is a wall (D179). A check that cannot fail is not a check. `UNKNOWN` is valid (D166).
**An audit finds; it does not fix (D180).** Never write a command whose output is a secret (D176) —
read a mixed file by **targeted grep for the non-secret lines**, never `cat`. The `Call_Feed` publish
URL and the live `/exec` URL are not for chat, docs, or screenshots. **The `Do_Not_Call` tab is the
only suppression point; humans write it, code reads it, and code never creates it.**

**MyOperator / D120 — cleared 10 Jul; watch for recurrence.** Ticket 653584 open; the unexplained
recovery window is the question to press.

────────────────────────────────────────────────────────────────────────────────

Connected sources: Google Drive (`drmka.ortho@gmail.com`) · Gmail · Notion (Clinic HQ) ·
GitHub (`drmanoj-clinic-automation`). ClickUp is parked (D17). Patient data is NOT in this project.

**D194 is live. The repo is honest. The last nohup is dead. Fifteen triggers await a dedupe, and one
of them errors at 14.29%.**

Next free decision number: **D206.** Next free finding number: **F-34.**
