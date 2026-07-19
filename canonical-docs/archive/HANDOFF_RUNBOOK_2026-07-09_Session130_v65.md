# HANDOFF RUNBOOK — 09 July 2026 — Session 130 — v65
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: FULL EOS — one live Apps Script file changed (`WebApp.gs` → version 64). No VPS code, no `.env`, no trigger, no property. Supersedes v64.**

---

## §0 — WHAT HAPPENED THIS SESSION

The session opened on Block A-0 and closed **F-9** — the only finding in this project where a stranger with a public URL could take the clinic away from its owner. It then read the front end end-to-end for the first time in 130 sessions and found a recorded decision (**D153**) standing exactly backwards.

### 1. A-0 — the repo is public, and that voided F-9's parking
One question: is the GitHub repo private? **No — it is public**, established with a control (a nonexistent repo → 404; this one → 200, shows `Public`, and serves `README.md` over anonymous `raw.githubusercontent.com`). The **live `/exec` deployment ID is in the public repo** (`sops/`, `launcher/portal.py`, `portal/portal.py`). D187 had parked F-9 last on the belief the URL alone was harmless because the function names were private. Both are public together. **The bound was void.** Mercy: `DASH_KEY`'s value is NOT in the repo — every `?k=` there is a placeholder.
- Making the repo private was **rejected**: git history keeps the leak; the assistant needs public read this session; obscurity was never the control. **The gate is the control.**

### 2. F-9 — closed (D189)
`setDashboardKey` / `setStaffKey`: ungated top-level functions in `WebApp.gs`, callable by any anonymous browser via `google.script.run`, each overwriting a master key. Chain confirmed by owner observation (incognito, no `?k=` → login card served → page fires `getAccess(k)` unauthenticated). Blast radius measured from the artefact: **55 browser-reachable functions, 28 ungated, and not one of the 28 is called by the page.** The two setters occur once each project-wide (their own definition). **Deletion breaks nothing.**
- Fix: 8 lines deleted, 4-line comment in. `node --check` OK, CR=0. **D34 named-suspended for this one deletion (D189), resumed on verify.**
- Deployed **version 64** on the single existing deployment — `/exec` URL unchanged.
- Verified against fresh export (md5 `449f3fe6…`): `WebApp.gs` **1,647 lines / 79,666 bytes / md5 `5173c3c7…`**; both setters gone; **other 14 files byte-identical**; `Dashboard.html` md5 `034529a1…` unchanged. Smoke tests green.
- **No silent exploitation:** the setters cannot read the old key back, so a still-working `DASH_KEY` (owner logged in post-fix) proves it was never overwritten; `STAFF_KEY` owner-confirmed unchanged in Script Properties.

