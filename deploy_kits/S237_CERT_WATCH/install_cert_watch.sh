#!/bin/bash
# =============================================================================
#  install_cert_watch.sh · kit S237_CERT_WATCH — the certificate night-watchman
#
#  Run by:  bash /root/deploy/vps_deploy.sh S237_CERT_WATCH
#  (vps_deploy.sh has already cd'd into this kit folder before calling us.)
#
#  Green path: md5 gate -> kit identity (F-88) -> back up any existing
#              cert_watch.py -> copy in -> py_compile -> --selftest must be
#              clean -> place the systemd units -> daemon-reload -> print the
#              live table with --dry-run.
#
#  IT DOES NOT ENABLE THE TIMER. Turning the watch on is the owner's own
#  separate line, printed at the end, so he sees the table BEFORE anything
#  starts running on a schedule.
#
#  Red path  : anything fails -> the previous cert_watch.py is restored (or the
#              new one removed if there was none), the units are removed, and
#              we exit non-zero. Nothing half-installed. No service is stopped,
#              started or restarted by this script at any point.
# =============================================================================
set -u
KIT="S237_CERT_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/root/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"
TARGET="/root/wa/cert_watch.py"
UNITS="/etc/systemd/system"
STAMP="$(date +%Y%m%d-%H%M%S)"
BAK=""            # path of the backup, once one has been taken
PLACED=0          # 1 once THIS run has written $TARGET
UNITS_PLACED=0    # 1 once THIS run has written the systemd units

# The red path undoes ONLY what this run did.
# (Earned at S237: the first version removed $TARGET whenever a gate failed --
#  including gates that run BEFORE anything is touched -- so a refused install
#  would have DELETED the owner's working cert_watch.py. A red path must never
#  destroy something it did not create.)
fail() { echo "!! RED — $*"
  if [ "$PLACED" -eq 1 ]; then
    if [ -n "$BAK" ] && [ -f "$BAK" ]; then cp -f "$BAK" "$TARGET" && echo "   restored the previous $TARGET"
    else rm -f "$TARGET" 2>/dev/null; echo "   removed the $TARGET this run had just created"; fi
  else
    echo "   $TARGET was NOT touched by this run and is exactly as it was"
  fi
  if [ "$UNITS_PLACED" -eq 1 ]; then
    rm -f "$UNITS/clinic-certwatch.service" "$UNITS/clinic-certwatch.timer" 2>/dev/null
    systemctl daemon-reload 2>/dev/null
    echo "   removed the systemd units this run had placed"
  fi
  echo "   nothing is installed, nothing is running, no service was started, stopped or restarted"; exit 1; }

cd "$KDIR" || fail "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || fail "SUMS.md5 gate failed — kit corrupt"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || fail "KIT_ID.txt names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum cert_watch.py | awk '{print $1}')" ] \
  || fail "KIT_ID.txt does not match cert_watch.py (F-88)"
echo "-- gates green: SUMS.md5 and KIT_ID.txt agree"

mkdir -p /root/wa || fail "cannot create /root/wa"
if [ -f "$TARGET" ]; then BAK="${TARGET}.bak_S237_${STAMP}"; cp -f "$TARGET" "$BAK" \
  || fail "could not back up the existing $TARGET"; echo "-- backed up the previous copy to $BAK"; fi

cp -f cert_watch.py "$TARGET" || fail "copy to $TARGET failed"
PLACED=1
# F-383: assert the copy, never trust that it happened.
[ "$(md5sum "$TARGET" | awk '{print $1}')" = "$(md5sum cert_watch.py | awk '{print $1}')" ] \
  || fail "the copied file does not match the kit's — the write did not land"
echo "-- copied and md5-verified: $TARGET"

"$PY" -m py_compile "$TARGET" || fail "py_compile failed on $TARGET"
echo "-- py_compile clean (using $PY)"

OUT="$("$PY" "$TARGET" --selftest)" || fail "selftest reported failures: $OUT"
echo "$OUT" | grep -q " 0 failures" || fail "selftest did not report 0 failures: $OUT"
echo "-- $OUT"

cp -f clinic-certwatch.service "$UNITS/" || fail "could not place the service unit"
UNITS_PLACED=1
cp -f clinic-certwatch.timer   "$UNITS/" || fail "could not place the timer unit"
systemctl daemon-reload || fail "daemon-reload failed"
echo "-- systemd units placed and reloaded (timer NOT enabled)"

echo ""
echo "================ THE LIVE TABLE — read-only, nothing sent ================"
"$PY" "$TARGET" --dry-run || echo "  (the dry run itself errored — the table above is what it managed)"
echo "========================================================================="
echo ""
echo "$KIT INSTALLED — file in place, gates green, timer NOT yet running."
echo ""
echo "If that table looks right, turn the daily watch on with this one line:"
echo ""
echo "  systemctl enable --now clinic-certwatch.timer && systemctl list-timers clinic-certwatch.timer --no-pager"
echo ""
