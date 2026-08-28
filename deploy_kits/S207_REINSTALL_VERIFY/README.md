# S207_REINSTALL_VERIFY — `VERIFY.bat` for both reinstall kits

**Built 27-Aug-2026, unattended session on manojz. Q2 of `UNATTENDED_QUEUE.md`.
STAGED, NOT INSTALLED. Nothing live was touched.**

Turns section 7 of each reinstall document — *"the checks that prove it worked"* — into one
command per machine that prints a pass/fail table and exits **0** (clear) or **1** (something
failed).

| file | run it on | rehearses |
|---|---|---|
| `VERIFY_MANOJZ.bat` + `verify_manojz.py` | **manojz** | `S205_LIVE_TOOLS/REINSTALL_MANOJZ.md` §7 |
| `VERIFY_MEDICAL.bat` + `verify_medical.py` | **the medical PC** | `S205_LIVE_TOOLS/REINSTALL_MEDICAL.md` §7 |

## HOW TO RUN

**On manojz** — Command Prompt, or double-click:

```
D:\dr-manoj-git\drmanoj-clinic-automation\deploy_kits\S207_REINSTALL_VERIFY\VERIFY_MANOJZ.bat
```

**On the medical PC** — copy the two `*_MEDICAL*` files and `verify_medical.py` anywhere on that
machine and run:

```
VERIFY_MEDICAL.bat
```

Offline proof, either machine, no live paths touched at all:

```
python verify_manojz.py --selftest
python verify_medical.py --selftest
```

## IT CHANGES NOTHING — and that is the whole point

The reinstall kits have **never been rehearsed**, because rehearsing them meant doing things to a
live machine. These verifiers read files, list folders, and run `pipeline_status.py` in its two
harmless modes. They never write into `margsync`, never post, never send, never start the agent,
never read a token. **So they can be run on the live machines on an ordinary Tuesday** — which is
the only way this kit ever gets rehearsed at all.

### The one check that is deliberately NOT the document's check

`REINSTALL_MANOJZ.md` §7 check 5 says **run `PULL_FROM_MEDICAL.bat`**. That is not read-only: it
copies, files, sends to the clinic server and mirrors to Drive. So check 5 here **reads the
evidence the last scheduled run left in `_last_pull.txt`** and says `(read)` in its own row.

**It is a weaker check and it is labelled as one.** On a *rebuilt* machine, where the pull has
never run, it is no substitute: run the batch by hand once, as the document says.

### Three of the medical checks run on the other machine

§7 checks 4, 5 and 6 of `REINSTALL_MEDICAL.md` are manojz-side. `verify_medical.py` prints them as
**CROSS** rows rather than dropping them, so the table matches the document one-for-one and nobody
concludes a check was lost.

### `verify_medical.py` reads the heartbeat rather than re-measuring

The agent already measures the watcher's pid, the watched folders, its own drift against Drive, the
ignored-file count and the backup age — and sends exactly those numbers to the clinic server.
Measuring them a second time here would produce a second answer that can disagree with the one the
server is being told, and then nobody knows which is true. **One measurement, one place.** The cost
is that a stale heartbeat makes every row unknowable — which is correct, because a stale heartbeat
*is* the fault, and check 2 fails first and says so.

## WHAT WAS PROVEN, AND WHERE — read this before trusting it

**Proven here, by running it:**

| | |
|---|---|
| `verify_manojz.py` | `py_compile` clean · **`--selftest` 33 checks, 0 failures** |
| `verify_medical.py` | `py_compile` clean · **`--selftest` 41 checks, 0 failures** *(38 at S207.1; three added by the live run below)* |
| end-to-end, manojz | run against a synthetic `MargPull` tree — PASS, WARN(stale) and FAIL(PROBLEM) branches each reached |
| end-to-end, medical | run against a healthy fixture (rc 0), a broken one (rc 1, 3 FAILs), and an empty folder |
| the real `pipeline_status.py --selftest` | executed for real: **`PIPELINE_STATUS SELFTEST PASSED -- 45 checks OK`** |

✎ **AND RUN AGAINST LIVE DATA, 28-Aug-2026 — this is S207.2.**

| | |
|---|---|
| `verify_manojz.py` vs the real `D:\Downloads\margsync` | check 3 **PASS** (real `pipeline_status`, 45 checks) · check 5 **PASS**, read the live `_last_pull.txt`: `END … -- ok`, 9 min old · **check 6 FAIL — and it was RIGHT**: it caught `days with NO export : 1 -> 2026-08-27` by itself, unprompted, on its first live run |
| `verify_medical.py` vs the manojz mirror | watcher **ALIVE, pid 11192**, all three folders, agent up to date, backup 0.7 days |

