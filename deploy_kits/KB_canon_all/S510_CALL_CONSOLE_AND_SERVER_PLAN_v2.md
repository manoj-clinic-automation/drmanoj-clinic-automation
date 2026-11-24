# S510 — CALL CONSOLE REPLACES THE CALLBACK TRACKER · DATA ON THE SERVER · SERVER KEPT LIGHT — v2 (Fable's review)
*The parent, session 510 (Fable), 24-Nov-2026 IST. **Supersedes `S507_CALL_CONSOLE_AND_SERVER_PLAN.md`** (S507, Opus) — the owner's word 09:31 24-Nov: "review of plan by Fable as the next session's first thing." Nothing below is built yet; nothing live was changed in S507 or in this review. This is a whole document, not a delta: S507's content is carried, corrected where the review found it short.*

---

## 0 · What the review changed (read this if nothing else)

Reviewed against: the owner's rulings (§1), the approved mock-up v4 (read by a sub-agent, screen by screen), the 24-Nov code bundle (`calls_console.py`, `crontab.txt`, the systemd timers), the tracker engine `processor.py` as installed by S895, and the Fault Register (F-773, F-1626, F-1627).

1. **The AI already judges every call on the go** — S507's "judged once a day at 03:40" was the night sweep only. The D200 at-hangup pipeline (S140, `call-pipeline.service`, enabled and active) runs archive → transcription → verdict at every hangup, with one +10-minute retry; measured on the owner's own sheets, in his browser, numbers only (§2.5): **last 30 days, 591 recorded calls — 585 (99.0 %) judged within 5 minutes of hangup, median 48 s, p90 54 s; 4 inside 3 hours; 2 never.** The engine's 21:05 run therefore already sees the whole day's verdicts; no second pass is needed. **What IS left over (§2.5): 14 recordings all time (all ≤ 30 s) that the transcriber refuses, re-tried by the night sweep every night for ever — 1,530 failed rows in the sheet and 14 wasted API calls a night; 48 July calls transcribed but never judged (before the verdict stage covered them); and F-1627 is a misreading — the 1,374 August "FAILED" verdict rows are debris of a run that was repeated successfully (every August call is judged).** Step **A2** stops the loop and clears the debris; the on-the-go pipeline becomes the feed D1 reads.
2. **The engine's call rules are live code, not a stub** (S507 read the header comment, which is stale): `RESOLVE`/`DECLINE`/`ESCALATE` hide a patient from the list, `RESCHEDULE` hides for 2 days, a promised return re-surfaces after 3 days, 3 unanswered tries → "hard to reach". Feeding the AI's outcomes therefore CHANGES the 120-cap list the morning after. **D1 is split: D0 = a dry pass on a copy with 14 days of AI outcomes, the count of rows that would leave the list by rule, one line to him, his OK; then D1 live, forward only — no backfill of Sep–Nov verdicts into the engine** (a backfill would hide hundreds at once).
3. **The mapping AI → engine is fixed here (§3.2)**, including: a "not coming" with no reason read counts as *unclear* (stays) — 20 % of the AI's "not coming" came back anyway; only a reasoned not-coming declines. "Wrong number" stops the calling and raises reception's "check the number" (suggestion 3).
4. **The mock-up predates the AI ruling.** Its staff screens say "response chuniye call ke baad" and row 7 nags the manual form; the owner ruled 08:32 that the AI decides and 08:48 that staff involvement is avoided. **B0's refresh removes the response choosers from the staff screens** (staff see the AI's reading on their own card, with the existing "Galat hai?" dispute) and **row 7 is switched off for follow-up-list calls once D1 is live** (kept for the other calls the Call-ke-baad form covers); his look at B0 confirms.
5. **Twelve mock-up details the S507 text dropped are now in §3** — the auto-clearing rule, delivery at the moment of the punch, the evening slot = grace calls + everyone not picked twice, row 8's rest-of-day redirect, row 4's unknown-number flag and the retained WABA auto-reply, row 6 cleared by a reply OR a call, row 9's full summary screen, the settings box, the ladder's stages, the WA / Call back / Jawab buttons, the tab counts and the per-try history, suggestion 2 removed from the screens.
6. **B1 builds on code that already exists**: `calls_console.py` already carries staff routes behind the portal's staff gate — each person's own card (`/portal/console/api/mycard`), their own recordings of the last 7 days (`/myrec`, local copy first, else Drive, never transcripts), the dispute. "Doctor-only" is the owner's page, not the module. B1 is a staff page over those routes plus the list tabs — a smaller kit than S507 sized.
7. **Presence by punch inherits F-773 (OPEN since 07-Oct: the listener accepts a punch from any sender).** For notifications the harm is small (a message to someone absent), but **E1's kit closes F-773 first** (admit only the known machine; count refusals where the health page sees them) and adds the fallback: no punch by 09:30 or the machine silent (S830's watch) → the duty roster is taken as present and every notification says "by roster".
8. **P retires the Tracker PAGE for staff only.** The GAS triggers (Outbound_Log, Daily_Summary, the Followup_Outcomes WebApp) keep running until F1–F4 replace them — `console.db` is built from their sheets every 10 min. Said plainly so nobody switches a trigger off at P.
9. **Named staff become settings.** "Shivani the morning list, Alisha 4–6 pm" are roles with a name box on his console, never code.
10. **F1 (the call log onto a server table) moves up — right after B1**, because it is additive (server first, Sheet copy kept 30 days) and it de-risks the Sheets middle store before staff depend on the page daily. Until then B1 shows the reading's age and turns amber past 30 min.
11. **B2's WhatsApp goes through the server's own sender (`portal_inbox`), not the Tracker's GAS section** the owner named at 20:39 — the result is the same button on the staff page, and GAS retires at P.
12. **The Monday audit items (AF-43 sign-in throttle, AF-44 unread token, AF-45 `clinic_users.py` into the bundle) are step S after E2**, in his 20:17 order.

