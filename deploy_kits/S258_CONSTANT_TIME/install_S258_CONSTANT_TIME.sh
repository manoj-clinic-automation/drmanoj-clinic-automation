#!/bin/bash
# install_S258_CONSTANT_TIME.sh -- every machine-door token check becomes constant-time (F-470).
# finance_app.py is patched ON THE BOX from its exact live bytes (the kit never carries that file);
# stock_app.py and purchase_app.py are full-file replacements. All three pinned from -> to.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S258_CONSTANT_TIME/install_S258_CONSTANT_TIME.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   FORCE_FAIL=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
FA_FROM="1fc62335f085b4cb4a634bbe9cca96c4"; FA_TO="a4201e9fc52c25528ba3b92db403101f"
ST_FROM="aa6d9cd9afbe5c7a2e44315678f58de3"; ST_TO="8615d64dbeda516e6efb6f025ec777b3"
PU_FROM="ad1fc00466458897751df7c9e9fcb99d"; PU_TO="52550e63e7fdffc186de4fcd4f93717b"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S258_CONSTANT_TIME installer =="; echo "target : $FIN"; echo "python : $PY"
for n in finance_app.py stock_app.py purchase_app.py; do [ -f "$FIN/$n" ] || { echo "REFUSED: $FIN/$n not found"; exit 1; }; done
FA="$(md5of $FIN/finance_app.py)"; ST="$(md5of $FIN/stock_app.py)"; PU="$(md5of $FIN/purchase_app.py)"
echo "finance_app.py  : from $FA_FROM -> to $FA_TO ; live $FA"
echo "stock_app.py    : from $ST_FROM -> to $ST_TO ; live $ST"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$FA" = "$FA_TO" ] && [ "$ST" = "$ST_TO" ] && [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (all three live md5 == to-pin)."; exit 0; fi
[ "$FA" = "$FA_FROM" ] || { echo "REFUSED: finance_app.py is $FA, expected $FA_FROM"; exit 1; }
[ "$ST" = "$ST_FROM" ] || { echo "REFUSED: stock_app.py is $ST, expected $ST_FROM"; exit 1; }
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }
FA_BAK="$FIN/finance_app.py.bak_S258_${FA_FROM:0:8}"; ST_BAK="$FIN/stock_app.py.bak_S258_${ST_FROM:0:8}"; PU_BAK="$FIN/purchase_app.py.bak_S258_${PU_FROM:0:8}"
\cp -p "$FIN/finance_app.py" "$FA_BAK"; \cp -p "$FIN/stock_app.py" "$ST_BAK"; \cp -p "$FIN/purchase_app.py" "$PU_BAK"
echo "backup : $FA_BAK"; echo "backup : $ST_BAK"; echo "backup : $PU_BAK"
restore() { echo "!! restoring all three byte-identically"; \cp -p "$FA_BAK" "$FIN/finance_app.py"; \cp -p "$ST_BAK" "$FIN/stock_app.py"; \cp -p "$PU_BAK" "$FIN/purchase_app.py"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi; md5sum "$FIN/finance_app.py" "$FIN/stock_app.py" "$FIN/purchase_app.py"; exit 1; }
"$PY" "$KIT_DIR/patch_compare_s258.py" fa "$FIN/finance_app.py" "$FIN/finance_app.py.S258new" || restore
[ "$(md5of "$FIN/finance_app.py.S258new")" = "$FA_TO" ] || { echo "!! patched finance_app.py is $(md5of "$FIN/finance_app.py.S258new"), predicted $FA_TO"; rm -f "$FIN/finance_app.py.S258new"; restore; }
mv "$FIN/finance_app.py.S258new" "$FIN/finance_app.py" || restore
\cp -p "$KIT_DIR/stock_app.py" "$FIN/stock_app.py" || restore
\cp -p "$KIT_DIR/purchase_app.py" "$FIN/purchase_app.py" || restore
"$PY" -m py_compile "$FIN/finance_app.py" "$FIN/stock_app.py" "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"
[ "${FORCE_FAIL:-0}" = "1" ] && { echo "smoke  : FORCED FAILURE"; restore; }
for n in finance_app.py stock_app.py purchase_app.py; do
  c=$(grep -cE '(==|!=) *(CRON_TOKEN|MARG_TOKEN|RENEWALS_TOKEN|_marg_token|tok)\b' "$FIN/$n" || true)
  [ "$c" = "0" ] || { echo "smoke  : $n still has $c plain compare(s)"; restore; }
done
echo "smoke  : SMOKE_OK no plain token compare left in any of the three"
if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || restore; sleep 3; systemctl is-active --quiet clinic-finance || restore; echo "service: clinic-finance active after restart"; fi
echo "md5sum of installed files:"; md5sum "$FIN/finance_app.py" "$FIN/stock_app.py" "$FIN/purchase_app.py"
echo "S258_CONSTANT_TIME: DONE"
echo "proof  : within 10 minutes the pipeline page should show a fresh manojz heartbeat and medical push -- both doors now answer through the new compare."
