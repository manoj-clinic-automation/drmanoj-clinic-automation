# S440 — THE SENDING FROM `/portal/messages` — the plan the next session builds from (written 12-Nov-2026, 22:2x IST, the parent)

## 1 · What the owner has decided (his words, in order)
- **D940 (20:21 IST 12-Nov, S439):** "proceed with the build for sending to real patients".
- **21:41 IST (S440):** "Keep the templates as such and proceed." — no new template; `appointment_reminder_1day_ortho` stays as approved (no helpline line); the sending uses the 14 approved templates as they stand.
- **22:21 IST, on the mock-up (artifact "WhatsApp Sending Mock", v1; copy `D:\Downloads\ClaudeCowork\03_WORKING_PAPERS\S440\wa_sending_mock_v1.html`):** "Timings ok". He asked why a limit of 40 and why only one message first.
- **22:22 IST:** "Ok" to: **the timings as shown · a daily ceiling of 150 (a runaway guard, not a target; the page says when it is reached) · all five automatic messages built together, each with its own switch, every switch his · "long overdue" only on his tick.** The first-evening suggestion ("Follow-up is tomorrow" first, a look the next morning, then the rest) is a suggestion only — he may turn all on the first day.

## 2 · The timings (agreed)
| list (key in `wa_ladder.LISTS`) | template | goes |
|---|---|---|
| tomorrow | drmanoj_followup_tomorrow | 6:00 pm, the day before |
| post_visit | drmanoj_post_visit | 9:00 pm, the same day |
| appt | appointment_reminder_1day_ortho | 6:00 pm, the evening before |
| due1 | drmanoj_followup_due | 10:00 am, the next morning |
| due5 | drmanoj_followup_missed | 10:00 am, on day 5 |
| overdue | drmanoj_followup_dropout | only the names he ticks, when he presses Send (two taps) |

## 3 · What the page must show (the mock-up is the reference)
One switch per message (OFF at install; two taps to turn ON, one to turn OFF; the doctor's login only) · a line "Sending is OFF for all six / ON for n" and **Stop all sending** · the time each goes · "n sent today · at most 150 a day" · each row: would go / will go at … / Held: reason · after sending: Sent hh:mm / Not sent: reason, per row · "See the message the patient gets" · **Send a test to my phone** per message · long overdue: tick boxes + "Send to the ticked names (n)".

## 4 · The rules the kit must hold (each one a walk check and a mutation)
1. A switch that is OFF sends nothing. All switches OFF at install.
2. The rules already in `wa_ladder.py` decide who is on a list (latest visit only; came back since; a booking ahead; one plain mobile on record; the stop list; if the stop list cannot be read EVERY row is held).
3. **The stop list is read again at the moment of sending**, per row.
4. **One number gets at most one message a day** — across the six lists AND across what any other page sent that day (the portal's send log).
5. **Never twice for the same follow-up date, whichever page sent the first** — the kit's own record AND the portal's send log (`/root/wa/wa_portal/wa_portal_sends.csv`: its columns are read on the box by the installer's DRY step before anything is built on them, F-1291; a log that cannot be read = nothing is sent).
6. **Written ahead:** a row is recorded as "trying" BEFORE the request leaves; a failure or a crash after that is **never retried** (F-1297) — the row shows "may have gone — not tried again".
7. The one canonical sender (`portal_wa.send`, on `http.client` since S802) — ONE request per message; no sender code of the kit's own.
8. A list goes once a day, at its time; if the server was down at that time it goes late only inside a short window (proposed: 90 minutes), otherwise that day is skipped and the page says so — nothing is sent late at night.
9. The daily ceiling of 150 across all lists; reached → the rest held, said on the page and in his morning notice.
10. **A test to his own phone before the first real send of each message** — the switch of a message cannot be turned ON until its test has been sent and he has pressed "it arrived". His number is given on the server line at install (never in the repository; F-185).
11. `PORTAL_WA_DRYRUN` (the portal's test switch) is respected: in TEST nothing leaves and the page says TEST.
12. Every send, hold and refusal is in the kit's own store (`/root/portal/wa_ladder.db` — already in the encrypted nightly since S806) and on the page.
13. One master off: the estate's switch `/root/finance/_off/ALL_OFF` (read first) and the page's **Stop all sending**.

## 5 · The build's first reads (on the newest bundle, whole files — no patcher from an inferred anchor)
- `/root/portal/wa_ladder.py` (cb197293, S805 1.3; 41 KB) — whole. It holds NO send code by design: the sending goes into a NEW file beside it (proposed `/root/portal/wa_ladder_send.py`), and `wa_ladder.py` gains only the page's controls and doors.
- `/root/portal/portal_wa.py` (e8b27db9, S802) — `send()` and `_log()`: the argument shape, the result dict, the log's columns.
- `/root/portal/portal.py` — how the token and `PORTAL_WA_DRYRUN` are read (`_cfg_get`), to decide HOW the timed run gets them: a cron line that calls a localhost-only door of the portal (the portal process already holds the config and the sender) is preferred to a second copy of the config reader.
- The crontab in the bundle (the `# S798_WA_STOP_LISTENER` line is the pattern).
- `S437_WHATSAPP_FINDINGS.md` §1–§2.

## 6 · The kit's gates (as S805 / S807)
Kit number from `board/_numbers` first · built on the live bytes (make script, anchors once) · walk on made-up stores with a CONTROL red on the live files · mutations · the page run in Chromium at 400 and 1100 px · the installer rehearsed on a stand-in root, red after placing → every file back · **a cold review by a second reader before it is placed** (S807's reviewer found what the walk had passed: only the number was checked for an old tab; a sender exception gave an error page and a second press repeated rows) · his publish, then ONE server line (with his own number for the test) · read live as manoj · then HE turns the first switch on.

## 7 · Not in this kit
Leaving out patients who bought medicines meanwhile (D919 — not yet matched) · the Hindi call-back recording and the busy step (parked, D940) · the helpline on the Google profile and the contact page (D937, F-1287: still the old number on both at 21:3x IST 12-Nov).
