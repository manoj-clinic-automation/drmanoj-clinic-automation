#!/bin/bash
# =============================================================================
#  install_S843_XRAY_DAY_MESSAGES.sh . kit S843 (14-Nov-2026, session S469, the parent) . D979 item 6
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s843kit && cp -rp /root/deploy/repo/deploy_kits/S843_XRAY_DAY_MESSAGES /tmp/s843kit && bash /tmp/s843kit/install_S843_XRAY_DAY_MESSAGES.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s843kit/install_S843_XRAY_DAY_MESSAGES.sh --undo
#
#  ONE NEW file /root/finance/xray_day_messages.py + TWO cron lines (09:30 morning, 19:00 evening). No other file is touched,
#  no service is restarted. The crontab is edited only from a good read of it, never written if a line that is not this kit's
#  would be lost, and read back. If anything is red after placing, everything goes back.
# =============================================================================
set -u
KIT="S843_XRAY_DAY_MESSAGES"
TAG="# S843_XRAY_DAY_MESSAGES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-$ROOT/s843_backup}"
FIN="$ROOT/finance"
DBF="${FINANCE_DB:-$FIN/finance.db}"
N1="$FIN/xray_day_messages.py"; PIN1=63073eefd6a2d055d750bb52b2a9edd2
WALK_OK="WALK OK 42/42"
LOGF="$FIN/xray_day_messages.log"
STATEF="$FIN/xray_day_messages_state.json"
L1="30 9 * * * $VPY -B $N1 morning >> $LOGF 2>&1 $TAG"
L2="0 19 * * * $VPY -B $N1 evening >> $LOGF 2>&1 $TAG"
OWN="$STATEF $STATEF.tmp $LOGF"
SCR=""; HAVE_LOCK=0; PLACED1=0; CRON_CHANGED=0; ORIG=""; KEEP=""; BACK_OK=0
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
on_exit() { [ -n "$SCR" ] && rm -rf "$SCR"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
read_cron() { "$CRONTAB" -l > "$1" 2>/dev/null || return 1; [ -s "$1" ] || return 1; [ -z "$(tail -c1 "$1")" ] || return 1; return 0; }
G() { LC_ALL=C grep -a "$@"; }
OURS_RE="${TAG}[[:space:]]*\$"
n_ours() { G -c -E -- "$OURS_RE" "$1"; }
n_lines() { G -c '' "$1"; }
strip_ours() { G -v -E -- "$OURS_RE" "$1"; }
keeps_all() { [ "$(n_lines "$2")" = "$(( $(n_lines "$1") - $(n_ours "$1") + $3 ))" ] && [ "$(strip_ours "$1" | md5sum)" = "$(strip_ours "$2" | md5sum)" ]; }
dry() { (cd "$SCR" && XD_FIN_DIR="$FIN" FINANCE_DB="$DBF" XD_STATE="$SCR/dry_state.json" timeout 120 "$VPY" -W ignore -B "$1" "$2" --dry 2>&1); }
back() {
  local ok=1
  if [ "$CRON_CHANGED" = 1 ]; then
    "$CRONTAB" - < "$BK/crontab.before_S843" 2>/dev/null
    if read_cron "$SCR/ct.back" && [ "$(m5 "$SCR/ct.back")" = "$ORIG" ]; then echo "   the crontab is back as it was, byte for byte (md5 ${ORIG:0:8})"
    else ok=0; echo "   !! THE CRONTAB DID NOT GO BACK -- its copy from before is kept at $BK/crontab.before_S843"; fi
  fi
  [ "$PLACED1" = 1 ] && rm -f "$N1" "$N1.s843new"
  for f in $OWN; do case " $KEEP " in *" $f "*) ;; *) rm -f "$f";; esac; done
  { [ -e "$N1" ] && [ "$PLACED1" = 1 ]; } && ok=0
  if [ "$ok" = 1 ]; then rm -f "$BK/crontab.before_S843"; rmdir "$BK" 2>/dev/null; echo "   the new file was taken out again"; fi
  BACK_OK=$ok; return 0
}
red() {
  trap '' INT TERM HUP
  echo "!! RED after placing: $1"; back; echo "!! STOPPED: $1"
  if [ "$BACK_OK" = 1 ]; then echo "   Everything this kit placed was taken out again; the box is as it was before. Send a photo of this screen to Claude."
  else echo "   NOT EVERYTHING WENT BACK -- read the !! line above. Send a photo of this screen to Claude."; fi
  exit 1
}

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 xray_day_messages.py)" = "$PIN1" ] || stop "the kit's xray_day_messages.py is not the built one"
SCR=$(mktemp -d /tmp/s843.XXXX) || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"

