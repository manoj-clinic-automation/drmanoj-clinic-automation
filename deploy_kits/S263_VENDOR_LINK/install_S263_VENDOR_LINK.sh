#!/bin/bash
# install_S263_VENDOR_LINK.sh -- link Marg's bill name to the account row (S263).
#
# ONE anchored append to purchase_app.py, patched ON THE BOX from its exact live
# bytes. Not one existing line is edited: _vendor_bank is wrapped, never changed.
# Before the service is restarted, BOTH files -- the one being replaced and the
# patched one -- are run against their own copy of the real database, and the
# only difference allowed is the lane of the 15 vendors the owner confirmed.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S263_VENDOR_LINK/install_S263_VENDOR_LINK.sh
#
# A NEW VENDOR'S ACCOUNT never travels in this repository. Hand it in on the line:
#   NEW_VENDOR="DAANSHI PHARMA" NEW_ACCT=<no> NEW_IFSC=<code> bash ...install_S263_VENDOR_LINK.sh
# Leave them off and the install still runs -- the vendor simply stays on the
# cheque lane, and the walk says so out loud.
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
PU_FROM="a7df849bb3d22b626eed1a958adc8107"
PU_TO="c4a64353e3b8d6ed0e0d46fe0ec32954"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S263_VENDOR_LINK installer =="; echo "target : $FIN/purchase_app.py"; echo "python : $PY"
[ -f "$FIN/purchase_app.py" ] || { echo "REFUSED: $FIN/purchase_app.py not found"; exit 1; }
PU="$(md5of "$FIN/purchase_app.py")"
echo "purchase_app.py : from $PU_FROM -> to $PU_TO ; live $PU"
if [ "$PU" = "$PU_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$PU" = "$PU_FROM" ] || { echo "REFUSED: purchase_app.py is $PU, expected $PU_FROM"; exit 1; }

BAK="$FIN/purchase_app.py.bak_S263_${PU_FROM:0:8}"
\cp -p "$FIN/purchase_app.py" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring purchase_app.py byte-identically"; \cp -p "$BAK" "$FIN/purchase_app.py"
  rm -f "$FIN/purchase_app.py.S263new"; rm -f /tmp/s263_walk.db
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; fi
  md5sum "$FIN/purchase_app.py"; exit 1; }

\cp -p "$FIN/purchase_app.py" "$FIN/purchase_app.py.S263new"
"$PY" -B "$KIT_DIR/patch_vendor_alias_s263.py" --file "$FIN/purchase_app.py.S263new" --from "$PU_FROM" || restore
NEW="$(md5of "$FIN/purchase_app.py.S263new")"
[ "$NEW" = "$PU_TO" ] || { echo "!! patched file is $NEW, predicted $PU_TO"; restore; }
mv "$FIN/purchase_app.py.S263new" "$FIN/purchase_app.py" || restore
rm -f "$FIN/purchase_app.py.S263new.bak_S263_${PU_FROM:0:8}" 2>/dev/null || true
"$PY" -m py_compile "$FIN/purchase_app.py" || restore; echo "smoke  : py_compile OK"

# ---- the walk: BOTH files, each against its own copy of the real database ----
if [ -f "$FIN/finance.db" ]; then
  rm -f /tmp/s263_walk.db
  \cp -p "$FIN/finance.db" /tmp/s263_walk.db || restore
  NEW_VENDOR="${NEW_VENDOR:-}"; NEW_ACCT="${NEW_ACCT:-}"; NEW_IFSC="${NEW_IFSC:-}"
  if [ -n "$NEW_VENDOR" ] && [ -n "$NEW_ACCT" ] && [ -n "$NEW_IFSC" ]; then
    echo "account: seeding $NEW_VENDOR on the COPY first, to prove it before the live row"
    "$PY" -B "$KIT_DIR/seed_account_s263.py" --db /tmp/s263_walk.db \
        --vendor "$NEW_VENDOR" --acct "$NEW_ACCT" --ifsc "$NEW_IFSC" \
        --by "owner (S263 install)" || restore
  else
    echo "account: no NEW_VENDOR/NEW_ACCT/NEW_IFSC given -- no account seeded (F-443)"
  fi
  echo "walk   : before and after, each on a copy of the live database"
  "$PY" -B "$KIT_DIR/walk_s263.py" --file "$FIN/purchase_app.py" --before "$BAK" --db /tmp/s263_walk.db || restore
  rm -f /tmp/s263_walk.db
  if [ -n "$NEW_VENDOR" ] && [ -n "$NEW_ACCT" ] && [ -n "$NEW_IFSC" ]; then
    \cp -p "$FIN/finance.db" "$FIN/finance.db.bak_S263" || restore
    echo "account: writing it to the live database (backup $FIN/finance.db.bak_S263)"
    "$PY" -B "$KIT_DIR/seed_account_s263.py" --db "$FIN/finance.db" \
        --vendor "$NEW_VENDOR" --acct "$NEW_ACCT" --ifsc "$NEW_IFSC" \
        --by "owner (S263 install)" || restore
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
echo "S263_VENDOR_LINK: DONE"
echo "read next: https://followup.dr-manoj.in/finance/purchase/page/pay"
