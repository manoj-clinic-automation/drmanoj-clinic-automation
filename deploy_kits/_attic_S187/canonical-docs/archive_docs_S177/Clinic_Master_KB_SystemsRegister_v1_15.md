# Clinic Master KB / Systems Register — v1.15
**Dr. Manoj Agarwal · Advanced Orthopaedic Surgery Centre, Bareilly**
Canonical reference for all infrastructure, identity, parameters, and decisions. If anything elsewhere disagrees with this file, **this file wins.**

> **Delta document for v1.15.** Carries forward everything in v1.14 unchanged and adds Session 27 (§27), an updated state line in §12, four new decisions (D44–D47), and a changelog entry. All prior sections and decisions (D1–D43) remain in force verbatim.

---

## §12 STATE — what is live right now (updated at Session 27 close)

- **Callback + Follow-Up Dashboard** (Apps Script) — LIVE at **build v17.8** (confirmed). **v17.9 DELIVERED but not yet confirmed deployed** (Slice 2b, needs Drive re-auth). Session 27 added: "Today's calls" live-stream section, dark-theme fix, follow-up last-visit, back-to-top, and (delivered) follow-up archived-recording playback.
- **`CallConsole.gs`** — the additive server layer for the Call Console. Now at **v1.1f**: `getAllCallsToday` (name/ClinicID-if-present/diagnosis/last-visit), `getAgentIdentity`, `logOutcome` → `Outcomes_Log`, `getFollowupLastVisits`, `getFollowupRecordings`, `getArchivedRecordingAudio`. **First DriveApp use in the dashboard project** (needs Drive scope authorized).
- **Stage 1 (recording archive, 02:00)** + **Stage 2 (Sarvam transcription, 03:00)** — LIVE, unchanged.
- **Follow-up watcher** (Task Scheduler, clinic PC), **Launcher portal** (:8099), **Revenue Reconciler**, **WA receiver/notifier**, **Attendance** — LIVE, unchanged.
- **Diagnostics.gs / System_Health tab** — NOT built (confirmed again absent at session start).
- **GitHub repo** — now **PUBLIC** (code-only; secrets/PHI gitignored).

---

## §27 SESSION 27 — Call Console build (v17.4 → v17.9), Clinic ID data gap found, follow-up recordings

**Theme:** execute `Call_Console_Evolution_Spec v1.1` in safe additive slices on the live dashboard; `WebApp.gs` never touched.

**Shipped (deployed + verified):** last-visit in `getAllCallsToday` · "Today's calls" live-stream section (v17.5) · dark-theme fix (v17.6) · follow-up last-visit via `getFollowupLastVisits` (v17.7) · back-to-top (v17.8).

**Delivered (deploy pending, Drive re-auth):** follow-up "🎧 Last call" — `getFollowupRecordings` + `getArchivedRecordingAudio` (v17.9 / CallConsole v1.1f).

**Investigated / parked:** numeric Clinic ID — `Patient_Master` (the tab the dashboard reads) has **no numeric Clinic ID column** (`mobile · patient name · diagnosis · age · gender · last visit · patient uid`). Code reads `Clinic_Specific_Id` if present, else blank. Un-park = add that column from Docterz.

**Finding (backlog):** `Followups_Today.section` is uniformly "Follow-up"; sub-sections (grace period, dropout) must be written by the Follow-Up Tracker push script (dashboard already groups by section).

**Deferred still:** Step 3 (doctor Escalation/Resolve console §7) and Step 4 (staff Flagged Calls tab §8) — the remaining big spec pieces.

---

## DECISIONS (new this session)

- **D44 — GitHub repo made public.** `drmanoj-clinic-automation` is now public so Claude can read code files reliably via `raw.githubusercontent.com` (the Drive connector was patchy). Secrets and PHI remain gitignored; no sensitive data exposed. (GitHub API listing is rate-limited on shared IP; raw file reads are the reliable path.)
- **D45 — Numeric Clinic ID is a DATA gap, not a code bug.** The `Patient_Master` tab read by the dashboard carries only the alphanumeric `patient uid`, not the Docterz numeric `Clinic_Specific_Id`. Dashboard code reads a `Clinic_Specific_Id` column IF present (blank otherwise; never the UID or name). The numeric ID appears dashboard-wide only after that column is added to `Patient_Master`. No further code needed.
- **D46 — Follow-up recordings play from the permanent Drive archive, streamed by File ID.** `getArchivedRecordingAudio` reads the archived MP3 via `DriveApp.getFileById` (the web app runs as the owner), because older calls' 24h MyOperator links are dead. This introduces the **first Drive OAuth scope** in the dashboard Apps Script project (one-time re-authorization required).
- **D47 — Follow-up sub-sections are written at the source.** The dashboard already groups the follow-up area by the `section` column; the Follow-Up Tracker push script must write the Staff-Action category (grace period / dropout / etc.) into that column. Currently all rows say "Follow-up".

---

## CHANGELOG
- **v1.15** (01 Jul 2026, Session 27): +§27, state line updated, D44–D47 added. Dashboard v17.4→v17.9 (v17.8 live, v17.9 delivered). `CallConsole.gs`→v1.1f (first DriveApp use). Repo public. Clinic ID data gap identified + parked. Follow-up last-visit + archived-recording playback added.
