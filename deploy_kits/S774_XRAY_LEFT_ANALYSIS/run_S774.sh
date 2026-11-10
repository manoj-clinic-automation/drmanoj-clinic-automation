#!/bin/bash
# S774_XRAY_LEFT_ANALYSIS -- READ-ONLY. A scratch copy of finance.db in /tmp (deleted after); the live records.py imported read-only;
# counts by mail. Nothing live is written. About one minute.
set -u
K="$(cd "$(dirname "$0")" && pwd)"
S=$(mktemp -d /tmp/s774.XXXX); chmod 700 "$S"
/usr/bin/python3 -c "import sqlite3,sys; s=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro', uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" /root/finance/finance.db "$S/s774.db" || { echo "S774: could not copy the database"; rm -rf "$S"; exit 1; }
mkdir -p "$S/app" && cp /root/finance/records.py "$S/app/"
(cd "$S" && timeout 600 /usr/bin/python3 -W ignore -B "$K/analyse_s774.py" "$S/app" "$S/s774.db" 2>&1 | tail -3)
rm -rf "$S"
echo "S774_ANALYSIS: DONE -- read-only; the counts are in the clinic mailbox"
