# S443 — THE FOLLOW-UP FEED — the readers, the roads, and ONE plan (13-Nov-2026, the parent)

*Analysis and a plan only (D949). Nothing is built, nothing on the server or the PC was changed. Counts only; no patient name, number or clinic ID. Sources: the 13-Nov bundle (01:35 IST), the kits S808/S809, the PC tracker's own program (read-only, folder allowed by the owner 05:4x IST), the database copy of 13-Nov 01:40 IST (queried in memory, no copy kept), the papers S421, S431, S433, S435, S437, S442 findings. File:line references are to those bytes.*

## 1 · The one finding that explains the rest

**Everything that knows "who came" and "who is due" is made by ONE program on the owner's PC** (`processor.py`, 3,556 lines, Task Scheduler job *DocterzPickup* every 5 minutes). Reception's two evening exports go **reception → server → the PC → back to the server**, and from the PC's output four different roads fan out, each with its own clock and its own rules. The WhatsApp lists then add a fifth source for the follow-up date (the Clinical data report, which only the owner exports, when he remembers).

## 2 · The readers and their roads — ONE table

| reader | what it shows | its source | the road | fresh at | read by |
|---|---|---|---|---|---|
| **PC tracker** (`processor.py`) | the calling list, the visit ledger, the patient master, the day's revenue | reception's consultation report + follow-up log, fetched FROM the server into `D:\Downloads` | Task Scheduler every 5 min; runs ~45 s after both files are 3 min old | 20:16–21:25 on 9 of 11 working days; next morning on 2 (31-Oct, 02-Nov); needs the PC ON | everything below |
| **Callback Tracker** (Apps Script) | Followups_Today in sections Due Today / Grace / Actionable Missed / Probable Dropout | the PC's `Staff_Action_Today_<day>.xlsx` | → `/fu-upload` → `/root/wa/followup-inbox/` → `push_followups_vps.py` → Sheet tab (within 5 min of arrival; timer 07:00, 11:00, 22:00) | ~21:15–21:30 the evening before | reception, Shavez |
| **Call Console** (`calls_console.py`) | follow-up sections today / grace 1–3 / overdue 4–14 / lapsed 15+; "called N of M" | the Sheet tab → `portal_console.py --build` (cron */10, 07–22) → `console.db` `fu_all` | as above + 10 min | ~21:30 | the owner; the staff cards |
| **WhatsApp lists** (`wa_ladder.py`) | six lists | follow-up date: `dx_visit` (Clinical data report); who came: `patient_visit` | `dx_visit`: the owner's own export → Drive → `docterz_pickup.py` */15 → `dx_feed.py`. `patient_visit`: the PC's `Visit_Ledger_Join.xlsx` → `finance_patient_sync.py`, cron **:20 past, 08–21 only** | `dx_visit`: when he exports (2–7 Nov arrived 10-Nov). `patient_visit`: 21:20 if the PC pushed before 21:20:00, else **08:20 next morning** (12-Nov: pushed 21:20:58) | the sender (S808) |
| **Command console — money, the day** | `clinic_day_line` | the *Day Revenue* tab of the PC's workbook via Drive → `docterz_ingest.py` */10 | 20:20–21:30 | the owner |
| **Call-back clock** | missed callers | `console.db` calls only | cron */5, 08–21 | live | staff, Shavez, the owner |
| **Call ke baad / Patient records** | came / did not come; a patient's visit dates | `patient_visit` | as the WhatsApp lists | as above | staff, the owner |
| **Aaj ka kaam** | no calling list; duty lines "both Docterz reports reached the server"; the staff call card | `docterz_export`; the Call Console | */15 | live | staff |
| **Patients page** | not built (mock-up v16) | — | — | — | — |

**The raw exports are on the server before any of this:** `docterz_pickup.py` (cron */15) keeps reception's consultation report and follow-up log under `/root/finance/docterz_exports/` — the consultation report at 20:15–21:15 on every working day measured. No server code reads their rows (only that they came and how many rows).

## 3 · What was measured

