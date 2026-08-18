# HANDOFF RUNBOOK — 09 July 2026 — Session 128 — v63
**Dr. Manoj Agarwal Clinic · Bareilly · Orthopaedic surgery · Solo practice**
**Session type: FULL EOS — new live Apps Script file (`Health.gs`). No VPS code, no `.env`, no restart. Supersedes v62 (written earlier the same day).**

---

## §0 — WHAT HAPPENED THIS SESSION

Three things, in the order the owner asked for them.

### 1. The rotation was parked, by the owner, correctly

> *"If both keys are doing their job, then I'm not interested in this ping pong of pasting commands and then pasting the output to you just for more security."*

Steps 1 and 2 are complete. The dual-key gate (D162) exists so the panel and the VPS may disagree **indefinitely**. Nothing is pending. Nothing degrades. **There is no clock.** Rotation is now a **parked item** (KB §S128, PARKED ITEMS REGISTER), closed to session-start review, re-opened only when the owner names it.

**The key was disclosed getting there.** Runbook **v61 §5** recorded, as hygiene, a `grep` of the live key "for safekeeping." The owner ran it. `key_ea20dd` entered a chat transcript. **Three sessions were spent taking a secret out of a transcript; one line of hygiene notes put a fresh one back.** Document defect, not owner error. **D176 — a hygiene note is executable. Anything written in a runbook will be run.**

**Bound of the exposure, so it is never re-litigated from fear:** `CALLHOOK_SECRET` gates one capability — an HTTP POST to the receiver. A holder can inject rows into `Call_Feed`. **No patient-data read, no call placement, no panel or dashboard access. Data-integrity, not breach.** When resumed, `stage` must generate a **THIRD** key; `key_ea20dd` must never be pasted into the panel.

### 2. `Health.gs` — the instrument that was missing

Four sessions of command-and-paste were **not** an impatient user. They were the symptom of a missing instrument: **nobody could learn whether the live systems were healthy without the owner typing into a terminal.**

`Health.gs` v2.2 is now live in the dashboard's Apps Script project. Read-only, zero write calls, `WebApp.gs` untouched (D34), no new OAuth scopes, zero collisions against 152 existing functions. **It emails every morning, green or not** — so if the mail does not arrive, *that absence is the fault*. It records its own last run, so a missed day surfaces the next morning.

**v1 shipped at 10:23 and was wrong three times. Each was caught by the owner reading a number in the email and asking about it. Not one was caught by reasoning.**

- **`today=0` on a nightly tab.** `Call_Feed` is rebuilt at 21:30; at 09:00 the answer is `0` whether it ran or died. v1 printed `✅ Clinic health OK` over it — on the day the runbook gained *"a check that cannot fail is not a check."* **D177.**
- **`Call_Durations` was not monitored at all** — the tab the VPS receiver writes, and the one that went silent for 44 hours on 06-Jul. Replayed against four scenarios: **v2 catches that outage on its second morning**; v1 says OK to all four.
- **`370 outcome(s) awaiting review`** — a lump with no clock. The review UI serves only `today`/`yesterday`. Truly: **3 today · 10 yesterday · 357 aged out.** 3+10+357 = 370. **The owner's first question of the session was spent on a queue that did not exist. D179.**

Also corrected: `Call_Durations` was labelled *"real time"*. The receiver writes a row **only** for `category=="obd"` with a `client_ref_id` — **console-dialled calls only.** 66 webhooks accepted on 09-Jul produced **29 rows**. Label now says so. **D178.**

And a rejected change worth recording: `maxLag: 2` on `Call_Durations` was tried and **failed its own test** — it delays outage detection to the third morning to buy comfort against a rare, dismissible false alarm. Reverted to `1`.

### 3. The Apps Script audit was opened

At the owner's direction. **Passes 1–2 complete, pass 3 preliminary, pass 4 not started. Nothing was fixed (D180).** New canonical doc: `Clinic_Callback_Tracker_AppsScript_Audit_v1_1.md`.

