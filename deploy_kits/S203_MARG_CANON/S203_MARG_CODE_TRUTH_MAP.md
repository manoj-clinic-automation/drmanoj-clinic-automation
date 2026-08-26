> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — MARG PIPELINE: WHAT THE CODE ACTUALLY DOES

**Read-only code audit, 26-Aug-2026. Nothing was modified, run, installed or committed.**
Source of every claim: the live files on **manojz** under `D:\Downloads\margsync\` (read through
the mounted device share) and the **mirror** of the medical PC's `D:\SendToClinic` at
`D:\Downloads\margsync\medical_SendToClinic\`. Line numbers are of the files as they stood today.

> **Method note / limit.** The medical PC's files are read through the *mirror*, which
> `PULL_FROM_MEDICAL.bat` refreshes with `robocopy /E` and **no `/PURGE`** (line 103). The mirror is
> therefore an accurate copy of what exists there, but a file deleted on the medical PC **stays in
> the mirror for ever**. Where that matters it is flagged. Windows Task Scheduler and the registry
> could not be queried (the shell that reaches these folders is not a Windows shell), so **what
> starts each component is taken from the installer code and from the artefacts those installers
> leave behind**, never assumed.

---

## 1 · COMPONENT TABLE

| file | machine | what starts it | reads | writes | how I know |
|---|---|---|---|---|---|
| `PULL_FROM_MEDICAL.bat` | manojz | Task Scheduler task **"Marg pull from medical"**, now repointed at `PULL_HIDDEN.vbs` | `\\100.119.151.40\DDrive\MARGERP\users`, `...\SendToClinic\Sent`, `...\SendToClinic\NEEDS_UPLOAD`, `...\SendToClinic\_captured`, `\\...\MARG REPORTS` | `MargPull\_last_pull.txt`, `MargPull\_task_repoint_tried.txt`, `MargArchive\*`, `medical_SendToClinic\*` (mirror), `marg_reports_mirror\*`, `H:\My Drive\Clinic Data Archive\MargArchive` | task name: `FIX_POPUP.bat:14` `set "TASK=Marg pull from medical"`; repoint proven by `MargPull\_task_repoint_tried.txt:3` `SUCCESS: The parameters of scheduled task "Marg pull from medical" have been changed.`; paths `PULL_FROM_MEDICAL.bat:55-59`, `:89-91`, `:103-105`, `:114`, `:127` |
| `PULL_HIDDEN.vbs` | manojz | the scheduled task (after the repoint); also self-launched by the batch | — | — | `PULL_HIDDEN.vbs:17` `sh.Run "cmd /c """ & here & "PULL_FROM_MEDICAL.bat"" AUTO HIDDEN", 0, False` |
| `marg_watch.py` (sweep mode) | manojz | invoked by the pull | the four medical folders above | `MargArchive\_spool\<stamp>__<slot>__<md5[:8]>.<ext>` | `PULL_FROM_MEDICAL.bat:89-91`; dest name `marg_watch.py:104-105` |
| `marg_router.py` | manojz | **in-process**, from `marg_watch.route()` — *not* a separate command | `MargArchive\_spool\*`, `MargPull\signatures.json`, `MargArchive\index.csv` | `MargArchive\<TYPE>\<YYYY-MM>\*`, `_UNKNOWN\`, `_REFUSED\`, `_outbox\`, `index.csv` | `marg_watch.py:272` `marg_router.main(["--scan", spool] + (extra or []))`; folders `marg_router.py:390-397`, outbox copy `:413-417`, index `:418` |
| `marg_rescan.py` | manojz | pull, guarded by `--if-signatures-changed`; and `RESCAN.bat` by hand | `index.csv`, `_UNKNOWN\`, `_REFUSED\`, `signatures.json`, `_signatures_seen.md5` | `index.csv` (rewritten), `index.csv.before_rescan_<stamp>`, `_rescued\`, `_signatures_seen.md5` | `PULL_FROM_MEDICAL.bat:140`; marker `marg_rescan.py:58,84,87-93`; backup `:122-124` |
| `marg_gate.py send` | manojz | pull; and `SEND_OUTBOX.bat` by hand | `MargArchive\_outbox\*`, `index.csv`, `_outbox_state.json`, `medical_SendToClinic\send_log.txt`, token from `\\100.119.151.40\DDrive\SendToClinic\token.txt` else `D:\Downloads\margsync\SendToClinic\token.txt` | `_outbox_state.json`, `_outbox_send_log.txt`, `_NEEDS_ATTENTION.txt`, token cache | `PULL_FROM_MEDICAL.bat:151`; paths `marg_gate.py:50,56-60`; state write `:164-172`; attention `:636-651` |
| `marg_gate.py status` | manojz | pull (output suppressed); `MARG_STATUS.bat` by hand | `index.csv`, `_outbox_state.json`, `_coverage_from.txt`, medical `send_log.txt` | `D:\Downloads\margsync\MARG_PICTURE.txt`, `D:\Downloads\margsync\_UPLOAD_NOW\*` | `PULL_FROM_MEDICAL.bat:164`; picture path `marg_gate.py:907` `out = os.path.join(os.path.dirname(args.archive.rstrip("\\/")), PICTURE_NAME)`; upload folder `:659-699` |
| `pipeline_status.py` | manojz | `call :report` from the pull, two call sites | `_outbox\`, `_outbox_state.json`, `_last_pull.txt`, newest of three `heartbeat.txt` paths, `H:\...\MargArchive` | **nothing on disk** — it POSTs to `https://followup.dr-manoj.in/finance/api/pipeline-status` | `PULL_FROM_MEDICAL.bat:84,188,197-199`; paths `pipeline_status.py:42-58`; post `:211-218` |
| `marg_report.py` | both | imported by `marg_router.verify()` and by `guard_and_send.py` | the .xls under test | nothing | `marg_router.py:221-228` `if sig and sig.get("deep_verify") == "marg_report": import marg_report` |
| `medical_agent.py` | **medical** | `Startup\MargAgent.cmd`, **at logon** | `D:\MARGERP\users`, `D:\MARG REPORTS`, `C:\Users\Public\MARG`, `D:\SendToClinic\_captured`, `<Drive>\Clinic Data Archive\ToMedical\_kit` | `D:\SendToClinic\heartbeat.txt`, `agent.log`, `_watcher.pid`, `agent_crash.txt`, kit destinations, `<Drive>\...\FromMedical\heartbeat.{txt,json}` | autostart written by `INSTALL_AGENT.bat:95-96` `> "%STARTUP%\MargAgent.cmd" echo @echo off` / `start "" /min "%RUN%" "D:\SendToClinic\medical_agent.py"`; and confirmed present in `BACKUP.txt` §5 startup listing (`MargAgent.cmd`); paths `medical_agent.py:39-58` |
| `marg_watch.py` (resident) | **medical** | **child of `medical_agent.py`**, never a task | the three WATCH_DIRS | `D:\SendToClinic\_captured\*` | `medical_agent.py:404-406` `cmd = [PY, WATCHER, "--watch"] + WATCH_DIRS + ["--spool", SPOOL]`; `:441-442` `subprocess.Popen(..., stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)` |
| `medical_census.py` | **medical** | **nothing automatic** — human double-click of `ToMedical\MEDICAL_CENSUS.bat` | both drives, Drive `MargArchive\index.csv` | `<Drive>\...\FromMedical\CENSUS.txt` + `BACKUP.txt`, `D:\SendToClinic\CENSUS.txt` + `BACKUP.txt` | `MEDICAL_CENSUS.bat:21` `"%PY%" "D:\SendToClinic\medical_census.py"`; outputs `medical_census.py:714-727`; **no invocation anywhere else** — a full-tree grep for `medical_census` finds only the kit entry `medical_agent.py:131` and the heartbeat line |
| `guard_and_send.py` / `GUARD_AND_SEND.bat` / `SEND_TO_CLINIC.bat` | **medical** | human double-click only (`pause` at `SEND_TO_CLINIC.bat:85`, `GUARD_AND_SEND.bat:144`) | `D:\MARGERP\users\*\report\REPORT_1.XLS`, `token.txt` | `Sent\REPORT_<stamp>.XLS`, `send_log.txt`, `sent_hashes.txt`, `last_response.txt`, `last_http.txt`, `NEEDS_UPLOAD\` | `SEND_TO_CLINIC.bat:28-33,99-100,133-136`; `GUARD_AND_SEND.bat:127-132` |
| `medical_inventory.py`, `MEDICAL_INVENTORY.bat`, `MEDICAL_RECENT.bat`, `CLEANUP_DRIVE.bat`, `FIX_POPUP.bat` | manojz | human double-click (all end in `pause`) | — | `MEDICAL_INVENTORY.txt`, `MEDICAL_RECENT.txt`, Drive tidy | e.g. `CLEANUP_DRIVE.bat:39` `pause` |

**Two things the table above kills:**

1. **`marg_router.py` is not a step in the pull.** The reference doc draws it as one. It is called
   in-process by `marg_watch.route()` (`marg_watch.py:265-272`). If it raises, it takes the watcher
   process down with it, and the batch does not notice (see §3).
2. **The medical watcher is started WITHOUT `--route`** (`medical_agent.py:405`). It captures only.
   All classification happens on manojz. That is why the medical PC's older `marg_watch.py`
   (md5 `aa55cdb5`, missing the S201 `spool_has_files` fix — diffed against manojz's `2076fe1d`)
   does not matter: the code path it lacks is never taken there.

---

## 2 · THE SCHEDULES, MEASURED FROM THE CODE

| interval | value | quote |
|---|---|---|
| the pull | **10 minutes — asserted by comment only** | `PULL_FROM_MEDICAL.bat:22` `REM  Task Scheduler: run every 10 minutes.` and `README_PULL.md:27` `Task Scheduler → new task, every **10 minutes**`. **The trigger itself is not determinable from the code** — it lives in the task definition, and `_last_pull.txt` retains only the most recent run (see §4). |
| medical heartbeat | **300 s** | `medical_agent.py:57` `BEAT_EVERY = 300          # seconds between heartbeats` |
| watcher liveness check | **30 s** | `medical_agent.py:58` `CHECK_EVERY = 30          # seconds between watcher liveness checks` — and it is also the loop period (`:727` `time.sleep(CHECK_EVERY)`), so kit installs and death-detection are both on a 30 s cadence |
| resident watcher safety poll | **5.0 s** | `marg_watch.py:43` `SAFETY_POLL_S = 5.0            # net under the event stream` |
| watcher event loop tick | **0.25 s** | `marg_watch.py:245` `path = evq.get(timeout=0.25)` |
| "file finished being written" settle | **60 ms** | `marg_watch.py:44` `SETTLE_MS = 60` and `:84` `time.sleep(SETTLE_MS / 1000.0)` |
| upload POST timeout | **90 s per report, no in-run retry** | `marg_gate.py:496` `def post_one(url, token, path, timeout=90)` and `:934` `ap.add_argument("--timeout", type=int, default=90)` |
| status POST timeout | **30 s** | `pipeline_status.py:211` `def post(payload, url, token, timeout=30)` |
| robocopy retries | **1 retry, 2 s wait** | `PULL_FROM_MEDICAL.bat:103,114,127` all carry `/R:1 /W:2` |
| medical PC ping in the diagnostic | **1 packet, 1500 ms** | `PULL_FROM_MEDICAL.bat:210` `ping -n 1 -w 1500 100.119.151.40 >nul 2>&1` |
| kit install give-up | **3 tries, then frozen until the source bytes change** | `medical_agent.py:137` `MAX_KIT_TRIES = 3`; enforced `:290-291` |
| kit backups kept | **3** | `medical_agent.py:351` `def prune_kit_backups(keep=3)` |
| manual sender busy-retry | **once, after 5 s** | `SEND_TO_CLINIC.bat:102-104` `timeout /t 5 /nobreak >nul` then one more `copy /y` |
| manual sender curl timeout | **90 s** | `SEND_TO_CLINIC.bat:134` `curl -s -m 90 ...` |
| coverage window for "is a day missing" | **45 days**, floored by a declared start date | `marg_gate.py:67` `COVERAGE_WINDOW_DAYS = 45`; `MargArchive\_coverage_from.txt` currently declares `2026-08-17` |

