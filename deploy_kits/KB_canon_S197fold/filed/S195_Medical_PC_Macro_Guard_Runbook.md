# S195 — Medical PC: Marg auto-export macro + guard-and-send — DEPLOYMENT RUNBOOK

**Session 195 · 21-Aug-2026 · built and verified directly on the MEDICAL PC**
(the PC where Marg + Labmate run, folder `D:\SendToClinic`).

This is the single doc to open to *see* and *re-run* the whole Marg daily-sale
automation. It supersedes the "install Python / pip install xlrd" steps in
`SETUP_S195_MARG.md` — the guard now ships with its **own** Python and xlrd, so
there is nothing to install.

---

## 1. TL;DR — current state

| Piece | State | Proven how |
|---|---|---|
| **Auto-export macro** (drives Marg → REPORT_x.XLS) | **CALIBRATED & PASSED** (export-only) | Ran clean on medical PC; Marg re-wrote the report; "Export finished" shown |
| **Guard** (validates a report before send) | **LIVE & PASSED** | `SETUP_CHECK.bat` → GREEN on sample, exit 0 |
| **Python engine** | **Bundled portable** `pyportable\` (CPython 3.11.9) | No install, no admin, no PATH change |
| **xlrd 1.2.0** | **Vendored** in `xlrd\` | `pip install` step eliminated |
| **Full end-to-end** (macro → guard → SEND_TO_CLINIC) | **PENDING** — needs `RunGuard := true` + one confirmed live test | — |
| **Task Scheduler** (unattended morning run) | **PENDING** | — |

`RunGuard := false` right now → the macro **generates the report only** and
sends nothing. Maker/checker (D325) intact: the sender only **stages**; **Dr
Manoj alone applies** at the Hub. `token.txt` and `SEND_TO_CLINIC.bat` were never
read or modified.

---

## 2. Where it runs, and how a Claude session reaches it

Everything lives on the **medical PC** at `D:\SendToClinic`. Marg's GUI must be
driven on that machine.

**Important for future Claude sessions:** the hands-on parts (running the macro,
calibrating, running the guard) can only be done from a Claude session whose
**device bridge is connected to the medical PC** — i.e. the Claude desktop app
running *on the medical PC*, with `D:\SendToClinic` added as a folder. A session
on the **manojz** PC can *read this doc and all the code* (it is all in the
project KB / below) but **cannot** drive Marg or run the guard on the medical PC.

What the bridge allows (medical-PC session): list / read / **write** files under
`D:\SendToClinic` (and `C:\Users\SET\Downloads`). It does **not** allow running
programs — so installers, `pip`, `python` and AutoHotkey are launched by the
human double-clicking, not by Claude. That is why the engine is shipped as files
(portable Python + vendored xlrd) rather than installed.

---

## 3. File inventory — `D:\SendToClinic` (what was deployed this session)

md5 pinned for the files that matter. The two `.py` md5s match the canonical
build-state (D247 manifest): `marg_report.py` and `guard_and_send.py` are
**byte-identical to the server's own parser** — the guard's judgment == the
server's.

```
marg_export_macro_v2.ahk   acec9ae9c1417e2fda8222e41e0628aa   6683 B  (CALIBRATED)
guard_and_send.py          6c248d5712731256c576722ad85f3ef1  10837 B  (canonical)
marg_report.py             28b47d447cfd966411742055717a5c56  31482 B  (canonical)
GUARD_AND_SEND.bat         4d66ff96aeb7f4691b88806b9d291c16   3870 B  (updated: auto-finds portable py)
SETUP_CHECK.bat            990a6e120e7817b83fe969ee35df0bb6   1586 B  (one-click self-test)
SETUP_S195_MARG.md         cc4416dc8f22a998b0a18dd42c4d8b99   4936 B  (kit readme; install steps now superseded)
_setup_sample.xls          58209bb1041f7dc0b4e59bd4ccd4d8ab   5632 B  (test fixture for SETUP_CHECK)
xlrd\  (11 files)          xlrd 1.2.0, pure-python           vendored library
pyportable\               CPython 3.11.9 (astral python-build-standalone, trimmed)  portable engine
pyportable\Lib\site-packages\distutils-precedence.pth   — neutralized (silences a harmless startup warning)
```

Untouched, pre-existing (do NOT rebuild without OK): `SEND_TO_CLINIC.bat`,
`token.txt` (**never read/printed**), `Sent\`, `send_log.txt`, `sent_hashes.txt`,
`COPY_MARG_DATA.bat`. Also present: `AutoHotkey64.exe` (owner copied it here —
convenient for launching the macro), `marg_macro_calib.txt` (the F9/Ctrl+Alt+C
capture log — history only), `pyportable.zip` (the source zip; can be deleted
once `pyportable\` exists).

---

## 4. The auto-export macro — `marg_export_macro_v2.ahk`

AutoHotkey **v2** script. Launch it by dragging the `.ahk` onto
`AutoHotkey64.exe` (or right-click → Open with → AutoHotkey64.exe). A green **H**
tray icon = loaded.

**Keys (chosen to need NO Fn key — this is an HP laptop, function keys are media
keys by default):**
- `Ctrl+Alt+C` — capture mouse X,Y into `marg_macro_calib.txt` (calibration)
- `Ctrl+Alt+G` — **run the export** ("G" = Go; `Ctrl+Alt+R` was being eaten by a
  screen recorder, so G is the real run key. F10 also works if the keyboard
  sends a true F10.)
- `Ctrl+Alt+Q` or `Esc` — quit the macro

**Calibrated screen positions (captured on the medical PC, maximised Marg — if
Marg's window is moved/resized or the screen resolution changes, re-calibrate):**

```
Daily Sale tile      X=1804  Y=941
Report Type dropdown X=1132  Y=850   (selects "Detail")
With Item Deta.      X=984   Y=992   (selects "Yes")
View button          X=641   Y=1414
Excel button         X=1391  Y=1254
```

**Other CONFIG knobs** (top of the file): `RunGuard` (false now), `GuardBat`,
`ReportFile = D:\MARGERP\users\61376\report\REPORT_2.XLS` (the file Marg writes
for login 61376 — note the sender scans `REPORT_1.XLS`; reconcile which
user/report the live daily flow uses before turning on `RunGuard`), `SET_DATE`
(false — Marg already shows yesterday), and the `Sleep`/`Enter` timings.

**Flow it performs:** click Daily Sale → set Report Type=Detail → With Item
Deta=Yes → View (+Enter ×2) → wait → Excel (+Enter ×4) → wait for the .XLS to be
re-written → close Excel → (if `RunGuard`) call `GUARD_AND_SEND.bat`.

**To re-calibrate:** launch macro, open Marg, do the export slowly by hand, and
at each of the 5 controls hover + press `Ctrl+Alt+C`. Read the 5 new lines from
`marg_macro_calib.txt` and paste them into the CONFIG block (or ask Claude to).

---

## 5. The guard — `guard_and_send.py` (+ `marg_report.py`, portable Python, vendored xlrd)

Validates a `REPORT_1.XLS` and refuses to send unless it is a single-day
**Detail** export (9-col, not the CASH-less Summary-1), ends with `GRAND TOTAL :`
(not a truncated partial), its arithmetic balances, and its business date is
sane. On GREEN it copies to `Sent\` named by the date it covers
(`REPORT_2026-08-19.XLS`). It sends nothing itself; `GUARD_AND_SEND.bat` calls
`SEND_TO_CLINIC.bat` only when the guard exits 0.

**How it now runs with zero install:** `GUARD_AND_SEND.bat` (and
`SETUP_CHECK.bat`) auto-select a working Python in this order — bundled
`pyportable\python.exe` → `py` → `python` — and they *test* each candidate by
actually running it, so the Microsoft-Store "python" stub (which answers `where
python` but fails to run) is skipped. `xlrd` is found automatically because it
sits in the same folder as the scripts (script dir is on `sys.path`).

**Run the guard by hand (no send):**
```
D:\SendToClinic\pyportable\python.exe D:\SendToClinic\guard_and_send.py "D:\MARGERP\users\61376\report\REPORT_1.XLS" --expect any
```
Date rules: `any` (default, single-day ≤3 days old) · `yesterday` · `today` ·
`2026-08-19` (exact). GREEN = safe; REFUSED = reason on screen + in
`guard_alerts.txt`.

**Self-test any time:** double-click `SETUP_CHECK.bat` → writes `setup_check.txt`
(`RESULT: PYTHON_OK` + a GREEN line = everything healthy).

---

## 6. Daily operation (reception) — unchanged from the kit

Instead of `SEND_TO_CLINIC.bat`, reception double-clicks **`GUARD_AND_SEND.bat`**.
It checks every `REPORT_1.XLS` under `D:\MARGERP\users\*\report\` and sends only
the ones that pass; otherwise it prints why (Hindi messages built in). Everything
downstream (archive, MD5 de-dup, ACCEPTED-FOR-REVIEW, Dr Manoj's Apply) is
unchanged.

---

## 7. What was verified this session

- `marg_report.py` / `guard_and_send.py` md5s match the canonical build-state
  (byte-for-byte the server's parser). Both `py_compile` clean.
- Export-only macro run on the medical PC: completed and Marg re-wrote the
  report ("Export finished").
- Guard chain proven with **only** the vendored xlrd (system packages disabled):
  GREEN on a good file (exit 0), REFUSED on a wrong date (exit 2).
- On the PC: `SETUP_CHECK.bat` → interpreter `D:\SendToClinic\pyportable\python.exe`
  (Python 3.11.9), guard GREEN on the sample, `RESULT: PYTHON_OK`.

---

## 8. Remaining next steps (for the next medical-PC session)

1. **Reconcile REPORT_1 vs REPORT_2 / which login.** The macro writes REPORT_2.XLS
   for user 61376; the sender/guard scan REPORT_1.XLS. Confirm the real daily
   path before turning on the guard hand-off.
2. **Flip `RunGuard := true`** in the macro (one edit), then run **one** confirmed
   end-to-end test: `Ctrl+Alt+G` → generate → guard validates → `SEND_TO_CLINIC`
   **stages** (Dr Manoj still applies). This is the first real send — do it
   deliberately, watching.
3. **Task Scheduler** unattended run: `GUARD_AND_SEND.bat any AUTO` (the `AUTO`
   word suppresses prompts). Test once by hand, then set the morning time.
4. Later: replicate for the Lab PC / Labmate.

---

## 9. How this was produced (so it is reproducible)

- xlrd 1.2.0 wheel pulled from PyPI, `xlrd/` package placed next to the scripts
  (pure python — no build step, works on any OS/Python 3).
- Portable Python = astral **python-build-standalone** CPython 3.11.9
  `x86_64-pc-windows-msvc` "install_only", trimmed (removed test suite, tkinter,
  tcl, idlelib, pip/setuptools, *.pdb symbols) to a 12 MB zip so it fit through
  the device file bridge, then unzipped on the PC to `pyportable\`. It bundles
  its own `vcruntime140*.dll`, so no VC++ redistributable is required.
- python.org downloads are blocked from the Claude cloud side (403); GitHub is
  reachable — that is why the standalone build was used rather than the official
  embeddable zip.

---

## 10. Guardrails honored

Plain-language, one-step-at-a-time delivery; `token.txt` never read or printed;
`SEND_TO_CLINIC.bat` and `D:\MARGERP` never modified; nothing live rebuilt; the
manual export + send workflow remains as the fallback; patient numbers are masked
to last-4 by `marg_report.py` on the way through.

---

*S195_Medical_PC_Macro_Guard_Runbook — written S195, 21-Aug-2026. Fold into
CANONICAL_MANIFEST.md at close-out (EOS). Companion to the pre-work brief
`S195_Medical_PC_Continuation_AHK.md` and the kit sources in
`claude/S195_medical_kit/`.*
