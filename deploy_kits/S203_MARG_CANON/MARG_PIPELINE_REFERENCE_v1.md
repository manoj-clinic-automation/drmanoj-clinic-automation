# MARG PIPELINE — THE REFERENCE

**v1 · 25-Aug-2026 (S201). Supersedes `S195_Medical_Watcher_LIVE_Reference.md` as the authoritative
description of Marg capture and transport.**

Everything here was verified against the running systems on 25-Aug, not copied forward. Where a
previous doc disagreed with reality, the disagreement is named.

> **Why this exists.** The previous sole reference was **wrong on its own diagram** in one direction
> and right in another, and nobody could tell which. The router's design doc and the upload
> contract were unreachable. The coverage map predates this entire estate. A new engineer following
> the old pointers landed on a stale or missing document at three turns out of four.

---

## 1 · THE CHAIN, AS IT ACTUALLY RUNS

```
MEDICAL PC  (Windows 10 Pro · python 3.11.9 bundled at D:\SendToClinic\pyportable)
  Marg ERP 9+ writes reports into  D:\MARGERP\users\<uid>\report\REPORT_n.XLS
       (FIXED slot names, OVERWRITTEN on every run -- this is why capture must be instant)
  Dr Manoj also saves reports by hand into  D:\MARG REPORTS
       │
  medical_agent.py  (autostart: Startup\MargAgent.cmd, runs at LOGON)
       ├── owns marg_watch.py as a CHILD process; restarts it within 60s if it dies
       ├── heartbeat every 5 min -> clinic Drive \FromMedical
       └── applies allowlisted updates from \ToMedical\_kit  (compile-checked, hash-verified)
       │
  marg_watch.py  captures .xls/.xlsx/.pdf from BOTH folders the instant they are written
       -> D:\SendToClinic\_captured        (renamed by content hash, dedup by md5)
       │
       │   Tailscale.  manojz reads medical READ-ONLY. manojz CANNOT write to medical.
       │   *** AND IT IS LOAD-BEARING. D347 calls Tailscale "NOT load-bearing";
       │       that is WRONG and 26-Aug-2026 proved it -- the whole pull leg runs
       │       over this share, and when it closed the feed stopped for 8h40m.
       │       Drive carries the heartbeat and the kit folder; the REPORTS come
       │       through here, and nothing else carries them today. ***
       ▼
MANOJZ  scheduled task "Marg pull from medical", every 10 minutes
  PULL_FROM_MEDICAL.bat:
       stamp START -> _last_pull.txt
       marg_watch.py --once --route   over 4 medical folders -> MargArchive\_spool
       marg_router.py                 classify · verify · name by the date INSIDE the file
       marg_rescan.py --if-signatures-changed   re-judge quarantine IF the registry changed
       marg_gate.py send              drain _outbox to the clinic server
       robocopy medical SendToClinic  -> margsync\medical_SendToClinic   (its logs, readable here)
       robocopy medical MARG REPORTS  -> margsync\marg_reports_mirror
       robocopy MargArchive           -> H:\My Drive\Clinic Data Archive\MargArchive  (offsite)
       marg_gate.py status            refresh MARG_PICTURE.txt + _UPLOAD_NOW
       stamp END -> _last_pull.txt
       │
       ▼
VPS   POST /finance/api/marg-push  ->  marg_push_staging  ->  (checker presses Apply)  ->  finance.db
```

**Automatic:** capture · pull · route · rescue-on-registry-change · send · mirrors · offsite ·
picture refresh · watcher supervision · heartbeat.
**Manual by design:** running the report in Marg · the checker pressing **Apply**.

---

## 2 · WHAT WAS BELIEVED AND WAS NOT TRUE

| claim | reality |
|---|---|
| *"the resident watcher also captures `D:\MARG REPORTS`"* — S195 ref | **TRUE**, and proven from the running process's own command line. An S201 code audit read `START_MARG_WATCHER.bat` (one folder) instead of the actual autostart `MargWatcher.cmd` (two) and reported the opposite. **Trust the running process, not a script that may not be the one running.** |
| *"`marg_report.py` is byte-for-byte the server's"* — S195 kit | **FALSE.** PC copy `28b47d44…` (S180); server `6411a57d…` (S193). Two builds apart. |
| *"queued for upload in Outbox"* — router output | **FALSE until 25-Aug.** Nothing read `_outbox`. Eight reports sat there. |
| *"ToMedical: drop a file here and it appears on the medical PC"* — the folder's own README | **FALSE since 23-Aug.** It describes a manojz relay disabled at S195 (SMB write = ERROR 5). It works now for a different reason: Drive is installed on medical and syncs the folder directly. |
| *"install Python, pip install xlrd"* — S195 setup | Never done against the bundled interpreter, and on python 3.11 `xlrd 1.2.0` cannot read `.xlsx` anyway. |

