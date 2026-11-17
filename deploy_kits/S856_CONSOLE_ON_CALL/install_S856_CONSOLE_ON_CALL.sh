#!/bin/bash
# =============================================================================
#  install_S856_CONSOLE_ON_CALL.sh . kit S856 (17-Nov-2026, session S478, the parent) . D997 item 2
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s856kit && cp -rp /root/deploy/repo/deploy_kits/S856_CONSOLE_ON_CALL /tmp/s856kit && bash /tmp/s856kit/install_S856_CONSOLE_ON_CALL.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s856kit/install_S856_CONSOLE_ON_CALL.sh --undo
#
#  ONE NEW file /root/wa/console_kick.py + ONE cron line (every minute, 07-22). The Call Console is rebuilt by its own
#  builder, under its own lock, ~20 s after each call the call hook logs -- instead of waiting up to 10 minutes.
#  portal_console.py, call_hook_capture.py, console.db's shape and the 10-minute line are NOT touched; no service restarts.
#  The crontab is edited only from a good read of it, never written if a line that is not this kit's would be lost,
#  and read back. If anything is red after placing, everything goes back.
# =============================================================================
set -u
KIT="S856_CONSOLE_ON_CALL"
TAG="# S856_CONSOLE_KICK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-$ROOT/s856_backup}"
N1="$ROOT/wa/console_kick.py"; PIN1=7e70753ead43c6a1915aec5db7f458d6
WALK_OK="WALK OK 35/35"
BUILDER="$ROOT/wa/portal_console.py"
RAWDIR="$ROOT/wa/call-hook/call_hook_logs"
CDB="$ROOT/wa/console.db"
LOGF="$ROOT/wa/logs/console_kick.log"
STATEF="$ROOT/wa/console_kick.state.json"
OFFF="$ROOT/wa/console_kick.OFF"; MADE_OFF=0
LINE="* 7-22 * * * $VPY -B $N1 >> $LOGF 2>&1 $TAG"
TEN_MIN="/root/wa/console_cron.lock /root/wa/venv/bin/python3 /root/wa/portal_console.py --build --with-myop-reconcile --with-transcripts --days 60"
OWN="$STATEF $STATEF.tmp $LOGF"
SCR=""; HAVE_LOCK=0; PLACED1=0; CRON_CHANGED=0; ORIG=""; KEEP=""; BACK_OK=0
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
on_exit() { [ "$MADE_OFF" = 1 ] && rm -f "$OFFF"; [ -n "$SCR" ] && rm -rf "$SCR"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
read_cron() { "$CRONTAB" -l > "$1" 2>/dev/null || return 1; [ -s "$1" ] || return 1; [ -z "$(tail -c1 "$1")" ] || return 1; return 0; }
G() { LC_ALL=C grep -a "$@"; }
OURS_RE="${TAG}[[:space:]]*\$"
n_ours() { G -c -E -- "$OURS_RE" "$1"; }
n_lines() { G -c '' "$1"; }
strip_ours() { G -v -E -- "$OURS_RE" "$1"; }
keeps_all() { [ "$(n_lines "$2")" = "$(( $(n_lines "$1") - $(n_ours "$1") + $3 ))" ] && [ "$(strip_ours "$1" | md5sum)" = "$(strip_ours "$2" | md5sum)" ]; }
back() {
  local ok=1
  if [ "$CRON_CHANGED" = 1 ]; then
    "$CRONTAB" - < "$BK/crontab.before_S856" 2>/dev/null
    if read_cron "$SCR/ct.back" && [ "$(m5 "$SCR/ct.back")" = "$ORIG" ]; then echo "   the crontab is back as it was, byte for byte (md5 ${ORIG:0:8})"
    else ok=0; echo "   !! THE CRONTAB DID NOT GO BACK -- its copy from before is kept at $BK/crontab.before_S856"; fi
  fi
  [ "$PLACED1" = 1 ] && rm -f "$N1" "$N1.s856new"
  [ "$MADE_OFF" = 1 ] && rm -f "$OFFF"
  for f in $OWN; do case " $KEEP " in *" $f "*) ;; *) rm -f "$f";; esac; done
  { [ -e "$N1" ] && [ "$PLACED1" = 1 ]; } && ok=0
  if [ "$ok" = 1 ]; then rm -f "$BK/crontab.before_S856"; rmdir "$BK" 2>/dev/null; echo "   the new file was taken out again"; fi
  BACK_OK=$ok; return 0
}
red() {
  echo "!! RED after placing: $1"; back; echo "!! STOPPED: $1"
  if [ "$BACK_OK" = 1 ]; then echo "   Everything this kit placed was taken out again; the box is as it was before. Send a photo of this screen to Claude."
  else echo "   NOT EVERYTHING WENT BACK -- read the !! line above. Send a photo of this screen to Claude."; fi
  exit 1
}

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 console_kick.py)" = "$PIN1" ] || stop "the kit's console_kick.py is not the built one"
SCR=$(mktemp -d /tmp/s856.XXXX) || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"

