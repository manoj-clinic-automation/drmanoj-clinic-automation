# HANDOFF RUNBOOK — 09 July 2026 — Session 129 — v64
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: EOS-LIGHT — no code changed, no file written, no trigger touched, no property set. Audit pass 3 item 1 complete. Supersedes v63.**

---

## §0 — WHAT HAPPENED THIS SESSION

`Dashboard.html` — 2,738 lines, unread after 128 sessions — was read in full. Eight findings. One of them has probably been costing the clinic data every day since it shipped.

### 1. The session opened by getting it wrong, and that matters

The assistant measured `Dashboard.html` at **2,676 lines** from the JSON export in project knowledge, declared five canonical documents defective for saying 2,738, and quoted the project's own rule back at it: *"the record is not the disk, and the record loses."*

**The record was right. The disk was the wrong disk.** `Clinic_Callback_Tracker_AppsScript_S124.json` carries `PAGE_BUILD = 'v18.18 · S57'` and contains **no `Health.gs`**. It is a *pre*-S124 export, named for a session it predates.

The owner exported fresh. The live file is **2,738 lines · 157,611 bytes · md5 `034529a1…20dfec`** — the exact md5 this KB's own **v1.48 changelog** already records for the v18.19 D156 fix. Two sources agree; the file in project knowledge disagrees with both.

**The rule held. The identification of the artefact did not. → D188, a filename is not provenance.** The claim was withdrawn before any document was edited on the strength of it.

### 2. F-8 — a button that has been dead for months, in the staff path, silently

Line 912 serialises patient details with `JSON.stringify` (which always emits `"`), passes them through `jsq()` (which does not escape `"`), and line 923 pastes the result into a `"`-delimited `onclick`. The first quote closes the attribute early.

- Number **not** in `Patient_Master` → handler compiles → button works.
- Number **in** `Patient_Master` → handler is a syntax error → **button does nothing, silently, forever.**

`inOpen()` is the only route to the incoming-outcome form. **For any incoming caller the clinic already knows, staff cannot file an outcome at all.**

**And D153 says: *"staff never file outcomes for incoming calls — workflow finding, not a gap."*** That population is exactly the one whose button is dead. A rendering defect may have been recorded as a staff habit, then relied upon to justify the Stage-3 join in `call_verdict.py`.

**D153 is now `UNKNOWN`.** One click on the live dashboard settles it — and **that evidence expires the moment F-8 is fixed.**

### 3. F-9 — F-1 was wrong, and wrong in the project's signature way

F-1 examined **seven** ungated globals, verified correctly that none returns patient data, and published *"not exfiltration"* over a surface of **twenty-seven**. Among the twenty it never opened: **`setDashboardKey`** and **`setStaffKey`**, which overwrite the doctor's key.

Manifest confirmed live: `ANYONE_ANONYMOUS` + `USER_DEPLOYING`. Anyone with the `/exec` URL, no `?k=` required, can set `DASH_KEY`, sign in as `full`, and read names, Clinic IDs, diagnoses, transcripts — and lock the owner out in the same call.

**Two things are true and must both be said.** Server-side role enforcement is otherwise **sound** — every doctor-only function checks `dashRole_(key) === 'full'`, so staff with a valid `AKEY` genuinely cannot reach the review console. And `removeTriggers` would be caught, because `Health.gs` alerts by silence.

Both setters live in `WebApp.gs`. **D34 forbids touching it.** The rule written to protect a fragile file now stands in front of the only real privilege escalation in the project. → **D186, D187.**

### 4. The incoming-call console, designed

The owner named the real problem: *"the incoming doesn't open the callback tracker currently."* F-8 is the broken button; underneath is a missing capability.

**The receiver already receives every incoming call and throws it away.** Per D178 it writes only `category == "obd"` with a `client_ref_id`. On 09-Jul: **66 webhooks accepted, 29 rows written.** The other 37 were real calls, raw-logged and dropped.

So this is **subtraction, not integration.** No Lokesh. No credential. No token. Verified against the API reference §9: `call.end` and `call.summary` already arrive; the event list is self-serve tick-boxes.

**The tile fires at hangup, not at ring (D184)** — because Apps Script cannot push, and because *while the phone is ringing the receptionist is answering the phone.* She cannot log during a ring and must not be looking at a screen. The outcome becomes knowable at hangup.

**Every fault found this session was in code nobody had read, and every one of them was silent.**

---

