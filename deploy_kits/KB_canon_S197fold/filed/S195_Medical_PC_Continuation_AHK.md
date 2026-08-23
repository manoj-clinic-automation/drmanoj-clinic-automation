# S195 — continue on the MEDICAL PC: finish AHK auto-generation + guard-and-send

**For the Claude session running ON the medical PC (where Marg + Labmate live).**
Goal: finish the Marg daily-sale automation locally, with native control of Marg.

## Context (already done from the manojz session)
- **Email agent ⭐5 hardening** — LIVE on the VPS (label-tracked, always-reply). Done.
- **Marg guard-and-send kit** built + validated vs real reports: `guard_and_send.py`
  (reuses `marg_report.py`, exact live parser), `GUARD_AND_SEND.bat`, `SETUP_S195_MARG.md`.
  In the git repo `deploy_kits/S195_MARG/`; also a copy of the sender folder exists
  at medical `D:\SendToClinic\` (has `SEND_TO_CLINIC.bat` v3 + `token.txt` — secret,
  never read/print).
- **AHK macro** rewritten for **AutoHotkey v2** (owner downloaded 2.0.26):
  `marg_export_macro_v2.ahk` — in manojz `D:\Downloads\margsync\` and should be
  copied to medical `D:\SendToClinic\`. It reproduces the recorded export flow and
  (optionally) calls `GUARD_AND_SEND.bat`. `RunGuard:=false` until calibrated.
- **Method A (read .dbf) = PARKED**: Marg tables are XOR-encrypted (256-byte key);
  crackable via known-plaintext crib-drag but fragile — see
  `S195_Marg_dbf_Encryption_Finding.md`. Not needed for the daily flow.

## The recorded export flow (from psr.exe on medical, 21 Aug)
Marg home → click **Daily Sale** tile → dialog "BILL WISE SALES STATEMENT":
dates already show yesterday (Report From/To); **Report Type dropdown → Detail**;
**With Item Deta dropdown → Yes**; other fields Marg remembers (Cash/Cr/Disc=Both,
Day Total=Yes, Report For=2 Sale-S/R-Brk). Click **View** → press Enter 1-2× →
report opens → click **Excel** button at bottom → an Excel box → press Enter a few
times → Excel writes the file → close Excel. Login user 61376 writes
`D:\MARGERP\users\61376\report\REPORT_2.XLS` (note: the sender matches REPORT_1.XLS
— reconcile which user/report the daily flow uses).

## To do on medical (native control)
1. **AutoHotkey v2**: installer at `C:\Users\SET\Downloads` (or the portable
   `AutoHotkey_2.0.26.zip` in manojz margsync). Install/unzip.
2. **Calibrate the macro** by driving Marg directly: capture screen X,Y for the 5
   controls (Daily Sale tile, Report Type dropdown, With Item Deta dropdown, View,
   Excel button) and fill the CONFIG block in `marg_export_macro_v2.ahk`. Tune the
   Sleep/Enter counts by running F10 while watching.
3. **Guard prerequisites**: install Python + `pip install xlrd==1.2.0` on medical;
   copy `guard_and_send.py` + `marg_report.py` + `GUARD_AND_SEND.bat` into
   `D:\SendToClinic\`. Then set `RunGuard:=true` so the macro validates before send.
4. **End-to-end test**: F10 → Marg generates today/yesterday's Detail export →
   guard validates (stops if truncated/wrong date) → SEND_TO_CLINIC pushes →
   Dr Manoj applies at the Hub. Maker/checker (D325) unchanged.
5. Optional: a Task Scheduler job runs `GUARD_AND_SEND.bat <expect> AUTO` (or the
   macro) at a set morning time.

## Guardrails (unchanged project protocol)
Plain language; ONE step at a time, wait for OK; mask patient numbers to last-4;
never read/print `token.txt` or secrets; nothing live rebuilt without OK; manual
workflow stays as fallback.
