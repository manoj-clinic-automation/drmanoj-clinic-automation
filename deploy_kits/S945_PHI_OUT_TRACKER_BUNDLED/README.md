# S945_PHI_OUT_TRACKER_BUNDLED — roadmap S510 phase 0, A3 (F-1631) + A4 (F-1613)

*The parent · S511 · 24-Nov-2026.* One kit, one line, read-only on everything live except the moves it names.

| what | pin | change |
|---|---|---|
| `/root/wa/recordings-archive/make_force_keys.py`, `force_keys.txt`, `call_verdict_BACKUP_S123_pre_join_redesign.py` | moved | → `/root/_retired/S510/` (0700, files 0600; the nightly bundle never enters `_retired`). The retired `make_force_keys.py` has its TRIPLES list (41 patient numbers) replaced by `TRIPLES = []   # removed S510 (F-1631)` — the numbers leave the box's code. Nothing imports them: `verdict_review.py` reads `force_keys.txt` only when it exists; the night's verdict stage never reads it. `retire_s945.py --check` says the counts (never a number). |
| state_backup/code_bundle.py | aa8f985f → 2f474dba | One SOURCES line: `/root/followup_tracker` top level, `*.py` and `*.sh` (token/secret/users by name excluded). Non-recursive, so `data/ uploads/ archive/ venv/ logs/ outputs/ intake/` are never entered; OFF, SWITCHED_AT, `*.json`, `*.txt` stay out by the patterns. |

The installer runs `code_bundle.py build` after the moves (the local tar only, no Drive — the 01:35 nightly uploads as always) and reads the built MANIFEST: the tracker's `server_runner.py` in, no `make_force_keys`, no tracker data folder — else everything back.

## Proof
- `retire_s945.py --selftest` **10/10** (made-up folder, numbers built at run time): the three moved, 0 phone-shaped runs left, the retired list empty and the script still compiles, 0700/0600, again = nothing, a file both live and retired = STOP, undo brings them back without the numbers.
- `walk_s945.py` **8/8**: the kit's `gather()` on a made-up root carries the tracker's `.py`/`.sh` only, nothing from its folders, no OFF/SWITCHED_AT/json/txt/token file, never `_retired`, `finance_app.py` still in. Control (the FROM) red 6/8.
- `rehearse_s945.sh` (a made-up ROOT; the real `build` runs on it): dry · install · again · undo · forced red → everything back · tampered · wrong pin · lock held · a half-retired state → STOP, everything back — **13/13**.
- The 25-Nov bundle's MANIFEST is the nightly proof (read at the next open): `root/followup_tracker/*.py` present, `make_force_keys.py` absent.

## Install (his one server line)
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s945kit && cp -rp /root/deploy/repo/deploy_kits/S945_PHI_OUT_TRACKER_BUNDLED /tmp/s945kit && bash /tmp/s945kit/install_S945_PHI_OUT_TRACKER_BUNDLED.sh
```
Undo: `bash /tmp/s945kit/install_S945_PHI_OUT_TRACKER_BUNDLED.sh --undo` (code_bundle.py back; the three files back — the 41 numbers do not come back, by design).

`--undo` when only part was applied: no `.bak` (code_bundle.py was already at its TO) → only the three files come back; a `.bak` present but the live file not this kit's (a later kit) → refuses everything.
