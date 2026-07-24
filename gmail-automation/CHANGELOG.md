# Changelog — gmail-automation suite

## v2.2.1 — 2026-07-24
- Statements runner integrated into Clinic Hub: `scripts/statements_app.py`
  (Flask, 127.0.0.1:5059) with Run-now button, last-run badge, output view,
  unified logging to process_statements.log
- Auto-runs once daily on hub launch (20-hour guard) — hands-off processing
  without a scheduled task
- `clinic_hub.html` + `open_clinic_hub.bat` patched: new "CC Statements → Tally"
  card wired into the port-probe array; launcher starts the service if the port
  is free, with the existing error-reporting pattern preserved
- **Task Scheduler approach evaluated and dropped** — hub launch is the reliable
  daily ritual and catches up after missed days; a fixed-time task cannot
- clinic-hub/ added to the repo (hub, launcher, runner, GMB assist)
- Documentation consolidated: DOSSIER.md is now the sole reference and
  supersedes KB_MASTER.md (removed)
- Repo folders renamed to mirror the live PC layout exactly: `scripts/`
  (was `pc-scripts/`) now maps 1:1 to `D:\Scripts` and holds BOTH Python
  files (process_statements.py + statements_app.py); `clinic-hub/` holds only
  what lives in the hub folder (clinic_hub.html, open_clinic_hub.bat, GMB assist)

## v2.2 — 2026-07-23 — operational close-out
- Janitor rules engine gained `markRead`; NEW auto-reports rule (2d) and
  vendor-promos rule (1d)
- Sweeps: OTPs trash @1d, content newsletters trash @1d (JustDial excepted —
  EPP transfer mail protection), MyOperator archive @7d (never trashed,
  alert.myoperator.info excluded), CC-Saved archive @30d
- RENEWALS 17 → 26: personal documents merged; arms licence CONFIRMED expiry
  26-12-2026 (action 27-Sep-2026, 5-year cycle); Vento RC (action 01-May-2028);
  Bhawna DL TODO placeholder
- ANNUAL_RENEWALS[6] introduced: Nagar Nigam ×2 (Jan), municipal taxes (May),
  Bareilly Club (Jun), TVS insurance (05-Dec), Aviator insurance (19-Jan)
- Idempotent `applySheetUpdatesOnce()`; Master v2 grown to 26 rows; Personal
  Documents sheet corrected — both verified by direct Drive read
- Gmail housekeeping: 35 threads trashed, 32 archived to Vendor-Archive,
  95-thread report backlog swept; daily triggers set for both GAS projects
- Renewals Master v2 canonical ID corrected to 1OB70_Mapuugc33zkfFevwnrS0e8s1NdWzsrzJDqO38E
- Notion Tech & Systems Register row created (page 3a618b9d-8f91-81e1-88a9-e35794da694a)

## v2.1 — 2026-07-22/23
- Three-rule janitor, Payment Register + monthlyPaymentDigest, 17-entry
  RENEWALS synced (17 events), label cleanup (~55 removed)
- CC Statement Saver deployed (32 statements captured)
- process_statements.py validated: 32 decrypted, 244 transactions, spot-checked

## v1 — 2026-07
- Initial renewals sheet (superseded, trashed)
