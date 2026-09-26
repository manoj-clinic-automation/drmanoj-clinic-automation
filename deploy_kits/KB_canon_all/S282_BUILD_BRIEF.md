# S282 BUILD BRIEF — the parent · for Session 284 · written at the S282 close, 26-Sep-2026

*One document instead of ten. Read this after `START_HERE_SESSION_284.md`. Everything below was read from the real files at this close; line numbers are from `deploy_kits/GAS_CURRENT/ClinicCallbackTracker/` (placed 21/22-Sep) and the 26-Sep 01:35 VPS bundle.*

## 0 · THE MANDATE — the owner's words, 26-Sep-2026

*"caller card is a very small build compared to this. So we can make it operational first and the WhatsApp functionality in the current setup. And then we proceed to these other tasks."* — and then: *"do EOS here complete so that we do all these builds with full context in the fresh chat in this project."*

**So, in order (D630):**
1. **The caller card, D590 steps 2 and 3** — one kit.
2. **WhatsApp in the current Google tracker** — Reply for every staff member with *sent by*; the sender's number in the ntfy WhatsApp alert; a failed alert not lost.
3. Then — **only after he confirms** — the Callback Tracker to the VPS (his direction: server-first, side by side, retire the Google tracker once proven, Google for backup only; *"We'll discuss"*). Then Vitals & Plan (F-598). Then F-595 and F-596 (the assistant's own).

What he already said yes to (S366 README, 21/22-Sep): *Appointment booked* tops the known-patient list; the 10-minute second pop-up — yes; full numbers to staff and owner on the card.

## 1 · THE CALLER CARD — what exists (S366 → S370, live)

- **Receiver:** `/root/portal/ring_hook.py` `a3cd0466…` (243 lines), unit `ring-hook.service`, OLS context `/ring-hook`. `handle_event()` line 85: `call.dial_begin` → push *ring* card to the dialled login (line 123, tag `call-<sid>`, ttl 60, url `TRACKER_URL`); `call.answered` (~130) → the others get *"ne utha liya"* (line 144); `call.end` / `call.summary` (~150) → a missed call stays **❌ Missed** (line 163, ttl 600, `requireInteraction`, `renotify`), a bridged call closes. `_push(login,payload,session_id,kind)` line 68. Every event body is written whole to `/root/portal/ring_state/YYYY-MM-DD.jsonl` (0700). Routes: `/ring-hook` (GET/POST, gated by `_gate_ok()` line 179), `/ring-hook/health`, `/ring-hook/test`.
- **Helpers:** `ring_common.py` `4344b592…` — `lookup_caller()` 144 (finance.db, by the mobile fingerprint), `caller_card()` 179, `send_push()` 210, `push_user()` 233, `agent_for()` 115 (ring_agents.json: extension → login). `portal_push.py` `576ae269…` (subscribe, `/portal/push/diag`). `portal_sw.js` `ab728b08…` (served at `/portal/sw.js`, scope `/portal`, F-623).
- **Now carried nightly** (S416) — `portal_sw.js` and `ring-hook.service` from the 27-Sep bundle. **`http_ece.py` does not exist on the box (F-637)**; the push encryption is in `ring_common.send_push` and its imports — read it before touching push.

## 2 · STEP 2 — THE OUTCOME AT HANG-UP (the design, decided)

**Where an outcome is stored.** The Google tracker writes every incoming outcome through `saveIncomingOutcome(key,p)` (WebApp.gs **1290**) as one row of `Followup_Outcomes` with the 18 headers `FU_OUTCOME_HEADERS` (WebApp.gs **885**): When · Key (`IN_<10-digit>_<yyyyMMdd>`) · Patient · Mobile · Section `Incoming` · Outcome `in_<resolution|reason>` · Source · Days · Expected Date · Detail · Handled By · Agent Ext · Settle (`settle`/`retry`/`escalate`) · Identity · Reason · Channel · For Whom · Clinic ID — and an escalation also appends to `Followup_Escalations`. Labels: `FU_OUTCOME_LABEL` (WebApp.gs **1590**) — `in_appointment_booked`, `in_resolved_on_call`, `in_info_given`, `in_needs_callback`, `in_escalated`, `in_will_come`, `in_enquiry_only`, `in_no_action`, `in_not_relevant`, `in_cant_communicate`. **The Apps Script has no `doPost`** — nothing outside the tracker page can call it.

**Decided (the assistant's technical call, D630's direction):** the pop-up's outcome is written **on the VPS first** — a new table beside the ring state (the store the VPS tracker will grow from) — and **mirrored the same minute into `Followup_Outcomes` as a row identical in shape** by the VPS's own Google Sheets access (the clinic-followup-push job already writes that spreadsheet with the venv's `gspread`; read its credentials path, never print it). So the Google tracker, its summary cross-tab and its escalation queue see the outcome exactly as if typed there; the VPS already holds it for the move.

**The screens (staff-facing, Hindi, as the owner ruled):**
- At `call.end` for an answered call: the card turns to **"Kya hua? — outcome chuniye"**; a tap opens a small page on the portal, `/portal/ring/outcome?s=<session>` (signed-in portal session; the card's session id and the caller already known).
- **Known patient:** *Appointment booked* first, then the tracker's own incoming set in its own order. **Unknown number:** the D225 new-lead set of seven, *Appointment booked* first. Escalation choices (doctor / urgent) behave exactly as the tracker's `IN_ESCALATE_*` maps — read those maps and copy the codes, never re-invent them.
- **Missed call:** no outcome page; the ❌ card stays as today.
- **10 minutes, no outcome:** one second push, *"Outcome baaki — <name / last 4>"*, same tag so it replaces rather than stacks; after that, the item waits in the tracker as today.
- An outcome already typed in the tracker for that `IN_<phone>_<day>` key closes the pop-up's reminder (read the sheet's row before re-pushing).

## 3 · STEP 3 — PER-PERSON COUNTS

From `ring_state` (calls rung / answered per login) and the outcome table: per staff member per day — answered · outcome logged · outcome missing · appointments booked. One small doctor-only panel on the portal and one line in the Clinic Gist. Numbers only, no patient detail.

## 4 · WHATSAPP IN THE CURRENT GOOGLE TRACKER

- **Reply for every staff member.** Gated to the doctor today in four places: `sendReply` WebApp.gs **616** (`dashRole_(key) !== 'full'`), `checkWindow` **591**, and Dashboard.html **1032, 1118, 3032, 3045**. Open to every signed-in staff role; `agentInfoForKey_()` (WebApp.gs **133**) gives the staff name — record it as *sent by* on the reply row and show it in the thread. Placed in the owner's signed-in browser (D577) as **a new version of the existing deployment — never a new deployment**; `GAS_CURRENT/ClinicCallbackTracker/` updated in the same breath with its `SUMS.md5` (D583).
- **The sender's number in the ntfy alert.** `notifier/notifier_wa.py` (live = repo `08219ae8`): the alert text is built at lines **266–287** and never includes `r[iPhone]`; add it (full number — ntfy goes only to the owner's and staff's own devices, as he ruled for the caller card). **A failed push is not lost:** `ntfy_push`'s return is ignored at 281/283/304/307 — do not advance the processed-state past a failed push; retry on the next run.
- **F-640:** the tracker web app 404s for the owner's own Google account (staff fine). Not fixed by this work; the VPS tracker removes it. Say so if he asks.

## 5 · THE TRACKER TO THE VPS — what was sized with him (no build until he confirms)

Side by side, no break: the VPS reads the same exports the Google tracker reads; staff keep the Google tracker until the VPS one is proven on real days; then retire it. Recordings stay at MyOperator (links, not copies). Backup: a Sheet mirror every 10 minutes during the parallel run, then an hourly Drive copy and the nightly encrypted bundle. Capacity last measured ~S230: 2 vCPU, 7.7 GB RAM, 99 GB disk, ~15 % used, load ~0 — the tracker's data is small. **Measure the box again before building.**

## 6 · FIRST ACTS AT THE OPEN (in this order, after Phase 0)

1. Take session **284** from the board (reserved by this close).
2. **Read `portal.py` whole from the live bytes** (drift 7, over the line) — the outcome page mounts there. Pin it from real bytes (the Sanjeevni chat moved it on 26-Sep).
3. Confirm S413 (`slip_log.py fa2d21bf…`) and S416 (`code_bundle.py 37a5a132…`) in the 27-Sep bundle — both DECLARED-PENDING — and that the bundle now carries `portal_sw.js`, `ring-hook.service`, `casepack_page.html`, `fu_push_on_arrival.sh`.
4. Read the 27-Sep `TASK_HISTORY_LATEST.txt` — the first night with the morning task (S415). The 26-Sep 03:10 run finished with result 2; read `NIGHTLY.bat`'s exit logic and say what 2 means before calling it anything.
5. Claim the kit number, then build step 2 + step 3 as one kit (walk on a scratch copy of the sheet row shape and the ring state), and the two WhatsApp pieces as the next.

## 7 · CARRIED (not now, in his order)

Contacts steps 3–5 when he returns `CONTACT_GROUPS_TO_UPDATE.xlsx` (D627) · the mail flood (kept, low) · the portal tiles after the Sanjeevni migration · `finance_app.py` read whole and re-pinned after the Sanjeevni build · AF-19 (not his priority) · the Docterz Clinical Data Report 2022 → today (his, when convenient; F-629).

*S282 close · 26-Sep-2026 · every line number read from the files named, at this close.*
