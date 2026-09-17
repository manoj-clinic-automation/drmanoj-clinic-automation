#!/bin/bash
# install_S299_STOCK_CHECK_HUB.sh -- the portal's Stock Check tile opens ONE page carrying every step
# of the count, and the swaps are answered there in the 09-Sep workbook's TRY TO MATCH layout.
# S299 = the held S297 with the owner's two fixes (he types answers too; a confirmed swap is STOCK ISSUE +
# STOCK RECEIVE vouchers at once, on Amir's board, the Marg cleanup Excel and the hub's step 6).
#   /root/finance/stock_app.py     bb7df8d7 -> 75ffe861  (patched on the box: engine, answers, swap vouchers, hub routes)
#   /root/finance/pad_receipt.py   239a81fb -> f06daf16  (Darpan's list: Qty in Marg | Physical <day> | Difference)
#   /root/finance/stock_desk.html  aac7f96c -> 485720fd  (footer link to the hub)
#   /root/finance/stock_amir.html  32aa7d45 -> 3181d9de  (swaps first on the vouchers card; the typing card for the owner too)
#   /root/finance/stock_hub.html   NEW d0bec54f   (the page)
#   /root/portal/portal.py         c14c2c64 -> e13adbd6  (the Stock Check tile's address and line)
# New table stock_match (created on first use). Nothing else. clinic-finance and clinic-portal restarted.
# Before anything is placed: the patched module walks a SCRATCH copy of the live database.
#
# One line to run on the VPS:
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S299_STOCK_CHECK_HUB/install_S299_STOCK_CHECK_HUB.sh
#
# Env (test only): ROOT=/some/dir   NORESTART=1   NOWALK=1
set -u
KIT="S299_STOCK_CHECK_HUB"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"; POR="$ROOT/portal"; DBF="${FINANCE_DB:-$FIN/finance.db}"
VPY="$ROOT/wa/venv/bin/python3"; [ -x "$VPY" ] || VPY="$(command -v python3)"
SPY="/usr/bin/python3"; [ -x "$SPY" ] || SPY="$VPY"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s299_walk_$STAMP"
HUB_MD5="d0bec54f682cbe41c5bec70b30bbefb9"
declare -A FROM=( [stock_app.py]=bb7df8d78b0f1ff8cfd86a5c260f301c [pad_receipt.py]=239a81fb7f637663092424c20974ca01
                  [stock_desk.html]=aac7f96c73f879dba557310d207d064f [portal.py]=c14c2c649e0405378abcd95d8749c666
                  [stock_amir.html]=32aa7d45fc93f19d4526a5bca3a3743a )
declare -A TO=(   [stock_app.py]=75ffe86168e94c98fd1d724d0226a373 [pad_receipt.py]=f06daf1621b025557b648378398c6c83
                  [stock_desk.html]=485720fd2bb75ba8669b11d3dff4c0d1 [portal.py]=e13adbd65d82ba9015fcbb1b24d832c3
                  [stock_amir.html]=3181d9de5133afd51fe46dd2f61e9133 )
declare -A DEST=( [stock_app.py]="$FIN/stock_app.py" [pad_receipt.py]="$FIN/pad_receipt.py"
                  [stock_desk.html]="$FIN/stock_desk.html" [portal.py]="$POR/portal.py" [stock_amir.html]="$FIN/stock_amir.html" )
ORDER=(stock_app.py pad_receipt.py stock_desk.html portal.py stock_amir.html)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
echo "== $KIT installer =="
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
echo "[1/8] kit sums green"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL=0; done
[ "$(m5 "$FIN/stock_hub.html")" = "$HUB_MD5" ] || ALL=0
if [ "$ALL" = 1 ]; then echo "ALREADY INSTALLED (every live md5 == its to-pin)."; exit 0; fi
for f in "${ORDER[@]}"; do
  cur="$(m5 "${DEST[$f]}")"; echo "$f : from ${FROM[$f]} -> to ${TO[$f]} ; live $cur"
  [ "$cur" = "${FROM[$f]}" ] || { echo "!! [2/8] ${DEST[$f]} is $cur, expected ${FROM[$f]} - nothing installed"; exit 1; }
