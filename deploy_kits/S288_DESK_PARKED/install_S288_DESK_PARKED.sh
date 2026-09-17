#!/bin/bash
# install_S288_DESK_PARKED.sh -- the decision desk gets the word it was missing:
# "Kept elsewhere -- with me, not lost" (PARKED) on every real-loss card and every
# lane row, and the find box shows a word already given with "Change this word".
#
# Three anchored edits in /root/finance/stock_desk.html, patched ON THE BOX from
# its exact live bytes. No server code, no table, no setting, NO RESTART -- the
# page is read from disk on every request.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S288_DESK_PARKED/install_S288_DESK_PARKED.sh
#
# Env (test only): ROOT=/some/dir
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
DK_FROM="54aeda96ba022b30b21bdb9f77616a18"
DK_TO="16b9a234b71150b19c8d2ef883eb5f08"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S288_DESK_PARKED installer =="; echo "target : $FIN/stock_desk.html"; echo "python : $PY"
[ -f "$FIN/stock_desk.html" ] || { echo "REFUSED: $FIN/stock_desk.html not found"; exit 1; }
DK="$(md5of "$FIN/stock_desk.html")"
echo "stock_desk.html : from $DK_FROM -> to $DK_TO ; live $DK"
if [ "$DK" = "$DK_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$DK" = "$DK_FROM" ] || { echo "REFUSED: stock_desk.html is $DK, expected $DK_FROM"; exit 1; }

BAK="$FIN/stock_desk.html.bak_S288_${DK_FROM:0:8}"
\cp -p "$FIN/stock_desk.html" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring stock_desk.html byte-identically"; \cp -p "$BAK" "$FIN/stock_desk.html"
  rm -f "$FIN/stock_desk.html.S288new"; md5sum "$FIN/stock_desk.html"; exit 1; }

\cp -p "$FIN/stock_desk.html" "$FIN/stock_desk.html.S288new"
"$PY" -B "$KIT_DIR/patch_desk_parked_s288.py" --file "$FIN/stock_desk.html.S288new" --from "$DK_FROM" || restore
NEW="$(md5of "$FIN/stock_desk.html.S288new")"
[ "$NEW" = "$DK_TO" ] || { echo "!! patched file is $NEW, predicted $DK_TO"; restore; }
mv "$FIN/stock_desk.html.S288new" "$FIN/stock_desk.html" || restore
rm -f "$FIN/stock_desk.html.S288new.bak_S288_${DK_FROM:0:8}" 2>/dev/null || true
grep -q 'data-reopen' "$FIN/stock_desk.html" || restore; echo "smoke  : the new words are in the page"
code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/stock/page/desk || true)
echo "page   : HTTP $code (302/401 = the login gate, as before; 200 = served)"
echo "md5sum of the installed file:"; md5sum "$FIN/stock_desk.html"
echo "S288_DESK_PARKED: DONE -- no restart needed; reload the desk page."
echo "read next: https://followup.dr-manoj.in/finance/stock/page/desk?count=1"
