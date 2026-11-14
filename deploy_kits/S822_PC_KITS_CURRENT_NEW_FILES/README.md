# S822_PC_KITS_CURRENT_NEW_FILES — the Clinic PC kits keep themselves current (S456, the parent, 14-Nov-2026)

**The owner's word (D972, 14-Nov-2026 05:57 IST):** the Clinic PCs page says how each PC is set up now, and its set-ups stay
current by themselves. S453 found two gaps in what S723 (nightly, `pc_kits_current.py`) already does:

- **F-1385** — only members the kit already carries are refreshed; a program file **added** on the medical PC is neither
  packed nor reported.
- **F-1386** — a repacked kit reached the Clinic PCs page only with the owner's **next server line**: nothing on the server
  pulled `/root/deploy/repo` by itself (the 14-Nov bundle's crontab, units and code read: no pull anywhere).

## Half 1 — Dr Manoj's PC (manojz): `D:\Downloads\_kbtools\pc_kits_current.py` S723+S794 → **S723+S794+S822**

Placed by Claude through the file tools (the old file kept beside it as `pc_kits_current.py.bak_S822_af2495ef`). NIGHTLY.bat
runs it unchanged (step 3b, before the kit rehearsal). What is new:

- A **program file** (`.py .bat .cmd .ps1 .ahk`) at the top of the mirror `D:\Downloads\margsync\medical_SendToClinic` that the
  kit does not carry is looked at. The mirror is `robocopy /E` without `/PURGE` — it keeps every file ever deleted on that PC
  (S214's note in that folder) — so a file counts as **on the PC** only when the PC's own share lists it tonight
  (`\\100.119.151.40\DDrive\SendToClinic`, the path PULL_FROM_MEDICAL.bat already reads; `os.listdir` only, read-only, 40 s limit).
- On the PC **and** its bytes are its newest live pin (`D:\SendToClinic\<f>` in the newest `live_pins_S*close.txt`) **and** Drive's
  `KIT_MANIFEST.txt` does not disagree → **ADDED**: `payload/<f>` after every existing member, a row appended to `MD5SUMS.txt`
  in the file's own shape (line ending, final newline), `KIT_INFO.txt`'s `version` says `added <f>`. `setup_pc.py` reads the
  payload list from `MD5SUMS.txt`, so a reinstall places the new file too.
- On the PC with **no live pin**, or bytes **not its pin** → **reported**, never packed ("record it as a pin, or retire it").
- In the mirror but **not on the PC** → "mirror-only (that PC no longer has it)". PC unreachable → "on the PC unknown tonight",
  nothing packed; the medical line also says the PC's folder could not be listed.
- Never looked at: `*.bak*`, `*.before_*`, `*RETIRED*`, `*.superseded*`, logs, text, zips; a name that is a member's in another
  case (Windows names) is not new.
- `drive_manifest()` now also looks under `<L>:\My Drive\Clinic Data Archive\ToMedical\_kit\` — the folder the medical PC's
  heartbeat names — so the nightly's "drive: not mounted" (S453 §3 gap 2) is answered when the Drive is mounted on that PC.
- The report gains a line `the PC : …`; the last line says the server pulls the repository by itself.

**Tonight's expected report (dry run 14-Nov 08:39 IST, the PC not asked):** `medical_agent.py d91fa79a -> b94434dc` repacked
(S823, the existing rule) and seven August files reported as new — `GUARD_AND_SEND.bat`, `INSTALL_WATCHER.bat`,
`SETUP_CHECK.bat`, `START_MARG_WATCHER.bat`, `_kit_marg_watch.py`, `guard_and_send.py`, `marg_report.py` — none has a live pin,
so none is packed; the share listing will say which of them the PC still has (S214: `START_MARG_WATCHER.bat` no longer exists
there). Whether to retire the rest is the Sanjeevni chat's to say.

**Proof:** `walk_s822.py` 38/38 GREEN on made-up roots (A1–A13 and the S723 behaviour kept); on the OLD tool 25 of 25 S822 checks
RED, the S723 checks still green (`--control`); S723's own walk 26/26 and S794's 30/30 on the new tool; a dry run on the real
repository, mirror and tools (14-Nov 09:16 IST).

**Cold review by a second reader: SAFE TO INSTALL, no must-fix.** Its should-fixes, built and walked: the report header says
when the PC could NOT be listed (and why); installer-shaped names (`install_*`, `setup_check*`, `_kit_*`) are reported and
never packed even when pinned — a set-up kit carries programs, not installers; the share's host and name come from
`D:\Downloads\margsync\_config\machine.conf` (`MEDICAL_HOST` / `MEDICAL_SHARE`, the keys PULL_FROM_MEDICAL.bat reads) with
the constants as fallback; the listing is one `os.scandir` round trip and a failure's reason is kept; the installer stops
when the cron service is not active; `--manifest <file>` lets the walk exercise the Drive-manifest rule (A12) and a kit
without `MD5SUMS.txt` is proved not to take a new member (A13). Left as nits: the first server run pulls for real from
inside the clone (later gates re-hash the kit); the pull log keeps git's last error line (git redacts credentials in URLs).

## Half 2 — the server, by the owner's one line

```
cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S822_PC_KITS_CURRENT_NEW_FILES/install_S822_PC_KITS_CURRENT_NEW_FILES.sh
```

- **NEW `/root/deploy/repo_pull_s822.sh`** + one cron line `7,37 * * * * … # S822_REPO_PULL`: `git pull --ff-only` in
  `/root/deploy/repo` every half hour under `flock`; skips a round while an installer holds `/root/deploy/.claude_code_build.lock`;
  `GIT_TERMINAL_PROMPT=0`; one log line per event (a move or a failure) in `/root/deploy/repo_pull_s822.log`, kept to 400 lines.
  It installs nothing — the Clinic PCs page serves `kit.zip` straight from the clone, so a repacked kit shows within half an
  hour of the owner's publish. His own server lines (`git pull --ff-only && bash …install.sh`) work as before; the one
  theoretical overlap is a pull in the same second as his, in which case his line stops at git's own lock and he runs it again.
- **`/root/finance/pc_kits.py` 4191e447 → 45d6f15d** (`edits_s822.py`, two exact edits on the live bytes; display only): the
  Medical PC's `kit_keeps` sentence — "A new program on that PC joins the kit the same way. The new kit shows here within half
  an hour of your publish." The Reception PC's sentence is unchanged (checked).
- **Proved before placing:** the clone on `main` tracking `origin/main`, no changed tracked file, and `git ls-remote` reaching
  the remote in a **bare environment without a terminal** (as cron runs) — else **NOT APPLIED**, nothing changed. After placing:
  the pull script run once (a no-op pull after his own), the service restarted and healthy, the cron line read back exactly
  once, every other crontab line kept byte-wise. Any red → everything back (crontab byte-exact, the script out, the old file back).
  `--undo` reverses all three. Rehearsed on a stand-in root (`rehearse_s822.sh`, in the working folder, not in the kit).

## Not in this kit (named in the entry point; owed)
- The pathology lab PC's card still says "Not set up yet" though S655 runs — the NK Pathology chat is told first.
- The "Other set-ups" notes (`/root/finance/setup_notes.py`, checked 22-Oct) — re-read against the newer builds, later.
- `pc_kits_current.py` picks the newest pin list by session **number** (`live_pins_S454close` over the later-placed
  `live_pins_S453close`), not the manifest's CURRENT row — a small fault for the record; both lists carry the medical pins.

Nothing in this kit reads or writes a patient, a number, a key or a token.

## Pins
- Dr Manoj's PC: `D:\Downloads\_kbtools\pc_kits_current.py` af2495ef → **aa2f1596** (the old file kept beside it as `pc_kits_current.py.bak_S822_af2495ef`).
- Server: `/root/finance/pc_kits.py` 4191e447 → **45d6f15d**; NEW `/root/deploy/repo_pull_s822.sh` **17ce188f**; cron `7,37 * * * * /bin/bash /root/deploy/repo_pull_s822.sh # S822_REPO_PULL`.
