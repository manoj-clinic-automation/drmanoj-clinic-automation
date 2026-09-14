#!/bin/bash
# install_S262_PAY_TILE.sh -- the Vendor payments tile (S262).
#
# TWO files move together, and they must: a grant matches a tile BY NAME, so a
# new grants file beside an unpatched portal.py grants nothing, and a patched
# portal.py beside the old grants file shows the tile to the doctor alone.
#   /root/portal/portal.py          d0f126a3... -> dc8f363e...   (one tile inserted)
#   /root/portal/tile_grants.json   d7edf850... -> 2eb2f271...   (v16 -> v17)
#
# Nothing else is touched. Before the service is restarted, the patched file is
# read back and compared to the file it was patched FROM, tile by tile.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S262_PAY_TILE/install_S262_PAY_TILE.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; P="$ROOT/portal"
PO_FROM="d0f126a3815a4c7e24960a15f1951857"
PO_TO="dc8f363e389259130764219e01a6b42d"
TG_FROM="d7edf850a977c033448d6e14076490b4"
TG_TO="2eb2f2714091d97ae8f53a80902c913f"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S262_PAY_TILE installer =="; echo "target : $P/portal.py + $P/tile_grants.json"; echo "python : $PY"
[ -f "$P/portal.py" ]        || { echo "REFUSED: $P/portal.py not found"; exit 1; }
[ -f "$P/tile_grants.json" ] || { echo "REFUSED: $P/tile_grants.json not found"; exit 1; }
PO="$(md5of "$P/portal.py")"; TG="$(md5of "$P/tile_grants.json")"
echo "portal.py        : from $PO_FROM -> to $PO_TO ; live $PO"
echo "tile_grants.json : from $TG_FROM -> to $TG_TO ; live $TG"
if [ "$PO" = "$PO_TO" ] && [ "$TG" = "$TG_TO" ]; then echo "ALREADY INSTALLED (both live md5 == to-pin)."; exit 0; fi
[ "$PO" = "$PO_FROM" ] || { echo "REFUSED: portal.py is $PO, expected $PO_FROM"; exit 1; }
[ "$TG" = "$TG_FROM" ] || { echo "REFUSED: tile_grants.json is $TG, expected $TG_FROM"; exit 1; }

BP="$P/portal.py.bak_S262_${PO_FROM:0:8}"; BG="$P/tile_grants.json.bak_S262_${TG_FROM:0:8}"
\cp -p "$P/portal.py" "$BP"; \cp -p "$P/tile_grants.json" "$BG"
echo "backup : $BP"; echo "backup : $BG"
restore() { echo "!! restoring both files byte-identically"
  \cp -p "$BP" "$P/portal.py"; \cp -p "$BG" "$P/tile_grants.json"
  rm -f "$P/portal.py.S262new"
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-portal || true; fi
  md5sum "$P/portal.py" "$P/tile_grants.json"; exit 1; }

\cp -p "$P/portal.py" "$P/portal.py.S262new"
"$PY" -B "$KIT_DIR/patch_portal_pay_tile_s262.py" --file "$P/portal.py.S262new" --from "$PO_FROM" || restore
NEW="$(md5of "$P/portal.py.S262new")"
[ "$NEW" = "$PO_TO" ] || { echo "!! patched portal.py is $NEW, predicted $PO_TO"; restore; }
mv "$P/portal.py.S262new" "$P/portal.py" || restore
rm -f "$P/portal.py.S262new.bak_S262_${PO_FROM:0:8}" 2>/dev/null || true
\cp "$KIT_DIR/tile_grants.json" "$P/tile_grants.json" || restore
NEWG="$(md5of "$P/tile_grants.json")"
[ "$NEWG" = "$TG_TO" ] || { echo "!! tile_grants.json is $NEWG, predicted $TG_TO"; restore; }
"$PY" -m py_compile "$P/portal.py" || restore; echo "smoke  : py_compile OK"

echo "walk   : the patched file read back against the file it was patched from"
"$PY" -B "$KIT_DIR/walk_s262.py" --file "$P/portal.py" --before "$BP" \
      --grants "$P/tile_grants.json" --grants-before "$BG" || restore

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-portal || restore; sleep 3
  systemctl is-active --quiet clinic-portal || restore
  echo "service: clinic-portal active after restart"
  code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8090/ || true)
  echo "portal : $code"
  case "$code" in 5*|000) echo "!! the portal did not answer"; restore;; esac
  pay=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/purchase/page/pay || true)
  echo "the tile's address answers: $pay  (a login redirect is the right answer here)"
  case "$pay" in 404|5*|000) echo "!! the tile would open nothing"; restore;; esac
fi
echo "md5sum of the installed files:"; md5sum "$P/portal.py" "$P/tile_grants.json"
echo "S262_PAY_TILE: DONE"
echo "read next: https://followup.dr-manoj.in/portal/  -- Money & Accounts -> Vendor payments"
