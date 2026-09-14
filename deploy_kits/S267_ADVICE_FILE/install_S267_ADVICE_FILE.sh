#!/bin/bash
# install_S267_ADVICE_FILE.sh -- link Marg's bill name to the account row (S267).
#
# THE LAST PIECE: the advice is also EMAILED to the bank, so it has to exist as a
# workbook -- and as the bank's own workbook, not a lookalike. Same sheet name,
# same merges, same widths, same headers, account numbers as TEXT so a leading
# zero survives, amounts as plain whole numbers, and the total as a real =SUM()
# with its value cached so it shows without recalculating.
#
# WRITTEN WITH THE STANDARD LIBRARY ALONE -- a .xlsx is a zip of XML and this
# builds it directly. Nothing to install on the box, nothing to go missing at
# month end.
#
# ONE anchored edit and one append, patched ON THE BOX from its exact live bytes.
# Before the service is restarted, BOTH files -- the one being replaced and the
# patched one -- are rendered against their own copy of the real database, and
# every page that is not the payment sheet must come back BYTE-IDENTICAL.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S267_ADVICE_FILE/install_S267_ADVICE_FILE.sh
#
# THIS KIT WRITES NO DATA and needs nothing on the command line.
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="30f6c28697eabab5beae609fa7965389"
PU_TO="34628cd8de65a5fbd4440cd7f96b0f70"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S267_ADVICE_FILE installer =="; echo "target : $FIN/purchase_app.py"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S267_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S267new"; rm -f /tmp/s267_walk.db
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S267new"
"$PY" -B "$KIT_DIR/patch_advice_file_s267.py" --file "$FIN/purchase_app.py.S267new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S267new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S267new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S267new.bak_S267_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the walk: BOTH files, each against its own copy of the real database ----
if [ -f "$FIN/finance.db" ]; then
  rm -f /tmp/s267_walk.db
  \cp -p "$FIN/finance.db" /tmp/s267_walk.db || restore
  echo "walk   : the workbook generated, unzipped and read back"
  "$PY" -B "$KIT_DIR/walk_s267.py" --file "$FIN/purchase_app.py" --before "$BAK" --db /tmp/s267_walk.db || restore
  rm -f /tmp/s267_walk.db
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
echo "S267_ADVICE_FILE: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay"
