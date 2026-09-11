#!/bin/bash
# =============================================================================
#  install_S240_MARG_SHADOW.sh · kit S240_MARG_SHADOW · D467 Phase 1b (SHADOW)
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_MARG_SHADOW
#
#  The server now WORKS THE STOCK OUT ITSELF and compares. It runs the PC's own computation --
#  push_expected.py 4b3b700c, vendored unchanged with the modules it imports -- over what
#  marg_ingest collected, and sets the answer against what the PC pushed to stock_feed, over the
#  SAME evidence (only the exports the PC had when it pushed).
#  It sends nothing, applies nothing and changes no screen. finance_app.py is untouched; no restart.
#  Also quietens google-auth's Python-3.9 warning in the 5-minute log (marg_ingest.py e0cbe6e9 -> new).
#
#  Needs S240_MARG_INGEST already in place. Switch-off: touch /root/marg_ingest/OFF
# =============================================================================
set -u
KIT="S240_MARG_SHADOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${MI_PY:-/root/wa/venv/bin/python3}"
DEST="${MI_DEST:-/root/marg_ingest}"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
export MARG_INGEST_DB="$DB"
LOG="$DEST/logs/shadow.log"
TAG="# S240_MARG_SHADOW"
INGEST_PIN_OLD="e0cbe6e9d42a9fd1b186bac2f56a9a50"
red() { echo "!! RED -- $*"; exit 1; }

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum marg_shadow.py | awk '{print $1}')" ] || red "KIT_ID does not match marg_shadow.py (F-88)"
[ -x "$PY" ] || red "$PY not found"
[ -f "$DEST/marg_ingest.py" ] || red "$DEST/marg_ingest.py is not there -- install S240_MARG_INGEST first"
[ -d "$DEST/archive" ] || red "$DEST/archive is not there -- let S240_MARG_INGEST run once first"
LIVE_ING="$(md5sum $DEST/marg_ingest.py | awk '{print $1}')"
NEW_ING="$(md5sum marg_ingest.py | awk '{print $1}')"
if [ "$LIVE_ING" != "$INGEST_PIN_OLD" ] && [ "$LIVE_ING" != "$NEW_ING" ]; then
  red "live marg_ingest.py is $LIVE_ING, neither the S240 kit's nor this one's -- nothing changed"
fi
echo "-- gates green; live marg_ingest.py ${LIVE_ING:0:8}"

# 1. the files
mkdir -p "$DEST/lib" "$DEST/logs" "$DEST/work" || red "cannot write in $DEST"
if [ "$LIVE_ING" != "$NEW_ING" ]; then
  \cp -f "$DEST/marg_ingest.py" "$DEST/marg_ingest.py.bak_${KIT}_${LIVE_ING:0:8}" || red "backup"
  \cp -f marg_ingest.py "$DEST/marg_ingest.py" || red "copy marg_ingest.py"
  echo "   marg_ingest.py ${LIVE_ING:0:8} -> ${NEW_ING:0:8} (quieter log; backup kept)"
fi
\cp -f marg_shadow.py "$DEST/marg_shadow.py" || red "copy marg_shadow.py"
\cp -f lib/*.py "$DEST/lib/" || red "copy lib"
$PY -m py_compile "$DEST/marg_shadow.py" "$DEST/marg_ingest.py" $DEST/lib/*.py || red "py_compile"
rm -rf "$DEST/__pycache__" "$DEST/lib/__pycache__"
[ -f "$DEST/shadow.json" ] || echo '{"baseline": "03-09-2026"}' > "$DEST/shadow.json"
echo "-- files in $DEST (baseline: $(cat $DEST/shadow.json))"

# 2. a backup of finance.db (the new tables are additive, but this costs nothing)
$PY - "$DB" "$FIN/finance.db.bak_${KIT}_$(date +%Y%m%d_%H%M%S)" <<'PYEOF' || red "finance.db backup failed"
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
print("-- finance.db backed up to " + sys.argv[2])
PYEOF

# 3. bring the store up to date, then compare once
echo "-- catching the store up first..."
$PY -B "$DEST/marg_ingest.py" 2>&1 | tail -3 | sed 's/^/     /'
echo "-- the server's own figure, against the PC's:"
$PY -B "$DEST/marg_shadow.py" 2>&1 | sed 's/^/     /'
RC=${PIPESTATUS[0]}
[ "$RC" = "0" ] || red "the comparison run failed (exit $RC) -- nothing scheduled"

# 4. the schedule: after the PC's 22:30 nightly push, and again in the morning
BK="$DEST/logs/crontab.bak_${KIT}_$(date +%Y%m%d_%H%M%S)"
crontab -l > "$BK" 2>/dev/null || : > "$BK"
OTHERS_BEFORE="$(grep -vc "$TAG" "$BK")"
{ grep -v "$TAG" "$BK"
  echo "20 23 * * * flock -n /tmp/marg_shadow.lock $PY -B $DEST/marg_shadow.py >> $LOG 2>&1 $TAG"
  echo "20 6 * * * flock -n /tmp/marg_shadow.lock $PY -B $DEST/marg_shadow.py >> $LOG 2>&1 $TAG"
} | crontab - || { crontab "$BK"; red "could not write the crontab (restored)"; }
OTHERS_AFTER="$(crontab -l | grep -vc "$TAG")"
[ "$(crontab -l | grep -c "$TAG")" = "2" ] && [ "$OTHERS_BEFORE" = "$OTHERS_AFTER" ] \
  || { crontab "$BK"; red "crontab check failed (restored)"; }
echo "-- scheduled 23:20 and 06:20 IST; every other crontab line unchanged ($OTHERS_AFTER)"

# 5. the record so far
$PY - "$DB" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
print("-- comparisons so far (newest first):")
for r in c.execute("SELECT started, as_on, items, same, differ, gap_units, verdict FROM sh_run "
                   "ORDER BY id DESC LIMIT 5"):
    print("     %s  as on %s  %d items · same %d · differ %d (%.0f units) · %s"
          % (r[0][:16].replace("T", " "), r[1] or "-", r[2], r[3], r[4], r[5], r[6]))
PYEOF
echo ""
echo "PINS  $DEST/marg_shadow.py $(md5sum $DEST/marg_shadow.py | awk '{print $1}')"
echo "      $DEST/marg_ingest.py $(md5sum $DEST/marg_ingest.py | awk '{print $1}')"
echo ""
echo "$KIT GREEN -- the server now works the stock out itself and compares it with the PC, twice a day."
