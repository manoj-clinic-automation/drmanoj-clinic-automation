#!/bin/bash
# install_S266_COVERING_LETTER.sh -- link Marg's bill name to the account row (S266).
#
# THE ASK: "covering letter is not there." The advice never goes to the bank on
# its own -- it goes with a signed letter authorising the debit. This is that
# letter, word for word, with the date, the cheque number and the amount filled
# in from the sheet instead of typed. It has its own page, prints A4 PORTRAIT,
# and the payment sheet still prints the advice LANDSCAPE.
#
# ONE anchored edit and one append, patched ON THE BOX from its exact live bytes.
# Before the service is restarted, BOTH files -- the one being replaced and the
# patched one -- are rendered against their own copy of the real database, and
# every page that is not the payment sheet must come back BYTE-IDENTICAL.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S266_COVERING_LETTER/install_S266_COVERING_LETTER.sh
#
# THE FIRM'S OWN DEBIT ACCOUNT is a number, so it does not travel in this
# repository (F-185). Hand it in on the line and it is kept in the database:
#   DEBIT_ACCOUNT=<the account the bank debits> bash ...install_S266_COVERING_LETTER.sh
# Leave it off and the letter prints a blank there to fill by hand, and the card
# says so rather than printing a wrong one.
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="f32cdfba36b97d9b402aef122bba1906"
PU_TO="30f6c28697eabab5beae609fa7965389"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S266_COVERING_LETTER installer =="; echo "target : $FIN/purchase_app.py"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S266_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S266new"; rm -f /tmp/s266_walk.db
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S266new"
"$PY" -B "$KIT_DIR/patch_letter_s266.py" --file "$FIN/purchase_app.py.S266new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S266new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S266new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S266new.bak_S266_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the walk: BOTH files, each against its own copy of the real database ----
if [ -f "$FIN/finance.db" ]; then
  rm -f /tmp/s266_walk.db
  \cp -p "$FIN/finance.db" /tmp/s266_walk.db || restore
  if [ -n "${DEBIT_ACCOUNT:-}" ]; then
    echo "letter : setting the debit account on the COPY first"
    "$PY" -B "$KIT_DIR/seed_config_s266.py" --db /tmp/s266_walk.db \
        --key debit_account --value "$DEBIT_ACCOUNT" || restore
  else
    echo "letter : no DEBIT_ACCOUNT given -- the letter will print a blank there (F-443)"
  fi
  echo "walk   : the letter held word for word to the one that has always gone"
  "$PY" -B "$KIT_DIR/walk_s266.py" --file "$FIN/purchase_app.py" --before "$BAK" --db /tmp/s266_walk.db || restore
  rm -f /tmp/s266_walk.db
  if [ -n "${DEBIT_ACCOUNT:-}" ]; then
    \cp -p "$FIN/finance.db" "$FIN/finance.db.bak_S266" || restore
    echo "letter : writing the debit account to the live database (backup $FIN/finance.db.bak_S266)"
    "$PY" -B "$KIT_DIR/seed_config_s266.py" --db "$FIN/finance.db" \
        --key debit_account --value "$DEBIT_ACCOUNT" || restore
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
echo "S266_COVERING_LETTER: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay"
