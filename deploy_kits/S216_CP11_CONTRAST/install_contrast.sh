#!/bin/bash
# S216_CP11_CONTRAST - PAGE ONLY, CSS ONLY. casepack_portal.py NOT installed.
set -e
K=$(cd "$(dirname "$0")" && pwd)
TS=$(date +%Y%m%d_%H%M%S)
\cp -v /root/wa/casepack/casepack_page.html "/root/wa/casepack/casepack_page.html.bak_S216_CONTRAST_$TS"
\cp -v "$K/casepack_page.html" /root/wa/casepack/casepack_page.html
systemctl restart clinic-portal 2>/dev/null || systemctl restart clinic-portal.service
sleep 2
systemctl is-active clinic-portal 2>/dev/null || systemctl is-active clinic-portal.service
cd "$K" && /root/wa/venv/bin/python3 selftest_casepack.py
echo "--- PINS (paste these back) ---"
md5sum /root/portal/casepack_portal.py /root/wa/casepack/casepack_page.html
