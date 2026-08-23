# S195 — MEDICAL-PC LEG — close summary & pins (one-off special session)

**Session 195 · 21-Aug-2026 · run directly ON the medical PC** (Marg + Labmate box),
folder `D:\SendToClinic`. This is a **special, one-off leg of S195**: unlike every other
session in this project, it did not run against the VPS / git canon at all — it ran on the
clinic's own Windows PC through the Claude desktop **file bridge** (read/write files only; no
ability to execute programs there). Recorded here so the context is on the permanent record.

Companion detail doc (full runbook): **`S195_Medical_PC_Macro_Guard_Runbook.md`**.

---

## What this leg did (all on the medical PC, nothing on the VPS)

Finished the **Marg daily-sale auto-export + guard-and-send** so a report can be generated
inside Marg and validated before it is sent — the Phase-2 item the earlier S195 (manojz) leg
had left pending for lack of a medical-PC session.

1. **Deployed the canonical medical kit** to `D:\SendToClinic` (from `claude/S195_medical_kit/`):
   `guard_and_send.py`, `marg_report.py`, `GUARD_AND_SEND.bat`, `SETUP_S195_MARG.md`.
2. **Wrote + calibrated the AutoHotkey v2 macro** `marg_export_macro_v2.ahk` by driving Marg
   directly (5 control positions captured on the box) and **passed an export-only test** —
   Marg re-wrote its report and the macro reported "Export finished". Guard stays OFF
   (`RunGuard := false`) so nothing is sent yet.
3. **Made the guard run with zero install:** python.org is blocked from the Claude side and the
   PC had no real Python (only the Microsoft-Store stub), so a **portable CPython 3.11.9** was
   trimmed to a 12 MB zip, shipped through the bridge, and unzipped to `D:\SendToClinic\pyportable\`;
   **xlrd 1.2.0 was vendored** into `D:\SendToClinic\xlrd\` (no `pip`). Launchers now auto-find
   the bundled Python and skip the Store stub. `SETUP_CHECK.bat` ran **GREEN** on a bundled
   sample (`RESULT: PYTHON_OK`, exit 0).

## Live pins — VPS: UNCHANGED this leg
No VPS file moved. The S194 FINAL LIVE PINS still stand and `verify_live_pins.py` is unaffected:
`finance_app.py d2863c30…` · `finance_ingest.py 6cb83302…` · `finance_daily.html 7ac94934…` ·
`finance_approvals.html 402fa7b2…` · `staff_ledger.py acd7b538…`.

## Medical-PC file record — `D:\SendToClinic` (md5 · bytes)
```
marg_export_macro_v2.ahk   acec9ae9c1417e2fda8222e41e0628aa    6683   CALIBRATED, RunGuard=false
guard_and_send.py          6c248d5712731256c576722ad85f3ef1   10837   canonical (== server parser)
marg_report.py             28b47d447cfd966411742055717a5c56   31482   canonical (== server parser)
GUARD_AND_SEND.bat         4d66ff96aeb7f4691b88806b9d291c16    3870   auto-finds portable Python
SETUP_CHECK.bat            990a6e120e7817b83fe969ee35df0bb6    1586   one-click self-test → GREEN
SETUP_S195_MARG.md         cc4416dc8f22a998b0a18dd42c4d8b99    4936   kit readme (install steps superseded)
_setup_sample.xls          58209bb1041f7dc0b4e59bd4ccd4d8ab    5632   test fixture
xlrd\  (11 files)          xlrd 1.2.0 pure-python                     vendored — no pip
pyportable\               CPython 3.11.9 (pbs, trimmed)              portable engine, no install
```
The two `.py` md5s are **byte-identical to the canonical build-state** (D247), so the guard's
judgment == the server's. `token.txt` and `SEND_TO_CLINIC.bat` were never read or modified.

## Calibrated macro (for re-use / re-calibration)
Keys (no Fn needed, HP laptop): **Ctrl+Alt+C** capture · **Ctrl+Alt+G** run · **Esc** quit.
Positions (maximised Marg): Daily Sale `1804,941` · Report Type `1132,850` · With Item Deta
`984,992` · View `641,1414` · Excel `1391,1254`. `ReportFile = …\users\61376\report\REPORT_2.XLS`.

## Still pending (next medical-PC session)
1. **Reconcile REPORT_1 vs REPORT_2 / which login** before joining macro → guard (macro writes
   REPORT_2 for user 61376; the guard/sender scan REPORT_1).
2. **Flip `RunGuard := true`** and run ONE confirmed end-to-end test (generate → guard → SEND
   stages for review; Dr Manoj still applies). First real send — do deliberately.
3. **Task Scheduler** unattended morning run (`GUARD_AND_SEND.bat any AUTO`), after a hand test.
4. Later: replicate for the Lab PC / Labmate.

## Guardrails honored
Plain-language, one-step-at-a-time; `token.txt` never read/printed; `SEND_TO_CLINIC.bat` and
`D:\MARGERP` untouched; nothing live rebuilt; manual workflow remains the fallback; patient
numbers masked to last-4 by `marg_report.py`.

## EOS accounting (what is done vs owed)
- **A0/A1 (record):** this doc + `S195_Medical_PC_Macro_Guard_Runbook.md` (both in project KB).
- **A2 Register / A7 Manifest / A8 live_pins:** **NOT bumped** — correct, because this leg moved
  no VPS pin and no D/F number. The **S193+S194+S195 canon monolith fold remains OWED** (carried
  from START_HERE_195; do it at a manojz session with box access, where `gen_live_pins.py` and
  `verify_live_pins.py` run).
- **A4 START_HERE:** `START_HERE_SESSION_195.md` updated with a medical-leg addendum.
- **A9 Notion:** session-log entry in Clinic HQ (see close report for URL / owed status).
- **C GitHub:** medical kit lives in project KB; optional repo home is `deploy_kits/S195_MARG/`
  (owner push — not reachable from the medical-PC bridge).
- No D-number, no F-number minted (kit deployment + calibration, not an architecture decision).
  Next-free unchanged: **D334 · F-160 · A-D25 · Session 195**.

---
*S195_Medical_PC_Close_Summary — the EOS record for the one-off medical-PC leg of Session 195.*
