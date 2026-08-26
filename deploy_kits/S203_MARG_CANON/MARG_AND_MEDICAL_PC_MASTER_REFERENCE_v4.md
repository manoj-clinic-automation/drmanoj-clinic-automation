> ## SUPERSEDED — S203 CONSOLIDATION
> **Replaced 26-Aug-2026 by `MARG_MEDICAL_CURRENT.md`** (what is true now) and
> **`MARG_MEDICAL_HISTORY.md`** (why it is like this), both in
> `deploy_kits/MARG_MEDICAL/`. Retained, not deleted (F-23).

# MARG & THE MEDICAL PC — MASTER REFERENCE v4

**Session 203 · 26 August 2026 · Dr Manoj Agarwal, Advanced Orthopaedic Surgery Centre, Bareilly**

> **What this is.** One document for everything at stake on the medical PC and in the
> Marg pharmacy pipeline. It exists because the knowledge was spread across **69
> documents**, of which **39 have no manifest row at all** and **30 exist in exactly one
> store**, and because a verification pass against the live code and the machine itself
> found **17 claims in the current references that are simply wrong** and 12 more stale.
>
> **How to trust it.** Every factual claim below was either measured on the machine on
> 26-Aug-2026, or read out of the live code with a file and line. Where something could
> not be checked it says so. **Nothing here is carried forward on the authority of an
> earlier document** — that practice is what produced the errors this replaces.

---

## 0. HOW TO USE THIS, AND WHAT IT REPLACES

**Read §1, §2 and §5 if you read nothing else.** §1 tells you which machine is which,
§2 tells you how a pharmacy figure travels, §5 is the backup — the only part where a
mistake is unrecoverable.

**This supersedes, on every point where they differ:** `MARG_PIPELINE_REFERENCE_v1`
(`97b3cf73…`), `MARG_PIPELINE_MAINTENANCE_FLOW_v1` (`c2b5251f…`),
`MARG_INGESTION_REFERENCE_v1` (`4d603b72…`), `S195_Medical_Watcher_LIVE_Reference`
(`885090ab…`). Those remain canonical for detail this document does not repeat;
§9 lists every correction so nothing is silently overwritten (F-23).

**The rule that governs this document.** A statement about a running system is a claim
with an expiry date. Drive letters move, counts change, hashes move on every build. So
each section marks its facts **[MEASURED 26-Aug]**, **[CODE]** with a line reference, or
**[DESIGN]** for things that are true by construction. When something contradicts what
you see, believe the machine and tell me.

### 0.1 WHAT THIS DOCUMENT OWNS, AND WHAT IT DEFERS TO

The KB already carries Marg and medical-PC content in many places. **Two documents that
are both plausible and disagree is the failure this project keeps paying for** — F-23,
and the S201 ruling that an uploaded copy is a second source of truth with no hash and no
owner. §4.3 above is a live example: this document asserted a superseded finding as fact
because the successor lived in a store the search did not cover.

**So every fact is owned by exactly one document CLASS, decided by the question it
answers:**