---

## 3 · THE UPLOAD CONTRACT

No spec existed anywhere. This is reconstructed from the live endpoint and verified by use.

```
POST https://followup.dr-manoj.in/finance/api/marg-push
Header:  X-Finance-Marg: <FINANCE_MARG_TOKEN>
Body:    multipart/form-data, field name "file", filename "REPORT_1.XLS"
```

| response | meaning |
|---|---|
| `200` + `{"ok":true,"verdict":"ACCEPTED-FOR-REVIEW","days":[…],"bills":n,"item_lines":n,"id":n}` | Staged. **Nothing has entered the books.** |
| `200` + a body saying the server already has it | Content already staged. |
| `401` + `{"error":"not_signed_in","message":"Sign in on the clinic portal first."}` | **The token was wrong or absent** — the request fell through to the session gate. This is what a stale token looks like; it does not say "bad token". |
| `503` | `FINANCE_MARG_TOKEN` absent server-side — fail-closed by design (F-84). |

**Rules that matter to any client:**
- The uploaded file is **parsed and deleted inside the same request** (S186). The VPS keeps no
  export file — so a report can never be "re-read from the server". Re-load from the archive.
- Staging is not applying. A day is **skipped and flagged `MARG_DAY_NOT_FILED`** unless the maker
  has filed that day first. File the day, then re-load the export.
- **The endpoint does NOT dedupe by content.** Sending the same bytes twice stages twice. Client-side
  state is what prevents duplicates.
- **Never** decide success from a response *file* that a failed request leaves untouched — that is
  audit finding AF-1, and it caused a false ACCEPTED plus a permanent client-side blacklist. Gate on
  the HTTP code **and** an affirmative body, and record nothing on doubt.

---

## 4 · WHERE THE TOKEN LIVES — all three copies

A rotation performed from any one of these breaks the others. No previous doc listed them together.

1. **VPS** — `FINANCE_MARG_TOKEN` in `/etc/systemd/system/clinic-finance.service` (made durable
   after the 21-Aug crisis, when it had lived somewhere transient and a restart killed the sender).
2. **Medical PC** — `D:\SendToClinic\token.txt`, plain text by design (scoped, stage-only).
   Deliberately **excluded from the manojz mirror** (`/XF token.txt`).
3. **manojz** — `D:\Downloads\margsync\SendToClinic\token.txt`, a **cache**. `marg_gate.py` reads
   the live token off the medical share at send time and refreshes this copy, falling back to it
   only when medical is unreachable. Before S201 this was a hand-copy from 20-Aug and had been
   answering **401 for five days** while medical's own copy worked.

**Rotation is the oldest open item in the project (21-Aug).** Both tokens transited chat during the
S195 diagnosis.

---

## 5 · RUNBOOK — a day did not arrive

Work down. Each step names where the truth lives.

1. **Is the day actually missing?** `MARG_STATUS.bat` on manojz, or read
   `margsync\MARG_PICTURE.txt`. Sundays are excluded; a report is credited to **every** day it
   covers.
2. **Did the pull run?** `margsync\MargPull\_last_pull.txt` — START/END stamps, including a FAILED
   line if it could not start. Nothing there = the scheduled task is not running.

   **`FAILED: medical PC unreachable` DOES NOT MEAN THE PC IS OFF.** On 26-Aug-2026 that line
   repeated every ten minutes for 8h40m while the PC was on, the owner was in an RDP session with
   it, and Tailscale reported it `active; direct`. The real cause was Windows on manojz blocking
   **unauthenticated guest access** to the share after a policy refresh. `ping` the medical address:
   no reply means the machine or the tunnel; a reply means the share is refusing us, and the remedy
   is a stored credential —
   `cmdkey /add:100.119.151.40 /user:MEDICAL\SET /pass` — using an account that HAS a password
   (`MEDICAL\user` has none, and Windows refuses passwordless network logins).
   **Credentials are stored PER WINDOWS USER**, so the scheduled task's Run-As account must be the
   one holding it. The pull diagnoses all of this itself from S202; read what it prints.
3. **Is the medical PC alive and capturing?** `H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt`
   — watcher alive/pid/restarts, captures today, the **installed watcher's md5**, and `IGNORED`:
   files in the watched folders the watcher cannot take.