**There is no retry anywhere in the send.** A refused report is simply left in `_outbox` and picked
up by the next pull (`marg_gate.py:643` `"These will be retried automatically on the next run."`).
With 12 files in `_outbox` today, a total outage would cost at most one 90 s timeout per *undelivered*
report — but nothing bounds that if the queue grows, and the pull has no overall timeout.

---

## 3 · FAILURE BEHAVIOUR, STAGE BY STAGE — AND EVERY PLACE A FAILURE IS SWALLOWED

### 3.1 The biggest one: since S201 the pull produces no log at all

The task now runs `wscript.exe PULL_HIDDEN.vbs` (`_task_repoint_tried.txt:3`), and the VBS runs the
batch **hidden**:

```
PULL_HIDDEN.vbs:17   sh.Run "cmd /c """ & here & "PULL_FROM_MEDICAL.bat"" AUTO HIDDEN", 0, False
```

`0` is `vbHide`. Nothing in `PULL_FROM_MEDICAL.bat` redirects stdout to a file. So **every line
printed by `marg_watch.py`, `marg_router.py`, `marg_rescan.py`, `marg_gate.py send` and
`pipeline_status.py` is written to a console nobody can see and is then destroyed.** The only
durable evidence a pull leaves behind on manojz is two lines in `_last_pull.txt`.