### 3. F-8 confirmed, D153 overturned (D190)
The frontend was read and documented (**Frontend/Dashboard Documentation v1**, this session's companion). `saveIncomingOutcome` writes to `Followup_Outcomes` stamping `Section='Incoming'`. **The live tab holds 400+ rows; exactly TWO are `Incoming` — 29 June and 1 July, both name-blank, both Identity `non_patient`** — precisely the two cases the F-8 quoting defect allows. **The incoming `Log outcome ▾` button has never once worked for a known patient.** So D153 (*"staff never file incoming outcomes — workflow finding"*) was **wrong: not a habit but an impossibility**, then relied upon for the Stage-3 join. **F-8's fix is deferred to a decision sheet (S131)** because incoming tiles clear on `Callbacks_Today.Staff Status`, not on outcome — a working button alone won't make them behave like follow-up tiles.

### 4. F-16 (new finding) — `PAGE_BUILD` is a page stamp, not a server stamp
Owner saw `v18.19·S124` after deploying WebApp v64 and reasonably asked. The served page cannot report which `WebApp.gs` version `/exec` runs. Cosmetic-but-misleading (D178 pattern); logged, not fixed.

### 5. One honest process note
The verification checker first mis-fired — it counted the substring `setDashboardKey` (now in the explanatory comment) instead of the definition `function setDashboardKey(`. The assertion caught the assistant; the fault was in the instrument. **A count without its scope is a wall (D179), broken in the very check built to catch a bad paste — and caught.**

---

## §1 — MENTAL MODELS (carried, all still true)

- **The gate is the control, not obscurity.** F-9's parking rested on a private-repo assumption that was false. Server-side role enforcement (`dashRole_`) is sound; the danger was ungated *setters* outside the page's call set.
- **Filing an outcome ≠ clearing a tile.** Incoming tiles clear on `Callbacks_Today.Staff Status`; the outcome card writes a different tab. Two mechanisms, one gesture — a UX trap independent of F-8.
- **Two spreadsheets, not one:** `SHEET_ID` (operational) + `PATIENT_SHEET_ID` (patient DB). Known/unknown = a `Patient_Master` match at read time.
- **`Followup_Outcomes` has two writers** (incoming + follow-up), separated only by the `IN_`/`Section` marker — bears on the D158 join.
- Every rule from v64 §1 stands: the record is not the disk but check which disk (D188) · a filename is not provenance · expected values from the artefact not memory (D172) · a check that cannot fail is not a check · verification of a subset is not verification of the set (D186) · `UNKNOWN` is valid (D166) · a label is part of the instrument (D178) · a count without scope is a wall (D179) · an audit finds, it does not fix (D180) · a hygiene note is executable (D176) · the `Call_Feed` publish URL is a bearer credential, never into chat/doc/screenshot.
- **New this session:** delete-don't-guard an ungated function nothing calls, and suspend D34 by name for one removal (**D189**) · a recorded workflow finding is verified against the artefact before it is relied upon; absence of data is not evidence of a habit (**D190**).

---

## §2 — BACKLOG

> **The rotation is NOT in this list.** Parked (KB §S128 · PARKED ITEMS REGISTER). Do not open a session with `rotate_callhook.sh status`.
> **Health check is zero-command:** `Health.gs` emails ✅/not-✅ at 09:00 IST; its *absence* is the fault. Ask for the email; don't ask the owner to run anything.

### 🔴 BLOCK A — remaining items (F-9 done; A-1 evidence banked; F-8 fix deferred)

1. **F-8 decision sheet (S131).** The button quoting fix (L912/L923) **plus** the tile-removal behaviour (incoming tiles clear on `Staff Status`, not on outcome). Ship the two together or the button logs without clearing. Evidence banked in Frontend Doc §6.
2. **A-3 — the three wrong client catches** (L1260 first — the one that hid F-8, then L1364, L1128). The other fourteen are correct and stay.
3. **A-4 — add a Sign out; strip `?k=` from the address bar after reading it.** Client-side only. (F-11: key sits in `localStorage` cleartext with no sign-out.)
4. **A-5 — close `removeTriggers` (`Main.gs`) and `removeHealthTrigger` (`Health.gs`).** Anonymous trigger-killers. **No `WebApp.gs`, no D34 waiver.** Cheap and clean. *(Carried, untouched this session.)*
5. **A-6 — finish audit pass 3: classify F-2's sixteen server-side `catch (e) {}` individually.** A swallowed `ntfy` push is fine; a swallowed outcome write is not. **Never fixed by one commit (D180).**
6. **A-7 — the Triggers screenshot.** Cheapest open item. `sendFollowupSummary` and `rebuildCallFeed` may or may not be armed. Ten seconds from the owner.
7. **Transcript smoke test — still unbanked.** `getTranscriptText` (OutcomeLog, untouched) — near-zero risk, owner asked to protect that path. One transcript open confirms it.

### ⏸️ BLOCK B — parked LAST, not silenced (D187) — but its premise changed
8. **`setDashboardKey` / `setStaffKey`** — **CLOSED this session (D189).** Block B's headline item is done. What remains of the "ungated surface" concern is the other **26** ungated functions (17 HIGH after A-5 removes two): each can fire an email, rebuild `Call_Feed`, or kill a trigger from any anonymous browser; **none returns PHI** (the two that could are gone). This is now a **Block-E-sized subtraction**, not a B-item: an ungated function the page never calls has no reason to be browser-reachable. Decision sheet when reached.

### 🟠 BLOCK C — make it cheap to run (prerequisite for Block D, D185). *Must not disrupt staff flow.*
9. One clock (server `todayIST`; closes F-5, F-13). 10. Stop whole-tab reads (fifteen `getDataRange().getValues()`, `Call_Feed` 3,019 rows — F-6). 11. Bundle the five follow-up calls (F-12). 12. `CacheService` on the payload, 30–60 s — largest saving, least change. 13. Quota headroom into `Health.gs` — daily budget `UNKNOWN`, unwatched.

### 🟢 BLOCK D — the incoming-call console (D181–D184)
14. Receiver stops discarding incoming calls; tile at **hangup**, not ring; unknown numbers get tiles; nothing ends the day unlogged. **Unify the two tile-removal mechanisms** so logging an outcome clears an incoming tile the way it clears a follow-up tile.

### 🟢 BLOCK E — delete `Probe.gs` · stop embedding patient data in button markup · **and now: retire the dead ungated surface** (the 26 non-page-called functions).

### Longer-running (carried)
- Referee the 32 cards in `Verdict_Review` (0 done — every accuracy claim is agreement, not accuracy).
- Stage-3 consolidation; **D158 join defect sits underneath and should be fixed first** — and the Frontend Doc shows the `Followup_Outcomes` two-writer split it must filter on.
- AKEY_14 rotation · service-account key rotation (Tier A1, Lokesh). Stage 4 doctor portal. WABA authorizer fault (D120, Lokesh). Track-1 Hindi spelling in `vitals_page.html`.

---

## §3 — DOCUMENT STATE

- **KB → `Clinic_Master_KB_SystemsRegister_v1_53.md`.** 207,959 bytes / 1,907 lines / CR 0. Adds **§S130**, changelog v1.53, **D189–D190**, **F-16**. Title, next-free line, and changelog were the only non-additive edits; three anchors asserted unique; counts asserted before/after. **Next free: D191.**
- **Runbook → this file, v65.** Supersedes v64. v61 §5 still contains D176's defect and must never be followed.
- **Frontend/Dashboard Documentation → `Frontend_Dashboard_Documentation_v1_S130.md`** (NEW). The front end mapped to match the backend: two spreadsheets, every tab + writer/reader, the full call flow (incoming known/unknown, outgoing), the three outcome vocabularies, the tile-fate table, and F-8 confirmed against the live sheet. **Fold into the KB as a standing section next consolidation.**
- **Umbrella → `Dr_Manoj_Clinic_Umbrella_Architecture_v1_40.md`.** F-9 module status flipped to CLOSED; D189/D190 added; frontend-map note.
- **Audit → `Clinic_Callback_Tracker_AppsScript_Audit_v1_2.md`.** Unchanged this session (F-2 classification is A-6, still open).
- **`WebApp_v19_D189.gs`** — the deployed file (1,647 lines, md5 `5173c3c7…`). **`WebApp_PRECHANGE_ROLLBACK.gs`** — the pre-fix live file (1,652 lines, md5 `276dc197…`), the rollback point.
- **Fresh export `Clinic_Callback_Tracker__3_.json`** (pre-fix, md5 `8bdb6d4d…`) and the post-fix export (md5 `449f3fe6…`) are the two canonical snapshots this session.

---

## §4 — THE ROTATION PROCEDURE (D162) — PARKED
Unchanged from v64 §4. Steps 1–2 done; steps 3–4 parked; both keys burned; resume needs a **third** key. **Do not raise unless the owner does.**

---

## §5 — SESSION HYGIENE NOTES

> **⚠️ Carries v64 §5 in full.** Secrets are never displayed; both `CALLHOOK_SECRET` keys are burned; the `Call_Feed` publish URL and the WABA bearer token never enter chat/doc/screenshot; `.env` backups are mode-600 secrets, do not delete.

- **New this session:** the live `/exec` URL appeared in two screenshots. It is **not** a credential and cannot be revoked without a redeploy that changes it everywhere — and it is already in the public repo — so nothing new was lost. But it is what makes the ungated surface reachable; **treat it like the `Call_Feed` URL from now on: not into screenshots.**
- **`DASH_KEY` and `STAFF_KEY`** were owner-confirmed unchanged in Script Properties — the F-9 non-exploitation proof. Do not display them; a working login is sufficient evidence.
- **This session changed exactly one live file** (`WebApp.gs` → v64). No VPS file, no `.env`, no trigger, no property. Four documents produced (KB v1.53, Runbook v65, Frontend Doc v1, Umbrella v1.40) plus two `WebApp.gs` snapshots.

---

**END OF RUNBOOK v65 — §5 is the last section. If §5 is absent, this file is truncated.**
