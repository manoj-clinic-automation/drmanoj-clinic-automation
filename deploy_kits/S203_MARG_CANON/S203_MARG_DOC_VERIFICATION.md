> ## WORKING PAPER — S203, not a reference
> Written to work something out on 26-Aug-2026. Its conclusions live in
> `MARG_MEDICAL_CURRENT.md`; its evidence and reasoning live in
> `MARG_MEDICAL_HISTORY.md`, both in `deploy_kits/MARG_MEDICAL/`.
> **Do not cite this as current.** Retained, not deleted (F-23).

# S203 — MARG DOCUMENT VERIFICATION

**Every factual claim in the four current Marg reference documents, tested against the live code on
manojz and against measurements taken from the MEDICAL PC on 26-Aug-2026.**

Read-only session. No file on either PC was modified. No `git` command was run (F-131). No token
value was read or printed. No phone number appears here.

## SCOPE AND METHOD

**Documents tested**

- `claude/MARG_PIPELINE_REFERENCE_v1.md` (S201)
- `claude/MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` (S201)
- `claude/MARG_INGESTION_REFERENCE_v1.md` (S201)
- `claude/S195_Medical_Watcher_LIVE_Reference.md` (S195, nominally superseded)

**Evidence sources**

| tag | what it is |
|---|---|
| **CODE** | the live files under `D:\Downloads\margsync\` on manojz, read this session, cited file+line |
| **MEAS** | the measurements taken from the medical PC on 26-Aug-2026, supplied as established fact |
| **LIVE** | live state files read this session — `_last_pull.txt`, `MARG_PICTURE.txt`, `heartbeat.txt`, `_outbox_send_log.txt`, `_outbox_state.json`, `BACKUP.txt` |
| **DRIVE** | `H:\My Drive\Clinic Data Archive` listed this session via `device_list_dir` |
| **REPO** | the git *working copy* at `D:\dr-manoj-git\drmanoj-clinic-automation\` (files read, no git run) |

**Verdict counts — 82 claims tested**

| verdict | count |
|---|---|
| VERIFIED | 42 |
| WRONG | 17 |
| STALE | 12 |
| UNVERIFIABLE | 11 |

---

## 1 · CORRECTIONS TABLE

### 1.1 `MARG_PIPELINE_REFERENCE_v1.md`

| # | § | claim as written | verdict | the measured truth | evidence |
|---|---|---|---|---|---|
| 1 | 1 | "MEDICAL PC (Windows 10 Pro · python 3.11.9 bundled at `D:\SendToClinic\pyportable`)" | VERIFIED | Windows 10 Pro build 19045; bundled python 3.11.9 | MEAS |
| 2 | 1 | "Marg ERP 9+ writes reports into `D:\MARGERP\users\<uid>\report\REPORT_n.XLS` (FIXED slot names, OVERWRITTEN on every run)" | VERIFIED | live heartbeat SLOTS line shows `61376/REPORT_2.XLS`; the sender walks `%%U\report\REPORT_1.XLS` | LIVE `heartbeat.txt`; CODE `medical_SendToClinic\SEND_TO_CLINIC.bat:60` |
| 3 | 1 | "`medical_agent.py` (autostart: `Startup\MargAgent.cmd`, runs at LOGON)" | VERIFIED | the agent starts only from `Startup\MargAgent.cmd`, via `pyportable\pythonw.exe`; no scheduled task | MEAS |
| 4 | 1 | "owns `marg_watch.py` as a CHILD process; restarts it within 60s if it dies" | VERIFIED | liveness checked every 30 s, restarted in the same loop | CODE `medical_SendToClinic\medical_agent.py:58` (`CHECK_EVERY = 30`), `:405`, `:715` |
| 5 | 1 | "heartbeat every 5 min -> clinic Drive `\FromMedical`" | VERIFIED | `BEAT_EVERY = 300` | CODE `medical_agent.py:57`; LIVE heartbeat 2026-08-26T12:18:16 |
| 6 | 1 | "applies allowlisted updates from `\ToMedical\_kit` (compile-checked, hash-verified)" | VERIFIED | allowlist of exactly three names; `py_compile` gate; md5 compare both sides | CODE `medical_agent.py:128-132`, `:237-243`, `:265-270` |
| 7 | 1 | "`marg_watch.py` captures .xls/.xlsx/.pdf from **BOTH** folders" | **WRONG** | **THREE** roots: `D:\MARGERP\users`, `D:\MARG REPORTS`, `C:\Users\Public\MARG` | MEAS; CODE `medical_agent.py:51-52`; LIVE heartbeat "watching: D:\MARGERP\users + D:\MARG REPORTS + C:\Users\Public\MARG" |
| 8 | 1 | "-> `D:\SendToClinic\_captured` (renamed by content hash, dedup by md5)" | VERIFIED (imprecise) | dedup is by full md5; the **name** carries only the first 8 hex characters, and the original extension is kept | CODE `MargPull\marg_watch.py:98`, `:104-105` |
| 9 | 1 | "manojz reads medical READ-ONLY. manojz CANNOT write to medical." | VERIFIED | share is `\\100.119.151.40\DDrive`, D: only, writes return ERROR 5 | MEAS; CODE `PULL_FROM_MEDICAL.bat:55`, `:170-173` |
| 10 | 1 | "Tailscale … IS load-bearing … the whole pull leg runs over this share" | VERIFIED | the pull's only report source is `\\100.119.151.40\DDrive`; there is no second transport in the batch | CODE `PULL_FROM_MEDICAL.bat:55`, `:74`, `:89-91` |
| 11 | 1 | "MANOJZ scheduled task 'Marg pull from medical', **every 10 minutes**" | UNVERIFIABLE | the task name is real (the batch tries to repoint it by that name) and the last run succeeded — but `_last_pull.txt` is written with `>` and holds **one** run only, so no cadence is observable. *Tried:* reading `_last_pull.txt` (START 26-08-2026 12:20:01.15 / END 12:20:20.12 -- ok) and `_task_repoint_tried.txt`. `schtasks` was not run — this session is read-only | CODE `PULL_FROM_MEDICAL.bat:43`, `:51-54`; LIVE `_last_pull.txt` |
| 12 | 1 | The chain diagram's **step order**: `marg_watch → marg_router.py → marg_rescan → marg_gate send → robocopy mirrors → robocopy MARG REPORTS → robocopy MargArchive offsite → marg_gate status` | **WRONG** | actual order is `marg_watch (:89) → robocopy SendToClinic mirror (:103) → robocopy MARG REPORTS (:114) → robocopy Drive offsite (:127) → marg_rescan (:140) → marg_gate send (:151) → marg_gate status (:164) → END (:184) → pipeline_status.py (:188)`. The three robocopies run **before** the rescan and the send. Consequence the doc hides: the offsite copy at `:127` runs before the send at `:151`, so a report sent this cycle reaches Drive only on the **next** cycle | CODE `PULL_FROM_MEDICAL.bat` lines as cited |
| 13 | 1 | "`marg_router.py` classify · verify · name by the date INSIDE the file" — drawn as a pipeline step | **WRONG** | `marg_router.py` is **never invoked** by `PULL_FROM_MEDICAL.bat`. It is a module imported by `marg_watch --route` and by `marg_rescan`. Grep of the whole batch finds no `marg_router` line | CODE `PULL_FROM_MEDICAL.bat` (whole file, 228 lines); `marg_router.py:221-224` |
| 14 | 1 | "`marg_watch.py --once --route` over **4** medical folders" | VERIFIED | exactly four: `MARGERP\users`, `SendToClinic\Sent`, `SendToClinic\NEEDS_UPLOAD`, `SendToClinic\_captured` | CODE `PULL_FROM_MEDICAL.bat:89-91` |
| 15 | 1 | "robocopy medical SendToClinic -> `margsync\medical_SendToClinic` (its logs, readable here)" | VERIFIED | `/E`, excluding `Sent pyportable __pycache__ _old 01_MEDICAL_PC` and `token.txt *.zip` | CODE `PULL_FROM_MEDICAL.bat:103-105` |
| 16 | 1 | "robocopy MargArchive -> `H:\My Drive\Clinic Data Archive\MargArchive` (offsite)" | VERIFIED | present and connected | CODE `:127`; DRIVE `connectedFolders` includes `H:\My Drive\Clinic Data Archive` |
| 17 | 1 | "`marg_gate.py status` refresh `MARG_PICTURE.txt` + `_UPLOAD_NOW`" | VERIFIED | | CODE `:164`; `marg_gate.py:659`, `:916` |
| 18 | 1 | VPS leg: "POST … -> `marg_push_staging` -> (checker presses Apply) -> `finance.db`" | UNVERIFIABLE | not reachable from either PC. *Tried:* the local repo working copy — it contains **no `marg-push` route at all** (see #74) | REPO `finance\*.py` |
| 19 | 2 | "An S201 code audit read `START_MARG_WATCHER.bat` (one folder) instead of the actual autostart **`MargWatcher.cmd` (two)**" | **STALE** | there is no `MargWatcher.cmd` today; the autostart is `MargAgent.cmd`. `START_MARG_WATCHER.bat` is **absent from the medical PC** — it survives only in the never-purged manojz mirror. And "(two)" is wrong: three | MEAS; CODE `medical_SendToClinic\START_MARG_WATCHER.bat` (mirror copy, 22-Aug) |
| 20 | 2 | "'`marg_report.py` is byte-for-byte the server's' — FALSE. **PC copy** `28b47d44…` (S180); server `6411a57d…` (S193). Two builds apart." | **STALE — and it now names the wrong machine** | `marg_report.py` is **ABSENT from the medical PC**. The `28b47d44` copy that still runs is on **manojz**: `MargPull\marg_report.py` md5 `28b47d447cfd966411742055717a5c56`, imported by `marg_router.py` for `deep_verify: "marg_report"` on every SALE_BILLWISE. The drift moved machines; the doc still points at medical. Separately, no `6411a57d` copy exists anywhere on manojz — the repo working copy is also `28b47d44` | MEAS; CODE md5 of `MargPull\marg_report.py`; `marg_router.py:221-224`; REPO `finance\marg_report.py` = `28b47d447cfd966411742055717a5c56` |
| 21 | 2 | "'queued for upload in Outbox' — FALSE until 25-Aug. Nothing read `_outbox`." | VERIFIED | the string is emitted by the router; the consumer was added at S201 and its log begins 2026-08-25 09:47:03 | CODE `marg_router.py:417`; `PULL_FROM_MEDICAL.bat:142-151`; LIVE `_outbox_send_log.txt` |
| 22 | 2 | "'ToMedical …' … It works now … because Drive is installed on medical and syncs the folder directly" | VERIFIED | and now pinnable: medical's Drive is **`F:\My Drive`**, content LOCAL. The agent re-searches every drive letter each heartbeat rather than hard-coding it | MEAS; LIVE heartbeat KIT line `F:\My Drive\Clinic Data Archive\ToMedical\_kit`; CODE `medical_agent.py:102-118` |
| 23 | 2 | "'install Python, pip install xlrd' … on python 3.11 `xlrd 1.2.0` cannot read `.xlsx` anyway" | VERIFIED | bundled 3.11.9 has **no xlrd and no openpyxl** | MEAS |
| 24 | 3 | "`POST https://followup.dr-manoj.in/finance/api/marg-push` / Header `X-Finance-Marg`" | VERIFIED (client side) | | CODE `marg_gate.py:60`, `:509` |
| 25 | 3 | "Body: multipart/form-data, field name `"file"`, **filename `"REPORT_1.XLS"`**" | **WRONG** | the field name is `file`, but the sender transmits the **archive filename**, e.g. `SALE_BILLWISE_DETAIL__2026-08-25__20260826-081434__813fd43c.XLS`. `marg_gate.py` has a selftest that asserts `filename="REPORT_1.XLS"` is *not* sent. Any client written from this contract would send the wrong filename deliberately | CODE `marg_gate.py:397-405`, `:506`, selftest `:737-742` |
| 26 | 3 | "`401` + `{"error":"not_signed_in", …}` … This is what a stale token looks like; it does not say 'bad token'" | VERIFIED | observed live and logged verbatim | LIVE `_outbox_send_log.txt` 2026-08-25 09:47:03 |
| 27 | 3 | "`503` … fail-closed by design (F-84)" / "`200` + already-received" | UNVERIFIABLE | server behaviour; no such response in the live send log. *Tried:* full read of `_outbox_send_log.txt` (6 entries: one 401, five 200/ACCEPTED) | LIVE |
| 28 | 3 | "The endpoint does NOT dedupe by content. … Client-side state is what prevents duplicates." | UNVERIFIABLE server-side / VERIFIED client-side | the client-side machinery exists exactly as described: `_outbox_state.json`, duplicate markers, per-business-date skip | CODE `marg_gate.py:75`, `:408-447`, `:584-592`; LIVE `_outbox_state.json` |
| 29 | 4 | "Medical PC — `D:\SendToClinic\token.txt`" | VERIFIED | present (value not read) | MEAS; CODE `marg_gate.py:56` |
| 30 | 4 | "Deliberately **excluded from the manojz mirror** (`/XF token.txt`)" | VERIFIED | | CODE `PULL_FROM_MEDICAL.bat:105` |
| 31 | 4 | "manojz — `D:\Downloads\margsync\SendToClinic\token.txt`, a **cache** … reads the live token off the medical share at send time … falling back to it only when medical is unreachable" | VERIFIED | exactly this, with selftests for all four cases | CODE `marg_gate.py:56-57`, `:196-217`, `:534-535`, selftests `:840-851` |
| 32 | 4 | "VPS — `FINANCE_MARG_TOKEN` in `/etc/systemd/system/clinic-finance.service`" | UNVERIFIABLE | VPS not reachable this session |  |
| 33 | 4 | "**all three copies** … A rotation performed from any one of these breaks the others" | **STALE** | three *stored* copies is still right, but there is now a fourth **consumer** the doc predates: `pipeline_status.py` (S202) posts on every pull using the same secret. It reuses `marg_gate`'s resolution rather than keeping a fourth copy (D349) — but a rotation list that omits it is incomplete | CODE `pipeline_status.py:26-29`; `PULL_FROM_MEDICAL.bat:188`, `:198` |
| 34 | 5.1 | "Sundays are excluded; a report is credited to **every** day it covers" | VERIFIED | `d.weekday() != 6`; a delivered range export credits every day inside it | CODE `marg_gate.py:258-263`, `:425`; LIVE `MARG_PICTURE.txt` |
| 35 | 5.2 | "`_last_pull.txt` — START/END stamps … **Nothing there = the scheduled task is not running.**" | **WRONG as a diagnostic** | the file is opened with `>` and holds the last run only. It can never be "nothing" once the task has ever run — a task that stopped a week ago leaves a stale but perfectly well-formed START/END pair. The real test is the **timestamp**, which the maintenance doc gets right (§1: "within the last 15 minutes") and this one does not | CODE `PULL_FROM_MEDICAL.bat:51-54`, `:184` |
| 36 | 5.2 | the unreachable-but-on diagnosis, `cmdkey /add:100.119.151.40 /user:MEDICAL\SET /pass`, per-Windows-user credentials, "the pull diagnoses all of this itself from S202" | VERIFIED | reproduced line for line by `:diagnose` | CODE `PULL_FROM_MEDICAL.bat:201-228` (the `cmdkey` line verbatim at `:222`) |
| 37 | 5.3 | heartbeat holds "watcher alive/pid/restarts, captures today, the **installed watcher's md5**, and `IGNORED`" | VERIFIED but INCOMPLETE | all four present. The live heartbeat also carries `AGENT` (version + up-to-date-vs-Drive), `SLOTS`, `KIT` (per-file md5 status), `DISK` — none documented | LIVE `heartbeat.txt` |
| 38 | 5.4 | "`MEDICAL_RECENT.bat` — every file written on medical's **D:** in the last N days, any type" | VERIFIED | correctly scoped to D: here (contrast #56); default N = 3, overridable | CODE `MEDICAL_RECENT.bat:26-27`; `medical_inventory.py:27`, `:300-313` |
| 39 | 5.8 | "`margsync\_UPLOAD_NOW\` holds exactly the reports that still need uploading by hand, refreshed every 10 minutes" | VERIFIED | refreshed by `marg_gate status` on every pull | CODE `marg_gate.py:659-686`; `PULL_FROM_MEDICAL.bat:164` |
| 40 | 6 | "`_spool` … **Also the watcher's dedupe memory** — emptying it re-captures everything. Never pruned." | VERIFIED but INCOMPLETE | true for manojz (43 files). The medical PC has a **second, independent** dedupe memory — `D:\SendToClinic\_captured`, 35 files — with the same property, and the doc never says so | CODE `marg_watch.py` `prime_captured`; `medical_agent.py:41`; MEAS (`_captured` = 35) |
| 41 | 6 | "`_outbox` … files are not removed after delivery" | VERIFIED | 12 files present against 5 recorded ACCEPTED deliveries; no removal path | LIVE `_outbox` listing, `_outbox_send_log.txt` |
| 42 | 6 | "`<TYPE>/<YYYY-MM>/` — the archive proper" | VERIFIED but INCOMPLETE | one archive TYPE is not in `signatures.json` at all: `DOCUMENT_PDF`, hard-coded in the router. Live: `MargArchive\DOCUMENT_PDF\2026-04`, `2026-07`, `2026-08` | CODE `marg_router.py:308`, `:319`; LIVE `MargArchive` listing |
| 43 | 6 | "Google Drive offsite is `robocopy /E` — append-only, no purge. `_spool` and `_outbox` are excluded, so **the pending-send queue has no offsite copy.**" | VERIFIED | `/XD _spool _outbox` | CODE `PULL_FROM_MEDICAL.bat:127` |
| 44 | 7 | "`marg_router.py --learn <sample.xls>` prints a signature block. Paste it into `signatures.json`. **A data edit, no code change.**" | VERIFIED | | CODE `marg_router.py:429-441`, `:505`, `:512-513` |
| 45 | 7 | "Within 10 minutes the pull notices the registry changed and **re-judges everything in quarantine**" | VERIFIED | | CODE `PULL_FROM_MEDICAL.bat:133-140`; `marg_rescan.py:58`, `:476-479`; LIVE `MargArchive\_signatures_seen.md5` |
| 46 | 7 | "Each signature carries: `title_regex`, `header`, `uploadable`, `dating`, `deep_verify`, and **`end_marker`** — the row that proves the export finished." | **WRONG** | `--learn` emits only `type, variant, title_regex, header, deep_verify, uploadable`. **It emits no `end_marker` and no `dating`.** Follow §7 literally — learn, paste, done — and you install a signature with no truncation check, which is the exact failure `signatures.json` says the marker exists to prevent: *"Without it a report that stopped mid-print filed as VERIFIED 'structural' and looked perfectly healthy."* One live signature already has none for want of a sample | CODE `marg_router.py:432-437`; `signatures.json:53`, `:69` |
| 47 | 8 | "The medical PC is source profile **#1**. … Attaching a source should be a **profile plus signatures**, never a copied script." | UNVERIFIABLE (aspirational) | no profile mechanism exists. `marg_watch.py`, `marg_gate.py`, `medical_inventory.py` and `pipeline_status.py` each hard-code `\\100.119.151.40\DDrive` and `D:\Downloads\margsync\…`. The doc states a design intent in the present tense | CODE `marg_gate.py:56-59`; `medical_inventory.py:27-30`; `marg_watch.py:44-45` |
| 48 | 8a | "`margwin.exe` must be started with its own folder as the working directory … Marg does accept a command-line argument" | UNVERIFIABLE | not testable read-only: launching a live pharmacy ERP is out of scope, and the medical share is read-only from manojz. Nothing contradicts it |  |
| 49 | 9 | "**No PC-side live pins.** `verify_live_pins.py` runs on the VPS and cannot reach either PC. This is how a two-builds-old parser sat on the medical PC unnoticed." | **STALE** | `pipeline_status.py` (S202) posts what only manojz can see on **every** pull, on both the success and the failure path, and the heartbeat carries the installed watcher md5 plus per-kit-file md5s. The gap has narrowed. The *example* is also stale: the two-builds-old parser is on **manojz**, not medical — and that copy still has no pin | CODE `pipeline_status.py:1-30`; `PULL_FROM_MEDICAL.bat:84`, `:188`, `:198`; LIVE heartbeat |
| 50 | 9 | "**The medical guard cannot run** — its Python has no spreadsheet reader at all." | **STALE** | the premise is true (no xlrd, no openpyxl) but there is no guard to run: `GUARD_AND_SEND.bat` and `guard_and_send.py` are **ABSENT from the medical PC**. They exist only in the never-purged manojz mirror, dated 21-Aug | MEAS; CODE `medical_SendToClinic\GUARD_AND_SEND.bat`, `guard_and_send.py` (mirror only) |
| 51 | 9 | "**Deep verification** exists only for sale reports." | VERIFIED | exactly one signature block carries `"deep_verify": "marg_report"`; every other is `"structural"` | CODE `signatures.json:37`, `:50`, `:66`, `:82`, `:99`, `:117`, `:133`, `:150` |
| 52 | 9 | "**Health checks cannot see this side of the line** … The heartbeat is the bridge; the server-side checks that consume it are not built." | **STALE** | `pipeline_status.py` was built for precisely this and runs every pull. Whether the *server* consumes it is not checkable from here | CODE `pipeline_status.py:1-30` |
| 53 | 9 | "**`xlsx_stdlib.py` is not yet on the medical PC**" | **WRONG** | it is on the medical PC, md5 `bbe11a8953f66c27126c48e773cfbe35`; the live heartbeat's KIT block reads `xlsx_stdlib.py up to date (bbe11a89)`; it is in the agent's install allowlist. manojz's copy is byte-identical | MEAS; LIVE heartbeat; CODE `medical_agent.py:130`; md5 of `MargPull\xlsx_stdlib.py` |

### 1.2 `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md`

| # | § | claim as written | verdict | the measured truth | evidence |
|---|---|---|---|---|---|
| 54 | 1 | "`MargPull\_last_pull.txt` — a `START` and an `END … ok` **within the last 15 minutes**" | VERIFIED | live: `START 26-08-2026 12:20:01.15` / `END 26-08-2026 12:20:20.12 -- ok` | LIVE |
| 55 | 1 | "heartbeat written **within the last 10 minutes** · `WATCHER : ALIVE` · `IGNORED : 0`" | VERIFIED | live: written 2026-08-26T12:18:16, `WATCHER : ALIVE, pid 13728`, `IGNORED : 0` | LIVE |
| 56 | 1 | "`MARG_PICTURE.txt` — `days with NO export : 0` and `exports NOT on server : 0`" | VERIFIED | live: both 0, 12 reports verified, coverage 2026-08-17..2026-08-25 | LIVE |
| 57 | 1 | "All three are on manojz. None needs a login." | VERIFIED | `H:\My Drive\Clinic Data Archive` is manojz's connected Drive folder | DRIVE `get_device_info` |
| 58 | 2 | "`MEDICAL_RECENT.bat` lists **EVERY file written on the medical PC** in the last 3 days, any type. If Marg wrote nothing, nothing was exported. **That is the answer.**" | **WRONG** | it lists everything on the medical PC's **D: drive only** — the share is `\\100.119.151.40\DDrive`, D: only, read-only. `C:\Users\Public\MARG` — a real watch root where Marg writes PDFs — is **invisible** to it. A report exported there and missed by the watcher would be reported as "Marg wrote nothing", and the doc instructs the reader to accept that as the answer | MEAS; CODE `medical_inventory.py:27`, `:302`, `:313`; `medical_agent.py:43-44` |
| 59 | 2 | "heartbeat older than ~10 min -> the AGENT is not running on medical. Re-run `ToMedical\INSTALL_AGENT.bat` there." | VERIFIED | the file exists on Drive (6251 bytes) | DRIVE `ToMedical\INSTALL_AGENT.bat` |
| 60 | 2 | "`WATCHER : DOWN` -> the agent will restart it within a minute." | VERIFIED | 30-second liveness loop | CODE `medical_agent.py:58`, `:715` |
| 61 | 2 | the whole "unreachable but the PC is ON" flow — ping, `dir \\…\DDrive\MARGERP\users`, `cmdkey /add:… /user:MEDICAL\SET /pass`, per-user credentials, `schtasks … findstr /i "Run As User"` | VERIFIED | reproduced line for line, including the exact `cmdkey` and `schtasks` strings | CODE `PULL_FROM_MEDICAL.bat:209-228` |
| 62 | 2 | "`HTTP 401` -> the token changed. **The sender reads it live from the medical PC, so this means the SERVER's token changed.**" | **WRONG** | the sender reads the live token **only when the medical share is reachable**. When it is not, `resolve_token` falls back to the manojz cache and prints `cache`. A 401 in that state means the **cache** is stale — which is exactly the five-day failure the reference doc §4 describes and which the send log records. This document's own §6 warns about that case and §2 forgets it. The correct instruction is: read the `token source:` line `marg_gate` prints | CODE `marg_gate.py:196-217`, `:534-535`, selftest `:846-848`; LIVE `_outbox_send_log.txt` 2026-08-25 09:47:03 |
| 63 | 2 | "A console window keeps popping up — Fixed by `MargPull\FIX_POPUP.bat` (S201). If it returns, the scheduled task has been repointed at the batch again instead of `PULL_HIDDEN.vbs`." | VERIFIED | both files present; the batch's own one-shot repoint has already been attempted | CODE `FIX_POPUP.bat`, `PULL_HIDDEN.vbs`, `PULL_FROM_MEDICAL.bat:40-47`; LIVE `_task_repoint_tried.txt` |
| 64 | 2a | "D347 records Tailscale as … NOT load-bearing. That is wrong … the reports themselves travel by Tailscale, and nothing else carries them today." | VERIFIED | see #10 | CODE `PULL_FROM_MEDICAL.bat:55`, `:74`, `:89-91` |
| 65 | 3 | "**monthly** — `MEDICAL_INVENTORY.bat` — **proves every export on the medical PC was captured**" | **WRONG** | same defect as #58 — it can only prove it for **D:**. It cannot see `C:\Users\Public\MARG`. "Proves" overstates what the tool can do | CODE `medical_inventory.py:27`, `:209-215`, `:235` |
| 66 | 3 | "**never** — the pull, the send, the rescue, the picture — all automatic, every 10 minutes" | VERIFIED | all four are in the batch | CODE `PULL_FROM_MEDICAL.bat:89`, `:140`, `:151`, `:164` |
| 67 | 3 | "**quarterly** — review `margsync\_to_delete\` and empty it" | VERIFIED but INCOMPLETE | exists (`_to_delete\S201_20260825`). Drive has a **second** parked folder the doc never mentions: `Clinic Data Archive\_to_delete_S201` | LIVE; DRIVE |
| 68 | 4 | manojz folder table | VERIFIED but INCOMPLETE | every row listed is correct. Omitted from the table: `_mvtest\` (present, holds `b.txt`), **`SendToClinic\`** — the folder holding the token cache, i.e. the only secret in `margsync` — and the three top-level report files `MARG_PICTURE.txt`, `MEDICAL_INVENTORY.txt`, `MEDICAL_RECENT.txt` | LIVE `margsync` listing |
| 69 | 4 | "`_UPLOAD_NOW\` — reports still needing a manual upload. **Empty = nothing to do**" | **WRONG as written** | the folder is **never empty**: `refresh_upload_folder` always writes a `READ_ME.txt` into it, and that is its entire live content. The correct test is "contains only `READ_ME.txt`" | CODE `marg_gate.py:686`; LIVE `_UPLOAD_NOW\READ_ME.txt` |
| 70 | 4 | "medical PC — `D:\SendToClinic\`: `_captured` (the watcher's spool), `heartbeat.txt`, `agent.log`, `pyportable\`, and the agent + watcher scripts." | **STALE / INCOMPLETE** | 77 files. Also present and undocumented: **`token.txt`** (the only copy of the secret on that machine), `Sent\` (16), `_old\` (3), `SEND_TO_CLINIC.bat`, `medical_census.py`, `xlsx_stdlib.py`, `pyportable.zip` (11.9 MB), `SCREEN REC 21 8 2026.zip` (3.4 MB). Omitting `token.txt` from the folder map of the machine that holds it is the significant miss | MEAS |
| 71 | 4 | "Google Drive — `Clinic Data Archive\`: `MargArchive` (offsite copy), `ToMedical`, `FromMedical`." | **STALE / INCOMPLETE** | live contents are `MargArchive`, `ToMedical`, `FromMedical`, **`MargBackups`**, `Bank Statements`, `_to_delete_S201`. `MargBackups` matters most: it now holds ~180 Marg `.mbk` / `.mst` database backups copied off the E: stick today, and it is the **only offsite copy of the Marg database that exists**. No document mentions it | DRIVE listing; LIVE `MargBackups` mtimes 26-Aug |
| 72 | 5 | "`FromMedical\heartbeat.txt` — and say what you were doing. … The first is usually enough on its own" | VERIFIED but INCOMPLETE | `FromMedical` now also holds `heartbeat.json`, `BACKUP.txt`, `CENSUS.txt`, `SURVEY.txt`, `READ_ME.txt` — the census/backup survey products, none of them documented anywhere | DRIVE `FromMedical` listing |
| 73 | 6 | "**The medical PC's watcher starts at LOGON.** A machine left at the login screen after a reboot captures nothing" | VERIFIED | `Startup\MargAgent.cmd` at logon; no scheduled task for it | MEAS |

### 1.3 `MARG_INGESTION_REFERENCE_v1.md`

This document describes the VPS. It is **not testable from either PC**, and the one local artefact
that might have stood in for the VPS does not.

| # | § | claim as written | verdict | the measured truth | evidence |
|---|---|---|---|---|---|
| 74 | hdr | "verified against the **live bytes** (`finance_app.py 2c99b2c6` → `d930b6b5`, `finance_ingest.py 6cb83302`, `marg_report.py 6411a57d`)" | UNVERIFIABLE — **and the local repo does not support any of the three hashes** | the manojz git working copy at `D:\dr-manoj-git\drmanoj-clinic-automation\finance\` reads `finance_app.py 7b62b7ae661914505c864d71cc6c9abc`, `finance_ingest.py 2cd0f264fb1a091f3e3ec7c3f4a17438`, `marg_report.py 28b47d447cfd966411742055717a5c56`. None matches. That checkout also contains **no `marg-push` route, no `days_payload`, no `marg_net_sql`** — i.e. it predates the entire ingestion chain the document describes. *Tried:* md5 of all three files and a grep of `finance\*.py` for each identifier. `git` was not run (F-131), so I cannot say whether this is a stale branch or a stale working tree | REPO |
| 75 | 2 | "Body: multipart/form-data, field `"file"`, filename `"REPORT_1.XLS"`" | **WRONG** | same defect as #25 — the sender transmits the archive filename and has a selftest asserting `REPORT_1.XLS` is not sent | CODE `marg_gate.py:397-405`, `:506`, `:737-742` |
| 76 | 2 | "`401` `{"error":"not_signed_in"}` — the token did not match … it never says 'bad token'" | VERIFIED | observed live | LIVE `_outbox_send_log.txt` |
| 77 | 2 | "this is why `marg_gate.py` keeps `_outbox_state.json`" | VERIFIED | present, with `business_date` / `export_stamp` / `http` / `result` / `when` per md5 | CODE `marg_gate.py:435-447`; LIVE `_outbox_state.json` |
| 78 | 0, 3–9 | everything else: `day_line` / `sale_item` separation, `days_payload` shape, the confidence gate and its 0.99 / 0.95 / 0.60 / 0.50 scores, `min_confidence` 0.70, supersede-first, `marg_net_sql`, the batch statuses, the ₹ tables, the review-queue counts, the `days_differing[:5]` truncation | UNVERIFIABLE | VPS and its database are out of reach this session; the local repo predates the code (#74). *Tried:* md5 of all three finance files, and greps of `finance\*.py` for `marg_net_sql`, `days_payload`, `marg-push`, `min_confidence`. Only `min_confidence` (`"0.70"` default) and a `0.95`/`0.99` confidence pair exist in the local `finance_ingest.py` — consistent with the doc, but from code that lacks the endpoint | REPO `finance_ingest.py:139`, `:226`, `:367` |

### 1.4 `S195_Medical_Watcher_LIVE_Reference.md`

Nominally superseded, but still one of the four documents in circulation and still cited by name.
**Nearly every operational claim in it is now false**, and one of them is actively dangerous.

| # | § | claim as written | verdict | the measured truth | evidence |
|---|---|---|---|---|---|
| 79 | hdr | "**This doc is the single reference** — if any of it breaks, start here." | **WRONG / EXPIRED** | superseded by `MARG_PIPELINE_REFERENCE_v1`, which says so in its own header. A "sole reference" label with nothing to expire it | the two documents |
| 80 | 1 | "watches: `D:\MARGERP\users` / `D:\MARG REPORTS`" | **WRONG** | three roots — see #7 | MEAS; CODE `medical_agent.py:51-52`; LIVE heartbeat |
| 81 | 1 | "on a NEW **.xls/.xlsx**" and "**.txt is ignored — the watcher only takes Marg's .xls/.xlsx**" | **WRONG** | `EXTS = (".xls", ".xlsx", ".pdf")` since S201. PDFs are captured and archived; live examples in `MargArchive\DOCUMENT_PDF\2026-04`, `2026-07`, `2026-08` | CODE `marg_watch.py:49`, `:44-48`; LIVE archive listing |
| 82 | 1 | "named `<stamp>__<slot>__<md5>.xlsx`" | **WRONG twice** | the hash in the name is `digest[:8]`, not the md5, and the original extension is preserved, not forced to `.xlsx`. Live example: `20260826-081436__REPORT_2__813fd43c.XLS` | CODE `marg_watch.py:104-105`; LIVE heartbeat CAPTURES line |
| 83 | 2 | "**Autostart:** `%APPDATA%\…\Startup\MargWatcher.cmd`" with the quoted two-folder command line | **WRONG** | the only startup entry is `Startup\MargAgent.cmd`, running `pyportable\pythonw.exe medical_agent.py`; the agent then launches the watcher as a child over three folders. No `MargWatcher.cmd` exists | MEAS; CODE `medical_agent.py:405`, `:448` |
| 84 | 2 | "no admin, no Task Scheduler (the earlier `Register-ScheduledTask` approach failed — task **'Marg export watcher' never registered**; abandoned)" | VERIFIED | Task Scheduler holds six non-Microsoft tasks, all Google/OneDrive. "Marg export watcher" does not exist | MEAS |
| 85 | 2 | the restart recipe: "`Stop-Process -Name python,pythonw -ErrorAction SilentlyContinue`" then start `marg_watch.py` directly | **WRONG — AND DESTRUCTIVE IF FOLLOWED** | `pythonw` is the **agent**. This kills the supervisor as well as the watcher, and nothing restarts the agent until the next logon: the heartbeat stops, kit updates stop, and watcher restarts stop. The machine then looks healthy from the PC and dead from the clinic. PowerShell 5.1.19041.6456 is present, so the recipe still runs exactly as written | MEAS (agent runs as `pythonw.exe medical_agent.py`); CODE `medical_agent.py:405` |
| 86 | 3 | "Router — **five** report types self-classify" | **WRONG** | `signatures.json` holds **8 signature blocks across 6 types**: `SALE_BILLWISE` ×2, `STOCK_CLOSING` ×2, `STOCK_EXPIRY`, `PURCHASE_SUPPLIERWISE`, `PURCHASE_BILLWISE`, `STOCK_VALUATION` — plus the hard-coded `DOCUMENT_PDF` route, which is a seventh archive type with no signature at all | CODE `signatures.json` (`"type"` ×8), `marg_router.py:308` |
| 87 | 3 | "Repo mirror: `margpull/` … **Publish with PUBLISH_ALL**" | UNVERIFIABLE | `git` is barred this session (F-131) and I did not inspect repository state |  |
| 88 | 4 | "**All clinic PCs use bundled `pyportable\python.exe`, called by full path**" | VERIFIED | agent, watcher and the manojz pull all resolve a full-path interpreter first | MEAS; CODE `medical_agent.py:39`; `PULL_FROM_MEDICAL.bat:62` |
| 89 | 5.1 | "**manojz cannot push to medical** … Delivery TO medical must be a medical-side PULL" | VERIFIED — and since RESOLVED | still read-only (ERROR 5), and the medical-side pull the item asks for now exists: the agent's allowlisted kit apply | MEAS; CODE `PULL_FROM_MEDICAL.bat:170-173`; `medical_agent.py:128-132` |
| 90 | — | kit file `READ_ME_FIRST.txt` (shipped alongside): "registers a logon task (**"Marg export watcher"**) that starts the watcher at every restart" and "**Needs Python 3 (already on this PC)**" | **WRONG** | the task was never registered (S195's own §2 says so), and the "already on this PC" line is contradicted by S195's own "hidden villain" paragraph. Both statements sit in the live mirror, one folder apart from the document that refutes them | MEAS; CODE `medical_SendToClinic\READ_ME_FIRST.txt` |

---

## 2 · TRUE BUT EXPIRING — stated as permanent, actually a snapshot

Each of these is correct today and will be silently wrong later. A MASTER document should carry them
with a **measured-on** date, or move them out of prose and into a pointer at the file that measures
them.

| stated as | actually | how it expires | where it should live |
|---|---|---|---|
| `H:\My Drive\Clinic Data Archive` (manojz) — hard-coded in `PULL_FROM_MEDICAL.bat:59` and in both PC docs | correct today | Google Drive for Desktop reassigns its letter when switched between streaming and mirrored. The batch degrades gracefully (`:125` skips offsite) — **silently**, which is worse | the code already does the right thing on medical (`medical_agent.py:102-118` re-searches every letter each heartbeat). manojz does not; that asymmetry should be written down |
| `F:\My Drive` (medical) — not stated in any document, only in the live heartbeat | correct today, content LOCAL not streaming | same mechanism | MASTER should state both letters **and** that only one of the two is auto-discovered |
| `\\100.119.151.40\DDrive` — treated as an address | a **Tailscale** address, i.e. a tunnel identity, not a LAN one | it survives a network change but not a re-provisioned Tailscale identity | one named constant, with the fact that four separate scripts hard-code it |
| "`D:\SendToClinic` holds 77 files"; `_captured` 35; `Sent` 16; `_old` 3 | counts on 26-Aug-2026 | every capture changes them | never quote counts as description — quote the file that reports them (`heartbeat.txt`, `CENSUS.txt`) |
| md5s: `SEND_TO_CLINIC.bat e19a8a77`, `marg_watch.py aa55cdb5`, `xlsx_stdlib.py bbe11a89`, `medical_agent.py 7b9a76f2` | correct on 26-Aug | any kit push moves them | the heartbeat already prints the watcher and kit md5s live. Pin **only** what nothing else measures: `medical_agent.py` (excluded from the allowlist by design) and `MargPull\marg_report.py` |
| "**PC copy `28b47d44`** … server `6411a57d` … Two builds apart" | the drift is real but has **moved machines** | it moved once already, silently | see #20 — the MASTER must say *manojz*, and say that `marg_router` imports it |
| "`marg_watch.py` … the installed watcher's md5" as a single value | there are **two different builds live**: medical `aa55cdb5`, manojz `MargPull\marg_watch.py 2076fe1d` | nothing compares them; no document says two exist | MASTER must state that the medical resident watcher and the manojz sweep watcher are separate builds, and which one the heartbeat's md5 refers to |
| "**This doc is the single reference**" (S195); "**Supersedes** `S195_…`" (REFERENCE v1) | the first was true for two days | a "sole reference" label with no expiry is how S195 stayed in circulation after being superseded | supersession belongs in `CANONICAL_MANIFEST.md`, not in a self-description inside the document |
| "the oldest open item in the project (21-Aug)" — token rotation | true, and ageing | the sentence gets less true every day it stays unchanged | state the date, not the ordinal |
| "eight reports sat there", "5 days", "8h40m", "eleven verified reports … three days" | incident figures, correct | they read as current state | keep them, but mark them as incidents with dates — they are the best evidence in the whole document set |

---

## 3 · WHAT THE DOCUMENTS OMIT ENTIRELY

Ordered by what would hurt most, restoring from nothing.

1. **THERE IS NO MARG DATABASE BACKUP RUNNING. NOTHING ANYWHERE SAYS SO.**
   `D:\MARGERP\Data` is 1,075 files / 0.9 GB of open FoxPro tables. `serverbackup` gets a
   day-of-week `.mst` near-daily but a real `*_c18_d_*` pair only sporadically — 26-Aug, 25-Aug,
   22-Aug, then a **12-day gap** to 10-Aug. The `E:` stick's newest `.mbk` is 22-Aug (4.1 days);
   `E:\auto` and `E:\MARGBCKUP\auto` are **EMPTY**; `E:\MARGBCKUP` was last written **09-Oct-2025**;
   28.5 GB of 28.9 GB free. **Nothing in Task Scheduler and nothing at startup runs any backup.**
   Four documents describe how to keep a *report* safe in triplicate and not one sentence covers the
   *database* those reports are drawn from. (`BACKUP.txt`, the survey that establishes this, is
   itself undocumented.)

2. **`pipeline_status.py` — the S202 monitor — is in no document.** It runs at the end of every pull,
   on both the success path (`:188`) and the failure path (`:84`), posts what only manojz can see,
   and reuses the Marg token. The reference doc's §9 still lists the gap it was built to close.

3. **`MargBackups\` on Drive is in no document.** ~180 `.mbk` / `.mst` files copied off the E: stick
   today — the only offsite copy of the Marg database in existence. Undocumented means unmaintained.

4. **Marg partitions its tables by financial year in the file EXTENSION** — `.c18` = FY 2026-27,
   `.c17` = the year before. Nobody restoring this system would guess that, and it decides which
   files matter.

5. **`medical_census.py` (S203.1) and its products** — `CENSUS.txt`, `SURVEY.txt`, `BACKUP.txt`,
   `heartbeat.json` — are in the kit allowlist (`medical_agent.py:131`), are pushed to `FromMedical`,
   and appear in no document.

6. **Two independent dedupe memories, not one.** `MargArchive\_spool` on manojz **and**
   `D:\SendToClinic\_captured` on medical. The docs name only the first. Emptying either
   re-captures everything.

7. **The pull does not watch `D:\MARG REPORTS` or `C:\Users\Public\MARG`.** Its four folders are
   `MARGERP\users`, `SendToClinic\Sent`, `SendToClinic\NEEDS_UPLOAD`, `SendToClinic\_captured`
   (`:89-91`). Everything the doctor saves by hand, and every PDF Marg writes to the Public folder,
   reaches the archive **only** if the medical watcher copied it into `_captured` first. The watcher
   is a single point of failure for two of the three sources, and no document says so.
   `C:\Users\Public\MARG` is additionally **unreachable** from manojz — the share is D: only — so
   the two audit tools cannot cross-check it either (#58, #65).

8. **`DOCUMENT_PDF` is a hard-coded archive type with no signature** (`marg_router.py:308`). It has
   three months of live content. `--learn` cannot produce it and `signatures.json` cannot describe it.

9. **`--learn` does not emit `end_marker` or `dating`** (#46). The one procedure the documents present
   as safe to run unsupervised silently omits the completeness check.

10. **The manojz git working copy is far behind the VPS.**
    `D:\dr-manoj-git\drmanoj-clinic-automation\finance\` has **no `marg-push` route at all**. Anyone
    treating it as the reference for the server half reads code that predates the whole ingestion
    chain. No document warns of this.

11. **The medical PC's own `SEND_TO_CLINIC.bat` still exists (`e19a8a77`) but its companions do not.**
    `GUARD_AND_SEND.bat`, `guard_and_send.py` and `marg_report.py` are gone from that machine.
    No document states what the surviving `.bat` does now, or whether it should be there.

12. **Restoring the medical PC needs, in order:** `pyportable\` (there is no system Python — the
    Store stub silently exits), `marg_watch.py`, `medical_agent.py`, `xlsx_stdlib.py`,
    `medical_census.py`, `token.txt`, `Startup\MargAgent.cmd`, and Google Drive signed in as
    `drmka.ortho@gmail.com` with **local** (not streaming) content. `medical_agent.py` is
    **deliberately excluded from the self-update allowlist** (`:125-127`) — it is the one file that
    must be placed by hand, and no document lists this sequence.

---

## 4 · WHERE A DOCUMENT CONTRADICTS THE LIVE CODE — both quoted

**A. Watch roots — two documents say two, the code and the machine say three**

> `MARG_PIPELINE_REFERENCE_v1.md` §1: "`marg_watch.py` captures .xls/.xlsx/.pdf from **BOTH** folders"
> `S195_…` §1: "watches: `D:\MARGERP\users` / `D:\MARG REPORTS`"

```
medical_agent.py:51-52
    WATCH_DIRS = [r"D:\MARGERP\users", r"D:\MARG REPORTS",
                  r"C:\Users\Public\MARG"]
```
Live heartbeat, 2026-08-26T12:18:16: `watching: D:\MARGERP\users + D:\MARG REPORTS + C:\Users\Public\MARG`

**B. `marg_router.py` as a pipeline step — the batch never calls it**

> `MARG_PIPELINE_REFERENCE_v1.md` §1: "`marg_router.py`   classify · verify · name by the date INSIDE the file"

`PULL_FROM_MEDICAL.bat` contains no `marg_router` invocation in 228 lines. Its only appearance is as
an import:
```
marg_router.py:221-224
    if sig and sig.get("deep_verify") == "marg_report":
            import marg_report
```

**C. Upload filename — both server-facing documents state a filename the sender refuses to send**

> `MARG_PIPELINE_REFERENCE_v1.md` §3 and `MARG_INGESTION_REFERENCE_v1.md` §2:
> "multipart/form-data, field name `"file"`, filename `"REPORT_1.XLS"`"

```
marg_gate.py:506
    body, ctype = build_multipart(data, filename=os.path.basename(path))

marg_gate.py:742  (selftest)
       b'filename="REPORT_1.XLS"' not in _b)
