# S594_WITNESS_CRON — brief for Claude Code (v2)

*v2: after an independent read (R1) — 2 blockers (a `grep -c` that exits 1 under `set -e` at the idempotence gate; a crontab backup not proven non-empty before the write) and the corrections below folded in; this text governs. R1 is `03_WORKING_PAPERS\S328\S594_R1_REVIEW.md`.*

*Written 19-Oct-2026 by the Sanjeevni chat (session 328) at the owner's word (01:40 IST: the witness line goes in from this project, not by a hand-off to the clinic project). One root crontab line — the one S577's README names at its l.77 and did not add — so that the seven-night side-by-side week of `stock_figure` against the old stock figures starts; 4b-2 (retiring the old figures) waits for it. **No file on the box changes; no restart.** The crontab is the clinic project's record (the map, row 4): this README says the kit touched it, and the clinic chat reads that at its next open. Charter v1.1. Kit shape: S471's crontab step (`deploy_kits/S471_PACKS_SEPTEMBER/install_S471_PACKS_SEPTEMBER.sh` l.82, 87, 101–102 — the precedent for adding a line with a backup and a restore). Read `CLAUDE.md` first.*

## 0 · For the owner

One line is added to the server's nightly schedule: at 23:58 every night the stock figure writes its side-by-side file (new figure against the old ones, item by item). Seven nights of that, each explained, is the condition for retiring the old figures. Nothing else changes; no screen moves; it reads only.

## 1 · Numbers and pins

- Kit **S594_WITNESS_CRON** (board `_numbers` v511 → v512). No ruling, no F. **PLANNED on the root crontab** (the clinic project's record) — this README's "For the parent" line is the notice.
- **Nothing edited on the box.** Read only, STOP if moved: `/root/finance/stock_figure.py` **92367a196b360f0cded4cda6a5ded700** (its `main` accepts `witness`, 1556–1580: honours `/root/finance/_off/ALL_OFF`, opens finance.db `mode=ro`, `stock_watch.Spine()`, writes `/root/finance/spine/stock_figure_witness_<Mon…Sun>.txt`); `stock_watch.py` c5f3ce21; `spine/spine_build.py` e3d3ed85.
- **The crontab today** (the 18-Oct 01:35 bundle's `crontab.txt`: 80 entries, 83 lines with its three blanks; S577/S583/S587 each proved the crontab unmoved by md5 since): no line tagged `# S577_WITNESS`. Neighbours at the same hour: `50 23` spine_cadence nightly, `55 23` sale_attribution build, `55 23` spine_compare, `57 23` near_expiry, **`58 23` order_rehearsal (same minute, same directory, separate files — no clash)**, `59 23` purchase_app rematch (writes finance.db; the witness's read-only connection has `timeout=60`); the spine's own build `*/10 8-23` under `flock /tmp/spine.lock` (l.66) writes `spine.db.new` then `os.replace` (spine_build 658/663), so a read at 23:58 always sees one complete file. The witness takes NO lock. The script itself: finance.db opened `mode=ro` (stock_figure 1575), the Spine read-only (stock_watch 539), output written to a temp file then `os.replace` — a same-day rerun overwrites the same weekday file harmlessly; one fail-soft stderr line may appear in the log (expected, named in the README).
- **The line, byte-exact** (S577 README l.77):
  `58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS`
- **Window 08:00–23:49 IST** by `TZ=Asia/Kolkata date +%H%M` (S577 install l.115) — one window, so the add never lands while the 23:58 run is due. The build lock. No `DOCTOR_AUTO_OFF` (no restart). **The installer runs under `set -u`, not `set -e`** (S471 l.23): every `grep -c` carries `|| true`, and every gate is an explicit test.

## 2 · The install (`install_S594_WITNESS_CRON.sh`)

Gates (window, lock, SUMS, KIT_ID) → the read-only md5s → `n=$(crontab -l 2>/dev/null | grep -c "# S577_WITNESS" || true)` must be 0 (1 → "already in — nothing to do", exit 0, say so) → **the rehearsal:** run the command itself once by hand, as the line will run it — `timeout 600 … stock_figure.py witness`, output through the kit's `mask` as S577's install l.319 does — and print its last line (`stock_figure witness written: /root/finance/spine/stock_figure_witness_<Day>.txt`), the file's size and its first ten lines; a non-zero exit or "switched off" = STOP (the switch `/root/finance/_off/ALL_OFF` must be absent); a line saying the spine is "not ready" is REPORTED, not a stop (the exit is 0 and the file is written either way) → DRY stops → **backup** `crontab -l > /root/finance/crontab.bak_S594_<stamp>`; **the backup must exist, be non-empty (`-s`), end in a newline and have the same line count as `crontab -l | wc -l` — otherwise STOP before any write** (a restore from an empty file is the one way this kit could harm the box); md5 printed → `( crontab -l; echo "$CRON_LINE" ) | crontab -` → `crontab -l | grep -c "# S577_WITNESS"` == 1 and the line byte-equal to §1's (`grep -F`) → `crontab -l | wc -l` == before + 1 and `diff <(cat crontab.bak_S594_<stamp>) <(crontab -l)` shows exactly one added line → nothing else moved (the read-only md5s again; `crontab -l | grep -v S577_WITNESS | md5sum` == the backup's md5). Red at any step after the write: `crontab /root/finance/crontab.bak_S594_<stamp>`, then prove the backup's md5 is back.

## 3 · The walk (`walk_s594.py`)

On the crontab TEXT (never the live crontab): the add is idempotent (applied twice to a copy → one line), the line parses as five fields + command, the command's program and script exist and are executable, the log directory exists, the line's tag is unique in the file. On the box, read only: `stock_figure.py witness` exits 0 and names its file (the rehearsal of §2). `--expect-red`: a copy that already holds the tag → the walk refuses to add.

## 4 · The report (`REPORT_S594.md`)

For the owner: two lines (the line is in; the first file's name and how many items it compares). For the chat: the crontab's line count before/after, the backup's path and md5, the rehearsal's output, the read-only md5s. **For the parent (the clinic project), one line:** "S594 added one line to the root crontab (`# S577_WITNESS`, 23:58 nightly, read-only; backup `/root/finance/crontab.bak_S594_<stamp>`); the first witness night is <date>; seven explained nights = 4b-2's start." Then publish, verify the clone, release the lock.

## 5 · Charter

- **Retired:** nothing. **Left:** 4b-2 itself (after the seven nights, judged by the witness files' explanations — the chat reads them at each open). **Touched outside this project's files:** the root crontab, one line, named above for the parent.
- **The tag:** the line keeps S577's tag `# S577_WITNESS` (S577 README l.77 names it; the parent's crontab record will look for that tag), not `# S594_…` — the README says so, and every grep in the kit uses that tag.
- **Dependency state at install:** S577 / S583 / S587 live (`stock_figure.py` 92367a19); `/root/finance/_off/ALL_OFF` absent; no other build holding the lock.

*S594_WITNESS_CRON brief v2 · 19-Oct-2026 · the Sanjeevni chat, session 328 · R1 in `03_WORKING_PAPERS\S328\S594_R1_REVIEW.md`.*
