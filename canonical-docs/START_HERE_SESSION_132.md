START-HERE — SESSION 132

Hi Claude. Continuing my clinic-automation project (Session 132).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

Working protocol as in `START_HERE_PROMPT_v3.md`. One step at a time. Full-file replacements
only. Plain language. Mask all secrets. Minimum manual commands — script the guards; don't
make me read exit codes.

---

Read first, before anything else

`Clinic_Master_KB_SystemsRegister_v1_57.md` — canonical; WINS on any conflict.
  (277,634 bytes · 2,727 lines · CR 0 · md5 `949b3f6c…`. §S131 incl. §S131.12–.14. D191–D202.
   F-17–F-23, with **F-19 WITHDRAWN**. Next free: **D203**.)
  ⚠️ **Its decisions index has never carried D1–D120 (F-22).** Eleven are restored in §S131.13.
`HANDOFF_RUNBOOK_2026-07-09_Session131_v69.md` — §0 what happened, §2 backlog. **A-000 and A-00 are new.**
`Fault_Action_Register_v2_0.md` — **kept, not retired (D114).** Read its §0.2 before trusting any
  "System does" cell. **Not one row is live-and-acting.**
`AI_Review_Layer_Design_Spec_v1_1_S131.md` — **the build order is §10.** Read it before you
  propose anything. Every item is tagged NOW / PROVISION / LATER and priced.
`Frontend_Dashboard_Documentation_v1_S130.md` — the whole front end. Read before touching
  the dashboard.
`Clinic_Callback_Tracker_AppsScript_Audit_v1_3.md` — re-based. F-9 CLOSED, D153 OVERTURNED, F-8
  priced twice. **F-2's sixteen `catch (e) {}` still unclassified — that is A-6.**
`Call_Console_Evolution_Spec_v2_0.md` — **self-contained.** The ONLY definition of D62, D66, D68,
  D69, D77, D78, D80, D81, D82, D97, D98. **Read §F before touching D195's attempt cap.**
`Diagnostics_Surveillance_System_Spec_v2_0.md` — **self-contained.**
`INCIDENT_2026-07-08_CALLHOOK_403_v5_CONSOLIDATED.md` — §1–§16, one file. Rotation **PARKED**.
  The F9 decision sheet and the four incident files have been retired; do not go looking for them.

The Apps Script export in project knowledge is `4.json`. **Assert the md5, not the filename**
(D188, D201): 465,074 bytes · md5 `449f3fe6981c2b75dfac0437126ece59` · 15 files ·
`WebApp.gs` 1,647 lines / md5 `5173c3c7…` · `function setDashboardKey(` = 0.
If any of that fails, stop and tell me — do not proceed on a wrong artefact.

---

What closed in S131, so you don't reopen it

Nothing was built. **The design is finished and eleven decisions are locked (D191–D201).**
Do not re-litigate them. Read §S131.7 and the spec, and build.

F-9 is closed **in the artefact** — the setters are gone from the live export, verified by
definition-count, not substring. Don't re-audit it.

The recording lag is **not unknown and not a blocker** (D200). `recording_filename` arrives in
the `call.end` webhook and is already written to `Call_Durations` in real time. Don't ask me to
measure it.

Rotation — still PARKED. Do not open with a status check. Raise only if I do.

**A-00 — READ THIS BEFORE PROPOSING ANY BUILD.** D78 (Session 53, Call Console Spec v2.0 §F) and
D195 (Session 131) **disagree** about what happens on the third failed attempt. D78 fires a WABA
template and snoozes; D195 sends the case to me. Neither is built. **Reconcile them with me first.**

**A-000 — DO NOT WAIT FOR A RESTART.** The Fault Register marks nine faults `AUTO→ESC`. **No
auto-responder exists.** The watchman is read-only. F-24.

