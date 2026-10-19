#!/bin/bash
# =============================================================================
#  install_S594_WITNESS_CRON.sh · kit S594 (19-Oct-2026) · brief claude_code_briefs/S594_WITNESS_CRON.md (v2) · the Sanjeevni chat, S328
#
#  ONE root crontab line -- the one S577's README names at its l.77 and did not add -- so that the seven-night side-by-side week of
#  stock_figure against the old stock figures starts (4b-2 waits for it):
#    58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS
#  NO file on the box changes; NO restart. The crontab is the clinic project's record: the README names this line for the parent.
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S594_WITNESS_CRON), 08:00-23:49 IST only (never while the
#  23:58 run is due):   rm -rf /tmp/s594kit && cp -rp <kit> /tmp/s594kit && bash /tmp/s594kit/install_S594_WITNESS_CRON.sh
#  (DRY=1 before bash: every gate, the walk, the negative control and the rehearsal; the crontab is not written.)
#
#  ORDER: gates (window, lock, SUMS, KIT_ID, the walk carries the same line) -> the read-only md5s (stock_figure 92367a19, stock_watch
#  c5f3ce21, spine/spine_build e3d3ed85), ALL_OFF absent, the spine's state -> the idempotence gate (the tag already in -> nothing to do,
#  exit 0) -> the crontab text copied to scratch -> the walk on the copy, with the rehearsal (the command run once by hand as the line
#  will run it, read only) -> the negative control (a copy that holds the tag: the walk refuses) -> DRY stops -> the backup
#  /root/finance/crontab.bak_S594_<stamp> (must exist, be non-empty, end in a newline, have the same line count and md5 as crontab -l)
#  -> ( crontab -l; echo "$CRON_LINE" ) | crontab - -> read back: the tag once, the line byte-equal, lines = before + 1, diff = exactly
#  the one added line, crontab -l without the tag = the backup's md5, the read-only md5s unmoved. Red after the write: the backup is
#  put back and its md5 proved. The installer runs under set -u, not set -e: every grep -c carries || true, every gate is a test.
# =============================================================================
set -u
KIT="S594_WITNESS_CRON"
TAG="# S577_WITNESS"
CRON_LINE='58 23 * * * cd /root/finance && /root/wa/venv/bin/python3 -B stock_figure.py witness >> /root/finance/spine/stock_figure_witness.log 2>&1 # S577_WITNESS'
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
SPN="$FIN/spine"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFF="$FIN/_off/ALL_OFF"
FIN_PORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s594_inst_$STAMP"
BAK="$FIN/crontab.bak_S594_$STAMP"
declare -A READ
READ[$FIN/stock_figure.py]=92367a196b360f0cded4cda6a5ded700
READ[$FIN/stock_watch.py]=c5f3ce21a785c45df58f21932cf920e7
READ[$SPN/spine_build.py]=e3d3ed85973eab2df0326dc9621e230e
HOLD=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
cronN() { crontab -l 2>/dev/null | wc -l | awk '{print $1}'; }
tagN() { local n; n="$(crontab -l 2>/dev/null | grep -cF -- "$TAG" || true)"; echo "${n:-0}"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
jget() { "$APY" -c "import json,sys; print(json.load(open(sys.argv[1])).get(sys.argv[2], ''))" "$1" "$2" 2>/dev/null; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; [ "$HOLD" = 1 ] || rm -rf "$LOCK"; }
pins_ok() { local f; for f in "${!READ[@]}"; do [ "$(m5 "$f")" = "${READ[$f]}" ] || return 1; done; return 0; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after the write ($1) - putting the crontab back from $BAK"
  crontab "$BAK" || say "!! crontab $BAK failed - RUN BY HAND: crontab $BAK"
  say "   crontab -l md5 now $(cron5) (the backup's $M0; the two must be equal) · lines $(cronN) (before: $L0) · tagged lines $(tagN)"
  exit 1
}
trap on_exit EXIT

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk date crontab grep diff wc tail head sed cut curl timeout find stat; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing done"; exit 1; }
done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing done"; exit 1; }
HM=$((10#$(TZ=Asia/Kolkata date +%H%M)))
if [ "$HM" -lt 800 ] || [ "$HM" -gt 2349 ]; then say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the window 08:00-23:49 IST (the line runs at 23:58) - nothing done"; exit 1; fi
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing done"; exit 1; }
[ "$("$APY" -B walk_s594.py --crontab /dev/null --print-line)" = "$CRON_LINE" ] || { say "!! [1/8] the walk's line is not the installer's - nothing done"; exit 1; }
for py in "$APY" "$VPY"; do PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/s594_pyc "$py" -m py_compile walk_s594.py || { say "!! [1/8] walk_s594.py does not compile on $py - nothing done"; exit 1; }; done
rm -rf /tmp/s594_pyc
if mkdir "$LOCK" 2>/dev/null; then
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  say "[1/8] kit gates green (the window $(TZ=Asia/Kolkata date '+%H:%M IST'), SUMS, KIT_ID, the walk's line = the installer's, compiles on both pythons); the build lock taken by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing done. Run it again when it is free."
  HOLD=1; exit 3
fi

# ---- 2 read only: the three pins, the switch, the spine's state ------------------------------------------------------------------------
for f in "${!READ[@]}"; do C="$(m5 "$f")"; [ "$C" = "${READ[$f]}" ] || { say "!! [2/8] $f is $C, expected ${READ[$f]} - it moved after the brief: STOP, nothing done"; exit 1; }; done
[ -e "$OFF" ] && { say "!! [2/8] the switch $OFF is present - the witness would write nothing: STOP, nothing done"; exit 1; }
[ -d "$SPN" ] && [ -f "$SPN/spine.db" ] || { say "!! [2/8] $SPN or its spine.db is missing - nothing done"; exit 1; }
SP_OK="$(jget "$SPN/spine_state.json" passed)"; SP_GATE="$(jget "$SPN/spine_state.json" gate)"; SP_AT="$(jget "$SPN/spine_state.json" last_success_iso)"
[ "$SP_OK" = True ] || { say "!! [2/8] the spine is red (passed $SP_OK, gate $SP_GATE, last success $SP_AT) - the witness reads it; nothing done (charter 1b)"; exit 4; }
say "[2/8] read only, unmoved: stock_figure.py 92367a19 · stock_watch.py c5f3ce21 · spine/spine_build.py e3d3ed85; $OFF absent; the spine passed $SP_GATE, last success $SP_AT"

# ---- 3 the idempotence gate, the crontab as it is -----------------------------------------------------------------------------------------
N0="$(tagN)"
if [ "$N0" = 1 ]; then say "-- ALREADY IN: the crontab holds one '$TAG' line - nothing to do. $(crontab -l | grep -F -- "$TAG" | cut -c1-80)..."; exit 0; fi
[ "$N0" = 0 ] || { say "!! [3/8] the crontab holds $N0 '$TAG' lines - not this kit's state: STOP, nothing done"; exit 1; }
mkdir -p "$SCR" || { say "!! cannot make $SCR - nothing done"; exit 1; }
crontab -l > "$SCR/crontab.txt" 2>/dev/null || { say "!! [3/8] crontab -l failed (no crontab?) - STOP, nothing done"; exit 1; }
L0="$(cronN)"; M0="$(cron5)"
[ -s "$SCR/crontab.txt" ] && [ "$(wc -l < "$SCR/crontab.txt" | awk '{print $1}')" = "$L0" ] && [ "$(md5sum "$SCR/crontab.txt" | awk '{print $1}')" = "$M0" ] || { say "!! [3/8] the scratch copy of the crontab is not crontab -l - nothing done"; exit 1; }
[ "$(tail -c1 "$SCR/crontab.txt" | od -An -c | tr -d ' ')" = '\n' ] || { say "!! [3/8] crontab -l does not end in a newline - an appended line would glue onto the last one: STOP, nothing done"; exit 1; }
say "[3/8] no '$TAG' line in the crontab; $L0 lines, md5 $M0, ends in a newline; the text copied to scratch"

# ---- 4 the walk on the copy (with the rehearsal), then the negative control ----------------------------------------------------------
WOUT="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s594.py" --crontab "$SCR/crontab.txt" --run-witness --timeout 600 2>&1 )"; WRC=$?
echo "$WOUT" | mask | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK $KIT"; then say "!! [4/8] the walk is RED (exit $WRC) - nothing done"; exit 1; fi
echo "$WOUT" | grep -q "stock_figure: switched off" && { say "!! [4/8] the rehearsal says switched off - STOP, nothing done"; exit 1; }
REH="$(echo "$WOUT" | sed -n 's/^  REHEARSAL //p' | mask)"
cp -p "$SCR/crontab.txt" "$SCR/crontab_with.txt" && echo "$CRON_LINE" >> "$SCR/crontab_with.txt" || { say "!! [4/8] no copy for the negative control - nothing done"; exit 1; }
ROUT="$( cd /tmp && timeout 120 "$APY" -B "$KDIR/walk_s594.py" --crontab "$SCR/crontab_with.txt" --expect-red 2>&1 )"; RRC=$?
echo "$ROUT" | mask | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control $KIT"; then say "!! [4/8] the negative control did not go red on a copy that holds the tag - the walk proves nothing; nothing done"; exit 1; fi
NOUT="$( cd /tmp && timeout 120 "$APY" -B "$KDIR/walk_s594.py" --crontab "$SCR/crontab.txt" --expect-red 2>&1 )"; NRC=$?
[ "$NRC" != 0 ] && echo "$NOUT" | grep -q "NOT RED" || { say "!! [4/8] the negative control did NOT fail on the plain copy (exit $NRC) - it cannot fail, so it proves nothing; nothing done"; exit 1; }
[ "$(cron5)" = "$M0" ] || { say "!! [4/8] the crontab moved during the walk - nothing done"; exit 1; }
say "[4/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control: $(echo "$ROUT" | grep "^WALK OK negative control" | sed "s/^WALK OK negative control $KIT: //"); and on the plain copy the control itself goes red (NOT RED, exit $NRC)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the rehearsal and the negative control green; the crontab NOT written ($L0 lines, md5 $M0)"; exit 0; fi

# ---- 5 the backup, proved before any write -------------------------------------------------------------------------------------------------
crontab -l > "$BAK" 2>/dev/null || { rm -f "$BAK"; say "!! [5/8] crontab -l > $BAK failed - nothing written"; exit 1; }
[ -s "$BAK" ] || { say "!! [5/8] the backup $BAK is EMPTY - STOP before any write"; exit 1; }
[ "$(tail -c1 "$BAK" | od -An -c | tr -d ' ')" = '\n' ] || { say "!! [5/8] the backup does not end in a newline - STOP before any write"; exit 1; }
[ "$(wc -l < "$BAK" | awk '{print $1}')" = "$(cronN)" ] && [ "$(cronN)" = "$L0" ] || { say "!! [5/8] the backup has $(wc -l < "$BAK") lines, crontab -l $(cronN) (before: $L0) - STOP before any write"; exit 1; }
[ "$(m5 "$BAK")" = "$M0" ] && [ "$(cron5)" = "$M0" ] || { say "!! [5/8] the backup's md5 $(m5 "$BAK") is not crontab -l's $(cron5) (before: $M0) - STOP before any write"; exit 1; }
chmod 600 "$BAK"
say "[5/8] backup $BAK: $(stat -c %s "$BAK") bytes, $L0 lines, md5 $M0 (= crontab -l), ends in a newline"

# ---- 6 the write ------------------------------------------------------------------------------------------------------------------------------
( crontab -l; echo "$CRON_LINE" ) | crontab - || restore "crontab - failed"
N1="$(tagN)"; [ "$N1" = 1 ] || restore "the tag is in $N1 line(s), not 1"
[ "$(crontab -l | grep -cFx -- "$CRON_LINE" || true)" = 1 ] || restore "the line in the crontab is not byte-equal to the brief's"
L1="$(cronN)"; [ "$L1" = "$((L0 + 1))" ] || restore "lines $L1, expected $((L0 + 1))"
DIFF="$(diff "$BAK" <(crontab -l))"
[ "$(echo "$DIFF" | grep -c '^<' || true)" = 0 ] && [ "$(echo "$DIFF" | grep -c '^>' || true)" = 1 ] && [ "$(echo "$DIFF" | grep '^>' )" = "> $CRON_LINE" ] || restore "the diff is not exactly the one added line: $(echo "$DIFF" | head -5 | tr '\n' '|')"
M2="$(crontab -l | grep -vF -- "$TAG" | md5sum | awk '{print $1}')"
[ "$M2" = "$M0" ] || restore "crontab -l without the tag is $M2, the backup $M0 - something else moved"
pins_ok || restore "a read-only file moved"
[ -e "$OFF" ] && restore "the switch appeared"
say "[6/8] written: ( crontab -l; echo LINE ) | crontab -  ·  read back: the tag in 1 line, byte-equal (grep -Fx), $L0 -> $L1 lines, diff = exactly the one added line, crontab -l without the tag = the backup's md5 $M0, the three read-only md5s unmoved"

# ---- 7-8 the record --------------------------------------------------------------------------------------------------------------------------
say "[7/8] the crontab now: $L1 lines, md5 $(cron5); the line:"
crontab -l | grep -F -- "$TAG" | sed 's/^/       /'
say "       the first witness night: $(TZ=Asia/Kolkata date '+%d-%m-%Y') at 23:58 IST (the file stock_figure_witness_$(TZ=Asia/Kolkata date +%a).txt; the log $SPN/stock_figure_witness.log)"
say "       rehearsal: ${REH:-see above}"
say "[8/8] nothing restarted; clinic-finance healthz $(health /finance/healthz) (unchanged by this kit); md5 read back:"
for f in "${!READ[@]}"; do md5sum "$f"; done
HOLD=1
say "$KIT: DONE. The build lock stays held by $KIT until the report is written."
say "undo: crontab $BAK   (then crontab -l | md5sum must read $M0)"
exit 0
