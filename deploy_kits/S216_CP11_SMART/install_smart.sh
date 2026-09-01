#!/bin/bash
# S216_CP11_SMART - PAGE ONLY. CP-1.1 steps 3 (auto-select) and 5 (transliteration).
set -e
K=$(cd "$(dirname "$0")" && pwd)
TS=$(date +%Y%m%d_%H%M%S)
\cp -v /root/wa/casepack/casepack_page.html "/root/wa/casepack/casepack_page.html.bak_S216_SMART_$TS"
\cp -v "$K/casepack_page.html" /root/wa/casepack/casepack_page.html
systemctl restart clinic-portal 2>/dev/null || systemctl restart clinic-portal.service
sleep 2
systemctl is-active clinic-portal 2>/dev/null || systemctl is-active clinic-portal.service
cd "$K" && /root/wa/venv/bin/python3 selftest_casepack.py
echo "--- PINS (paste these back) ---"
md5sum /root/portal/casepack_portal.py /root/wa/casepack/casepack_page.html
