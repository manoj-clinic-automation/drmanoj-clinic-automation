# S499_MEDICAL_AGENT_BACKUP — the medical PC's agent re-issued: Marg's own backup reaches the stick, the heartbeat says what was measured

**Project:** Sanjeevni. **Made:** 08-Oct-2026, in the cloud workspace, from the repository's own bytes; two **fix rounds** the same day after
independent reviews (experiments: `s499/review/exp/`, `s499/review_delta/exp/`; the builds they reviewed are kept in `s499/kit_prev/`
and `s499/kit_prev2/`).
**Touches:** ONE file on the medical PC, `D:\SendToClinic\medical_agent.py`. Nothing on the server, nothing on manojz, no scheduled task,
no start-up entry. **Not installed, not delivered, not published by this build.**

| | md5 | version |
|---|---|---|
| FROM | `70d5c4e3c439eaa049acb27f9851688c` | S205.1 — `deploy_kits\S212_LIVE_TOOLS\medical\medical_agent.py`, the md5 the medical PC's own heartbeat reports as running (08-Oct-2026 06:20 IST) |
| TO | `d91fa79ad972c39e531c70afb1a1c758` | S499.1 — `medical_agent.py` in this folder (the reviewed builds were `e60e04df…` and `b2dacd9b…`; neither was delivered) |

## What is in it

| file | |
|---|---|
| `medical_agent.py` | the TO file, S499.1 |
| `make_s499.py` | builds it from the FROM bytes: 13 anchored edits, each anchor exactly once, compiled in memory before a byte is written |
| `install_s499.py` | the installer's work, run ON the medical PC with that PC's own python (FROM / TO pins inside) |
| `INSTALL_AGENT_S499.bat` | the double-click: checks python starts, pins `install_s499.py`, runs it, keeps the window open — pure ASCII, CRLF (`.gitattributes` pins `*.bat` to CRLF, so `SUMS.md5` holds the CRLF bytes a fresh checkout gives) |
| `walk_s499.py` | the proof, with three negative controls |
| `KIT_ID.txt` · `SUMS.md5` | the kit's id; `md5sum -c SUMS.md5` from inside this folder |

## Why

