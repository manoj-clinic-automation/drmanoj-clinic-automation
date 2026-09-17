#!/bin/bash
# install_S284_SHAVEZ_MAKER.sh -- D524: Shavez may write the cheque register.
#
# The owner's word (board line F5, 15-Sep): "make him maker". The scope recorded
# in the Register: maker ON THE CHEQUE REGISTER. So this is not a unit_role row
# (which would also let him file the day, give bill verdicts, type carry-forwards
# and read the phone book). It is the house pattern used for the phone book and
# the salt list: a named list in the `setting` table, purchase.cheque_users,
# read fail-closed. Four anchored edits and one helper in purchase_app.py, then
# one setting row: shavez.
#
# INSTALLS ON TOP OF S282_LINE_OWNER. It refuses on any other pin.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S284_SHAVEZ_MAKER/install_S284_SHAVEZ_MAKER.sh
#
# The undo that leaves the code in place and takes the grant away (one line):
#   /root/wa/venv/bin/python3 -B /root/deploy/repo/deploy_kits/S284_SHAVEZ_MAKER/seed_setting_s284.py --db /root/finance/finance.db --value ""
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="216a0cd95afad73eecbc484683892ca3"
PU_TO="d1476f80836e8b68fae2da1855c7105f"
WRITERS="${WRITERS:-shavez}"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S284_SHAVEZ_MAKER installer =="; echo "target : $FIN/purchase_app.py + setting purchase.cheque_users"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
[ -f "$FIN/finance.db" ] || { echo "REFUSED: $FIN/finance.db not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then
  echo "ALREADY INSTALLED (live md5 == to-pin). Making sure the list is set:"
  "$PY" -B "$KIT_DIR/seed_setting_s284.py" --db "$FIN/finance.db" --value "$WRITERS"; exit 0
fi
if [ "$PU" = "3535dc978d4ec53846368c8772347a50" ]; then
  echo "REFUSED: this is the pre-S282 file. Install S282_LINE_OWNER first, then run this again."; exit 1
fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S284_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S284new"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S284new"
"$PY" -B "$KIT_DIR/patch_cheque_writer_s284.py" --file "$FIN/purchase_app.py.S284new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S284new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S284new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S284new.bak_S284_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

echo "setting: the cheque-writer list"
"$PY" -B "$KIT_DIR/seed_setting_s284.py" --db "$FIN/finance.db" --value "$WRITERS" || restore

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/purchase/api/healthz || true)
  echo "health : $code"
fi
echo "md5sum of the installed file:"; md5sum "$FIN/purchase_app.py"
echo "S284_SHAVEZ_MAKER: DONE -- shavez may now log, hand over and void cheques; nothing else changed for him"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/cheques"
