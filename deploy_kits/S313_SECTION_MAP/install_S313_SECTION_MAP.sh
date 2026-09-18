#!/bin/bash
# install_S313_SECTION_MAP.sh -- one stored answer to "which section is this item in" (F-528).
#
# Four rules in this estate answer that question today and none of them is stored: _is_ortho (37 words,
# the pricing margin), _is_consumable (31 words + a setting), _is_orthotic (34 words), and the
# orthotics.vocab SETTING the counter's screen reads. They disagree about 17 items on the live data.
# That is harmless while every count is a whole-shop count -- and it stops being harmless the moment a
# round is scoped, because a monthly orthotics count is a promise about WHICH LINES were counted.
#
#   /root/finance/section_map.py      NEW      -> b05b0f08   (the table, the seed, the dispute view)
#   /root/finance/stock_sections.html NEW      -> 17e006cc   (the owner's review page)
#   /root/finance/stock_app.py        f313f3d3 -> 10be8a9e   (one page + two doors, nothing else)
#
# REQUIRES S312_CLAIM_QUEUE TO BE LIVE -- its FROM pin is S312's TO. If S312 has not been installed the
# installer refuses at [2/7] and places nothing; run S312's line first.
#
# READ-ONLY TO THE ESTATE. New table stock_item_section; NOTHING else reads it. The walk proves the stock
# hub is byte-identical before and after -- this kit is meant to be invisible and the claim is tested.
# The page is not linked from any tile on purpose: it is the foundation rung of the count-#2-by-section
# plan and it is deliberately quiet until the rung above it exists.
#
#   https://followup.dr-manoj.in/finance/stock/page/sections
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S313_SECTION_MAP/install_S313_SECTION_MAP.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S313_SECTION_MAP"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
PY="$ROOT/wa/venv/bin/python3"; [ -x "$PY" ] || PY="/usr/bin/python3"; [ -x "$PY" ] || PY="$(command -v python3)"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s313_walk_$STAMP"

