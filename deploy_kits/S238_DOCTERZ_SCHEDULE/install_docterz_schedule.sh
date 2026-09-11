#!/usr/bin/env bash
# =============================================================================
#  install_docterz_schedule.sh · kit S238_DOCTERZ_SCHEDULE
#  Run by:  bash /root/deploy/vps_deploy.sh S238_DOCTERZ_SCHEDULE
#
#  The owner, 11-Sep-2026: "add extra runs, every 10 minutes till 12 noon, then
#  at 1.40 pm and 7.40 pm" -- and then: "the bank MPR of the day's transactions
#  arrives not before 9.30 am next day, so a first run before that is not very
#  useful". So: every 10 minutes 09:30-12:00, then 13:40 and 19:40 IST. It is cheap and safe to repeat: unchanged sheets are
#  skipped; flock stops two runs overlapping.
#  Replaces the single S223 line (25 9 * * *). Touches no other crontab line.
#  Red path: the crontab is restored from its backup.
# =============================================================================
set -u
KIT="S238_DOCTERZ_SCHEDULE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN_DIR:-/root/finance}"
ING="$FIN/docterz_ingest.py"
PY="${PY:-/root/wa/venv/bin/python3}"
LOG="$FIN/logs/docterz_ingest.log"
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/4] SUMS.md5 gate failed — nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/4] KIT_ID names another kit — nothing changed"; exit 1; }
[ -f "$ING" ] || { echo "!! [1/4] no $ING — nothing changed"; exit 1; }
echo "[1/4] kit gates green · server clock $(date +%Z)"
[ "$(date +%z)" = "+0530" ] || { echo "!! [1/4] the server clock is not IST — the times below would be wrong; nothing changed"; exit 1; }
mkdir -p "$FIN/logs" || { echo "!! cannot create $FIN/logs"; exit 1; }
LK="flock -n /tmp/docterz_ingest.lock"; command -v flock >/dev/null 2>&1 || LK=""
CMD="$LK $PY -B $ING >> $LOG 2>&1"
TAG="# S238_DOCTERZ_SCHEDULE"
TS=$(date +%Y%m%d_%H%M%S); BK="$FIN/logs/crontab.bak_${KIT}_$TS"
crontab -l > "$BK" 2>/dev/null || : > "$BK"
echo "[2/4] crontab backed up: $BK"
echo "      docterz line(s) now:"; grep "docterz_ingest.py" "$BK" | sed 's/^/        /'
{ grep -v "docterz_ingest.py" "$BK"
  echo "30-50/10 9 * * * $CMD $TAG every 10 min from 09:30 IST"
  echo "*/10 10-11 * * * $CMD $TAG every 10 min 10:00-11:50 IST"
  echo "0 12 * * * $CMD $TAG 12:00 IST"
  echo "40 13,19 * * * $CMD $TAG 13:40 and 19:40 IST"
} | crontab - || { echo "!! [3/4] could not write the crontab — restoring"; crontab "$BK"; exit 1; }
NEW="$(crontab -l 2>/dev/null)"
OTHERS_BEFORE="$(grep -vc "docterz_ingest.py" "$BK")"
OTHERS_AFTER="$(printf '%s\n' "$NEW" | grep -vc "docterz_ingest.py")"
if [ "$(printf '%s\n' "$NEW" | grep -c "docterz_ingest.py")" != "4" ] || [ "$OTHERS_BEFORE" != "$OTHERS_AFTER" ]; then
  echo "!! [3/4] crontab check failed — restoring the backup"; crontab "$BK"; exit 1
fi
echo "[3/4] docterz line(s) now:"; printf '%s\n' "$NEW" | grep "docterz_ingest.py" | sed 's/^/        /'
echo "      every other crontab line unchanged ($OTHERS_AFTER)"
echo "[4/4] GREEN — the reader runs every 10 minutes 09:30-12:00, then 13:40 and 19:40 IST"
echo
echo "  Day Revenue:  https://followup.dr-manoj.in/finance/clinic/day"
echo "  Reverse:      crontab $BK"