## §1 — STATE / MENTAL MODELS

### Nothing live changed this session

No VPS file, no `.env`, no restart, no Apps Script file, no trigger, no script property, no publish setting. Everything in §1 of **v63** stands verbatim. The four clocks are unchanged (KB §S128B).

### The Apps Script project, now measured

**Live export: 465,195 bytes · md5 `8bdb6d4dfdb0a331c5048b3c0fccf367` · 15 files.**
Twelve `.gs` files byte-identical to the stale project-knowledge copy. `Dashboard` differs; `Health.gs` is new.

- `Dashboard.html` — **2,738 lines · 157,611 bytes · md5 `034529a124c6bfab8aec2b675620dfec`** (v18.19, D156, unchanged since S124).
- **55 browser-reachable globals. 27 ungated. 24 called by the page.**
- Manifest: `access: ANYONE_ANONYMOUS`, `executeAs: USER_DEPLOYING`, `timeZone: Asia/Kolkata`.

**In Apps Script, every top-level function not ending in `_` is callable from any browser that has loaded the page** — not only the ones the page calls. This is the fact F-1 missed.

### Three clocks, not two

`Session.getScriptTimeZone()` (IST, 15× in `WebApp.gs`) · `CC_TZ` (18× in `Callconsole.gs` / `OutcomeLog.gs` — **F-5**) · the browser's device clock (`fuDayKey`, L1603). **"Local" is not "IST."** A tablet with a wrong time zone can corrupt follow-up state.

### Carried, all still true

The worker reads `.env` once, at import · absence of coverage is not absence of events · **a check that cannot fail is not a check** · two labels of the same key can disagree and both be right (D165) · `grep -c` exits 1 on a zero count — never chain with `&&` · restart at a moment **you** choose · one successful call does not verify a fix · **the runbook is not evidence** · install by candidate path · verify the rollback point at the moment of use · a constant offset is not a rate · **the record is not the disk, and the record loses** · the correct entry is sometimes `UNKNOWN` · a control on one path into a hazard is not a control on the hazard · a safety flag is a clinical signal about a patient, never a statement about staff accuracy · **0 cards refereed, so every accuracy claim is agreement, not accuracy** · expected values come from the artefact, never memory (D172) · a selftest is not a production verification (D174) · a hygiene note is executable (D176) · a check must match the clock of what it checks (D177) · a label is part of the instrument (D178) · a count without its scope is a wall (D179) · an audit finds, it does not fix (D180).

**New this session:** incoming calls become first-class — the receiver already has them (**D181**) · an unknown number gets a tile; identity is established by staff, not a filter (**D182**) · nothing ends the day unlogged (**D183**) · the tile fires at hangup, not at ring (**D184**) · **nothing real-time is built on a system whose running cost is unmeasured** (**D185**) · **verification of a subset is not verification of the set** (**D186**) · a fix needing D34's suspension is priced first and made last (**D187**) · **a filename is not provenance** (**D188**).

---

## §2 — BACKLOG

> **The rotation is NOT in this list.** Parked (KB §S128). Do not open a session with `rotate_callhook.sh status`.
> **F-9's key setters ARE in this list.** Parked *for ordering*, not for safety (D187). Raise them.

### 🔴 BLOCK A — cheap, safe, independent. Session 130 should stop after this block.

0. **Confirm the GitHub repo is private.** If it is public, the ungated function names in F-9 are public too, and the bound in D187 does not hold. **Currently `UNKNOWN`.** One look.
1. **The evidence click.** On the live dashboard, click *Log outcome ▾* on an incoming row showing a patient's name. Nothing happens = F-8 confirmed, D153 overturned. **Must precede item 2 — a fixed button can never tell us whether it was broken.**
2. **Fix F-8.** One line (`Dashboard.html` L912). Dead outcome button for every known patient.
3. **Fix the three wrong client catches** (L1260 first — the one that hid F-8), L1364, L1128.
4. **Add a Sign out; strip `?k=` from the address bar after reading it.** Client-side only.
5. **Close `removeTriggers` (`Main.gs`) and `removeHealthTrigger` (`Health.gs`).** Anonymous trigger-killers. No `WebApp.gs`, no D34 waiver.
6. **Finish audit pass 3 — classify the sixteen server-side `catch (e) {}` individually.** Unstarted. **They must never be fixed by one commit (D180).**
7. **The Triggers screenshot.** Still the cheapest open item in the project. `sendFollowupSummary` and `rebuildCallFeed` may or may not be armed.

