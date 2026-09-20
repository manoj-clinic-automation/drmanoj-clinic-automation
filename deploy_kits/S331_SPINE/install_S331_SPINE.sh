#!/bin/bash
# install_S331_SPINE.sh -- S272 / kit S331 (Sanjeevni). Rungs 1-3 of S272_SPINE_ARCHITECTURE.
#
#   cd /root/deploy/repo && bash deploy_kits/S331_SPINE/install_S331_SPINE.sh
#   ... --restore     removes the two crontab lines and restores the crontab backup; the folder is left (nothing reads it)
#
# WHAT IT TOUCHES: a NEW folder /root/finance/spine/ and TWO lines in root's crontab (declared for the parent).
# WHAT IT DOES NOT TOUCH: any existing file, any table of finance.db (opened read-only for one COUNT), the collector,
# the archive, the 06-Sep stock check. If the gate does not pass on the box, no cron line is written and it says so.
set -u
KIT="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-}"                                   # rehearsal: a fake root
PY="${PY:-/root/wa/venv/bin/python3}"
DEST="$ROOT/root/finance/spine"
FIN="$ROOT/root/finance/finance.db"
SRC="${SPINE_SOURCE:-drive}"                       # rehearsal: a local folder laid out like the archive
CRONTAB="${CRONTAB_CMD:-crontab}"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILES="marg_read.py spine_evidence.py spine_build.py spine_read.py spine_compare.py spine_rules.json selftest_spine.py"
TAG="# S331_SPINE"
say() { echo "[$1] $2"; }
die() { echo "REFUSED at $1 -- $2"; echo "S331_SPINE: nothing further done."; exit 1; }

if [ "${1:-}" = "--restore" ]; then
  B="$(ls -t "$ROOT"/root/finance/crontab.bak_S331_* 2>/dev/null | head -1)"
  [ -n "$B" ] || die restore "no crontab backup from S331 found"
  $CRONTAB "$B" && say restore "crontab restored from $B; /root/finance/spine/ left in place (nothing reads it)"
  exit 0
fi

say 1/8 "kit sums"
( cd "$KIT" && md5sum -c SUMS.md5 --quiet ) || die 1/8 "SUMS.md5 does not verify inside $KIT"
say 2/8 "python and readers"
[ -x "$PY" ] || die 2/8 "$PY missing"
"$PY" -c "import xlrd, sqlite3" || die 2/8 "$PY cannot import xlrd"
[ -n "$ROOT" ] || "$PY" -c "import sys; sys.path.insert(0,'/root/marg_ingest'); import marg_ingest, xlsx_stdlib" || die 2/8 "the collector's modules do not import"
say 3/8 "destination"
mkdir -p "$DEST/readings" || die 3/8 "cannot make $DEST"
ALREADY=1
for f in $FILES; do
  if [ -f "$DEST/$f" ]; then
    if [ "$(md5sum < "$DEST/$f")" != "$(md5sum < "$KIT/$f")" ]; then
      grep -q "S331" "$DEST/$f" 2>/dev/null || die 3/8 "$DEST/$f exists and is not from this kit -- a later kit owns it"
      ALREADY=0
    fi
  else ALREADY=0; fi
done
if [ $ALREADY = 1 ] && $CRONTAB -l 2>/dev/null | grep -q "$TAG"; then
  say 3/8 "ALREADY INSTALLED -- every file equals the kit and the cron lines are present"
  "$PY" -B "$DEST/spine_read.py" status; exit 0
fi
say 4/8 "placing files"
for f in $FILES; do cp "$KIT/$f" "$DEST/$f" || die 4/8 "copy $f"; done
say 5/8 "selftest on the box"
( cd "$DEST" && "$PY" -B selftest_spine.py ) || die 5/8 "selftest red -- files placed, nothing scheduled"
say 6/8 "the evidence store: every export in the archive, read once, PHI-free"
( cd "$DEST" && "$PY" -B spine_evidence.py --source "$SRC" --out readings --limit 1000 ) || die 6/8 "the evidence run failed"
N=$(ls "$DEST/readings" | grep -c '\.json$')
SEED=$("$PY" -c "
import json,glob
print(sum(1 for f in glob.glob('$DEST/readings/*.json') if json.load(open(f)).get('family')=='SALE_BILLWISE' and json.load(open(f))['data'].get('date_from','9')<'2026-08-16'))")
say 6/8 "$N readings; back-fill sale readings (April-15 Aug) present: $SEED"
[ "$SEED" -ge 9 ] || die 6/8 "the back-fill seed (MargArchive/_SPINE_SEED, 9 readings) has not reached the archive mirror yet -- run this again after the next manojz pull"
say 7/8 "building the spine and running the gate (acceptance: stock must equal Marg at the latest closing)"
( cd "$DEST" && "$PY" -B spine_build.py --readings readings --out spine.db --finance-db "$FIN" --acceptance ) || die 7/8 "the gate did not pass -- no spine swapped in, nothing scheduled; read $DEST/spine.db.failed with spine_read.py gate"
( cd "$DEST" && "$PY" -B spine_compare.py --finance-db "$FIN" --spine spine.db ) || die 7/8 "compare failed"
say 8/8 "crontab: two lines tagged $TAG"
$CRONTAB -l > "$ROOT/root/finance/crontab.bak_S331_$STAMP" 2>/dev/null || : > "$ROOT/root/finance/crontab.bak_S331_$STAMP"
if ! grep -q "$TAG" "$ROOT/root/finance/crontab.bak_S331_$STAMP"; then
  { cat "$ROOT/root/finance/crontab.bak_S331_$STAMP"
    echo "*/10 8-23 * * * cd /root/finance/spine && flock -n /tmp/spine.lock sh -c '$PY -B spine_evidence.py && $PY -B spine_build.py --readings readings --out spine.db --finance-db /root/finance/finance.db' >> /root/finance/spine/spine.log 2>&1 $TAG"
    echo "55 23 * * * cd /root/finance/spine && $PY -B spine_compare.py >> /root/finance/spine/spine.log 2>&1 $TAG"
  } | $CRONTAB - || die 8/8 "crontab write failed; backup at $ROOT/root/finance/crontab.bak_S331_$STAMP"
fi
echo "S331_SPINE: DONE -- $DEST placed, $N readings, spine.db built and gated, 2 cron lines."
"$PY" -B "$DEST/spine_read.py" status
for f in $FILES; do echo "  $(md5sum < "$DEST/$f" | cut -c1-32)  /root/finance/spine/$f"; done
