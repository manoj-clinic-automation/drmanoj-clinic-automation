# S830_ATT_SILENCE_ALERT — the attendance machine's silence is told to the owner (the parent, S460, 14-Nov-2026) — F-1402

**The gap.** From 13-Nov 11:17 to 14-Nov 11:44 IST no punch reached the server and nothing told anyone: the machine's clock had
frozen, then it shut itself down. The freshness page watches the punch *file* with a 74-hour window; `att_doctor.py` fires only
at 14:00 on a day with zero punches; nothing looked at the time since the machine last called.

**What the S458 note assumed and the code does not give.** `/root/attlistener_sources.jsonl` records every punch but only the
first 30 *other* calls of each day per address (`SRC_OTHER_PER_DAY`), so after the first minutes of the day it cannot show the
machine's calls; and the listener's own read count (`/proc/<pid>/io`) does not count socket reads. The watcher therefore looks
for the machine's connections in the kernel's tables -- `/proc/net/nf_conntrack` (a closed connection stays about two minutes)
and `/proc/net/tcp`, `tcp6` -- **from the machine's own address only**, learnt from the source log (its punches and its own
calls, which carry a `request_code`) and kept in the state; any other caller is never the machine. **Silence is judged only once
the box has shown it can see those connections** (the first sighting is kept as `conn_seen_iso`); until then the 10:00 rule
and the clock rule work alone, and the log line says so. `/root/attlistener_v2.py` is NOT touched (D247).

**The change.** One NEW file, one cron line, one leg.
- `/root/att_silence_watch.py` — every 5 minutes (`*/5 * * * *`, the venv's python, `# S830_ATT_SILENCE_WATCH`, log
  `/root/att_silence_watch.log`, cut back past 200 KB; a line only when something changes):
  - Monday–Saturday inside clinic hours (earliest start to latest end of the active staff's weekday shifts, clamped to
    08:00–11:00 / 17:00–22:00; 10:00–20:00 when unreadable), from 30 minutes after the start: **no contact for 30 minutes → one
    message**; **contact again → one message**; three silences a day at most, then only the console;
  - **no punch received by 10:00 (or 30 minutes after the earliest start, if later) on a working day → one message** (it stands for the silence too; a silence that goes on into the
    next working day is told again once, at 10:00);
  - **the clock** (S792's column): a punch today stored more than 5 minutes from its machine time, or two punches 2+ minutes
    apart with one machine time → one message a day;
  - the portal's own Web Push to the owner (`ring_common.push_user`, as S811), the ntfy topic when no device takes it; three
    tries a day at most, each counted before it is made;
  - its state `/root/att_silence_watch.state.json` carries `last_ok_iso` / `last_failure_iso`.
- **The console line:** the leg *attendance machine contact* (group Attendance; `state_json`, `fail_field`, 1 hour) in the
  freshness legs file (the conf's `LEGS_FILE`) — red while the machine is silent in hours or no punch has come by 10:00, and red
  if the watcher stops. Added by `legs_s830.py` only when the file re-dumps to its own bytes.
- **Told twice, knowingly:** while the leg is red, `freshness.py --shout` (hourly at :35) also sends its own once-a-day ntfy line
  for it, as it does for every red leg; a closed weekday (no holiday list) and the off switch also turn it red.
- Off: `/root/finance/_off/ALL_OFF` or `/root/finance/_off/ATT_SILENCE_OFF`.

**Install (one line on the server):**
`cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s830kit && cp -rp /root/deploy/repo/deploy_kits/S830_ATT_SILENCE_ALERT /tmp/s830kit && bash /tmp/s830kit/install_S830_ATT_SILENCE_ALERT.sh`
Undo: `bash /tmp/s830kit/install_S830_ATT_SILENCE_ALERT.sh --undo`. `DRY=1` before `bash`: every gate, nothing written.

**Proof:** `walk_s830.py` on a made-up root (62 checks) and `--control` (three broken copies go red: silence at 300 min, the 10:00 message told twice, a stray address taken for the machine); the installer runs both on
the box before placing anything, and the probe stops it if the listener process or the punch file cannot be read.
