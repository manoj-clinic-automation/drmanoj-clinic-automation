#!/bin/bash
# =============================================================================
#  install_S525_SPINE_RED_FAST.sh · kit S525_SPINE_RED_FAST (session 305, 11-Oct-2026) · F-849
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S525_SPINE_RED_FAST/install_S525_SPINE_RED_FAST.sh
#
#  WHY: the Marg spine's gate failed on 08-Oct 09:10 and kept failing; the health page's leg judged it only by the
#  age of its last success (26 h) and the collector ran once a day (08:05), so the first red shout was 10-Oct 08:05.
#  THIS KIT: (1) the spine-gate leg also reads the state file's own last_failure_iso and is red as soon as the newest
#  build failed; (2) the collector also runs at :35 every hour 09-23 -- its shout stays once per leg per calendar day.
#  (the legs file ships as freshness_legs.json.kit -- the repository ignores *.json, F-832 -- and is placed under its own name)
#  FILES: /root/finance/freshness.py 66d93a63 -> 83865d94 · /root/finance/freshness_legs.json 716734ae -> 9df66934.
#  CRON: one appended line, tagged S525_FRESH_HOURLY. No service is restarted (the collector is a cron job; the page
#  serves the file it writes). The spine's own files are only read.
#
#  ORDER: kit SUMS + KIT_ID -> the build lock -> pins (ALREADY INSTALLED first) -> compile -> THE WALK ON THIS BOX
#  (both collectors read every live leg; every leg the same but the one that names its failure field) -> DRY=1 stops
#  -> backups -> place -> the cron line -> one collector run, its output read -> undo line.
#  Red after placing -> both old files back byte for byte and the cron line taken out again.
# =============================================================================
set -u
KIT="S525_SPINE_RED_FAST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
PYF="$FIN/freshness.py"; LEGS="$FIN/freshness_legs.json"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FROM_PY=66d93a631c6c46ebb6536620450efa74; TO_PY=83865d94c22d57c00661c2b1c3d20209
FROM_LG=716734aef3bcacdef54d0172a00440e2; TO_LG=9df66934e0df2bf3771ffeb517312674
TAG="S525_FRESH_HOURLY"
CRON_LINE="35 9-23 * * * $VPY $PYF --shout >> $FIN/freshness.log 2>&1 # $TAG"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s525_inst_$STAMP"
HAVE_LOCK=0; PLACED=0; CRON_ADDED=0
BAK_PY="$PYF.bak_S525_${FROM_PY:0:8}"; BAK_LG="$LEGS.bak_S525_${FROM_LG:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
CB=""                                                  # the crontab as it was, read once into a file (step 5)
cron_out() { [ -n "$CB" ] && [ -s "$CB" ] && crontab "$CB"; }   # back to exactly that file, never through a pipe
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both old files back byte for byte"
  [ -f "$BAK_PY" ] && \cp -p "$BAK_PY" "$PYF"
  [ -f "$BAK_LG" ] && \cp -p "$BAK_LG" "$LEGS"
  [ "$CRON_ADDED" = 1 ] && cron_out
  say "   $PYF $(m5 "$PYF")  (expected $FROM_PY)"
  say "   $LEGS $(m5 "$LEGS")  (expected $FROM_LG)"
  say "   cron lines tagged $TAG: $(crontab -l 2>/dev/null | grep -c "# $TAG\$")  (expected 0)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date crontab grep tail timeout; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 freshness.py)" = "$TO_PY" ] && [ "$(m5 freshness_legs.json.kit)" = "$TO_LG" ] \
  || { say "!! [1/8] the kit's two files are not their predicted md5 - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

for f in "$PYF" "$LEGS"; do [ -f "$f" ] || { say "!! [2/8] $f is not there - nothing installed"; exit 1; }; done
CPY="$(m5 "$PYF")"; CLG="$(m5 "$LEGS")"; NCRON="$(crontab -l 2>/dev/null | grep -c "# $TAG\$")"
if [ "$CPY" = "$TO_PY" ] && [ "$CLG" = "$TO_LG" ] && [ "$NCRON" = 1 ]; then
  say "-- ALREADY INSTALLED: both files are the kit's and the cron line is there. Nothing written."; md5sum "$PYF" "$LEGS"; exit 0
fi
[ "$NCRON" -le 1 ] || { say "!! [2/8] $NCRON cron lines already carry the tag $TAG - nothing installed"; exit 1; }
[ "$CPY" = "$FROM_PY" ] || { say "!! [2/8] $PYF is $CPY, expected $FROM_PY - nothing installed"; exit 1; }
[ "$CLG" = "$FROM_LG" ] || { say "!! [2/8] $LEGS is $CLG, expected $FROM_LG - nothing installed"; exit 1; }
say "[2/8] two live pins exact"

mkdir -p "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"
export PYTHONDONTWRITEBYTECODE=1
"$VPY" -m py_compile freshness.py walk_s525.py make_s525.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
"$VPY" -c "import json; json.load(open('freshness_legs.json.kit'))" || { say "!! [3/8] the kit's legs file is not JSON - nothing installed"; exit 1; }
say "[3/8] py_compile green (3 files); the legs file reads as JSON"

WOUT="$( cd /tmp && timeout 300 "$VPY" -B "$KDIR/walk_s525.py" "$KDIR" --live-py "$PYF" --live-legs "$LEGS" 2>&1 )"; WRC=$?
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [4/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -6; say "   nothing installed"; exit 1
fi
echo "$WOUT" | grep -E '^   '
say "[4/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, no cron line"; exit 0; fi

\cp -p "$PYF" "$BAK_PY" && \cp -p "$LEGS" "$BAK_LG" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
[ "$(m5 "$BAK_PY")" = "$FROM_PY" ] && [ "$(m5 "$BAK_LG")" = "$FROM_LG" ] || { say "!! [5/8] a backup is not the live file - nothing placed"; exit 1; }
CB="$FIN/crontab.before_S525_$STAMP"
crontab -l > "$CB" 2>/dev/null && [ -s "$CB" ] || { say "!! [5/8] could not read the crontab - nothing placed"; exit 1; }
say "[5/8] backups: $(basename "$BAK_PY") · $(basename "$BAK_LG") · crontab.before_S525_$STAMP"

\cp -p freshness.py "$FIN/.freshness.py.s525" && \cp -p freshness_legs.json.kit "$FIN/.freshness_legs.json.s525" \
  || { rm -f "$FIN/.freshness.py.s525" "$FIN/.freshness_legs.json.s525"; say "!! [6/8] could not stage the two files - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.freshness_legs.json.s525" "$LEGS" || restore "placing freshness_legs.json"
mv -f "$FIN/.freshness.py.s525" "$PYF" || restore "placing freshness.py"
[ "$(m5 "$PYF")" = "$TO_PY" ] && [ "$(m5 "$LEGS")" = "$TO_LG" ] || restore "the files did not land at their pins"
say "[6/8] both files placed at their pins"

BEFORE_N="$(grep -c "" "$CB")"
if [ "$NCRON" = 0 ]; then
  \cp -p "$CB" "$SCR/cron.new" || restore "the cron line (copy)"
  [ -z "$(tail -c1 "$SCR/cron.new")" ] || echo >> "$SCR/cron.new"   # a last line with no newline keeps its own line
  echo "$CRON_LINE" >> "$SCR/cron.new"
  CRON_ADDED=1
  crontab "$SCR/cron.new" || restore "the cron line"
fi
AFTER_N="$(crontab -l 2>/dev/null | grep -c "")"
[ "$(crontab -l 2>/dev/null | grep -c "# $TAG\$")" = 1 ] || restore "the cron line is not there exactly once"
[ "$NCRON" = 1 ] || [ "$AFTER_N" = $((BEFORE_N + 1)) ] || restore "the crontab changed by more than one line ($BEFORE_N -> $AFTER_N)"
say "[7/8] the cron line is there once ($BEFORE_N -> $AFTER_N lines): $(crontab -l | grep "# $TAG\$")"

for _w in 1 2 3 4 5 6 7; do                             # never beside the collector's own runs (08:05, :35)
  _m=$((10#$(date +%M))); _h=$((10#$(date +%H)))
  { [ "$_m" -ge 33 ] && [ "$_m" -le 37 ]; } || { [ "$_h" = 8 ] && [ "$_m" -ge 3 ] && [ "$_m" -le 7 ]; } || break
  say "   waiting a minute: the collector runs at this time of the hour"; sleep 60
done
ROUT="$( cd /tmp && timeout 120 "$VPY" "$PYF" check >> "$FIN/freshness.log" 2>&1; echo "rc=$?" )"
AOUT="$( cd /tmp && timeout 60 "$VPY" -B -c "
import json
d = json.load(open('$FIN/freshness.json'))
leg = [l for l in d['legs'] if l['name'] == 'Marg spine gate (S331)']
assert leg, 'the spine gate leg is not in the output'
assert 'S525' in (leg[0].get('note') or ''), 'the collector did not read the kit legs file (its conf names another LEGS_FILE?)'
st = json.load(open('$FIN/spine/spine_state.json'))
failing = (st.get('last_failure_iso') or '') > (st.get('last_success_iso') or '') and not st.get('passed')
v = leg[0]['verdict']
assert (v == 'STALE') if failing else True, 'the gate is failing but the leg reads ' + v
print('AFTER OK - %d legs read; the spine gate leg reads %s (the newest build %s); counts %s' % (len(d['legs']), v, 'FAILED' if failing else 'passed', d['counts']))
" 2>&1 )"; ARC=$?
if [ "$ARC" != 0 ] || ! echo "$AOUT" | grep -q "^AFTER OK"; then
  say "!! [8/8] the collector's first run does not read as it must (exit $ARC; $ROUT):"; echo "$AOUT" | tail -3; restore "after-check"
fi
PLACED=0
say "[8/8] $AOUT"
md5sum "$PYF" "$LEGS"
say "$KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/freshness"
say "undo: \\cp -p $BAK_PY $PYF && \\cp -p $BAK_LG $LEGS && crontab -l > /root/finance/crontab.undo_S525 && grep -v '# $TAG\$' /root/finance/crontab.undo_S525 > /root/finance/crontab.undo_S525.new && crontab /root/finance/crontab.undo_S525.new"