if [ "${1:-}" = "--undo" ]; then
  [ "${DRY:-0}" = 1 ] && stop "DRY=1 and --undo were given together -- nothing done"
  read_cron "$SCR/ct" || stop "root's crontab could not be read -- nothing undone"
  [ -e "$N1" ] && [ "$(m5 "$N1")" != "$PIN1" ] && stop "$N1 has been changed since this kit (a later kit is on top) -- not undone"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1; echo "$KIT undo $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  read_cron "$SCR/ct" || stop "root's crontab could not be read under the lock -- nothing undone"
  mkdir -p "$BK" && chmod 700 "$BK" && \cp -f "$SCR/ct" "$BK/crontab.before_S843_undo" && chmod 600 "$BK/crontab.before_S843_undo" || stop "could not keep a copy of the crontab in $BK -- nothing undone"
  strip_ours "$SCR/ct" > "$SCR/ct.want"
  if [ "$(m5 "$SCR/ct.want")" != "$(m5 "$SCR/ct")" ]; then
    keeps_all "$SCR/ct" "$SCR/ct.want" 0 || stop "the new crontab would lose a line that is not this kit's -- not undone"
    "$CRONTAB" - < "$SCR/ct.want" || stop "the crontab could not be written -- not undone"
    if [ -s "$SCR/ct.want" ]; then
      read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || stop "the crontab did not read back as written" "Look at the crontab before anything else (its copy: $BK/crontab.before_S843_undo)."
    else
      [ "$("$CRONTAB" -l 2>/dev/null | wc -c)" = 0 ] || stop "the crontab did not read back empty" "Look at the crontab before anything else (its copy: $BK/crontab.before_S843_undo)."
    fi
  fi
  rm -f "$N1" "$N1.s843new" $OWN "$BK/crontab.before_S843"
  [ -e "$N1" ] && { echo "!! the file is still there -- send a photo"; exit 1; }
  echo "UNDONE: the two S843 cron lines and xray_day_messages.py are out (the crontab as it was: $BK/crontab.before_S843_undo). The 3 pm / 6 pm notice was never touched."
  exit 0
fi

echo "[1/5] kit files: all match SUMS.md5; the messages file is the built one (${PIN1:0:8})"
read_cron "$SCR/ct" || stop "root's crontab could not be read (crontab -l gave nothing usable) -- it is never edited from a bad read"
ORIG=$(m5 "$SCR/ct")
if [ "$(m5 "$N1")" = "$PIN1" ] && [ "$(n_ours "$SCR/ct")" = 2 ] && [ "$(G -c -F -x -- "$L1" "$SCR/ct")" = 1 ] && [ "$(G -c -F -x -- "$L2" "$SCR/ct")" = 1 ]; then
  echo "-- ALREADY INSTALLED (the file and its two cron lines are there). Nothing written."; exit 0