- **The consultation report alone gives "who came".** 30-Oct … 11-Nov, ten working days: matched on clinic ID, **0 patients in the report but not in `patient_visit`, 0 the reverse.** The server holds it 5–50 minutes before `patient_visit` catches up, a whole night before when the PC's push lands after 21:20. Its header carries Patient UID, Mobile, Consultation Date, Clinic Specific Id, Procedure Amount — all `patient_visit` needs. Two things to carry over exactly: the tracker's `visit_id` format (the primary key) and its `had_procedure` rule — both now readable in `processor.py`.
- **The follow-up log reached the server the same evening on 8 of 11 working days;** 31-Oct's and 05-Nov's came next morning (~08:00); 12-Nov's not at all by 01:40 — the PC reused the 11-Nov log (9 of 117 rows for 13-Nov).
- **Follow-up dates in `dx_visit` (the WhatsApp lists' only source) arrive when the owner exports the Clinical data report.** 544 of 726 advised periods are 7 days or less: a report that arrives five days late has already missed their "follow-up tomorrow".
- **Follow-ups due in October (398 advices, 297 patients):** within 3 days either side 146 · more than 3 days early 20 · 4–14 days late 28 · 15–45 days late 8 · not back by 12-Nov 196.
- **Three ladders, three "came back" rules:**

| | sections (days after the due date) | "has come back" |
|---|---|---|
| PC tracker → Callback Tracker | grace 1–3 · missed 4–10 · probable dropout 11–60 · hidden after 60 | a visit from half the advised period before the due date (D893, since 10-Nov 19:13); one visit closes all of that patient's open follow-ups |
| Call Console | grace 1–3 · overdue 4–14 · lapsed 15+ | the tracker's row; one row per mobile |
| WhatsApp lists | exactly +1, +5, +14 | any visit after the prescribing visit |

- **Medicines bought without a consultation (D919)** are read by none of the three.
- **Staff outcomes** (coming, out of town, on medication, not interested, asked not to call …) are written to the Sheet (`Followup_Outcomes`); the server reads them (`ring_outcome.py`, `call_verdict.py`, `daily_digest.py`); the PC tracker has not read a call log since 30-Jun (`data\call_log.csv`). Whether a settled row stays off the next day's list was not traced in `WebApp.gs`.
- **The calling list for a day is frozen the evening before** (visits enter only from the evening report, `processor.py`:3299): a patient who walks in on the day stays on that day's list.

## 4 · His three findings, read from the pages' own code

**F-1322 — "called" on the folded lines.** `calls_console.py`:819 keeps a call when `call day >= due day`; :725–728 "called" = any OUTGOING call to the row's mobile, answered or not; :848 counts them; :2073 prints "called N of M". So a call made on the appointment day itself counts for a patient who then did not come. The same filter feeds "reached", the pill and "who called today" (:729, :741, :836–839). The older page already uses "strictly after" (`portal_console.py`:499–501). Also: a mobile shared by a family counts any call to it.

**F-1323 — "awaiting WhatsApp".** `calls_console.py`:435–506. Every incoming MESSAGE is judged alone (:463). It is answered only by a later non-template reply whose status is *delivered* or *read* (:365, :502), or an answered call of 30 s+ within 2 clinic hours (:84–85, :504). Only messages inside the page's day span are read (:383, :1665). So a chat he replied to still reads awaiting when: (1) the sender wrote again after the reply ("ok", thanks, a greeting, a photo); (2) the reply fell on the other side of midnight; (3) the reply never reached "delivered" in the store — the Inbox writes "sent" (`portal_inbox.py`:1315) and turns it "delivered" only when MyOperator's ping is read, which the Call Console never triggers; the staff card and the follow-up pill count delivered only (:1311, :741). Staff replies from the Callback Tracker enter the store only when the Inbox list is opened (`portal_inbox.py`:1131). **There is no notion of "not a patient" and no way to dismiss a chat**; Spam can be set only from a call's review. Which of the three hit his chat of 12-Nov night needs that chat's rows (not opened).

**F-1324 — the tiles** (`portal.py`:134–658, groups :683–724). Group *Calls & WhatsApp*: Clinic Gist · Call Console · Call Tracker · Call ke baad · GMB Review Assist · **WhatsApp Inbox** (chats) · **Send WhatsApp** (one approved template to one patient, by hand) · **Follow-up WhatsApps** (only a link into the Call Console; the old batch page behind it refuses any list but today's since S807) · Follow-up Tracker (the PC's old browser page, `localhost:5000`). Elsewhere: **WhatsApp messages** in *Patients* (small line "Show only · who would get which message" — out of date since S808) · **WhatsApp Approvals** in *System* (the earliest tick-and-send page, `wa_approve.py`, superseded twice; its service still running).

## 5 · THE PLAN — for his word; nothing is built before it

**The decision (the assistant's):** the lists are made **on the server, from reception's two evening exports, within minutes of their arrival, by the PC tracker's own rules** — one follow-up list that every screen reads. The PC tracker keeps running beside it as the check, and stays as the fallback.

**Step 1 — the feed in time** (no screen changes; this is what the WhatsApp switches wait for)
- "Who came" is taken on the server straight from the consultation report as it arrives (same `visit_id`, same `had_procedure` rule); the PC's push becomes the cross-check. The 21:20 race is gone.
- The follow-up dates for the WhatsApp lists come from the **follow-up log reception already exports** — the same dates the calling list uses — not from the Clinical data report. That report stays what it is: diagnosis for the Patients page, whenever it comes.
- A missed export is chased: at 9:45 pm, if either report has not reached the server, reception's phone and Shavez get one push; he hears only if it is still missing at closing. A follow-up log that comes next morning re-makes the lists (as the PC does today).
- Gate: two evenings where the server's "who came" and the PC's agree to the patient, shown as one line on his console.

**Step 2 — the screens he found wrong** (one mock-up first)
- Call Console: in *Grace* and older sections a call counts only from the day AFTER the due date; *Today* counts today's calls. Each folded line reads "called N of M · reached K"; each patient shows when last reached (D899).
- WhatsApp awaiting: judged per CHAT. Awaiting only when the last word is the sender's and nothing went back — a reply accepted by MyOperator (his, staff's, the panel's) or an answered call. A bare "ok / thanks / greeting" after our reply does not reopen it. Midnight does not cut a chat. Two buttons on his page: **Done — no reply needed** and **Not a patient** (the number leaves the awaiting lists and the staff cards; a small list he can undo).
- Tiles: *WhatsApp messages* moves to *Calls & WhatsApp*, small line "Daily patient messages · switches · what went". Retired: *Follow-up WhatsApps* and *WhatsApp Approvals* (its service stopped, kept to put back). Left: WhatsApp Inbox · WhatsApp messages · Send WhatsApp.

**Step 3 — one list everywhere**
- The tracker's engine runs on the server each evening on the files already there; for two weeks its list is compared nightly with the PC's ("server 63 · PC 63 · same"). Then the Callback Tracker's tab, the Call Console and the WhatsApp lists are switched to it one at a time; the PC run stays as fallback.
- One ladder on every screen: **Today · Grace (1–3 days late) · Missed (4–10) · Long overdue (11–60)**; after 60 days a quiet list, never "lost" (D920). The WhatsApp messages sit on it (day 1, day 5; long overdue on his tick).
- One "came back" rule everywhere: D893.
- A fourth state, *on medicines* ("bought medicines on <date>, has not consulted since", D919), on the calling list and held out of the "date passed" messages.
- A staff outcome closes or snoozes the row on every screen; "asked not to call" also stops the WhatsApp reminders.
- The Follow-up Tracker tile (the PC's page) retires at the end of this step.

**What each person does, by when**
- Reception: the same two exports, by 9:30 pm. Nothing new.
- Shavez: the day's list in the morning. Alisha: Grace and Missed, 4–6 pm (D819).
- The owner: nothing daily. His switches, his tick on long overdue.

**The WhatsApp switches** stay OFF until Step 1's gate is green. Then: after-visit ~9:30 pm (as soon as the day's visits are in) · date passed, 10 am · follow-up tomorrow and appointment reminder, 6 pm.

## 6 · Not settled — to read at the build, not asked of him
- The follow-up log's columns (patient key, the day it was advised) — read from a real file's header before Step 1 is designed.
- Whether a settled outcome keeps a row off the next day's Sheet tab today (`WebApp.gs`).
- Whether the Apps Script in the repository (Sep-2026) is the deployed one.
- Whether MyOperator sends delivered / read pings and echoes of panel replies now (the receiver's log).
- An option not in the plan: a patient whose OPD slip is made today drops off today's calling list at once (the slips desk knows who came during the day).
- The device VM's home disk was 100% full at 05:4x IST 13-Nov (two readers could not make a scratch folder) — a fault for the close.

## 7 · THE OWNER'S WORD, 06:26 IST 13-Nov — and the plan as amended (this section WINS over §5 where they differ)

1. **The Clinical data report** can be exported only from a doctor's login; he exports it himself, at night or the next morning. It is to be analysed for its best use (below).
2. **A missing reception export is escalated to HIM** — staff have left by then. (§5's push to reception and Shavez is withdrawn.)
3. **Call Console, the folded lines of Grace and older:** show prominently the calls made THAT DAY; the earlier days' calls additionally; and only patients who have not visited by the decided rule (D893) have a place on these lists.
4. **"Skip compare 2 weeks if it's okay, and shift tracker from PC to server?"** — the assistant's call: YES to both. The two-week wait is replaced by a proof BEFORE the install: the server's engine replays the past month's archived evenings and must make the same lists the PC made on those evenings. Then the readers switch in one go. The PC's task stays installed and keeps making its list quietly as the spare; it feeds nothing.
5. **The roster:** Shivani makes the morning follow-up calls (the day's list). Shavez is the fallback only. (§5's "Shavez: the day's list in the morning" was wrong — taken from D819.) Alisha: Grace and older, 4–6 pm, as before.

**The steps as amended**
- **Step 1 — the tracker moves to the server.** The same rules, run on reception's two exports within minutes of arrival; proven by the replay; the PC as the spare. Every output of the PC's engine is reproduced: the call sheet, the visit ledger and patient master (`patient_visit`, `patient_ref`), the Day Revenue tab and `Day_Tenders.csv` (the command console's money), the 08:00 Patient_Master mirror. At 9:45 pm a missing report is pushed to the owner. The WhatsApp switches wait only for this step.
- **Step 2 — the screens** (mock-up first): the folded lines as in 3 above; WhatsApp awaiting; the tiles.
- **Step 3 — one ladder, one "came back" rule, *on medicines*, staff outcomes** — as §5.

**The Clinical data report — what it holds** (header and fill rates of two real files, 50 and 137 rows; no cell read out)
55 columns. Everything the consultation report has (patient, UID, mobile, date AND time, clinic ID, purpose of visit, the bill by head, mode, invoice) plus: **Diagnosis** (on 52–58% of rows) · **Follow Up** as a date (52–58%) · **Drugs Prescribed** and **Dosage** (52–62%) · **Instructions** (48–59%) · **Tests** advised (16–18%) · **Procedures** advised (5–6%). Empty in practice: Complaints, Findings, Vitals, Notes, Clinical Note, Lab Trends, Ref By / Ref To.

**Its best use — it arrives late, so it never makes a list wait; it makes each list better when it comes**
| what it adds | where it goes |
|---|---|
| the follow-up date WITH the visit it was advised at | the exact advised period for every row (the tracker's weak spot: "when the prescribing day cannot be read", `processor.py`:2011); a follow-up the log missed is added; a count of differences on his console |
| the diagnosis | the group on each calling row, so calls go where patients are lost (degenerative, radicular, trauma) and rheumatology gets one reminder at 2 months (D920); the Patients page |
| drugs and dosage | how many days of medicines were given → the day they run out; the *on medicines* state; prescribed here against bought at Sanjeevni (the Sanjeevni chat is told before anything is built on it) |
| tests advised | against *Report baaki* and the lab: advised, not done |
| procedures advised | against *Kal ke procedures* and the slips |
| purpose of visit, the time of the consultation | new against review as Docterz itself records it; the load by hour |
| the same visit rows | a second check on "who came" |
- His part stays what it is: export when he does; it is picked up from his Downloads by itself (the 5 MB skip, F-1274, and the file-name trap, F-1276, are repaired with this work).

*S443 · 13-Nov-2026 · the parent · analysis only.*