done
[ -e "$FIN/stock_hub.html" ] && { echo "!! [2/8] $FIN/stock_hub.html exists but is not this kit's - nothing installed"; exit 1; }
echo "[2/8] every live pin exact"
for f in "${ORDER[@]}"; do rm -f "${DEST[$f]}.S299new"*; \cp -p "${DEST[$f]}" "${DEST[$f]}.S299new" || { echo "!! [3/8] copy failed"; exit 1; }; done
"$VPY" -B patch_stock_check_hub_s299.py --app "$FIN/stock_app.py.S299new" --receipt "$FIN/pad_receipt.py.S299new" \
    --desk "$FIN/stock_desk.html.S299new" --portal "$POR/portal.py.S299new" --amir "$FIN/stock_amir.html.S299new" \
    --app-from "${FROM[stock_app.py]}" --receipt-from "${FROM[pad_receipt.py]}" --desk-from "${FROM[stock_desk.html]}" --portal-from "${FROM[portal.py]}" --amir-from "${FROM[stock_amir.html]}" \
  || { echo "!! [3/8] patch refused - nothing placed"; rm -f "$FIN"/*.S299new* "$POR"/*.S299new*; exit 1; }
rm -f "$FIN"/*.S299new.bak_S299_* "$POR"/*.S299new.bak_S299_*
for f in "${ORDER[@]}"; do
  [ "$(m5 "${DEST[$f]}.S299new")" = "${TO[$f]}" ] || { echo "!! [3/8] $f patched to an unpredicted md5 - nothing placed"; rm -f "$FIN"/*.S299new "$POR"/*.S299new; exit 1; }
done
"$VPY" -m py_compile "$FIN/stock_app.py.S299new" "$FIN/pad_receipt.py.S299new" "$POR/portal.py.S299new" \
  || { echo "!! [3/8] compile failed - nothing placed"; rm -f "$FIN"/*.S299new "$POR"/*.S299new; exit 1; }
echo "[3/8] patched on the box to the predicted md5s; py_compile green"
if [ "${NOWALK:-0}" != "1" ]; then
  mkdir -p "$WALK/app" && cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
  \cp -p "$FIN/stock_app.py.S299new" "$WALK/app/stock_app.py"; \cp -p "$FIN/pad_receipt.py.S299new" "$WALK/app/pad_receipt.py"; \cp -p stock_hub.html "$WALK/app/"
  "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
    || { echo "!! [4/8] scratch copy of the database failed - nothing placed"; rm -rf "$WALK"; rm -f "$FIN"/*.S299new "$POR"/*.S299new; exit 1; }
  WOUT="$( cd "$WALK/app" && timeout 170 "$SPY" -B "$KDIR/walk_s299.py" "$WALK/app" "$WALK/walk.db" 2>&1 | tail -2 )"
  echo "$WOUT" | sed 's/^/       /'
  echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { echo "!! [4/8] walk red - nothing placed"; rm -rf "$WALK"; rm -f "$FIN"/*.S299new "$POR"/*.S299new; exit 1; }
  rm -rf "$WALK"; echo "[4/8] walk green on a scratch copy of the live database"
else echo "[4/8] walk skipped (NOWALK=1, test only)"; fi
declare -A BAK
for f in "${ORDER[@]}"; do BAK[$f]="${DEST[$f]}.bak_S299_${FROM[$f]:0:8}"; \cp -p "${DEST[$f]}" "${BAK[$f]}" || { echo "!! [5/8] backup failed - nothing placed"; exit 1; }; echo "backup : ${BAK[$f]}"; done
restore() { echo "!! RED after placing - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  [ -e "$FIN/stock_hub.html" ] && mv -f "$FIN/stock_hub.html" "$FIN/stock_hub.html.removed_S299_$STAMP"
  rm -f "$FIN"/*.S299new "$POR"/*.S299new
  if [ "${NORESTART:-0}" != "1" ]; then systemctl restart clinic-finance clinic-portal || true; sleep 3; fi
  for f in "${ORDER[@]}"; do echo "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done; exit 1; }
for f in "${ORDER[@]}"; do mv -f "${DEST[$f]}.S299new" "${DEST[$f]}" || restore; done
\cp -p stock_hub.html "$FIN/stock_hub.html" || restore
[ "$(m5 "$FIN/stock_hub.html")" = "$HUB_MD5" ] || restore
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || restore; done
echo "[5/8] placed; stock_hub.html $HUB_MD5"
if [ "${NORESTART:-0}" != "1" ]; then
  systemctl restart clinic-finance || restore; systemctl restart clinic-portal || restore; sleep 4
  for s in clinic-finance clinic-portal; do systemctl is-active --quiet "$s" || { echo "!! $s not active"; restore; }; done
  c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
  c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8099/portal)
  c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/stock/page/hub)
  echo "health : finance $c1 · portal $c2 · the hub $c3 (302/401 = the login gate)"
  [ "$c1" = 200 ] && { [ "$c2" = 200 ] || [ "$c2" = 302 ]; } && { [ "$c3" = 302 ] || [ "$c3" = 401 ] || [ "$c3" = 200 ]; } || restore
  echo "[6/8] both services active and answering"
else echo "[6/8] restart skipped (NORESTART=1, test only)"; fi
echo "[7/8] md5 of the installed files:"; for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done; md5sum "$FIN/stock_hub.html"
echo "[8/8] $KIT: DONE"
echo "open: the Stock Check tile on your portal"
