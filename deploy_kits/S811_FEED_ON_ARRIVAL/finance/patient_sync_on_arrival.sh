#!/bin/bash
# patient_sync_on_arrival.sh -- kit S811_FEED_ON_ARRIVAL (session S443, 13-Nov-2026, the parent). NEW. Modelled on
# /root/wa/fu_push_on_arrival.sh (S376), which does the same for another file.
#
# WHY. The tracker on the owner's PC sends Visit_Ledger_Join.xlsx and Patient_Master_Join.xlsx into /root/wa/followup-inbox each
# evening (usually 21:10-21:25). /root/finance/finance_patient_sync.py folds them into finance.db (patient_visit, patient_ref)
# from cron "20 8-21 * * *" ONLY. On 12-Nov the workbooks landed at 21:20:58 -- after the day's last run -- so the visits waited
# until 08:20 next morning and the WhatsApp lists (which read patient_visit) were a day behind.
#
# WHAT IT DOES. Run by root's cron every 5 minutes. When either workbook is not the one the last GOOD run read (size or time
# changed; no stamp yet = new once), and neither has been written in the last 60 seconds, it runs the SAME sync the hourly line
# runs -- same interpreter, same -B, no arguments, from root's home, into the same log -- and moves the stamp only when the sync
# exits 0. finance_patient_sync.py is not changed and its hourly line stays (the backstop).
#   * never two at once: its own flock; a sync already running (the hourly one, or by hand -- any python process whose
#     arguments name finance_patient_sync.py, by whatever path; an editor that merely has the file open does not count) = this
#     tick is skipped; the hourly run's own minute (HH:20, 08-21) is left to it; the sync is stopped after 240 seconds, so a
#     21:15 run is over before 21:20.
#     (The sync takes no lock of its own and commits once at the end: two together cannot write a visit twice -- visit_id is the
#     primary key -- but the slower one would stop on an error. So they are kept apart.)
#   * nothing between 01:25 and 02:15 (the nightly backups); it catches up on the next tick after.
#   * a failed sync is tried again on a later tick, not before 15 minutes.
#   * one line per run / per skip-with-a-reason in its own log (cut back before it reaches 200 KB); a quiet tick says nothing
#     -- it only moves the log's TIME (no word added), because /root/finance/job_pulse.py reads a cron job's pulse from the
#     time of the log its line names: without that this job would read SILENT all day.
# Off switch: /root/finance/_off/ALL_OFF or /root/finance/_off/PATIENT_SYNC_ON_ARRIVAL_OFF.
# The PSOA_* names below exist for the walk (a made-up root, a stand-in sync, a set clock); cron sets none of them.
set -u
ROOT="${PSOA_ROOT:-/root}"
INBOX="${PSOA_INBOX:-$ROOT/wa/followup-inbox}"
SYNC="${PSOA_SYNC:-$ROOT/finance/finance_patient_sync.py}"
VPY="${PSOA_PY:-/root/wa/venv/bin/python3}"
SYNCLOG="${PSOA_SYNC_LOG:-$ROOT/finance/patient_sync.log}"
STAMP="${PSOA_STAMP:-$ROOT/finance/.patient_sync_on_arrival.stamp}"
FAIL="${PSOA_FAIL:-$ROOT/finance/.patient_sync_on_arrival.fail}"
LOG="${PSOA_LOG:-$ROOT/finance/patient_sync_on_arrival.log}"
LOCK="${PSOA_LOCK:-/tmp/patient_sync_on_arrival.lock}"
OFFDIR="${PSOA_OFF_DIR:-$ROOT/finance/_off}"
NOW="${PSOA_NOW:-$(date +%s)}"
SETTLE="${PSOA_SETTLE:-60}"          # seconds a workbook must have been left alone
RETRY="${PSOA_RETRY:-900}"           # seconds after a failed sync before the next try
TMO="${PSOA_TIMEOUT:-240}"           # seconds the sync may take
LOGMAX="${PSOA_LOGMAX:-150000}"      # bytes; above this the log is cut back to its last 60000
V="$INBOX/Visit_Ledger_Join.xlsx"
M="$INBOX/Patient_Master_Join.xlsx"

{ [ -e "$OFFDIR/ALL_OFF" ] || [ -e "$OFFDIR/PATIENT_SYNC_ON_ARRIVAL_OFF" ]; } && exit 0
quiet() { touch "$LOG" 2>/dev/null; exit 0; }                                           # the pulse: the log's time, no word
# the sync itself refuses without both workbooks (finance_patient_sync.py: "!! not in the inbox"), so there is nothing to start
{ [ -f "$V" ] && [ -f "$M" ]; } || quiet
SIG="$(stat -c '%n %s %Y' "$V" "$M" 2>/dev/null)"
[ -n "$SIG" ] || quiet
if [ -f "$STAMP" ] && [ "$SIG" = "$(cat "$STAMP" 2>/dev/null)" ]; then quiet; fi         # the quiet tick: nothing new