12 server files, 4,231 lines, `Dashboard.html` 2,738 lines, 51 browser-reachable globals, **zero duplicate definitions after 128 sessions.**

**Three of the assistant's audit checks failed and were rebuilt before any finding was stated.** And the script that folded F-0 into the audit **threw before saving while the file was copied out under the new name** — for ten seconds a `v1.1` existed that was byte-identical to `v1.0`. **A version number is not evidence of a version.** Caught only because the traceback was read.

**Every fault found this session was the assistant's own, and all of them were one fault: a number, a label, or a name presented without the thing that gives it meaning.**

---

## §1 — STATE / MENTAL MODELS

### The four clocks — do not re-derive these

| Tab | Writer | Cadence | maxLag |
|---|---|---|---|
| `Followups_Today` | `push_followups_today.py` (clinic PC) | each morning | 0 |
| `Followup_Outcomes` | staff, via dashboard | through the day | 2 |
| `Call_Durations` | `call_hook_capture.py` (VPS) | real time — **console-dialled (OBD) calls ONLY** | 1 |
| `Call_Feed` | `rebuildCallFeed()` (Apps Script) | nightly **21:30**, 14-day clear-and-rewrite | 1 |
| `Call_Recordings` | Stage 1 (VPS) | ~02:00, archives **yesterday** | 1 |
| `Call_Transcripts` | Stage 2 (VPS) | ~03:00, archives **yesterday** | 1 |

**`Call_Feed` and `Call_Durations` are different tables on different clocks.** `today=0` on `Call_Feed` at breakfast is correct, not a fault.

### Call-hook family — unchanged, healthy

- **`call-hook.service` LIVE.** `call_hook_capture.py` v2 (dual-key), 31,490 bytes, 701 lines, md5 `beafccafbf7e81aa5f2736be939b2bbb`, 43/43. gunicorn `-w 1`, no `--preload`, `127.0.0.1:8098`.
- **`.env` — 33 lines, CR 0, mode 600.** `CALLHOOK_SECRET len=24` (`key_ea20dd`) · `CALLHOOK_SECRET_PREV len=12` (`key_db8972`). **Both accepted. Both exposed.**
- **Rotation: steps 1–2 done, steps 3–4 ⏸️ PARKED (D176 · KB §S128).**
- **`rotate_callhook.sh` LIVE.** Cosmetic defect: `status` looks back only two minutes for the startup line, so it prints a blank.
- **`callhook_watchdog.py` v1.0** — built, manual only, two defects open. Not scheduled.
- **`ANTHROPIC_API_KEY len=111`** still unaccounted in `/root/wa/.env`.

### Staff-facing systems

- **`Health.gs` v2.2 LIVE**, daily 09:00 IST trigger. Rollback: `Health_v1_S128.gs.bak` (neither version ever wrote anything).
- **`Diagnostics.gs`** (S53) live in the same project — alerts **only on failure**. Its silence is unreadable; that is why `Health.gs` exists.
- **`processor.py`** (clinic PC) md5 `8813a27db66c91628153c55912612ceb`, carries the D146 de-dupe.
- **Apps Script dashboard — the live project, not GitHub, is canonical (D160).** `WebApp.gs` is never touched (D34).

### Carried, all still true

The worker reads `.env` once, at import · absence of coverage is not absence of events · **a check that cannot fail is not a check** · two labels of the same key can disagree and both be right (D165) · `grep -c` exits 1 on a zero count — never chain with `&&` · restart at a moment **you** choose · one successful call does not verify a fix · **the runbook is not evidence** · install by candidate path, never overwrite the live file to test it · verify the rollback point at the moment of use · a constant offset is not a rate · **the record is not the disk, and the record loses** · the correct entry is sometimes `UNKNOWN` · a control on one path into a hazard is not a control on the hazard · a safety flag is a clinical signal about a patient, never a statement about staff accuracy · **0 cards refereed, so every accuracy claim is agreement, not accuracy** · expected values come from the artefact, never memory (D172) · a selftest is not a production verification (D174) · walked by hand twice, scripted the third time (D171).