1. **The stick alarm stood for days, and overstated.** The `.mbk` on `E:\` exists only when a person accepts Marg's prompt (every 2–4
   days, nobody's duty). Marg's OWN automatic backup (`D:\MARGERP\serverbackup`) was copied offsite hourly and **never to the stick**.
2. **`BACKUPS : 6 kit backup files are lying about` was false**: the prune keeps 3 per kit file (12 legal for four files); the line fired
   above 5; files delivered by `KIT_MANIFEST.txt` were neither pruned nor counted.
3. **Every pass re-copied three files** (`copied: 3`, `copied_bytes: 7429171`): three backups named `d1-sanjeevni-20250401-20260331.mbk`
   in `E:\`, `E:\MARGBCKUP\`, `E:\MARG BACKUPS 25\` (4,042,001 + 2,548,222 + 838,948 bytes, census 26-Aug) share one flat offsite name.

## What S499.1 does

- **The stick leg.** Each pass, the newest database file in `serverbackup` (`<n>_c18_d_…`) and the files written within 5 minutes of it go
  to the agent's OWN folder `E:\MargAuto_by_agent\<YYYY-MM-DD_HHMMSS>\` — temp name, `fsync`, size + md5 against the source, the source's
  time kept, then the real name. Left for the next pass: a folder Marg wrote to in the last 2 minutes, a file that changes between two
  looks. Newest **30 sets** kept in that folder only; nothing else on the stick is ever listed for removal; links and junctions are never
  followed (resolved path must lie inside the folder); nothing is deleted on Drive.
- **Only the backup stick is written to.** E: is used only if `E:\MargAuto_by_agent` exists or a hand-made Marg backup (`.mbk` or a
  `_cNN_` file, in any folder, any case) is on it. Otherwise nothing is written and a calm line says `STICK HOLDS NO MARG BACKUP: E:\ is
  plugged in … Take one in Marg by hand onto this stick; then the copies start by themselves.` A copy needs 10× the set's size free,
  else `STICK COPY FAILED: the stick has only N MB free …`.
- **The loud lines — these three only.** `*** NO MARG BACKUP ON THE STICK FOR N DAYS ***` when the newest backup of ANY kind on the stick
  (hand-made or the agent's copy) is over 3 days old; `*** NO MARG BACKUP ON THE STICK -- the backup stick is not plugged in since … ***`
  when nothing has been at E: for over a day; `*** NO MARG BACKUP ON THE STICK -- E:\ is plugged in but holds no Marg backup since … ***`
  (+ "take one in Marg by hand onto this stick") when a drive without a Marg backup has been at E: for over a day. Each has its own
  "since" in the state (`stick_absent_since`, `stick_unrecognised_since`), kept across restarts. A gap in Marg's own
  backup alone is one calm line (`its newest database file: N day(s) old`) — it is ordinary on this PC (Drive shows none 01→05-Oct).
  `exactly one place` is printed only when measured in this pass: the stick in and stale, the offsite folder read, nothing newer in it,
  no fresh hand-made or automatic copy.
- **Other heartbeat words.** Every key S205.1 wrote keeps its name and meaning (`newest_stick` = newest backup of any kind on the stick).
  Added: `stick_present`, `newest_handmade(_age_days)`, `newest_auto_on_stick(_age_days)`, `newest_serverbackup_blob(_age_days)`,
  `newest_serverbackup_offsite(_age_days)`, `stick_copy`, `offsite_renamed`, `zip_compare`, `stick_absent_since(_ts)`, `stick_unrecognised_since(_ts)`,
  `offsite_measured`, `future_dated`; top level `kit_backup_state`; `agent_self.installer`. A file dated more than a day ahead is left
  out of every choice and age and named in one calm line; a time no clock can show (Windows raises on it) is written `?` and never
  stops a pass. A spoiled `backup_state.json` no longer stops the heartbeat; it is written
  whole or not at all.
- **The OUT OF DATE line** now says `FIX: double-click <the Drive folder the agent found>\ToMedical\INSTALL_AGENT_S499.bat` — no drive
  letter of its own, never the old installer. The only other mention of `INSTALL_AGENT.bat` in the file is a historical docstring.
- **For the record, once a day:** the file LIST (central directory, no password, **no member opened**) of the newest hand-made `.mbk` and
  the automatic file nearest it in time. **Not a restore; no restore of either has ever been tested.**
- **The prune alarm** fires only when a prune could not remove a file, or a file the prune has been over still has more than 3; the
  manifest's files are pruned and counted too; the prune also runs hourly.
- **The re-copy loop ends:** namesakes get distinct offsite names (`…__in_MARGBCKUP_<6 hex>.mbk`); 3 copies once, then none.
- **Unchanged to the letter:** 25 of S205.1's 34 functions, every module constant but `AGENT_VERSION`, the crash handler; `main()` gains
  seven lines (the hourly prune). Standard library only (`zipfile` added). Parses as Python 3.8+; that PC runs 3.11.9.

## The installer

The agent is the child of `D:\SendToClinic\agent_guard.py` (S387/S388), started at sign-in. Its only switch is
`D:\SendToClinic\_off\AGENT_OFF.txt`. `INSTALL_AGENT_S499.bat` checks that python starts (else prints `FAIL:` and pauses), that
`install_s499.py` is the file built, and runs it. `install_s499.py`:

0. **The lock** `D:\SendToClinic\S499_INSTALL.lock` holds the installer's pid: a lock whose process is gone (the window was closed) is
   stale AT ONCE (the guard's own `pid_alive` test); a live run's lock means "another run"; no permission is said as that.
   On Windows a console close / Ctrl handler (`SetConsoleCtrlHandler`; failure to register is harmless) removes THIS installer's
   switch when the window is closed.
1. **Gates, nothing changed if any fails.** A switch a PERSON wrote → stop. A switch an earlier run of THIS installer left (its first line
   `written by install_s499.py <time>`) → taken away, the agent waited for, then on. Live file TO → `ALREADY INSTALLED` only when no
   switch, a heartbeat under 10 minutes old names S499.1 and says `WATCHER : ALIVE` — else `INSTALLED BUT NOT RUNNING RIGHT - <what>`;
   if the new file is in place but the OLD agent still runs it from memory (a run cut short before the guard saw its switch), the
   job is finished through the guard (steps 4–5).
   Live ≠ FROM → stop. Kit file ≠ TO → stop. Not compiling with that PC's python → stop. **Any export or capture in the last 5 minutes**
   (`_captured`, `_captured_txt`, Marg's three output folders, the top of `E:\`) → stop: "wait five minutes and double-click again".
   The guard's own records must show its agent running.
2. Backup `medical_agent.py.before_70d5c4e3`.
3. The new file takes the live name while the OLD agent still runs from memory; md5 read back.
4. Switch written whole (temp name, then `os.replace`), the answer of **the guard that runs the agent** (its own `[account pid]` tag — another account's standing-by guard
   never counts) waited for, switch removed at once in a `finally` (Ctrl-C included). **Nothing is printed while the switch is there.**
   No answer in 90 s → the old file is put back INSIDE the `finally`, before the switch goes; nothing changed.
5. The new agent's `starting` line and a heartbeat naming S499.1 with `WATCHER : ALIVE` waited for (240 s).
6. Anything red after 3 → old file back byte-identically, old agent waited for.
7. `S499_INSTALL_RESULT.txt` appended in `D:\SendToClinic\` and Drive `FromMedical\`.

Capture stops for about 30 seconds (the guard stops the watcher with the agent). **If the window is closed while the switch is on:**
on Windows the close handler removes the switch; if the process is killed outright (no handler runs), the switch and the lock stay, and
the agent stays off **until the next double-click** — which finds the lock's process gone, takes the lock, recognises the switch as its
own, removes it and finishes. The `.bat` says `WARNING: the agent is still switched off … double-click this file again` whenever it
ends with `AGENT_OFF.txt` still there. The banner says: do this when nobody is exporting; do not click inside or close the window.

**The `.bat` has never been executed** (no Windows here); linted (`deploy_kits\lint_bat.py`: OK) and checked for ASCII / CRLF / pin.

## Delivery and the one action at the PC (not done by this build)

Into Drive `Clinic Data Archive\ToMedical\` — **the root, not `_kit`** — byte-identical to this folder:
`INSTALL_AGENT_S499.bat` (CRLF) · `install_s499.py` (LF) · `medical_agent.py` (LF, TO; it replaces S205.1 there — keep that as
`medical_agent_S205.1.py.superseded`). The agent's 30-second kit pickup reads only `ToMedical\_kit\` and only names on its built-in list
or in `KIT_MANIFEST.txt`; none of the three is either, so it never touches them. It does read `ToMedical\medical_agent.py`, for the
OUT OF DATE check: S205.1 says OUT OF DATE until the install, S499.1 says up to date after it.
**Rename the old `ToMedical\INSTALL_AGENT.bat` (v3, md5 `b7a702f2…`) to `INSTALL_AGENT_v3_RETIRED_DO_NOT_RUN.txt`** — a `.txt` cannot be
run by a double-click. It kills every python including the guard; S205.1's own FIX line still names it.

**The sentence for the person at the medical PC:** "When nobody is using Marg for a report, open Google Drive, go to
`G:\My Drive\Clinic Data Archive\ToMedical`, double-click `INSTALL_AGENT_S499`, do not touch the black window, and wait about two
minutes until it says DONE." (G: is where the heartbeat of 08-Oct shows Drive for the account `user`.)

## Undo

Create `D:\SendToClinic\_off\AGENT_OFF.txt`, wait half a minute, copy `medical_agent.py.before_70d5c4e3` over `medical_agent.py`, delete
`AGENT_OFF.txt`; put S205.1 back in `ToMedical\medical_agent.py`; delete `E:\MargAuto_by_agent` (S205.1 would send its files offsite as
if hand-made and could loop on reused names).

## Proof (`walk_s499.py`, python 3.11 — the PC's — and 3.13, one full run each)

`walk_s499.py --old <S205.1> --prev <kit_prev> --prev2 <kit_prev2> --readers <copies of pipeline_status.py, verify_medical.py> --guard <copy of agent_guard.py> --work DIR`

- **NEW agent** 138 checks, all green. Three negative controls on the same checks: **S205.1** 72 red as declared, 58 same;
  **first reviewed build e60e04df** 27 red (stranger drive, gap-alone loud, absent stick, unmeasured "one place", future dates, spoiled
  state, link pruning, free space, FIX line, half-written state, fsync, a 4000-state fuzz, the blank stick, an impossible time …), 111
  same; **second reviewed build b2dacd9b** 4 red (the blank stick said as "not plugged in", an impossible time stopping the pass, the
  new state keys), 134 same.
- **Installer** 38 checks green against the REAL guard: 33 with stand-in agents (installed · twice · wrong pins · crash / mute / watcher
  down → put back · no compile · no guard · dead guard · a person's switch · two runs · a stale lock · Ctrl-C with the switch on ·
  a leftover switch of its own · not running right · a recent export · a standing-by guard answering first · a lock without
  permission · nothing printed while switched off · a mutant without put-back · **the process killed with the switch on (switch and
  lock left) → the next double-click finishes at once** · the close handler · a half-written switch · the old file back before the
  switch goes), and 5 with **the kit's own two files at their own pins** (real S205.1 under the real guard, swapped by the real
  installer, real S499.1's first heartbeat). Controls on the same 33: **installer 6ace86a9** 14 red, 19 same; **installer 5c7e1b90**
  4 red (killed run, close handler, half-written switch, restore order), 29 same.
- **Readers** — `pipeline_status.py` (31aad5e6, live on manojz) and `verify_medical.py` (S207.2), their own code, on 10 heartbeats and
  4000 made-up states: every field they read equals what the agent measured. **UPG** 2, **Q** 6, **K** 13 green.

## Not done, and not known

- Not run on Windows: `E:\`, FAT, `certutil`, a file Marg holds open, junctions (resolved by `realpath` — Linux symlinks stand in), the
  console's QuickEdit, **the console close handler** (its cleanup is walked; `SetConsoleCtrlHandler` itself is not), the Windows
  `pid_alive` branch (copied from `agent_guard.py`). No real Marg backup was opened. No restore tested.
- Three unchanged S205.1 functions (`captures_today`, `ignored_files`, `marg_slots`) still turn file times into dates without the new
  guard; they are not in the backup pass, but a file with an impossible time in `_captured` or Marg's folders could still stop a beat.
- Found in S205.1 and **left as they are**: a manifest line can replace `medical_agent.py` under another kit name, and the manifest md5 is
  not compared for a `.py`; the offsite test is name + size (a same-size rewrite is not re-sent); `pipeline_status.py` cannot read a
  name containing `(1)`; `verify_medical.py` still says "run INSTALL_AGENT.bat"; `deploy_kits\PC_KITS\medical\kit.zip` and
  `S212_LIVE_TOOLS` carry S205.1 for a reinstall.