fi
for t in timeout md5sum mktemp; do command -v "$t" >/dev/null 2>&1 || stop "the box has no '$t'"; done
"$VPY" -c "import json, sqlite3" 2>/dev/null || stop "$VPY does not run"
[ -e "$N1" ] && [ "$(m5 "$N1")" != "$PIN1" ] && stop "$N1 is there and is not this kit's"
case "$(n_ours "$SCR/ct")" in 0|1|2) ;; *) stop "the crontab carries this kit's tag more than twice";; esac
[ -f "$DBF" ] || stop "the database $DBF is not on the box"
[ -f "$FIN/check_screens.py" ] && [ -f "$FIN/records.py" ] || stop "check_screens.py / records.py are not in $FIN"
"$VPY" -B -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$KDIR/xray_day_messages.py" 2>/dev/null || stop "xray_day_messages.py does not compile with $VPY"
( cd "$SCR" && "$VPY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import ring_common as rc; assert callable(rc.push_user)" "$ROOT/portal" 2>/dev/null ) || stop "the portal's own push (ring_common.push_user) could not be loaded with $VPY"
echo "[2/5] the box: the venv runs, the database and check_screens / records are there, the push loads"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s843.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s843.py" "$KDIR" 2>&1 | grep -E '^BAD|Error' | cut -c1-300 | head -6); stop "the walk is not green on this box ($R)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s843.py" "$KDIR" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red 5/5") ;; *) stop "the control (five broken copies) did not go red ($R2)";; esac
DM=$(dry "$KDIR/xray_day_messages.py" morning); DE=$(dry "$KDIR/xray_day_messages.py" evening)
case "$DM" in "DRY "*) ;; *) stop "the morning dry run on the live database did not answer as expected ($(echo "$DM" | tail -1 | cut -c1-160))";; esac
case "$DE" in "DRY "*) ;; *) stop "the evening dry run on the live database did not answer as expected ($(echo "$DE" | tail -1 | cut -c1-160))";; esac
echo "[3/5] the walk on this box (made-up data): $R | $R2; both dry runs read the live database (read-only)"
{ [ "${DRY:-0}" = 1 ] || [ "${1:-}" = "--dry" ]; } && { echo "DRY=1: every gate green; nothing written."; echo "$DM"; echo "$DE"; exit 0; }

mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
read_cron "$SCR/ct2" && [ "$(m5 "$SCR/ct2")" = "$ORIG" ] || stop "the crontab changed (or could not be read) while this kit was checking -- run the line again"
for f in $OWN; do [ -e "$f" ] && KEEP="$KEEP $f"; done
mkdir -p "$BK" && chmod 700 "$BK" && \cp -f "$SCR/ct" "$BK/crontab.before_S843" && [ "$(m5 "$BK/crontab.before_S843")" = "$ORIG" ] || stop "could not keep a copy of the crontab in $BK"
chmod 600 "$BK/crontab.before_S843"
trap 'red "interrupted (Ctrl-C or the session closed)"' INT TERM HUP
[ -e "$N1" ] || PLACED1=1
\cp -f "$KDIR/xray_day_messages.py" "$N1.s843new" && mv -f "$N1.s843new" "$N1" && [ "$(m5 "$N1")" = "$PIN1" ] || red "xray_day_messages.py did not land byte-exact"
chmod 644 "$N1"
echo "[4/5] placed $N1 (${PIN1:0:8})"
{ strip_ours "$SCR/ct"; echo "$L1"; echo "$L2"; } > "$SCR/ct.want"
keeps_all "$SCR/ct" "$SCR/ct.want" 2 || red "the new crontab would lose a line that is not this kit's -- not written"
CRON_CHANGED=1
"$CRONTAB" - < "$SCR/ct.want" || red "the crontab could not be written"
read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || red "the crontab did not read back as written"
[ "$(n_ours "$SCR/ct.now")" = 2 ] || red "the two cron lines are not there exactly once each"
D=$(dry "$N1" evening | head -1)
case "$D" in "DRY "*) ;; *) red "the placed file's dry run did not answer as expected (${D:0:160})";; esac
trap - INT TERM HUP
echo "[5/5] two cron lines added (09:30 morning, 19:00 evening), read back; every other line kept ($(n_lines "$SCR/ct") lines before, $(n_lines "$SCR/ct.now") now)"
echo ""
echo "What tonight's evening message would have said (counts only):"
echo "$DE" | tail -n +2
echo ""
echo "$KIT: DONE. From tomorrow: 9:30 am 'X-ray <date>' to Reception, Shivani and Alisha; 7 pm 'Aaj ki upload' to them and 'Records today' to you. The 3 pm / 6 pm notice is unchanged."