Nothing in his rulings is missing from the plan. The order stands as S507 set it, with D0 inserted, F1 moved up and S named.

---

## 1 · The owner's rulings (verbatim gist, IST) — D1054, D1055

| when | ruling |
|---|---|
| 23-Nov 20:17 | Order: the switch's watch → notifications for awaiting call-backs etc. that open on the relevant page for him, Shavez, receptionists → the Monday audit jobs. |
| 23-Nov 20:39 | The Callback Tracker has a WhatsApp section — use it; ntfy notifies and the tap opens the right place. Follow-up list "not started" is only one part: patients who do not pick up must be re-called in a structured way, with notifications. |
| 24-Nov 07:12 | The re-call is **same-day only, for the follow-up lists**. Incoming missed calls and WhatsApp: the v2 mock-up is OK. **Notifications go only to staff present that day.** |
| 24-Nov 07:31 | The attendance machine is working (presence = punch). Every caller and WhatsApp sender already gets an automatic WABA reply — no new patient message needed. |
| 24-Nov 07:35 | Complete mock-up wanted (incl. incoming missed etc.) → v4. |
| 24-Nov 08:25 | Suggestions: **skip 2**, explain 5, **others OK** (1, 3, 4, 5, 6). Analyse giving staff the **Call Console in place of the Callback Tracker**; only WhatsApp replying needs adding. |
| 24-Nov 08:32 | Follow-up answers: **leave it to the AI verdict**, not staff. |
| 24-Nov 08:48 | **Go.** Staff involvement to be avoided as far as possible. |
| 24-Nov 09:11 | Maximum data is the call recordings; assess the server; **replace the Callback Tracker with the Call Console**, with a plan to manage its data. |
| 24-Nov 09:18–09:25 | Assess all current and incremental load; a stepwise plan for a fresh session. |
| 24-Nov 09:31 | EOS-light; **review of the plan by Fable as the next session's first thing.** |

**Mock-up (approved shape, v4):**
```
https://claude.ai/artifact/8eCHsQg17igdtbqxaT4Rdj
```
Its screens are labelled "Callback Tracker"; the build puts the same tabs on the **staff Call Console** (B0 refreshes the labels and removes the response choosers, §0.4, for his look).

---

## 2 · What was found

### 2.1 The switch watch (23-Nov) — GREEN (S507)
Reception's 23-Nov exports reached the server ~20:50; the server's runner made the 24-Nov list at 21:05; the PC spare computed the same minute and sent nothing. Both: 120 of 352 due on the sheet, 232 wait.

### 2.2 How follow-up calling really runs (S507; counts only)
~7–10 outgoing follow-up calls a day against a 120 list; ~55–60 % answered; ~700 recordings a month in all. Staff file an outcome on ~70 % of answered calls; "No answer" is almost never marked. **The engine's own call read-back (`data/call_log.csv`) last changed 30-Jun** — staff moved to the Tracker's buttons (Followup_Outcomes, Google), which the engine does not read (**F-1626**, OPEN).

