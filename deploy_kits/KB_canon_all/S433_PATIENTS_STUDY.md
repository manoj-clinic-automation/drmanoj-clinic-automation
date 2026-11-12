# S433 — THE PATIENTS STUDY (the parent, Claude Fable, 11/12-Nov-2026) — counts only, no patient data. The figures behind mock-up v11 of the Patients section; the next session builds on this paper. Mock-up: https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA


Source: finance.db copy of 10-Nov 21:45 in the device VM (/tmp/s433), the 11-Nov bundle's code. Scripts beside this file: a1_dx_coverage.py, a2_terms.py, a3_patients_section.py, a4_checks.py, a5_final_numbers.py.

## ITEM 1 — Patients section part 2: analysed; mock-up v5 published on real figures (awaiting his word)
Canvas: https://claude.ai/artifact/TNw8B62K2GHvST3NPU1WNA (v5; project/Main.dc.html).

Decisions made (stated to him, not offered):
1. Diagnosis per visit = dx_visit; a visit with no diagnosis typed takes the same patient's nearest written one (earlier first, then later). Aug-Oct 1,703 visits: typed 1,186 (70%) + carried 252 (15%) = 84%; none 265 visits / 200 patients (150 one-visit, 167 new). F-1225's hole (735 of 1,305 patients) is closed by S779.
2. "New" = first-ever by clinic-ID order (a clinic ID above every ID seen on an earlier day; IDs are 4-digit, issued in order). patient_ref.first_seen is NOT usable for this (it is the finance system's first sight: 336 of August's 380 would read as new). New: Jul 198, Aug 211, Sep 207, Oct 187, 1-10 Nov 38.
3. Revenue per group = clinic_day_line (consult + xray + proc), which joins 100% to patient_visit by clinic_id + day (Jul-Nov 3,328 of 3,328 lines). Pharmacy (sale_bill) and lab carry no patient ID -> not in it.
4. Follow-ups come from dx_visit.follow_up_date alone (no PC tracker needed): due Aug 434, Sep 444, Oct 398 (S421 had 436/426/392). Split by what was advised: <=7 d (74% of all), 8-30 d, >30 d.
5. Groups: 8 main categories + "Other groups" (10 small categories incl. the unplaced words) + "No diagnosis typed". A percentage only where the base is >= 20 visits.
6. One-tap list today: 29 words / 50 visits (of 511 distinct spellings). Refinement: the page SUGGESTS a group and one tap places the word with its spelling slips and other sides (cellulitis x4 spellings = 1 tap). dx_term_map is keyed by the exact term today -> the build adds a stem key (side / laterality / bracket text stripped). dx_feed.unknown_terms() and reclassify() already exist.
7. "Called" columns: from /root/wa/console.db at build (not in the nightly database copy).

What the figures say (new, not in S421):
- Planned reviews (8-30 d advised) kept: due Aug 55% (56/101), Sep 32% (26/82), Oct 36% so far (32/88, 36 open). Short follow-ups steady 50/51/48%.
- Fewer planned reviews are being advised: visits given one — Jul 103, Aug 100, Sep 85, Oct 65.
- New patients steady (~200/month, 54-57% of patients); their first visit: back <=7 d 41/43/36/42%, back 8-30 d 7/8/8/8%.
- Seen-before patients' 8-30 d return: Jul 30, Aug 29, Sep 20, Oct so far 22%.

