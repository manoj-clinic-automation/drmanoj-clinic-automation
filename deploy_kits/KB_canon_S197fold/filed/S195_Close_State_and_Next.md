# S195 close — what is LIVE, what is parked, what is next
**22 Aug 2026, ~01:15 IST.** Long session: a live crisis, a money reconciliation, and
the Marg pipeline built and installed.

## LIVE and proven
| Layer | State |
|---|---|
| VPS `finance_app.py` | `f25ed48923a5647ba1f6111bad0737d3` (S195_NCSCAN: no-payment bills + per-bill scan). Smoke 573/573. |
| VPS `finance_ui/finance_daily.html` | `20efc5caa664c9b96be23bb66866d21c` |
| VPS `FINANCE_MARG_TOKEN` | now in the unit file — durable across restarts (was the crisis) |
| Medical `D:\SendToClinic` | S195_SEND installed. `GUARD_AND_SEND.bat` = the one icon. |
| Medical `SEND_TO_CLINIC.bat` | untouched proven v3 `e19a8a777ac22fe75a242f1eb9762185` |
| Medical report discovery | `find_sale_report.ps1` (content-based, own file — batch escaping bug) |
| manojz `D:\Downloads\margsync\MargPull` | installed, **Task Scheduler every 10 min** ("Marg pull from medical") |
| manojz archive | `margsync\MargArchive` — 5 days, named by business date, `index.csv` |
| manojz mirror | `margsync\medical_SendToClinic` — medical's logs/alerts readable from here |
| Offsite | `H:\My Drive\Clinic Data Archive\MargArchive` (drmka.ortho Drive) |
| VPS `finance.db` backups | 01:05 daily, verified nightly, **restore PROVEN** (126 days, 3141 sale items) |

Proven end-to-end twice with real reports: 20-Aug (ALREADY-RECEIVED) and **21-Aug
(ACCEPTED, 37 bills, ₹49,181, 170 item lines)** — the 21st is staged and awaits Apply.

## PARKED (in priority order for next session)
1. **Health tile on the portal** — owner's stated top priority. Live status: last
   accepted push + its date, days filed vs missing, open flags, drawer vs last
   physical count, last verified backup. Turns a silent failure into a visible one;
   tonight's 401 went unnoticed from 20:51 to ~22:00.
2. **AHK macro v3** — syntax now correct on disk, but "nothing happened" on run.
   **Next step: `(Get-Item D:\SendToClinic\AutoHotkey64.exe).VersionInfo.FileVersion`**
   — if 1.x, that is the answer (v2 script under v1). `AutoHotkey_2.0.26.zip` is in
   manojz margsync. Calibration is good (it reached line 111 before erroring).
   `GuardExpect` is currently `"any"` — set back to `"yesterday"` for daily use.
3. **DB off-box pull** (`S195_DBPULL`) — needs an SSH key manojz→VPS. Local-only until
   the copy is encrypted (passphrase decision outstanding).
4. **Router signatures** for Labmate / Docterz / stock / purchase — needs one sample of
   each; a signature is a data edit in `signatures.json`, never code.
5. Retention: monthly-zip tier for closed FYs; confirm 8 years with the CA.

## OWNER ACTIONS OUTSTANDING (money + security)
- **Rotate BOTH tokens** — `FINANCE_CRON_TOKEN` and `FINANCE_MARG_TOKEN` were pasted
  into chat during diagnosis. New Marg token must also go into medical `token.txt`;
  compare md5 hashes, never values.
- **18 Aug**: total 23,879 → **25,176** (UPI stays 6,707; cash becomes 18,469). His
  handwritten copy AND Marg both say 25,176 — the count was right, the entry was not.
- **17 Aug**: record the **₹20,000** August salary advance (left the drawer, recorded
  nowhere). Ceiling policy D331 may refuse it — say so if it does.
- Both at `/finance/entry?legacy=1` (checker can edit an approved day; the earlier
  version is kept as a revision).
- **After both: the drawer should read ₹175,201** = Dr Bhawna 1,56,235 + owner 18,963
  + Darpan's real ₹3.
- **Apply the 21-Aug push** at the Hub.

## Lessons worth keeping
- **A filename proves nothing.** Marg names by slot and mixes report types in one
  folder. Every layer now identifies by content and renames by the date inside.
- **A restart is not a no-op** when a service's environment has drifted from its unit
  file. `systemctl show -p Environment` reads the FILE; `/proc/<pid>/environ` reads
  what is actually running. Disagreement is the warning sign.
- **Diagnosis must not share fate with the thing diagnosed** — hence the mirror on
  manojz and the runbook published off the VPS.
- **Don't embed a PowerShell pipeline inside a batch if-block** — cmd mangles the
  escaped pipes silently. Put it in its own `.ps1`.
- Assistant shipped four Windows syntax/plumbing bugs tonight (batch escaping, AHK v2
  comma-chaining, and two follow-ons) — all from code that could not be executed here.
  Prefer separate, independently runnable files over inline embedding.
