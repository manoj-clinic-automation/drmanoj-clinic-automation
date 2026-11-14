#!/bin/bash
# install_S829_SEPT_COUNT_KTROS.sh -- kit S829 (14-Nov-2026, Sanjeevni session 457; F-1232, D976): one tap job on Amir's card --
# KT ROS DT STOCK ISSUE 6:11, the 6-Sep count's lot-3 voucher that never reached Marg. Data only (amir_job); no file changes; no restart.
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S829_SEPT_COUNT_KTROS/install_S829_SEPT_COUNT_KTROS.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KDIR" || exit 1
DB="${DB:-/root/finance/finance.db}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! SUMS.md5 gate failed - nothing written"; exit 1; }
[ -f "$DB" ] || { echo "!! $DB missing - nothing written"; exit 1; }
R=$(cd /tmp && "$VPY" -B "$KDIR/s829_job.py" "$DB" ${DRY:+--dry} 2>&1); echo "$R"
case "$R" in S829:\ added*|S829:\ ALREADY*|S829:\ DRY*) ;; *) echo "!! S829 did not finish - see above"; exit 1;; esac
echo "undo (one line): $VPY -c \"import sqlite3;c=sqlite3.connect('$DB');c.execute(\\\"DELETE FROM amir_job WHERE key='S829:ktros:sept-count-lot3'\\\");c.commit()\""
echo ""
echo "S829_SEPT_COUNT_KTROS: DONE. Amir's card now asks him to key the KT ROS DT stock issue (6:11) the 6-September count needed."
