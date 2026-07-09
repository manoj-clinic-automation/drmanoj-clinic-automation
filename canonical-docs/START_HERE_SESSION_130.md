START-HERE — SESSION 130

Hi Claude. Continuing my clinic-automation project (Session 130).
I'm Dr. Manoj Agarwal, orthopaedic surgeon, Advanced Orthopaedic Surgery Centre, Bareilly.
Solo practice, older Hindi-first semi-urban patients.

Working protocol as in `START_HERE_PROMPT_v3.md`. One step at a time. Full-file
replacements only. Plain language. Mask all secrets. Minimum manual commands —
script the guards; don't make me read exit codes.

---

## Read first, before anything else

- `Clinic_Master_KB_SystemsRegister_v1_52.md` — canonical; WINS on any conflict.
- `HANDOFF_RUNBOOK_2026-07-09_Session129_v64.md` — §0 (what happened), §2 (backlog).
- `Clinic_Callback_Tracker_AppsScript_Audit_v1_2.md` — the audit. `Dashboard.html` done.

**The Apps Script export in project knowledge must be the fresh one** —
md5 `8bdb6d4dfdb0a331c5048b3c0fccf367`, **15 files**, `Health.gs` present,
`Dashboard` at 2,738 lines. If it has 14 files or `PAGE_BUILD v18.18`, it is the
old misnamed file and **must not be used** (D188).

---

## Do NOT open this session with a rotation status check

The `CALLHOOK_SECRET` rotation is ⏸️ **PARKED** (KB §S128 · PARKED ITEMS REGISTER).
Steps 1–2 done. Both keys accepted. `refused today: none`. **There is no clock.**
Not abandoned, not pending, not for session-start review. Raise it only if I do.
If resumed: generate a **THIRD** key. `key_db8972` and `key_ea20dd` are both burned (D176).

**But DO raise F-9.** The key setters are parked **for ordering, not for safety** (D187).
That item stays in session-start review until it is closed.

---

## Health check — takes zero commands from me

`Health.gs` emails a daily report at 09:00 IST. If it arrived and says `✅ Clinic health OK`,
the live systems are fine. If it did not arrive, **that absence is the fault** — the trigger
stopped, not the clinic. Ask me for the email; do not ask me to run anything.
`today=0` on `Call_Feed`, `Call_Recordings` and `Call_Transcripts` before 21:30 is correct.

---

## BLOCK A — this session. Stop when it is done.

**A-0 — Is the GitHub repo public?** One look. If it is public, the ungated function
names in F-9 are public, and D187's bound does not hold. Currently `UNKNOWN`.

**A-1 — THE EVIDENCE CLICK. Do this before anything is fixed.**
On the live dashboard, find an incoming-call row that shows a **patient's name**.
Click **Log outcome ▾**.
- Nothing happens → **F-8 confirmed. D153 is overturned.**
- A form opens → **F-8 is wrong and I want to know why.**

This evidence exists only until A-2 lands. It cannot be recovered afterwards.

**A-2 — Fix F-8.** One line, `Dashboard.html` L912. The dead outcome button.

**A-3 — Fix the three wrong client catches.** L1260 first — it is the one that hid F-8.
Then L1364, L1128. The other fourteen are correct and stay.

**A-4 — Sign out + strip `?k=` from the URL after reading it.** Client-side only.

**A-5 — Close `removeTriggers` (`Main.gs`) and `removeHealthTrigger` (`Health.gs`).**
Anonymous trigger-killers. No `WebApp.gs`. No D34 waiver.

**A-6 — Finish audit pass 3: classify F-2's sixteen server-side `catch (e) {}` individually.**
A swallowed `ntfy` push is correct. A swallowed outcome write is not.
**They must never be fixed by one commit (D180).**

**A-7 — The Triggers screenshot.** Apps Script → Triggers. Ten seconds from me.
Nobody knows whether `sendFollowupSummary` and `rebuildCallFeed` are armed.
`Call_Feed`'s `lag=1d` is *consistent with* a live 21:30 trigger — not proof of one.

---

## What comes after, in order — do not start these this session

- **Block B** — `setDashboardKey` / `setStaffKey`. Anonymous privilege escalation → full PHI
  read + owner lockout. Needs a named **D34 suspension** and a rollback. **Blast radius
  assessed first, changed last (D187).**
- **Block C** — make it cheap to run, **without disrupting staff flow**: one clock (server sends
  `todayIST`) · bounded reads · bundled calls · `CacheService` · quota headroom in `Health.gs`.
  **Precedes Block D (D185).**
- **Block D** — the incoming-call console (D181–D184). The receiver already receives every
  incoming call and throws it away. Subtraction, not integration. Tile at **hangup**, not ring.
  Unknown numbers get tiles. Nothing ends the day unlogged.
- **Block E** — delete `Probe.gs` · stop embedding patient data in button markup.

---

## Standing rules earned the hard way

The record is not the disk, and the record loses — **but check which disk.** A filename is
not provenance (D188). Assert md5 and file count, never a nickname.
A check's expected value comes from the artefact, never from memory of it (D172).
A check that cannot fail is not a check. A green result produced by a code path the fault
does not traverse proves nothing (D174, D177).
**Verification of a subset is not verification of the set (D186).**
A version number is not evidence of a version. Assert byte and line counts.
The correct entry is sometimes `UNKNOWN` (D166). Don't infer from a snippet.
A hygiene note is executable. Never write a command whose output is a secret (D176).
A number, a label, or a name without the thing that gives it meaning is not information (D177–D179).
An audit finds; it does not fix (D180).
The `Call_Feed` publish URL is a bearer credential. Never into a chat, a doc, or a screenshot.

---

Connected sources: Google Drive (`drmka.ortho@gmail.com`) · Gmail · Notion (Clinic HQ) ·
GitHub (`drmanoj-clinic-automation`). ClickUp is parked (D17) — don't check it, don't suggest it.
Code lives in GitHub. Patient data is NOT in this project.

**Next free decision number: D189.**
