# REINSTALL KIT — **the MEDICAL PC** (the capture machine)

**D350 §4 · Session 205 · 27-Aug-2026.** One kit per machine. This one rebuilds the
**medical PC**, where Marg ERP runs and where every pharmacy report is born.

> **This is the machine that matters most.** Marg writes each report into a **FIXED slot
> name** that it **overwrites on the next export** — `D:\MARGERP\users\<uid>\report\REPORT_n.XLS`.
> If nothing captures a report within seconds of it being written, that report is gone and
> the only way back is to run it again in Marg. Capture cannot be done from manojz; it has
> to happen here.
>
> **It has NOT been rehearsed.** Say when you want to, and we will — on a spare machine or
> into a NEW/TEST Marg company, **never the live one**.

---

## 0 · WHAT THIS MACHINE DOES

`medical_agent.py` starts at **logon** and never stops. It supervises a child process,
`marg_watch.py`, which watches three folders and copies any `.xls`/`.xlsx`/`.pdf` the
instant it appears into `D:\SendToClinic\_captured`, renamed by content hash. Every five
minutes the agent writes a heartbeat to Google Drive. Every hour it copies new Marg
backup files to an offsite Drive folder. manojz then reads `D:` over Tailscale and takes
everything from there.

**Nothing on this machine sends money anywhere.** The sale report it produces is *staged*
on the clinic server and only enters the books when the checker presses Apply.

---

## 1 · INSTALL ORDER — and it matters

