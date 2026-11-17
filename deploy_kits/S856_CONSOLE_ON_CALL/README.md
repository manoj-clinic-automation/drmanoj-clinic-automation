# S856_CONSOLE_ON_CALL — the Call Console keeps pace with the Callback Tracker (the parent, S478, 17-Nov-2026) — D997 item 2

**His word (17:10, 17-Nov):** the Call Console's figures lag the Callback Tracker's.

**Why (read, then measured live at 18:2x IST).** The tracker's calls reach its Google Sheet (tab `Call_Durations`) within a
second of hang-up: MyOperator's hook on our own server (`/root/wa/call-hook/call_hook_capture.py`) writes its raw log line,
then the row. The Call Console reads `/root/wa/console.db`, whose only writer is `/root/wa/portal_console.py --build`, run by
cron every 10 minutes (07:00–22:50, D819) from that same sheet; one build takes about 1.5 minutes. Measured: tracker 63
calls today, newest 18:22; console 62, newest 17:56, "as of 18:20"; the 18:30 reading reached the page at 18:31:4x. So the
console showed each call 1.5–11.5 minutes after the tracker. The slow leg is the console's 10-minute clock, not the sheet,
not the hook, not the page.

**The change.** One NEW file, one cron line. Nothing existing is edited.
- `/root/wa/console_kick.py` — every minute, 07:00–22:50 (`* 7-22 * * *`, the venv's python, `# S856_CONSOLE_KICK`, log
  `/root/wa/logs/console_kick.log`, a line only in a minute it acts). When the hook's raw log for today has been written
  since the console's last reading took the sheet, and has been quiet 20 seconds, it runs **the same builder** under **the
  same lock** (`/root/wa/console_cron.lock`) as the 10-minute run: `portal_console.py --build --with-myop-reconcile --days 60`
  (the 10-minute command without `--with-transcripts`: transcript and recording pulls stay on the 10-minute run; every
  build already merges the pulled transcripts from the cache). **No second copy of the calls**: console.db stays the
  builder's alone, from the sheet.
- It reads only the raw log's **modified time** (the file is never opened — it carries phone numbers) and console.db's
  `meta.built_at`; it writes only its state `/root/wa/console_kick.state.json` (last try, its result, the hook time it
  covered). The build's own output goes to the 10-minute run's log, so the freshness leg *call console cron* is unchanged.
- Guards: the shared lock (a reading running now → this minute does nothing); **the minutes :X7–:X0 are left to
  the 10-minute run** (its `flock -n` gives up silently on a busy lock, so a kick there would cost it that run and its
  transcript pull — the cold review's MUST); **at most 6 kicks in any hour** (each build runs the MyOperator reconcile);
  never within 2 minutes of the last reading; a call it already read is not built again; a failed build waits 10 minutes
  (the 10-minute run is the floor); one build is stopped after 9 minutes. Off: create `/root/wa/console_kick.OFF`
  (the installer also holds it off this way while it writes and reads back the crontab).
- **Result:** a call reaches the console about 2–4 minutes after hang-up (20 s quiet + the next minute + ~1.5 min build),
  instead of 1.5–11.5 (a call in :X7–:X0, or past the hour's 6 kicks, is read by the 10-minute run as today). Calls
  between 22:50 and 07:00 still wait for 07:00, as D819 set. The freshness leg *call console cron* reads only the log's time.

**Install (one line on the server):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s856kit && cp -rp /root/deploy/repo/deploy_kits/S856_CONSOLE_ON_CALL /tmp/s856kit && bash /tmp/s856kit/install_S856_CONSOLE_ON_CALL.sh`
Undo: `bash /tmp/s856kit/install_S856_CONSOLE_ON_CALL.sh --undo`. `DRY=1` before `bash`: every gate, nothing written.

**Proof:** `walk_s856.py` on a made-up root (35 checks: the window and 22:51, the measured 18:22 case, settle, gap, a call
already read, the shared lock held by `flock(1)` as cron holds it, a failed and a hanging build, no reading, the off switch,
the raw log never opened (whole file checked), the command and lock the 10-minute run's own, the probe writes nothing and
reads the reading time at any hour, the :X7–:X0 yield, the hourly cap, a quiet minute writes nothing) and `--control` (six
broken copies go red: the old world, no lock, no settle, no window, no yield, no cap). Cold review: NOT SAFE (1 MUST, 3
SHOULD, 3 LOW) → all built in → second look SAFE TO INSTALL (3 LOW → built in: :X7 yielded too; an interrupted
install takes its hold-off switch away on exit; wording). The installer runs both on the box, then a read-only
probe on the live paths, before anything is placed; the crontab is changed only from a good read and read back.
No page is changed (F-1445 does not apply); no service restarts.