**New this session:** a hygiene note is executable (**D176**) · a check must be calibrated to the clock of the thing it checks (**D177**) · a label is part of the instrument (**D178**) · a count without its scope is a wall, not a summary (**D179**) · an audit finds, it does not fix (**D180**) · **a version number is not evidence of a version** · **repeated command-and-paste is a missing instrument, not a diligent process.**

---

## §2 — BACKLOG

> **The rotation is NOT in this list.** Parked (KB §S128). Do not open a session with `rotate_callhook.sh status`.

### 🔴 TOP — finish the audit

1. **Audit pass 3 — `Dashboard.html`.** 2,738 lines, entirely unread. Where the key lives client-side, how it is passed, what the staff UI can reach. **Needs nothing but the export already in hand.**
2. **Audit pass 3 — classify F-2's sixteen silent `catch (e) {}` individually.** A swallowed `ntfy` push is correct; a swallowed outcome write is not. **They must never be fixed by one commit (D180).**
3. **Audit pass 4 — price every finding.** Lines changed, files touched, staff path disturbed?, rollback needs redeploy? Then decision sheets, one per fix.
4. **Which triggers are actually armed.** Not visible in code. One screenshot of Apps Script → Triggers closes it. Needed to know whether `sendFollowupSummary` and `rebuildCallFeed` really run — `Call_Feed`'s `lag=1d` is *consistent with* a live 21:30 trigger, not proof of one.

### 🟠 AUDIT FINDINGS — documented, untouched, awaiting decision sheets

5. **F-0** — `Call_Feed` published to the web. Deliberate; the clinic-PC tracker depends on it. **Do not disable.** ~3,000 patient mobiles + agent names public. One alternative exists (service-account pull) and it is **a trade, not a win**: it puts a service-account key on a Windows clinic PC, whose rotation is already an open Tier-A1 item.
6. **F-1** — `doGet` has no key; seven ungated globals. No exfiltration; unauthenticated write/send/quota as the deploying account.
7. **F-3** — `Followup_Outcomes` has three writers under a "one-writer tab" comment. Safe today by accident of layout.
8. **F-4** — `logOutcome` dead, `Outcomes_Log` never created, writer still browser-reachable and appends PHI.
9. **F-5/F-6/F-7** — two timezone sources · fifteen full-tab reads · dev scaffolding in production.

### 🟡 BUILD WORK — nothing needed from Lokesh

10. **`ANTHROPIC_API_KEY` in `.env`.** 111 chars, unaccounted. Rotate; find what wrote it; move it out. *Has an investigative half — do not open half-way.*
11. **Watchdog's two defects.** (a) coverage guard → exit 3 when the access log does not span the date; (b) `unquote()` before hashing in `mask_key()` (D165).
12. **`rotate_callhook.sh status` startup-line window.** Two minutes → last service start.
13. **Schedule the watchdog** — only after 11. It exits 1 on WARN.
14. **`wa_approve.py` → systemd service.** Currently nohup; dies on SSH close.
15. **Optional: a second `Health.gs` trigger at 13:00** with `maxLag: 0` on `Call_Durations`, to catch a receiver outage on its *first* afternoon rather than its second morning. Designed, not built.

### 🟢 OPEN QUESTIONS — cheap

16. What changed in Window 2 — one read-only command. Do not close it on `tail -3`.
17. 133 vs 132. Constant offset across 18 deliveries. One historical event.
18. Six unexplained bytes between `.env` and `.env.bak_20260707_162509`.

### OWNER TASK (~20 min) — everything downstream depends on it

19. **Referee the 32 cards in `Verdict_Review`.** Zero done. Until some are, every accuracy claim about the AI judge is *agreement*, not *accuracy*.

