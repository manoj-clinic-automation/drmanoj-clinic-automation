# S232_MEDICAL_BOOT_TASK — captures survive a reboot (F-362 · ⭐5 item 1.9)

**PREPARED. One paste on the MEDICAL PC, Administrator PowerShell. Nothing else.**

## The problem, in one line

`MargAgent.cmd` lives in Dr Agarwal's Startup folder, so **a reboot with nobody logged in means no
captures, no heartbeat and no backup** — and the only signal is an absence. **It already cost 21½
hours of uncaptured trading on 29–30 Aug.**

## Why this is two tasks and not one

The obvious fix — run the agent at boot as `SYSTEM` — **breaks the offsite Drive copy.**
`medical_agent.py`'s `find_drive_out()` looks for `My Drive` on a drive letter or under
`%USERPROFILE%`, and **Google Drive only mounts inside an interactive logon session.** As SYSTEM
there is no such session, so the Marg `.mbk` backups would stop reaching Drive — and manojz's pull
does **not** cover them (it watches `_captured`, `Sent`, `NEEDS_UPLOAD` and `MARGERP\users`, not
`E:\MARGBCKUP`). **That copy is the only offsite route the database backups have. Trading a lost
reboot for a lost backup is not a fix.**

So:

| task | trigger | runs as | does |
|---|---|---|---|
| **`MargAgentBoot`** | At startup | `MEDICAL\SET`, whether logged on or not | starts the agent, so **captures run with nobody logged in** |
| **`MargAgentBootStop`** | At logon | SYSTEM | ends `MargAgentBoot`, so the interactive agent takes over cleanly |

**The Startup folder item is left exactly as it is.** When he logs in, the boot agent is stopped and
his own session's agent starts as it always has — **Drive leg included, unchanged.**

Without the second task the two agents fight: `medical_agent.py` kills the watcher pid recorded by
the previous run and starts its own, so each would keep killing the other's watcher. **One agent at
a time is the whole point of the pair.**

## What it does not do

**No code changes. No file is replaced. The Startup item is not removed or renamed.** The only
change on disk is two entries in Task Scheduler, and the undo is one line, printed at the end.

## Proof it worked, printed by the paste itself

It starts the task immediately, waits 20 seconds, reads `_watcher.pid` and confirms that process is
actually running, then shows the last three heartbeat lines. **A green "WATCHER ALIVE" is the
result** — not the fact that the task was created.

## The one thing it asks for

The `MEDICAL\SET` password, once, at the `/RP *` prompt. That is Windows' own prompt; the password
is never in this file, never on a command line, and never reaches anyone else. A task that runs when
nobody is logged on cannot be created without it.

---
*S232 · ⭐5 item 1.9 · F-362 · prepared 08-Sep-2026, not applied.*
