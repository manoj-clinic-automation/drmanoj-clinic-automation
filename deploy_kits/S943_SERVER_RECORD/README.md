# S943_SERVER_RECORD — the nightly server record (roadmap S510 phase 0, A1 · plan L1)

*The parent · S511 · 24-Nov-2026.* Read-only on the box. Phase 0's first kit.

| file | pin | what changes |
|---|---|---|
| finance/server_record.py | NEW a3b5950f | Nightly 02:50 (cron, its own lock, ALL_OFF gate): one JSON under `/root/finance/server_record/` (`YYYY-MM-DD.json` + `LATEST.json`, 90 days kept) — df of every real filesystem, du of the known roots (`/root/finance`, `/root/wa`, `/root/backups`, `/root/state_backup`, `/root/assetapp`, `/root/followup_tracker`, `/root/portal`, `/root/labdata`, `/root/deploy`, `/root/marg_ingest`, `/var/log`, `/tmp`), RAM total/available, load 1/5/15 + CPUs, the five biggest processes (pid, memory, cpu, age, **command name only — never arguments**). Warnings: disk ≥ 80 % · RAM available < 1 GB · 15-minute load at or above the CPU count. `--check` says LATEST in one line; `--selftest` on made-up tools. |
| finance/owner_console.py | cf7f8b09 → 55a3daa2 | System section, after the reception PC's heartbeat: one line "Server: disk N% used (N GB free) · RAM N GB available · load N — recorded 02:50" (green; amber with the warnings as sub-lines; grey "not written yet" before the first night; amber "not written since …" when a night was missed). Through `piece()`, so a broken record never takes the section down. |
| finance/freshness_legs.json | f2ade687 → 2a03e305 | One leg: `server record`, file_mtime on LATEST.json, 26 h, group Watchdog. The other 41 byte-for-byte. |

**The assistant's call (recorded for the close):** the roadmap's "server N · PC N · same" line is not built here — the PC spare's `_last_pass.txt` lives on manojz (`D:\Downloads\DocterzArchive\`) and nothing carries it to the box since the switch (the red line forbids PC uploads). The server's own count already shows (S911's CALL CAP line); the PC's count is read by the assistant from manojz's folder during the seven-day watch, not by a box-side build.

## Proof
- `walk_s943.py` (made-up data): **WALK 16/16** — the selftest (10/10: the three warnings, 90-day keep, tools missing), the console reader in five states, the legs file. Control (the FROM console) red 6/16.
- `rehearse_s943.sh` on a made-up root (stub systemctl / health / crontab): dry · install (first record written, cron in, one restart) · again · undo · forced red (everything back) · healthz 500 before → nothing · tampered kit · wrong live pin · lock held · crontab empty → restored — **12/12**.
- No ten-digit run in any kit file (the selftest builds its figures at run time).

## Install
See S942's README — one combined server line. Undo: `bash /tmp/s943kit/install_S943_SERVER_RECORD.sh --undo` (files back, the new script moved aside, the cron line out; the records folder kept).
