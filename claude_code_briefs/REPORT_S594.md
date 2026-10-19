# REPORT S594_WITNESS_CRON — installed 19-Oct-2026, 08:27 IST

## For the owner

1. **The nightly line is in.** From tonight, at 23:58 every night, the server writes the stock figure's side-by-side file: the new figure against the old ones, item by item, with the reason for each difference. Seven such nights, each explained, is the condition for retiring the old figures.
2. **It was run once by hand first, exactly as the schedule will run it:** it wrote `stock_figure_witness_Mon.txt` (99,410 bytes) comparing **384 items** of the newest usable closing (printed 16-10, taken 17-10 09:20). Nothing else on the server changed, no screen moves, no program was restarted; the finance service answers as before (healthz 200).

## For the parent (the clinic project — the crontab is its record)

S594 added one line to the root crontab (`# S577_WITNESS`, 23:58 nightly, read-only; backup `/root/finance/crontab.bak_S594_20261019_082748`); the first witness night is **19-10-2026**; seven explained nights = 4b-2's start.

## For the chat

### The crontab, before → after (read back on the box after the write, 08:27:49 IST)

| | lines | entries | md5 of `crontab -l` | `# S577_WITNESS` lines |
|---|---|---|---|---|
| before (= the 18-Oct 01:35 bundle's `crontab.txt`) | 83 | 80 | 684fe2fd5f92d1217c7689010fca5831 | 0 |
| after | 84 | 81 | 3ee614054065aedf0c9f28903c8cee6a | 1 |

The line, byte-equal to the brief's §1 (`grep -Fx` found it once):
```
58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS
```
`diff backup <(crontab -l)` = exactly the one added line (`83a84 > …`); `crontab -l | grep -vF '# S577_WITNESS' | md5sum` = the backup's md5 684fe2fd. The crontab was unmoved between the brief and the write (md5 684fe2fd at 08:20 and at 08:27).

### The backup

`/root/finance/crontab.bak_S594_20261019_082748` — 10,925 bytes, 83 lines, md5 **684fe2fd5f92d1217c7689010fca5831** (= `crontab -l` before the write), ends in a newline, mode 600. Proved non-empty, same line count and same md5 BEFORE the write (R1's blocker 2). Undo: `crontab /root/finance/crontab.bak_S594_20261019_082748`, then `crontab -l | md5sum` must read 684fe2fd….

### The read-only md5s (STOP if moved) — exact at the open (08:20), at the gate (08:27) and read back after the write

| file | md5 |
|---|---|
| `/root/finance/stock_figure.py` | 92367a196b360f0cded4cda6a5ded700 |
| `/root/finance/stock_watch.py` | c5f3ce21a785c45df58f21932cf920e7 |
| `/root/finance/spine/spine_build.py` | e3d3ed85973eab2df0326dc9621e230e |

### The rehearsal (the command run once by hand as the line will run it; the walk's section 6, 08:27:00 DRY and 08:27:48 real — read only)

```
stock_figure: start capture 6d718060 (2026-10-18T09:37:08) stays pending: attempt to write a readonly database
stock_figure witness written: /root/finance/spine/stock_figure_witness_Mon.txt
```
exit 0 · the file 99,410 bytes · 384 items compared · `marg() vs expected_units, a pack or more apart: 20` · `marg() vs the PC's push, a pack or more apart: 165` · `marg_shadow lines a pack or more apart (server vs PC): 110`. Its first lines:
```
stock_figure witness  2026-10-19T08:27:48 IST  (kit S587_MORNING_FLOW; the old ways run beside the new for one week -- 4b-2 retires them)
newest usable capture: printed 2026-10-16, taken 2026-10-17T09:20:35, stands for the end of 2026-10-16 (7f4d5832)
PC's newest push_expected: day 17-10-2026, received 2026-10-18T22:30:11, 395 items · marg_shadow's newest run: as on 17-10-2026, 118 lines

item                               marg()   expected    PC push     shadow   closing / reason
ACILOC 300                              0          0         62          -   closing 2026-10-16 name · closing days differ: 2026-10-16 by name vs 2026-10-18 by sp_close
```
The first stderr line is the one fail-soft line the brief foresaw (§1): the witness's `mode=ro` connection meets S587's start-capture judge, which wants to write the 18-10 09:37 capture's verdict; the capture stays pending in that run and the file is written all the same. It will appear in `stock_figure_witness.log` each night while a start capture is pending. Not this kit's to change — a finding for the chat.

### The walk on the box (08:27:48 run)

`WALK OK S594_WITNESS_CRON: 25 checks green (the crontab text 83 -> 84 lines, the add idempotent, the line parses, program/script/folders present, the rehearsal wrote its file); 1 note(s)` — the copy ends in a newline; the add once (83 → 84, one tagged line, the rest byte for byte), twice (refused: one line); five fields + command, `58 23 * * *`, the command parses, the program `/root/wa/venv/bin/python3` executable, `/root/finance/stock_figure.py` readable, `/root/finance` and `/root/finance/spine` present; the tag unique; no other line writes to the witness log; the one other line at `58 23` (S341_ORDER_REHEARSAL) writes elsewhere.

**Negative control:** `WALK OK negative control S594_WITNESS_CRON: the walk refuses to add -- the copy already holds '# S577_WITNESS' (1 line(s), 84 lines in all)`; and on the plain copy the control itself goes red (`NOT RED`, exit 1). Locally (Windows, python 3.14, synthetic crontab text) the same walk went red on: a copy without a trailing newline, a copy where another line writes the witness log, a missing script; and exit 2 (refused) on a tagged copy in normal mode.

### Gates at install

Window 08:27 IST (08:00–23:49); the build lock free, taken 08:27:48 by S594; SUMS and KIT_ID; the walk's line = the installer's; `walk_s594.py` compiles on `/usr/bin/python3` and `/root/wa/venv/bin/python3` (both 3.9.25); `/root/finance/_off/ALL_OFF` absent; the spine passed 13/13, last success 08:20:44 IST (charter 1b); the idempotence gate 0.

### Two runs, said plainly

- **08:27:00 DRY run** (`DRY=1`, nothing written): every gate, the walk (25 green) and the negative control green; then my installer stopped itself at its own last check before the DRY exit — `grep -q "switched off"` matched the walk's check label *"6.2 not switched off"*, not the script's message. The crontab was untouched (md5 684fe2fd, 83 lines, lock released). I changed that one grep to the script's exact message `stock_figure: switched off`, added the fail-soft line to the README, regenerated SUMS, re-ran the number gate, re-copied the kit.
- **08:27:48 real run:** green end to end; the kit in the repository is the one that ran (SUMS checked on the box before the run; the clone verified after the publish, below).

### Backups, restarts, lock

- Backup: `/root/finance/crontab.bak_S594_20261019_082748` (above). No database backup: no data step, finance.db opened read-only by the rehearsal only.
- Restarts: **none.** `clinic-finance` untouched (healthz 200 before and after).
- The build lock `/root/deploy/.claude_code_build.lock` taken 08:27:48 by S594, released after this report. `/tmp/s594kit`, `/tmp/s594probe`, the scratch `/tmp/s594_inst_*` removed.

### Not done, and findings outside the brief

- **Not done:** nothing of the brief. No `DUTY_MAP` change (no staff duty added, moved or removed; no login affected — no staff-eye walk).
- **Finding (above):** the witness's read-only run prints S587's *"start capture … stays pending: attempt to write a readonly database"* while a start capture is pending. Fail-soft, exit 0, the file written. For the chat's register.
- **Finding:** the witness file's header still says `kit S587_MORNING_FLOW` (the module's `KIT` constant moved with S587). Cosmetic.
- **Finding:** `/root/finance/spine/stock_figure_witness.log` does not exist yet; the shell creates it at the first 23:58 run. The 23:58 run's stdout/stderr (the fail-soft line and the "written" line) will accumulate there with no rotation — one or two lines a night.
- **Permissions:** nothing refused.

### Charter

- **Retired:** nothing. **Left:** 4b-2 itself (after the seven nights, judged by the witness files' explanations — the chat reads them at each open).
- **Touched outside this project's files:** the root crontab, one line (named above for the parent).
- **Dependency state at install:** S577 / S583 / S587 live (`stock_figure.py` 92367a19); `ALL_OFF` absent; the spine 13/13, 7 minutes old; no other build holding the lock.
- **Charter: left out / seen, not touched:** nothing left out; the two findings above are seen, not touched.
