# MARG & THE MEDICAL PC — CURRENT STATE

**Sanjeevni Medicos · Advanced Orthopaedic Surgery Centre, Bareilly**
**True as at 26 August 2026.** Every figure below was measured on the machines on that
date unless marked otherwise.

> **This is the only Marg document you need to read.**
> Why it is the way it is → `MARG_MEDICAL_HISTORY.md` (opened only to answer that).
> At the counter, in a hurry → the printed card beside the medical PC.
>
> **When this file and any other document disagree, and the other is older: this wins.
> When this file and the machine disagree: the machine wins.**

---

## 1. THE MACHINES

**MEDICAL PC** — `MEDICAL`, Windows 10 Pro 19045, user `SET`. Marg lives here, and so does
every pharmacy figure before it goes anywhere.
- Marg: `D:\MARGERP\` · our software: `D:\SendToClinic\` · Google Drive: **`F:\My Drive`**
- Bundled Python `D:\SendToClinic\pyportable\python.exe` 3.11.9 — **standard library only**,
  no xlrd, no openpyxl. Never rely on the system Python; it is a Store stub.
- Reached from manojz over Tailscale as `\\100.119.151.40\DDrive` — **read-only, D: drive
  only.** Nothing can write to it and nothing can start a program on it.
- Disks: C: 32.4 GB free of 79.6 · D: 30.5 of 39.1 · **E: (backup stick) 28.5 of 28.9** ·
  F: 30.8 of 79.6

**manojz** — Dr Manoj's PC. The pipeline (`D:\Downloads\margsync\`) and the repo
(`D:\dr-manoj-git\`). Google Drive is **`H:\My Drive`** here — same Drive, different letter.
Cannot see the medical PC's `C:` or `E:` at all.

**The clinic server (VPS)** — holds the books. **It can reach neither PC.** Everything it
knows about them arrives in a report or a heartbeat.

**Google Drive** — the only way *in* to the medical PC. `Clinic Data Archive\` holds
`FromMedical\` (the PC reports out), `ToMedical\` (the way in; `_kit\` auto-installs),
`MargArchive\` and `MargBackups\`.

> **Tailscale is load-bearing.** It is the sole transport for every report. On 26-Aug
> Windows blocked unauthenticated guest access to that share and the feed was dark for
> **8 hours 40 minutes** while every component reported healthy.

---

## 2. FROM YOUR CLICK TO THE BOOKS

| # | What happens | Where | When |
|---|---|---|---|
| 1 | **You generate the report in Marg** (§3) | MEDICAL | when you click |
| 2 | The watcher copies it before Marg can overwrite the slot | MEDICAL | seconds |
| 3 | The agent supervises the watcher and heartbeats out | MEDICAL | 30 s / 5 min |
| 4 | The pull sweeps the medical PC | manojz | every 10 min |
| 5 | The router classifies and archives it | manojz | inside step 4 |
| 6 | The gate sends it to the clinic server | manojz | inside step 4 |
| 7 | It is staged for approval | VPS | on arrival |
| 8 | **You alone apply it** | VPS, browser | when you approve |

**Running now:** `medical_agent.py` **S203.3** `7b9a76f2…` · `marg_watch.py` `aa55cdb5…` ·
`medical_census.py` **S203.6** `a7706d60…` · `xlsx_stdlib.py` `bbe11a89…`

**Marg writes to two places**, and manojz can only see one: exports go to
`D:\MARGERP\users\<id>\report\REPORT_n.XLS`, but a **PDF** export goes to
`C:\Users\Public\MARG\<id>\all\REPORT.PDF` — on C:, invisible to the share. The watcher
runs on the machine and covers **three** roots: `D:\MARGERP\users`, `D:\MARG REPORTS`,
`C:\Users\Public\MARG`.

**The agent starts at logon only** (`Startup\MargAgent.cmd`). There is no scheduled task
for it. **No logon, nothing runs** — no capture, no heartbeat, no backup.

---

## 3. GENERATING THE REPORT — the step everything begins with

Nothing generates it automatically. **Marg → Daily Reports → Sale Reports → `BILL WISE
STATEMENT`.**

| Field | Set to |
|---|---|
| Operator Name · Patient Mobile · Pres.By Mobile | *(blank = all)* |
| Stock Less · Club Cash Sale · Add Challans | `No` |
| **Report From / To** | **the single business day** |
| Cash/Cr/Disc. | `Both` |
| Less Cr/Dr Adj. | `Yes` |
| Report For | `2 Sale-S/R-Brk` |
| **Report Type** | **`Detail`** |
| width | `80 Col` |
| Disc.Bill Sign | `2-Bill+Item` |
| Day Total | `Yes` |
| **With Item Deta.** | **`Yes`** |
| Single Party · Selected Group · Selected COMPNA | `N` |

**Export screen `SELECT DELIMETER LINE/HEADER`** — do not change: separator `Header` ·
line as heading `No`/`1` · data starts line `5` · ends `0` · format `Formated`.

**Two checks, one second each:**
- **`Report Type` must be `Detail`.** `Summary-1` gives three columns and loses CASH entirely.
- **The title line must name the range you asked for.** `AS ON <date>` means the range did
  not apply.

> ### ⚠ ONE DAY AT A TIME
> Month-to-date **with item detail** once truncated at **day 6 of 15, silently** — the file
> opened, the rows looked right, the days were missing. **One business day per export.**
> Historical backfill: one file per month. *(Whether Marg has a line cap on the export is
> still an open question for the vendor.)*

Then do nothing. The watcher takes it within seconds. To confirm it arrived, read
`MARG_PICTURE.txt` — **not** `_last_pull.txt` (§5).

---

## 4. THE MONEY — how to read a Marg report correctly

**Two rules, and they operate at different levels. Both matter.**

**Reading the file:** the nine columns are
`BILL NO. | DESCRIPTION | D.R. | GROSS AMT. | DISCOUNT | TAX | DR/CR | NET AMT. | CASH`.
Cash comes from the **CASH** column — **never** from `D.R.`

**Reading the business:** **Marg is authoritative for the DAY TOTAL, and only the total.**
Over 119 days Marg and Darpan's own book agreed to **0.3%** (26,54,543 vs 26,47,321; 118 of
119 days within ₹2,000). But the cash split did **not**: Marg 18,99,768 against Darpan
17,67,393 — **Marg overstates cash by ₹1,32,375.**

**The reason is not a bug.** `HOME MEDISUN` / `HOME MEDICINE` bills are booked as cash and
never collected, so Marg's CASH column is overstated by exactly the home-medicine amount on
any day carrying one.

> **So: never use Marg's CASH column as the cash figure for the books.** The money is
> **the maker's typed entry** — that is D313, and it is why a half-attributed day is never
> a half-counted day. Marg's role is attribution and the day total.

*The one day more than ₹2,000 apart in 119 is **12 June** (Marg 23,252 vs Darpan 14,765,
+8,487) — isolated, still open, and the reason that day's report was accepted but
deliberately not applied.*

**Two traps in real files:** the description field **truncates at 33 characters**, and a
credit note can arrive as a **text cell** rather than a number.

---

## 5. IS IT WORKING? — sixty seconds, no login

1. **`D:\Downloads\margsync\MARG_PICTURE.txt`** (manojz) — **the real answer.** Business
   days covered, days with no export, exports not on the server.
2. **`H:\My Drive\Clinic Data Archive\FromMedical\heartbeat.txt`** — is the watcher alive,
   what was captured today, **and how old the backup is**.
3. `_last_pull.txt` — see the warning.

> ### ⚠ "ok" IN `_last_pull.txt` MEANS ALMOST NOTHING
> It is written on a straight-line path with **no error test above it**. Capture, routing,
> sending and the picture can all have failed and it still says `ok` — and that same word
> is relayed to the clinic server as pipeline liveness. **The pull also writes no log at
> all.** Judge health from `MARG_PICTURE.txt`.

**The deep audit, on the medical PC:** double-click
`F:\My Drive\Clinic Data Archive\ToMedical\MEDICAL_CENSUS.bat`. Read-only. It reports every
report-shaped file on both drives and whether each reached the archive, the drives and the
stick, every backup folder and its age, the Marg data size, scheduled tasks unfiltered,
Marg's own config, **an md5 for every live file**, whether Marg is running, the power
history, and `D:\SendToClinic` as it really is. Results come back by themselves as
`FromMedical\CENSUS.txt` and `BACKUP.txt`.

**It is the only tool that sees the machine rather than a copy of it.** manojz's mirror is
`robocopy /E` with **no `/PURGE`** — it keeps every file ever deleted on the medical PC, so
it can never prove what is still there.

---

## 6. BACKUP AND DISASTER RECOVERY

**Marg's data:** `D:\MARGERP\Data`, 1,075 files, **0.9 GB**. Marg splits its FoxPro tables
**by financial year in the file extension** — `.c18` = FY 2026-27, `.c17` = the year before.
**They are open tables while Marg is running**, so no file copier can take a usable copy of
that folder while Marg is open.

**What protects it:**

| | Rhythm | Worth |
|---|---|---|
| **Your manual `.mbk`** on `E:\` | every 2–4 days, by hand | **the only real backup** |
| **Since S203: an automatic offsite copy** — the agent copies every backup file from `E:\` into `F:\…\MargBackups\`, and Drive carries it off site | hourly; catch-up every 2 min | **removes the single point of failure** |
| `D:\MARGERP\serverbackup` | sporadic — 26, 25, 22-Aug, then a **12-day gap** | **on the same disk as the data.** Not a disaster copy |
| `E:\auto`, `E:\MARGBCKUP\auto` | **empty since Oct 2025** | nothing — see below |

> **Why the "automatic backup" produced nothing: it was never scheduled.** Nothing in Task
> Scheduler and nothing at startup runs a backup. It was not failing; it did not exist.

**The heartbeat now states the backup's age** and says so plainly past three days.

**Still true and still a risk:** **no restore has ever been tested**, and the **previous
financial year** was last backed up **17 July**, with one copy.

**If the medical PC dies:** the newest `.mbk` from `MargBackups` on Drive · a vendor
reinstall of Marg (licence `LIC-14116710`) · our software from the repo · rotate the token,
don't recover it · every filed report from `MargArchive` and its Drive copy.

**Reading Marg's database directly is retired.** Four independent attacks over all 27,246
records and every `*.c18` file failed; the identical 19-byte header prefix across files from
809 bytes to 13 MB falsifies the simple-XOR hypothesis. The only route left is a debugger
session on the Marg PC, and it is not worth it — the report export already gives item lines.
**Do not reopen this.**

---

## 7. WHEN SOMETHING IS WRONG — by symptom

| You see | It is | Does anything catch it? |
|---|---|---|
| A report never arrives | the Tailscale share blocked, or the medical PC off | now yes — pull liveness |
| Nothing new on the server, all looks fine | the watcher died | yes — the agent restarts it within a minute |
| Everything green, nothing arriving | a queue with no consumer | yes, since S201 |
| A report is refused for ever and silently | an unreadable `.xls` returns before archiving — no `_REFUSED` copy, **no index row** | **no** |
| The pull says `ok` but nothing happened | §5's warning | **no** |
| A PDF export ignored | it lands on `C:`, outside the share | yes, since S201 |
| No backup for days | — | **yes, since S203** |
| Nothing runs after a restart | the agent starts at logon only | only the heartbeat's absence |

---

## 8. WHAT NOTHING CAN SEE

1. **Five live tools exist only on the two PCs** — `medical_agent.py`, `xlsx_stdlib.py`,
   `marg_rescan.py`, `medical_inventory.py`, `medical_census.py`. Not in the repo.
2. **`marg_report.py`**, used to verify every sale report, runs on manojz **two builds
   behind the server**, and nothing pins it.
3. **The pull produces no log.** Ten minutes of diagnostics destroyed, every ten minutes.
4. **`_spool` and `_outbox` have no offsite copy**, and emptying `_spool` re-imports
   everything.
5. **The token lives in five places**, not the three on record — the VPS unit, the medical
   PC, the manojz cache, `D:\Downloads\MARG_TOKEN_S187.txt`, and a loose file under
   `margsync\_to_delete\S201_20260825\loose\`. **A rotation that reaches three leaves two
   live.**

---

## 9. OPEN

| | Item | Whose |
|---|---|---|
| 1 | **Rotate the token** — oldest item in the project, and five places to reach | Dr Manoj |
| 2 | **Test one restore, into a NEW or TEST company — never the live one** | vendor engineer |
| 3 | Ask Marg: can `margwin.exe` back up or export from the command line? | vendor |
| 4 | Ask Marg: is there a line cap on the Excel export? *(the cause of the truncation)* | vendor |
| 5 | Back up the **previous financial year** — 40 days stale, one copy | Dr Manoj |
| 6 | **12 June, +8,487** — the one day in 119 that disagrees | open |
| 7 | The silently vanishing refused file | build |
| 8 | Carry the backup age through to the clinic server | build |
| 9 | Put the five orphan live tools in the repo | build |
| 10 | Does the server dedupe by content? The code and the references disagree | check |

---

## WHERE FACTS LIVE, WHEN YOU NEED ANOTHER DOCUMENT

**What is true now** → this file, and the live files it names.
**VPS code versions** → the KB Register. **What was decided** → the decisions index.
**What is wrong** → the Fault Register. **What happened** → `MARG_MEDICAL_HISTORY.md`.
**Your task list** → `OWNER_TODO_LIVE.md`.

*A fact repeated outside its owner must name the owner. The owner beats the copy. **The
machine beats both.***

---

*MARG & THE MEDICAL PC — CURRENT STATE · 26-Aug-2026 · replaces the master reference and
the four Marg references as the thing to read. History, provenance and every superseded
document: `MARG_MEDICAL_HISTORY.md`.*
