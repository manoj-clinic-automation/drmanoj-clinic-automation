# S450 — X-RAY PHOTOS AND LAB REPORTS: WHAT EXISTS, WHAT IS UNFILED AND WHY (13-Nov-2026)

*His words, 18:14 / 18:22 / 18:24 IST 13-Nov: staff upload X-rays daily and the notice still says 24, then 30 pending · "is there a confirmation report sort of daily x-rays upload, or a prompt next morning with a list to be uploaded, date wise … upload automatically moved these to uploaded section, and pending ones and the ones with issue stay flagged, section wise, or you suggest something else, analyse the current status and write back" · "a lot of x-ray sorting logic was built recently, so look into all such pending issues, i want all x-rays and blood reports to be filed properly". Read-only study by a helper: code from the 13-Nov bundle, counts from the 13-Nov database copy (in the device VM; slips to 12-Nov). Nothing changed. No patient data here.*

## A · What exists today
- `/finance/checks` (Check karein) — reception, Alisha, Shivani: parked pictures of the last 7 days with the photo and that day's patients; Shavez: one queue (photos, wrong-ID lab reports, payment gaps). An item leaves on a tap; the next mailbox run files it.
- `/finance/records/xray-check` — the owner: tiles (filed by themselves · waiting · X-ray with no slip · lab wrong ID · Not in Docterz / payment gap).
- `/finance/slips/pending` (Report baaki) — X-ray tab: slips with no SAME-DAY photo; Blood tab for Sukhveer.
- `/finance/slips/film/list` — the date-wise X-ray slip list (it replaced the Excel). No photo column.
- Aaj ka kaam lines (DUTY_MAP v24), the console's "Needs you" lines, the phone notice at 15:00 and 18:00 (S790).
- **No daily date-wise confirmation exists. No next-morning prompt exists. No mail covers it.**

## B · The pipeline and its timing
- X-ray: X-ray PC → pen drive → reception PC "X-ray upload" shortcut → Drive X-ray inbox → the mailbox script every 15 minutes round the clock (F-1260) → the server's plan → the patient's folder. The film-date reader every 30 minutes.
- Lab: the lab's mail → the same mailbox script → filed by ID (by name if no ID). WhatsApp files are swept to Drive and wait for a person.
- **Evening X-rays are not uploaded the same night:** of 74 slips written after 19:00 that have a photo, 5 were seen the same day, 36 the next day, 33 later. The cause is the upload, not the server. On 12-Nov the 18:00 notice saw 2 slips; 6 existed by night, 4 without a photo.

## C · X-rays (patient-days)

| month | slips | photo same day | within 2 days | none | not done |
|---|---|---|---|---|---|
| Sep (from 23rd) | 40 | 29 | 9 | 2 | – |
| Oct | 174 | 170 | – | 3 | 1 |
| Nov (to 12th) | 54 | 45 | – | 9 (four are 12-Nov) | – |

- Docterz X-ray lines with no slip: 19; slips with no Docterz line: 23.
- Pictures, 493: filed at arrival 322 · by the re-try rules 96 · by system rule answers 31 · after a person's answer 10 (owner 8, Alisha 2) · duplicates 12 · one stuck "planned" since 9-Nov.
- In check, 21: 12 marked Not in Docterz (7 people; Sep 4, Oct 2, Nov 6), 9 unanswered (6 people; Sep 8, Nov 1). Reasons: no ID in the file name 18, a short number 3. All 21 have a film date; 2 a film ID.
- Elimination: 2 days pair exactly one picture with one photo-less X-ray patient. Four waiting days have no photo-less slip at all.
- Payment gaps: 12 pictures open (7 people), none explained or billed. X-ray filed with no slip: 3 open (Sep), 1 answered.
- The notice's 23 (to 12-Nov) = 11 of 26–29 Sep (9 with the photo 1–2 days BEFORE the slip's date) + 3 October ("put" tapped, nothing matched) + 9 November.

## D · Lab reports
- Blood tests (table `blood_order`): Sep 22, Oct 51, Nov 15. Reports filed from the lab's mail: Sep 78, Oct 82, Nov 17. Filed with no blood order that week: 21, 20, 1 (information only since S788).
- Orders with no report after 3 days: Oct 2, Nov 1, all chased. Not tested: 10.
- Lab mails with no ID: 25 placed by name, 5 waiting (4 older than 7 days).
- **WhatsApp files (`record_wa`): 117 "saved", 0 ever filed, 3 "not a report".** Age: 1 within 2 days, 22 at 3–7 days, 94 older. 48 have a suggested patient.

## E · Faults and notes
- Every X-ray fault is CLOSED (F-1201, 1204, 1205, 1206, 1233, 1236, 1252, 1258, 1264, 1265). OPEN and related: F-1358 (incoming WhatsApp files pushed with no link never arrive — MyOperator), F-1316.
- READMEs: S752 "known, not changed" (a filed picture whose report never arrives goes "gone", the Drive copy unlinked) · S791 rule H stays with a person · S382 doctors' counts door "comes next" · S655 lab health row not wired.
- Not established (the device link dropped): the Runbook §2A X-ray lines were not read through; who is shown the WhatsApp item was taken from the READMEs, not the code.

## F · Why items stay unfiled — and what the server can settle
1. The same-day rule: 9 September slips dated 1–2 days after the photo. **Automatic.**
2. Evening X-rays uploaded the next day or later, and nobody prompted the next morning: about 30% of slips. The server cannot file them; it can list them date-wise the next morning.
3. No clinic ID in the file name: 18 pictures against 14 photo-less slips; 7 of the 9 November slips fall on days holding an unplaced picture. 2 pair by elimination; the rest can be OFFERED as "likely" for one tap.
4. Answers that did not stick: 3 October "put" taps, 1 stuck "planned". Partly automatic.
5. WhatsApp reports never answered: 117. The mobile number plus the visit day can suggest; a person confirms.
6. Payment gaps: 7 people. A person.

