# S195 — Medical PC Marg watcher: LIVE and how it's wired (23-Aug, final)

**Status: WORKING, confirmed by capture test.** A watcher runs resident on the medical
PC, captures every Marg export the instant it is written (before Marg overwrites the slot),
and survives restarts. This doc is the single reference — if any of it breaks, start here.

## The whole pipeline, medical → manojz

```
MEDICAL PC (no user login-independent; watcher runs at logon)
  marg_watch.py  (resident, event-driven ReadDirectoryChangesW + 5s safety poll)
    watches:  D:\MARGERP\users        (Marg's own output slots, overwritten each report)
              D:\MARG REPORTS         (where Dr Manoj saves reports by hand)
    on a NEW .xls/.xlsx it copies to:  D:\SendToClinic\_captured   (renamed, dedup by md5)
        │
        │  (Tailscale, manojz reads medical — READ ONLY; manojz CANNOT write to medical)
        ▼
MANOJZ  "Marg pull from medical" scheduled task, every 10 min (PULL_FROM_MEDICAL.bat AUTO)
    - sweeps D:\SendToClinic\_captured  -> marg_router classifies/verifies/archives
    - raw-mirrors  D:\MARG REPORTS  ->  D:\Downloads\margsync\marg_reports_mirror
    - mirrors medical SendToClinic (logs)  ->  margsync\medical_SendToClinic
    - offsite:  MargArchive  ->  H:\My Drive\Clinic Data Archive\MargArchive (Google Drive)
```

## Medical-side install (what actually made it work)

**The hidden villain:** the medical PC has **no system Python** — `python.exe` on PATH is
the Microsoft Store *stub* that prints "Python was not found" and exits. Every launch that
used bare `python`/`pythonw` died instantly and silently. The real interpreter is the
bundled portable one:

- **Python:** `D:\SendToClinic\pyportable\python.exe` (Python 3.11.9). ALWAYS call it by
  full path. Never `python` / `pythonw` (Store stub).
- **Watcher script:** `D:\SendToClinic\marg_watch.py` (stdlib only; needs no marg_router
  in watch mode). `--selftest` passes.
- **Autostart:** `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\MargWatcher.cmd`
  contains:
  ```
  @echo off
  start "" /min "D:\SendToClinic\pyportable\python.exe" "D:\SendToClinic\marg_watch.py" --watch "D:\MARGERP\users" "D:\MARG REPORTS" --spool "D:\SendToClinic\_captured"
  ```
  → runs at every logon; no admin, no Task Scheduler (the earlier `Register-ScheduledTask`
  approach failed — task "Marg export watcher" never registered; abandoned).

### To (re)start the watcher NOW without a logon (PowerShell on medical):
```powershell
$py = "D:\SendToClinic\pyportable\python.exe"
$al = @('"D:\SendToClinic\marg_watch.py"','--watch','"D:\MARGERP\users"','"D:\MARG REPORTS"','--spool','"D:\SendToClinic\_captured"')
Stop-Process -Name python,pythonw -ErrorAction SilentlyContinue
Start-Process $py -ArgumentList $al -WindowStyle Hidden
Start-Sleep 2; Get-Process python | Select ProcessName,Id
```
Note: `$args` is reserved in PowerShell — use `$al`. Pass args as an ARRAY, not one
string (single-string quoting mangles and the process dies).

### Confirm it works
- Process: `Get-Process python` shows a running python.
- Capture: drop any **.xls/.xlsx** into `D:\MARG REPORTS` → within ~10s a file appears in
  `D:\SendToClinic\_captured` named `<stamp>__<slot>__<md5>.xlsx`. **(.txt is ignored —
  the watcher only takes Marg's .xls/.xlsx; testing with a .txt proves nothing.)**
- The medical PC's `D:\SendToClinic\_captured` is the INSTANT truth; the manojz mirror of
  it lags up to 10 min.

## Router — five report types self-classify (`margpull/signatures.json`)

`SALE_BILLWISE` · `STOCK_CLOSING` · `STOCK_EXPIRY` · `PURCHASE_SUPPLIERWISE` ·
`PURCHASE_BILLWISE`. Adding a type = run `marg_router.py --learn <file>` on a sample,
paste the block into `signatures.json`, done (data edit, no code). `dating: file_mtime` is
a signature field for reports whose only dates are future (expiry). Repo mirror:
`margpull/` (router + signatures + marg_watch + medical_watcher kit). **Publish with
PUBLISH_ALL** — these lived only on manojz until S195.

## Standing standard (Task #10)

**All clinic PCs use bundled `pyportable\python.exe`, called by full path — never a system
install.** Every tonight's failure came from system-Python/Store-stub/PATH. Portable =
version-pinned, zero-install, no admin, copy-the-folder to a new PC. Ship pyportable with
every medical/lab/reception kit.

## Two known-broken things (backlog, not blocking)

1. **manojz cannot push to medical** — the medical share is read-only. The ToMedical
   Drive→medical delivery leg was removed (it error-spammed). Delivery TO medical must be a
   medical-side PULL (browser/Drive, as used to place marg_watch.py). Needed for Amir's
   statements + correction workbook. See `S195_ToMedical_Pipe_Broken.md`.
2. **RDP copy-paste** now works (owner enabled clipboard+drive redirection) — Task #9. Keep
   the `.rdp` saved so it persists.