**⚠ Never judge the medical PC from the mirror.** `medical_SendToClinic\` refreshes only when the
pull runs, so its heartbeat is up to ten minutes behind — and from a machine in another timezone it
reads as *future-dated*. `VERIFY_MEDICAL.bat` points at `D:\SendToClinic` and must run **on that PC**.

### Three defects the live run found in THIS kit — all fixed, all now covered by selftests

1. **The timestamp hard-coded `IST`** and printed it on a UTC box: `27-Aug 23:59 IST` when the true
   IST time was `05:29` the next day. Right on manojz and the medical PC, **silently wrong anywhere
   else** — the exact mistake the working protocol's IST rule exists to prevent, committed by the
   file that prints it. It now reads the machine's **actual** zone label.
2. 🔴 **A heartbeat dated in the FUTURE read as FRESH.** Reading the mirror from a UTC shell made an
   IST heartbeat look **325 minutes ahead**, and `-325 <= 6` sailed through the "is it recent" test
   as healthy. **A negative age is not a small age.** Two clocks that disagree is a finding, and this
   is the failure class the whole medical-PC story is made of. Now FAILs beyond two minutes and
   names both causes.
3. **`IGNORED != 0` was a hard FAIL.** `REINSTALL_MEDICAL.md` §7 asks for zero; **the live machine
   reports 33**, all Marg auto-exports (`sanjeevni_medicos_<date>_s_a00NNNN.csv`) written per bill
   into a watched folder by Marg itself. **It can never be zero on a day the pharmacy sells
   anything.** A check that always fails gets waved through, and then it is not a check (D316). Now
   a WARN that says which names are noise and which would be a real missed report. **The document
   needs an owner ruling — candidate F-234.**

**NOT proven — say so rather than imply it:**

- **The two `.bat` wrappers have never been executed.** There is no Windows in the session that
  wrote them. They were written by copying the shape of `S206_F216_DISPOSITION/VERIFY_KB_CANON.bat`,
  which *did* pass on Windows on 27-Aug — but a shape is not a run. **First run on manojz is the
  real test of the wrappers**, and if one misbehaves the python file underneath it is fine: call it
  directly.
- Neither verifier has yet seen a **live** `heartbeat.txt`, `_last_pull.txt` or `MARG_PICTURE.txt` —
  only synthetic ones built from the format strings in `medical_agent.py` and `marg_gate.py`.

## A LEAK THAT WAS FOUND BY RUNNING IT

The first working version masked the medical address in the header it printed — and then printed the
**whole address** one line below, inside the text of the `OSError`. `redact()` and five selftest
checks now exist because of it. Recorded rather than quietly fixed: masking what you *build* is not
masking what you *print*.

## TWO FINDINGS THIS EXERCISE TURNED UP

1. **`REINSTALL_MANOJZ.md` §7 check 3 says `42 checks OK`. The captured `pipeline_status.py` says
   `45`, and with a double dash: `SELFTEST PASSED -- 45 checks OK`.** Measured, not read. The
   document is stale by three checks. **The verifier therefore does not hard-code the number** — it
   asserts on `SELFTEST PASSED` and *reports* the count, so it does not go red the next time a check
   is added. The document should be corrected at the next attended close.
2. **`.gitattributes` pins `*.bat`, `*.cmd` and `*.vbs` to CRLF but says nothing about `*.ps1`.**
   `VERIFY_KB_CANON.ps1` is CRLF today by luck of how it was written, not by rule — the same shape as
   F-152 and F-214. PowerShell tolerates LF, so this is cosmetic today; it is a rule-gap, not a
   break. **Not fixed here:** a `.gitattributes` line is a repo-wide rule and that is an attended
   decision.

## WHY A NEW FOLDER AND NOT INSIDE `S205_LIVE_TOOLS`

The queue said *"stage it in the kit folder"*. It is here instead, and the reason is
`S205_LIVE_TOOLS/SUMS.md5`.

That file's 27 rows are **bytes captured from the live machines**, and `MANIFEST.md` says every one
was additionally verified against its live source — 24 checked, 0 drift. `VERIFY_MANOJZ.bat` has no
live source; it is a new tool. Adding it to that `SUMS.md5` would make the file mean two different
things at once, and the next person to run the capture check would have rows that cannot pass it.

**Move it if you would rather** — nothing here depends on the location. The batch files find their
own `.py` beside them (`%~dp0`) and hard-code no path to the kit.

## WHAT THIS DOES NOT DO

- **It does not rehearse the reinstall.** It rehearses the *proof*. A rebuild still has to be done
  by the document, on a spare machine or a fresh profile, never on the live one.
- **It does not check the clinic health page.** Both documents end with a check that is not a
  command; both verifiers print it as **MANUAL** and neither counts it. §7 is explicit: until the
  health page agrees, the rebuild is not finished, however green the table is.

---
*S207_REINSTALL_VERIFY · Q2 · staged 27-Aug-2026 · NOT INSTALLED · nothing live touched.*
