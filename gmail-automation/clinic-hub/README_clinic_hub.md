# Clinic Hub (repo copy — CANONICAL)

Live location on clinic PC: `D:\clinic_hub\`. **This GitHub folder is the canonical copy** —
the hub is a shared surface across both Claude projects (website track + Clinic Systems &
Automation). Whichever project edits the hub must start from this copy and commit back here.

Cards / ports (as of 2026-07-26):
- Surgical Case Pack — 127.0.0.1:5058/case — `D:\casepack tool\casepack_app.py`
- Follow-up Tracker — 127.0.0.1:5000 — NOT auto-started (its own `open_tracker.bat`
  archives CSVs first — safety ritual; one upload per clinic day)
- Vitals & Plan — 127.0.0.1:5057/vitals — `D:\clinic_writer\vitals_app.py`
- GMB Review Assist — plain file, relative link, no server
- CC Statements → Tally — 127.0.0.1:5059 — `D:\Scripts\statements_app.py`
  (auto-runs once daily on hub start; on-demand button inside)

`open_clinic_hub.bat` is SELF-CONTAINED: direct `start /D` python launches with port +
file-existence checks; it never calls per-tool bats. If a tool moves, edit its `set ..._DIR=` line.

Known accepted quirk: hub launch also opens tabs self-opened by casepack/vitals apps
(fix designed: HUB_LAUNCH env guard — deferred).
