#!/bin/bash
# install_S265_BANK_ADVICE.sh -- link Marg's bill name to the account row (S265).
#
# THE ASK: "we should be able to see the exact preview of the Excel sheet here as
# we send it to the bank" -- it is printed on blank A4 and emailed to the bank from
# the account linked to it. So the page now carries the advice itself: same
# letterhead, same seven columns, same order, same wording as every NEFT ADVICE
# sheet from April to July 2026. Printing the page prints the advice and nothing
# else, A4 landscape.
#
# ONE anchored edit and one append, patched ON THE BOX from its exact live bytes.
# Before the service is restarted, BOTH files -- the one being replaced and the
# patched one -- are rendered against their own copy of the real database, and
# every page that is not the payment sheet must come back BYTE-IDENTICAL.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S265_BANK_ADVICE/install_S265_BANK_ADVICE.sh
#
# THE SHOP'S PRINTED MOBILE is a number, so it does not travel in this repository
# (F-185). Hand it in on the line and it is kept in the database:
#   SHOP_MOBILE=<number> bash ...install_S265_BANK_ADVICE.sh
# Leave it off and the letterhead simply does not print a mobile, and the card
# says so rather than printing a wrong one.
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="8d7b1eadc70d122ff181002692815bd7"
PU_TO="f32cdfba36b97d9b402aef122bba1906"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S265_BANK_ADVICE installer =="; echo "target : $FIN/purchase_app.py"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S265_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S265new"; rm -f /tmp/s265_walk.db
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S265new"
"$PY" -B "$KIT_DIR/patch_advice_s265.py" --file "$FIN/purchase_app.py.S265new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S265new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S265new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S265new.bak_S265_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the walk: BOTH files, each against its own copy of the real database ----
if [ -f "$FIN/finance.db" ]; then
  rm -f /tmp/s265_walk.db
  \cp -p "$FIN/finance.db" /tmp/s265_walk.db || restore
  if [ -n "${SHOP_MOBILE:-}" ]; then
    echo "letterhead: setting the printed mobile on the COPY first"
    "$PY" -B "$KIT_DIR/seed_config_s265.py" --db /tmp/s265_walk.db \
        --key shop_mobile --value "$SHOP_MOBILE" || restore
  else
    echo "letterhead: no SHOP_MOBILE given -- the advice will print no mobile (F-443)"
  fi
  echo "walk   : the advice held to the shape of the bank's own sheets"
  "$PY" -B "$KIT_DIR/walk_s265.py" --file "$FIN/purchase_app.py" --before "$BAK" --db /tmp/s265_walk.db || restore
  rm -f /tmp/s265_walk.db
  if [ -n "${SHOP_MOBILE:-}" ]; then
    \cp -p "$FIN/finance.db" "$FIN/finance.db.bak_S265" || restore
    echo "letterhead: writing it to the live database (backup $FIN/finance.db.bak_S265)"
    "$PY" -B "$KIT_DIR/seed_config_s265.py" --db "$FIN/finance.db" \
        --key shop_mobile --value "$SHOP_MOBILE" || restore
  fi
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
echo "S265_BANK_ADVICE: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay"
