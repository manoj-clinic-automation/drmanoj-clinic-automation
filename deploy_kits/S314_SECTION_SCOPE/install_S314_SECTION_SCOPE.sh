#!/bin/bash
# install_S314_SECTION_SCOPE.sh -- a stock count can now cover ONE SECTION (rungs 2 and 3 of
# S268_COUNT2_BY_SECTION_PLAN). Count only the orthotics on the ordinary pad, upload it, and the
# round is answerable for the orthotics and nothing else -- where until now it reported the other
# 300-odd shelves as "not counted" and could never be closed.
#
#   /root/finance/stock_app.py   10be8a9e -> 1b473fbf
#
# REQUIRES S313_SECTION_MAP LIVE -- its FROM pin is S313's TO pin. Run S313's line first if not.
#
# WHAT CHANGES
#   * stock_count.section, added HERE and not in stock_schema.sql (which is CREATE TABLE IF NOT
#     EXISTS and would change nothing on a live database). Every existing round stays NULL, which
#     means what it has always meant: the whole shop.
#   * _pad_family() -- the ONE function that decided "the count is the whole shop", and which feeds
#     the upload's reply, the result workbook, the recent-counts list, the desk, Amir's board, the
#     report, the hub and the loss board -- now measures what is owed against the ROUND'S SCOPE.
#   * the scope is DECLARED (the column) or, when it is not, OBSERVED: every item counted across the
#     family sits in one section of the map. One item outside it, or one the map does not know, and
#     the round is a whole-shop round again. The pad reader has always been right that a blank means
#     NOT COUNTED, so counting only the orthotic rows of the ordinary pad already records exactly
#     those rows -- the round says what it covers in the only way that cannot be wrong.
#   * an OBSERVED scope can be closed COMPLETE only by the owner, so a whole-shop count whose first
#     sheet happened to hold one section cannot be signed off by staff with the rest never counted.
#   * _newest_root() -- the pages prefer a WHOLE-SHOP round, so the 06-Sep count keeps the hub, the
#     desk, Amir's board, the report and the loss board. A sectioned round is opened by ?count=N.
#   * NEW door POST /finance/stock/api/pad/section/<count> {"section": "Orthotics"} -- the owner
#     declares a round's scope, or clears it. Nothing else writes the column.
#
# NO table is created, NO screen changes, NO existing figure moves: the walk holds the 06-Sep round
# against the live module and every figure, and the whole hub payload, must be identical.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S314_SECTION_SCOPE/install_S314_SECTION_SCOPE.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S314_SECTION_SCOPE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s314_walk_$STAMP"
SA="$FIN/stock_app.py"; SA_FROM="10be8a9ec5c59b2cde15e6c4b1934a32"; SA_TO="1b473fbf586dea13edd40a6a993cb2ba"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
BAK=""
restore() {
  echo "!! restoring -- nothing of S314 stays"
  [ -n "$BAK" ] && [ -f "$BAK" ] && \cp -p "$BAK" "$SA"
  rm -f "$SA.S314new" "$FIN"/*.bak_S314_* 2>/dev/null
  [ "${NORESTART:-0}" != "1" ] && systemctl restart clinic-finance >/dev/null 2>&1
  echo "   stock_app.py $(m5 "$SA")"
  exit 1
}

echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
echo "[1/7] kit sums green"

cur="$(m5 "$SA")"
echo "stock_app.py : $SA_FROM -> $SA_TO ; live $cur"
[ "$cur" = "$SA_TO" ] && { echo "ALREADY INSTALLED (live md5 == the to-pin)."; exit 0; }
if [ "$cur" != "$SA_FROM" ]; then
  echo "!! [2/7] stock_app.py is $cur, expected $SA_FROM - nothing installed"
  echo "   $SA_FROM is S313_SECTION_MAP's to-pin. If S313 is not live yet, run its line first."
  exit 1
fi
[ -f "$FIN/section_map.py" ] || { echo "!! [2/7] section_map.py is not on the box - S313 must be live first"; exit 1; }
echo "[2/7] the live pin is exact (S313 is live)"

fail3() { rm -f "$SA.S314new"*; rm -rf "$WALK"; echo "!! [3/7] $1 - nothing placed"; exit 1; }
rm -f "$SA.S314new"; \cp -p "$SA" "$SA.S314new"
"$PY" -B patch_scope_s314.py --file "$SA.S314new" --from "$SA_FROM" --expect "$SA_TO" || fail3 "the patch refused"
rm -f "$SA.S314new.bak_S314_"*
[ "$(m5 "$SA.S314new")" = "$SA_TO" ] || fail3 "patched to an unpredicted md5"
"$PY" -c "import sys, os, tempfile, py_compile; py_compile.compile(sys.argv[1], cfile=os.path.join(tempfile.mkdtemp(), 'x.pyc'), doraise=True)" "$SA.S314new" \
  || fail3 "stock_app.py does not compile"
echo "[3/7] patched on the box to the predicted md5; compiles"

mkdir -p "$WALK/live" "$WALK/new" || fail3 "scratch failed"
for f in stock_app.py stock_hub.html stock_sections.html section_map.py claim_queue.py darpan_card.html \
         pad_receipt.py padwriter.py padreader.py stock_schema.sql stock_check_live.html stock_diffs.html; do
  [ -f "$FIN/$f" ] && \cp -p "$FIN/$f" "$WALK/live/$f"
done
\cp -p "$WALK/live/"* "$WALK/new/" 2>/dev/null
\cp -p "$SA.S314new" "$WALK/new/stock_app.py"
"$PY" -B "$KDIR/selftest_s314.py" "$WALK/new" | tail -1 | grep -q ', 0 failed' || fail3 "the scope selftest is red"
echo "[4/7] selftest green"

if [ "${NOWALK:-0}" != "1" ]; then
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { rm -rf "$WALK"; rm -f "$SA.S314new"; echo "!! [5/7] scratch copy of the database failed - nothing placed"; exit 1; }
  WOUT="$( cd "$FIN" && timeout 170 "$PY" -B "$KDIR/walk_s314.py" "$WALK/live" "$WALK/new" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q '^WALK OK' || { rm -rf "$WALK"; rm -f "$SA.S314new"; echo "!! [5/7] the walk is red - nothing placed"; exit 1; }
  echo "[5/7] walked green on a scratch copy of the live database"
else echo "[5/7] walk skipped (NOWALK=1, test only)"; fi

BAK="$SA.bak_S314_${SA_FROM:0:8}"; \cp -p "$SA" "$BAK"
mv -f "$SA.S314new" "$SA"
[ "$(m5 "$SA")" = "$SA_TO" ] || restore
echo "[6/7] placed; md5 read back == the to-pin (backup .bak_S314_${SA_FROM:0:8})"

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance >/dev/null 2>&1; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  # F-525: the gate hits a PUBLIC_PATHS route; login-gated pages are probed for information only.
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
  c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/hub)
  c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/desk)
  c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/report)
  echo "health : finance $c1 · hub $c2 · desk $c3 · report $c4 (302/401 = the login gate, expected)"
  [ "$c1" = 200 ] || restore
  for c in "$c2" "$c3" "$c4"; do case "$c" in 200|302|401) : ;; *) restore ;; esac; done
  echo "[7/7] clinic-finance active and answering"
else echo "[7/7] restart skipped (NORESTART=1, test only)"; fi

rm -rf "$WALK"
echo "$KIT: DONE -- stock_app.py $(m5 "$SA")"
echo "   an orthotics-only count: download the ordinary pad, fill ONLY the orthotic rows, upload it."
