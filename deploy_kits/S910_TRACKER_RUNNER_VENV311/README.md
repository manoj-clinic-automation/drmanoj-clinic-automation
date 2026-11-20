# S910_TRACKER_RUNNER_VENV311 — the runner to its own Python 3.11; the engine back to the clinic PC's exact bytes (the parent, S495, 20-Nov-2026)

Plan: `claude/S492_TRACKER_TO_SERVER_PLAN_FINAL.md` (his OK 15:31 IST 20-Nov). Session 3 of four, step A2 of `START_HERE_SESSION_495`.
**Nothing switches:** `/root/followup_tracker/OFF` stays present; the clinic PC still makes and sends the list. The switch evening is his to name.

## What it does (one run on the box, as root)
1. **The engine to the PC's bytes.** Kit S900 had put one line (`from __future__ import annotations`) into `/root/followup_tracker/processor.py`
   and into the replay copy, because the runner then stood on `/root/wa/venv` (Python 3.9). With S904's venv (Python 3.11, the PC's
   library versions) that line is not needed: `future_out_s910.py` takes it out of both files (`.bak_S910_<from>` beside each). The engine
   must then read **6929fc15** — the PC's `processor.py` byte for byte — and the replay copy **c1f7b50f**; anything else is put back, STOP.
2. **Proof under the 3.11 venv:** `replay2_s897.py --import-check` 0 errors; `server_runner.py --selftest` 0 failures; **Replay 2** again —
   every compared run's content hash must equal S908's (24 of 24; the S908 report is kept as `REPLAY2_REPORT_before_S910.txt`). Else put back, STOP.
3. **The runner's Python:** the two `# S895_TRACKER` crontab lines re-pointed `/root/wa/venv/bin/python3` → `/root/followup_tracker/venv/bin/python3`
   (only those two lines; the crontab's line count must be unchanged; the runner stays OFF).
4. **A dry pass** of `server_runner.py --dry-run` on a COPY of the tracker folder (venv, logs and backups left out) with OFF lifted in the copy
   only — the live folder is not written. Its last lines are printed (intake links, "waiting" / "nothing new").
5. **The watch (read only):** today's uploads at the receiver by origin (`pc` / `server`), the push unit's Do-not-call lines, what `logs/` holds.

`--undo`: the cron lines back to `/root/wa/venv`; the engine and the replay copy back from their `.bak_S910_` files (the venv folder stays).

## Proof before the install
- `future_out_s910.py` on the S908 files reproduced in the VM: engine b5b01d87 → 6929fc15 (`cmp` equal to the PC's file), replay copy 8d56e084 → c1f7b50f (equal to 0e7c129f + S908's two stable sorts); idempotent; `--check` exit codes.
- `rehearse_s910.sh` on a made-up root (stub crontab, stub venv python, stub replay2/runner; the real `future_out_s910.py`): 32/32 —
  green install · install again (already) · undo · hashes differ → put back, cron untouched · wrong engine → STOP, nothing changed ·
  tampered kit refused · selftest fails → put back · a failing run twice never writes the live report (no false pass) · a failing
  re-run never restores a stale backup · an undo with an unreadable crontab touches no file.
- Cold review (a reviewer that had not seen the build): 1 MUST (Replay 2 wrote the live report before the compare — a second run could pass
  falsely) + 5 SHOULD built in: the replay writes a scratch report, the live one only on success; every failure path puts back only what the
  run made; a crontab that does not read back is restored; the dry pass runs the copy's own runner with finance.db / the export store
  checked unchanged; the copy skipped above 2 GB; an undo stops before touching a file when the crontab cannot be read.
- Number gate (`NO_PHONE_NUMBERS.py --files-from`): clean. Second look: see the session's close report.

## His part
The publish (`D:\dr-manoj-git\drmanoj-clinic-automation\PUBLISH_ALL.bat`) and one server line:
```
cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s910kit && cp -rp /root/deploy/repo/deploy_kits/S910_TRACKER_RUNNER_VENV311 /tmp/s910kit && bash /tmp/s910kit/install_S910_TRACKER_RUNNER_VENV311.sh
```
