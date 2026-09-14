#!/bin/bash
# install_S264_PAY_MONTHS.sh -- link Marg's bill name to the account row (S264).
#
# THE COMPLAINT: the tile opened the newest month and the payment sheet had no
# way to reach any other one, so the only route to August was the hub -- whose
# month link goes to the PURCHASE AUDIT page, a different job entirely.
#
# Three anchored edits, patched ON THE BOX from its exact live bytes. Before the
# service is restarted, BOTH files -- the one being replaced and the patched one
# -- are rendered against their own copy of the real database, and every page
# that is not the two being changed must come back BYTE-IDENTICAL to before.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S264_PAY_MONTHS/install_S264_PAY_MONTHS.sh
#
# THIS KIT WRITES NO DATA. It changes three lines of screen code and adds one
# helper; no table, no row, no account, nothing in the database is touched.
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="c4a64353e3b8d6ed0e0d46fe0ec32954"
PU_TO="8d7b1eadc70d122ff181002692815bd7"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S264_PAY_MONTHS installer =="; echo "target : $FIN/purchase_app.py"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S264_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S264new"; rm -f /tmp/s264_walk.db
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S264new"
"$PY" -B "$KIT_DIR/patch_pay_months_s264.py" --file "$FIN/purchase_app.py.S264new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S264new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S264new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S264new.bak_S264_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the walk: BOTH files, each against its own copy of the real database ----
if [ -f "$FIN/finance.db" ]; then
  rm -f /tmp/s264_walk.db
  \cp -p "$FIN/finance.db" /tmp/s264_walk.db || restore
  echo "walk   : the navigation followed, link by link, on a copy of the live database"
  "$PY" -B "$KIT_DIR/walk_s264.py" --file "$FIN/purchase_app.py" --before "$BAK" --db /tmp/s264_walk.db || restore
  rm -f /tmp/s264_walk.db
else
  echo "walk   : COULD NOT RUN -- $FIN/finance.db not found (said out loud, F-443)"
  restore
fi

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  echo "service: clinic-finance active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/purchase/api/healthz || true)
  echo "health : $code"
fi
echo "md5sum of the installed file:"; md5sum "$FIN/purchase_app.py"
echo "S264_PAY_MONTHS: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay"
