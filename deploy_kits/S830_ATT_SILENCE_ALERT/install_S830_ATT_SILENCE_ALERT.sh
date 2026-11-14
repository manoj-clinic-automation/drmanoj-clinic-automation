#!/bin/bash
# =============================================================================
#  install_S830_ATT_SILENCE_ALERT.sh . kit S830 (14-Nov-2026, session S460, the parent) . F-1402
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s830kit && cp -rp /root/deploy/repo/deploy_kits/S830_ATT_SILENCE_ALERT /tmp/s830kit && bash /tmp/s830kit/install_S830_ATT_SILENCE_ALERT.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s830kit/install_S830_ATT_SILENCE_ALERT.sh --undo
#
#  ONE NEW file /root/att_silence_watch.py + ONE cron line (every 5 minutes) + ONE leg in the freshness legs file
#  ("attendance machine contact", group Attendance). /root/attlistener_v2.py is NOT touched; no service is restarted.
#  The crontab is edited only from a good read of it, byte-wise, never written if a line that is not this kit's would be
#  lost, and read back. The legs file is changed only if it re-dumps to its own bytes (so no other leg can move); its copy
#  from before is kept. If anything is red after placing, everything goes back.
# =============================================================================
set -u
KIT="S830_ATT_SILENCE_ALERT"
TAG="# S830_ATT_SILENCE_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-$ROOT/s830_backup}"
N1="$ROOT/att_silence_watch.py"; PIN1=3517f3074afbe56bc57a6846e1ccbb03
WALK_OK="WALK OK 62/62"
CONF="$ROOT/finance/freshness.conf"
FRESH="$ROOT/finance/freshness.py"
LOGF="$ROOT/att_silence_watch.log"
STATEF="$ROOT/att_silence_watch.state.json"
LINE="*/5 * * * * $VPY -B $N1 >> $LOGF 2>&1 $TAG"
OWN="$STATEF $STATEF.tmp $STATEF.lock $STATEF.unreadable $LOGF"
SCR=""; HAVE_LOCK=0; PLACED1=0; CRON_CHANGED=0; LEGS_CHANGED=0; ORIG=""; LORIG=""; KEEP=""; BACK_OK=0
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
# the live legs file: LEGS_FILE in the freshness conf (only that key is read), else legs.json beside freshness.py
legs_path() { local p; p=$(sed -n 's/^[[:space:]]*LEGS_FILE[[:space:]]*=[[:space:]]*//p' "$CONF" 2>/dev/null | tail -1 | tr -d '\r'); [ -n "$p" ] && echo "$p" || echo "$ROOT/finance/legs.json"; }
fresh_has_leg() { (cd "$SCR" && timeout 60 "$VPY" -B "$FRESH" list 2>/dev/null | G -c -F "attendance machine contact"); }
back() {
  local ok=1
  if [ "$CRON_CHANGED" = 1 ]; then
    "$CRONTAB" - < "$BK/crontab.before_S830" 2>/dev/null
    if read_cron "$SCR/ct.back" && [ "$(m5 "$SCR/ct.back")" = "$ORIG" ]; then echo "   the crontab is back as it was, byte for byte (md5 ${ORIG:0:8})"
    else ok=0; echo "   !! THE CRONTAB DID NOT GO BACK -- its copy from before is kept at $BK/crontab.before_S830"; fi
  fi
  if [ "$LEGS_CHANGED" = 1 ]; then
    \cp -f "$BK/legs.before_S830" "$LEGS.s830back" && mv -f "$LEGS.s830back" "$LEGS"
    if [ "$(m5 "$LEGS")" = "$LORIG" ]; then echo "   the legs file is back as it was, byte for byte (md5 ${LORIG:0:8})"
    else ok=0; echo "   !! THE LEGS FILE DID NOT GO BACK -- its copy from before is kept at $BK/legs.before_S830"; fi
  fi
  [ "$PLACED1" = 1 ] && rm -f "$N1" "$N1.s830new"
  for f in $OWN; do case " $KEEP " in *" $f "*) ;; *) rm -f "$f";; esac; done
  { [ -e "$N1" ] && [ "$PLACED1" = 1 ]; } && ok=0
  if [ "$ok" = 1 ]; then rm -f "$BK/crontab.before_S830" "$BK/legs.before_S830"; rmdir "$BK" 2>/dev/null; echo "   the new file and what its first run left were taken out again"; fi
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
[ "$(m5 att_silence_watch.py)" = "$PIN1" ] || stop "the kit's att_silence_watch.py is not the built one"
SCR=$(mktemp -d /tmp/s830.XXXX) || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"
LEGS=$(legs_path)

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
  if [ -f "$LEGS" ]; then
    C=$("$VPY" -B "$KDIR/legs_s830.py" check "$LEGS")
    case "$C" in *" has=0") ;;
      "LEGS ok"*) "$VPY" -B "$KDIR/legs_s830.py" remove "$LEGS" "$SCR/legs.want" >/dev/null && \cp -f "$SCR/legs.want" "$LEGS.s830new" && mv -f "$LEGS.s830new" "$LEGS" || stop "the leg could not be taken out of $LEGS" "The cron line is already out.";;
      *) echo "NOTE: the legs file did not re-dump to its own bytes ($C) -- the leg 'attendance machine contact' was left in it; it will show red. Send a photo to Claude.";;
    esac
  fi
  rm -f "$N1" "$N1.s830new" $OWN "$BK/crontab.before_S830" "$BK/legs.before_S830"; rmdir "$BK" 2>/dev/null
  [ -e "$N1" ] && { echo "!! the file is still there -- send a photo"; exit 1; }
  echo "UNDONE: the S830 cron line, the watcher and its leg on the freshness page are out. Attendance itself was never touched."
  exit 0