That means these messages, all of which the code was carefully written to emit, are unobservable in
the automatic run:

- `marg_watch.py:108` `out("  ! copy failed (busy?), will retry: %s" % ex)` — the capture of a Marg
  slot failing because Marg had it open.
- `marg_router.py:400-404` the per-file verdict and reason lines, including every `REFUSED`.
- `marg_gate.py:560` `print("  skipping %s -- not a verified sale report in index.csv" % name)`.
- `marg_gate.py:631-632` `REFUSED (HTTP %s)` and `server said: %s`.
- `pipeline_status.py:309` `print("pipeline_status: post failed (%s) — the pull is unaffected" % ex)`
  — **the monitor's own failure to report is itself unreported.**

`_NEEDS_ATTENTION.txt` (`marg_gate.py:636-646`) is the one exception: a send failure does land on
disk. A capture failure, a routing failure and a status-post failure do not.

### 3.2 Named swallow sites

| site | quote | effect |
|---|---|---|
| pull: watcher/router | `PULL_FROM_MEDICAL.bat:89` `"%PY%" "%HERE%marg_watch.py" --once --route ^` | **no `errorlevel` check.** If capture or routing dies, the batch walks straight on to the mirrors, the send and `echo END ... -- ok`. |
| pull: rescan | `:140` `"%PY%" "%HERE%marg_rescan.py" --if-signatures-changed --apply` | no `errorlevel` check |
| pull: the picture | `:164` `"%PY%" "%HERE%marg_gate.py" status >nul 2>&1` | **stdout *and* stderr discarded.** `marg_gate.py:913` `print("\n(could not write the picture file: %s)" % e)` and `:921` `print("(could not refresh the upload folder: %s)" % e)` can therefore never be seen. A stale `MARG_PICTURE.txt` and a stale `_UPLOAD_NOW` look exactly like a fresh one. |
| pull: robocopy verdicts | `:106` `if errorlevel 8 (echo    mirror had a problem ^(code %errorlevel%^)) else (...)`; same shape at `:115` and `:128` | robocopy exit codes **1–7 are treated as success** (correct), but code ≥8 only *prints* — into the hidden console. The offsite copy can fail every ten minutes for ever and nothing on disk records it. |
| pull: the `AUTO` hand-off | `:40-47`, ending `exit /b 0` | the scheduled task's own process **always exits 0**, before any work happens. Task Scheduler's "Last Run Result" is therefore meaningless as a health signal. |
| pull: schtasks repoint | `:43` `schtasks /Change ... < nul >> "%HERE%_task_repoint_tried.txt" 2>&1` | correctly captured to a file — the one place output *is* kept. Ran once, succeeded. |
| pull: python probe | `:63-64` `py -c "import sys" >nul 2>&1 && set "PY=py"` | benign |
| pull: no-python exit | `:65-72` | writes `END ... FAILED: no python` to `_last_pull.txt` but **does not `call :report`** — the two failure paths are not symmetric. The server sees a gap rather than a reason. |
| pull: diagnose | `:210` `ping -n 1 -w 1500 100.119.151.40 >nul 2>&1` | intentional; the verdict is echoed (into the hidden console) |
| router: unreadable spreadsheet | `marg_router.py:349-354` `except Exception as ex: res.update(... verdict="REFUSED", reason="not a readable .xls (%s)" % ex, rows=0)` then `return res` | **This returns before line 406.** The file is never copied to `_REFUSED\`, never gets a `.txt` sidecar, and **is never appended to `index.csv`**. Only the in-memory `seen` dict is updated (`:543`), so next cycle it is found again, fails again, and is refused again — for ever, invisibly, with no row anywhere saying so. This is the most serious single defect I found in the Python. |
| router: no per-file guard | `:539-543` `for f in files: r = process(f, sigs, cfg, seen, out)` | there is **no `try/except` around the loop**. An exception inside `process()` — a failed `shutil.copy2`, a failed `append_index` — aborts the whole routing run and every remaining spool file goes unprocessed this cycle. (S201 partially mitigated this by re-routing the spool whenever it is non-empty, `marg_watch.py:237`.) |
| router: exit code | `:546` `return 0` | `main()` returns 0 **whatever the verdict counts are**. A run in which every file was REFUSED exits 0. |
| router: xlsx fallback | `:101-106` `except Exception as first: try: import xlrd ... except Exception: raise first` | deliberate and correct |
| watcher: capture failure | `marg_watch.py:107-109` `except OSError as ex: out(...); return False` | printed only — see §3.1. A file that is permanently busy is retried silently every cycle for ever. |
| watcher: incomplete file | `:73-87` `looks_complete()` returns False on bad magic, zero size, changing size, or `OSError` | silent by design; a file Marg is mid-write is skipped with no line at all |
| watcher: event thread | `:177-183` `except Exception: pass` / `finally: try: k32.CloseHandle(h) except Exception: pass` | documented: the thread dies quietly and the 5 s poll carries the load. But **nothing reports that the event path is gone** — the difference between "instant capture" and "up to 5 s of exposure to slot reuse" is invisible. |
| watcher: router missing | `:266-270` `except ImportError: out("  ! marg_router.py not beside this script — spool kept, not routed.")` | printed only |
| gate: corrupt state file | `marg_gate.py:158-161` `except Exception: return {"sent": {}}` | documented and correct — worst case a re-send |
| gate: unreadable coverage file | `:329-330` `except Exception: declared = None` | silently falls back to the 45-day horizon. If `_coverage_from.txt` is ever lost, the picture quietly widens its window and can start reporting July as missing again — the exact S202 false alarm, re-armed. |
| gate: token read | `:191-192` `except Exception: return None`; `:214-215` cache-refresh failure returns `"cache refresh failed, not fatal"` | reported in the (hidden) output only |
| gate: network | `:520-524` `except Exception as e: return 0, "LOCAL-ERROR: %s" % e.__class__.__name__` | **this is the AF-1 fix and it is correct** — the reply is held in memory, never in a file, and http 0 classifies as `refused` (`:486` `if http != 200: return "refused"`) |
| gate: picture/upload writes | `:912-913`, `:920-921` `except Exception as e: print(...)` | printed, then discarded by the `>nul 2>&1` at `PULL_FROM_MEDICAL.bat:164` |
| pipeline_status: everything | `:88-89`, `:95-96`, `:103-104`, `:118-119`, `:134-135`, `:165-166`, `:175-176`, `:189-190`, `:289-291`, `:299-301`, `:308-310` | **eleven guarded blocks, and `main()` returns 0 on every one of them.** This is deliberate (`:22-24` `it NEVER fails the pull`), and it is the right call — but combined with §3.1 it means the reporter can fail totally, every cycle, and produce no evidence anywhere. |
| agent: log write | `medical_agent.py:89-90` `except OSError: pass` | if `agent.log` cannot be written the agent goes completely silent |
| agent: watcher output | `:441-442` `stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL` | **the resident watcher's entire output — every capture line, every busy-file warning, every traceback — is discarded.** If the watcher crashes, `agent.log` records only `WATCHER DIED (exit %s)` (`:716`), never why. |
| agent: pid file write | `:446-447` `except OSError: pass` | a `_watcher.pid` that cannot be written means the *next* agent start cannot kill the stale watcher, and two watchers then share one spool |
| agent: kill | `:409-414` `except Exception: pass` | silent |
| agent: crash handler | `:747-766` writes `agent_crash.txt` locally and to Drive, then `raise` | correct and complete — the one genuinely well-instrumented failure path in the estate |
| medical sender | `SEND_TO_CLINIC.bat:100` `copy /y "%SRC%" "%WORK%" >nul 2>&1`; `:113` `certutil ... 2^>nul`; `:123` `findstr ... >nul 2>&1`; `:135` `... > "%HERE%last_http.txt" 2>nul` | all suppressed; the batch **always `exit /b 0`** (`:86`), which `GUARD_AND_SEND.bat:113` acknowledges in a comment |
| **`GUARD_AND_SEND.bat` — AF-1, still live** | `:119-123` `if exist "%HERE%last_response.txt" ( findstr /c:"ACCEPTED-FOR-REVIEW" "%HERE%last_response.txt" >nul 2>&1 && set "OK=1" ... ) / if defined OK exit /b 0` | `curl -o` does **not** overwrite `last_response.txt` when the connection never completes. A network drop therefore leaves yesterday's `ACCEPTED-FOR-REVIEW` body in place, this check sets `OK=1`, and the batch exits 0 declaring success for a report that never left the building. Manual path only, but it is still on the machine and still reachable by double-click. |
| `INSTALL_AGENT.bat` | `:56-57` `taskkill /f /im python.exe >nul 2>&1` / `taskkill /f /im pythonw.exe >nul 2>&1` | kills **every** Python on the medical PC, not only the pipeline's |

### 3.3 The consequence, stated plainly

`_last_pull.txt` gains `END ... -- ok` at `PULL_FROM_MEDICAL.bat:184` on a path that requires only
two things to be true: a Python exists (`:61-72`) and `\\100.119.151.40\DDrive\MARGERP\users` is
reachable (`:74`). **Capture, routing, rescue, send and the picture can all have failed and the
stamp still reads `ok`.** `pipeline_status.last_pull_state()` then reports that stamp verbatim
(`pipeline_status.py:122` `"ended_ok": any(l.startswith("END") and l.endswith("ok") for l in tail)`),
so the server is told the pull ended ok too.

This is the same shape as the S202 finding, one layer up: the *reporter* was fixed so it fires on
the unreachable-share path (`:81-84`), but the thing it reports on — the word `ok` — is still
produced by a check that does not cover the work.

---

## 4 · STATE FILES

| file | written by | read by | if missing | if stale |
|---|---|---|---|---|
| `MargPull\_last_pull.txt` | the pull, **truncated at every start**: `:54` `>"%HB%" echo START %DATE% %TIME%`, then appended at `:67`, `:79` or `:184` | `pipeline_status.last_pull_state()` `:114-123`; the runbook; a human | `last_pull_state` returns `{}` (`:118-119`) and the payload simply omits it — **a missing pull stamp is not an alarm** | holds **only the current/most recent run**. There is no history, so "the task fired 6 times in the last hour" is unanswerable from this file. A run that dies between `START` and `END` leaves a lone `START` line — the only detectable mid-run crash signature. |
| `MargArchive\index.csv` | `marg_router.append_index()` `:248-255` (append-only); rewritten wholesale by `marg_rescan.write_index()` `:119-131` | `marg_gate.read_index()` `:95-112`, `verified_sales()` `:115-125`; `marg_rescan.read_index()` | `read_index` returns `[]` → `build_picture` prints *"No verified sale reports in the archive at all."* (`marg_gate.py:295`) and `do_send` finds no verified sales, so **the entire outbox becomes unsendable and the picture goes green-ish-empty rather than red** | it is the **only** record linking a content hash to a business date. A half-written final line is tolerated (`:109-110` `if len(r) < len(hdr): continue`). Rescan keeps a dated `.before_rescan_<stamp>` copy each time it rewrites (`:122-124`) — one exists today. |
| `MargArchive\_outbox_state.json` | `marg_gate.save_state()` `:164-172`, atomically via `os.replace` | `marg_gate.load_state()`; `pipeline_status.outbox_state()` `:92-94` | `load_state` returns `{"sent": {}}` (`:151-152`) → **everything in `_outbox` is sent again**. The server does not dedupe (see §6), so that stages every report a second time. `pipeline_status` would report all 12 files pending. | this is the authority on "delivered". `build_picture` counts only `result in ("accepted","duplicate")` as on-server (`:278-279`) |
| `MargArchive\_coverage_from.txt` | **by hand** (its own header says so) | `marg_gate.build_picture()` `:321-333` | falls back to `max(first_seen, yesterday-45d)` silently (`:329-330`) — re-arming the S202 "56 missing days" false alarm | currently `2026-08-17` |
| `MargArchive\_signatures_seen.md5` | `marg_rescan.remember_signatures()` `:87-93` | `signatures_changed()` `:61-84` | `seen = None` → `cur != seen` is true → the rescan runs once, then re-stamps. Self-healing. | 33 bytes today |
| `MargArchive\_spool\` (43 files) | `marg_watch.capture()` `:100-106` | `prime_captured()` `:125-135` — **the spool IS the watcher's dedupe memory**; and re-routed every cycle it is non-empty (`:237`) | emptying it re-captures and re-routes everything (the router's `index.csv` blacklist then skips it, `marg_router.py:345-346`) | never pruned. Every cycle MD5s all 43 files. |
| `MargArchive\_NEEDS_ATTENTION.txt` | `marg_gate.py:638-645`; **deleted on a clean run** `:650-651` `if os.path.exists(att): os.remove(att)` | a human; `SEND_OUTBOX.bat:47` points at it | absence means "nothing failed last run" — which is correct, and is the one self-clearing alarm in the estate | — |
| `MargArchive\_outbox_send_log.txt` | `marg_gate.log_line()` `:175-177`, append-only | a human | — | 6 lines today; carries the 25-Aug `HTTP 401 {"error":"not_signed_in"...}` then the recovery |
| `D:\Downloads\margsync\MARG_PICTURE.txt` | `marg_gate.do_status()` `:907-910` | the runbook; a human | the pull's status call is `>nul 2>&1`, so a write failure is undetectable | **there is a second, contradictory file**: `MargPull\MARG_PICTURE.txt` (48 bytes, 25-Aug 05:21) reads `No verified sale reports in the archive at all.` while `margsync\MARG_PICTURE.txt` (26-Aug 11:50) reads `Every trading day up to yesterday has a report and the server has it.` The live code can only ever write the second (`:907` takes the *parent* of the archive path). The first is an orphan from an older build and is a trap for anyone opening the wrong one. |
| `_UPLOAD_NOW\` | `marg_gate.refresh_upload_folder()` `:659-699` — **wipes every file first** (`:667-670`) then re-populates | a human | empty + `READ_ME.txt` is the "all clear" signal (`:694-698`). Currently empty. | if `do_status` ever stops running, the folder freezes in whatever state it was last left — and because the call is `>nul 2>&1` nothing says so |
| `D:\SendToClinic\heartbeat.txt` (+ `.json`, + the Drive copies) | `medical_agent.write_beat()` `:651-673` | `pipeline_status.heartbeat_state()` `:126-153` via `pick_heartbeat()` `:179-193` | `heartbeat_state` returns `({}, {}, None)` → the payload's `watcher` block is `{}`. `pick_heartbeat` deliberately picks the **newest of three paths** so a moved drive letter degrades to "could not read", not to a silent green (`:180-181`) | age is carried explicitly as `heartbeat.age_hours` (`:133`). Live copy at `H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt` is current (11:53 today). |
| `D:\SendToClinic\_watcher.pid` | `medical_agent.start_watcher()` `:444-447` | `kill_stale_watcher()` `:417-433` | a stale watcher from a previous agent run **cannot be killed** and two watchers then write the same spool (harmless for dedup, wasteful for I/O) | contains `13728` today, matching the heartbeat's live pid |
| `D:\SendToClinic\agent.log` | `medical_agent.log()` `:70-96`, self-truncating at 512 KB to the last 2000 lines (`:82-86`) | a human | the agent goes silent | this is the **only** durable record of watcher deaths and kit installs |
| medical `send_log.txt`, `sent_hashes.txt` | `SEND_TO_CLINIC.bat:127,141-142,149-150,157` | `marg_gate.accepted_from_medical_log()` `:128-146` — explicitly **a hint, never proof** (`:131-134`) | empty set; nothing breaks | `sent_hashes.txt` is the permanent client-side blacklist that AF-1 could poison; `marg_gate` correctly refuses to trust it |
| medical `last_response.txt` / `last_http.txt` | `SEND_TO_CLINIC.bat:133-136` | `SEND_TO_CLINIC.bat:138,146`; `GUARD_AND_SEND.bat:119-126` | `OK` unset → the report is parked in `NEEDS_UPLOAD` (correct) | **stale content is read as success** — AF-1, quoted in §3.2 |
| `MargPull\_task_repoint_tried.txt` | `PULL_FROM_MEDICAL.bat:42-43` | the batch itself, as a one-shot latch (`:41`) | the repoint is attempted again | present, and records `SUCCESS` |

---

## 5 · WHERE A BACKUP JOB COULD HOOK IN

The owner's constraint: *"marg is very poor in all this, and mostly the pc is pwr off after 9 pm"* —
so a midnight schedule is useless and Marg's own machinery cannot be relied on.

### 5.1 What the code and the surveys establish first

- **Nothing on the medical PC is scheduled.** `BACKUP.txt` §5: `NONE. Nothing in Task Scheduler
  mentions Marg or backup.` The only autostart entries are `Startup\MargAgent.cmd` and
  `MargWatcher.cmd.replaced_by_agent.bak` — i.e. **the agent is the only thing that runs unattended
  on that machine, and it starts at LOGON, not at boot** (`INSTALL_AGENT.bat:91-96`).
- **Marg's own backup writes to a target that is not attached.** `BACKUP.txt` §2: `E:\auto  EMPTY`,
  `E:\MARGBCKUP  3 file(s)  <-- STALE (321 days)`. §7: *"The backup target is NOT ATTACHED... every
  automatic run has been writing to a drive letter that is not there."* The only recent `.mbk` files
  sit loose in `E:\` (newest `2026-08-22 10:42:14`, 4.0 days old) — i.e. **someone ran it by hand**.
- **What has to be covered.** `BACKUP.txt` §4: `D:\MARGERP\Data  1075 file(s)  0.9 GB  newest
  2026-08-26 10:20:42`; `System  265 file(s)  0.3 GB`; `operator  223 file(s)`; `GSTRETURN  43
  file(s)  0.3 GB`; `serverbackup  65 file(s)  0.1 GB  newest 2026-08-26 00:01:14`. Total realistic
  payload ≈ **1.6 GB**.
- **`D:\MARGERP\Data` is live while Marg runs** — its newest file was 10:20 today, during clinic
  hours. Marg is a Foxpro-family application (`medical_census.py:48` skips `.dbf .cdx .idx .fpt`),
  and those tables are held open for writing by `margwin.exe`. **A plain file copy of `Data\` while
  Marg is open will produce a torn, unrestorable set.** The code does not say this in words, but two
  places show the machine already loses this race on much smaller files: `marg_watch.py:107-108`
  `except OSError as ex: out("  ! copy failed (busy?), will retry: %s" % ex)` and
  `SEND_TO_CLINIC.bat:102-105` `file busy, waiting 5 seconds... / COULD NOT READ the report - Marg
  file busy.` **`D:\MARGERP\serverbackup\` is the exception** — it is Marg's own written-out backup
  (newest `2026-08-26 00:01:14`, i.e. Marg produced it at one minute past midnight), a closed file
  once written, and therefore the only Marg artefact safe to copy byte-for-byte at any time.

### 5.2 The candidate hooks, ranked

**A. `medical_agent.py`'s supervision loop — `main()` lines 696-727. RECOMMENDED.**
Add a time-of-day/interval check inside the existing `while True`, beside the kit and heartbeat
blocks (`:698`, `:714`, `:721-725`).

- *Copies:* `D:\MARGERP\serverbackup\` (safe, closed) and the newest `E:\*.mbk`, into
  `<Drive>\My Drive\Clinic Data Archive\FromMedical\_backup\` — the same channel the heartbeat
  already uses (`find_drive_out()` `:102-117`), which is proven to work in both directions today.
- *Pros:* it is **the only process on that machine that runs unattended**, it is already awake every
  30 s so it can fire the moment it notices the hour has arrived rather than at a fixed minute, it
  already has a crash handler that reports to Drive (`:743-766`), it already has an audited
  install-and-verify-by-hash discipline to copy (`install_kit()` `:296-348`), and **its heartbeat is
  already parsed by `pipeline_status.py`** — so a `BACKUP:` line added to `human()` (`:585-648`)
  becomes visible on the clinic server through machinery that already exists.
- *Cons:* the agent starts at **logon**, so it covers exactly the hours the PC is in use — which is
  the constraint, not a defect, but it must never be described as "nightly". Adding work to the
  supervisor risks the supervisor: any new code must be inside its own `try/except` or a watcher
  death goes unhandled while a copy runs. And it does **not** solve `D:\MARGERP\Data` — see 5.4.
- *Cost:* Drive quota and sync time for ~0.1–0.3 GB per run if `serverbackup` is copied whole;
  it must be incremental (mtime/size), not a re-upload.

**B. A new Windows Scheduled Task on the medical PC.**
- *Pros:* independent of logon if configured "run whether logged on or not"; the natural home for a
  long job.
- *Cons:* **`BACKUP.txt` §5 proves no such task exists today and that the last attempt at unattended
  scheduling on this machine is what left `E:\auto` empty.** A task also needs a stored credential,
  and `medical_census.py` reports the account `MEDICAL\SET`; the reference doc records that
  `MEDICAL\user` has no password and Windows refuses passwordless network logons. It is a second,
  unmonitored scheduling surface on a machine that already has one thing that works. It would also
  have to be installed by hand at the machine — there is no remote-execution channel (see 5.5).

**C. The resident `marg_watch.py`.** *Reject.* Its docstring is explicit — `:22` *"Capture is
deliberately dumb and fast so it can never be the slow step."* A 1.6 GB copy inside the capture
loop would block `ReadDirectoryChangesW` draining and lose exports to slot reuse, which is the exact
failure the watcher exists to prevent. Its output is also `DEVNULL`'d (`medical_agent.py:441-442`),
so a backup running there could not report anything.

**D. `PULL_FROM_MEDICAL.bat` on manojz.** *Partial only.*
- *Pros:* runs every 10 minutes on a machine that is on, needs no change on the medical PC at all,
  and `robocopy` with `/XO` is already the idiom used three times in the file (`:103,114,127`).
- *Cons:* **the share is D: only.** `medical_agent.py:42-48` states it in as many words: *"a drive
  manojz cannot see -- the Tailscale share is DDrive only."* So `C:\` is out of reach, and any
  `E:\` stick is out of reach. Worse, `\\100.119.151.40\DDrive` is **read-only from manojz**
  (`PULL_FROM_MEDICAL.bat:170-173`, the disabled ToMedical leg: *"the medical share is READ-ONLY
  from manojz -- robocopy to FROM_CLINIC returns ERROR 5"*), so it can pull but never trigger.
  And it would inherit the pull's total blindness (§3.1) unless it wrote its own state file.
  It *is* the right hook for **copying `D:\MARGERP\serverbackup\` off the machine** — that folder is
  on D:, so manojz can already reach it today with one added `robocopy` line.

**E. A `.bat` in the medical Startup folder, beside `MargAgent.cmd`.** *Reject.* It duplicates hook
A's trigger (logon) with none of hook A's reporting, and `INSTALL_AGENT.bat:92-93` shows the project
has already moved one autostart entry out of the way precisely to stop having two.

### 5.3 What each would have to copy, and from where

| source | size / freshness (`BACKUP.txt`) | locked while Marg runs? | reachable from manojz? |
|---|---|---|---|
| `D:\MARGERP\Data\` | 1075 files · 0.9 GB · newest **2026-08-26 10:20:42** | **Yes — assume torn.** Foxpro tables held open by `margwin.exe` | yes (D: share, read-only) |
| `D:\MARGERP\System\` | 265 files · 0.3 GB · newest 2026-08-26 10:00:23 | probably | yes |
| `D:\MARGERP\operator\` | 223 files · newest 2026-08-26 10:20:42 | probably | yes |
| `D:\MARGERP\GSTRETURN\` | 43 files · 0.3 GB · newest 2026-07-09 | no (dormant) | yes |
| **`D:\MARGERP\serverbackup\`** | 65 files · 0.1 GB · **newest 2026-08-26 00:01:14** | **no — Marg writes it and closes it** | **yes** |
| `E:\*.mbk` (the stick) | newest `2026-08-22 10:42:14`, 2.3 MB, 4.0 days old · 177 files total | no | **no** — E: is not on the D: share |
| `C:\Users\Public\MARG\` (PDF tree) | present per `medical_agent.py:51-52` | slot `REPORT.PDF` overwritten each export | **no** |

### 5.4 The honest caveat about `Data\`

Nothing in this codebase can produce a *consistent* copy of `D:\MARGERP\Data` while Marg is running.
A correct backup of that folder needs either Marg closed, or a VSS shadow copy. Copying it live and
calling it a backup would be the same class of error as the AF-1 false ACCEPTED: a record that says
"protected" when nothing is. **The only Marg artefact this estate can honestly back up unattended
today is `serverbackup\`, plus whatever `.mbk` a human produces on E:.** Say that out loud rather
than shipping a green tick.

### 5.5 One structural fact that shapes all of this

There is a working **code delivery** channel to the medical PC — Drive `ToMedical\_kit\` →
`medical_agent.pending_kit()`/`install_kit()` (`:275-348`), allowlisted (`:128-132`),
compile-checked (`:230-245`), hash-verified (`:340-347`). There is **no execution channel**:
`medical_census.py` is delivered by that kit and then sits there until a human double-clicks
`MEDICAL_CENSUS.bat` (a whole-tree grep finds no other caller). Hook A is attractive precisely
because it converts the existing delivery channel into a trigger for free — new code arrives by
Drive, and the agent that installs it is also the agent that would run it.

---

## 6 · WHERE THE CODE CONTRADICTS THE DOCUMENTS

**1. Does the server dedupe by content?** The two authorities disagree, and a client was written
against the wrong one.

> `marg_gate.py:31-32` — *"A false 'sent' is the expensive failure. **A repeat send is free -- the
> server dedupes by content.**"*
>
> `MARG_PIPELINE_REFERENCE_v1.md` §3 — *"**The endpoint does NOT dedupe by content.** Sending the
> same bytes twice stages twice. Client-side state is what prevents duplicates."*

If the reference is right, `marg_gate`'s stated safety margin does not exist, and every path that
loses `_outbox_state.json` (§4) stages 12 duplicate reports into the approvals queue. **Resolve this
against the server before anything else in this list.**

**2. The multipart filename.** Reference §3 specifies `filename "REPORT_1.XLS"`. The code changed in
S202: `marg_gate.py:506` `body, ctype = build_multipart(data, filename=os.path.basename(path))`,
with a selftest asserting the opposite of the doc (`:741-742` *"it is NOT the Marg slot name every
report used to arrive under"*). The doc's contract section is stale. Note the same file still
carries `:760` `ck("multipart names the file REPORT_1.XLS", b"REPORT_1.XLS" in body)` — true only
because `build_multipart`'s *default* argument is unchanged (`:397`).

**3. How many folders the resident watcher watches.** Reference §1: *"captures .xls/.xlsx/.pdf from
**BOTH** folders"*. Code: `medical_agent.py:51-52` `WATCH_DIRS = [r"D:\MARGERP\users", r"D:\MARG
REPORTS", r"C:\Users\Public\MARG"]` — **three**, confirmed by the live heartbeat line
`watching: D:\MARGERP\users + D:\MARG REPORTS + C:\Users\Public\MARG`.

**4. The pull's step order.** Reference §1 lists send before the mirrors and the offsite. The batch
runs mirrors and the Drive offsite **first** (`:103`, `:114`, `:127`), then rescan (`:140`), then
send (`:151`), then status (`:164`). Consequence: `MARG_PICTURE.txt` is refreshed *after* the
offsite copy, and `_outbox`/`_spool` are excluded from the offsite anyway (`:127` `/XD _spool
_outbox`) — so, as the reference itself says in §6, **the pending-send queue has no offsite copy**.
That part the doc gets right.

**5. `README_PULL.md` is two things out of date.** `:10` *"reads three folders on the medical PC"* —
the batch reads **four** (`:90` adds `...\SendToClinic\_captured`). `:17` *"files it under
`D:\MargArchive\<TYPE>\<YYYY-MM>\`"* and `:23` *"e.g. `D:\MargPull`"* — the live paths are
`D:\Downloads\margsync\MargArchive` and `D:\Downloads\margsync\MargPull` (`:56`, `:26`). A reader
following the README would also inherit `marg_router.py`'s defaults, `:45-46` `DEFAULT_ARCHIVE =
r"D:\MargArchive"` / `DEFAULT_OUTBOX = r"D:\SendToClinic\Outbox"` — **running `marg_router.py` by
hand with no arguments on manojz writes to two folders that are not the live ones.**

**6. `xlsx_stdlib.py` on the medical PC.** Reference §9 *"KNOWN GAPS": "`xlsx_stdlib.py` is **not yet
on the medical PC**"*. It is: `agent.log` `2026-08-25 19:28:17  installed xlsx_stdlib.py from the
kit and verified (bbe11a89)`, and the mirror's copy hashes `bbe11a8953f66c27126c48e773cfbe35`,
identical to manojz's. The doc was written before that install landed.

**7. `marg_report.py` version drift — the doc is still right, and it is still broken.** Reference §2
records PC copy `28b47d44…` vs server `6411a57d…`. Verified today: **both** manojz's and the medical
PC's copies hash `28b47d447cfd966411742055717a5c56`. The two-builds-old parser named in §9 as a
known gap is unchanged, and `marg_router.py:221-224` deep-verifies every sale report with it.

**8. `MEDICAL_BACKUP_SURVEY.bat` disagrees with the folder it sits in.** The file itself
(`ToMedical\MEDICAL_BACKUP_SURVEY.bat:3-8`) says *"SUPERSEDED, S203 -- do not use this file... The
backup survey now lives inside medical_census.py"* — correct, and `medical_census.py` does now write
`BACKUP.txt` (`:714-717`). Worth recording that the S203 supersession is already done in code.

**9. A power-history section exists in the newest `medical_census.py` (`_power_history()`,
`:298-345`, reading Windows events 6005/6006/6008) but does not appear in the `CENSUS.txt` on disk
(written `2026-08-26 10:24:24`).** The kit installed `medical_census.py` md5 `44c84744` at
`11:43:09`; the census has not been re-run since. **The evidence for the owner's "pc is pwr off
after 9 pm" is one double-click away and has not been collected.** That single run would turn the
backup-window question from an assumption into a measurement.

---

## 7 · TWO OPERATIONAL ITEMS FOUND ALONG THE WAY

- **The mirror never purges.** `medical_SendToClinic\` holds **363** files named
  `marg_watch.py.before_20260825-1757xx` through `-1829xx`, one every ~30 s. `agent.log` records
  `2026-08-25 18:46:16  pruned 360 stale kit backup(s)` — i.e. they were **deleted on the medical PC**
  and survive on manojz only because `PULL_FROM_MEDICAL.bat:103` uses `robocopy /E` with no
  `/PURGE`. They are wreckage from the S201.3 retry loop that `medical_agent.py:299-311` documents
  and `MAX_KIT_TRIES` (`:137`) fixed. Harmless, but they make the mirror unreadable and they will
  never go away by themselves.
- **A second copy of the upload token exists in a folder named for deletion.** Two files:
  `D:\Downloads\margsync\SendToClinic\token.txt` (the legitimate cache, `marg_gate.py:57`) and
  `D:\Downloads\margsync\_to_delete\S201_20260825\loose\finance marg token.txt`. **No token value
  was read or printed by this audit.** Rotation is already the project's oldest open item; this is a
  second copy to remember when it happens.

---

*S203 · code audit only · read-only · no patient identifiers reproduced, no token value read or
printed. Where the code could not answer a question — the scheduled task's actual trigger interval,
the true count of files under `\\...\SendToClinic\Sent`, whether `D:\MARGERP\Data` is locked as
opposed to merely written-to — this document says so rather than filling the gap.*
