# S202_B2B — the manojz half of the pipeline heartbeat

**Place this only AFTER `S202_B2A` is green on the VPS** — until the endpoint exists there is
nothing to post to.

## What it is

`pipeline_status.py` runs on manojz at the end of every 10-minute pull and posts what manojz can
see and the server cannot: outbox depth and age, whether the pull ran, whether the medical
watcher is alive and capturing, files it cannot take, and how far behind the Drive offsite copy is.

It is a **reporter**. It reads, it posts, it changes nothing.

## Rules it keeps

- **It can never fail the pull.** Every section is independently guarded and every failure path
  returns 0 with a note. A monitor that takes down the thing it monitors is worse than no monitor.
- **It never prints or logs the token**, and it reuses `marg_gate.resolve_token` rather than keeping
  a second copy of that rule (D349).
- **It reuses `FINANCE_MARG_TOKEN`** — no fourth secret to rotate.

## The bug that running it against REAL data caught

The first version counted **files in `_outbox`** and reported *"10 waiting, oldest 192.8 hours"*.

**That was wrong.** Delivered files are deliberately KEPT in `_outbox` — the pipeline reference says
so in as many words. So the check would have gone red on day one and stayed red forever, and the
owner would have learned to ignore it. **A false alarm is worse than no alarm.**

Corrected to read `marg_gate`'s own `_outbox_state.json`, which is the authority on what has been
delivered, and to count only what is genuinely pending. Against the same real data it now reads
**0 pending, 10 kept** — the outbox *is* draining and F-179's fix is working.

A selftest check now covers exactly that case, so it cannot regress.

## Install (after B2A is green)

1. Copy `pipeline_status.py` to `D:\Downloads\margsync\MargPull\`
2. Prove it before wiring it in:
   ```
   python D:\Downloads\margsync\MargPull\pipeline_status.py --selftest
   python D:\Downloads\margsync\MargPull\pipeline_status.py --dry-run
   ```
   The dry run prints exactly what would be posted, and posts nothing.
3. Add one line to the end of `D:\Downloads\margsync\MargPull\PULL_FROM_MEDICAL.bat`, after the
   existing `marg_gate.py status` step:
   ```
   python "%~dp0pipeline_status.py"
   ```

## Verify

`https://followup.dr-manoj.in/finance/health` — the **Pipeline heartbeat** row should change from
*"manojz has never posted a status"* to *"manojz reported N minutes ago"* within ten minutes.

---

## PLACED AND WIRED — 26-Aug-2026, S202

- `pipeline_status.py` → `D:\Downloads\margsync\MargPull\` · md5 `51cf10c9f2543fcd48a61ee7f8faf51a`
- `PULL_FROM_MEDICAL.bat` wired **after** the `END ... -- ok` stamp, so the status it posts includes
  this run's own result. Backup kept beside it as `PULL_FROM_MEDICAL.bat.bak_before_B2B`;
  CRLF line endings preserved and verified.
- Its selftest passes from the installed location: **15 checks OK**.
- A second robustness fix before placing: the heartbeat path is now **discovered** among H:, F: and
  the local margsync mirror, newest-that-exists winning, and the payload reports **which** file it
  read. A moved drive letter must degrade to "I could not read it", never to a silent green.

---

## CORRECTED SAME DAY — the wiring was on the success path only

**The first wiring was wrong in the way that matters most.** `PULL_FROM_MEDICAL.bat` exits early
when the medical PC is unreachable:

```
echo END %DATE% %TIME% -- FAILED: medical PC unreachable>> "%HB%"
exit /b 1
```

…and that exit is **before** the line I added. So the reporter ran only when the pull SUCCEEDED —
**a monitor that could report success and nothing else.** Exactly the born-dead shape AF-2 had, and
the shape the never-fired witness in B2A exists to catch. Built in B2A, then wired past in B2B.

Found because the owner asked why a Marg report had not arrived and the sweep read
`_last_pull.txt`: `FAILED: medical PC unreachable` at 06:30, 06:40 and 07:00 — three cycles that
would have posted nothing.

**Corrected:** one `:report` subroutine, called from **every** exit path (D349 — one rule, one
place). Its output is deliberately NOT suppressed.

**And a pre-existing hazard found beside it:** the no-python failure path had an **unguarded
`pause`**. Under the scheduled task (`AUTO`) it would wait for a keypress that never comes and hold
the pull cycle for ever. Guarded like every other pause in the file.

**Note on the file:** it has MIXED line endings — some lines LF, some CRLF. The patch was applied
line-by-line preserving each line's own ending rather than rewriting the file.
