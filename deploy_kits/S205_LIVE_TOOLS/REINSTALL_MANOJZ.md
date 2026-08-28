# REINSTALL KIT — **manojz** (the pull machine)

**D350 §4 · Session 205 · 27-Aug-2026.** One kit per machine. This one rebuilds
**manojz**, the PC that pulls every Marg report off the medical PC, identifies it,
archives it, and sends the sale reports to the clinic server.

> **Why this exists.** Before S204 neither PC could be rebuilt from anything written
> down. The knowledge lived in session transcripts. Everything that carries Sanjeevni
> pharmacy revenue runs on two Windows PCs, and the *bytes* being backed up is not the
> same as being able to put the machine back.
>
> **It has NOT been rehearsed.** A recovery document nobody has followed is a guess.
> Say when you want to rehearse it and we will, on a spare machine or a fresh Windows
> user profile — never on the live one.

---

## 0 · WHAT THIS MACHINE DOES, IN ONE PARAGRAPH

Every ten minutes a scheduled task runs `PULL_FROM_MEDICAL.bat`. It reads the medical
PC's `D:` over a Tailscale SMB share (read-only), copies any new Marg export into a
spool, identifies each file **by its contents** against a signature registry, files it
under the business date **inside** the file, sends verified sale reports to the clinic
server, mirrors the archive to Google Drive, and refreshes `MARG_PICTURE.txt`. Then it
reports what only this machine can see to the clinic server's health page.

**Nothing on this machine holds patient identifiers, and no report is ever changed
here.** manojz reads the medical PC and never writes to it.

---

## 1 · INSTALL ORDER — and it matters

| # | install | why here |
|---|---|---|
| 1 | **Windows account** — the one the scheduled task will run as | everything below is stored per-user |
| 2 | **Python 3** (see §2) | the pull is python; nothing else works without it |
| 3 | **Tailscale**, signed into the tailnet | the pull's whole transport |
| 4 | **The stored credential** for the medical share (§4) | without it the share refuses; this is the 26-Aug fault |
| 5 | **Google Drive for Desktop**, clinic account, mounted at `H:` | offsite copy + the heartbeat |
| 6 | **The `margsync` folder tree** (§3) | the working set |
| 7 | **The files in this kit** (§3) | the tooling |
| 8 | **The scheduled task** (§5) | last: nothing should run until everything it needs is there |
| 9 | **The proof checks** (§7) | a rebuild is verified, not hoped |

---

## 2 · PYTHON — read this before assuming

`PULL_FROM_MEDICAL.bat` looks for an interpreter in this order:

```
1.  D:\Downloads\margsync\MargPull\pyportable\python.exe
2.  py          (the Windows launcher)
3.  python      (on PATH)
```

**There is NO `pyportable` folder on manojz today.** The live machine falls through to
`py` or `python` on PATH. That is an undocumented dependency and it is written down
here for the first time: *a rebuilt manojz with no system Python will fail every cycle
with `FAILED: no python`*, and that line goes to `_last_pull.txt` and `_logs\pull_early.log`.

