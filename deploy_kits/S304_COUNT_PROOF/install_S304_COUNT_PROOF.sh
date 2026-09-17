#!/bin/bash
# install_S304_COUNT_PROOF.sh -- step 7 of the stock check becomes a real proof: for each item with vouchers
# ENTERED in Marg, did Marg's next export move by exactly the voucher? (drift = Marg minus our computed figure,
# same basis, purchases in). It stops reading "done" from the counting close of 06-Sep.
#   /root/finance/stock_app.py     5cc1328d -> b997aa35  (patched on the box: _proof_state; the hub's step 7)
#   /root/finance/stock_hub.html   a3bfab19 -> 3f548592  (replaced whole: step 7 text and the lines that differ)
# Reads only; no table. clinic-finance restarted.
# Before anything is placed: the patched module walks a SCRATCH copy of the live database.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S304_COUNT_PROOF/install_S304_COUNT_PROOF.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S304_COUNT_PROOF"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
VPY="$ROOT/wa/venv/bin/python3"; [ -x "$VPY" ] || VPY="$(command -v python3)"
SPY="/usr/bin/python3"; [ -x "$SPY" ] || SPY="$VPY"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s304_walk_$STAMP"
declare -A FROM=( [stock_app.py]=5cc1328d9289ad8b1f662fe4d4e33ef4 [stock_hub.html]=a3bfab191fb7ac2f0dd02bf6852ae9bf )
declare -A TO=(   [stock_app.py]=b997aa355d4b56a0794534369e38385f [stock_hub.html]=3f54859201892ec59dfc4455f07b330b )
ORDER=(stock_app.py stock_hub.html)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(m5 stock_hub.html)" = "${TO[stock_hub.html]}" ] || { echo "!! [1/8] the kit's stock_hub.html is not the predicted file - nothing installed"; exit 1; }
echo "[1/8] kit sums green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then echo "ALREADY INSTALLED (every live md5 == its to-pin)."; exit 0; fi
for f in "${ORDER[@]}"; do
  cur="$(m5 "$FIN/$f")"; echo "$f : from ${FROM[$f]} -> to ${TO[$f]} ; live $cur"
  [ "$cur" = "${FROM[$f]}" ] || { echo "!! [2/8] $FIN/$f is $cur, expected ${FROM[$f]} - nothing installed"; exit 1; }
done
echo "[2/8] every live pin exact"
for f in stock_app.py; do rm -f "$FIN/$f.S304new"*; \cp -p "$FIN/$f" "$FIN/$f.S304new" || { echo "!! [3/8] copy failed"; exit 1; }; done
\cp -p stock_hub.html "$FIN/stock_hub.html.S304new" || { echo "!! [3/8] copy failed"; exit 1; }
"$VPY" -B patch_count_proof_s304.py --app "$FIN/stock_app.py.S304new" \
    --app-from "${FROM[stock_app.py]}" \
  || { echo "!! [3/8] patch refused - nothing placed"; rm -f "$FIN"/*.S304new*; exit 1; }
rm -f "$FIN"/*.S304new.bak_S304_*
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f.S304new")" = "${TO[$f]}" ] || { echo "!! [3/8] $f is not the predicted md5 - nothing placed"; rm -f "$FIN"/*.S304new; exit 1; }
done
"$VPY" -m py_compile "$FIN/stock_app.py.S304new" || { echo "!! [3/8] compile failed - nothing placed"; rm -f "$FIN"/*.S304new; exit 1; }
echo "[3/8] patched on the box to the predicted md5s; py_compile green"
if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK/app" && cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
  \cp -p "$FIN/stock_app.py.S304new" "$WALK/app/stock_app.py"
  "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { echo "!! [4/8] scratch copy of the database failed - nothing placed"; rm -rf "$WALK"; rm -f "$FIN"/*.S304new; exit 1; }
  WOUT="$( cd "$WALK/app" && timeout 170 "$SPY" -B "$KDIR/walk_s304.py" "$WALK/app" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { echo "!! [4/8] walk red - nothing placed"; rm -rf "$WALK"; rm -f "$FIN"/*.S304new; exit 1; }
  rm -rf "$WALK"; echo "[4/8] walk green on a scratch copy of the live database"
else echo "[4/8] walk skipped (NOWALK=1, test only)"; fi
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S304_${FROM[$f]:0:8}"; \cp -p "$FIN/$f" "${BAK[$f]}" || { echo "!! [5/8] backup failed - nothing placed"; exit 1; }; echo "backup : ${BAK[$f]}"; done
restore() { echo "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  rm -f "$FIN"/*.S304new
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; sleep 3; fi
  for f in "${ORDER[@]}"; do echo "   $FIN/$f $(m5 "$FIN/$f")"; done; exit 1; }
for f in "${ORDER[@]}"; do mv -f "$FIN/$f.S304new" "$FIN/$f" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
echo "[5/8] placed"
if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; sleep 4
  systemctl is-active --quiet clinic-finance || { echo "!! clinic-finance not active"; restore; }
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
  c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/amir)
  c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/hub)
  echo "health : finance $c1 · Amir's board $c2 · the hub $c3 (302/401 = the login gate)"
  [ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ] || [ "$c2" = 200 ]; } && { [ "$c3" = 302 ] || [ "$c3" = 401 ] || [ "$c3" = 200 ]; } || restore
  echo "[6/8] clinic-finance active and answering"
else echo "[6/8] restart skipped (NORESTART=1, test only)"; fi
echo "[7/8] md5 of the installed files:"; for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
echo "[8/8] $KIT: DONE"
echo "open: Stock Check tile -> step 7"