## G · Proposed (told to him ~18:58 IST; nothing built)
- **A small kit first (on his "go"):** a photo within 2 days of the slip counts (the notice, Aaj ka kaam — DUTY_MAP `alisha.xray_photo`, shared with the Sanjeevni chat, F-1024's REWRITE fit — and Report baaki); the notice counts the last 7 days, today first; older than 7 days to him and Shavez, one-tap close; the one stuck "planned" row.
- **Then a mock-up for him: the daily records sheet** — one page, date-wise, newest first: X-rays billed → Filed / Pending / Issue; blood tests → Filed / Pending / Issue; an upload moves a row to Filed by itself; a 9:30 am prompt to reception with yesterday's list; one evening line to him. With it: likely matches for no-ID pictures (one tap), WhatsApp reports with a suggested patient (one tap), payment gaps as their own section.

## I · His rulings of 19:27 – 19:34 IST and the plan AS DEFINED (nothing built; "Do not build or code anything now")

**His rulings (to be numbered at the close):**
- Evening X-rays cannot be uploaded the same day; the next afternoon is the earliest window, together with that day's morning X-rays.
- Pictures with no clinic ID in the file name: the film reading plus Docterz and slips matching already built is the way — keep it.
- **"Not in Docterz" are NOT payment gaps** — occasional complimentary X-rays that enter the system nowhere. (This replaces his word of 11-Nov 09:45 and rule 7 of `S428_XRAY_MATCH_PLAN.md`.)
- WhatsApp files: not pursued now (random pictures, patient forwards).
- No new page: a section on Shavez's slips desk (last few days' X-rays not uploaded / with an issue) plus a link; the X-ray sorting page he and Shavez work from is to be inspected as the home for the date-wise view; his existing X-ray sheet is updated, not replaced. The phone notice stays.
- Reception gets yesterday's list at 9:30 am and a confirmation in the evening after the upload; he gets the evening line too.
- The slips desk's back-date patient search must accept a NAME as well as the clinic ID (the drop-down already shows both).
- Point 8 (older than 7 days to him and Shavez) — "already there" (S782, 11-Nov): dropped from the plan; only the phone notice's count still reaches back to 23-Sep, and that is point 1.
- Lab reports without an ID: add suggested patients by name and date, range matching, if possible.

**The plan as defined (one mock-up of the screen changes first, then one or two kits, on his word):**
1. **Due rule.** A morning X-ray is due at that afternoon's upload; an evening X-ray at the next afternoon's. Nothing is pending before it is due; a photo filed within 2 days of the slip counts (the notice, Aaj ka kaam / DUTY_MAP `alisha.xray_photo` — shared with the Sanjeevni chat, F-1024 — and Report baaki). The notice looks back 7 days, not to 23-Sep.
2. **Messages.** 9:30 am to reception: yesterday's list by date and name, plus what is still open from the last 7 days. Evening, after the upload: "all N in" or "n of N in, the rest named" — to reception and to him. The afternoon notice stays, counting only what is due.
3. **The X-ray sorting page (he and Shavez): a date strip** — last 7 days: billed · filed · pending · issue; a date opens its rows; issue rows are the existing one-tap cards. Blood tests on the same strip: ordered · report in · pending.
4. **Shavez's slips desk:** a compact "X-rays, last 7 days" section (pending and issue per date) with a link to the sorting page; the back-date search takes a name.
5. **His X-ray sheet** (`https://followup.dr-manoj.in/finance/slips/lists`, X-rays tab): a Photo column — Filed (opens it) / Pending / Issue — and a "not filed" filter.
6. **"Not in Docterz":** the payment-gap wording and the red line go; one tap "Complimentary" by him or Shavez closes it.
7. **Pairing by elimination — defined as a SUGGESTION first.** When, once a day's upload window has passed, that day (by the film's date) has exactly one X-ray slip with no photo and exactly one unplaced picture, they very likely belong together. Automatic only when nobody has answered the picture and its written name does not fit another patient; otherwise the card shows "this day has one X-ray without a photo — is this his?" for one tap. On the 13-Nov copy: 2 days fit, and both pictures had been marked Not in Docterz — so both would be asked, not filed. Every such filing shows on "Filed by themselves" with Move.
8. *(dropped — already live)*
9. **WhatsApp:** left alone.
10. **Lab reports without an ID — suggested patients.** Rank candidates by: (a) the name, with the same spelling tolerance as the X-ray rules; (b) the date range — a blood test ordered 0–3 days before the report, then a clinic visit in the 7 days before, then the patient list; (c) where the report prints them, age / sex and the tests against what was ordered. One strong candidate (name + a blood order in range) → filed by itself, shown under "Filed by themselves" with Move. Two or more → the card lists them, best first, each with its reason, one tap. None → one tap "not our patient". Today: 5 waiting, 4 older than a week.

**Not yet done for this plan:** the code of the sorting page, the slips desk and his sheet has not been read (the PC link was down from ~18:55 IST and a read of the repository from the cloud was refused) — it is read before the mock-up.

## H · For the close
- **A slip of the helper's (minted at the S450 close as F-1374):** one grouped query printed two duplicate-verdict strings that contain a patient's name into the helper's tool output (the cloud side). Nothing was written anywhere and no name is in any paper. The rule for the next probe: never GROUP BY a free-text column (`verdict`, `note`) — group by state / code columns only.
- The device link dropped for some minutes around 18:45–18:50 and again ~18:55 IST (Service Unavailable), then answered.
