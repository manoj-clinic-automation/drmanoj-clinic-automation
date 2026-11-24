# S510 — THE CALL CONSOLE SYSTEM — ROADMAP v1 · every component · the kits · the rollout
*The parent, session 510 (Fable), 24-Nov-2026 IST. The owner's word 10:51: "make a final Roadmap, all components of call console, and plan the kits and the rollout properly, but don't miss details." Companion of `S510_CALL_CONSOLE_AND_SERVER_PLAN_v2.md` (the rulings, the target screens, the data plan — that paper is the WHAT; this one is the WHAT-EXISTS, the kits and the ORDER). Built from the 24-Nov code bundle, the S895–S911 kits, the GAS project's CURRENT files and the owner's rulings since 01-Nov. Nothing below is built in S510.*

---

## 0 · The shape of the system in one paragraph

A patient is due → the **engine** (the PC's tracker, now on the server) makes the day's **Call Sheet** from reception's Docterz exports → it is pushed to the Google tab **Followups_Today** (minus Do_Not_Call) → staff open the **GAS Callback Tracker** page (today) and press **Call** → `call_api` dials through MyOperator (agent first, then patient) → MyOperator's webhook reaches **call_hook_capture**, which writes **Call_Durations** and kicks the **AI pipeline** (archive → Sarvam transcript → Claude verdict, 48 s median) → every 10 minutes **portal_console** folds nine sheet tabs into **console.db** → the owner reads **/portal/console**; staff read their own card on **Aaj ka kaam**; **callback_clock**, **ring_hook/ring_outcome** and the **WhatsApp ladder** act on the same stores. What staff type as outcomes goes to **Followup_Outcomes** — which the engine never reads (F-1626); the engine's only feedback is a nightly GAS **Call_Feed**. The target: staff on a server **Call Console**, outcomes from the AI, the engine fed, the same-day re-call, notifications by presence, the data on the server, the GAS project retired piece by piece.

---

## 1 · THE COMPONENTS — as they stand, and their fate

Fate codes: **KEEP** (unchanged) · **CHANGE** (a kit touches it) · **REPLACE** (a server piece takes its job) · **RETIRE** (switched off after its replacement proves) · **PARKED** (the owner's word). Kit codes are §3's.

### 1.1 Telephony and capture
| # | component | where / trigger | does | fate |
|---|---|---|---|---|
| C1 | MyOperator IVR "80" + the "93" number (forwarded; also the WABA number) | vendor | all outgoing through "80"; incoming on both | KEEP |
| C2 | `wa/call_api.py` | `call-api.service` 127.0.0.1:8097; `POST /call` (X-Call-Key) | click-to-call (OBD: agent's phone first, then the patient); `reference_id` = `<row>-<epoch><hex>` → becomes the hook's `client_ref_id`; 7 agents hard-coded (ext 10–16) | KEEP (B1 reuses the same door; the agent map stays until the roster is a table — F-phase) |
| C3 | `wa/call-hook/call_hook_capture.py` 70c3d257 (S935) | `call-hook.service` 127.0.0.1:8098; `/mo-callhook` | raw jsonl per day (the recovery truth); **Call_Durations — the one writer**; OBD + incoming + (S935) the staff app's `oneway` as `OUT-<session>`; drops a `.kick` per hangup | CHANGE at **F1** (server table first, Sheet copy 30 d) |
| C4 | `call-hook/callhook_write_probe.py` | cron 08:45 | one synthetic call through the public URL, reads the sheet back | KEEP; re-pointed at F1 |
| C5 | `call-hook/callhook_watchdog.py` (403 detector) | **not scheduled anywhere** | — | decide at A2: schedule daily or retire (F at the close) |
| C6 | `portal/ring_hook.py` | `ring-hook.service`; MyOperator's second webhook (dial/answered/end) | caller-name pop-up on staff phones; the "क्या हुआ?" card at hang-up; `ring_outcomes.db`; 30-s sweeper | KEEP (E1 reads its stores for "answered"/"missed") |
| C7 | `portal/ring_agents.json` + `ring_agents_build.py` | manual | phone → login map | KEEP; folded into the roster table at F6 |

### 1.2 Recordings and the AI
| # | component | trigger | does | fate |
|---|---|---|---|---|
| C8 | `recordings-archive/call_pipeline_worker.py` (D200) | `call-pipeline.service`, polls 15 s | at every hangup: archive → transcribe → verdict for today; one retry +10 min; quiet 01:55–04:05 | KEEP (measured: 99 % judged < 5 min) |
| C9 | `call_recording_archive.py` | timer 02:00 + worker | MyOperator `/search` → mp3 → Drive folder → **Call_Recordings** (one writer); Join Key `phone10_startunix` | CHANGE at **F2** (server month folders + Drive; manifest to a table) |
| C10 | `call_transcription.py` | timer 03:00 + worker | Sarvam `saaras:v3` (sync ≤ 30 s, batch above) → Drive txt → **Call_Transcripts** | CHANGE at **A2** (give-up rule) and **F3** (table) |
| C11 | `call_verdict.py` v2.1-S141, `claude-haiku-4-5` | cron 03:40 + worker | blind judge (transcript + direction + talk seconds) → **Call_Verdicts** (Audit sheet); vocabulary §1.9; claim join from Followup_Outcomes −10 min…+28 h | CHANGE at **C1** (the ladder's answer set, prompt v3) and **F3** |
| C12 | `flag_investigator.py` (D239) | cron */30 09–20 + 20:00 | talk-but-no-recording rows → asks MyOperator, heals with one kick; "take to Lokesh" after 3/7 d | KEEP |
| C13 | `daily_digest.py` (D236) | cron 11:00 pulse, 21:30 digest | e-mail to his personal Gmail | KEEP; its figures from tables at F3; the Sunday section stays unbuilt unless he asks |
| C14 | `verdict_review.py` (Stage 3b) | cron 21:00 | harvests Doctor_Verdicts, redraws Verdict_Review — **which nothing reads since Track G** | RETIRE at **L7** (after the owner's word; the harvest half kept if his sheet answers still matter) |
| C15 | `make_force_keys.py` (S143 one-off) + `force_keys.txt` | none | **hard-codes 41 full patient numbers**; rides in the nightly code bundle (plain tar) and the SSD mirror | RETIRE NOW — **A3** (an F at the S510 close) |
| C16 | `call_verdict_BACKUP_S123_pre_join_redesign.py` | dead file | — | A3 moves it to `_retired` |
| C17 | `wa/rec_cache/` (1 GB, 60 d) + `/portal/rec/<jk>` | portal | local copy first, else Drive link; staff through `myrec` | KEEP; becomes the month-folder store at F2 |

### 1.3 The engine and the Docterz road
| # | component | trigger | does | fate |
|---|---|---|---|---|
| C18 | reception PC / manojz Docterz exports → Drive "Docterz exports"; owner upload door `/finance/console/docterz-reports` (S897) | staff after 21:00; S916 from manojz | the two daily reports + the clinical data report | KEEP |
| C19 | `finance/docterz_pickup.py` (S443…S868), `docterz_taken_notice.py` (S915), `docterz_missing_alert.py` (S811) | cron */15; 2-59/5; 21:45 + 08:15 | takes the exports into `docterz_export`; tells him; alerts him when missing | KEEP |
| C20 | `/root/followup_tracker/` — `server_runner.py` → `tracker/docterz_pickup.py` → `processor.py` 64824680 (the PC's bytes + S908 stable sort + S911 cap line), 3.11 venv | cron */5 (OFF-gated — **switched 10:43 23-Nov**) + 08:00 | the ladder (§1.8), the 120 cap, `Staff_Action_Today_<date>.xlsx`, the CSV ledgers (`call_log.csv` unfed since 30-Jun) | CHANGE at **D1** (the feed), **F5** (Call_Feed from the server); **F-1613** first (into the nightly bundle) |
| C21 | `wa/followup_receiver.py` (8100) + `fu_push_on_arrival.sh` + `push_followups_vps.py` (`clinic-followup-push`) | on arrival; timer 22:00/07:00/11:00 | workbook → **Followups_Today** (minus **Do_Not_Call**, the human tab) + **Followups_Settled** | KEEP until **F4** (console.db from the workbook/table directly); Do_Not_Call becomes a table with his page at F4 |
| C22 | `push_patient_mirror.py` (08:00) / `push_patient_join.py` | cron | **Patient_Master** tab (replace-only); salted fingerprints to the box | KEEP until F4 |
| C23 | `followup_tracker/pc_upload_watch.py` (S897) | cron */10 | red leg if the PC still sends after the switch | KEEP through the seven days' watch; retire after |
| C24 | `finance/docterz_ingest.py` | cron */10 | the workbook's Day Revenue → finance.db | KEEP |
| C25 | the PC spare (`_SPARE_MODE.txt`, `docterz_pickup.py` 9e0bf2e1) | PC task | computes, sends nothing | KEEP as the spare; its retirement is his word after the watch |

### 1.4 The Google Sheets — every tab, its writer, its readers, its fate
| tab (sheet) | writer today | readers | fate |
|---|---|---|---|
| Call_Durations (Tracker) | call_hook (C3) | console builder, digest, flag_investigator, probe, GAS duration gate | **F1** → table `call_log_raw`; Sheet copy 30 d, then stop |
| Call_Recordings | archive (C9) | transcription, verdict, console, GAS (🎧) | **F2** → table |
| Call_Transcripts | transcription (C10) | verdict, digest, console | **F3** → table |
| Call_Verdicts (Audit) | verdict (C11) | console, digest, verdict_review | **F3** → table |
| Verdict_Review, Doctor_Verdicts (Audit) | verdict_review (C14) | digest reads Doctor_Verdicts | L7 |
| Followup_Outcomes | GAS WebApp/Callconsole + ring_outcome mirror | verdict (claim join), digest, GAS review | **D1** → table `call_outcome` (AI + staff disputes); the GAS writer stops at **P**; ring_outcome's mirror re-pointed at D1 |
| Followup_Escalations, K_Strikes | GAS | GAS, portal_gist | **E2/P** → the Console's "to the doctor" line + the 3-strike rule in the server's ladder; GAS stops at P |
| Followups_Today, Followups_Settled | push_followups_vps (C21) | console builder (fu_all, no_shows), GAS worklist | **F4** |
| Do_Not_Call | the owner by hand | push_followups_vps | **F4** → table + his page (today "asked_not_to_call" never writes it — a gap, closed at D1: an AI/staff "asked not to call" raises his one-tap "add to Do-not-call") |
| Patient_Master | push_patient_mirror (C22) | archive, console, GAS | **F4** |
| Agents | the owner | console, ring_outcome, GAS | **F6** → roster table (with `call_api`'s agent map and `ring_agents.json`) |
| Call_Feed (published CSV) | **GAS CallField.gs 21:30** (14 days outgoing + incoming-missed) | the engine (`feed_url.txt` → `outbound_log.csv` → reconcile / reinstate) | **F5** — the server writes the same CSV from `call_log_raw` to a local path; `feed_url.txt` → file; GAS trigger off after 7 equal nights |
| Callbacks_Today, Callbacks_Archive, Daily_Monitor, Daily_Report_Log, Daily_Summary | GAS Main.gs/Monitor.gs/Sheets.gs | console builder reads **Daily_Summary**; portal_gist reads Callbacks_Today, K_Strikes, Call_Feed | **F6** — the builder computes its own daily summary from `call_log_raw` (it already has `myop_daily`); portal_gist re-pointed; GAS triggers off |
| Outbound_Log | nobody (superseded by Call_Feed) | console builder (header says so) | builder's read dropped at F6 |
| WA_Inbox (WA sheet) | the VPS relay / receiver | GAS chat, portal_inbox "out" rows | KEEP until the inbox is the one store (outside this roadmap) |

### 1.5 The owner's console and its stores
| # | component | fate |
|---|---|---|
| C26 | `wa/portal_console.py` (one writer of `console.db`; cron */10 07–22, `--with-myop-reconcile --with-transcripts --days 60`) + `console_kick.py` (S856, ~20 s after a call) | KEEP; its sources move tab by tab (F1–F6); the page's 0.9–1.4 s falls when the join is local |
| C27 | `portal/calls_console.py` (S818) — `/portal/console`: the strip, Needs you, follow-up sections (one open row per patient; Grace/Overdue calls counted after due, F-1322; a visit from half the advised period closes a row, D893), the people timelines (calls + WhatsApps, icons), WhatsApp awaiting (wa-mark Done / Not a patient), staff cards (net missed first; reception mobile credited to the one phone staff on duty, F-1168), review buttons (`call_review.db`), disputes; duty windows from `/root/staff_master.csv` + `/root/punches.csv` | CHANGE at **B1** (the staff page over its staff routes), **E1** (re-call sections, presence), **E2** |
| C28 | `console_reviews.db` (old console dispositions, send-backs) | KEEP read-only; retire the old console views at L7 on his word |
| C29 | `portal/portal.py` — gates (`login_required`, `doctor_required`, `wa_required`), the "Calls & WhatsApp" tile group (Call Console · Call Tracker · Call ke baad · WhatsApp Inbox · WhatsApp messages · Send WhatsApp · GMB Review Assist · Follow-up Tracker (pc_only) · Clinic Gist), `tile_grants.json` v47, `/portal/rec`, `/portal/go/call-tracker` (mints the GAS SSO pass) | CHANGE at **B1** (the staff tile), **P** (the Tracker tile's fate — his word only, D997) |
| C30 | `wa/portal_gist.py` → "Clinic Gist" tile | re-pointed at F6 |

### 1.6 The staff's surfaces today
| # | component | fate |
|---|---|---|
| C31 | **GAS Callback Tracker page** (`Dashboard.html` v18.28f; web app ANYONE_ANONYMOUS behind a key / the portal's SSO pass; 60-s refresh): KPIs · New leads · Today's calls · Needs a callback now (guided incoming outcome flow) · Resolved / Handled · **Today's follow-up calls** (Call with the 15-s duration gate, No answer 3/day → the doctor's Unreachable band, outcome dropdown, one-tap K mode in Hindi, Save + 10-s undo) · Settled · Recent WhatsApp (Chat / Reply / Call; free text inside 24 h through the VPS `/wa-send` relay) · Clinic Team; owner extras: Escalations, Unreachable review, 3rd-strike WhatsApp (template `drmanoj_followup_due` after exactly 3 cross-day no-answers), Outcome review, mails ×3/day, health mail 09:00, sweep 21:30, follow-up summary, URGENT ntfy on surgery enquiries | **REPLACE** by B1/B2/E1/E2 (§4 maps every function); **RETIRE for staff at P**; its triggers off at F5/F6 |
| C32 | `calls_console` staff routes: `mycard` (own card on Aaj ka kaam), `myrec` (own recordings, 7 d), `dispute` | KEEP; B1 builds on them |
| C33 | `ring_outcome.py` — the "Kya hua?" card and the **Call ke baad** list (`/portal/ring/list`, D693/D696; booking followed to the Docterz visit; mirrors to Followup_Outcomes/Escalations) | KEEP; mirror re-pointed at D1; row 7 off for follow-up calls once D1 is live |
| C34 | `callback_clock.py` (S796): missed callers not spoken to → Web Push 30 duty-min (shivani, alisha, reception) / 60 (shavez) / closing (manoj), landing `/portal/go/call-tracker` | CHANGE at **E1** (landing → the Console's Missed tab; presence rule; one engine for all nine rows) |
| C35 | `portal_push.py` + `ring_common.push_user` — **the Clinic app's own Web Push** (VAPID, `push_subs.json`, ≤ 6 devices per login, tap opens a URL) | KEEP — **the decision (§5.1): this is the staff notification channel; ntfy is the fallback for a login with no subscribed device** |
| C36 | `portal/wa_ladder.py` + `wa_ladder_send.py` (S808): the patient WhatsApp lists (tomorrow / post-visit / appointment / due1 / due5 / overdue), STOP list, **every switch OFF** at his word, ceiling 150, test-to-owner first | KEEP; the due-date switches wait on the engine's server data (they do now) — his word |
| C37 | `portal/portal_inbox.py` (S871) — his WhatsApp Inbox: send text/image/document/audio inside 24 h, templates, canned replies, Call, media links, send log → MyOperator ticket 691386 | KEEP; **B2 reuses its sender** for the staff page's Jawab (the inbox page itself stays his, D: 19-Oct) |
| C38 | `portal_followups.py` (retired tile S816; page answers) | RETIRE at L7 |
| C39 | the automatic WABA replies (post-call templates; the "hi" greeting with the "80" number) | KEEP (ruling 07:31 24-Nov) |

### 1.7 Presence, attendance, duty
| # | component | fate |
|---|---|---|
| C40 | `attlistener_v2.py` → `/root/punches.csv`; `att_silence_watch.py` (S830); `staff_master.csv` duty times; DUTY_MAP (shared with Sanjeevni) | **E1 closes F-773** (known machine only) and reads punches for presence; roster fallback when silent |

### 1.8 The ladder as coded (what D1 feeds)
Due Today (0) · Grace 1–3 · Actionable Missed 4–10 · Probable Dropout 11–60 · Expired > 60. `RESOLUTION_MAP`: YES / Tt COMPLETE / MED HERE / MED OUTSIDE / DIKHA CHUKE → RESOLVE (hidden; a YES with no real return re-surfaces after 3 d) · NO → DECLINE · LATER → RESCHEDULE (2 d; 3 → ESCALATE) · NOT PICK / SWITCH OFF → RETRY (3 → ESCALATE "Unreachable / Watch"; STRIKE_LIMIT 3 → Hard-to-Reach tab). One row per mobile+name+diagnosis, latest due wins; freshest first; the 120 cap after the 3-strike split (winnable buckets first, dropouts oldest first fill the room); `CALL CAP` line (S911). **Feedback today: only the Call_Feed CSV (reconcile / reinstate) and a FILLED Call Sheet (which the server never passes).**

### 1.9 The AI's vocabulary as coded (what C1 re-tunes)
Outgoing: coming, out_of_town, on_medication, cant_communicate, dikha_chuke, problem, close_followup, not_interested, treatment_elsewhere, wrong_number, asked_not_to_call. Incoming: resolved_on_call, appointment_booked, info_given_will_act, needs_callback, escalated, cant_communicate, will_come, enquiry_only, no_action. Always UNCLEAR. Flags postop / complaint / urgent / surgery / clinical / conduct. The GAS K-mode words (k_coming, k_not_coming, k_call_again, no_answer, problem) map onto these (S140 equivalences). **The ladder needs a smaller, sharper set (plan v2.1 §3.2); C1 keeps the old names as sub-reasons so history stays comparable.**

---

## 2 · THE TARGET — one page (the detail is plan v2.1 §3)
Staff: a Hindi, phone-sized **Call Console** page — Aaj ki list · Dobara call · Shaam ki list · Missed calls · WhatsApp, own calls and recordings, Call / WA / Call back / Jawab, no response choosers, items clear themselves. Owner: the console as today, plus the re-call sections, the day-summary screen, the settings box. Outcomes: the AI's reading → the engine's `call_log` the same minute (forward only); staff see the reading and may dispute. Same-day re-call: +2 h, then the 16–18 h slot, one NOT PICK a day. Notifications: nine rows by presence (punch), Clinic-app push first, ntfy fallback, each opening the exact section. Data: server tables first, Sheets kept 30 days per step, recordings on the server by month. GAS: retired function by function (§4).

---

## 3 · THE KITS — in order (each: walk + control red + live-shape + rehearsal + cold review; his publish + one server line; undo named)

| kit | name | files (all the parent's) | depends | proof | his action | owner sees |
|---|---|---|---|---|---|---|
| **A1** | SERVER_RECORD — L1 nightly server record + the console's "server N · PC N · same" line | NEW `/root/finance/server_record.py` + cron 02:50; `owner_console.py`; `freshness_legs.json` | — | read-only; walk on made-up df/free output | publish + 1 line | one health line |
| **A2** | PIPELINE_LEFTOVERS — give-up after 3 failures on a clip ≤ 30 s (`skipped — too short`, never re-tried; the verdict treats it as no recording); clips ≤ 10 s not sent; the 14 marked; the 48 July calls marked not-judgeable; the 1,374 August debris rows removed (tab backed up to an owner-only CSV first); leg "AI judged within 15 min"; `callhook_watchdog` scheduled daily or retired | `call_transcription.py`, `call_verdict.py`, `freshness_legs.json`, crontab | — | synth on copies of the three tabs' CSV shapes; live-shape = counts before/after | publish + 1 line | one health line |
| **A3** | PHI_OUT_OF_CODE — `make_force_keys.py` + `force_keys.txt` + the S123 backup out of `/root/wa/recordings-archive/` into `/root/_retired/S510/` with the TRIPLES list blanked; the code-bundle excludes `_retired`; `NO_PHONE_NUMBERS.py` run over the live folder | the three files; `state_backup/code_bundle.py` exclude list | — | grep for 10-digit runs = 0 in the bundled folders | publish + 1 line | — (an F closed) |
| **A4** | F-1613 — `/root/followup_tracker/` (code only) into the nightly code bundle | `state_backup/code_bundle.py` | — | tomorrow's bundle lists it; pins verified | publish + 1 line | — |
| **B0** | STAFF_CONSOLE_MOCKUP — mock-up v4 → the staff screens: labels, no response choosers, suggestion 2 out, WA / Call back / Jawab, tab counts, try history, the AI's reading line + "Galat hai?" | a design artifact | — | his look | "ok" | the mock-up |
| **C1** | AI_RETUNE — prompt v3 for the ladder's answer set (coming · not coming + reason · call later · problem for the doctor · wrong number · unclear; old names kept as sub-reasons); re-judge Sep–Nov outgoing follow-up calls into a SHADOW column set (not Final); validate return-within-14 d in the device VM on salted hashes (gate: coming ≥ 41 %, unclear ≤ 15 %); report | `call_verdict.py` (prompt + columns), a one-off re-judge | — | the gate numbers | publish + 1 line | one result line |
| **B1** | STAFF_CONSOLE — `/portal/console/staff` over the existing staff routes: role gate (phone staff + Shavez; the owner's `?as=`), Hindi, five tabs with counts, own calls/recordings, Call (existing door) and WA buttons, per-row try history from `call_log_raw`/Call_Durations, the reading's age (amber > 30 min), the AI's reading + dispute; tile "Call Console" for staff (grants v48); side by side with the Tracker | `calls_console.py`, `portal.py`, `tile_grants.json` | B0 | walk per role on a made-up console.db; the owner's page byte-equal; cold review | publish + 1 line | the page |
| **F1** | CALL_LOG_TABLE — the hook writes `call_log_raw` (finance.db or `/root/wa/calls.db`, one writer) first, the Sheet second; the builder reads the table; probe re-pointed | `call_hook_capture.py`, `portal_console.py`, probe | B1 | 30 days table = sheet (a nightly compare leg) | publish + 1 line + a hook restart | — |
| **B2** | STAFF_WHATSAPP — the WhatsApp tab's Jawab through `portal_inbox`'s sender (text + canned replies + templates inside/outside the window), Call; the chat view read-only otherwise; the inbox page stays his | `calls_console.py`, `portal_inbox.py` (a callable, no route change) | B1 | walk with a stubbed sender; one live reply to his own number | publish + 1 line | — |
| **D0** | ENGINE_FEED_DRY — `call_outcome` table (AI + hook tries + disputes, one writer `call_outcome_feed.py`); the mapping of plan §3.2; a dry pass on a copy of `/root/followup_tracker/data/`: 14 days of outcomes through `processor.ingest_call_sheet()`'s own path → rows that would leave the list by class; one line to him | NEW `call_outcome_feed.py`; processor read only | C1 | the dry pass's counts; control = a copy with no feed | his OK on the line | one line |
| **D1** | ENGINE_FEED_LIVE — the feed writes `call_log.csv` through the engine's own ingest (forward only from go-live; a WRONG NO response added to `RESOLUTION_MAP` → ESCALATE; `asked_not_to_call` raises his one-tap Do-not-call); `ring_outcome`'s mirror re-pointed to `call_outcome`; the verdict's claim join reads `call_outcome`; row 7 off for follow-up calls (setting) | `call_outcome_feed.py` + cron */5; `processor.py` (one map entry; the PC's copy byte-equal); `ring_outcome.py`; `call_verdict.py` | D0 | Replay 2 unchanged without a feed; a 3-day shadow where the feed writes to a copy and the console shows "would hide N" | publish + 1 line | the console line "hidden by the AI today: N" |
| **E0** | PUNCH_DOOR — F-773 closed: the listener admits the known machine only, counts refusals on the health page; presence reader `presence.py` (punched-in today, punch-out, duty hours, roster fallback when the machine is silent / no punch by 09:30) | `attlistener_v2.py`, NEW `presence.py`, `freshness_legs.json` | — | replay of a week's punches; a spoofed sender refused | publish + 1 line + listener restart | one health line |
| **E1** | RECALL_AND_NOTIFY — the same-day re-call (Dobara +2 h, Shaam 16–18 with the grace calls; one NOT PICK a day to D1's table); `notify_engine.py` = ONE scheduler for rows 1–9 (presence from E0; role names and every time a setting; Clinic-app push first, ntfy fallback; Click → the exact section; one per item per stage; `callback_clock`'s rows folded in, its cron retired); the owner's day-summary screen; the settings box on his console | NEW `notify_engine.py` + cron */5 07–21; `calls_console.py`; `callback_clock.py` (retired by the kit); `ring_common.py` | B1, B2, D1, E0 | a simulated day on made-up stores (every row fires once, to the right present person); live-shape on a copy of today | publish + 1 line | his phone; the summary screen |
| **E2** | SUGGESTIONS — 3 "check the number" (never-connecting) · 4 own day on Aaj ka kaam (the card's new lines) · 5 the weekly under-cap line · 6 acted-within-the-hour per staff; the "to the doctor" line replaces GAS Escalations; the 3-strike rule and the Unreachable band on the server (the engine already escalates at 3) | `calls_console.py`, `notify_engine.py`, `owner_console.py` | E1 | walks | publish + 1 line | console lines |
| **S** | MONDAY_AUDIT — AF-43 sign-in throttle + failed-sign-in line + `bump_epoch()`; AF-44 the unread token out; AF-45 `clinic_users.py` into the bundle | `portal.py` / `clinic_sso.py`, units, bundle script | — | walks | publish + 1 line | one line |
| **P** | PARALLEL_WEEK → RETIRE THE TRACKER PAGE FOR STAFF — seven clinic days with both pages; the gate: every follow-up try, outcome and WhatsApp reply of the week visible on the Console with no staff complaint; then the Call Tracker tile masked for staff (grants), the GAS Followup_Outcomes writer stops (staff no longer there); the GAS **triggers stay** | `tile_grants.json` | B1–E2 | the week's counts, side by side | his one decision | one decision |
| **F2** | RECORDINGS_ON_SERVER — month folders under `/root/wa/recordings/YYYY-MM/`, outside the nightly bundles; Drive and MyOperator stay as copies 2 and 3; monthly copy to the SSD; `rec_cache` retired; manifest table | `call_recording_archive.py`, `portal.py` `_serve_rec`, `state_backup` excludes | A1 | 30 days three copies equal by md5 | publish + 1 line | — |
| **F3** | TRANSCRIPTS_VERDICTS_TABLES — tables first, Sheets 30 d; the builder, digest, flag_investigator read the tables | `call_transcription.py`, `call_verdict.py`, `portal_console.py`, `daily_digest.py` | F1 | 30-day equality leg | publish + 1 line | — |
| **F4** | LISTS_AND_PATIENTS_ON_SERVER — the builder reads the workbook / engine ledgers directly; `Followups_Today/Settled` and `Patient_Master` pushes stop after 30 d; **Do_Not_Call → table + his page** (one tap from D1's "asked not to call") | `portal_console.py`, `push_followups_vps.py`, `push_patient_mirror.py`, NEW `dnc.py` | P | equality leg | publish + 1 line | his Do-not-call page |
| **F5** | CALL_FEED_FROM_SERVER — `call_feed_build.py` writes the 14-day CSV from `call_log_raw` to `/root/followup_tracker/data/feed.csv`; `feed_url.txt` → the file; 7 nights equal to GAS's Call_Feed, then the GAS 21:30 trigger off | NEW `call_feed_build.py` + cron 21:00; `feed_url.txt` | F1 | 7 equal nights | publish + 1 line | — |
| **F6** | GAS_TRIGGERS_OFF — the builder's own daily summary (from `myop_daily` + `call_log_raw`); `portal_gist` re-pointed; the roster table (Agents + `call_api` map + `ring_agents.json`); then every GAS trigger removed (Main, Monitor, Health, Diagnostics, sweep, summary mail) — the digest's figures cover the mails; the web app left deployed but unlinked for 30 days, then undeployed | `portal_console.py`, `portal_gist.py`, NEW `roster.py`; his Apps Script (built-in browser, before/after hashes) | F5 | the console unchanged with the tabs frozen | his one word per trigger set | the Calls tiles without the Tracker |
| **L2/L3/L7** | LIGHT — `/root/backups` keep-N after A1's inventory; `.bak_*` and kit copies archived; `verdict_review` retired, the old console views and `portal_followups` retired | — | A1 | counts | one line each | one line each |

Kit numbers are taken from `board/_numbers` when each is started (never here). Every kit's cold review by a second reader; a NOT SAFE is fixed before the publish; the number gate (`NO_PHONE_NUMBERS.py`) before every publish.

---

## 4 · THE ROLLOUT — phases and gates

| phase | kits | gate to pass before the next phase | undo |
|---|---|---|---|
| **0 · Ground** (this week) | A1 A2 A3 A4 | the health line shows the server record; the leftover loop stopped (0 failed rows a night); 10-digit runs 0 in the bundled code; the tracker in the bundle | each kit's `--undo` |
| **1 · Staff Console beside the Tracker** | B0 → B1 → F1 → B2 | staff open it from their tile for 3 clinic days; the owner's page byte-equal; the table = the sheet 3 days | grants back; hook `--undo` |
| **2 · The AI feeds the engine** | C1 → D0 → D1 | C1's gate (coming ≥ 41 %, unclear ≤ 15 %); D0's line OK'd; D1's 3-day shadow shows no row hidden that a human would have called | the feed cron off; `call_log.csv` restored from the kit's backup |
| **3 · Re-call, presence, notifications** | E0 → E1 → E2 → S | a simulated day green; the first live day: every row's first and second notification reached the right present person (the owner's summary says so) | `notify_engine` off (callback_clock's line back) |
| **4 · The week, then the page** | P | the gate in §3 P | the tile un-masked |
| **5 · Data home** | F2 → F3 → F4 → F5 → F6 | each: 30 days equal (7 nights for the feed) | the Sheet path is still written for 30 days — switch back by one setting |
| **6 · Light** | L2 L3 L7 | — | the archive kept 90 days |

**Standing rules through every phase:** nothing live rebuilt without his OK; the GAS page keeps working for staff until P; the GAS triggers keep running until F5/F6; the PC stays the spare; patient data never through the cloud workspace (D656); page text into the chat filtered (F-1629); the two publishes a day at most around the clinic's hours.

**Sessions, roughly:** phase 0 one session · phase 1 two · phase 2 two (C1 is the long one) · phase 3 two · phase 4 the week itself · phase 5 four short sessions spread over the 30-day proofs · phase 6 one. About twelve working sessions over five to six weeks of calendar, most of it waiting on proofs.

---

## 5 · DECISIONS MADE HERE (technical calls, stated once)
1. **Staff notifications ride the Clinic app's own push** (`ring_common.push_user`, already on every staff phone, opens the exact URL); ntfy is the fallback for a login with no subscribed device. The owner's words "ntfy notifies and the tap opens the right place" are met either way; the existing channel is the proven one.
2. **The engine is fed through its own ingest** (`ingest_call_sheet()`'s keys: Obligation_Key + Call_Date + Response + Called_By), never by writing `call_log.csv` directly — one writer stays the engine. Called_By = "AI" for the AI's readings, the agent's name for hook tries.
3. **No bulk backfill** of historical verdicts into the engine (it would hide hundreds at once); forward only, after the dry pass and the 3-day shadow.
4. **Call_Feed stays a CSV the engine reads from a local file** (its reconcile/reinstate code untouched) — the server writes it; GAS's copy stops after seven equal nights.
5. **The GAS project retires function by function**, never by one switch: page for staff at P; Followup_Outcomes writer stops with it; Call_Feed at F5; mails, summaries, health, sweep at F6; the web app undeployed 30 days later.
6. **Do_Not_Call** stays the human tab until F4 (the push applies it); D1 only raises his one-tap when the AI hears "asked not to call".
7. **Staff never see transcripts** (standing rule 07-Nov); recordings of their own calls only; the owner's page unchanged in content.

---

## 6 · FAULTS SURFACED BY THIS INVENTORY (minted at the S510 close)
- `make_force_keys.py` with 41 full patient numbers in the live code folder and in the nightly code bundle (plain tar on Drive, mirrored to the SSD) — OPEN until A3.
- `callhook_watchdog.py` scheduled nowhere — decide at A2.
- `verdict_review.py` rebuilds a sheet nothing reads (21:00 nightly) — L7.
- F-1626 refined: staff outcomes never reach the engine by any path; the only feedback is the nightly GAS Call_Feed — D1 and F5.
- F-1627 corrected: the 1,374 August rows are debris; every August call is judged — A2 removes them.
- The S507 plan's "judged once a day at 03:40" was the night sweep only; the at-hangup pipeline (D200) judges 99 % within 5 minutes — recorded, nothing to build.
- `asked_not_to_call` never writes Do_Not_Call — a gap closed at D1/F4.
- The GAS web app is deployed to anyone with the key (ANYONE_ANONYMOUS + key / SSO pass) — closed by its retirement; until then unchanged.

*S510 · 24-Nov-2026 · Fable · v1 · numbers at the close.*
