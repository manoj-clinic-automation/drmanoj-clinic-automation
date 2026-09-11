#!/usr/bin/env bash
# =============================================================================
#  install_docterz_live.sh · kit S238_DOCTERZ_LIVE
#  Run by:  bash /root/deploy/vps_deploy.sh S238_DOCTERZ_LIVE
#
#  The owner, 11-Sep-2026: "the Docterz revenue system is not getting updated
#  since we set it up on 3rd Sept — make it live again."
#  WHY: the day sheets keep arriving in Drive every morning, but the reader
#  (/root/finance/docterz_ingest.py) was only ever run BY HAND — its nightly
#  line was an optional step of S223 that was never added (S230 recorded it).
#  THIS KIT: (1) proves the live reader is the S223_SPLIT_LEGS file it was built
#  as, (2) backs up finance.db, (3) runs the reader once to catch up every day
#  since 03-Sep, (4) adds ONE cron line so it runs itself 3x a day from now on.
#  No code changes. Red path: nothing is scheduled if the catch-up run fails;
#  the backup is kept.
# =============================================================================
set -u
KIT="S238_DOCTERZ_LIVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN_DIR:-/root/finance}"
ING="$FIN/docterz_ingest.py"; PIN=80bf760dd6103504776964c58d876f17   # S223_SPLIT_LEGS
DB="$FIN/finance.db"
PY="${PY:-/root/wa/venv/bin/python3}"
LOG="$FIN/logs/docterz_ingest.log"
TAG="# S238_DOCTERZ_LIVE: Docterz day revenue, 09:40 13:40 19:40 IST"
# the runs are 09:40, 13:40 and 19:40 IST whatever the server clock is set to
WHEN="$(python3 -c 'import time
off = -time.altzone if time.localtime().tm_isdst > 0 else -time.timezone
ist = [9*60+40, 13*60+40, 19*60+40]
loc = [(m - 330 + off // 60) % 1440 for m in ist]
mins = {m % 60 for m in loc}
print("%d %s" % (loc[0] % 60, ",".join(str(m // 60) for m in loc)) if len(mins) == 1 else "40 9,13,19")' 2>/dev/null || echo "40 9,13,19")"
LINE="$WHEN * * * flock -n /tmp/docterz_ingest.lock $PY -B $ING >> $LOG 2>&1 $TAG"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/6] SUMS.md5 gate failed — nothing done"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/6] KIT_ID names another kit — nothing done"; exit 1; }
echo "[1/6] kit gates green"
[ "$(md5of "$ING")" = "$PIN" ] || { echo "!! [2/6] $ING is $(md5of "$ING"), not the S223_SPLIT_LEGS reader $PIN — nothing done"; exit 1; }
[ -f "$DB" ] || { echo "!! [2/6] no $DB — nothing done"; exit 1; }
command -v flock >/dev/null 2>&1 || LINE="$WHEN * * * $PY -B $ING >> $LOG 2>&1 $TAG"
echo "[2/6] the live reader is the pinned S223_SPLIT_LEGS file · server clock $(date +%Z) · schedule '$WHEN * * *' = 09:40/13:40/19:40 IST"
state(){ "$PY" - "$DB" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
try:
    n, last = c.execute("SELECT COUNT(*), MAX(business_date) FROM clinic_day_revenue").fetchone()
    print("%s days, newest %s" % (n, last))
except Exception as e:
    print("unreadable (%s)" % e)
PY
}
BEFORE="$(state)"
TS=$(date +%Y%m%d_%H%M%S); BAK="$DB.bak_${KIT}_$TS"
"$PY" - "$DB" "$BAK" <<'PY' || { echo "!! [3/6] backup failed — nothing done"; exit 1; }
import sqlite3, sys
src = sqlite3.connect(sys.argv[1]); dst = sqlite3.connect(sys.argv[2])
src.backup(dst); dst.close(); src.close()
PY
chmod 600 "$BAK"
echo "[3/6] finance.db backed up: $BAK"
mkdir -p "$FIN/logs"
echo "[4/6] catch-up run (reads every new day sheet from Drive):"
echo "=== $(date '+%F %T') catch-up by $KIT ===" >> "$LOG"
"$PY" -B "$ING" 2>&1 | tee -a "$LOG" | sed 's/^/    /' | tail -25
RC=${PIPESTATUS[0]}
AFTER="$(state)"
echo "    clinic_day_revenue before: $BEFORE"
echo "    clinic_day_revenue after:  $AFTER"
if [ "$RC" != "0" ]; then
  echo "!! [4/6] the reader reported a failure (exit $RC) — NOT scheduling it. Backup kept: $BAK"
  exit 1
fi
CUR="$(crontab -l 2>/dev/null)"
printf '%s\n' "$CUR" > "$FIN/logs/crontab.bak_${KIT}_$TS"
if printf '%s\n' "$CUR" | grep -q "docterz_ingest.py"; then
  echo "[5/6] a docterz_ingest line is already in the crontab — left as it is:"
  printf '%s\n' "$CUR" | grep "docterz_ingest.py" | sed 's/^/    /'
else
  { [ -n "$CUR" ] && printf '%s\n' "$CUR"; printf '%s\n' "$LINE"; } | crontab - \
    || { echo "!! [5/6] could not write the crontab — the catch-up above stands; nothing scheduled"; exit 1; }
  [ "$(crontab -l | grep -c 'docterz_ingest.py')" = "1" ] \
    || { echo "!! [5/6] crontab check failed — restoring it"; crontab "$FIN/logs/crontab.bak_${KIT}_$TS"; exit 1; }
  echo "[5/6] scheduled: every day at 09:40, 13:40 and 19:40 IST (crontab backed up beside the log)"
fi
echo "[6/6] GREEN"
echo
echo "  Day Revenue:  https://followup.dr-manoj.in/finance/clinic/day"
echo "  Log:          $LOG"