**Requirements:** Python 3 (3.8+). **Standard library only** — no `pip install` is
needed. `xlrd` ships inside `MargPull\xlrd\`, and `xlsx_stdlib.py` reads `.xlsx` with
nothing but the standard library, on purpose: a rebuild that needs the internet is a
rebuild that fails when the internet is what broke.

---

## 3 · WHICH FILES GO WHERE

Everything lives under **`D:\Downloads\margsync\`**.

```
D:\Downloads\margsync\
├── MargPull\                     <-- the tooling. THIS KIT's manojz\ folder.
│   ├── PULL_FROM_MEDICAL.bat     the 10-minute job
│   ├── PULL_HIDDEN.vbs           what the scheduled task actually launches
│   ├── marg_watch.py             capture
│   ├── marg_router.py            identify + verify + file
│   ├── marg_rescan.py            re-judge quarantine when signatures change
│   ├── marg_gate.py              send to the clinic server + the picture
│   ├── marg_report.py            sale-report arithmetic + truncation check
│   ├── pipeline_status.py        what only this machine can see -> health page
│   ├── medical_inventory.py      monthly proof that nothing was missed
│   ├── signatures.json           THE REGISTRY. A data edit adds a report type.
│   ├── xlsx_stdlib.py            .xlsx reader, standard library only
│   ├── xlrd\                     .xls reader (vendored, not pip)
│   ├── SEND_OUTBOX.bat  MARG_STATUS.bat  RESCAN.bat  FIX_POPUP.bat
│   ├── MEDICAL_INVENTORY.bat  MEDICAL_RECENT.bat  CLEANUP_DRIVE.bat
│   └── _logs\                    created on first run
├── MargArchive\                  <-- THE RECORDS. Restore from Drive, not from git.
├── medical_SendToClinic\         read-only mirror; refills itself
├── marg_reports_mirror\          read-only mirror; refills itself
├── SendToClinic\token.txt        a CACHE of the scoped token (§4)
└── _UPLOAD_NOW\                  manages itself
```

**`MargArchive` IS NOT IN THIS KIT AND MUST NOT BE.** It is the record — every verified
report, named by the business date inside it. Restore it from the Google Drive offsite
copy at `H:\My Drive\Clinic Data Archive\MargArchive`, which is `robocopy /E`,
append-only, never pruned.

**Two folders inside it are NOT in the offsite copy, by design:** `_spool` and
`_outbox`. `_spool` is also the capture dedupe memory — **restoring an empty `_spool`
re-imports every report from the medical PC**. That is not data loss, but it is a
surprise, and it is written here so it is not a surprise twice.

---

## 4 · CREDENTIALS — **the values are never in this kit, and never in any file I write**

| what | where it lives | how to restore it |
|---|---|---|
| **The medical share credential** | Windows Credential Manager, **per user** | `cmdkey /add:<medical address> /user:MEDICAL\SET /pass` — it prompts. Use `MEDICAL\SET` because it **has** a password; `MEDICAL\user` has none and Windows refuses passwordless network logins. |
| **`FINANCE_MARG_TOKEN`** | `D:\Downloads\margsync\SendToClinic\token.txt` — **a cache, not the master** | Do nothing. `marg_gate.py` reads the live token off the medical share at send time and refreshes this copy by itself. **Never hand-copy it**: a hand-copy went stale and answered 401 for five days. |
| **Tailscale** | the Tailscale app's own store | sign in as Dr Manoj on the tailnet |
| **Google Drive** | Drive for Desktop | sign in as the clinic account; it must mount at `H:` |

> **CREDENTIALS ARE STORED PER WINDOWS USER.** If a manual `dir \\<medical>\DDrive`
> succeeds and the scheduled pull still fails, the task is running as a different
> account from the one that holds the credential. That failure is silent, permanent, and
> looks exactly like a dead machine. Check with:
> `schtasks /query /tn "Marg pull from medical" /fo list /v | findstr /i "Run As User"`
>
> **From S205 the clinic server is told this directly** — whether a credential exists at
> all, and which account the pull ran as. Look at the health page before walking to
> either machine.

---

## 5 · THE SCHEDULED TASK

| | |
|---|---|
| **Name** | `Marg pull from medical` |
| **Runs** | every **10 minutes**, indefinitely |
| **Action** | `wscript.exe "D:\Downloads\margsync\MargPull\PULL_HIDDEN.vbs"` |
| **Run as** | the account holding the medical-share credential (§4) |
| **Logged on or not** | works either way — UNC needs no mapped drive — **but only if that account's stored credential is available to it** |

**A live detail worth knowing before you rebuild.** `_task_repoint_tried.txt` on the
running machine records that the task's run-as account is **`Dr Manoj Agarwal` with an
EMPTY password**, and Windows warned at the time: *"When the run-as password is empty,
the scheduled task may not run because of the security policy."* It works today. On a
rebuilt machine with a stricter policy it may not, and the symptom will be a task that
simply never fires. **If nothing runs after a rebuild, look here first.**

`PULL_HIDDEN.vbs` is what the task launches, not the `.bat`: the batch hands off to it
so no console window appears, and the vbs redirects the console output to
`_logs\pull_console_YYYY-MM.log`. **If the task is ever repointed back at the `.bat`, a
window pops up every ten minutes** — `FIX_POPUP.bat` puts it back.

---

## 6 · THE OTHER SOFTWARE

| | version / detail |
|---|---|
| **Tailscale** | `C:\Program Files\Tailscale\tailscale.exe`. The medical PC must appear in `tailscale status` as `active`. **It is LOAD-BEARING** — D347 called it "not load-bearing" and that is wrong; the entire pull leg runs over this share and when it closed the feed stopped dead for 8h40m. |
| **Google Drive for Desktop** | clinic account (`drmka.ortho`), mounted at **`H:`**. If Drive is absent the pull still works — the offsite step is skipped silently — but there is then no third copy. |
| **Windows** | nothing special. Do **NOT** re-enable insecure guest access to make the share work; use the credential in §4. |

---

## 7 · THE CHECKS THAT PROVE IT WORKED — **run all six**

A rebuild is verified, not hoped. In order:

```
1.  python -c "import sys; print(sys.version)"
        -> Python 3.x. If this fails, nothing below will work.