| # | install | why here |
|---|---|---|
| 1 | **Windows account, WITH A PASSWORD** | see §4 — an account with no password cannot serve the share |
| 2 | **Marg ERP** and its data at `D:\MARGERP` | everything else watches it |
| 3 | **Share `D:` as `DDrive`**, read access for the manojz account | the transport |
| 4 | **Tailscale**, signed in, this machine visible as `medical` | the transport |
| 5 | **Google Drive for Desktop**, clinic account, mounted at `F:` | heartbeat out, kit in, backups offsite |
| 6 | **Portable Python** at `D:\SendToClinic\pyportable\` | the agent hard-fails without it |
| 7 | **The files in this kit** (§3) | the tooling |
| 8 | **`token.txt`** (§4) | the scoped, stage-only token |
| 9 | **The Startup entry** (§5) | last |
| 10 | **The proof checks** (§7) | a rebuild is verified, not hoped |

---

## 2 · PYTHON — a hard dependency, not a fallback

```
D:\SendToClinic\pyportable\python.exe        (currently python 3.11.9)
```

`medical_agent.py` **exits with `FATAL: bundled python missing`** if this is absent. There
is no fall-back to a system Python here, deliberately: this machine must not depend on
anything a Windows update can move.

**Standard library only.** No `pip install` is required or wanted. `xlsx_stdlib.py` reads
`.xlsx` with nothing but the standard library — a rebuild that needs the internet is a
rebuild that fails when the internet is what broke.

> **A known gap, recorded rather than hidden:** this machine's Python has **no
> spreadsheet reader for `.xls`**, so the deep verification that runs on manojz cannot run
> here. Capture is byte-faithful; it is not verified until it reaches manojz.

---

## 3 · WHICH FILES GO WHERE

```
D:\SendToClinic\
├── pyportable\python.exe      the interpreter (§2)
├── medical_agent.py           the supervisor. Starts at LOGON.
├── marg_watch.py              the watcher. A CHILD of the agent.
├── medical_census.py          the monthly proof that nothing was missed
├── xlsx_stdlib.py             .xlsx reader, standard library only
├── SEND_TO_CLINIC.bat         the MANUAL send path -- see §8, it is not innocent
├── token.txt                  the scoped token (§4). NEVER mirrored to manojz.
├── _captured\                 the watcher's spool -- renamed by content hash
├── heartbeat.txt              written every 5 minutes
├── agent.log                  self-truncating at 512 KB
├── _watcher.pid  backup_state.json     state, recreated by themselves
└── Startup\MargAgent.cmd      -> the shell:startup entry (§5)
```

**The three watched folders — all three, or reports are lost silently:**

```
D:\MARGERP\users          Marg's own report slots. FIXED NAMES, OVERWRITTEN.
D:\MARG REPORTS           where Dr Manoj saves reports by hand.
C:\Users\Public\MARG      Marg's SECOND output tree. PDF exports land here.
```

> `C:\Users\Public\MARG` is **on C:**, and the Tailscale share is `DDrive` only — so a PDF
> exported there is invisible to manojz no matter how hard it pulls. The watcher runs on
> this machine and can read `C:` perfectly well; before S201.7 it simply was never told to
> look. **A rebuild that watches only the two `D:` folders will lose every PDF export and
> nothing will say so.**

---

## 4 · CREDENTIALS — **no value is in this kit, or in any file I write**

| what | where it lives | how to restore it |
|---|---|---|
| **The Windows account** | this machine | **It must HAVE a password.** Windows refuses network logins for passwordless accounts, so a passwordless account cannot serve `DDrive` to manojz. The live machine uses `MEDICAL\SET` for exactly this reason; `MEDICAL\user` has no password and cannot be used. |
| **The `DDrive` share** | Windows sharing | share `D:` as `DDrive`, **read** for the manojz account. manojz must never be able to write here. |
| **`FINANCE_MARG_TOKEN`** | `D:\SendToClinic\token.txt`, plain text **by design** | ask me to regenerate it on the VPS. It is **scoped and stage-only**: it opens the push route and nothing else, and it can never apply anything to the books. It is deliberately **excluded from the manojz mirror** (`/XF token.txt`) — a secret stays on one machine. |
| **Tailscale** | the Tailscale app | sign in; this machine should show as `medical`, ideally `direct` |
| **Google Drive** | Drive for Desktop | clinic account, mounted at **`F:`** on this machine (manojz uses `H:` — different letters, same account; the agent scans A–Z rather than trusting either) |

> **The token lives in FIVE places, not three.** The VPS service unit · this machine ·
> the manojz cache · `D:\Downloads\MARG_TOKEN_S187.txt` on manojz · and a loose file
> under `margsync\_to_delete\`. **A rotation that reaches three leaves two live.**
> (F-202. Rotation is parked at your instruction.)

---

## 5 · HOW IT STARTS — **at LOGON, and that is load-bearing**

```
shell:startup  ->  MargAgent.cmd  ->  pyportable\python.exe medical_agent.py
```

**Nothing on this machine runs until somebody logs in.** No capture, no heartbeat, no
backup. A machine left sitting at the login screen after a reboot looks, from every other
angle, exactly like a machine that is working — and the heartbeat going stale is the only
thing that says otherwise.

| timer | value |
|---|---|
| watcher liveness check | every **30 s** — a dead watcher is restarted in the same cycle |
| heartbeat | every **5 min**, and immediately after any restart or kit install |
| offsite backup pass | every **60 min**; every **2 min** while a backlog remains |

**The agent updates its tools, but never itself.** `marg_watch.py`, `xlsx_stdlib.py` and
`medical_census.py` are picked up automatically from
`F:\My Drive\Clinic Data Archive\ToMedical\_kit\` — allow-listed by name, refused unless
they compile, backed up by source-md5, installed, then **re-hashed and verified**.
`medical_agent.py` is deliberately **not** in that allow-list: a process that overwrites
itself while running is how an unattended machine bricks itself. It is updated by hand,
by double-clicking `F:\My Drive\Clinic Data Archive\ToMedical\INSTALL_AGENT.bat`.

---

## 6 · THE BACKUP LEG (S203)

| | |
|---|---|
| **Marg's own backup** | you take it in Marg. It lands on the stick at **`E:\`**. |
| **`D:\MARGERP\serverbackup`** | Marg writes here itself — **but it is on `D:`, the same disk as the data. It is not a disaster copy** and the heartbeat says so in those words. |
| **Offsite** | the agent copies new backup files to `F:\My Drive\Clinic Data Archive\MargBackups`, bounded to 64 MB per pass so it never starves the watcher |
| **The alarm** | a newest-backup older than **3 days** is called out loudly in the heartbeat |

**The automatic Marg backup was never scheduled** — that was F-201, and it was found by
measuring rather than by reading the record, which said "configured and never run."
**A rebuild must schedule it, not assume it.** Marg holds `D:\MARGERP\Data` open, which is
why this is still an open question with Marg support.

---

## 7 · THE CHECKS THAT PROVE IT WORKED — **run all six**

```
1.  D:\SendToClinic\pyportable\python.exe -c "import sys; print(sys.version)"
        -> 3.11.x. If this fails the agent will not start at all.