| Class | Answers | Owner |
|---|---|---|
| **STATE** | what is true *now* | the **KB Register**'s live-file table for VPS code · **§3.2 here** for medical-PC pins · the live state files (`MARG_PICTURE.txt`, `heartbeat.txt`, `BACKUP.txt`, `_outbox_state.json`) |
| **MECHANISM** | how it *works* | **this document**, then `MARG_PIPELINE_REFERENCE_v1` · `MARG_PIPELINE_MAINTENANCE_FLOW_v1` · `MARG_INGESTION_REFERENCE_v1` |
| **RULING** | what was *decided* | the **Register's decisions index** and the signed contracts |
| **FAULT** | what is *wrong* | the **Fault Action Register** (F-#) and the Auditor's runs (AF-#) |
| **HISTORY** | what *happened* | the **KB History Archive** |

**The rules that follow from it:**

1. **A fact may be restated outside its owner only as a citation that names the owner.**
   A copy without a pointer goes stale silently — that is F-134's shape.
2. **When a restatement and its owner disagree, the owner wins. When either disagrees
   with a measurement, the measurement wins** (D321(d), F-169). The box is the last word.
3. **History is never in conflict.** An Archive line that is false today is still a true
   record of what was believed then. A conflict exists only where a STATE, MECHANISM or
   RULING document repeats it as current.
4. **A ruling is amended only by a ruling.** Where this document contradicts a decision —
   D347 on Tailscale, D348 on `min_confidence` — the fix is an edit to the **decisions
   index**, not to a reference. Until that happens the decision record stands as written
   and this document flags the disagreement rather than overriding it.
5. **Where this document restates a figure** — file counts, backup ages, first-run
   numbers, live pins — **the figure is a snapshot with a date, and the live file wins.**
   Every such figure here is marked `[MEASURED <date>]` for that reason.

**This document does NOT own, and must not be trusted for:** the VPS live-code pins (the
Register) · fault status and numbering (the Fault Register) · what was decided and when
(the decisions index) · the owner's current task list (`OWNER_TODO_LIVE.md`) · session
history (the Archive) · the D350 scope (its signed contract) · retention policy
(`Clinic_Source_Data_Retention_Policy_v1`).

---

## 1. THE MACHINES

### 1.1 The MEDICAL PC — `MEDICAL`

The machine Marg runs on. **Everything in this project is downstream of it.**

| | |
|---|---|
| OS | Windows 10 Pro build 19045 · PowerShell 5.1.19041.6456 **[MEASURED 25-Aug]** |
| User | `SET` **[MEASURED]** |
| Reached by | Tailscale `100.119.151.40`, share `\\100.119.151.40\DDrive` |
| Reach limits | **The share is READ-ONLY from manojz and exposes the D: drive ONLY.** A write returns ERROR 5 **[MEASURED, S195 probe 06:50 23-Aug]** |
| Marg | `D:\MARGERP\` · `margwin.exe` 13.9 MB, dated 2025-09-24 **[MEASURED 26-Aug]** |
| Our software | `D:\SendToClinic\` — 77 files **[MEASURED 26-Aug]** |
| Python | **bundled** `D:\SendToClinic\pyportable\python.exe` 3.11.9, **no xlrd, no openpyxl** — stdlib only **[MEASURED 25-Aug]** |
| Google Drive | **`F:\My Drive`**, content **LOCAL, not streaming** **[MEASURED 25-Aug]** |
| Default printer | HP Laser 103 107 108 (13 printers installed) **[MEASURED 25-Aug]** |
| Disk | D: 30.5 GB free of 39.1 · C: 32.4 of 79.6 · E: 28.5 of 28.9 · F: 30.8 of 79.6 **[MEASURED 26-Aug]** |

**It is the single point of failure for every pharmacy figure in the system, and for
Marg's own database.** Nothing else holds either.

**Why the bundled Python matters.** The system Python on PATH is the Microsoft Store
stub. Every one of our scripts must be launched with the full path to the bundled
interpreter, and may use **the standard library only** — which is why `xlsx_stdlib.py`
exists instead of `openpyxl`.

### 1.2 manojz — Dr Manoj's own PC

| | |
|---|---|
| Pipeline | `D:\Downloads\margsync\` — `MargPull\` (the code), `MargArchive\` (the archive), `medical_SendToClinic\` (a mirror of the medical PC) |
| Repo | `D:\dr-manoj-git\drmanoj-clinic-automation\` |
| Google Drive | **`H:\My Drive`** — the same Drive, a different letter from the medical PC's `F:` |
| Reach | Reads the medical PC's **D: only, read-only**. Cannot see `C:\Users\Public\MARG`, cannot see `E:`, cannot start anything there |

**Single point of failure for:** routing, sending to the server, the offsite archive copy,
and publishing to git.

> **⚠ The mirror is not the machine.** `PULL_FROM_MEDICAL.bat:103` copies with
> `robocopy /E` and **no `/PURGE`** **[CODE]**. Deletions on the medical PC are never
> reflected. On 26-Aug the mirror still held 340 files, an AutoHotkey installation and
> three tools that the machine's own listing proves are gone. **Never conclude anything
> about the medical PC from the mirror.** Ask the machine — `MEDICAL_CENSUS.bat`.

### 1.3 The VPS — `clinic-finance`

`/root/finance/`, `finance_app.py`. Receives reports and holds the books. **It can reach
neither PC.** Every server-side health check watches *arrival at the VPS*; four of the
seven ways this pipeline fails happen entirely on the two Windows machines and were
structurally invisible there until B2 (S202).

### 1.4 Google Drive — the only channel INTO the medical PC

`Clinic Data Archive\` with `MargArchive\`, `FromMedical\`, `ToMedical\`, and — new at
S203 — `MargBackups\`.

- **`FromMedical\`** — the medical PC writes out: `heartbeat.txt`/`.json` every 5 min,
  `CENSUS.txt`, `BACKUP.txt`.
- **`ToMedical\`** — the way in. **`ToMedical\_kit\` is auto-installed by the agent**;
  everything else there is for a human to double-click.
- **This is the only inbound path.** Because the Tailscale share is read-only, delivery
  to the medical PC must be a medical-side *pull*, never a manojz *push* **[S195, proven
  by probe]**.

### 1.5 Tailscale — and a correction to the record

**D347 records that Tailscale is "a read-only D:-only view and NOT load-bearing".**
**That is wrong.** `\\100.119.151.40\DDrive` is the **sole transport** for every report
from the medical PC to manojz. On 26-Aug Windows applied its default block on
unauthenticated guest access to that share and the feed went dark for **8 hours 40
minutes** while every component reported healthy. The S202 references were corrected;
**the decision record itself still says "not load-bearing" and needs correcting.**

---

## 2. THE CHAIN, STAGE BY STAGE

**Dr Manoj clicks a report in Marg → the figure appears on the clinic server.**

| # | What | Where it runs | Trigger | Proof it ran |
|---|---|---|---|---|
| 1 | Marg writes an export | MEDICAL | a human clicks | the file appears in a slot |
| 2 | `marg_watch.py` captures it | MEDICAL, child of the agent | file event, seconds | a dated copy in `_captured` |
| 3 | `medical_agent.py` **S203.3** supervises, heartbeats **and runs the offsite backup** | MEDICAL, from `Startup\MargAgent.cmd` **at logon** | 30 s loop · 300 s beat · backup hourly | `FromMedical\heartbeat.txt`, incl. the `BACKUP` block |
| 4 | `PULL_FROM_MEDICAL.bat` sweeps | manojz, Task Scheduler → `PULL_HIDDEN.vbs` | every 10 min | `_last_pull.txt` — **but see the warning below** |
| 5 | `marg_watch.route()` → `marg_router.py` | manojz, in-process **[CODE `marg_watch.py:272`]** | inside step 4 | rows in `MargArchive\index.csv` |
| 6 | `marg_gate.py send` drains `_outbox` | manojz | inside step 4 | `_outbox_state.json` |
| 7 | VPS `finance_ingest` stages it | VPS | on POST | the report appears for approval |
| 8 | **Dr Manoj alone applies it** | VPS, browser | a human | the figure enters the books |

**Current versions running, as at 26-Aug-2026 [MEASURED]:** `medical_agent.py` **S203.3** (`7b9a76f2…`) · `marg_watch.py` (`aa55cdb5…`) · `medical_census.py` **S203.6** (`a7706d60…`) · `xlsx_stdlib.py` (`bbe11a89…`). Live pins in §3.2; the Register owns VPS pins, not this document (§0.1).

**Step 1 is why the watcher exists.** Marg reuses fixed slot names — `REPORT_1.XLS`,
`REPORT_2.XLS` — so the next export **overwrites** the last. Capture must be local and
immediate; no amount of polling from manojz can win that race.

**Marg has TWO output trees, and one is invisible to manojz:**
- `D:\MARGERP\users\<id>\report\REPORT_n.XLS` — the Excel exports
- **`C:\Users\Public\MARG\<id>\all\REPORT.PDF`** — PDF exports, **on C:**, which the
  D:-only share cannot see at all. Recorded as far back as `S180_Marg_Sample_Findings`
  (15-Aug) and only acted on at S201.

The watcher therefore watches **three** roots **[MEASURED, live heartbeat 26-Aug]**:
`D:\MARGERP\users` + `D:\MARG REPORTS` + `C:\Users\Public\MARG`.
*(Two current documents still say two roots. They are wrong.)*

### 2.1 THE MANUAL STEP — where all of this actually begins

**Everything downstream starts with a person clicking in Marg.** Nothing generates the
report automatically; whether `margwin.exe` can be driven from the command line is still
an open question for the vendor (§11). So this is step zero, and it is written here
because a chain document that starts at step two is missing its trigger.

**On the MEDICAL PC: Marg → Daily Reports → Sale Reports → `BILL WISE STATEMENT`.**

| Field | Set to |
|---|---|
| Operator Name | *(blank — all operators)* |
| Stock Less | `No` |
| **Report From / To** | **the single business day being exported** — see the warning below |
| Cash/Cr/Disc. | `Both` |
| Club Cash Sale | `No` |
| Less Cr/Dr Adj. | `Yes` |
| Add Challans | `No` |
| Patient Mobile / Pres.By Mobile | *(blank — all)* |
| Report For | `2 Sale-S/R-Brk` |
| **Report Type** | **`Detail`** — the critical one |
| width | `80 Col` |
| Disc.Bill Sign | `2-Bill+Item` *(proven)* |
| Day Total | `Yes` — the `DAY TOTAL` rows are used to self-check each day |
| **With Item Deta.** | **`Yes`** |
| Single Party / Selected Group / Selected COMPNA | `N` |

Then the export screen, **`SELECT DELIMETER LINE/HEADER`** — these produced the verified
file and must not be changed: separator `Header` · line as heading `No` / `1` · data
starts at line `5` · data ends `0` · format `Formated`.

**Two checks that take one second each:**
- **`Report Type` must be `Detail`.** `Summary-1` collapses the report to three columns
  and **loses the CASH column entirely** — cash and UPI then cannot be separated (§4.4).
- **The title line must name the range you asked for.** If it reads `AS ON <date>` when
  you asked for a range, the date range was not applied.

> ### ⚠ ONE DAY AT A TIME — do not export month-to-date with item detail
> `S180_Marg_Daily_Sale_Button_Settings` (15-Aug) specifies **`Report From = 01` of the
> current month**. **Do not follow that for an item-detail export.** Month-to-date *with*
> `With Item Deta. = Yes` is the exact combination that **truncated at day 6 of 15,
> silently** — the file opened, the rows looked right, only the days were missing (V7,
> §4.4). Current practice, and the correct practice, is **one business day per export**;
> historical backfill is **one file per month**. Whether Marg has a page or line cap on
> the Excel export is still an open vendor question — if it can be lifted, this
> constraint may go away.

**Where it lands, and why the watcher exists:** the export always writes to
`D:\MARGERP\users\<user id>\report\REPORT_1.XLS` (or `REPORT_2.XLS`) — a **fixed slot
name that the next export overwrites**. That is the whole reason capture has to be local
and immediate. A PDF export instead lands at `C:\Users\Public\MARG\<id>\all\REPORT.PDF`,
on a drive manojz cannot see at all.

**After you click, you do nothing.** The watcher copies it within seconds, the 10-minute
pull collects it, and it appears for your approval on the clinic server. To confirm it
arrived, read `MARG_PICTURE.txt` (§6) — not `_last_pull.txt`.

*Owner of the full vendor-facing recipe, including the questions still open with Marg:
`S180_Marg_Daily_Sale_Button_Settings` and `Marg_Report_Requirement_Sanjeevni`. This
section is the operating summary; those two remain authoritative for the detail — and the
first is **stale on the date range**, corrected here.*

> ### ⚠ THE "ok" IN `_last_pull.txt` MEANS ALMOST NOTHING
> `PULL_FROM_MEDICAL.bat:184` writes `echo END %DATE% %TIME% -- ok` on a straight-line
> path with **no error test above it** **[CODE]**. Capture, routing, sending and the
> picture can all have failed and it still says `ok`. Worse,
> `pipeline_status.py:122` relays that word to the clinic server as pipeline liveness.
> **And the pull writes no log at all** — `PULL_HIDDEN.vbs:17` runs it hidden with
> nothing redirected, so every line of output is destroyed every ten minutes.
> **To know the feed is healthy, read `MARG_PICTURE.txt`, never `_last_pull.txt`.**

---

## 3. THE MEDICAL PC IN FULL

### 3.1 What is on it — `D:\SendToClinic`, 77 files **[MEASURED 26-Aug]**

| File | What it is |
|---|---|
| `medical_agent.py` | the supervisor: owns the watcher, heartbeats, installs kit files, **and from S203 runs the offsite backup** |
| `marg_watch.py` | the capture watcher — runs as the agent's child |
| `medical_census.py` | the on-machine audit tool (see §6) |
| `xlsx_stdlib.py` | reads `.xlsx` with the standard library only |
| `SEND_TO_CLINIC.bat` | **the manual fallback sender.** Self-contained: posts the report directly with the token; calls no Python |
| `token.txt` | 32 bytes. Never mirrored (`/XF token.txt`), never hashed, never printed |
| `pyportable\` | the bundled Python 3.11.9 |
| `_captured\` | 35 files — the capture spool |
| `Sent\` | 16 files — the old sender's archive |
| `_old\` | 3 files — a deliberate attic, **excluded from the mirror** |
| `pyportable.zip` (11.9 MB), `SCREEN REC 21 8 2026.zip` (3.4 MB) | setup leftovers, excluded from the mirror by `/XF *.zip` |

**Not on the machine, though the mirror and several documents still imply otherwise:**
`GUARD_AND_SEND.bat`, `guard_and_send.py`, `marg_report.py`, `xlrd\`,
`INSTALL_WATCHER.bat`, `START_MARG_WATCHER.bat`, AutoHotkey and its macros,
`_backup_20260822_002354\`, and the 340 `marg_watch.py.before_*` files.

> **AF-1 should be struck.** It is recorded — in seven places — against
> `GUARD_AND_SEND.bat` lines 119-123 reading a stale `last_response.txt`. **That file is
> not on the machine.** The fallback D347 protects is `SEND_TO_CLINIC.bat`, which was
> read and is self-contained. The fallback works; the fault attached to it cannot fire.

### 3.2 Live pins — the first ever taken **[MEASURED 26-Aug 13:04]**

| File | md5 |
|---|---|
| `SEND_TO_CLINIC.bat` | `e19a8a777ac22fe75a242f1eb9762185` |
| `marg_watch.py` | `aa55cdb51521c796a9167ee7d27a368f` |
| `medical_agent.py` | `7b9a76f24abc5be369186507279cfaad` (S203.3; was `69e60d77…` S201.11) |
| `medical_census.py` | `a7706d60965e45545e93a4eaa94fa892` (S203.6) |
| `xlsx_stdlib.py` | `bbe11a8953f66c27126c48e773cfbe35` |
| `Startup\MargAgent.cmd` | `edcb2f2e2ef1258d4e0d3bae9ef38460` |

**Why these did not exist before.** `verify_live_pins.py` runs on the VPS and cannot
reach either PC; the share is read-only and D:-only; the mirror never purges. **Drift on
this machine was undetectable by construction from the day it was set up.**

### 3.3 How the agent starts — and the trap in it

`Startup\MargAgent.cmd`, verbatim **[MEASURED]**:

    @echo off
    start "" /min "D:\SendToClinic\pyportable\pythonw.exe" "D:\SendToClinic\medical_agent.py"

**At logon only. There is no scheduled task for it** — Task Scheduler holds six
non-Microsoft entries, all Google and OneDrive **[MEASURED 26-Aug]**. No logon, nothing
runs: no capture, no heartbeat, no kit updates, and no backup.

> **The S195 restart recipe is dangerous and should not be used.**
> `Stop-Process -Name python,pythonw` kills `pythonw.exe medical_agent.py` — the
> supervisor itself. Because nothing schedules it, **it does not come back until the next
> logon**, and the PC looks perfectly normal meanwhile. To restart safely, use
> `ToMedical\INSTALL_AGENT.bat`, which stops, replaces, verifies and starts again.

### 3.4 Delivering changes to the medical PC

- **Automatic, no keystroke:** put the file in **`ToMedical\_kit\`**. The agent installs
  it within ~30 s, compile-checked and md5-verified, backs up the previous copy (keeps 3)
  and reports it in the heartbeat. **The allowlist is exactly three names**
  **[CODE `medical_agent.py:128-131`]**: `marg_watch.py`, `xlsx_stdlib.py`,
  `medical_census.py`. A stray file in that folder can never become code that runs.
- **The agent itself is deliberately excluded** — a process that overwrites itself while
  running is how an unattended machine bricks itself. Update it by putting
  `medical_agent.py` in **`ToMedical\`** (not `_kit`) and double-clicking
  **`ToMedical\INSTALL_AGENT.bat`** on the medical PC.
- **Nothing can *run* anything there.** The agent installs; it does not execute. Any
  one-off job needs a human double-click.

---

## 4. MARG ITSELF

### 4.1 How Marg stores data — the fact everything else depends on

**Marg partitions its FoxPro tables by financial year in the FILE EXTENSION**
**[from `_old\COPY_MARG_DATA.bat`, S195, recovered 26-Aug]**:

- `.c18` = FY **2026-27** (the current year)
- `.c17` = the year before

So `mdis.c18` is the bill header table, `dis.c18` the drug lines, `subdis.c18`, and so
on. This is why Marg's own backup files are named `*_c18_d_*`, and why a backup of "this
year" and "last year" are two different sets of files.

`D:\MARGERP\Data` — **1,075 files, 0.9 GB** **[MEASURED 26-Aug]**.

> **These are OPEN TABLES while Marg is running** (`margwin.exe` was pid 7172 during the
> audit). **A file copy taken then restores inconsistent.** No copier — robocopy, our
> agent, anything — can produce a usable backup of that folder while Marg is open. This
> is the single most important constraint in §5.

### 4.2 The three things that call themselves a backup, and what each is worth

| | What it is | Rhythm **[MEASURED 26-Aug]** | Worth |
|---|---|---|---|
| **Your manual `.mbk`** on `E:\` | Marg's own packaged company backup, ~2.3 MB | every 2–4 days, by hand. Newest **22-Aug**, 4.1 days old. 177 files, 0.4 GB total | **The only real one.** Until S203 it existed in exactly one place |
| **`D:\MARGERP\serverbackup`** | Marg's internal backup: `monday.mst`…`sunday.mst` (~11 KB, near-daily) plus a ~2.3 MB `*_c18_d_*` pair | the big pair only sporadically: 26-Aug, 25-Aug, 22-Aug, then a **12-day gap** to 10-Aug | **Not dependable, and on the same disk as the data.** Survives a mistake, not the disk |
| **`E:\auto`, `E:\MARGBCKUP\auto`** | where a scheduled Marg backup would land | **EMPTY.** `E:\MARGBCKUP` last written **09-Oct-2025** | Nothing |

> **Why the automatic backup produces nothing — settled.** It is not failing.
> **Nothing in Task Scheduler and nothing at startup runs a backup** **[MEASURED]**. It
> was never scheduled. The empty `auto` folders were never going to fill. *(The record
> said it "was configured and has never once run"; the machine says it was never there.
> 115 Marg config files were read and none mentions backup, so the setting — if it
> exists — lives inside Marg's GUI or database and is the vendor's to explain.)*

**Also true and easily missed:** the **previous financial year**
(`d1-sanjeevni-20250401-20260331`) was last backed up **17-Jul — 40 days ago** — and
there is one copy of it.

### 4.3 THE DATABASE IS ENCRYPTED — and reading it directly is RETIRED

**Marg's FoxPro tables are encrypted** — `mdis.c18` (bill header), `dis.c18` (lines),
`subdis.c18`, `saletype`, `gledger`, `support`, `pro.c18` (item master) — via Marg
`bsVault` → **Chilkat32.dll**.

**Every supported route to the data was ruled out first**, with the vendor and by
research: **the API Gateway is paid cloud only · there is no ODBC · Tally XML is
accounting only and carries NO item lines.** That is the whole reason item-level daily
data comes out through a *report export* — the long way round we have built — rather
than by reading the database.

**Reading the tables directly ("Method A") was attempted thoroughly, and it failed.**
Four independent attacks across **all 27,246 records and all seven co-encrypted `*.c18`
files**: a per-column printable/charset attack · space-pad and null-pad hypotheses with
brute single-byte fill · a cross-file CHAR-witness union for a global key (which pinned
only 54 of 256 columns) · and a DBF zero-crib with displacement-chain reconstruction.
**All four failed on the record fields.** The decisive negatives:

- **Zero** occurrences of bill numbers (`A00nnnn` / `CN00nnn`) in any of the 256 phases.
- **Zero** occurrences of `"2026"` in any phase, and no all-digit columns at all.
- Field descriptors do not decode to valid VFP types — `dbfread` reports *"Unknown field
  type"*.
- **All seven files share an identical 19-byte header prefix despite ranging from 809
  bytes to 13 MB.** Under a simple XOR of a standard DBF those prefixes would differ, as
  each carries its own date, record count and header length. **Identical prefixes falsify
  the "XOR of a standard DBF" hypothesis outright.**

There **is** a 256-byte repeating XOR *period* — autocorrelation confirms it — but the
plaintext beneath it is **not a standard DBF**. Marg applies a fixed wrapper plus a
per-record or non-XOR transform. Only byte 0 (`0x30`) and the record length (`256`) ever
appear to "verify", **and those two are consistent with coincidence or with the wrapper,
not with a real decrypt.**

> **VERDICT: remote decryption from the files alone is not tractable by known methods,
> and is RETIRED.** The only realistic route left is a **runtime debugger dump of the key
> AND the algorithm from `MARGWIN.EXE` / bsVault on the Marg PC itself** — heavy,
> uncertain reverse engineering, and not worth it: **Method B already delivers exactly
> what Method A was for.** The report export yields bill-wise sales *with item and drug
> lines*, daily. Method A's only advantage was avoiding the GUI.
>
> **Do not spend another session on the cipher.** The encrypted samples are kept on
> manojz (`…\_to_delete\margdata\*.c18`, gitignored) in case a hands-on debugger session
> is ever done.

> ### ⚠ HOW THIS SECTION WAS WRONG IN v2, AND WHY IT MATTERS
> v2 of this document said the cipher was *"genuinely breakable"* and *"parked, not
> because it failed"*, citing the `0x30` and `256` as confirmations. **That was the
> 21-Aug note, and it was superseded on 23-Aug by `S195_Marg_decrypt_partial_key.md`,
> whose own first line says so.** The successor **is in the repo and was never in project
> knowledge**, so a search of the Project alone found only the optimistic version.
> **The consequence, had it stood: §4.3's stated job is to be the standing answer to
> "why not just read the database?" — and it would have invited a wasted session.**
> This is the two-sources-of-truth failure, caught by checking the master against the
> documents it claimed to consolidate rather than by trusting the newest summary. Both
> notes are now in `deploy_kits\S203_MARG_CANON\`; the 21-Aug one is superseded and
> labelled.

### 4.4 THE MONEY RULE, THE REPORT VARIANTS, AND THE TRUNCATION THAT MUST NOT BE FORGOTTEN

**The money rule — one line, and getting it wrong misstates revenue:**

> **cash = the CASH column. UPI = net − CASH.**
> **Never** derive cash from the `D.R.` column **[S179 report analysis, verified against a
> real day: CASH column total 193,412]**.

**The report has two shapes**, and only one is usable:
- **9 columns (Detail):** `BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX |
  DR/CR | NET AMT. | CASH` — this is the one we ingest.
- **3 columns (Summary-1):** `BILL NO. | DESCRIPTION | BILL VALUE` — **no CASH column at
  all**, so it cannot separate cash from UPI. Refused.

**Two traps recorded from real files:** the description field **truncates at 33
characters** (`PRADEEP KUMAR GUPTA 77` is cut mid-ID), and a **credit note can arrive as a
text cell** rather than a number.

> ### ⚠ V7 — THE SILENT TRUNCATION
> A month-to-date export **with item detail** **stopped at day 6 of 15 — silently.** The
> file opened, the rows looked right, and only the days were missing. Nothing errored.
> **This is why every historical item-wise export is taken ONE FILE PER MONTH**, never
> "till date", and why `signatures.json` carries an `end_marker` per report type: the
> marker is the only thing that can tell a complete export from a truncated one.
> Whether Marg has a page or line cap on the Excel export is **still an open question for
> the vendor** — if it can be lifted, the historical backfill gets much simpler.

### 4.5 WHAT THE SERVER DOES WITH A REPORT — the ingestion half

A report reaching the VPS does **not** move money. That is **D313**, and it is the rule
that keeps a half-attributed day from becoming a half-counted day:

> **The money is the maker's typed entry. `sale_item` is attribution only.**
> `day_line` — the money — is untouchable by ingest.

- **Returns are a magnitude with their direction in the row's type** (D314). Netting is
  done in SQL, not by sign-juggling on the way in:
  `marg_net_sql(a) = SUM(CASE WHEN a.service LIKE '%return%' THEN -a.amount_p ELSE a.amount_p END)`
  *Verified live on one day: naive `SUM` = 23,879.00, `marg_net_sql` = 20,599.00.*
- **"This month vs Marg" on the health page** compares `v_cash_ledger.revenue_p` (the
  whole day, typed) against `marg_net_sql(sale_item)` (attributed lines only). **They
  will never agree on any day that has one parked line** — that is by design, not a fault.
- **`ingest.min_confidence` is closed by MEASUREMENT (D348), not by owner judgement.**
  Across 192 bills over seven days every Marg bill scores either 0.95+ or 0.50 and
  nothing in between: it is a has-clinic-ID switch imported from an OCR path that has no
  OCR here. *(`MARG_INGESTION_REFERENCE_v1` §9 item 5 still calls it "an owner decision".
  It is wrong; D348 was minted hours after it was written.)*
- **The Docterz cross-match key is `bill_date + patient_name + phone_last4`**, the phone
  stored as **last 4 digits only** (F-86). `split_clinic_id()` scores one text field and
  the phone never enters it. **A re-apply wipes that day's parked list** — which is why
  the 12-June report was accepted and deliberately NOT applied.


---

## 5. BACKUP AND DISASTER RECOVERY

> **This section did not exist anywhere before today.** Four documents describe keeping
> *reports* in triplicate. Not one sentence covered the 0.9 GB of pharmacy database they
> are drawn from. That was the largest hole in the record.

### 5.1 What is protected now — S203

`medical_agent.py` **S203.3** copies closed backup files from `E:\` — and the newest few
from `serverbackup` — into **`F:\My Drive\Clinic Data Archive\MargBackups\`**, whence
Drive carries them off the premises. Bounded to 64 MB a pass so it can never delay
watcher supervision; hourly, or every two minutes while a backlog remains. **Never
deletes, never overwrites a same-size file, copies via a `.part` name and renames, so a
half-copy can never pass as whole.**

Every heartbeat now carries the backup's age, and past 3 days says so plainly.

**Proven on first run [MEASURED 26-Aug 13:40]:** `offsite: 38 file(s), 0.07 GB … 145
file(s) still to copy`. The pharmacy backups left the machine that holds them for the
first time.

**It deliberately does NOT copy `D:\MARGERP\Data`** — §4.1. A backup that cannot be
restored is not a backup, so it is not taken.

### 5.2 What is still missing

1. **The `.mbk` is still made by hand.** The one question that would fix it: *can
   `margwin.exe` take a backup, or export a report, from the command line?* Unanswered —
   ask the vendor.
2. **No restore has ever been tested.** Scheduled with the vendor engineer.
   **The restore must go into a NEW or TEST company, never the live one.** A restore over
   the live company with a 4-day-old backup destroys four days of billing and looks like
   success while doing it.
3. **The backup age reaches the owner, not yet the clinic server.** `pipeline_status.py`
   already reads the heartbeat; carrying the backup state to the VPS is a small change,
   and pending.

### 5.3 If the medical PC dies tomorrow

What you would need, and where it is:

| Need | Where |
|---|---|
| The pharmacy database | newest `.mbk` in `MargBackups` on Drive — **and a restore procedure nobody has yet performed** |
| Marg itself | vendor reinstall; licence `LIC-14116710` (see `Marg_Report_Requirement_Sanjeevni`) |
| Our software | `deploy_kits/` in the repo — **except the five files that live nowhere else, see §8** |
| The token | rotate it; do not attempt to recover it |
| Every report ever filed | `MargArchive` on manojz **and** its Drive copy |

---

## 6. HOW TO KNOW IT IS WORKING

### The 60-second check — three files, no login

1. **`D:\Downloads\margsync\MARG_PICTURE.txt`** (manojz) — the real answer. Business days
   covered, days with no export, exports not on the server.
2. **`H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt`** (manojz, from Drive) —
   is the watcher alive, what was captured today, **and now the backup's age**.
3. `D:\Downloads\margsync\MargPull\_last_pull.txt` — **only** tells you the batch file
   reached its last line. See the warning in §2.

### The deep audit — on the medical PC

Double-click **`F:\My Drive\Clinic Data Archive\ToMedical\MEDICAL_CENSUS.bat`**.

Read-only. Writes `FromMedical\CENSUS.txt` and `FromMedical\BACKUP.txt`, which sync back
by themselves. It reports: every report-shaped file on both drives and whether each
reached the archive · the drives and the backup stick · every backup folder and its age ·
the Marg data size · scheduled tasks, unfiltered · Marg's own config · **an md5 for every
live file on the machine** · whether Marg is running · the power history from the Windows
event log · and `D:\SendToClinic` as it really is.

**It is the only tool that sees the machine rather than a copy of it.**

---

## 7. FAILURE MODES, BY SYMPTOM

| Symptom | Cause | Detected by |
|---|---|---|
| A report never arrives | the share blocked by Windows guest-access policy (26-Aug, 8h40m) | **nothing at the time** — now B2's pull-liveness |
| Reports stop appearing on the server | the watcher died | the heartbeat, and the agent restarts it within a minute (F-180) |
| Everything green, nothing arriving | **the outbox had no consumer** (F-179; 11 reports stranded 3 days) | now `_outbox_state.json` and B2's drain count |
| A report is refused for ever, silently | `marg_router.py:349-354` — an unreadable `.xls` returns **before** archiving: never copied to `_REFUSED`, **never written to `index.csv`**, retried and re-refused every cycle | **nothing** |
| The pull says `ok` but nothing happened | §2's warning | **nothing** |
| A PDF export is ignored | it lands on `C:`, outside the D: share | the watcher's third root (since S201) |
| No backup for days | **nothing, until S203** | the heartbeat's `BACKUP` line |
| The agent is gone after a restart | it starts at logon only; no logon, nothing runs | the heartbeat's absence — if anyone looks |

---

## 8. THE BLIND SPOTS

1. **Five live tools exist nowhere but the medical PC and manojz** — `medical_agent.py`,
   `xlsx_stdlib.py`, `marg_rescan.py`, `medical_inventory.py`, `medical_census.py`.
   Not in the repo, not in the cold kit. If manojz died today they are gone.
2. **`marg_report.py` — the parser `marg_router.py:221-224` uses for `deep_verify` on
   every sale report — is on manojz at `28b47d44…`, two builds behind the server**, and
   nothing pins it. The medical PC's copy is gone entirely.
3. **The pull produces no log.** Ten minutes of diagnostics destroyed, every ten minutes.
4. **`_spool` and `_outbox` have no offsite copy**, and emptying `_spool` re-imports
   everything.
5. **The token lives in FIVE distinct stores, not the three on record.** The systemd unit
   on the VPS · the medical PC's `D:\SendToClinic\token.txt` · manojz
   `D:\Downloads\margsync\SendToClinic\token.txt` · the loose note
   `D:\Downloads\MARG_TOKEN_S187.txt` · and
   `D:\Downloads\margsync\_to_delete\S201_20260825\loose\finance marg token.txt`.
   **Rotation — the oldest open item in the project — must reach all five**, and a
   rotation that reaches three leaves the other two live.
6. **No push-rejection counter, no offsite verification**, and no deep verification for
   purchase or stock reports.

---

## 9. CORRECTIONS TO THE EXISTING RECORD

Struck rather than deleted, per F-23. Full detail in `S203_MARG_DOC_VERIFICATION.md`
(82 claims tested: 42 verified, **17 wrong**, 12 stale, 11 unverifiable).

| # | The record says | The truth |
|---|---|---|
| 1 | The upload sends filename `"REPORT_1.XLS"` (both references) | `marg_gate.py:506` sends the **archive name**; `:742` is a selftest asserting `REPORT_1.XLS` is *not* sent. Writing a client from the contract would send the wrong thing |
| 2 | `marg_report.py` "PC copy `28b47d44` (S180)" | **Absent from the medical PC.** The `28b47d44` copy runs on **manojz** and is used on every sale report |
| 3 | The watcher watches two roots | **Three** — the third is on `C:`, invisible to the D:-only share, so `MEDICAL_RECENT.bat` cannot list "EVERY file" as claimed |
| 4 | Restart with `Stop-Process -Name python,pythonw` | That **kills the supervisor**, which only returns at logon |
| 5 | §7: install a signature with `--learn` | `marg_router.py:432-437` emits no `end_marker` and no `dating` — you get a signature with **no truncation check**, the exact failure the marker exists to prevent |
| 6 | Tailscale is "NOT load-bearing" (D347) | It is the **sole transport**; 26-Aug proved it |
| 7 | `xlsx_stdlib.py` is a §9 gap | It is installed (`bbe11a89`, in the heartbeat) |
| 8 | The C: tree was discovered 25-Aug | Recorded in `S180_Marg_Sample_Findings` on **15-Aug** — ten days earlier, in the one store nothing indexes |
| 9 | `ingest.min_confidence` is "an owner decision" | Retired by **D348** — closed by measurement |
| 10 | AF-1 armed on `GUARD_AND_SEND.bat` | That file is not on the machine (§3.1) |
| 11 | The server dedupes by content (`marg_gate.py:31-32`) vs both references saying it does not | **Unresolved.** Being wrong here stages duplicates. Needs a VPS-side check |
| 12 | The chain diagram's step order | The three robocopies run **before** rescan/send, so a report sent this cycle is offsited only next cycle |

**Also, and live right now:** the copy of `MARG_PIPELINE_MAINTENANCE_FLOW_v1.md` sitting
at `D:\Downloads\margsync\` — the one you would actually open — is `f02cd8bd…`, the
**S201** version. The canonical current is `c2b5251f…`, corrected at S202 to carry the
guest-access fault by symptom. **The operational copy does not contain the fix for the
outage that produced it.** F-134's shape: a derived copy not rebuilt with its source.

---

## 10. WHERE THE DOCUMENTS ARE

**69 documents** mention Marg or the medical PC. **8 are individually pinned** in the
manifest; **17** are covered only by a wildcard row with no md5, so Phase 0 cannot verify
them; **5 are manifest-named but absent from the repo** (F-107 open); **39 are orphans**
with no row of any kind; and **30 existed in exactly one store** — project knowledge — with
no repo and no cold-kit copy. **That is no longer true:** at this session **52 Marg and
medical documents were copied into `deploy_kits\S203_MARG_CANON\` and hash-verified
52/52** (`SUMS.md5` = `4642b0227c49c52957637e65e3eb94c9`). They now exist in two stores.
**The folder is not yet manifest-pinned, so Phase 0 does not verify it — pin it at the
close, before anything is retired, or this repeats F-184.**
Full inventory: `S203_MARG_DOC_INVENTORY.md`; retirement decisions:
`S203_MARG_RETIREMENT_LIST.md`.

**Current and authoritative:** this document · `MARG_PIPELINE_REFERENCE_v1` ·
`MARG_PIPELINE_MAINTENANCE_FLOW_v1` · `MARG_INGESTION_REFERENCE_v1` ·
`S195_Medical_Watcher_LIVE_Reference` · `S202_..._D350_CONTRACT` ·
`S203_MEDICAL_PC_PINS` · `S203_MARG_CODE_TRUTH_MAP` · `S203_MARG_MEDICAL_SYSTEM_MAP`.

**Must be preserved, and are at risk** (unique content, single store): `S180_Marg_Folder_Recon`
(the whole data-layer analysis) · `S180_Marg_Daily_Sale_Button_Settings` and
`Marg_Report_Requirement_Sanjeevni` (**the only recipe for regenerating the feed**, and
the licence number) · `S180_Marg_Sample_Findings` (the C: tree, the column variants, the
text-cell credit-note trap) · `AUDIT_RUN_2026-08-24_slice1` (**the only place AF-3's scan
command exists**, which two backlogs order run before the August close) ·
`S201_Part1_xlsx_Dependency_Removed` (the only proof `xlsx_stdlib.py` is correct) ·
`S201_Parts2_3_4_Record` (the per-type `end_marker` derivations).

**On manojz only, outside both the repo and the KB:**
`D:\Downloads\Marg_Report_Requirement_Sanjeevni.md` · `D:\Downloads\S180_Marg_Action_Register.md` ·
`D:\Downloads\Marg_Sample_Exports_Needed.pdf` · `D:\Downloads\Marg_Watcher_medical\` (the
S195 kit) · `D:\Downloads\MARG REPORTS CLAUDE\` (real May–Aug exports) ·
`D:\Downloads\Finance-Accounts\Reconciliation\CARRYOVER_Pharmacy_Lab_Reconciliation_2026-06-19.md`.

---

## 11. OPEN ITEMS

| | Item | Owner |
|---|---|---|
| 1 | **Token rotation** — the oldest and highest-severity item, and it has **five** copies to reach, not three | Dr Manoj |
| 2 | **The restore test**, into a TEST company | vendor engineer, watched |
| 3 | **Can `margwin.exe` back up or export from the command line?** | ask the vendor |
| 4 | Back up the **previous financial year** — 40 days stale, one copy | Dr Manoj |
| 5 | `marg_router.py:349-354` — the silently vanishing refused file | build |
| 6 | Carry the backup age to the clinic server | build, needs the owner's OK |
| 7 | Refresh the stale runbook copy at `D:\Downloads\margsync\` | build |
| 8 | Correct D347's "not load-bearing"; strike AF-1 | at the close |
| 9 | File the five orphan live tools into the repo | build |
| 10 | Resolve the dedupe contradiction (§9 #11) against the VPS | build |
| 11 | **Is there a page or line cap on Marg's Excel export?** — the cause of V7's silent truncation | ask the vendor |
| 12 | Decryption of the `.c18` tables — **RETIRED** on a thorough negative (§4.3). Do not reopen without a hands-on debugger session on the Marg PC | closed |
| 13 | Pin `deploy_kits\S203_MARG_CANON\` in the manifest **before** retiring anything | at the close |

---

*MARG & THE MEDICAL PC — MASTER REFERENCE v4 · Session 203 · 26-Aug-2026.
v2 added §4.3, §4.4 and §4.5 — three subjects v1 lost. **v3 corrects §4.3, which v2 got
wrong** by asserting a 21-Aug note that had been superseded on 23-Aug, and adds §0.1, the
precedence rule that decides which document wins when two disagree. **v4 adds §2.1 — the
manual Marg export that everything downstream begins with**, which no document carried as
part of the flow, and corrects the recipe's month-to-date date range to one day. Built from measurement, not from the record. Where it and an older document disagree,
this one was checked against the machine and the older one was not.*