2.  dir \\<medical address>\DDrive\MARGERP\users
        -> a listing. "security policies block unauthenticated guest access"
           means the credential in §4 is missing.

3.  cd /d D:\Downloads\margsync\MargPull
    python pipeline_status.py --selftest
        -> PIPELINE_STATUS SELFTEST PASSED -- 45 checks OK
           (this said "- 42 checks OK". Measured 28-Aug-2026 against the
            captured pipeline_status.py: FORTY-FIVE, and a DOUBLE dash.
            Do not match on the number -- it grows every time a check is
            added, and a proof that goes red on an improvement gets waved
            through. Match on "SELFTEST PASSED" and read the count.)

4.  python pipeline_status.py --dry-run
        -> prints JSON and POSTS NOTHING. Read the "link" section: verdict
           should be "ok". Read "credential": exists should be true.

5.  D:\Downloads\margsync\MargPull\PULL_FROM_MEDICAL.bat
        -> runs to the end and writes
           D:\Downloads\margsync\MargPull\_last_pull.txt with "-- ok".
           The word "ok" is EARNED from every step's exit code (S203_R2);
           a PROBLEM line names which step failed.

6.  type D:\Downloads\margsync\MARG_PICTURE.txt
        -> "days with NO export : 0" and "exports NOT on server : 0"
```

**And one that is not a command:** wait twenty minutes and confirm the clinic server's
health page shows *Pipeline heartbeat — manojz reported N minutes ago*. Until that is
true, the rebuild is not finished, however green the six checks above are.

---

## 8 · WHAT THIS KIT DELIBERATELY DOES NOT CONTAIN

- **Any token, password or key.** Not one. They are the owner's and they never enter a
  document or a session.
- **`MargArchive`** — the records. Restored from Drive (§3).
- **Patient data.** There is none on this machine.

---

## 9 · A FAULT THIS KIT EXISTS BECAUSE OF — **F-215**

The previous capture, `deploy_kits/S203_LIVE_TOOLS/manojz/`, was taken at **12:42 on
26-Aug**. The three S203 repair kits landed at **12:53, 13:04 and 14:47** — *after* it.
Nothing re-captured at the S203 close, or at the S204 close.

So three of its ten files held the **pre-fix** bytes, byte-for-byte identical to the
`.bak_S203_R*` backups still sitting on manojz:

| file | the old kit | what is running |
|---|---|---|
| `PULL_FROM_MEDICAL.bat` | `92f03999…` — **before F-196's fix**, i.e. it writes `-- ok` unconditionally | `cfb8b13d…` |
| `marg_router.py` | `bbc50f91…` (pre-`S203_R1`) | `781e5ff6…` |
| `pipeline_status.py` | `51cf10c9…` (pre-`S203_R3`) | `0b3dd968…` |

**A rebuild from that kit would have restored the exact fault that let the feed run dark
for 8h40m while reporting itself healthy.** And its `SUMS.md5` verified **exit 0** the
whole time — because it hashes the kit against *itself*. A kit verified against its own
copy proves nothing about whether it matches what is running. That is F-209's lesson —
*a pin is not a backup* — in its mirror image: here the bytes existed, and they were the
wrong bytes, and the check said green.

It was also **missing nine files**, including **`PULL_HIDDEN.vbs`** — the thing the
scheduled task actually launches. A rebuild would have restored the pull and not the
launcher.

**This kit's 24 files were each verified against their LIVE SOURCE, not against this
kit's own SUMS: 24 checked, 0 drift.** That independent check is the difference, and it
is the one the next capture must also run.

---

*REINSTALL_MANOJZ · D350 §4 · S205 · bytes in `manojz\`, hashes in `SUMS.md5`.
NOT YET REHEARSED.*
