#!/bin/bash
# install_S291_DOCTERZ_EARLY.sh -- the Docterz Revenue screen fills minutes after the pickup, not at 09:30.
#
# The Docterz day sheet reaches Drive the moment the auto-pickup runs the tracker on the owner's PC
# (22:25 on 14-Sep, 04:50 on 16-Sep, 05:05 on 17-Sep), but the reader only started at 09:30 (S238,
# written when the sheet arrived by 09:20). Root's crontab: the four S238 lines become ONE line running
# the same command every 10 minutes, all day. No file of code changes. One writer, one source.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S291_DOCTERZ_EARLY/install_S291_DOCTERZ_EARLY.sh
#
# Undo, one line (restores the crontab byte for byte):
#   crontab /root/finance/crontab.bak_S291
set -u
KIT="S291_DOCTERZ_EARLY"; KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"; BAK="${BAK:-/root/finance/crontab.bak_S291}"
CUR="/tmp/s291_cron_now_$$.txt"; NEW="/tmp/s291_cron_new_$$.txt"
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! SUMS.md5 gate failed - nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { echo "!! KIT_ID names another kit - nothing changed"; exit 1; }
echo "[1/5] kit gates green"
crontab -l > "$CUR" 2>/dev/null || { echo "!! cannot read root's crontab - nothing changed"; exit 1; }
if grep -q "S291_DOCTERZ_EARLY" "$CUR" && ! grep -q "# S238_DOCTERZ_SCHEDULE" "$CUR"; then
  echo "ALREADY INSTALLED:"; grep "S291_DOCTERZ_EARLY" "$CUR"; rm -f "$CUR"; exit 0
fi
"$PY" -B cron_edit_s291.py "$CUR" "$NEW" || { echo "!! [2/5] editor refused - nothing changed"; rm -f "$CUR" "$NEW"; exit 1; }
echo "[2/5] new crontab text prepared"
[ -e "$BAK" ] || \cp -p "$CUR" "$BAK" || { echo "!! [3/5] backup failed - nothing changed"; exit 1; }
echo "[3/5] backup: $BAK ($(md5sum "$BAK" | awk '{print $1}'))"
crontab "$NEW" || { echo "!! [4/5] crontab refused the new text - restoring"; crontab "$BAK"; exit 1; }
crontab -l > "$CUR"
n291=$(grep -c "S291_DOCTERZ_EARLY" "$CUR"); n238=$(grep -c "# S238_DOCTERZ_SCHEDULE" "$CUR")
[ "$n291" = 1 ] && [ "$n238" = 0 ] || { echo "!! [4/5] read-back wrong (S291 $n291, S238 $n238) - restoring"; crontab "$BAK"; exit 1; }
echo "[4/5] installed and read back: 1 S291 line, 0 S238 lines"
echo "[5/5] one reader pass now, read-only (--dry-run):"
flock -n /tmp/docterz_ingest.lock "$PY" -B /root/finance/docterz_ingest.py --dry-run 2>&1 | tail -3
rm -f "$CUR" "$NEW"
echo "$KIT: DONE"
echo "read next: https://followup.dr-manoj.in/finance/clinic/day"
