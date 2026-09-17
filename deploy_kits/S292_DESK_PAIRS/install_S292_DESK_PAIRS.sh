#!/bin/bash
# install_S292_DESK_PAIRS.sh -- the desk's "over" card stops being a wall of text:
# each item on the card gets its own same-salt partner line, a toggle shows all
# pairs one per line, and a real-loss card names its partner. Over S288 (16b9a234).
#
# Four anchored edits + two helpers in /root/finance/stock_desk.html, patched ON
# THE BOX from its exact live bytes. No server code, no table, no setting, NO
# RESTART -- the page is read from disk on every request.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S292_DESK_PAIRS/install_S292_DESK_PAIRS.sh
#
# Env (test only): ROOT=/some/dir
set -e; set -u
ROOT="${ROOT:-/root}"; KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; FIN="$ROOT/finance"
DK_FROM="16b9a234b71150b19c8d2ef883eb5f08"
DK_TO="6b6636bfbcec022169532042ba6b7d53"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
md5of() { md5sum "$1" | awk '{print $1}'; }
echo "== S292_DESK_PAIRS installer =="; echo "target : $FIN/stock_desk.html"; echo "python : $PY"
[ -f "$FIN/stock_desk.html" ] || { echo "REFUSED: $FIN/stock_desk.html not found"; exit 1; }
DK="$(md5of "$FIN/stock_desk.html")"
echo "stock_desk.html : from $DK_FROM -> to $DK_TO ; live $DK"
if [ "$DK" = "$DK_TO" ]; then echo "ALREADY INSTALLED (live md5 == to-pin)."; exit 0; fi
[ "$DK" = "$DK_FROM" ] || { echo "REFUSED: stock_desk.html is $DK, expected $DK_FROM"; exit 1; }

BAK="$FIN/stock_desk.html.bak_S292_${DK_FROM:0:8}"
\cp -p "$FIN/stock_desk.html" "$BAK"; echo "backup : $BAK"
restore() { echo "!! restoring stock_desk.html byte-identically"; \cp -p "$BAK" "$FIN/stock_desk.html"
  rm -f "$FIN/stock_desk.html.S292new"; md5sum "$FIN/stock_desk.html"; exit 1; }

\cp -p "$FIN/stock_desk.html" "$FIN/stock_desk.html.S292new"
"$PY" -B "$KIT_DIR/patch_desk_pairs_s292.py" --file "$FIN/stock_desk.html.S292new" --from "$DK_FROM" || restore
NEW="$(md5of "$FIN/stock_desk.html.S292new")"
[ "$NEW" = "$DK_TO" ] || { echo "!! patched file is $NEW, predicted $DK_TO"; restore; }
mv "$FIN/stock_desk.html.S292new" "$FIN/stock_desk.html" || restore
rm -f "$FIN/stock_desk.html.S292new.bak_S292_${DK_FROM:0:8}" 2>/dev/null || true
grep -q 'function pairBlock(' "$FIN/stock_desk.html" || restore; echo "smoke  : the new words are in the page"
code=$(curl -s -o /dev/null -w '%{http_code}' -m 10 http://127.0.0.1:8106/finance/stock/page/desk || true)
echo "page   : HTTP $code (302/401 = the login gate, as before; 200 = served)"
echo "md5sum of the installed file:"; md5sum "$FIN/stock_desk.html"
echo "S292_DESK_PAIRS: DONE -- no restart needed; reload the desk page."
echo "read next: https://followup.dr-manoj.in/finance/stock/page/desk?count=1"
