# Follow-Up Tracker — Update Kit (11 Jun 2026, build B)
**Deploy = replace code files only. NEVER touch the `data\` folder.**

## What changed

**P0-01 — One visit closes ONE follow-up.** A patient with several pending
follow-ups no longer has all of them closed by a single return visit. Each
visit is "consumed" by exactly one obligation (earliest due first). New ledger
column `Matched_Visit_ID` records which visit closed which follow-up; old
terminal rows are retro-linked automatically on the first run.

**Prescribing-visit fix (found during testing).** Previously, a "come
tomorrow" follow-up was instantly marked *Returned Early* by the very visit at
which it was prescribed — silently hiding next-day dropouts. Matching is now
strictly AFTER the log date. Trade-off: a patient who genuinely returns one
day early will briefly show as due/missed until staff call. Constant
`COUNT_LOG_DATE_VISIT_AS_RETURN` in processor.py flips this back if ever needed.

**P0-02 — 60-day expiry.** Follow-ups >60 days overdue become
**Expired Unresolved**: hidden from Staff Action Today (no more stale rows),
counted on the Dashboard, kept in the ledger, and still reconciled to
*Returned Late* if the patient eventually comes back. Stale identity-problem
rows expire the same way. Tune via `EXPIRY_DAYS`.

**P0-03 — Diagnosis keyed by Patient UID.** Diagnosis/Priority/VIP now attach
by UID, never by a shared family mobile. Run `migrate_diagnosis_add_uid.py`
ONCE after deploying to add the UID column to `patient_diagnosis.csv`
(it backs up first, fills unique-mobile rows automatically, and lists the few
shared-mobile rows for one-time manual assignment).

**Roles (VPS-ready).** Two passwords: `TRACKER_PASSWORD` (staff) and
`TRACKER_ADMIN_PASSWORD` (admin). On a server the app REFUSES to start if
either is missing or they match — the `clinic2026` default is gone. Staff can
upload CSVs and download only `Staff_Action_Today_<date>.xlsx` (action sheet +
vacation list). Admin gets the full audit, master initialisation, and the
vacation editor. **The clinic PC is unaffected:** `TRACKER_LOCAL=1` keeps
running with no login, as admin.

**Vacation calendar.** Admin panel: add/remove unavailability periods
(from–to, Morning / Evening / Full Day, note). Follow-ups due inside a window
get a **Doctor Unavailable** flag on the action sheet and appear in a new
**Vacation Notice List** sheet (High/Medium-confidence mobiles only) — the
list staff use to inform patients now, and the feed for the WABA
unavailability template later. Stored in `data\vacation_calendar.csv`.

**Taxonomy message provisions (no sending).** New **Msg Category** column on
the action sheet. `TAXONOMY_MESSAGE_MAP` in processor.py maps diagnoses to
template categories — RA/AS → `inflammatory_arthritis_bilingual` is pre-wired;
add fracture/OA lines when those templates exist. Nothing is messaged today.

## Deploy steps (clinic PC)
1. Close the tracker.
2. Copy in `processor.py`, `app.py`, `migrate_diagnosis_add_uid.py` (Replace).
3. Run once: `python migrate_diagnosis_add_uid.py` — assign any listed
   shared-mobile rows manually in `patient_diagnosis.csv`.
4. Restart the tracker; run a normal day. First run backfills
   `Matched_Visit_ID` and applies expiry — expect the Dashboard's open count
   to DROP as stale rows archive. This is correct, not data loss.

## For the VPS build later
Set both password env vars (different values). Everything else ships as-is.

## Known note
The old `test_suite.py` expects `run_daily()` to return one path; it now
returns `(audit_path, staff_path)`. `test_fixes.py` in this kit covers the
new behaviour (19 checks, all passing).

---

## HOTFIX (same day) — tracker wouldn't open after the update

**Cause:** the new "refuse to start without passwords" check ran at *import*
time. On the clinic PC the launcher imports the app before local-mode is set,
so the check killed the server — Chrome opened but the page never loaded.

**Fix:**
- The credential check now runs ONLY when a real server starts (VPS), never at
  import. Importing the app can no longer crash the launcher.
- Added a hardened `run_local.py`: it sets local mode *before* importing the
  app, picks a free port if 5000 is busy, and opens the browser only *after*
  the server is confirmed up.

**To recover right now:** copy `app.py` and `run_local.py` from this kit into
the tracker folder (Replace), then launch as usual. No data touched.
