# HANDOFF RUNBOOK — 09 July 2026 — Session 131 — v68
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: EOS-LIGHT — no live code touched. No Apps Script deploy, no VPS file, no `.env`, no trigger, no property, no GitHub commit. Supersedes v65 and v66.**

> **v68 — the document set was mended.** Three delta chains retired into self-contained masters, each asserted line-by-line to lose nothing: **Call Console Spec v2.0**, **Diagnostics Spec v2.0**, **Incident 403 v5**. **Four of six Call-Console files and three of seven Diagnostics files were in neither git nor Drive** — all recovered from the owner's cold-backup zips. **F-22:** this KB has never carried D1–D120; **D68, D78, D80, D81 have zero mentions in it**, and it *amends* D77/D82 without ever stating them. **Eleven decisions restored** (KB §S131.13). **F-19 WITHDRAWN.** **F-21, F-23** raised. **D202** minted. **D153/D157** now carry overturn markers.
>
> **v67 corrected v66.** §0.2 of v66 called F-8's blast radius *"wider than the audit's headline."* **It was not.** Audit v1.2 stated it in Session 129, in its own title and body. v66 restated an existing finding as an extension of it. **The fact stands; the lineage was wrong.** Corrected below; recorded in Audit v1.3's F-8 lineage note and KB §S131.11. Audit re-based to **v1.3** in the same pass.

---

## §0 — WHAT HAPPENED THIS SESSION

The session was told, at the outset, that nothing would be built: *"first we finalise the changes as much as possible, document them, and after that only we execute the code change."* That instruction was followed exactly. **The product of this session is a finished design and eleven decisions.**

### 1. The export was verified, and an absence claim was found wrong
The Apps Script export arrived as `4.json` — a filename carrying no information (D188). Asserted by hash: **465,074 bytes, md5 `449f3fe6981c2b75dfac0437126ece59`, 15 files.** `WebApp.gs` 1,647 lines / md5 `5173c3c7…`; `function setDashboardKey(` = **0**; `function setStaffKey(` = **0** — counted by definition, not substring. `Dashboard.html` `034529a1…` / 2,738 lines. CR = 0 throughout. **F-9 is closed in the artefact, not merely in the record.**

Before it arrived, the assistant reported the export **absent** from project knowledge, on the strength of a directory listing. The listing was true of the disk. **The file manifest in the assistant's own opening context already named `4.json`.** The absence claim was made from one disk while the record described another. → **D201.**

### 2. F-8, anatomised
`esc()` (L685) escapes `& < > "` but not `'`. `jsq()` (L729) escapes `\ '` but not `"`. **F-10's two blind escapers.** L912 pushes `JSON.stringify` output (always double-quoted) through `jsq`; L923 pastes it into a `"`-delimited `onclick`; the attribute closes at the first `"` and **the handler is never installed.** The button renders and does nothing, silently, with no error at click time.

**The blast radius — established by Audit v1.2 in S129, not by this session:** the breaking condition is `e.patient` being truthy — **any `Patient_Master` match**, including a bare UID with no name. `known` is a strictly narrower set. *S131 re-derived it from the artefact and mistook its own re-derivation for a new finding.*