### 2.3 Whose reading comes true — AI vs staff (S507; 354 answered outgoing calls, 1-Sep → 16-Nov; returned within 14 days)
AI "coming" **41 %** · AI "not coming" 20 % · AI "call later" 7 % · staff "coming" 26 % · staff "not coming" 27 % · staff "not coming" + AI "coming" (37 calls) **56 %**. Weak spot: **AI UNCLEAR on 29 %** of answered calls. 1,374 of 4,887 verdict rows FAILED with an API 400 (**F-1627**, OPEN). Method: salted hashes in the device VM; nothing patient-level entered the cloud workspace (F-1629 rule).

### 2.4 The engine's call rules as installed (S510, `processor.py` S895/S911 bytes)
`RESOLUTION_MAP` (approved by the owner 22-Jun-2026): YES / Tt COMPLETE / MED HERE / MED OUTSIDE / DIKHA CHUKE → **RESOLVE** (hidden; a YES with no real return re-surfaces after `PROMISE_GRACE_DAYS` = 3) · NO → **DECLINE** (hidden) · LATER → **RESCHEDULE** (hidden `RESCHEDULE_DAYS` = 2; 3 LATERs → ESCALATE) · NOT PICK / SWITCH OFF → **RETRY** (3 in a row → **ESCALATE**, "hard to reach, your decision"). The overlay on the generated sheet is live (the "capture-only" comment in the file's header is stale). The 120 cap fills from the ladder's priority among what is not hidden.

### 2.5 The AI pipeline as it runs (S510 — code + the owner's sheets read in his browser, aggregates only)
**At hangup:** `call_hook_capture.py` drops a kick; `call_pipeline_worker.py` (`call-pipeline.service`, enabled, active in the 24-Nov bundle; polls 15 s, coalesces, flock) runs `call_recording_archive.py --date today` → `call_transcription.py` → `call_verdict.py`, then one retry kick +10 min; quiet window 01:55–04:05. **Night sweeps** (the floor): archive 02:00, transcription 03:00 (systemd timers), verdict 03:40 (cron). `portal_console.py --build` every 10 min 07–22 h (+ S856 kick) carries the verdicts to `console.db`. The engine runs at 21:05.
**Measured, last 30 days (591 recorded calls, incoming 470 / outgoing 121, the staff app's calls included):** transcript and verdict within 5 min of hangup **585 (99.0 %)** — median 48 s, p90 54 s; within 15 min 1; within 1 h 2; within 3 h 1 (the slowest 91 min, 21-Nov 18:42 — the retry caught it); never 2 (both 21–30 s clips). No call waited for the night sweep.
**All time (3,582 recordings since June):** transcribed 3,568 (99.6 %), judged 3,520 (98.3 %). The 62 unjudged: **14 never transcribed** — every one ≤ 30 s (3 of them ≤ 10 s), the transcriber returns an HTTP error, and **each carries > 20 failed rows**: the night sweep re-tries the same 14 every night (1,530 failed rows in Call_Transcripts; 14 API calls a night for nothing); **48 July calls** transcribed, no verdict row at all (the verdict stage's history starts after them); the **1,374 August "FAILED" verdict rows (API 400) are debris** — their calls were all judged by a later run (0 August calls unjudged), so **F-1627 as written is wrong** and is corrected at this close. Method: the sheets' CSV read by a script in the owner's signed-in browser; only counts and minutes left the page (F-1629 rule).

### 2.6 What already exists for staff in `calls_console.py` (S510)
`staff_gate` routes: `GET /portal/console/api/mycard` (own card, Hindi, every call they handled), `GET /portal/console/api/myrec/<jk>` (own recordings of the last 7 days through `/portal/rec`, local copy first else Drive; anyone else's 403; never transcripts), `POST /portal/console/api/dispute` ("Galat hai?") and his answer. The owner's page is doctor-gated; the module is not.

### 2.7 The server (S507, owner's paste 09:21 + measurements)
RAM 7.9 GB / 5.0 available · load 0.3–0.5 · disk 99 GB, 71 free · finance.db ≈ 25 MB/month · recordings ≈ 85 MB/month ≈ 1 GB/year · Call Console page 0.9–1.4 s, others 65–210 ms. **Verdict: no upgrade; ~3 years of headroom; revisit at disk > 70 % or RAM available < 1.5 GB.**

---

## 3 · The target

### 3.1 Staff use the Call Console, not the Callback Tracker
Staff page of `/portal/console` — **Hindi, phone-sized**, per-login gate: tabs with live counts **Aaj ki list · Dobara call · Shaam ki list · Missed calls · WhatsApp**; their **own** calls and recordings only (§2.6), **no transcripts**, no other staff's cards, nothing of his reviews. Buttons: **Call** (the portal's click-to-call door) and **WA** on follow-up rows; **Call back** on missed-call rows; **Jawab** (reply, in-page through `portal_inbox`'s sender/templates) and **Call** on WhatsApp rows. Dobara-call rows list each try with time and result ("1st try 10:05 nahi uthaya", "switch off", "aakhri try" on the 3rd); the Shaam row marks the final attempt. **No response chooser on any staff screen** (§0.4); the AI's reading shows on their own card with "Galat hai?". **A done item leaves its list by itself** — an answered call (either way), the patient calling in, or his WhatsApp reply; nobody presses "done"; tries are read from the MyOperator call log, the staff app's calls included (S935). The page shows the reading's time and turns amber past 30 min. Owner's view stays English and keeps everything.

### 3.2 Follow-up outcomes from the AI, not staff — and how they reach the engine
- Unanswered tries: from the call log (hook; NOT PICK / SWITCH OFF by the call's status).
- Answered calls: the AI reading of the recording, re-tuned (C1) to the ladder's answers. **Mapping to the engine's responses:** coming → YES · medicine here → MED HERE · medicine outside → MED OUTSIDE · already seen → DIKHA CHUKE · treatment complete → Tt COMPLETE · elsewhere / not interested → NO · call later → LATER · **not coming with no reason read → unclear (nothing written)** · wrong number → a new response WRONG NO → ESCALATE (stop) + reception's "check the number — correct from Docterz" line · a problem for the doctor → nothing on the ladder; the existing "to the doctor" line to Shavez/owner · **unclear or no recording → nothing written; the patient stays on the ladder unchanged. Nobody is asked. Nobody is dropped.**
- Forward only from D1's go-live; no backfill (§0.2). The at-hangup pipeline (§2.5) is the feed: a verdict lands within a minute of the call and the engine's 21:05 run reads the whole day.
- Suggestion 1: a patient's reply to the automatic WABA message after a missed try counts as reached (shows in row 6).
- Staff may mark the AI's reading wrong (the existing dispute); his Accept removes the outcome from the engine's log for that call.

### 3.3 The same-day re-call (follow-up list only)
Try 1 (morning list) → not picked → **Dobara call** due **+2 h** → not picked → **Shaam ki list, 16:00–18:00** = the grace-period calls **plus everyone not picked twice today**, today's unanswered first → not picked → the day counts **once** as "not picked" (one NOT PICK row to the engine); tomorrow the existing ladder (Due today → Grace 1–3 d → Missed 4–10 → Probable dropout 11–60 → Expired > 60; 3 not-picked days → hard to reach, his decision). No 4th try the same day. Missed incoming callers whose call-back is not picked join the same re-call. The re-call gap and tries per day are settings.

### 3.4 Notifications (mock-up v4 rows 1–9)
ntfy ("ntfy · Clinic"; row 7 through the Clinic app as today), each tap opening the **exact Console section/item** (signed in). Only staff **present = punched in today**; **what was waiting reaches her the moment she punches**; on leave = nothing; when no punch has come by 09:30 or the machine is silent → the duty roster counts as present and the message says "by roster" (§0.7). Order: whose job (the morning-list role from 08:00; the evening-slot role 4–6 pm — names as settings) → other reception present → Shavez → owner. Duty hours Mon–Sat 09:00–20:30, Sun 09:00–14:30; one notification per item per stage; several due together = one.

| # | waiting | first | then |
|---|---|---|---|
| 1 | day's list not started | 10:00 reception present | 11:30 Shavez |
| 2 | re-call due | +2 h the caller | +1 h Shavez |
| 3 | evening slot opens | 16:00 the evening role / reception present | 17:00 Shavez |
| 4 | missed incoming not spoken to (unknown-number flag "purana patient nahi"; how many times he rang; his WABA auto-reply goes as today) | 30 duty min | 60 duty min Shavez (`callback_clock.py` S796 sends today — only the landing changes) |
| 5 | call-back not picked | re-call as 2/3; still unreached at day's end → counted in row 9 | — |
| 6 | WhatsApp unanswered — no reply AND no call (the instant new-message alert stays as today); cleared by a reply OR a call | 20 duty min | 45 duty min Shavez |
| 7 | Call ke baad form not filled | as today (ring_outcome); **off for follow-up-list calls once D1 is live** (§0.4) | — |
| 8 | nobody at reception | 10:00 Shavez; **for the rest of the day every reception notification goes to Shavez**; Shavez absent too → the owner, one English line "No phone staff present today — N follow-ups waiting" | — |
| 9 | owner's day end | 20:30 (Sun 14:30), only if something is left — English summary, opening his own day-summary screen (the unreached on top): follow-ups reached X of Y; not picked after 3 tries → tomorrow; missed callers reached X of Y with the unreached; WhatsApp answered/waiting, slowest reply; notifications sent / acted on within the hour, "Shavez stepped in N times"; staff present | — |

**Settings on his console** (each notification on/off): re-call gap 2 h · tries per day 3 · evening slot 16:00–18:00 · list-not-started 10:00 / backup 11:30 · missed caller 30/60 min · WhatsApp 20/45 min · owner message 20:30 · the role names.

### 3.5 Accepted suggestions to carry
1 WABA reply = reached · 3 never-connecting number → "check the number — correct from Docterz" for reception · 4 staff see their own day on Aaj ka kaam · 5 weekly line: calls waiting under the 120 cap by stage ("232 last night"; to decide whether to raise the cap on quiet days) · 6 notifications acted on within the hour, per staff. **2 skipped — B0 removes it from the screens.**

---

## 4 · The data plan — the server primary

| data | today | target |
|---|---|---|
| call log (Call_Durations) | call_hook → Google Sheet | **F1 (after B1):** server table first; Sheet copy for 30 days |
| recordings | MyOperator → Drive month folders (+ the archive's local copies) | **server month folders** + Drive + MyOperator (3 copies); monthly copy to the SSD; **not in the nightly bundles**; kept indefinitely (~1 GB/yr) |
| transcripts, AI verdicts | Sheets | server tables (small → in the nightly DB copy) |
| outcomes | GAS → Followup_Outcomes | server table (AI + call log), fed to the engine's `call_log` (D1) |
| Outbound_Log, Daily_Summary | GAS | server equivalents; **only then** the GAS triggers retired (§0.8) |
| console.db | rebuilt from Sheets every 10 min | built from the server tables (faster; fixes the ~1 s page) |

Each move: write to the server first, keep the Sheet copy, prove 30 days, then stop the Sheet. The Tracker page is retired for staff only after a clean week on the Console; its tiles change only on his word.

---

## 5 · Keeping the server light (unchanged from S507)

| # | action | how |
|---|---|---|
| L1 | **Nightly server record** — disk by folder, RAM available, load, biggest processes → his health page; warn at disk 80 %, RAM < 1 GB, load high for an hour | new read-only job + one freshness leg |
| L2 | **/root/backups 6.5 G** — inventory read-only first, then a keep-N rule | after L1's first inventory |
| L3 | **`.bak_*` and kit copies** in /root/finance, /root/deploy, /root/_retired | keep the last 2 baks per file and anything pinned; older to a dated archive, removed on his word |
| L4 | **recordings** on the server by month, outside the nightly bundles | step F2 |
| L5 | **Call Console speed** | server tables (F4) + the leaner staff page (B1) |
| L6 | **failed AI verdicts** (F-1627) — a misreading: the rows are debris, every August call is judged | done inside A2 (the one-off removes the rows) |

---

## 6 · The stepwise build — SUPERSEDED for the kits and their order by `S510_CALL_CONSOLE_ROADMAP_v1.md` §3–§4 (24-Nov; the roadmap carries every component, the kits A1–A4 · B0–B2 · C1 · D0–D1 · E0–E2 · S · P · F1–F6 · L, the phases and the gates). The table below is kept as the S507/S510 design record only.

| step | what | depends on | owner sees |
|---|---|---|---|
| **R0** | **this review** — done 24-Nov (S510) | — | this paper, a few lines in chat |
| A0 | the S498 chat's 22:00/08:30 checks if he passes them on; the 24-Nov bundle confirmed S935 | — | — |
| **A1** | **L1 nightly server record** + the console's "server N · PC N · same" line (one kit, read-only) | — | one health line |
| **A2** | **the pipeline's leftovers** (§2.5): a transcription that fails 3 times on a clip ≤ 30 s is written once as `skipped — too short` and never re-tried (the verdict treats it as no recording → nothing written); clips ≤ 10 s not sent at all; the 14 marked now; the 48 July calls marked not-judgeable; the 1,374 August debris rows removed by a one-off (backup of the tab first); a freshness leg "AI judged within 15 min" on the health page | — | one health line |
| **B0** | mock-up v4 → the **staff Call Console** screens (Hindi): labels, no response choosers, suggestion 2 out, the WA / Call back / Jawab buttons, tab counts, try history | — | the mock-up, his OK |
| **C1** | **AI re-tune** to the ladder's answer set (§3.2); re-judge Sep–Nov follow-up calls; validate by return-within-14 d in the device VM on salted hashes (gate: "coming" ≥ 41 % and **unclear ≤ 15 %**) | — | one result line |
| **B1** | **staff Call Console** over the existing staff routes (§2.6) — role gate, Hindi, five tabs, own recordings, no transcripts, Call/WA buttons, reading age; side by side with the Tracker | B0 | the page |
| **F1** | call log onto a server table (Sheet copy kept 30 d) | B1 | — |
| **B2** | **WhatsApp inside the staff Console** (`portal_inbox` sender/templates; Jawab) | B1 | — |
| **D0** | **the dry pass on a copy**: 14 days of the at-hangup pipeline's outcomes through the mapping, rows that would leave the list by rule, one line (no new judging pass — the pipeline already judges within a minute, §2.5) | C1 | one line, his OK |
| **D1** | **outcomes server-side + the engine feed**, forward only: call-log tries + AI outcomes → `call_log` (restores next-call-day / 3-strike / LATER / YES re-confirm; F-1626); row 7 off for follow-up calls | D0 | — |
| **E1** | **F-773 closed** (known machine only, refusals counted) · presence by punch with the roster fallback · **same-day re-call** · notifications 1–9 (ntfy Click → Console sections; `callback_clock`'s landing moved; row 9's owner screen) · the settings box | B1, B2 | his phone |
| E2 | suggestions 3, 4, 5, 6 | E1 | console lines |
| **S** | Monday audit: **AF-43** (sign-in throttle + failed-sign-in line + `bump_epoch()` in `set_password()`), **AF-44** (`FINANCE_MARG_TOKEN` unread → remove; F-456's review date), **AF-45** (`clinic_users.py` into the nightly bundle) · **F-1613** (tracker code into the bundle) | — | one line |
| **P** | parallel week → the Tracker **page** retired for staff (tiles on his word); GAS triggers stay (§0.8) | B1–E1 a clean week | one decision |
| F2–F4 | recordings → transcripts/verdicts → console.db from server tables; Outbound_Log/Daily_Summary replaced; then the GAS triggers retired | P (F2 may start after A1) | — |
| L2/L3/L6 | backups/baks clean-up; failed verdicts | A1's inventory | one line each |

**Also open:** S881 (sheet 7 as a voucher document) · F-1510 · F-1627 (L6). **Reminders:** the packs page (D713) · BL Computers (the attendance machine) · section 8 only on his tick (D1011) · HDFC's November card statement · the three September Free X-ray taps.

**Files the build touches (all the parent's):** `/root/portal/calls_console.py`, `portal.py` (gates/tiles), `portal_inbox.py` (reuse), `callback_clock.py`, `ring_common.py` (push); `/root/wa/portal_console.py`, `call-hook/call_hook_capture.py`, `recordings-archive/{call_recording_archive,call_transcription,call_verdict}.py` + their timers/cron; `/root/attlistener_v2.py` (F-773, E1); `/root/followup_tracker/` (the `call_log` feed — `processor.py` read whole first; the PC's copy kept byte-equal); `/root/finance/owner_console.py`, `freshness_legs.json`. Read the newest bundle's bytes before any patch (F-472); `/root/followup_tracker/` is not in the bundle until F-1613.

*S510 · 24-Nov-2026 · Fable · v2.2 (§6 superseded by the roadmap; v2.1: the pipeline measured on the owner's word 10:35, "AI must be judging calls on the go") · supersedes the S507 plan · numbers at the close.*