2.  Log out and log back in.
    type D:\SendToClinic\heartbeat.txt
        -> written within the last 5 minutes
        -> "WATCHER : ALIVE, pid ..."
        -> "watching:" names ALL THREE folders, including C:\Users\Public\MARG
        -> "AGENT   : up to date"
        -> "IGNORED : 0"

3.  Export any report in Marg. Within seconds:
    dir D:\SendToClinic\_captured
        -> a new file, named by content hash. If not, the watcher is not
           seeing that folder.

4.  On MANOJZ:  dir \\<medical address>\DDrive\MARGERP\users
        -> a listing. This proves the share half.

5.  On MANOJZ:  D:\Downloads\margsync\MargPull\PULL_FROM_MEDICAL.bat
        -> the report you exported in step 3 appears in MargArchive.

6.  type D:\Downloads\margsync\MARG_PICTURE.txt   (on manojz)
        -> that business day now reads yes / yes.
```

**And one that is not a command:** confirm the clinic server's health page shows
*Medical PC capture — watcher alive*. Until that is true the rebuild is not finished.

---

## 8 · **A LIVE FAULT ON THIS MACHINE — AF-1 / F-206. READ BEFORE USING `SEND_TO_CLINIC.bat`.**

`SEND_TO_CLINIC.bat` is the manual send path and it stays as the fallback (D347). **It is
also armed with a fault that has never been fixed**, and until now the cure was written
nowhere a person standing at this machine could find it:

- `%RESP%` **is not cleared before `curl` runs**, so a failed request leaves the previous
  run's response in place;
- the `ACCEPTED-FOR-REVIEW` check **never consults `%HTTP%`** — it reads the response text
  and nothing else;
- so a request that failed can be read as accepted, **and that report is then blacklisted
  client-side FOR EVER.**

**Until it is fixed, if you ever run it by hand:**

1. **Do not trust the "ACCEPTED" line.** Check on the clinic server instead:
   `/finance/approvals` should show that day's export.
2. **If it is not there, the send did not happen** however the batch read. Tell me the
   report and the date and I will clear the blacklist entry.
3. **Prefer the automatic path.** manojz sends every verified report by itself every ten
   minutes; `D:\Downloads\margsync\_UPLOAD_NOW\` is empty when there is nothing to do by
   hand — and it has been empty. This batch is for when manojz is unavailable.

*The fix is queued. This section exists because a high-severity fault whose cure lives
only in a session transcript is not documented at all.*

---

## 9 · WHAT THIS KIT DELIBERATELY DOES NOT CONTAIN

- **Any token, password or key.** Not one.
- **Marg itself, or `D:\MARGERP\Data`.** That is the vendor's software and the pharmacy's
  database; it comes back from a Marg backup, restored **into a NEW or TEST company,
  never the live one**, with the vendor engineer, using `MARG_VENDOR_VISIT_CHECKLIST.md`.
- **`pyportable\`** — an interpreter is not a document. Any Python 3.11 embeddable build
  works; verify with check 1.
- **Patient data.**

---

*REINSTALL_MEDICAL · D350 §4 · S205 · bytes in `medical\`, hashes in `SUMS.md5`
(5 files, each verified against the live mirror: 0 drift). NOT YET REHEARSED.*