**Fix A** = one line, `esc(jsq(…))`. **Fix B (recommended)** = six lines: hold the packet in a page-level map keyed by slot id, pass only the id. Fix B also kills the **L1260 `catch(e){}`** (A-3's first item — no `JSON.parse` left to fail) and delivers **Block E's** *stop embedding patient data in button markup*. `Dashboard.html` only. **No server file, no D34 question.**

### 3. Two tile mechanisms, and a line nobody ever wrote
An incoming tile leaves at **WebApp L247** on `Callbacks_Today.Staff Status`. **Every `setValue`/`setValues` in all fifteen files was searched: nothing in this project has ever written that column.** `Sheets.gs` preserves it by design (`STAFF_COL_COUNT: 2`) and writes only `Auto-Status`.

**The only thing that has ever cleared an incoming tile is a human typing a word into the Google Sheet by hand.** A repaired button would not have cleared it either.

And **WebApp L1252–55 already computes `settle`/`escalate`/`retry` for incoming calls**, already writes it to `Followup_Outcomes`, and the client at **L1382** already renders *"saved — stays for callback"*. **The machine is built. Nobody consumes its output.**

### 4. The doctor→staff return loop has been live since Session 52
`sendBackToStaff` (**L1502**) writes `SENT_BACK` + the doctor's note into `Followup_Escalations`. `getFollowups` (**L938**) reads it back and rebuilds it as a staff tile in a section named **"Sent back by doctor"**, and **auto-clears** when staff file a newer outcome. `getEscalations` (**L1387–1401**) already attaches recording + transcript per row.

**The owner's proposal — AI verdict lands on his dashboard, he verifies, he sends the tile back — is a second row source into an existing loop. Not a new mechanism.**

### 5. The AI review layer — designed and locked (D191–D201)
> **The judge proposes. The doctor disposes. The staff act.**

- **Axis 1 CONTACT** (new): 18 codes, five groups. **Group A is metadata-derived and costs no AI** — a no-answer produces no recording, so the judge never sees it.
- **Axis 2 OUTCOME**: unchanged, and **meaningful only under `spoke_patient` / `spoke_family_proxy`**. Today a staff member can file `coming` on a voicemail and nothing objects. That is the invisible failure this layer closes.
- **Axis 3 CONDUCT**: **no composite score.** Six binary checks, split objective (auto-recorded) vs interpretive (doctor confirms before it becomes record). Per-flag exclusions. Doctor-only. Coach by recording, not by number. **Play, don't export.**
- **Two-phase gate:** Phase 1 — **no machine-initiated tile movement of any kind.** Phase 2 unlocks auto-bounce for Groups A+B only, at **100 refereed cards · ≥95% agreement · zero false-settles in the last 50.** *A false bounce costs one phone call; a false settle is invisible.*
- **`Do_Not_Call` tab** is the single enforcement point for `number_invalid`, `patient_deceased`, `asked_not_to_call` — because the dashboard performs **zero writes** on `PATIENT_SHEET_ID` and `Followups_Today` is **read-only** to it.
- Dashboard becomes **sole writer of `Doctor_Verdicts`** (D193). New property **`AUDIT_SHEET_ID`**. **Three** spreadsheets now.

### 6. The recording lag was never unknown (D200)
`recording_filename` arrives in the **`call.end` webhook** (API Ref §9.1) and `call_hook_capture.py` **already writes it to `Call_Durations` in real time** (HEADER L183–186, extract L408). Recordings persist on MyOperator indefinitely; only the *link* expires (24 h). **The 02:00 / 03:00 batch clocks are a choice, not a constraint.** A fetch-with-backoff makes the file-availability delay irrelevant to correctness. **The assistant asked for a measurement the artefacts had already made.**

### 7. Four findings raised, none fixed (D180)
- **F-17** — the public repo's `dashboard/WebApp.gs` is the **pre-fix** file (`276dc197…`), both setters still defined, wearing the live file's name. The deployed code sits beside it as `WebApp_v19_D189.gs`. Not exploitable; **but the next reader of that filename gets the vulnerable source.**
- **F-18** — `verdict_review.py` prints overturned **D153** as a design justification (*"Incoming calls, no claim — Correct by design"*) and excused **19 incoming calls** from scrutiny.
- **F-19 — WITHDRAWN (S131).** `call_hook_capture.py` **L385** is **not a defect.** Call Console Spec v2.0 **§G.1**, describing the receiver as built in Session 54 under **D80**: *"Skips incoming / non-OBD calls."* Deliberate, documented. **Reclassified as a scope change against D80** — the boundary must move, because the AI review layer needs incoming recordings. Not a bug to fix; a decision to take. **Block D still depends on it.**
- **F-20** — `asked_not_to_call` is a live outcome code with **no enforcement anywhere**. Closed by D194 alongside the deceased gap.

### 8. Process notes, recorded honestly
- The KB build's own post-edit probe fired on `D201 —` twice — the second match was the **§S131.7 heading**. **A count without its scope is a wall (D179) — broken again, in the very check written to catch a bad paste, and caught again.** The instrument was tightened, not the file.
- **The session's own F-8 lineage claim was wrong, and the owner's question caught it.** Asked whether three callback-tracker documents needed consolidating, the assistant read them properly for the first time and found that **Audit v1.2 had already stated F-8's blast radius** — the thing v66 and Spec v1.0 called a widening of it. **D190 and D201 were written in this session and violated in it**, against the very document that taught the lesson. *An artefact is read before it is characterised — including an artefact that is only a document.*
- **`F9_Decision_Sheet_D189_Session130.md` leaves project knowledge.** Its decision was made, executed as version 64, and verified. A decision sheet's job ends when its decision is executed; keeping it invites a closed question to be reopened. **Archived in the cold kit** — it was missing from the first kit built this session, which was a gap in the close-out itself.
- The owner reported the Claude Windows desktop app's scrolling had broken after an update. Known open regression, not his machine; PgUp/PgDn and scrollbar drag are the workarounds. **Not a clinic-system fault. Recorded so it is not mistaken for one.**

---

## §1 — MENTAL MODELS (carried, all still true)

- **The judge proposes. The doctor disposes. The staff act.** Each clause is a writer of a different table.
- **A false bounce costs one phone call. A false settle is invisible.** Every gate in this design is asymmetric for that reason.
- **Filing an outcome ≠ clearing a tile.** Incoming tiles clear on `Callbacks_Today.Staff Status`; the outcome card writes a different tab. Two mechanisms, one gesture.
- **`Staff Status` has never been written by any code in this project.** Staff clear tiles by hand, in the spreadsheet, or not at all.
- **Three spreadsheets, not two:** `SHEET_ID` (operational) + `PATIENT_SHEET_ID` (patient DB) + the doctor-only **Call Audit** sheet (`AUDIT_SHEET_ID`, to be added).
- **The dashboard cannot act on the patient DB or the follow-up source.** Zero writes on `PATIENT_SHEET_ID`; `Followups_Today` is read-only to it and rewritten every morning by the clinic PC. **A flag that lives anywhere but `Do_Not_Call` is overwritten before breakfast.**
- **The blind judge is a fairness guarantee, and it is fragile** (D198). The agent's name is attached after the verdict, by the join. It dies the moment somebody adds the name to the prompt "for context."
- **An impression is not a measurement.** *"Conduct is good, script is not followed, closing is weakest"* is a hypothesis the training pack must **test**, not assume. This is D190's exact shape.
- Every rule from v65 §1 stands: the record is not the disk, but check which disk (D188) · **and check the manifest too (D201)** · a filename is not provenance · expected values from the artefact, not memory (D172) · a check that cannot fail is not a check · verification of a subset is not verification of the set (D186) · `UNKNOWN` is valid (D166) · a label is part of the instrument (D178) · a count without scope is a wall (D179) · an audit finds, it does not fix (D180) · the `Call_Feed` publish URL and the live `/exec` URL never enter chat, docs, or screenshots.

---

## §2 — BACKLOG

> **The rotation is NOT in this list.** Parked. Do not open a session with `rotate_callhook.sh status`.
> **Health check is zero-command:** `Health.gs` emails ✅/not-✅ at 09:00 IST; its *absence* is the fault. Ask for the email.

### 🔴 BLOCK A — the build session (design is finished; nothing here needs further discussion)

**A-00 — RECONCILE D78 AGAINST D195 BEFORE BUILDING EITHER.** D78 (Session 53; `Call_Console_Evolution_Spec_v2_0` §F, *sticky-on-staff 3-strike*): the third strike drops the patient to a bottom band, fires the WABA template, snoozes X days. **D195 (Session 131): the third attempt goes to the doctor.** Both designs. **Neither built.** D78 was invisible for eighty sessions because the spec holding it was a stump.

**A-0 — TWO OWNER INPUTS GATE THE AXIS-3 BUILD.** The **call script** (Hindi, as staff are meant to speak it) and the **definition of a complete closing** (2–4 checkable things). Both collected by `AI_Review_Layer_Decision_Workbook_S131.docx`. Until they arrive, `script_not_followed` and `no_closing` are **specified and inoperable** (D199, `UNKNOWN` per D166). *If there is no written script, that absence is the finding, and the first fix is a script, not a judge.*

**A-1 — THE D34 QUESTION. Owner's call, asked exactly once.** `saveIncomingOutcome` (L1233), the pending builder (L247), `getFollowups` (L925+), `sendBackToStaff` (L1502) and `getEscalations` (L1373) **all live in `WebApp.gs`.** D189 set the pattern: **suspend D34 by name, for a bounded edit, resume on verification.** Nothing server-side ships without this answer.

1. **F-8 — Fix B** (six lines, `Dashboard.html` only). Closes F-8, kills the L1260 catch, delivers a Block E item. **No D34 waiver needed.** Do this first; it stands alone.
2. **A-3 — the other two wrong client catches** (L1364, L1128). L1260 is handled by Fix B.
3. **Tile unification (D195)** — removal moves onto the outcome. **Needs A-1.**
4. **`Do_Not_Call` tab (D194)** — one tab, one filter line in `push_followups_today.py`. Closes `patient_deceased`, `number_invalid`, `asked_not_to_call` (F-20). **No `WebApp.gs`.** Cheap, and it stops a bereaved family being called.
5. **Stable case identity (D196)** — adopt `<phone>_<call_epoch>`. Sits on D158's join defect.
6. **A-4 — add a Sign out; strip `?k=` from the address bar.** Client-side only.
7. **A-5 — close `removeTriggers` (`Main.gs`) + `removeHealthTrigger` (`Health.gs`).** No `WebApp.gs`, no waiver. Cheap.
8. **A-6 — classify F-2's sixteen server-side `catch (e) {}` individually.** Never one commit (D180).
9. **A-7 — the Triggers screenshot.** Ten seconds. `sendFollowupSummary` / `rebuildCallFeed`.
10. **Transcript smoke test — still unbanked.** One transcript open confirms `getTranscriptText`.

### 🟠 BLOCK A′ — the AI review layer (build order, after A-0 and A-1 are answered)
11. **PROVISION** — columns on `Call_Verdicts` for Axis 1 and Axis 3; a provenance column that is **not** named `Source` (that name is taken by *source-on-medication*). Inert until filled.
12. **The doctor's review section** — a second row source into the Session-52 loop. `AUDIT_SHEET_ID` property. Read-only to start.
13. **`Doctor_Verdicts` writer flip (D193)** — dashboard becomes sole writer; `verdict_review.py` retires its harvest.
14. **F-18 first** — `verdict_review.py` must stop excusing incoming calls before any of its counts can be trusted.
15. **Phase-2 gate stays shut** until 100 refereed cards clear the bar (D191).

### 🟠 BLOCK C — make it cheap to run (prerequisite for Block D, D185)
16. One clock (server `todayIST`; closes F-5, F-13). 17. Stop whole-tab reads (fifteen `getDataRange().getValues()`; `Call_Feed` 3,019 rows — F-6). 18. Bundle the five follow-up calls (F-12). 19. `CacheService` on the payload, 30–60 s. 20. Quota headroom into `Health.gs`.
> **Note:** D195's pending builder gains a read of `Followup_Outcomes`. That lands on F-6/F-12. Block C exists to make exactly this cheap. Not a blocker; a cost to book.

### 🟢 BLOCK D — the incoming-call console (D181–D184)
21. **The D80 scope change first** (ex-F-19, withdrawn): the receiver stops skipping non-OBD calls (`call_hook_capture.py` L385). This amends a decision; it does not fix a bug. Tile at **hangup**, not ring; unknown numbers get tiles; nothing ends the day unlogged.

### 🟢 BLOCK E
22. Delete `Probe.gs` · stop embedding patient data in button markup (**delivered by F-8 Fix B**) · retire the dead ungated surface (26 non-page-called functions).

### 🔵 REPO HYGIENE (next git session)
23. **F-17** — `dashboard/WebApp.gs` must be replaced by the deployed file; the pre-fix copy renamed to `WebApp_PRECHANGE_ROLLBACK.gs`. Fix the doubled extensions on `CallField.gs.gs` and `Probe.gs.gs`.

### Longer-running (carried)
- Referee the 32 cards in `Verdict_Review` — **or don't, and let D191's dashboard clicks build the ledger instead.** That was the point of the design.
- Stage-3 consolidation; **D158 join defect sits underneath** and D196 closes it.
- AKEY_14 rotation · service-account key rotation (Tier A1, Lokesh). Stage 4 doctor portal. WABA authorizer fault (D120, Lokesh). Track-1 Hindi spelling in `vitals_page.html`.

---

## §3 — DOCUMENT STATE

- **KB → `Clinic_Master_KB_SystemsRegister_v1_54.md`.** **239,175 bytes / 2,311 lines / CR 0** *(counted with `splitlines()` — the v65 statement of 1,907 for v1.53 was wrong; the artefact was 1,906)*. Adds **§S131**, changelog v1.54, **D191–D201**, **F-17 – F-20**. Four anchors asserted unique; counts asserted before and after; the stale end-marker corrected. **Next free: D202.**
- **Runbook → this file, v66.** Supersedes v65. **v65 §3's KB line count is wrong** (1,907 → 1,906). v61 §5 still contains D176's defect and must never be followed.
- **AI Review Layer Design Specification → `AI_Review_Layer_Design_Spec_v1_1_S131.md` (NEW, v1.1).** Six sections, every item **NOW / PROVISION / LATER**, priced, rollback stated, D34 raised once. **This is what the build session reads.**
- **Decision workbook → `AI_Review_Layer_Decision_Workbook_S131.docx` (NEW).** Yes/no confirmations plus write-in areas for the call script and the closing definition. **The two gating inputs of A-0.**
- **Umbrella → `Dr_Manoj_Clinic_Umbrella_Architecture_v1_41.md`.** D191–D201 added; AI-review module opened as DESIGNED-NOT-BUILT; F-17–F-20 registered.
- **Frontend Doc → `Frontend_Dashboard_Documentation_v1_S130.md`.** Unchanged, and still correct. Read it before touching the dashboard.
- **Call Console Spec → `Call_Console_Evolution_Spec_v2_0.md` (NEW).** Self-contained. PART I = v1.1 §1–§11 (design); PART II = §A–§K (as built). **The only definition of D62, D66, D68, D69, D77, D78, D80, D81, D82, D97, D98.** Supersession stated: §E→§G, §G.4→§J, §A's 3rd-strike→§F.
- **Diagnostics Spec → `Diagnostics_Surveillance_System_Spec_v2_0.md` (NEW).** Self-contained. §L1–§L5 live checks · §M1–§M6 models · §P1 planned. Three sections named `§NEW` renamed (D178). **v1.6's full text restored — v1.7 had abridged it (F-23).**
- **Incident → `INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` (NEW).** §1–§16, one file. **v4's "rotation in progress" corrected to PARKED.** v1–v4 retired.
- **Audit → `Clinic_Callback_Tracker_AppsScript_Audit_v1_3.md`.** **RE-BASED, not re-audited.** §0 now carries the live artefact (`449f3fe6…`) beside the pre-fix one the findings were made on (`8bdb6d4d…`), and records that `Dashboard.html` is byte-identical across both — **so every `Dashboard.html` finding stands unre-derived.** Only `WebApp.gs` differs; **F-9 is CLOSED** and its reasoning preserved as the record of why. **D153 OVERTURNED**, not `UNKNOWN`. F-8 re-priced with two options and a lineage note. §4's questions 2 and 4 answered. **F-2's sixteen `catch (e) {}` untouched and still unclassified — A-6 (D180).**
- **Apps Script export → `4.json`**, md5 `449f3fe6981c2b75dfac0437126ece59`, 15 files. **The post-fix snapshot. Assert the md5, never the filename.**

---

## §4 — THE ROTATION PROCEDURE (D162) — PARKED
Unchanged from v65 §4. Steps 1–2 done; steps 3–4 parked; both keys burned; resume needs a **third** key. **Do not raise unless the owner does.**

---

## §5 — SESSION HYGIENE NOTES

> **⚠️ Carries v65 §5 in full.** Secrets are never displayed; both `CALLHOOK_SECRET` keys are burned; the `Call_Feed` publish URL, the live `/exec` URL and the WABA bearer token never enter chat, doc, or screenshot; `.env` backups are mode-600 secrets, do not delete.

- **This session touched nothing live.** No deploy, no VPS file, no property, no trigger, no commit. Six documents produced.
- **`AUDIT_SHEET_ID` will be a new script property.** It is an ID, not a credential — but the doctor-only Call Audit sheet carries **full patient numbers** (D152). Treat its ID with the same care as `PATIENT_SHEET_ID`.
- **The conduct data is doctor-only and stays out of the daily summary email.** An email is a document that can be forwarded.
- **The training pack plays; it does not export.** Patients' recorded voices do not become a file that leaves the clinic.

---

**END OF RUNBOOK v68 — §5 is the last section. If §5 is absent, this file is truncated.**