## ITEM 2 — Part 3 (reception's third export): analysed from the code; nothing built
- The road already carries it: docterz_pickup.identify() knows kind 'clinical' by content (S779) from the same Drive folder reception's Chrome saves into; take() calls dx_feed.run() at once.
- Overlap is safe: dx_feed.ingest() is INSERT OR REPLACE per (patient, visit day), a later export wins -> a rolling window heals a missed evening and picks up a diagnosis typed the next day. Decision: reception exports the Clinical data report for the LAST 7 DAYS every evening.
- Gaps to build: (a) no line anywhere when the clinical export is missing (owner_lines() watches the consultation report only; reception's evening duty counts two reports) -> the third report joins reception's existing evening duty line, and the owner sees a line only after 2 working days without one; (b) every clinical export is kept for ever as 'current' (never superseded: matched by md5) -> 300+ files a year of names and prescriptions on the box; keep the newest 14, the rest deleted once a later export covers their span; (c) the staff instruction (Hindi) = one more line on the existing evening card.
- Still to read: DUTY_MAP.json's reception evening line and the Docterz screen's own date-range control (his GUI) before the wording is fixed.

## ITEM 3 — Call Console older follow-ups: not started (needs /root/wa/console.db — read through the live page as manoj, counts only).

## The open
Session 433 taken 22:43 IST (board v1260). Day page re-run 22:42 IST: gate 1957/1957 GREEN, publish main = origin/main ad5e45aa (the S431 + S432 close records NOT yet published — the owner's double-click), pins 282 match / 0 mismatch / 10 DECLARED-PENDING. F-1268: at 22:50 IST the console still reads the same four with no punch -> the machine has not re-sent; staff switch it off and on in the morning. Board: 3 unread messages, none for the parent (growth x2, nkpath). PC_KITS check waits for the 12-Nov nightly.

## ADDED 23:10 IST — the owner's word 22:53 IST: "many patients, instead of returning for a consultation, keep buying medicines (Patient Records tab) ... use this data while assessing the follow-ups ... a local trend ... then they come at their own"
CORRECTION of decision 3 above: Sanjeevni bills ARE tied to a patient — sale_item (service 'pharmacy', patient_ref_id, confidence, verified_by) + day_entry, the Patient Records page's own rule (records.pharmacy(): verified by a person or confidence >= 0.95, open identity disputes left out, walk-in / name-only IDs never guessed). I had looked at sale_bill only. Scripts: a6_pharmacy_link.py, a7_medicine_refills.py.
- Bills tied to a numeric clinic ID: Jul 75%, Aug 74%, Sep 94%, Oct 89%, 1-10 Nov 89% (Jul-Aug read low).
- "Medicines, no consultation" (a tied bill on a day that patient had no visit): Jul 80, Aug 85 (67 patients, Rs 73,780), Sep 89 (73, Rs 78,364), Oct 127 (88, Rs 1,05,090), 1-10 Nov 36 (34). Aug-Oct by days since the last consultation: 1-7 d 76, 8-30 d 134, 31-60 d 39, >60 d 41, no visit since Jun 11.
- Follow-ups re-read (kept | on medicines without a visit | came late, no medicines between | neither | open):
  planned reviews (8-30 d): Aug 101: 56 | 5 | 16 | 24 | 0 · Sep 82: 26 | 17 | 11 | 28 | 0 · Oct 88: 32 | 16 | 7 | 6 | 27. Kept-or-on-medicines 60 / 52 / 55% so far.
  within a week: Aug 301: 150 | 21 | 18 | 112 · Sep 323: 164 | 20 | 8 | 131 · Oct 302: 145 | 18 | 7 | 37 | 95 open.
  after a month: Aug 32: 19 | 1 | 6 | 6 · Sep 39: 15 | 7 | 4 | 13 · Oct 8: 3 | 0 | 0 | 2 | 3 open.
- By group (follow-ups due Aug-Oct, on medicines instead): Rheumatology 11%, DJD 11%, Trauma 10%, Degenerative spine 8%, General 7%, Other 7%, Radicular 6%, Mechanical 6%, none 5%, Foot 2%.
- Pharmacy Rs by group, Oct (tied, Rs 5,19,143 of 5,80,447): Rheumatology 1,62,017 · DJD 1,03,162 · Radicular 79,869 · Other 55,513 · Trauma 45,446 · none 32,210 · Mechanical 19,637 · Foot 7,643 · General 6,926 · Degenerative spine 6,720.
Decisions: a fourth follow-up state "on medicines, no consultation" everywhere follow-ups are counted (Patients section; and on the calling list, item 3: the caller sees "bought medicines on <date>, has not consulted since" — a different conversation from "never came"). Floor only: walk-in bills and medicines bought elsewhere are invisible. Mock-up v6 published 23:0x IST.

## ADDED 23:25 IST — the owner's word 23:03 IST: (1) "patients due for a review at 1 month turn up later, mainly rheumatology, degenerative, after 2 months, 3 months ... do they find a place?" (2) "the mock-up is comprehensive, but it should include the analysis lines also and the suggestions also. That layer is also required."
Script a8_late_returners.py. Counts only.
- Visits by seen-before patients whose last consultation was more than 30 days earlier (31-60 | 61-90 | 91+ | not seen since before 1-Jun | total): Aug 33|4|0|42|79 · Sep 30|10|5|40|85 · Oct 27|6|5|27|65 · 1-10 Nov 7|1|3|4|15. Aug-Oct 229 = 13% of visits. By group: Rheumatology 75, DJD 44, Trauma 21, Radicular 21, no diagnosis 31, others 37. 42 of the 229 bought medicines at Sanjeevni in the gap.
- Reviews advised 8+ days, due Jul-Aug (n 185): by the date (+7) 56%, 8-30 d late 14%, 31-60 d late 4%, 61+ 0, not back by 10-Nov 26%. Rheumatology n 49: 53 / 18 / 10 / 0 / 18%. The window is too short (dx_visit from 1-Jul, patient_visit from 1-Jun) to see a 2-3 month late return against its follow-up date yet.
Decisions: (a) a follow-up is never closed as lost — statuses kept / on medicines / came late (with how late) / not back yet; (b) a "Back after a gap" block on the page; (c) for rheumatology and degenerative joints a missed review moves to a quiet list and is called again at 2 months (item 3, the calling list); (d) THE READING-AND-SUGGESTIONS LAYER: lines written every night from the figures by fixed rules (same figures -> same words; no model call at night), one suggestion under each reading, each opening its patients; (e) one ask to him, optional: a Docterz Clinical data report export 01-Jan-2025 .. 30-Jun-2026 (true gaps; last year's festival season) — the same road as S780.
Mock-up v7 published 23:2x IST (canvas board 1280 x 3700).

## ADDED 23:20 IST — the owner's word 23:12 IST
- He has REQUESTED the Clinical data report (Jan-2025 .. Jun-2026) from Docterz; it will come to his PERSONAL Gmail. Road: he saves the attachment into D:\Downloads on manojz -> S780 sends it on -> dx_feed reads it -> studied from the next database copy in the device VM. It is never opened through the assistant's cloud workspace or the Gmail connector (D656).
- His reading: October's more-medicines / fewer-review-consultations could be the festival time (patients continue medicines for their own reasons). Put on the page as his reading, to be tested on October 2025. Note for the study: the fall in planned reviews kept shows in reviews DUE IN SEPTEMBER (32%), before Navratri (11-20 Oct) — check whether last year shows the same September dip.
- ITEM 1 IS ON HOLD by his word: "when I will give you the clinical data, then you study it also and then come to a better result, and then only we will proceed further." No build. Mock-up stands at v7 (+ the festival line).

## ADDED 23:40 IST — the owner 23:15 IST: "The 6 MB file is in my downloads folder ... a CSV file."
File: D:\Downloads\clinical data report (1).csv — 6,282,540 B, 9,845 rows, Jan-2025 .. Jun-2026 (55 columns; the amount columns are empty, so no revenue history). READ ON MANOJZ ONLY (device VM), counts out. Scripts b1_export_shape.py, b2_build_history.py (-> /tmp/s433/hist.db: 8,635 visit-days from the export + 2,411 from the server = 22 months), b3_history_analysis.py.
FAULT TO MINT AT THE CLOSE: S780's sender (docterz_clinical_send.py, MAX_BYTES 5 MB) skips a larger file with NO log line — this export has NOT gone to the server (log's last line 21:25 IST, a 19-row daily report). I had told him it "should go by itself". Left so on purpose: item 1 is on hold and the study needs no server change; at build it goes in as two halves (2025, 2026), each under 5 MB, by the same road. Repair: the sender logs a skipped oversize file.
What the 22 months say (counts / percentages only):
- Visits per open day Aug/Sep/Oct: 2025 19.5 / 18.6 / 16.4 · 2026 23.7 / 22.1 / 19.0. New patients Oct 141 -> 187. The Sep->Oct dip is the same shape both years (-12%, -14%). Festival weeks 2025: 29-Sep week 11.4/day, Diwali week 13.7, the week after 22.2.
- Planned reviews (8-30 d advised) kept by due+7, by due month, 2025-01..2026-10: 54%, 37%, 47%, 50%, 63%, 45%, 46%, 44%, 44%, 46%, 57%, 45% | 32%, 50%, 43%, 52%, 44%, 58%, 46%, 55%, 32%, 36%. Range 32-63, usually 44-55. Festival months 2025 (Sep, Oct) 44 / 46 = ordinary. Sep-2026 32 and Oct-2026 36 (final for "kept") are low; Jan-2026 was 32. Short follow-ups 40-60, steady ~52.
- Reviews due per month (8-30 d): 28..146; Sep-26 82, Oct-26 88 — ordinary. MY EARLIER READING "you are advising fewer planned reviews" IS WITHDRAWN (it was within the usual swing); replaced on the page by the year-on-year reading.
- Seen-before visits followed by another in 8-30 d (all visits but a patient's first-ever), by month: 2025: 27%, 34%, 27%, 31%, 27%, 24%, 28%, 25%, 23%, 28%, 33%, 26% | 2026: 24%, 26%, 27%, 26%, 27%, 31%, 30%, 25%, 19%, 21% — Sep and Oct 2026 are the two lowest of 22.
- HOW LATE (reviews 8+ d advised, due Jan-2025 .. mid-May-2026): 3 wk-1 month advised n 526: by date 46, 8-30 late 16, 31-60 9, 61-90 3, 91-180 5, 180+ 3, never 19. By group (n): Rheum 728: 55/17/7/2/3/2/never 13 · DJD 278: 39/15/5/5/4/2/32 · Radicular 175: 41/15/6/2/2/2/31 · Trauma 180: 53/8/3/1/1/1/34 · Other 219: 41/8/2/1/2/2/44 · none 39: never 64.
- Gaps of seen-before visits Aug-Oct 2026 (1,098): <=7 547, 8-30 322, 31-60 90, 61-90 23, 91-180 31, 181-365 21, 365+ 23, not seen since before Jan-2025 41. Late (>30 d) by group: Rheum 81, DJD 47, Other 28, Trauma 23, none 23, Radicular 20, Deg spine 7.
- Late returns (>30 d) as a share of seen-before visits: 2025 Oct-Dec 17/20/21%, Jan-26 20%, then 12-18%.
- Pharmacy bills are tied to patients only from Apr-2026 -> last October's medicine purchases cannot be compared.
- The export's unplaced diagnosis words: 147 spellings / 269 visits (the one-tap list at build, before grouping by stem).
Readings changed on the page (v8): festival = right for the October visit dip, not for September's review dip; calls go where patients are lost (DJD, radicular, trauma, small groups ~1 in 3 never return), rheumatology one reminder at 2 months (13% never).

## ADDED 23:55 IST — the owner 23:22 IST attached the CONSULTATION REPORT (Jan-2025..Jun-2026) to the chat and asked whether it adds value
- The attached copy (cloud side) was NOT opened (D656). The same file is D:\Downloads\consultation report.csv on manojz (2,629,372 B, 9,111 dated rows, 39 columns) — read there. Scripts b4_consultation_shape.py, b5_consultation_value.py.
- SAFETY CHECKED: the PC tracker's pickup (docterz_pickup.py, NAME_PREFIXES consultation_report / followup_logs / clinical_data_report) ignores both big files because Chrome named them with spaces ("consultation report.csv", "clinical data report (1).csv"); pickup log 23:20 IST "nothing new to run". S780's sender sends clinical reports only and skips > 5 MB. Neither file has reached the tracker or the server. THEY MUST NOT BE RENAMED with underscores or put into the Drive "Docterz exports" folder: the server would take the 18-month consultation file as the report of 30-Jun-2026 (docterz_pickup.identify: business day = latest consultation).
- VALUE: yes. (1) rupees per visit: consultation fee from Apr-2025 (Jan-Mar 2025 bills are not in Docterz), procedure and X-ray ("Laboratory Amount") from Oct-2025; (2) paid vs free per visit; (3) it matches the clinical report on 8,554 of 8,558 visit-days.
- Consultation fees Aug/Sep/Oct: 2025 1,79,600 / 1,92,800 / 1,58,700 · 2026 2,54,000 / 2,34,400 / 2,18,600 (+41 / +22 / +38%).
- Returns <=7 d: 55-66% carry no consultation fee; returns at 8-30 d: 77-91% are paid (Aug-Oct 2026: 89-91%).
- 12 months Nov-2025..Oct-2026 (clinic Rs 42,27,900): per patient — Trauma 2,322 (2.5 visits, 1.7 paid) · Rheumatology 2,113 (4.1, 3.0) · DJD 1,990 (2.5, 1.9) · Other 1,408 · Radicular 1,395 · Degenerative spine 1,370 · Mechanical spine 1,133 · no diagnosis 788 (1.3, 0.8).
- BUILD DECISION: both files load ONCE into history-only tables beside the live ones (the Patients section reads them for last-year comparison); they never enter the money pages, the day sheet or the tracker. Mock-up v9 published.

## ADDED 12-Nov 06:50 IST — the owner 06:32 IST: can the monthly Google My Business mail add value to the page (insights, correlations, year on year)?
Read from the clinic mailbox (drmka.ortho, sender businessprofile-noreply@google.com, subject "... your performance report for <Month> 2026"); the mailbox holds them for Jun..Oct 2026 only. Each mail: interactions, calls, chat clicks, direction requests, website visits, profile views, searches, top 3 search terms, each vs the PREVIOUS month (no year-on-year in the mail).
2026      searches  views  calls  directions  chats  website  interactions | new patients (clinic)  new per 10 directions
Jun       1,450     6,352  231    206         14     23       474          | 192                    9.3
Jul       1,940     7,323  258    239         34     24       555          | 198                    8.3
Aug       1,417     6,939  205    231         15     27       478          | 211                    9.1
Sep       1,547     6,984  212    217         25     15       469          | 207                    9.5
Oct       1,415     6,421  185    203         22     16       426          | 187                    9.2
Top terms: "orthopedic doctor bareilly" 252-338, "best orthopedic doctor in bareilly" 164-185, "top (10) orthopedic doctor(s) in bareilly" 89-136; Oct third = "manoj" 73. The profile's name changed in mid-October (the October report carries the new name).
Also in the mailbox, not yet used: Search Console monthly mail for drmanojagarwal.com (clicks / impressions: Aug 123 / 12.9K, Sep 107 / 13.6K, Oct 91 / 11.8K; June was the .in site 66 / 4.04K) and the Google Analytics 4-weekly mail.
Decisions: a block "Before they reach you — Google" on the Patients page (v10 published); the server reads the monthly mail by itself at build (the mailbox script already works this mailbox); the Google calls are matched with the Call Console's answered / missed (item 3); year-on-year fills as months accrue, or from the Business Profile performance page if it still holds older months (to check at build through his signed-in browser, read-only). Five months is too short for a proven correlation — said so on the page.

## ADDED 12-Nov 07:15 IST — the owner 06:37 IST: the mail's "See full report" shows the previous year too
Read in the built-in browser on manojz (signed in as the profile's manager; read-only): https://www.google.com/local/business/<profile id>/promote/performance?...&from=YYYY-MM&to=YYYY-MM&tab=N (tab 1 all, 2 calls, 4 bookings, 5 directions, 6 website). The picker offers SIX months only (Jun..Nov 2026); a single-month view gives the month's total, its % against the same month a year before, and a figure for EVERY DAY. The big headline digit renders wrongly in page text (304 for 404) — totals are taken from the daily table's sum (they equal the mail's calls / directions exactly). Script c1_google_vs_clinic.py holds the 153 daily values (interactions, calls, directions).
2026 vs the same month 2025 (Google's %): calls Jun +0.9, Jul +39.5, Aug -1.9, Sep +1.9, Oct +16.4 · directions +3.0, +25.8, +39.2, +8.0, +25.3 · interactions +1.5, +32.2, +18.7, +3.3, +19.9 · profile views +7.9, +45.4, -1.1, +4.8, +1.6 · searches -6.1, +88.9, -14.1, +6.4, +1.1. Implied 2025: directions 200 / 190 / 166 / 201 / 162; calls 229 / 185 / 209 / 208 / 159. Clinic new patients 2025 -> 2026: 169->192, 222->198, 161->211, 142->207, 141->187.
Correlations (honest): monthly, 10 points, directions vs new patients r 0.61, calls 0.24; weekly (21 weeks) directions 0.27, calls 0.24; daily on open days directions 0.33, calls 0.18, no next-day effect. MY EARLIER LINE "direction requests track new patients closely" WAS TOO STRONG — corrected on the page to "moderate, not exact".
Other: on the 21 days the clinic was closed, Google still brought 4.1 calls and 3.3 direction requests a day (about 17 calls a month); Monday is the busiest day (8.9 calls, 8.9 directions, 9.2 new patients); the highest call day was 28-Sep (31 calls).
Build decision: the server reads the Performance page's six months once a month (daily figures + year-on-year) so no month is lost when it rolls off; how it signs in is settled at build (the owner's Google sign-in stays his).
Mock-up v11 published.
