# S594_WITNESS_CRON — the witness line goes into the root crontab (23:58 nightly, read only)

**Brief:** `claude_code_briefs/S594_WITNESS_CRON.md` (v2, the Sanjeevni chat, session 328, 19-Oct-2026). **Charter:** v1.1. Board
`_numbers` v511 → v512; no ruling, no F. **Kit shape:** S471's crontab step (a line added with a backup and a restore), S577's `mask`.

## For the owner

One line is added to the server's nightly schedule: at 23:58 every night the stock figure writes its side-by-side file (the new figure
against the old ones, item by item). Seven nights of that, each explained, is the condition for retiring the old figures. Nothing else
changes; no screen moves; it reads only.

## For the parent (the clinic project — the crontab is its record, the map's row 4)

S594 added one line to the root crontab (`# S577_WITNESS`, 23:58 nightly, read-only; backup `/root/finance/crontab.bak_S594_<stamp>` —
the stamp is in `REPORT_S594.md`); the first witness night is the install day; seven explained nights = 4b-2's start.

## What it does

- **Nothing on the box is edited; no restart.** One line is appended to the root crontab, byte-exact (S577 README l.77):
  `58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS`
- **The tag stays S577's** (`# S577_WITNESS`): S577's README names it and the parent's crontab record will look for it. Every grep in
  the kit uses that tag.
- **What the line runs:** `stock_figure.py witness` (`main`, 1556–1580) honours `/root/finance/_off/ALL_OFF`, opens finance.db
  `mode=ro` with `timeout=60`, reads the spine through `stock_watch.Spine()` (read only; the spine's own build replaces `spine.db` by
  `os.replace`, so a read at 23:58 always sees one complete file) and writes `/root/finance/spine/stock_figure_witness_<Mon…Sun>.txt`
  through a temp file and `os.replace`. It takes no lock. A same-day rerun overwrites the same weekday file harmlessly.