fi

echo "[1/6] kit files: all match SUMS.md5; the watcher is the built one (${PIN1:0:8})"
read_cron "$SCR/ct" || stop "root's crontab could not be read (crontab -l gave nothing usable) -- it is never edited from a bad read"
ORIG=$(m5 "$SCR/ct")
[ -f "$LEGS" ] || stop "the freshness legs file ($LEGS) is not on the box"
if [ "$(m5 "$N1")" = "$PIN1" ] && [ "$(n_ours "$SCR/ct")" = 1 ] && "$VPY" -B "$KDIR/legs_s830.py" check "$LEGS" 2>/dev/null | G -q " has=1\$"; then
  echo "-- ALREADY INSTALLED (the watcher, its cron line and its leg are there). Nothing written."; exit 0
fi
for t in timeout md5sum mktemp sed; do command -v "$t" >/dev/null 2>&1 || stop "the box has no '$t'"; done
"$VPY" -c "import json, fcntl" 2>/dev/null || stop "$VPY does not run"
[ -e "$N1" ] && [ "$(m5 "$N1")" != "$PIN1" ] && stop "$N1 is there and is not this kit's"
[ "$(n_ours "$SCR/ct")" = 0 ] || [ "$(n_ours "$SCR/ct")" = 1 ] || stop "the crontab carries this kit's tag more than once"
[ -f "$FRESH" ] || stop "$FRESH is not on the box"
"$VPY" -B -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$KDIR/att_silence_watch.py" 2>/dev/null || stop "att_silence_watch.py does not compile with $VPY"
( cd "$SCR" && "$VPY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import ring_common as rc; assert callable(rc.push_user)" "$ROOT/portal" 2>/dev/null ) || stop "the portal's own push (ring_common.push_user) could not be loaded with $VPY"
C=$("$VPY" -B "$KDIR/legs_s830.py" check "$LEGS" 2>&1 | tail -1)
case "$C" in "LEGS ok"*) ;; *) stop "the legs file $LEGS cannot be changed safely ($C)";; esac
F0=$(fresh_has_leg); F0=${F0:-0}
[ "$F0" = 0 ] || case "$C" in *" has=1") ;; *) stop "the freshness page already has a leg of this name that is not this kit's";; esac
P=$(cd "$SCR" && ASW_STATE="$SCR/probe_state.json" timeout 60 "$VPY" -B "$KDIR/att_silence_watch.py" --probe 2>&1 | tail -1)
case "$P" in "PROBE "*) ;; *) stop "the watcher's probe did not answer as expected (${P:0:160})";; esac
case "$P" in *" listener=yes"*) ;; *) stop "the listener process (attlistener_v2.py) was not found on this box ($P)";; esac
TABLES=$(printf '%s\n' "$P" | sed -n 's/.* tables=\([^ ]*\).*/\1/p')
case "$P" in *" punches=ok"*) ;; *) stop "the punch file cannot be read ($P)";; esac
DEV=$(printf '%s\n' "$P" | sed -n 's/.* devices=\([0-9?]*\).*/\1/p'); DEV=${DEV:-?}
HRS=$(printf '%s\n' "$P" | sed -n 's/.* hours=\([0-9:]*-[0-9:]*\).*/\1/p')
echo "[2/6] the box: the listener runs; connection tables read: ${TABLES:-none}; the punch file reads; the push loads; legs file $LEGS ($C)"
echo "      $P"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s830.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s830.py" "$KDIR" 2>&1 | grep -E '^BAD|Error' | cut -c1-300 | head -6); stop "the walk is not green on this box ($R)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s830.py" "$KDIR" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control (three broken copies) did not go red ($R2)";; esac
echo "[3/6] the walk on this box (a made-up root): $R | $R2"
{ [ "${DRY:-0}" = 1 ] || [ "${1:-}" = "--dry" ]; } && { echo "DRY=1: every gate green; nothing written."; exit 0; }

mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
read_cron "$SCR/ct2" && [ "$(m5 "$SCR/ct2")" = "$ORIG" ] || stop "the crontab changed (or could not be read) while this kit was checking -- run the line again"
for f in $OWN; do [ -e "$f" ] && KEEP="$KEEP $f"; done
LORIG=$(m5 "$LEGS")
mkdir -p "$BK" && chmod 700 "$BK" && \cp -f "$SCR/ct" "$BK/crontab.before_S830" && [ "$(m5 "$BK/crontab.before_S830")" = "$ORIG" ] \
  && \cp -fp "$LEGS" "$BK/legs.before_S830" && [ "$(m5 "$BK/legs.before_S830")" = "$LORIG" ] || stop "could not keep a copy of the crontab and the legs file in $BK"
chmod 600 "$BK/crontab.before_S830"
[ -e "$N1" ] || PLACED1=1
\cp -f "$KDIR/att_silence_watch.py" "$N1.s830new" && mv -f "$N1.s830new" "$N1" && [ "$(m5 "$N1")" = "$PIN1" ] || red "att_silence_watch.py did not land byte-exact"
chmod 644 "$N1"
S=$(cd "$SCR" && timeout 60 "$VPY" -B "$N1" --seed 2>&1 | tail -1)
case "$S" in "SEED "*) ;; *) red "the watcher's first run (the baseline) did not answer as expected (${S:0:160})";; esac
[ -f "$STATEF" ] || red "the watcher's first run wrote no state file"
echo "[4/6] placed $N1 (${PIN1:0:8}); its first run wrote the baseline: ${S#SEED }"

"$VPY" -B "$KDIR/legs_s830.py" add "$LEGS" "$SCR/legs.want" >/dev/null || red "the leg could not be added to a copy of the legs file"
"$VPY" -B "$KDIR/legs_s830.py" check "$SCR/legs.want" | G -q " has=1\$" || red "the changed legs file does not carry the leg once"
LEGS_CHANGED=1
\cp -f "$SCR/legs.want" "$LEGS.s830new" && chmod --reference="$BK/legs.before_S830" "$LEGS.s830new" 2>/dev/null; mv -f "$LEGS.s830new" "$LEGS" || red "the legs file could not be written"
[ "$(m5 "$LEGS")" = "$(m5 "$SCR/legs.want")" ] || red "the legs file did not read back as written"
[ "$(fresh_has_leg)" = 1 ] || red "the freshness collector does not list the new leg"
echo "[5/6] the freshness page's legs: 'attendance machine contact' added, read back, listed by freshness.py (the copy from before: $BK/legs.before_S830)"

{ strip_ours "$SCR/ct"; echo "$LINE"; } > "$SCR/ct.want"
keeps_all "$SCR/ct" "$SCR/ct.want" 1 || red "the new crontab would lose a line that is not this kit's -- not written"
CRON_CHANGED=1
"$CRONTAB" - < "$SCR/ct.want" || red "the crontab could not be written"
read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || red "the crontab did not read back as written"
[ "$(n_ours "$SCR/ct.now")" = 1 ] || red "the cron line is not there exactly once"
D=$(cd "$SCR" && timeout 60 "$VPY" -B "$N1" --dry 2>&1 | tail -1)
case "$D" in "DRY "*) ;; *) red "the placed watcher's dry run did not answer as expected (${D:0:160})";; esac
echo "[6/6] one cron line added (every 5 minutes), read back; every other line kept ($(n_lines "$SCR/ct") lines before, $(n_lines "$SCR/ct.now") now)"
echo "      what it sees now: ${D#DRY }"
echo ""
WHAT="From now, if no punch has come by 10:00 on a working day you get one message; once the machine has been seen calling the server (the first day it is back), a silence of 30 minutes in clinic hours ($HRS, Monday to Saturday) is one message, and its return one more; a wrong or stuck machine clock is told once a day. The freshness page and your console show it as 'attendance machine contact'."
case "$D" in *"would send: nothing"*) NOW="Nothing is due now.";; *) NOW="Something is due now (the line above): the first message comes within 5 minutes.";; esac
if [ "$DEV" = 0 ]; then echo "$KIT: DONE. $WHAT No phone is registered for your login, so it would come by ntfy only. $NOW"
else echo "$KIT: DONE. $WHAT $NOW"; fi
