#!/bin/bash
# install_S282_LINE_OWNER.sh -- F-494: a purchase line whose bill number belongs to
# two suppliers on the same day is given to the supplier the ITEMWISE export names.
#
# Bill 160 of 1 September exists twice (DAANSHI PHARMA, KEDAR PHARMACEUTICAL).
# BILLITEMWISE prints no supplier, so its five lines could not be placed and sat
# in September's total on nobody's payment sheet: Rs 17,776.68. The ITEMWISE
# export carries the same five lines WITH their owners. The rule: give the line
# to the ONE supplier ITEMWISE names for that exact (bill, date, item, amount),
# provided it is one of the candidates. Otherwise leave it alone.
#
# ONE anchored edit and one helper appended to purchase_app.py, patched ON THE BOX
# from its exact live bytes, then the one-off pass over finance.db for the lines
# already stored -- rehearsed on a COPY of the database first, written to the
# live one only if the rehearsal placed something and left nothing it should not.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S282_LINE_OWNER/install_S282_LINE_OWNER.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="3535dc978d4ec53846368c8772347a50"
PU_TO="216a0cd95afad73eecbc484683892ca3"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S282_LINE_OWNER installer =="; echo "target : $FIN/purchase_app.py + $FIN/finance.db"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
[ -f "$FIN/finance.db" ] || { echo "REFUSED: $FIN/finance.db not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then
  echo "ALREADY INSTALLED (live md5 == to-pin). Running only the one-off pass, which places nothing twice:"
  "$PY" -B "$KIT_DIR/repair_f494_s282.py" --db "$FIN/finance.db" --dry-run; exit 0
fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S282_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
DBBAK="$FIN/finance.db.bak_S282"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S282new"; rm -f /tmp/s282_try.db
  if [ -f "$DBBAK" ] && [ "${DB_WRITTEN:-0}" = "1" ]; then echo "!! restoring finance.db from $DBBAK"; \cp -p "$DBBAK" "$FIN/finance.db"; fi
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }
DB_WRITTEN=0

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S282new"
"$PY" -B "$KIT_DIR/patch_line_owner_s282.py" --file "$FIN/purchase_app.py.S282new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S282new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S282new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S282new.bak_S282_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the one-off pass: rehearsed on a COPY, then the live database ----
rm -f /tmp/s282_try.db
\cp -p "$FIN/finance.db" /tmp/s282_try.db || restore
echo "rehearsal on a copy of finance.db:"
"$PY" -B "$KIT_DIR/repair_f494_s282.py" --db /tmp/s282_try.db | tee /tmp/s282_try.txt || restore
grep -q "^placed : " /tmp/s282_try.txt || { echo "!! the rehearsal placed nothing -- the lines are not as F-494 described; nothing written to the live database"; restore; }
if grep -q "^left   : " /tmp/s282_try.txt; then echo "note   : some lines stay unowned (named above); they are not this fault's shape"; fi
rm -f /tmp/s282_try.db /tmp/s282_try.txt
\cp -p "$FIN/finance.db" "$DBBAK" || restore
echo "backup : $DBBAK"
DB_WRITTEN=1
echo "the live database:"
"$PY" -B "$KIT_DIR/repair_f494_s282.py" --db "$FIN/finance.db" || restore

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/purchase/api/healthz || true)
  echo "health : $code"
fi
echo "md5sum of the installed file:"; md5sum "$FIN/purchase_app.py"
echo "S282_LINE_OWNER: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay/2026-09"
