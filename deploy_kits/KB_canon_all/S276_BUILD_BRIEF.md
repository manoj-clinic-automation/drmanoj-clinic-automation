# S276 BUILD BRIEF — four backlog items live in one day; the X-ray filing still waits on staff files

*Session 276 · the parent project · 20-Sep-2026 · written at the close. The one document for the next session.*

---

## 1 · WHAT WENT LIVE TODAY (each from your one line)

| kit | what it does now | proof |
|---|---|---|
| **S347_SPINE_BACKUP** (10:55) | The pharmacy spine — `spine.db`, its 159 readings, its code and rule files — is in both nightly backups from tonight. It had been in none. | preflight OK on the box: `spine.db integrity ok · would include 251 files` (was 90) |
| **S348_DAILY_REPORT_ATTENDANCE** (11:15, Apps Script) | The Daily Clinic Report's attendance line reads your own attendance server's 21:00 mail. It had said *"Attendance report not received"* every day since 02-Aug — the old ONtime machine's mail stopped on 01-Aug. | live run: 19-Sep · 12 present · 0 absent · 9 late with names |
| **S349_WATCHER_FRESHNESS** (12:42) | The health card's *Medical PC capture* row goes **red** when the medical PC's heartbeat is stale **during clinic hours** (9–21, Sundays off unless you set `pipeline.clinic_sunday` = 1); info at night. And the freshness table is a page. | page read live: 31 legs · 31 OK |
| **S350_FRESHNESS_CLOCK** (12:48) | The page's "written N ago" line reads the real clock (it said 0 min for a 4-hour-old file). | re-read live: *written 08:05 IST (4.7 h ago)* |

```
https://followup.dr-manoj.in/finance/freshness
```
```
https://followup.dr-manoj.in/finance/health
```

## 2 · NEXT — in order

1. **The live X-ray filing** the day the *X-ray test* folder holds 2–3 days of staff files (`S273_BUILD_BRIEF.md §2`, unchanged). Nothing else is ahead of it.
2. `gas_export.py`'s weekly comparison still points at the old S230 photograph of the daily-report script and will say "drift" from next Sunday — true, expected, and mine to repoint (F-591).
3. **Two lines that are yours, whenever you like** (neither is urgent): the nightly unattended task's stored prompt still names `START_HERE_PROMPT_v8` (repoint to v10 — a scheduled task's prompt is yours); and its reports live only in project knowledge until you say they may go into the repository (proposal (c)).
4. Carried: the phonebook from your two exports · the last four units into the backup (your ruling on `fitlog` / `gutlog` / `rxguard` / `email-agent`) · fault injection for `backup`/`outbox` · Bhati's petty-book layout (offered) · Docterz uploads stop on your word · bank-SMS PARKED.

## 3 · PINS

| file | pin |
|---|---|
| `/root/state_backup/code_bundle.py` | `8200dcca2256a843ccabcdbd8250ec55` (S347, v1.7) |
| `/root/state_backup/clinic_state_backup.py` | `05397337a09fbb3eafcc02bb12f3267d` (S347, v4) |
| `/root/finance/finance_app.py` | `29819879dec3f057b7690e004e4e87cb` (S349) |
| `/root/finance/freshness_page.py` | `5c38847eb99e8e530500c1f704bf8cba` (S350) |
| Apps Script `DailyClinicReports/Code.gs` | v6.1, masked-text hash `cb859b0f` (S348) |

## 4 · THE LESSON (F-590)

A walk that supplies the very input a defect could live in proves nothing about it. S349's walk handed the page its
own clock and passed 28 checks; the live page was wrong by five and a half hours. **Every walk keeps one check on
the real thing — the real clock, the real path, a real row.**

*S276 · 20-Sep-2026. Decisions D578–D581, findings F-585–F-591.*
