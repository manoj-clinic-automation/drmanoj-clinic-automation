#!/bin/bash
# =============================================================================
#  install_S535_PUNCH_SOURCE_WATCH.sh · kit S535 (session 305, 12-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S535_PUNCH_SOURCE_WATCH/install_S535_PUNCH_SOURCE_WATCH.sh
#
#  WHY: the owner, 12-Oct 05:33 IST, on the punch listener that saves anything shaped like a punch from anyone:
#  "close it only if it is safe and keeps attendance running glitch free" (D713; his word waives the attendance
#  freeze D247 for this change only). Closing it safely needs a mark that is on EVERY genuine punch. This kit is
#  STEP 1 of 2 and only RECORDS: the listener writes who sent each punch (address, the machine's own headers) to
#  /root/attlistener_sources.jsonl; every reply to the machine and every row of punches.csv stays exactly as today.
#  A nightly summary (01:25) lands in /root/finance/punch_sources_summary.json, which the 01:35 bundle carries to
#  the owner's PC. Step 2 (refuse a stranger, keep it aside, never lose a genuine punch) is built on a week of it.
#
#  ORDER: gates -> the file found (ALREADY first) -> compile -> the walk ON THIS BOX (the old and new listener side by
#  side on spare ports; replies and punches.csv identical; the watch failing changes nothing) -> backups -> place ->
#  restart the listener -> it answers the machine's heartbeat exactly as before -> the cron line once -> the first
#  summary -> undo line. Red after placing: the old listener back byte for byte and restarted; the cron line removed.
# =============================================================================
set -u
KIT="S535_PUNCH_SOURCE_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOTD="${ROOTD:-/root}"
PYBIN="${PYBIN:-/usr/bin/python3}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LPORT="${LPORT:-8041}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
LIS="$ROOTD/attlistener_v2.py"; SUMPY="$ROOTD/att_source_summary.py"
SRCLOG="$ROOTD/attlistener_sources.jsonl"; LISLOG="$ROOTD/attlistener.log"
OUTJ="$ROOTD/finance/punch_sources_summary.json"
FROM="94fc58caff28de0d400f788374106952"
TO="$(md5sum "$KDIR/attlistener_v2.py" 2>/dev/null | awk '{print $1}')"
TO_SUM="$(md5sum "$KDIR/att_source_summary.py" 2>/dev/null | awk '{print $1}')"
TAG="S535_PUNCH_WATCH"
CRON_LINE="25 1 * * * cd $ROOTD && $PYBIN $SUMPY >> $ROOTD/att_source_summary.log 2>&1 # $TAG"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="$(mktemp -d /tmp/s535.XXXXXX)"
HAVE_LOCK=0; PLACED=0; CRON_ADDED=0; CB=""; BAK=""; SUM_NEW=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
ack() { curl -s -m 10 -D - -o /dev/null -X POST -H 'request_code: receive_cmd' --data-binary '' "http://127.0.0.1:$LPORT/" 2>/dev/null | tr -d '\r' | grep -i '^response_code:' | awk '{print $2}'; }
cron_out() { [ -n "$CB" ] && [ -s "$CB" ] && crontab "$CB"; }
on_exit() { rm -rf "$SCR"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting everything back"
  [ "$CRON_ADDED" = 1 ] && cron_out
  [ -n "$BAK" ] && [ -f "$BAK" ] && \cp -p "$BAK" "$LIS"
  [ "$SUM_NEW" = 1 ] && rm -f "$SUMPY" "$OUTJ"
  "$SYSTEMCTL" restart attlistener >/dev/null 2>&1; sleep 3
  say "   $LIS $(m5 "$LIS") (expected $FROM) · service $("$SYSTEMCTL" is-active attlistener 2>/dev/null) · heartbeat answered: $(ack)"
  say "   cron lines tagged $TAG: $(crontab -l 2>/dev/null | grep -c "# $TAG\$")  (expected 0)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for c in md5sum awk curl crontab grep "$PYBIN" "$SYSTEMCTL"; do command -v "$c" >/dev/null 2>&1 || { say "!! [1/8] $c not found - nothing installed"; exit 1; }; done
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
[ "$HAVE_LOCK" = 1 ] || { say "!! [1/8] another build holds the lock $LOCK - nothing installed. Paste the line again when it is free."; exit 3; }
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

CUR="$(m5 "$LIS")"; NCRON="$(crontab -l 2>/dev/null | grep -c "# $TAG\$")"
if [ "$CUR" = "$TO" ] && [ "$(m5 "$SUMPY")" = "$TO_SUM" ] && [ "$NCRON" = 1 ]; then
  say "-- ALREADY INSTALLED: the listener is $TO, the summary is in place, the cron line once; heartbeat answered: $(ack). Nothing written."; exit 0
fi
[ "$CUR" = "$FROM" ] || { say "!! [2/8] $LIS is $CUR, not the FROM pin $FROM - nothing installed"; exit 1; }
[ "$NCRON" = 0 ] || { say "!! [2/8] $NCRON cron lines already carry $TAG - nothing installed"; exit 1; }
[ "$("$SYSTEMCTL" is-active attlistener 2>/dev/null)" = active ] || { say "!! [2/8] the attlistener service is not running before any change - nothing installed"; exit 1; }
A0="$(ack)"; [ "$A0" = ERROR_NO_CMD ] || { say "!! [2/8] the listener does not answer a heartbeat as expected before any change ('$A0') - nothing installed"; exit 1; }
[ -d "$ROOTD/finance" ] || { say "!! [2/8] $ROOTD/finance not found - nothing installed"; exit 1; }
say "[2/8] $LIS is the FROM pin; the service is running; a heartbeat is answered '$A0'"

"$PYBIN" -c "import py_compile,sys; [py_compile.compile(f, cfile='$SCR/x.pyc', doraise=True) for f in sys.argv[1:]]" \
  "$KDIR/attlistener_v2.py" "$KDIR/att_source_summary.py" || { say "!! [3/8] the kit's files do not compile under $PYBIN - nothing installed"; exit 1; }
say "[3/8] both files compile under $PYBIN ($("$PYBIN" -V 2>&1))"

\cp -p "$LIS" "$SCR/from_attlistener_v2.py"
W="$(cd "$SCR" && "$PYBIN" -B "$KDIR/walk_s535.py" "$SCR/from_attlistener_v2.py" "$KDIR/attlistener_v2.py" "$KDIR/att_source_summary.py" "$PYBIN" 2>&1)"
echo "$W" | grep -q "^WALK: GREEN" || { echo "$W" | grep -E "FAIL|WALK|Error|error" | head -12; say "!! [4/8] the walk on this box is not green - nothing installed"; exit 1; }
say "[4/8] the walk on this box: $(echo "$W" | grep -c '^  ok') checks green - replies and punches.csv identical, the watch failing changes nothing"

BAK="$LIS.bak_S535_$STAMP"
\cp -p "$LIS" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
CB="$ROOTD/finance/crontab.before_S535_$STAMP"
crontab -l > "$CB" 2>/dev/null && [ -s "$CB" ] || { say "!! [5/8] could not read the crontab - nothing placed"; exit 1; }
say "[5/8] backups: $(basename "$BAK") · crontab.before_S535_$STAMP"

PLACED=1
[ -e "$SUMPY" ] || SUM_NEW=1
\cp "$KDIR/att_source_summary.py" "$SUMPY.s535_new" && chmod 644 "$SUMPY.s535_new" && mv -f "$SUMPY.s535_new" "$SUMPY" || restore "placing the summary"
\cp "$KDIR/attlistener_v2.py" "$LIS.s535_new" && chown --reference="$LIS" "$LIS.s535_new" && chmod --reference="$LIS" "$LIS.s535_new" \
  && mv -f "$LIS.s535_new" "$LIS" || restore "placing the listener"
[ "$(m5 "$LIS")" = "$TO" ] && [ "$(m5 "$SUMPY")" = "$TO_SUM" ] || restore "the placed files are not the kit's bytes"
say "[6/8] placed: $(basename "$LIS") $FROM -> $TO · $(basename "$SUMPY") $TO_SUM"

"$SYSTEMCTL" restart attlistener || restore "the restart"
A1=""; for i in 1 2 3 4 5 6 7 8 9 10; do sleep 1; A1="$(ack)"; [ "$A1" = ERROR_NO_CMD ] && break; done
[ "$("$SYSTEMCTL" is-active attlistener 2>/dev/null)" = active ] || restore "the service is not running after the restart"
[ "$A1" = ERROR_NO_CMD ] || restore "the heartbeat is answered '$A1', not ERROR_NO_CMD"
tail -n 50 "$LISLOG" 2>/dev/null | grep -q "SOURCE_WATCH=S535" || restore "the listener's start-up line does not say SOURCE_WATCH=S535"
grep -q '"ip": "127.0.0.1"' "$SRCLOG" 2>/dev/null || restore "the test heartbeat is not in $SRCLOG"
say "[7/8] the listener restarted with the watch on; a heartbeat is answered '$A1' exactly as before; the source log records"

BEFORE_N="$(grep -c "" "$CB")"
\cp "$CB" "$SCR/cron.new" && echo "$CRON_LINE" >> "$SCR/cron.new"
CRON_ADDED=1
crontab "$SCR/cron.new" || restore "the cron line"
[ "$(crontab -l 2>/dev/null | grep -c "# $TAG\$")" = 1 ] || restore "the cron line is not there exactly once"
[ "$(crontab -l 2>/dev/null | grep -c "")" = $((BEFORE_N + 1)) ] || restore "the crontab changed by more than one line"
S1="$(cd "$ROOTD" && "$PYBIN" "$SUMPY" 2>&1 | tail -1)"
"$PYBIN" -c "import json,sys; json.load(open(sys.argv[1]))" "$OUTJ" 2>/dev/null || restore "the first summary was not written ($S1)"
PLACED=0
say "[8/8] the cron line once (01:25 nightly); the first summary: $S1"
md5sum "$LIS" "$SUMPY"
say "$KIT: DONE -- step 1 of 2: it only records. Attendance runs exactly as before."
say "undo: \\cp -p $BAK $LIS && systemctl restart attlistener && crontab -l > $ROOTD/finance/crontab.undo_S535 && grep -v '# $TAG\$' $ROOTD/finance/crontab.undo_S535 > $ROOTD/finance/crontab.undo_S535.new && crontab $ROOTD/finance/crontab.undo_S535.new"
