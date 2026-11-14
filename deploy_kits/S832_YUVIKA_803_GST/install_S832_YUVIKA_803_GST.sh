#!/bin/bash
# install_S832_YUVIKA_803_GST.sh -- kit S832 (14-Nov-2026, Sanjeevni session 459): one tap job on Amir's card -- Yuvika bill 803 (06-11):
# the XXL line's 5% GST, so Marg's total becomes Rs 1,410 as the revised paper (scan B-0272). Data only (amir_job); no file changes; no restart.
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S832_YUVIKA_803_GST/install_S832_YUVIKA_803_GST.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KDIR" || exit 1
DB="${DB:-/root/finance/finance.db}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! SUMS.md5 gate failed - nothing written"; exit 1; }
[ -f "$DB" ] || { echo "!! $DB missing - nothing written"; exit 1; }
R=$(cd /tmp && "$VPY" -B "$KDIR/s832_job.py" "$DB" ${DRY:+--dry} 2>&1); echo "$R"
case "$R" in S832:\ added*|S832:\ ALREADY*|S832:\ DRY*) ;; *) echo "!! S832 did not finish - see above"; exit 1;; esac
echo "undo (one line): $VPY -c \"import sqlite3;c=sqlite3.connect('$DB');c.execute(\\\"DELETE FROM amir_job WHERE key='fix:S832:YUVIKA 803'\\\");c.commit()\""
echo ""
echo "S832_YUVIKA_803_GST: DONE. Amir's card now asks him to put 5% GST on the XXL line of Yuvika bill 803 (total Rs 1,410)."