say() {
  echo "$(date -d "@$NOW" '+%F %T') $*" >> "$LOG"
  if [ "$(stat -c %s "$LOG" 2>/dev/null || echo 0)" -gt "$LOGMAX" ]; then
    tail -c 60000 "$LOG" | sed 1d > "$LOG.cut" && cat "$LOG.cut" > "$LOG"
    rm -f "$LOG.cut"
  fi
}

HM="$(date -d "@$NOW" +%H%M)"; HM=$((10#$HM))
if [ "$HM" -ge 125 ] && [ "$HM" -lt 215 ]; then say "skipped: new workbook waiting, but 01:25-02:15 is the nightly backups' time"; exit 0; fi
NEWEST=0
for f in "$V" "$M"; do
  # a time AHEAD of this clock says nothing about when the file was written here: it is left out (the other time decides)
  for t in $(stat -c '%Y %Z' "$f" 2>/dev/null); do [ "$t" -le "$NOW" ] && [ "$t" -gt "$NEWEST" ] && NEWEST="$t"; done
done
if [ $((NOW - NEWEST)) -lt "$SETTLE" ]; then say "skipped: a workbook was written less than $SETTLE seconds ago -- it may still be arriving"; exit 0; fi
if [ -f "$FAIL" ]; then
  LASTFAIL="$(head -1 "$FAIL" 2>/dev/null | tr -cd '0-9')"; LASTFAIL="${LASTFAIL:-0}"
  if [ $((NOW - LASTFAIL)) -lt "$RETRY" ] && [ $((NOW - LASTFAIL)) -ge 0 ]; then
    say "skipped: the last sync failed $(( (NOW - LASTFAIL) / 60 )) minutes ago -- the next try is $((RETRY / 60)) minutes after it"; exit 0
  fi
fi
if [ $((HM % 100)) -eq 20 ] && [ $((HM / 100)) -ge 8 ] && [ $((HM / 100)) -le 21 ]; then say "skipped: this is the hourly sync's own minute -- left to it"; exit 0; fi
( : >> "$LOCK" ) 2>/dev/null || { say "skipped: the lock file $LOCK could not be opened"; exit 0; }
exec 9>>"$LOCK"
flock -n 9 || { say "skipped: the last tick's sync is still running (lock held)"; exit 0; }
# a sync already running: a PYTHON process whose SCRIPT (its first argument that is not an option) is the sync's file,
# however it was started (cron's full path, or by hand as `cd /root/finance && python3 finance_patient_sync.py`). An editor
# with the file open, or another script that is merely given its name, is not one. This script's own name does not hold
# that name, and its own sync is started only after this look.
PAT="$(basename "$SYNC" | sed 's/\./\\./g')"
sync_running() {
  local pid arg script skip
  local -a ARGV
  for pid in $(pgrep -f -- "$PAT" 2>/dev/null); do
    [ "$pid" = "$$" ] && continue
    [ -r "/proc/$pid/cmdline" ] || continue
    mapfile -t ARGV < <(tr '\0' '\n' < "/proc/$pid/cmdline" 2>/dev/null)
    [ "${#ARGV[@]}" -ge 2 ] || continue
    case "${ARGV[0]##*/}" in python*) ;; *) continue ;; esac
    script=""; skip=0
    for arg in "${ARGV[@]:1}"; do
      if [ "$skip" = 1 ]; then skip=0; continue; fi
      case "$arg" in
        -W|-X) skip=1 ;;
        -m|-c) break ;;
        -*) ;;
        *) script="$arg"; break ;;
      esac
    done
    printf '%s\n' "$script" | grep -qE -- "(^|/)${PAT}\$" && return 0
  done
  return 1
}
if sync_running; then say "skipped: a patient sync is running already (the hourly one, or by hand)"; exit 0; fi

FIRST=""; [ -f "$STAMP" ] || FIRST=" (the first run: no stamp yet)"
printf '%s\n' "$SIG" > "$STAMP.next" || { say "skipped: the stamp could not be written beside $STAMP"; exit 0; }
( cd "$ROOT" && timeout -k 10 "$TMO" "$VPY" -B "$SYNC" >> "$SYNCLOG" 2>&1 9>&- )
RC=$?
if [ "$RC" = 0 ]; then
  mv -f "$STAMP.next" "$STAMP"
  rm -f "$FAIL"
  say "new workbook -> sync ran, exit 0$FIRST"
else
  rm -f "$STAMP.next"
  echo "$NOW" > "$FAIL"
  WHY=""; [ "$RC" = 124 ] && WHY=" (stopped after $TMO seconds)"
  say "new workbook -> sync FAILED, exit $RC$WHY -- stamp not moved; tried again after $((RETRY / 60)) minutes (see $SYNCLOG)"
fi
exit 0
