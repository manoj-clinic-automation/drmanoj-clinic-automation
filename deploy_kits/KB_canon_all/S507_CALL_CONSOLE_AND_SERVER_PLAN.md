# S507 — CALL CONSOLE REPLACES THE CALLBACK TRACKER · DATA ON THE SERVER · SERVER KEPT LIGHT
*The parent, session 507 (Opus), 23–24 Nov 2026 IST. The build plan for the fresh sessions. Nothing below is built yet; nothing live was changed in S507. **First act of session 510: Fable reviews this plan (the owner's word, 09:31 24-Nov).***

---

## 1 · The owner's rulings (verbatim gist, IST) — D1054, D1055

| when | ruling |
|---|---|
| 23-Nov 20:17 | Order: the switch's watch → notifications for awaiting call-backs etc. that open on the relevant page for him, Shavez, receptionists → the Monday audit jobs. |
| 23-Nov 20:39 | The Callback Tracker has a WhatsApp section — use it; ntfy notifies and the tap opens the right place. Follow-up list "not started" is only one part: patients who do not pick up must be re-called in a structured way, with notifications. |
| 24-Nov 07:12 | The re-call is **same-day only, for the follow-up lists** (that is the gap). Incoming missed calls and WhatsApp: the v2 mock-up is OK. **Notifications go only to staff present that day.** |
| 24-Nov 07:31 | The attendance machine is working (presence = punch). Every caller and WhatsApp sender already gets an automatic WABA reply — no new patient message needed. |
| 24-Nov 07:35 | Complete mock-up wanted (incl. incoming missed etc.) → v4. |
| 24-Nov 08:25 | Suggestions: **skip 2**, explain 5, **others OK** (1, 3, 4, 5, 6 accepted). Analyse giving staff the **Call Console in place of the Callback Tracker** as their patient-communication page; only WhatsApp replying needs adding. |
| 24-Nov 08:32 | Follow-up answers: **leave it to the AI verdict**, not staff. |
| 24-Nov 08:48 | **Go.** Staff involvement to be avoided as far as possible (non-recorded calls etc. — staff cannot help). |
| 24-Nov 09:11 | Maximum data is the call recordings; assess the server; **replace the Callback Tracker with the Call Console**, with a plan to manage its data. |
| 24-Nov 09:18–09:25 | Assess all current and incremental load and whether the specs carry everything without lag; assimilate everything into a stepwise plan for a fresh session. |
| 24-Nov 09:31 | EOS-light; **review of the plan by Fable as the next session's first thing.** |

**Mock-up (approved shape, v4):**
```
https://claude.ai/artifact/8eCHsQg17igdtbqxaT4Rdj
```
Its screens are labelled "Callback Tracker" — the build puts the same tabs on the **staff Call Console** (step B0 refreshes the labels for his look).

---

## 2 · What was found (S507, read-only)

### 2.1 The switch watch (23-Nov) — GREEN
Reception's 23-Nov exports reached the server ~20:50; the server's runner made the 24-Nov list at 21:05 (inbox file 21:05, origin server; `pc_upload_watch` OK). The PC spare computed the same minute and sent nothing (`_SPARE_MODE.txt` present). **Both: 120 of 352 due on the sheet, 232 wait** (identical CALL CAP lines). Content-hash comparison: left to the S498 chat's 08:30 check.

### 2.2 How follow-up calling really runs (Call_Durations, Followup_Outcomes, Call_Verdicts; counts only)
- Outgoing follow-up calls: Sep 296 · Oct 254 · Nov (to 23rd) 141 → **~7–10 a day against a 120 list**; ~55–60 % answered; ~700 recordings/month in all (incoming + outgoing).
- Staff file an outcome on ~70 % of answered calls; **"No answer" is almost never marked** (4–9 a month against 100+ unanswered).
- **The engine's own call read-back (`data/call_log.csv`, 145 rows) last changed 30-Jun** — staff moved to the Tracker's buttons (`Followup_Outcomes`, Google), which the engine does not read. So the multi-day ladder's call rules (NOT PICK → next call day; 3 strikes → Hard to reach; LATER → 2 days; YES → re-confirm in 3 days) have had **no input since July** (**F-1626**, OPEN). Step D restores the feed.

### 2.3 Whose reading comes true — AI vs staff (354 answered outgoing calls, 1-Sep → 16-Nov; did the patient return within 14 days?)
| reading | came back |
|---|---|
| AI "coming" | **41 %** |
| AI "not coming" | 20 % |
| AI "call later" | 7 % |
| staff "coming" | 26 % |
| staff "not coming" | 27 % |
| staff "not coming" + AI "coming" (37 calls) | **56 %** |

Staff marks do not predict returns; the AI's do. **Weak spot: AI UNCLEAR on 29 % of answered calls** (28 % of those returned). Also: 1,374 of 4,887 verdict rows (mostly Aug incoming) FAILED with an API 400 — never re-judged (**F-1627**, OPEN). Method: per-call rows hashed in the owner's browser (salted SHA-256, 10 hex), joined in the device VM with `visit_ledger.csv`; no patient number or name entered the cloud workspace; the hash file was deleted.

### 2.4 What the Call Console depends on
`/portal/console` (calls_console.py, doctor-only) reads `/root/wa/console.db`, rebuilt every 10 min (+ S856 kick ~20 s after a call) by `wa/portal_console.py` **from Google Sheets**: Call_Durations · Call_Recordings · Call_Transcripts · Patient_Master (Tracker sheet), Call_Verdicts (Call Audit sheet) — all written by **our server's** programs (call_hook_capture, call_recording_archive, call_transcription, call_verdict) — plus **Outbound_Log** and **Daily_Summary**, written by the GAS project (Monitor.gs / Callconsole.gs). The Tracker **page** plays no part. Followup_Outcomes is written only by the GAS WebApp.

### 2.5 The server (owner's read-only paste 09:21 IST 24-Nov + S507 measurements)
- **RAM** 7.9 GB, **5.0 GB available**, swap 0 used · **load 0.30–0.52** · up 38 days · disk **99 GB, 28 GB used, 71 GB free**.
- Biggest memory users: mariadbd 0.35 GB (website), each gunicorn ~0.07–0.13 GB, python jobs ~0.06–0.09 GB.
- Disk by folder: /root/backups **6.5 G** · /root/finance **4.4 G** (finance.db only 62 MB — the rest exports, scans, `.bak_*`) · /root/deploy **2.4 G** · /root/labdata 1.3 G · /root/wa 1.2 G · /home 0.65 G · /usr/local/lsws 0.6 G · /root/followup_tracker 0.55 G · xray_ocr 0.43 G · assetapp 0.39 G · _retired 0.38 G · mysql 0.31 G · gutlog 0.17 G · health_mirror 0.09 G · /var/log 0.08 G; OS ~8 G.
- **finance.db growth**: 18.7 MB (15-Sep) → 37.3 MB (15-Oct) → 62.2 MB (23-Nov) ≈ 25 MB/month.
- **Recordings**: ~700/month × ~120 KB (8 kHz MP3, ~85 s avg) ≈ **85 MB/month ≈ 1 GB/year**; all since July ≈ 0.5 GB. Today on Drive (month folders) + MyOperator's cloud; not on the server.
- Page times (built-in browser, network floor ~65 ms): most pages 65–210 ms; **Call Console ~0.9–1.4 s**; portal home 0.2–1.0 s.
- **Verdict: the server carries everything planned (staff Console for 6–8 users, recordings on disk, the AI per call) comfortably. No upgrade.** Estimated growth ≤ ~25 GB/year (mostly backups/scans/exports) → ~3 years of headroom. Revisit only if disk > 70 % or RAM available < 1.5 GB.

---

## 3 · The target (what the build delivers)

### 3.1 Staff use the Call Console, not the Callback Tracker
Staff version of `/portal/console` — **Hindi, phone-sized**, gated per login: tabs **Aaj ki list · Dobara call · Shaam ki list · Missed calls · WhatsApp**; their **own** calls and recordings only; **no transcripts** (standing rule), no other staff's cards, nothing of his reviews; **Call** button through the portal's existing click-to-call door; **WhatsApp reply** inside the page (reuse `portal_inbox` send / template / call — not a new sender). Owner's view stays English and keeps everything.

### 3.2 Follow-up outcomes from the AI, not staff
- Unanswered tries: from the call log (MyOperator, incl. the staff app's calls since S935).
- Answered calls: the AI reading of the recording, re-tuned to the ladder's answers — **coming · not coming (medicine here / outside · already seen · treatment complete · elsewhere · not interested) · call later · a problem for the doctor · wrong number · unclear**.
- **Unclear or no recording → the patient stays on the ladder unchanged. Nobody is asked. Nobody is dropped.**
- Suggestion 1 (accepted): a patient's reply to the automatic WABA message after a missed try/call counts as reached.
- Staff see the AI's reading on their own card and may mark it wrong (the existing dispute flow).

### 3.3 The same-day re-call (follow-up list only)
Try 1 (morning list) → not picked → **Dobara call** due **+2 h** → not picked → **4–6 pm slot** (with the grace-period calls, today's unanswered first) → not picked → the day counts **once** as "not picked"; tomorrow the existing ladder. No 4th try the same day. Missed incoming callers whose call-back is not picked join the same re-call.

### 3.4 Notifications (mock-up v4 rows 1–9)
ntfy (staff have it), each tap opening the **exact Console section/item** (signed in). Only staff **present = punched in today**; waiting items reach her at her punch; on leave = nothing. Order: whose job (Shivani morning list from 08:00; Alisha 4–6 pm) → other reception present → Shavez → owner. Duty hours Mon–Sat 09:00–20:30, Sun 09:00–14:30; one notification per item per stage; several due together = one.

| # | waiting | first | then |
|---|---|---|---|
| 1 | day's list not started | 10:00 reception present | 11:30 Shavez |
| 2 | re-call due | +2 h the caller | +1 h Shavez |
| 3 | evening slot | 16:00 Alisha / reception present | 17:00 Shavez |
| 4 | missed incoming not spoken to | 30 duty min | 60 duty min Shavez (`callback_clock.py` S796 sends today — landing changes) |
| 5 | call-back not picked | re-call as 2/3 | — |
| 6 | WhatsApp unanswered | 20 duty min | 45 duty min Shavez |
| 7 | Call ke baad form | unchanged (ring_outcome) | — |
| 8 | nobody at reception | 10:00 Shavez, else owner | — |
| 9 | owner's day end | 20:30 (Sun 14:30), only if something is left — English summary incl. notifications acted on within the hour (suggestion 6) | — |

Every time is a setting on his console (and on/off per notification).

### 3.5 Accepted suggestions to carry
1 WABA reply = reached · 3 never-connecting number → "check the number" for reception · 4 staff see their own day on Aaj ka kaam · 5 weekly line: calls waiting under the 120 cap by stage (probable dropouts never called; went past 60 days uncalled) · 6 notifications acted on within the hour, per staff. **2 skipped.**

---

## 4 · The data plan — the server primary

| data | today | target |
|---|---|---|
| call log (Call_Durations) | call_hook → Google Sheet | server table first; Sheet copy for 30 days |
| recordings | MyOperator → Drive month folders | **server month folders** + Drive + MyOperator (3 copies); monthly copy to the SSD; **not in the nightly bundles**; kept indefinitely (~1 GB/yr) |
| transcripts, AI verdicts | Sheets | server tables (small → in the nightly DB copy) |
| outcomes | GAS → Followup_Outcomes | server table (AI + call log), fed to the engine's call read-back |
| Outbound_Log, Daily_Summary | GAS | server equivalents; then the GAS triggers retired |
| console.db | rebuilt from Sheets every 10 min | built from the server tables (faster; fixes the ~1 s page) |

Each move: write to the server first, keep the Sheet copy, prove 30 days, then stop the Sheet. The GAS Tracker is retired only after staff have used the Console a clean week; its tiles change only on his word.

---

## 5 · Keeping the server light

| # | action | how |
|---|---|---|
| L1 | **Nightly server record** — disk by folder, RAM available, load, biggest processes → his console/health page; warn at disk 80 %, RAM < 1 GB, load high for an hour | new read-only job + one freshness leg (no live change to anything else) |
| L2 | **/root/backups 6.5 G** — inventory read-only first (what, how many, how old), then a keep-N rule | after L1's first inventory |
| L3 | **`.bak_*` and kit copies** in /root/finance, /root/deploy (2.4 G), /root/_retired | keep the last 2 baks per file and anything pinned; older to a dated archive, then removed on his word |
| L4 | **recordings** on the server by month, outside the nightly code/DB bundles | step F |
| L5 | **Call Console speed** | built from server tables (step F) + leaner page for staff (step B) |
| L6 | **failed AI verdicts** (1,374 rows, API 400 — F-1627) | re-judge or mark not-judgeable; small |

---

## 6 · The stepwise build (fresh sessions; one kit at a time; each: walk + control red + rehearsal + cold review; his publish + one server line)

| step | what | owner sees |
|---|---|---|
| **R0** | **Fable reviews this plan** (his word 09:31 24-Nov) — gaps, order, risks; the plan revised in place before any build | the revised plan, briefly |
| **A0** | Open: the S498 chat's 22:00/08:30 checks; the 24-Nov bundle confirms S935 | — |
| **A1** | **L1 nightly server record** (read-only, smallest, gives real growth) | one console line |
| **B0** | Refresh mock-up v4 → the **staff Call Console** screens (Hindi), for his OK | the mock-up |
| **C1** | **AI re-tune** — the ladder's answer set; re-judge Sep–Nov follow-up calls; validate by return-within-14 d (gate: "coming" ≥ 41 % and **unclear ≤ 15 %**); report before going live | one result line |
| **B1** | **Staff Call Console** — role gate, Hindi, tabs, own recordings, no transcripts, Call door; side by side with the Tracker | the page |
| **B2** | **WhatsApp inside the staff Console** (portal_inbox send/template reuse) | — |
| **D1** | **Outcomes server-side + engine feed**: call-log tries + AI outcomes → `call_log` the engine reads (restores next-call-day / 3-strike / LATER / YES re-confirm; F-1626) | — |
| **E1** | **Same-day re-call** + presence by punch + notifications 1–9 (ntfy Click → Console sections; callback_clock's landing moved) + settings | his phone |
| **E2** | Suggestions 3, 4, 5, 6 | console lines |
| **P** | **Parallel week** → retire the Tracker for staff (tiles on his word) | one decision |
| **F1–F4** | Data onto the server: call log → recordings → transcripts/verdicts → console.db from server tables; Outbound_Log/Daily_Summary replaced; Sheets kept 30 days per step | — |
| **L2/L3/L6** | Backups/baks clean-up and failed verdicts, after A1's inventory | one line each |

**Also open (unchanged from START_HERE_507):** Monday audit — **AF-43** (sign-in throttle + failed-sign-in line + `bump_epoch()` in `set_password()`), **AF-44** (`FINANCE_MARG_TOKEN` unread → remove; review date on F-456), **AF-45** (`clinic_users.py` into the nightly bundle); F-1613 (tracker code into the bundle); the console's "server N · PC N · same" line; S881; F-1510. Reminders: the packs page (D713), section 8 on his tick, HDFC's Nov statement, the three September Free X-ray taps.

**Files the build touches (all the parent's):** `/root/portal/calls_console.py`, `portal.py` (gates/tiles), `portal_inbox.py` (read/reuse), `callback_clock.py`, `ring_common.py` (push); `/root/wa/portal_console.py`, `call-hook/call_hook_capture.py`, `recordings-archive/{call_recording_archive,call_transcription,call_verdict}.py`; `/root/followup_tracker/` (engine call_log feed — read `processor.py` RESOLUTION_MAP / ESCALATE_AFTER first); `/root/finance/owner_console.py`, `freshness_legs.json`. Read the newest bundle's bytes before any patch (F-472); `/root/followup_tracker/` is not in the bundle until F-1613.

*S507 · 24-Nov-2026 · D1054, D1055 · F-1626 – F-1629 (board `_numbers` v2111). In canon at the S507 close.*