if [ "${1:-}" = "--undo" ]; then
  [ "${DRY:-0}" = 1 ] && stop "DRY=1 and --undo were given together -- nothing done"
  read_cron "$SCR/ct" || stop "root's crontab could not be read -- nothing undone"
  [ -e "$N1" ] && [ "$(m5 "$N1")" != "$PIN1" ] && stop "$N1 has been changed since this kit (a later kit is on top) -- not undone"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1; echo "$KIT undo $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  strip_ours "$SCR/ct" > "$SCR/ct.want"
  if [ "$(m5 "$SCR/ct.want")" != "$(m5 "$SCR/ct")" ]; then
    keeps_all "$SCR/ct" "$SCR/ct.want" 0 || stop "the new crontab would lose a line that is not this kit's -- not undone"
    "$CRONTAB" - < "$SCR/ct.want" || stop "the crontab could not be written -- not undone"
    read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || stop "the crontab did not read back as written" "Look at the crontab before anything else."
  fi
  rm -f "$N1" "$N1.s856new" $OWN "$BK/crontab.before_S856"; rmdir "$BK" 2>/dev/null
  [ -e "$N1" ] && { echo "!! the file is still there -- send a photo"; exit 1; }
  echo "UNDONE: the S856 cron line and $N1 are out. The Call Console is read every 10 minutes again, as before."
  exit 0
fi

echo "[1/6] kit files: all match SUMS.md5; the watcher is the built one (${PIN1:0:8})"
read_cron "$SCR/ct" || stop "root's crontab could not be read (crontab -l gave nothing usable) -- it is never edited from a bad read"
ORIG=$(m5 "$SCR/ct")
if [ "$(m5 "$N1")" = "$PIN1" ] && [ "$(n_ours "$SCR/ct")" = 1 ]; then
  echo "-- ALREADY INSTALLED (the watcher and its cron line are there). Nothing written."; exit 0
fi
for t in timeout md5sum mktemp sed flock; do command -v "$t" >/dev/null 2>&1 || stop "the box has no '$t'"; done
"$VPY" -c "import json, fcntl, sqlite3" 2>/dev/null || stop "$VPY does not run"
[ -e "$N1" ] && [ "$(m5 "$N1")" != "$PIN1" ] && stop "$N1 is there and is not this kit's"
[ "$(n_ours "$SCR/ct")" = 0 ] || [ "$(n_ours "$SCR/ct")" = 1 ] || stop "the crontab carries this kit's tag more than once"
[ -f "$BUILDER" ] || stop "$BUILDER is not on the box"
[ -d "$RAWDIR" ] || stop "the call hook's raw log folder $RAWDIR is not on the box"
[ "$(G -c -F -- "$TEN_MIN" "$SCR/ct")" = 1 ] || stop "the 10-minute console line is not in the crontab exactly as this kit expects (its lock and command) -- the kick would not share its lock"
"$VPY" -B -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$KDIR/console_kick.py" 2>/dev/null || stop "console_kick.py does not compile with $VPY"
P=$(cd "$SCR" && CK_STATE="$SCR/probe_state.json" timeout 60 "$VPY" -B "$KDIR/console_kick.py" --probe 2>&1 | tail -1)
case "$P" in "PROBE "*) ;; *) stop "the watcher's probe did not answer as expected (${P:0:160})";; esac
case "$P" in *" reading=none"*) [ -f "$CDB" ] && stop "console.db is on the box but its reading time could not be read ($P)";; esac
echo "[2/6] the box: the builder, the hook's log folder and the 10-minute line (its lock) are there"
echo "      $P"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s856.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s856.py" "$KDIR" 2>&1 | grep -E '^BAD|Error' | cut -c1-300 | head -6); stop "the walk is not green on this box ($R)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s856.py" "$KDIR" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control (six broken copies) did not go red ($R2)";; esac
echo "[3/6] the walk on this box (a made-up root): $R | $R2"
{ [ "${DRY:-0}" = 1 ] || [ "${1:-}" = "--dry" ]; } && { echo "DRY=1: every gate green; nothing written."; exit 0; }

mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
read_cron "$SCR/ct2" && [ "$(m5 "$SCR/ct2")" = "$ORIG" ] || stop "the crontab changed (or could not be read) while this kit was checking -- run the line again"
for f in $OWN; do [ -e "$f" ] && KEEP="$KEEP $f"; done
mkdir -p "$BK" && chmod 700 "$BK" && \cp -f "$SCR/ct" "$BK/crontab.before_S856" && [ "$(m5 "$BK/crontab.before_S856")" = "$ORIG" ] || stop "could not keep a copy of the crontab in $BK"
chmod 600 "$BK/crontab.before_S856"
[ -e "$N1" ] || PLACED1=1
\cp -f "$KDIR/console_kick.py" "$N1.s856new" && mv -f "$N1.s856new" "$N1" && [ "$(m5 "$N1")" = "$PIN1" ] || red "console_kick.py did not land byte-exact"
chmod 644 "$N1"
P2=$(cd "$SCR" && timeout 60 "$VPY" -B "$N1" --probe 2>&1 | tail -1)
case "$P2" in "PROBE "*) ;; *) red "the placed watcher's probe did not answer as expected (${P2:0:160})";; esac
echo "[4/6] placed $N1 (${PIN1:0:8}); its probe answers"

{ strip_ours "$SCR/ct"; echo "$LINE"; } > "$SCR/ct.want"
keeps_all "$SCR/ct" "$SCR/ct.want" 1 || red "the new crontab would lose a line that is not this kit's -- not written"
# the watcher is held off (its own switch) while the crontab is written and read back, so a red can never race a first run
[ -e "$OFFF" ] || { : > "$OFFF" && MADE_OFF=1; } || red "the hold-off switch $OFFF could not be made"
CRON_CHANGED=1
"$CRONTAB" - < "$SCR/ct.want" || red "the crontab could not be written"
read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || red "the crontab did not read back as written"
[ "$(n_ours "$SCR/ct.now")" = 1 ] || red "the cron line is not there exactly once"
[ "$(G -c -F -- "$TEN_MIN" "$SCR/ct.now")" = 1 ] || red "the 10-minute console line is no longer in the crontab"
if [ "$MADE_OFF" = 1 ]; then rm -f "$OFFF" && MADE_OFF=0 || red "the hold-off switch $OFFF could not be taken away"; fi
[ -e "$OFFF" ] && echo "NOTE: $OFFF was already there before this kit and is left in place -- the watcher stays off until it is removed."
echo "[5/6] one cron line added (every minute, 07-22), read back; every other line kept ($(n_lines "$SCR/ct") lines before, $(n_lines "$SCR/ct.now") now)"
echo "[6/6] what it sees now: ${P2#PROBE }"
echo ""
echo "$KIT: DONE. From the next minute the Call Console is rebuilt about 20 seconds after each call ends (between 07:00 and 22:50), so it keeps pace with the Callback Tracker; the 10-minute reading stays underneath, unchanged."
