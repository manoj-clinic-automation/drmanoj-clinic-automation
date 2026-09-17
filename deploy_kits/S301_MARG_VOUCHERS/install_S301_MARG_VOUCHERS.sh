#!/bin/bash
# install_S301_MARG_VOUCHERS.sh -- the Marg cleanup list becomes Marg vouchers Amir can key (at most six lines
# each, the 09-Sep workbook's VOUCHER 1 - SHORT / VOUCHER 2 - EXCESS), and each one is recorded as entered.
#   /root/finance/stock_app.py     75ffe861 -> 5cc1328d  (patched on the box: the voucher engine, three routes)
#   /root/finance/stock_amir.html  3181d9de -> 14024b8d  (patched on the box: card 2 -- make, enter, record)
#   /root/finance/stock_hub.html   d0bec54f -> a3bfab19  (replaced whole: step 6 figures and the button)
# New tables stock_voucher_line and stock_voucher_entered (created on first use). clinic-finance restarted.
# Before anything is placed: the patched module walks a SCRATCH copy of the live database.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S301_MARG_VOUCHERS/install_S301_MARG_VOUCHERS.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S301_MARG_VOUCHERS"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; DBF="${FINANCE_DB:-$FIN/finance.db}"
VPY="$ROOT/wa/venv/bin/python3"; [ -x "$VPY" ] || VPY="$(command -v python3)"
SPY="/usr/bin/python3"; [ -x "$SPY" ] || SPY="$VPY"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s301_walk_$STAMP"
declare -A FROM=( [stock_app.py]=75ffe86168e94c98fd1d724d0226a373 [stock_amir.html]=3181d9de5133afd51fe46dd2f61e9133 [stock_hub.html]=d0bec54f682cbe41c5bec70b30bbefb9 )
declare -A TO=(   [stock_app.py]=5cc1328d9289ad8b1f662fe4d4e33ef4 [stock_amir.html]=14024b8dfc64c76959ec12f43e0a4f88 [stock_hub.html]=a3bfab191fb7ac2f0dd02bf6852ae9bf )
ORDER=(stock_app.py stock_amir.html stock_hub.html)
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
for f in stock_app.py stock_amir.html; do rm -f "$FIN/$f.S301new"*; \cp -p "$FIN/$f" "$FIN/$f.S301new" || { echo "!! [3/8] copy failed"; exit 1; }; done
\cp -p stock_hub.html "$FIN/stock_hub.html.S301new" || { echo "!! [3/8] copy failed"; exit 1; }
"$VPY" -B patch_marg_vouchers_s301.py --app "$FIN/stock_app.py.S301new" --amir "$FIN/stock_amir.html.S301new" \
    --app-from "${FROM[stock_app.py]}" --amir-from "${FROM[stock_amir.html]}" \
  || { echo "!! [3/8] patch refused - nothing placed"; rm -f "$FIN"/*.S301new*; exit 1; }
rm -f "$FIN"/*.S301new.bak_S301_*
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f.S301new")" = "${TO[$f]}" ] || { echo "!! [3/8] $f is not the predicted md5 - nothing placed"; rm -f "$FIN"/*.S301new; exit 1; }
done
"$VPY" -m py_compile "$FIN/stock_app.py.S301new" || { echo "!! [3/8] compile failed - nothing placed"; rm -f "$FIN"/*.S301new; exit 1; }
echo "[3/8] patched on the box to the predicted md5s; py_compile green"
if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK/app" && cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
  \cp -p "$FIN/stock_app.py.S301new" "$WALK/app/stock_app.py"
  "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { echo "!! [4/8] scratch copy of the database failed - nothing placed"; rm -rf "$WALK"; rm -f "$FIN"/*.S301new; exit 1; }
  WOUT="$( cd "$WALK/app" && timeout 170 "$SPY" -B "$KDIR/walk_s301.py" "$WALK/app" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { echo "!! [4/8] walk red - nothing placed"; rm -rf "$WALK"; rm -f "$FIN"/*.S301new; exit 1; }
  rm -rf "$WALK"; echo "[4/8] walk green on a scratch copy of the live database"
else echo "[4/8] walk skipped (NOWALK=1, test only)"; fi
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="$FIN/$f.bak_S301_${FROM[$f]:0:8}"; \cp -p "$FIN/$f" "${BAK[$f]}" || { echo "!! [5/8] backup failed - nothing placed"; exit 1; }; echo "backup : ${BAK[$f]}"; done
restore() { echo "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "$FIN/$f"; done
  rm -f "$FIN"/*.S301new
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance || true; sleep 3; fi
  for f in "${ORDER[@]}"; do echo "   $FIN/$f $(m5 "$FIN/$f")"; done; exit 1; }
for f in "${ORDER[@]}"; do mv -f "$FIN/$f.S301new" "$FIN/$f" || restore; done
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
echo "open: Stock Check tile -> step 6 -> The vouchers"