### ⏸️ BLOCK B — parked LAST, not silenced (D187)

8. **`setDashboardKey` / `setStaffKey`.** Unauthenticated privilege escalation → full PHI read + owner lockout. Requires suspending **D34**. Owner directive: **assess blast radius first, change last.** Decision sheet required, naming a rollback.

### 🟠 BLOCK C — make it cheap to run. Prerequisite for Block D (D185). *Must not disrupt staff flow.*

9. **One clock.** Server sends `todayIST`; the client computes no dates. Closes **F-5** and **F-13**.
10. **Stop reading whole tabs.** Fifteen `getDataRange().getValues()` reads, incl. `Call_Feed` at 3,019 rows (**F-6**). Read the last *N*.
11. **Bundle the five follow-up calls into one.** (**F-12**)
12. **`CacheService` on the dashboard payload, 30–60 s.** Six agents refreshing becomes one sheet read. **Largest saving, least change.**
13. **Quota headroom into `Health.gs`.** The daily execution budget is **`UNKNOWN`** and nothing watches it. Exhaustion should be predicted, not discovered mid-clinic.

> **Escalation path if 9–13 prove insufficient:** move the *read* path to the VPS (service account + `gspread` already exist; Apps Script keeps the writes) — **a trade, not a win**, adding a second auth surface. Beyond that: move the dashboard off Apps Script entirely. Large, not recommended. See KB §S129.

### 🟢 BLOCK D — the incoming-call console (D181–D184)

14. **Receiver stops discarding incoming calls.** `call.end` with `category == "incoming"` is written, not dropped. Offline build → `py_compile` → md5 → install.
15. **New `Incoming_Calls` tab. One writer. Never `Call_Durations`** — that tab means *console-dialled* (D178).
16. **The incoming band on the dashboard.** A tile per call at hangup. **Unknown numbers get a tile (D182)** — the unknown-caller path in `inOpen()` already exists.
17. **The 21:30 sweep (D183).** Every unlogged call, both directions, escalates to a doctor-facing review band. This is what makes the console self-correcting.
18. **Ring-time tile — deferred, not dropped (D184).** Needs Block C, a panel tick, and a captured `call.initiated` body. **No `call.initiated` has ever been seen on this account. `UNKNOWN`.**

### ⚪ BLOCK E — hygiene

19. **Delete `Probe.gs`.** Three of the ungated globals, and the sole reason the deployment holds the `documents` OAuth scope (**F-7**, **F-15**). *Assistant's call, per owner.*
20. **Stop embedding patient data in button markup (F-10).** Buttons carry a row ID; details stay in memory. Twenty-four fragile sites become none. *Approved if workflow is not compromised.*
21. **Audit → v1.2.** Done this session. F-1 corrected; F-8…F-15 added.

### 🟡 CARRIED FROM v63 — unchanged

22. **F-0** — `Call_Feed` published to the web. Deliberate. **Do not disable.** ~3,000 patient mobiles + agent names public.
23. **F-3** — `Followup_Outcomes` has three writers under a "one-writer tab" comment. Safe by accident of layout.
24. **F-4** — `logOutcome` dead, `Outcomes_Log` never created, writer still browser-reachable, appends PHI.
25. **`ANTHROPIC_API_KEY len=111`** unaccounted in `/root/wa/.env`. *Has an investigative half — do not open half-way.*
26. **Watchdog's two defects** (coverage guard → exit 3; `unquote()` before hashing). Then schedule it.
27. **`rotate_callhook.sh status`** startup-line window: two minutes → last service start.
28. **`wa_approve.py` → systemd.** Currently `nohup`; dies on SSH close.
29. **Optional second `Health.gs` trigger at 13:00**, `maxLag: 0` on `Call_Durations`. Designed, not built.
30. **Open questions, cheap:** Window 2 · 133 vs 132 · six unexplained bytes between `.env` and `.env.bak_20260707_162509`.

### OWNER TASK (~20 min) — everything downstream depends on it

31. **Referee the 32 cards in `Verdict_Review`.** Zero done. Until some are, every accuracy claim about the AI judge is *agreement*, not *accuracy*. **And if F-8 confirms, the incoming half of that data was never fileable in the first place.**

### Longer-running

