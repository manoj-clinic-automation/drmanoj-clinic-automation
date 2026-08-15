#!/bin/bash
# =============================================================================
#  finance_backup.sh  ·  Session 179
#
#  finance.db holds the money history and, once lines are ingested, patient
#  names. Until now the only copies of it were the *.bak files my install
#  scripts happened to leave behind — which is not a backup, it is a side
#  effect. This is the backup.
#
#  * uses sqlite3's own .backup, so a copy taken mid-write is still consistent
#    (cp on a live WAL database can produce a file that will not open)
#  * verifies every copy opens and answers a query BEFORE trusting it
#  * keeps 30 days, and one copy per month kept for a year
#  * refuses to delete anything if today's backup did not verify
#
#  Install:  cp finance_backup.sh /root/finance/ && chmod +x /root/finance/finance_backup.sh
#  Cron:     5 1 * * *  /root/finance/finance_backup.sh >> /root/finance/backup.log 2>&1
# =============================================================================
set -u
SRC=/root/finance/finance.db
DIR=/root/backups/finance
KEEP_DAILY=30
STAMP=$(date +%Y-%m-%d_%H%M%S)
DAY=$(date +%Y-%m-%d)
OUT="$DIR/finance_$STAMP.db"

log(){ echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

[ -f "$SRC" ] || { log "FATAL: $SRC not found"; exit 1; }
mkdir -p "$DIR" && chmod 700 "$DIR"

# ---- take the copy the safe way -------------------------------------------
if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 "$SRC" ".backup '$OUT'" || { log "FATAL: sqlite3 .backup failed"; exit 2; }
else
  /usr/bin/python3 - "$SRC" "$OUT" <<'PYBK' || { log "FATAL: python backup failed"; exit 2; }
import sqlite3, sys
src, dst = sys.argv[1], sys.argv[2]
s = sqlite3.connect(src); d = sqlite3.connect(dst)
with d:
    s.backup(d)
d.close(); s.close()
PYBK
fi
chmod 600 "$OUT"

# ---- verify it before trusting it -----------------------------------------
VERIFY=$(/usr/bin/python3 - "$OUT" <<'PYCK'
import sqlite3, sys
try:
    c = sqlite3.connect(sys.argv[1])
    ok = c.execute("PRAGMA integrity_check").fetchone()[0]
    days = c.execute("SELECT COUNT(*) FROM day_entry").fetchone()[0]
    c.close()
    print("%s|%d" % (ok, days))
except Exception as ex:
    print("FAIL|%s" % ex)
PYCK
)
STATE=${VERIFY%%|*}
DAYS=${VERIFY##*|}
if [ "$STATE" != "ok" ]; then
  log "FATAL: backup did not verify ($VERIFY) — keeping it for inspection, pruning NOTHING"
  exit 3
fi
log "ok  $(basename "$OUT")  $(du -h "$OUT" | cut -f1)  ${DAYS} day-entries"

# ---- keep one copy per month, for a year ----------------------------------
MONTHLY="$DIR/monthly"; mkdir -p "$MONTHLY" && chmod 700 "$MONTHLY"
MTAG=$(date +%Y-%m)
[ -f "$MONTHLY/finance_$MTAG.db" ] || { cp -a "$OUT" "$MONTHLY/finance_$MTAG.db"; log "kept monthly copy $MTAG"; }
find "$MONTHLY" -name 'finance_*.db' -mtime +400 -print -delete | sed 's/^/pruned monthly /'

# ---- prune dailies, only now that today's copy is proven ------------------
PRUNED=$(find "$DIR" -maxdepth 1 -name 'finance_*.db' -mtime +$KEEP_DAILY -print -delete | wc -l)
[ "$PRUNED" -gt 0 ] && log "pruned $PRUNED daily copies older than $KEEP_DAILY days"

COUNT=$(find "$DIR" -maxdepth 1 -name 'finance_*.db' | wc -l)
log "held: $COUNT daily, $(find "$MONTHLY" -name 'finance_*.db' | wc -l) monthly, in $DIR"

# ---- one honest warning ---------------------------------------------------
# These copies sit on the SAME DISK as the original. That protects against a
# bad deployment or a wrong DELETE, which are the likely failures — but not
# against losing the VPS. An off-box copy is a decision for the owner, because
# this file contains patient names and should not be sent somewhere casually.
[ -d /root/backups/finance/offsite ] || log "note: local copies only — no off-box copy configured"