```

**D. 401 diagnosis — the maintenance doc's §2 contradicts its own §6 and the code**

> `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` §2: "`HTTP 401` -> the token changed. The sender reads it
> live from the medical PC, **so this means the SERVER's token changed.**"
> …and §6 of the same document: "a hand-copy went stale and answered 401 for five days."

```
marg_gate.py:196-217   resolve_token(unc_path, local_path)
    """(token, where) -- the live token from the medical PC if that share is
    ...
    tok = read_token(local_path)      # falls back to the cache
marg_gate.py:846-848   (selftest)
    ck("token: falls back to cache when medical is unreachable", ...)
    ck("token: fallback says so", "cache" in where2)
```

**E. `xlsx_stdlib.py` — the doc lists it as a gap; the machine has it**

> `MARG_PIPELINE_REFERENCE_v1.md` §9: "**`xlsx_stdlib.py` is not yet on the medical PC** — not
> needed until verification runs there."

Live heartbeat: `xlsx_stdlib.py     up to date (bbe11a89)`. `medical_agent.py:130`:
`"xlsx_stdlib.py": r"D:\SendToClinic\xlsx_stdlib.py",`. MEAS: `xlsx_stdlib.py
bbe11a8953f66c27126c48e773cfbe35` present.

**F. Signature fields — §7 lists six, `--learn` emits four of them**

> `MARG_PIPELINE_REFERENCE_v1.md` §7: "Each signature carries: `title_regex`, `header`,
> `uploadable`, `dating`, `deep_verify`, and **`end_marker`**"

```
marg_router.py:432-437
    block = {
        "type": "CHANGE_ME", "variant": "DEFAULT",
        "title_regex": TITLE_RE_FOR(title),
        "header": header,
        "deep_verify": "structural", "uploadable": False,
    }
```

**G. The S195 restart recipe kills the supervisor**

> `S195_…`: "`Stop-Process -Name python,pythonw -ErrorAction SilentlyContinue`"

MEAS: the agent runs as `pyportable\pythonw.exe medical_agent.py`, started from
`Startup\MargAgent.cmd` at logon, with **no scheduled task** to bring it back.
`medical_agent.py:405` shows the watcher is the agent's child — so the recipe kills parent and
child and restores neither.

**H. Report-type count**

> `S195_…` §3: "Router — **five** report types self-classify"

`signatures.json` carries 8 `"type"` blocks across 6 distinct types, plus `DOCUMENT_PDF` hard-coded
at `marg_router.py:308`.

**I. The kit's own README contradicts the document shipped beside it**

> `READ_ME_FIRST.txt` (live, in `medical_SendToClinic\`): "it registers a logon task
> (**"Marg export watcher"**)" and "Needs Python 3 (**already on this PC**)."
> `S195_…` §2: "the earlier `Register-ScheduledTask` approach failed — task 'Marg export watcher'
> **never registered**; abandoned" and "**the medical PC has no system Python**."

MEAS confirms S195 on both counts: no such task exists, and the bundled interpreter is the only one.

---

## 5 · A NOTE ON THE MIRROR, WHICH MAKES ALL OF THIS WORSE

`PULL_FROM_MEDICAL.bat:103` runs `robocopy … /E` with **no `/PURGE`**. `margsync\medical_SendToClinic`
therefore holds **450 files** against the medical PC's **77**. Every file the doctor or a past session
deleted from the medical PC is still sitting in the mirror, with its original timestamp, looking live:
`GUARD_AND_SEND.bat`, `guard_and_send.py`, `marg_report.py`, `INSTALL_WATCHER.bat`,
`START_MARG_WATCHER.bat`, `AutoHotkey64.exe`, `marg_export_macro_v3.ahk`, `_backup_20260822_002354\`,
and eight dated `marg_watch.py.before_*` copies.

The mirror is a graveyard, not a census. **It is not evidence of what is on the medical PC**, and at
least three of the errors in this report (#19, #20, #50) are what happens when it is read as if it
were. The MASTER document must say this in one line, next to the first mention of the mirror.

---
*S203_MARG_DOC_VERIFICATION · 26-Aug-2026 · read-only. No file on either PC was modified; no `git`
command was run; no token value was read or printed; no patient identifier or phone number appears
above.*