4. **Was the report ever generated?** `MEDICAL_RECENT.bat` — every file written on medical's D: in
   the last N days, **any type**. If nothing, it was never exported: run it in Marg.
5. **Was it captured but refused?** `MargArchive\_REFUSED\` and `\_UNKNOWN\`, each with a `.txt`
   sidecar giving the reason, title and header.
6. **Was it verified but not sent?** `MargArchive\_NEEDS_ATTENTION.txt` and
   `_outbox_send_log.txt`. Run `SEND_OUTBOX.bat`.
7. **Did it reach the server but not the books?** The day is probably **not filed** — the export is
   skipped until it is. File the day, then re-load.
8. **Manual fallback:** `margsync\_UPLOAD_NOW\` holds exactly the reports that still need uploading
   by hand, refreshed every 10 minutes. Upload at `/finance/approvals` → Choose File.

**Fallback order when a file is wanted:** manojz archive → the medical PC → regenerate in Marg.

---

## 6 · FOLDERS, AND WHAT IS NEVER CLEANED

| folder | meaning |
|---|---|
| `_spool` | byte-safe landing zone that defeats Marg's slot reuse. **Also the watcher's dedupe memory** — emptying it re-captures everything. Never pruned. |
| `_outbox` | reports queued for the clinic server. Drained by `marg_gate.py`; files are not removed after delivery. |
| `_UNKNOWN` | structurally sound, but no signature matched the title. |
| `_REFUSED` | title matched but the layout did not, or an integrity check failed. |
| `_rescued` | quarantine copies whose rescue is proven; a record, not a deletion. |
| `<TYPE>/<YYYY-MM>/` | the archive proper, named by the business date **inside** the file. |

Google Drive offsite is `robocopy /E` — append-only, no purge. `_spool` and `_outbox` are excluded,
so **the pending-send queue has no offsite copy.**

---

## 7 · ADDING A NEW REPORT TYPE

1. `marg_router.py --learn <sample.xls>` prints a signature block.
2. Paste it into `signatures.json`. **A data edit, no code change.**
3. Within 10 minutes the pull notices the registry changed and **re-judges everything in
   quarantine**, rescuing whatever that signature should have caught.

Each signature carries: `title_regex`, `header` (exact prefix match on non-empty cells),
`uploadable`, `dating` (`file_mtime` for reports whose only dates are future ones), `deep_verify`,
and **`end_marker`** — the row that proves the export finished. **Derive a marker from a real
sample; never guess one**, or real reports get refused.

## 8 · ATTACHING A NEW SOURCE (Lab PC / Labmate)

The medical PC is source profile #1. A second source needs: machine + share, watch folders, spool,
python path, its signatures, and its upload target. Attaching a source should be a **profile plus
signatures**, never a copied script.

Survey the lab PC before designing: python? Tailscale? where does Labmate export, in what format?
And note `S181`'s warning — revenue arithmetic is **inverted** between medical and clinic/lab, called
there *"the single most dangerous copy-paste in the build"*. Do not assume replication.

---

## 8a · LAUNCHING MARG FROM A SCRIPT (S202)

`margwin.exe` **must be started with its own folder as the working directory**:

```
cd /d D:\MARGERP
margwin.exe
```

Launched from anywhere else it refuses with *"Few important files not found in SYSTEM / Please
RE-INSTALL software!"* — which is badly misleading and would panic anyone reading it on a live
pharmacy system. The desktop shortcut sets `Start in: D:\MARGERP`, so only scripts hit this.

Marg **does** accept a command-line argument and resolves it as a path (`/?` returns *"Invalid path
or file name"*), but there is no evidence it can be told to RUN A REPORT. That question is with Marg
support; nothing should be guessed at against a live ERP.

## 9 · KNOWN GAPS AT v1

- **No PC-side live pins.** `verify_live_pins.py` runs on the VPS and cannot reach either PC. This is
  how a two-builds-old parser sat on the medical PC unnoticed.
- **The medical guard cannot run** — its Python has no spreadsheet reader at all.
- **Deep verification** exists only for sale reports.
- **Health checks cannot see this side of the line** — every server check watches *arrival at the
  VPS*. Watcher death, pull death, a PDF export and a failing offsite are all invisible there. The
  heartbeat is the bridge; the server-side checks that consume it are not built.
- **`xlsx_stdlib.py` is not yet on the medical PC** — not needed until verification runs there.

---
*MARG_PIPELINE_REFERENCE v1 · S201 · verified against the running systems. No patient identifiers
reproduced; no tokens read or printed.*