- **Neighbours at the same hour** (unchanged): `50 23` spine_cadence, `55 23` sale_attribution and spine_compare, `57 23` near_expiry,
  `58 23` order_rehearsal (same minute, same folder, separate files — no clash; the walk proves no other line writes to the witness
  log), `59 23` purchase_app rematch (writes finance.db; the witness's read-only connection waits up to 60 s).

## Pins (read only, never edited; the installer STOPS if one moved, and proves none moved after the write)

| file | md5 |
|---|---|
| `/root/finance/stock_figure.py` | 92367a196b360f0cded4cda6a5ded700 |
| `/root/finance/stock_watch.py` | c5f3ce21a785c45df58f21932cf920e7 |
| `/root/finance/spine/spine_build.py` | e3d3ed85973eab2df0326dc9621e230e |

The crontab before: 83 lines (80 entries, three blanks), no `# S577_WITNESS` line (the 18-Oct 01:35 bundle's `crontab.txt`; S577 / S583 /
S587 proved it unmoved by md5 since; read again on the box at 08:20 IST 19-Oct: md5 684fe2fd, 83 lines, 80 entries, 0 tagged lines).
After: 84 lines. Backup: `/root/finance/crontab.bak_S594_<stamp>` (mode 600).

## The install (`install_S594_WITNESS_CRON.sh`)

`set -u`, not `set -e` (S471 l.23): every `grep -c` carries `|| true`, every gate is an explicit test. Window **08:00–23:49 IST** by
`TZ=Asia/Kolkata date +%H%M` — one window, so the add never lands while the 23:58 run is due. The build lock; no `DOCTOR_AUTO_OFF`
(no restart).

Gates (the window, the lock, SUMS, KIT_ID, the walk's line = the installer's, the walk compiles on both pythons) → the three read-only
md5s, `ALL_OFF` absent, the spine's `spine_state.json` passed (charter 1b) → **the idempotence gate** `crontab -l | grep -cF "# S577_WITNESS"
|| true` must be 0 (1 → "ALREADY IN — nothing to do", exit 0; more → STOP) → `crontab -l` copied to scratch (its line count, md5 and
trailing newline proved) → **the walk on the copy, with the rehearsal** (the command run once by hand as the line will run it, through
`mask`; its last line, the file's size and first ten lines printed; a non-zero exit or "switched off" = STOP; "not ready" = a NOTE) →
**the negative control** (a copy that holds the tag → the walk refuses; and the control itself goes red on the plain copy) → the crontab
unmoved during the walk → **DRY stops** → **the backup** `crontab -l > /root/finance/crontab.bak_S594_<stamp>`, which must exist, be
non-empty (`-s`), end in a newline, have the same line count as `crontab -l | wc -l` and the same md5 — otherwise STOP before any
write (a restore from an empty file is the one way this kit could harm the box) → `( crontab -l; echo "$CRON_LINE" ) | crontab -` →
read back: the tag in exactly one line, the line byte-equal (`grep -Fx`), lines = before + 1, `diff backup <(crontab -l)` = exactly the
one added line, `crontab -l | grep -vF "# S577_WITNESS" | md5sum` = the backup's md5, the three read-only md5s unmoved, `ALL_OFF`
still absent. **Red at any step after the write:** `crontab /root/finance/crontab.bak_S594_<stamp>`, then the md5 is proved back.

## The walk (`walk_s594.py`)

On the crontab TEXT (never the live crontab): the add is idempotent (applied twice to a copy → one line; the rest of the text byte for
byte as it was); the line parses as five fields + command (`58 23 * * *`; `cd <dir> && <python> -B stock_figure.py witness >> <log>
2>&1 # S577_WITNESS`); the program exists and is executable, the script exists and is readable, the working folder and the log folder
exist; the tag is unique after the add; no other line writes to the witness log and the lines already at `58 23` write elsewhere.
On the box, read only (`--run-witness`): `stock_figure.py witness` exits 0, is not "switched off", names its file, the file is there,
not empty and compares items (or says the spine is not ready — a NOTE). **`--expect-red`:** a copy that already holds the tag → the walk
refuses to add (green as a control); a copy without it → `NOT RED`, exit 1 (the control can fail).

## Charter

- **Retired:** nothing. **Left:** 4b-2 itself (after the seven nights, judged by the witness files' explanations).
- **Touched outside this project's files:** the root crontab, one line (named above for the parent).
- **Dependency state at install:** S577 / S583 / S587 live (`stock_figure.py` 92367a19); `/root/finance/_off/ALL_OFF` absent; the spine
  passed 13/13; no other build holding the lock (the installer prints all four).
- **Duties:** no staff duty is added, moved or removed — no `DUTY_MAP` change, no login affected, so no staff-eye walk.
- **Seen, not touched:** `/root/finance/spine/stock_figure_witness.log` does not exist yet (the shell creates it at the first 23:58 run).
  The rehearsal (08:27 IST 19-Oct, DRY) printed the one fail-soft line the brief foresaw, before the file was written and with exit 0:
  `stock_figure: start capture 6d718060 (2026-10-18T09:37:08) stays pending: attempt to write a readonly database` — the witness's
  read-only connection meets S587's start-capture judge, which wants to write the verdict; the capture stays pending in that run (the
  verdict is written by the paths that open finance.db for writing). That line will appear in the witness log each night while a start
  capture is pending. For the chat; not this kit's to change.

## Files

`KIT_ID.txt`, `README.md`, `SUMS.md5`, `walk_s594.py`, `install_S594_WITNESS_CRON.sh`. No `make_*.py`: no file is patched.

## The undo

`crontab /root/finance/crontab.bak_S594_<stamp>`, then `crontab -l | md5sum` must read the md5 the installer printed as the backup's
(`684fe2fd5f92d1217c7689010fca5831` as the crontab stood on 19-Oct 08:20 IST). No service to restart. The witness files written so far stay.
