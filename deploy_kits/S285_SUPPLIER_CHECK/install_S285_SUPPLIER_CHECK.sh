#!/bin/bash
# install_S285_SUPPLIER_CHECK.sh -- Amir's bill list warns when a bill names a
# supplier who has never supplied that item while another supplier always has,
# offers "Supplier galat likha" under Theek nahi, and drops from his list any bill
# that no live export carries any more (the corrected-away bill clears itself).
#
# Five anchored edits and one helper in /root/finance/amir_day.py, patched ON THE
# BOX from its exact live bytes. No table, no setting, nothing on manojz.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S285_SUPPLIER_CHECK/install_S285_SUPPLIER_CHECK.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
AD_FROM="a9f2062267ebac59e02fdb0f88e775de"
AD_TO="b3c20319c4808ebc64bec197c951468c"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S285_SUPPLIER_CHECK installer =="; echo "target : $FIN/amir_day.py"; echo "python : $PY"
[ -f "$FIN/amir_day.py" ] || { echo "REFUSED: $FIN/amir_day.py not found"; exit 1; }
AD="$(md5of "$FIN/amir_day.py")"
echo "amir_day.py : from $AD_FROM -> to $AD_TO ; live $AD"
if [ "$AD" = "$AD_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$AD" = "$AD_FROM" ] || { echo "REFUSED: amir_day.py is $AD, expected $AD_FROM"; exit 1; }

BAK="$FIN/amir_day.py.bak_S285_${AD_FROM:0:8}"
\cp -p "$FIN/amir_day.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring amir_day.py byte-identically"; \cp -p "$BAK" "$FIN/amir_day.py"
  rm -f "$FIN/amir_day.py.S285new"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/amir_day.py"; exit 1; }

\cp -p "$FIN/amir_day.py" "$FIN/amir_day.py.S285new"
"$PY" -B "$KIT_DIR/patch_supplier_check_s285.py" --file "$FIN/amir_day.py.S285new" --from "$AD_FROM" || restore
NEW="$(md5of "$FIN/amir_day.py.S285new")"
[ "$NEW" = "$AD_TO" ] || { echo "!! patched file is $NEW, predicted $AD_TO"; restore; }
mv "$FIN/amir_day.py.S285new" "$FIN/amir_day.py" || restore
rm -f "$FIN/amir_day.py.S285new.bak_S285_${AD_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/amir_day.py" || restore; echo "smoke  : py_compile OK"

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/amir/api/healthz || true)
  echo "health : $code"
fi
echo "md5sum of the installed file:"; md5sum "$FIN/amir_day.py"
echo "S285_SUPPLIER_CHECK: DONE"
echo "read next: https://followup.dr-manoj.in/finance/amir/step/4"
