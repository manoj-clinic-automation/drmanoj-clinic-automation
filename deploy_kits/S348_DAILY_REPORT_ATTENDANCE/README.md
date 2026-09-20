# S348_DAILY_REPORT_ATTENDANCE — the daily report reads the clinic's own attendance mail again

*Session 276 (parent) · 20-Sep-2026 · a RECORD kit: nothing to install. The change is live in the Apps Script project.*

## What was wrong

The **Daily Clinic Report** (Apps Script `DailyClinicReports`, 11:39 IST) had printed *"Attendance report not
received"* every day since **02-Aug-2026**. Its attendance section looked for the ONtime biometric machine's mail
(subject *ONtime Employee Manager Report*, an ABSENT csv attached). **That mail last arrived on 01-Aug-2026** — the
clinic's own attendance server (S153) has mailed *"Attendance — day summary (DD Mon): N present, M absent"* at 21:00
IST every day since, into the same mailbox, and nothing read it. (The unattended lane named this on five nights; the
S269 close put it on the owner's build list as item 7.)

## What changed — Code.gs v5 → v6.1, five anchored edits, in the owner's signed-in browser

- `CONFIG.ATTENDANCE_SUMMARY_SUBJECT = 'Attendance — day summary'`, read **first**; the ONtime path stays as the fallback.
- `processAttendanceSummary_()` + `parseAttendanceSummary_()`: the newest day-summary mail (yesterday's — the day the
  digest covers), parsed from its **HTML body** (three count boxes; the PRESENT table whose Name cell carries
  `<b>(late Nm)</b>`; the ABSENT heading followed by one div of names or *None*), with the tag-stripped plain rendering
  as a fallback.
- The digest's attendance section now reads **"N present · M absent: names · K late (name Nm, …)"**; the old
  *"Attendance report not received"* line remains for the day neither mail exists.
- `previewAttendance()`: a read-only proof — logs what the section would say; sends nothing.

Every edit was applied **inside the page** (the live text never left the browser; the four MyOperator values were
never read): the live text's masked hash `d0a17cbb` equalled the S230 photograph, and after the save the page's masked
hash `cb859b0f` equals `DailyClinicReports/Code.gs` here. The edit scripts (`edit_v6_s276.js`, `edit_v6_1_s276.js`) are
the anchored replacements as run.

## Proof

- Offline: the whole file evaluated under node with GAS stubs (syntax); the parser on the real 19-Sep mail HTML
  (12 present · 0 absent · 9 late with names), on a 2-absent variant, on the plain rendering, and on garbage (null).
- **Live, read-only:** `previewAttendance` run in the editor, 11:15 IST 20-Sep:
  `found:true · dated "19 Sep" · present 12 · absentees [] · late 9 · lateList [Shivani 8m, Sandip 6m, …] · source "summary" · notes []`.
- **The first live run caught what the offline test could not (F-581 class):** v6 read `getPlainBody()` and the mail
  is HTML-only, so the shape the parser expected was not there; v6.1 reads the HTML first. Recorded, not hidden.

## What this kit does NOT do

- `deploy_kits/S230_GAS_EXPORT/` is frozen (F-512) and still holds the v5 photograph. `gas_export.py` (Sunday 02:20)
  compares live against S230 by line count and function names for this masked file, so from next Sunday it will
  report shape drift on `DailyClinicReports` — **true, and expected** — until its `REPO_COPY` is pointed at a current
  photograph. Named to the next close; not done here.
- The ONtime path was not removed.
- `appsscript.json` is unchanged from S230 and is not carried here (it is a blanket-ignored .json; S230 holds it).

## After

Tomorrow's digest (21-Sep, 11:39 IST, *Data for 2026-09-20*) should read the 20-Sep day summary. Read it before
calling this done at the next open.