### Longer-running

20. Consolidate the call-transcript + Stage-3 AI layer (nightly timer; `call_transcription.py` GitHub commit; agent + Clinic ID missing from `Call_Verdicts`). **D158's join defect sits underneath it and should be fixed first.**
21. AKEY_14 rotation · service-account key rotation (Tier A1, Lokesh).
22. Stage 4 — doctor portal at `followup.dr-manoj.in/portal`, port 8099.
23. WABA authorizer fault (D120, Lokesh).
24. Track-1: Hindi **spelling** in `vitals_page.html` LIB strings · Step 7 reconciliation · living Clinic Data Map.

---

## §3 — DOCUMENT STATE

- **KB → `Clinic_Master_KB_SystemsRegister_v1_51.md`.** 171,032 bytes / 1,698 lines / CR 0. Six anchors asserted unique before edit; D121–D180 all present, verified by loop against the artefact. Adds **§S128B**, **D177–D180**.
- **Runbook → this file, v63.** Supersedes v62. **v61 §5 contained D176's defect and must never be followed.**
- **Audit → `Clinic_Callback_Tracker_AppsScript_Audit_v1_1.md`.** New canonical document.
- **Umbrella → `Dr_Manoj_Clinic_Umbrella_Architecture_v1_38.md`.** Module table and decisions list brought current.

---

## §4 — THE ROTATION PROCEDURE (D162) — PARKED

1. ✅ **DONE 08-Jul 23:38:00.** `PREV` = current.
2. ✅ **DONE 09-Jul 09:05:58.** New key into `CALLHOOK_SECRET`. WARN lines on the previous key are **the instrument, not a fault**.
3. ⏸️ **PARKED.** Update the MyOperator panel. No restart. **When resumed: generate a THIRD key first (D176).** Verify per the S124 standard — one real call **and** a re-check ≥1 hour later, same clinic day.
4. ⏸️ **PARKED, and blocked on 3 regardless (D173).** The step-4 command exists in no document, by design.

**Rollback, any time:** `bash /root/wa/rotate_callhook.sh rollback`. Or put the old key back in the panel — the VPS needs no touching.

---

## §5 — SESSION HYGIENE NOTES

> **⚠️ REWRITTEN UNDER D176.** The v61 version of this section named a command whose output is a live credential. It was executed and the key was disclosed. **No command whose output is a secret appears in this project's documents. Not as an instruction, not as a description of what was once done.**

- **Secrets are never displayed.** If a value must be retained, the **generating process** writes it to a mode-600 file on the box. `rotate_callhook.sh stage` already does this. **Do not read it back.** Both parties work with `key_<md5[:6]>` labels only.
- **Both keys are burned.** `key_db8972` and `key_ea20dd` have each appeared in a chat transcript. Resuming the rotation requires a **third** key.
- **`/root/wa/.rotate_s127_state`** (mode 600) holds the path of the current rollback backup. **Do not delete it.**
- **`.env` backups all contain live or historical secrets.** Mode 600, treat as secrets, do not delete: `.env.bak_20260707_162509` (forensic) · `.env.bak_s126_20260708_212316` · `.env.bak_s127_pre_rotation_20260708_232229` · `.env.bak_s127_step2_20260709_085801` (**the live rollback point**).
- **`.env.candidate_s127` should not exist.** If it reappears, a `stage` was run and not installed; it contains a live key.
- **The `Call_Feed` publish URL is a bearer credential.** It lives in `data\feed_url.txt` on the clinic PC. It must never be pasted into a chat, a document, or a screenshot. F-0 records what it exposes; it does not record the URL.
- **This session wrote no VPS file, touched no key, and restarted nothing.** One new Apps Script file was added, read-only, by paste.

---

**END OF RUNBOOK v63 — §5 is the last section. If §5 is absent, this file is truncated.**