SM="$FIN/section_map.py";        SM_TO="b05b0f08ad65519675e21c9a6f4e90a0"
PG="$FIN/stock_sections.html";   PG_TO="17e006cc8f66ad99745df7a37b8824bc"
SA="$FIN/stock_app.py";          SA_FROM="f313f3d337818cf07612507c58bf60f4"; SA_TO="10be8a9ec5c59b2cde15e6c4b1934a32"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
BAK_SA=""; SM_PLACED=0; PG_PLACED=0
restore() {
  echo "!! restoring -- nothing of S313 stays"
  [ -n "$BAK_SA" ] && [ -f "$BAK_SA" ] && \cp -p "$BAK_SA" "$SA"
  [ "$SM_PLACED" = "1" ] && rm -f "$SM"
  [ "$PG_PLACED" = "1" ] && rm -f "$PG"
  rm -f "$SA.S313new" "$FIN"/*.bak_S313_* 2>/dev/null
  [ "${NORESTART:-0}" != "1" ] && systemctl restart clinic-finance >/dev/null 2>&1
  echo "   stock_app.py $(m5 "$SA")"
  exit 1
}

echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
echo "[1/7] kit sums green"

c_sa="$(m5 "$SA")"; c_sm="$(m5 "$SM")"; c_pg="$(m5 "$PG")"
echo "stock_app.py        : $SA_FROM -> $SA_TO ; live $c_sa"
echo "section_map.py      : NEW -> $SM_TO ; live ${c_sm:-absent}"
echo "stock_sections.html : NEW -> $PG_TO ; live ${c_pg:-absent}"
if [ "$c_sa" = "$SA_TO" ] && [ "$c_sm" = "$SM_TO" ] && [ "$c_pg" = "$PG_TO" ]; then
  echo "ALREADY INSTALLED (every live md5 == its to-pin)."; exit 0
fi
if [ "$c_sa" != "$SA_FROM" ]; then
  echo "!! [2/7] stock_app.py is $c_sa, expected $SA_FROM - nothing installed"
  echo "   $SA_FROM is S312_CLAIM_QUEUE's to-pin. If S312 is not live yet, run its line first."
  exit 1
fi
for pair in "$c_sm:$SM_TO:section_map.py" "$c_pg:$PG_TO:stock_sections.html"; do
  cur="${pair%%:*}"; rest="${pair#*:}"; want="${rest%%:*}"; name="${rest#*:}"
  if [ -n "$cur" ] && [ "$cur" != "$want" ]; then
    echo "!! [2/7] $name already exists at $cur and is not this kit's - nothing installed"; exit 1
  fi
done
echo "[2/7] every live pin is exact (S312 is live)"

fail3() { rm -f "$SA.S313new"*; rm -rf "$WALK"; echo "!! [3/7] $1 - nothing placed"; exit 1; }
rm -f "$SA.S313new"; \cp -p "$SA" "$SA.S313new"
"$PY" -B patch_sections_s313.py --file "$SA.S313new" --from "$SA_FROM" --expect "$SA_TO" || fail3 "the patch refused"
rm -f "$SA.S313new.bak_S313_"*
[ "$(m5 "$SA.S313new")" = "$SA_TO" ] || fail3 "patched to an unpredicted md5"
[ "$(m5 "$KDIR/section_map.py")" = "$SM_TO" ] || fail3 "the kit's section_map.py is not $SM_TO"
[ "$(m5 "$KDIR/stock_sections.html")" = "$PG_TO" ] || fail3 "the kit's stock_sections.html is not $PG_TO"
for f in "$SA.S313new" "$KDIR/section_map.py"; do
  "$PY" -c "import sys, os, tempfile, py_compile; py_compile.compile(sys.argv[1], cfile=os.path.join(tempfile.mkdtemp(), 'x.pyc'), doraise=True)" "$f" \
    || fail3 "$(basename "$f") does not compile"
done
echo "[3/7] patched to the predicted md5; both modules compile"

"$PY" -B "$KDIR/selftest_s313.py" | tail -1 | grep -q ', 0 failed' || fail3 "the section map's own selftest is red"
echo "[4/7] selftest green"

if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK/live" "$WALK/new" || fail3 "scratch failed"
  for f in stock_app.py stock_hub.html darpan_card.html claim_queue.py pad_receipt.py padwriter.py \
           padreader.py stock_schema.sql stock_check_live.html stock_diffs.html; do
    [ -f "$FIN/$f" ] && \cp -p "$FIN/$f" "$WALK/live/$f"
  done
  \cp -p "$WALK/live/"* "$WALK/new/" 2>/dev/null
  \cp -p "$SA.S313new" "$WALK/new/stock_app.py"
  \cp -p "$KDIR/section_map.py" "$WALK/new/section_map.py"
  \cp -p "$KDIR/stock_sections.html" "$WALK/new/stock_sections.html"
  "$PY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { rm -rf "$WALK"; rm -f "$SA.S313new"; echo "!! [5/7] scratch copy of the database failed - nothing placed"; exit 1; }
  WOUT="$( cd "$FIN" && timeout 170 "$PY" -B "$KDIR/walk_s313.py" "$WALK/live" "$WALK/new" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q '^WALK OK' || { rm -rf "$WALK"; rm -f "$SA.S313new"; echo "!! [5/7] the walk is red - nothing placed"; exit 1; }
  echo "[5/7] walked green on a scratch copy of the live database"
else echo "[5/7] walk skipped (NOWALK=1, test only)"; fi

BAK_SA="$SA.bak_S313_${SA_FROM:0:8}"; \cp -p "$SA" "$BAK_SA"
\cp -p "$KDIR/section_map.py" "$SM" && SM_PLACED=1
\cp -p "$KDIR/stock_sections.html" "$PG" && PG_PLACED=1
mv -f "$SA.S313new" "$SA"
[ "$(m5 "$SA")" = "$SA_TO" ] || restore
[ "$(m5 "$SM")" = "$SM_TO" ] || restore
[ "$(m5 "$PG")" = "$PG_TO" ] || restore
echo "[6/7] placed; every md5 read back == its to-pin (backup .bak_S313_${SA_FROM:0:8})"

if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance >/dev/null 2>&1; sleep 3
  systemctl is-active --quiet clinic-finance || restore
  # F-525: the gate hits a PUBLIC_PATHS route. Login-gated pages are probed for information only.
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
  c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/sections)
  c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/hub)
  echo "health : finance $c1 · the section map $c2 · hub $c3 (302/401 = the login gate, expected)"
  [ "$c1" = 200 ] || restore
  for c in "$c2" "$c3"; do case "$c" in 200|302|401) : ;; *) restore ;; esac; done
  echo "[7/7] clinic-finance active and answering"
else echo "[7/7] restart skipped (NORESTART=1, test only)"; fi

rm -rf "$WALK"
echo "$KIT: DONE"
echo "   section_map.py      $(m5 "$SM")"
echo "   stock_sections.html $(m5 "$PG")"
echo "   stock_app.py        $(m5 "$SA")"
echo "   the page:           https://followup.dr-manoj.in/finance/stock/page/sections"
