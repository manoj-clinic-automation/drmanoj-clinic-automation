#!/bin/bash
# install_S261_VENDOR_PAY.sh -- the vendor payments page (S261).
#
# ONE anchored insert into purchase_app.py, patched ON THE BOX from its exact
# live bytes. Not one existing line is edited. Before the service is restarted
# the page is RENDERED against a COPY of the real database and read back.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S261_VENDOR_PAY/install_S261_VENDOR_PAY.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="52550e63e7fdffc186de4fcd4f93717b"
PU_TO="a7df849bb3d22b626eed1a958adc8107"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S261_VENDOR_PAY installer =="; echo "target : $FIN/purchase_app.py"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S261_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S261new"; rm -f /tmp/s261_walk.db
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S261new"
"$PY" "$KIT_DIR/patch_vendor_pay_s261.py" --file "$FIN/purchase_app.py.S261new" || restore
NEW="$(md5of "$FIN/purchase_app.py.S261new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S261new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S261new.bak_S261_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the walk: the page is RENDERED against a COPY of the real database -----
if [ -f "$FIN/finance.db" ]; then
  rm -f /tmp/s261_walk.db
  \cp -p "$FIN/finance.db" /tmp/s261_walk.db || restore
  echo "walk   : rendering the page against a copy of the live database"
  "$PY" "$KIT_DIR/walk_live_s261.py" --file "$FIN/purchase_app.py" --db /tmp/s261_walk.db || restore
  rm -f /tmp/s261_walk.db
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
echo "S261_VENDOR_PAY: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay"