**Four things S131 got wrong, so you don't repeat them.**
(1) It called F-8's blast radius *"wider than the audit's headline."* The audit said it in S129.
(2) It presented D200 as a finding. The Call Console spec recorded it in **Session 25**.
(3) It raised **F-19** as a defect. It is **D80, as built, Session 54** — *"skips incoming / non-OBD
calls."* **Withdrawn.**
(4) It recommended retiring the Fault Register. **D114 makes it the single brain.** Caught in time.
All three have one cause: **a decision characterised without reading the document that made it.**
Read the document. A document is an artefact.

**The old note, kept:** It described F-8's blast radius as *"wider than
the audit's headline."* It was not — Audit v1.2 said it in S129, in its own title. The session wrote
D190 and D201 and then broke both against the very document that taught the lesson. **Read a document
before you characterise it. A document is an artefact.** (KB §S131.11.)

Health check — zero commands from me. `Health.gs` emails ✅/not-✅ at 09:00 IST. If it arrived
green, live systems are fine. If it did NOT arrive, that absence is the fault. Ask me for the
email; don't ask me to run anything.

---

TWO GATES. Ask me about these FIRST, before proposing any work.

**GATE 1 — the decision workbook.** `AI_Review_Layer_Decision_Workbook_S131.docx`. Ask me
whether I have filled it in. It carries:
  · Part 2 — the **D34 question**. Nothing server-side is built until I answer it.
  · Part 4 — the **call script**, in Hindi.
  · Part 5 — the **definition of a complete closing**.
Parts 4 and 5 gate the Axis-3 build. Until they arrive, `script_not_followed` and `no_closing`
are specified and **inoperable**, status `UNKNOWN` (D166/D199). If I say there is no written
script, **that absence is the finding**, and the first fix is a script, not a judge.

**GATE 2 — what ships without a D34 waiver.** If I refuse the waiver, these four still ship,
and they are worth doing on their own:
  1. **F-8 Fix B** — six lines, `Dashboard.html` only. Kills the dead button, removes the
     L1260 `catch(e){}`, and takes patient data out of the button markup (a Block E item).
  2. **`Do_Not_Call` tab (D194)** — one tab + one filter line in `push_followups_today.py`.
     **Do this early. A bereaved family can be called tomorrow.**
  3. **F-18** — `verdict_review.py` must stop printing the overturned D153 and excusing 19
     incoming calls from scrutiny.
  4. **A-3 (L1364, L1128)** and **A-5** (`removeTriggers`, `removeHealthTrigger`).

---

Standing rules earned the hard way

**The judge proposes. The doctor disposes. The staff act.** Each clause writes a different
table. No table gains a second writer.
**A false bounce costs one phone call. A false settle is invisible.** Every gate is asymmetric.
**An impression is not a measurement.** "Conduct is good, script is not followed, closing is
weakest" is a hypothesis with D190's exact shape. The training pack tests it; it does not
assume it.
The judge is **blind to agent identity** — a rule, not a convention (D198). It dies the moment
someone adds the name to the prompt "for context."
The record is a manifest **and** a disk — presence is verified by hashing, **absence by
exhaustion** (D201, sibling of D188).
A check's expected value comes from the artefact, never memory (D172). A count without its
scope is a wall (D179) — broken twice now, both times in a check written to catch a bad paste.
A check that cannot fail is not a check. Verification of a subset is not verification of the
set (D186). `UNKNOWN` is a valid entry (D166). An audit finds; it does not fix (D180).
Never write a command whose output is a secret (D176). The `Call_Feed` publish URL and the live
`/exec` URL are not for chat, docs, or screenshots.

Repo hygiene, owed: **F-17** — the public repo's `dashboard/WebApp.gs` is the **pre-fix** file
with both setters still in it, wearing the live file's name. Fix at the next git session.

---

Connected sources: Google Drive (`drmka.ortho@gmail.com`) · Gmail · Notion (Clinic HQ) ·
GitHub (`drmanoj-clinic-automation`). ClickUp is parked (D17). Patient data is NOT in this project.

Next free decision number: **D202**.