32. Stage-3 consolidation (nightly timer; `call_transcription.py` commit; agent + Clinic ID missing from `Call_Verdicts`). **D158's join defect sits underneath it and should be fixed first.**
33. AKEY_14 rotation · service-account key rotation (Tier A1, Lokesh).
34. Stage 4 — doctor portal at `followup.dr-manoj.in/portal`, port 8099.
35. WABA authorizer fault (D120, Lokesh).
36. Track-1: Hindi **spelling** in `vitals_page.html` LIB strings · Step 7 reconciliation · living Clinic Data Map.

---

## §3 — DOCUMENT STATE

- **KB → `Clinic_Master_KB_SystemsRegister_v1_52.md`.** 196,340 bytes / 1,867 lines / CR 0. Seven anchors asserted unique before edit; the guard threw once and nothing was written; pre-edit md5 re-verified after. Adds **§S129**, **D181–D188**. Next free: **D189.**
- **Runbook → this file, v64.** Supersedes v63. **v61 §5 contained D176's defect and must never be followed.**
- **Audit → `Clinic_Callback_Tracker_AppsScript_Audit_v1_2.md`.** F-1 corrected; F-8…F-15 added; §0 now names the export by md5 and file count, not by nickname (D188).
- **Umbrella → `Dr_Manoj_Clinic_Umbrella_Architecture_v1_39.md`.** Decisions list and module table brought current.
- **⚠️ `Clinic_Callback_Tracker_AppsScript_S124.json` in project knowledge is MISNAMED AND STALE.** It is a pre-S124 export (`v18.18 · S57`, no `Health.gs`). **Delete it.** Replace with the fresh export, named by its md5.

---

## §4 — THE ROTATION PROCEDURE (D162) — PARKED

1. ✅ **DONE 08-Jul 23:38:00.** `PREV` = current.
2. ✅ **DONE 09-Jul 09:05:58.** New key into `CALLHOOK_SECRET`. WARN lines on the previous key are **the instrument, not a fault**.
3. ⏸️ **PARKED.** Update the MyOperator panel. No restart. **When resumed: generate a THIRD key first (D176).** Verify per the S124 standard — one real call **and** a re-check ≥1 hour later, same clinic day.
4. ⏸️ **PARKED, and blocked on 3 regardless (D173).** The step-4 command exists in no document, by design.

**Rollback, any time:** `bash /root/wa/rotate_callhook.sh rollback`. Or put the old key back in the panel — the VPS needs no touching.

> **Note for Block D:** adding an incoming-call webhook event is a **tick-box** in the MyOperator panel (API ref §9.0 item 5, self-serve). **It does not touch any key and does not resume this rotation.**

---

## §5 — SESSION HYGIENE NOTES

> **⚠️ REWRITTEN UNDER D176.** The v61 version of this section named a command whose output is a live credential. It was executed and the key was disclosed. **No command whose output is a secret appears in this project's documents. Not as an instruction, not as a description of what was once done.**

- **Secrets are never displayed.** If a value must be retained, the **generating process** writes it to a mode-600 file on the box. **Do not read it back.** Both parties work with `key_<md5[:6]>` labels only.
- **Both keys are burned.** `key_db8972` and `key_ea20dd` have each appeared in a chat transcript. Resuming the rotation requires a **third** key.
- **`/root/wa/.rotate_s127_state`** (mode 600) holds the path of the current rollback backup. **Do not delete it.**
- **`.env` backups all contain live or historical secrets.** Mode 600, treat as secrets, do not delete: `.env.bak_20260707_162509` (forensic) · `.env.bak_s126_20260708_212316` · `.env.bak_s127_pre_rotation_20260708_232229` · `.env.bak_s127_step2_20260709_085801` (**the live rollback point**).
- **`.env.candidate_s127` should not exist.** If it reappears, a `stage` was run and not installed; it contains a live key.
- **The `Call_Feed` publish URL is a bearer credential.** It lives in `data\feed_url.txt` on the clinic PC. It must never be pasted into a chat, a document, or a screenshot.
- **`DASH_KEY` lives only in the owner's Apple Notes** — and, per F-11, in cleartext `localStorage` on every device it has ever been typed into. **There is no sign-out.** Block A item 4.
- **The `/exec` URL is not a credential and cannot be revoked** without a redeploy that changes it everywhere. F-9's bound depends on it.
- **This session wrote nothing.** No VPS file, no Apps Script file, no key, no trigger, no property. Four documents were produced and one stale artefact identified for deletion.

---

**END OF RUNBOOK v64 — §5 is the last section. If §5 is absent, this file is truncated.**
