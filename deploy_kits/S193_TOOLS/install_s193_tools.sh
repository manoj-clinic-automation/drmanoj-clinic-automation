#!/bin/bash
# S193_TOOLS · dr_query.py — the standard READ-ONLY box query tool (mode=ro).
set -u; cd "$(dirname "$0")"
DEST=/root/deploy/dr_query.py
echo "==============================================================="
echo " S193_TOOLS · dr_query.py (read-only DB query tool)"
echo "==============================================================="
echo "[1/3] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/3] install -> $DEST"; cp dr_query.py "$DEST"; chmod +x "$DEST"
echo "[3/3] selftest (read-only)"
python3 "$DEST" selftest 2>&1 | tail -1 | grep -q "SELFTEST OK" || { echo '*** RED: selftest failed.'; exit 1; }
echo "==============================================================="
echo " GREEN. Installed. Examples:"
echo "   python3 /root/deploy/dr_query.py day    2026-08-17"
echo "   python3 /root/deploy/dr_query.py marg   2026-08-17"
echo "   python3 /root/deploy/dr_query.py cash   30"
echo "   python3 /root/deploy/dr_query.py custody"
echo "   python3 /root/deploy/dr_query.py sql \"SELECT ...\"   (SELECT-only)"
echo "==============================================================="
