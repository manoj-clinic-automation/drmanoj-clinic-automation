#!/bin/bash
# =============================================================================
#  install_S338_SPINE_HEALTH.sh · kit S338_SPINE_HEALTH (session 274, Sanjeevni, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S338_SPINE_HEALTH/install_S338_SPINE_HEALTH.sh
#
#  D567 item 4: the spine on the health page.
#    /root/finance/spine/spine_build.py   f5907fd4 (S331) -> TO below: after every build it writes
#                                         spine_state.json beside the spine (last_success_iso moves only on 14/14)
#    /root/finance/freshness_legs.json    DATA EDIT on the parent's file (declared): two legs appended --
#                                         'Marg spine gate (S331)' (state_json) and 'Marg spine compare (S331)' (file_mtime)
#  No service restart (both readers are cron jobs).  Nothing else touched.  The nightly bundle / state backup
#  widening for /root/finance/spine (spine.db, readings/) is NAMED to the parent in README.md, not done here.
# =============================================================================
set -u
KIT="S338_SPINE_HEALTH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; SP="$FIN/spine"
LEGS="$FIN/freshness_legs.json"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s338_walk_$STAMP"
SB_FROM=f5907fd4c3ada022a4cfa400356bd097
SB_TO=1378c87de2f8d4b3796cd92c7ca50d8d
LEGS_FROM=0e56aa9ead530a70b7977cbf237d13ea
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 spine_build.py)" = "$SB_TO" ] || { say "!! [1/8] kit spine_build.py is not its pin - nothing installed"; exit 1; }
say "[1/8] kit gates green"
LEGS_NOW="$(m5 "$LEGS")"
if [ "$(m5 "$SP/spine_build.py")" = "$SB_TO" ] && grep -q '"Marg spine gate (S331)"' "$LEGS" 2>/dev/null; then
  say "-- ALREADY INSTALLED (spine_build $SB_TO; legs present, freshness_legs.json $LEGS_NOW)"; exit 0; fi
[ "$(m5 "$SP/spine_build.py")" = "$SB_FROM" ] || { say "!! [2/8] spine_build.py is $(m5 "$SP/spine_build.py"), not the S331 pin - nothing installed"; exit 1; }
if [ "$LEGS_NOW" != "$LEGS_FROM" ]; then
  if grep -q '"Marg spine gate (S331)"' "$LEGS"; then say "   legs already carry the spine gate leg ($LEGS_NOW)"; else
  say "!! [2/8] freshness_legs.json is $LEGS_NOW, not the last recorded $LEGS_FROM (the parent has moved it) - nothing installed; read it and re-pin"; exit 1; fi
fi
say "[2/8] live pins exact (spine_build $SB_FROM · legs $LEGS_NOW)"
mkdir -p "$WALK/compile" || exit 1
cp -p spine_build.py apply_legs_s338.py selftest_s338.py "$WALK/compile/" \
  && ( cd "$WALK/compile" && "$SPY" -m py_compile spine_build.py apply_legs_s338.py selftest_s338.py && "$VPY" -m py_compile spine_build.py apply_legs_s338.py selftest_s338.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green on both pythons (on copies)"
SOUT="$( cd "$WALK/compile" && "$VPY" -B "$KDIR/selftest_s338.py" --legs "$LEGS" --freshness "$FIN/freshness.py" 2>&1 )"
echo "$SOUT" | grep -E '^  (ok|FAIL)|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -qE "^selftest: ([0-9]+)/\1$" || { say "!! [4/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest green on copies of the live legs file, with freshness.py's own loader"
rm -rf "$WALK"
BAK="$SP/spine_build.py.bak_S338_${SB_FROM:0:8}"
\cp -p "$SP/spine_build.py" "$BAK" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$SP/spine_build.py"; rm -f "$SP/spine_state.json"
  LB="$(ls -t "$LEGS".bak_S338_* 2>/dev/null | head -1)"; [ -n "$LB" ] && \cp -p "$LB" "$LEGS"
  say "   spine_build.py $(m5 "$SP/spine_build.py") · spine_state.json removed · legs $(m5 "$LEGS")"
  exit 1
}
\cp -p spine_build.py "$SP/spine_build.py" && [ "$(m5 "$SP/spine_build.py")" = "$SB_TO" ] || restore
say "[5/8] placed $SB_TO; backup $BAK"
BOUT="$( cd "$SP" && flock -w 170 /tmp/spine.lock "$VPY" -B spine_build.py --readings readings --out spine.db --finance-db "$FIN/finance.db" 2>&1 | tail -3 )"
echo "$BOUT" | sed 's/^/   /'
echo "$BOUT" | grep -q "SPINE BUILT AND SWAPPED" && [ -s "$SP/spine_state.json" ] || restore
say "[6/8] one build run now under the spine's own lock; spine_state.json written"
"$VPY" -B apply_legs_s338.py --file "$LEGS" --from "${LEGS_FROM:0:8}" | sed 's/^/   /' || restore
grep -q '"Marg spine gate (S331)"' "$LEGS" || restore
V="$( cd "$FIN" && "$VPY" -B -c "
import json, freshness as f
legs = f.load_legs('$LEGS', {'STATE_FILE': '/tmp/none'})
bad = [(l['name'], l['bad']) for l in legs if l.get('bad')]
mine = [l for l in legs if l['name'].startswith('Marg spine')]
st = json.load(open('$SP/spine_state.json'))
print('legs %d, bad %d, spine legs %d · state gate %s passed %s · %s' % (len(legs), len(bad), len(mine), st['gate'], st['passed'], st['status'][:160]))
" 2>&1 )"
say "[7/8] $V"
echo "$V" | grep -q "bad 0, spine legs 2 · state gate .* passed True" || restore
say "[8/8] no restart needed: freshness.py reads the legs on its next run; the build writes the state every 10 min 08-23"
md5sum "$SP/spine_build.py" "$LEGS"
say "$KIT: DONE -- the health page gains 'Marg spine gate (S331)' and 'Marg spine compare (S331)' at its next run"
