#!/bin/bash
# =============================================================================
#  install_S240_MARG_INGEST.sh · kit S240_MARG_INGEST · D467 Phase 1 (SHADOW)
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_MARG_INGEST
#
#  The server's own front door for Marg exports. Every 5 minutes it reads the Marg archive that
#  the owner's PC already mirrors to Google Drive, runs THE SAME ROUTER the PC runs, keeps the
#  PHI-free files, reads sale reports into PHI-free item lines (no file kept), and compares its
#  verdicts with the PC's. It SENDS NOTHING and FEEDS NO SCREEN: finance_app.py is not touched and
#  the service is not restarted. New folder /root/marg_ingest; new tables mi_* in finance.db.
#
#  If the box cannot see the Drive folder yet, it prints the ONE thing to share and stops -- no
#  schedule is added. Run the same line again after sharing.
#  Switch off any time:  touch /root/marg_ingest/OFF
# =============================================================================
set -u
KIT="S240_MARG_INGEST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${MI_PY:-/root/wa/venv/bin/python3}"
DEST="${MI_DEST:-/root/marg_ingest}"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
export MARG_INGEST_DB="$DB"
LOG="$DEST/logs/ingest.log"
TAG="# S240_MARG_INGEST"
red() { echo "!! RED -- $*"; exit 1; }

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum marg_ingest.py | awk '{print $1}')" ] || red "KIT_ID does not match marg_ingest.py (F-88)"
[ -x "$PY" ] || red "$PY not found"
$PY -c "import google.oauth2, requests" 2>/dev/null || red "the venv lacks google-auth/requests (docterz_ingest's own libraries)"
[ -f "$DB" ] || red "$DB not found"
echo "-- gates green"

# 1. lay the files down (a different earlier copy is kept aside, never overwritten blind)
mkdir -p "$DEST/logs" "$DEST/work" || red "cannot create $DEST"
if [ -f "$DEST/marg_ingest.py" ] && ! cmp -s "$DEST/marg_ingest.py" marg_ingest.py; then
  \cp -f "$DEST/marg_ingest.py" "$DEST/marg_ingest.py.bak_$(date +%Y%m%d_%H%M%S)"
fi
for f in marg_ingest.py marg_router.py signatures.json xlsx_stdlib.py marg_report.py; do
  \cp -f "$f" "$DEST/$f" || red "copy $f"
done
rm -rf "$DEST/xlrd" && \cp -r xlrd "$DEST/xlrd" || red "copy xlrd"
$PY -m py_compile "$DEST/marg_ingest.py" "$DEST/marg_router.py" "$DEST/marg_report.py" || red "py_compile"
rm -rf "$DEST/__pycache__"
echo "-- files in $DEST"

# 2a. a backup of finance.db before the first write (tables are new and additive)
$PY - "$DB" "$FIN/finance.db.bak_${KIT}_$(date +%Y%m%d_%H%M%S)" <<'PYEOF' || red "finance.db backup failed"
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()
print("-- finance.db backed up to " + sys.argv[2])
PYEOF

# 2. can the box see the Drive folder?
WHO="$($PY -B $DEST/marg_ingest.py --whoami 2>&1)"
echo "-- this box reads Google Drive as: $WHO"
PROBE="$($PY -B $DEST/marg_ingest.py --dry-run --limit 3 2>&1)"; RC=$?
echo "$PROBE" | tail -6 | sed 's/^/     /'
if echo "$PROBE" | grep -q "HTTP 404\|HTTP 403\|listed 0,"; then
  echo ""
  echo "== ONE STEP FOR YOU (nothing was scheduled) =="
  echo "   In Google Drive (drmka.ortho), share the folder  Clinic Data Archive  with"
  echo "   $WHO   as Viewer, then run the same line again:"
  echo "   bash /root/deploy/vps_deploy.sh $KIT"
  exit 3
fi
[ "$RC" = "0" ] || red "the trial read failed -- nothing scheduled"

# 4. the first real run (the backlog; anything past 400 files is taken by the schedule)
echo "-- first run (this can take a few minutes on the first day's backlog)..."
$PY -B $DEST/marg_ingest.py 2>&1 | tail -4 | sed 's/^/     /'

# 5. the schedule: every 5 minutes, one lock; replaces only its own line
BK="$DEST/logs/crontab.bak_$(date +%Y%m%d_%H%M%S)"
crontab -l > "$BK" 2>/dev/null || : > "$BK"
OTHERS_BEFORE="$(grep -vc "$TAG" "$BK")"
{ grep -v "$TAG" "$BK"
  echo "*/5 * * * * flock -n /tmp/marg_ingest.lock $PY -B $DEST/marg_ingest.py >> $LOG 2>&1 $TAG"
} | crontab - || { crontab "$BK"; red "could not write the crontab (restored)"; }
OTHERS_AFTER="$(crontab -l | grep -vc "$TAG")"
[ "$(crontab -l | grep -c "$TAG")" = "1" ] && [ "$OTHERS_BEFORE" = "$OTHERS_AFTER" ] \
  || { crontab "$BK"; red "crontab check failed (restored)"; }
echo "-- scheduled every 5 minutes; every other crontab line unchanged ($OTHERS_AFTER)"

# 6. what the server now holds, and whether it agrees with the PC
cd "$FIN" && $PY - "$DB" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
n = c.execute("SELECT COUNT(*) FROM mi_file").fetchone()[0]
print("-- the server has read %d export file(s):" % n)
for t, v, k, cnt in c.execute("SELECT type, verdict, kept, COUNT(*) FROM mi_file GROUP BY 1,2,3 ORDER BY 1"):
    print("     %-24s %-9s %-10s %d" % (t or "?", v, "file kept" if k else "no file", cnt))
ag = dict(c.execute("SELECT agree, COUNT(*) FROM mi_file GROUP BY agree").fetchall())
print("-- agrees with the PC's own verdict: %d · differs: %d · PC has no row: %d"
      % (ag.get("yes", 0), ag.get("NO", 0), ag.get("", 0)))
print("-- sale item lines held (no names, no phones): %d"
      % c.execute("SELECT COUNT(*) FROM mi_sale_line").fetchone()[0])
PYEOF
echo ""
echo "PINS  /root/marg_ingest/marg_ingest.py $(md5sum $DEST/marg_ingest.py | awk '{print $1}')"
echo ""
echo "$KIT GREEN -- the server now reads every Marg export itself, in shadow. Nothing it does reaches the books yet."
