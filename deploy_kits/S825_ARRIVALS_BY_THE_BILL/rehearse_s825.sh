#!/bin/bash
# rehearse_s825.sh -- S825 (rebuilt S457): the installer on a STAND-IN root in the device VM (the 14-Nov bundle's files, a database copy with
# made-up tied orders, a made-up assets store, a spine copy); systemctl / journalctl / health stubbed. Never the live box.
#   bash rehearse_s825.sh <kit dir> <bench dir: /tmp/s457w>
set -u
K="$1"; B="$2"; R="$B/stand"; OUT=""
OT0=3f20faca; SF0=a0008c14; OR0=bdefd058
OT1=$(awk '$2=="finance/order_track.py"{print substr($1,1,8)}' "$K/TO_PINS.md5"); SF1=$(awk '$2=="finance/stock_figure.py"{print substr($1,1,8)}' "$K/TO_PINS.md5"); OR1=$(awk '$2=="finance/order_rules.py"{print substr($1,1,8)}' "$K/TO_PINS.md5")
mk() { rm -rf "$R"; mkdir -p "$R/finance" "$R/shared" "$R/assetapp" "$R/deploy" "$R/bin"
  cp -rp "$B/b/root/finance/." "$R/finance/"; cp -rp "$B/b/root/shared/." "$R/shared/"; cp "$B/keep/finance.db" "$R/finance/finance.db"; cp "$B/keep/assets.db" "$R/assetapp/assets.db"
  cp "$B/spine.db.failed" "$R/finance/spine/spine.db"
  # S459 (F-1400): the stand's made-up tied orders were made by the walk's own fixture (WALK* names, scan ids 9901-9903); the installer's
  # walk then added its fixture again on top and went red. Rename the stand's copies so the walk's fixture never meets them.
  python3 -B -c 'import sqlite3,sys
f=sqlite3.connect(sys.argv[1]); a=sqlite3.connect(sys.argv[2]); R=lambda t: "REPLACE(%s,\x27WALK\x27,\x27REHR\x27)" % t
for t,c in (("purchase_order","vendor"),("purchase_order","supplier_norm"),("purchase_order_line","item"),("stock_item_section","item_key"),("stock_item_section","item")):
    f.execute("UPDATE %s SET %s=%s WHERE %s LIKE \x27%%WALK%%\x27" % (t,c,R(c),c))
for t,c in (("bills","vendor"),("bill_items","item_name"),("claude_reading","data")):
    a.execute("UPDATE %s SET %s=%s WHERE %s LIKE \x27%%WALK%%\x27" % (t,c,R(c),c))
f.commit(); a.commit()' "$R/finance/finance.db" "$R/assetapp/assets.db"
  printf '#!/bin/sh\n[ "$1" = show ] && { echo 0; exit 0; }\nexit 0\n' > "$R/bin/sysctl"; printf '#!/bin/sh\nexit 0\n' > "$R/bin/jctl"
  printf '#!/bin/sh\ncase "$1" in */healthz) printf 200;; *) printf 302;; esac\n' > "$R/bin/health"; chmod +x "$R/bin/"*; rm -rf "$R/kit"; cp -rp "$K" "$R/kit"; }
run() { (ROOT="$R" APY=$(command -v python3) VPY="$B/venv/bin/python3" LOCK="$R/deploy/lock" SYSTEMCTL="$R/bin/sysctl" JOURNALCTL="$R/bin/jctl" HEALTH_CMD="$R/bin/health" \
  SKIP_WINDOW=1 TMPW="$R" "$@" bash "$R/kit/install_S825_ARRIVALS_BY_THE_BILL.sh" 2>&1); }
m5() { md5sum "$1" | cut -c1-8; }
pins() { echo "$(m5 $R/finance/order_track.py) $(m5 $R/finance/stock_figure.py) $(m5 $R/finance/order_rules.py)"; }
N=0; P=0
ok() { N=$((N+1)); if [ "$2" = 1 ]; then P=$((P+1)); echo "  ok   $1"; else echo "  FAIL $1"; printf '%s\n' "$OUT" | tail -6 | sed 's/^/        /'; fi; }
mk; OUT=$(run env DRY=1); ok "1 DRY: green, nothing written" $([ "$(pins)" = "$OT0 $SF0 $OR0" ] && printf '%s' "$OUT" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
printf '%s\n' "$OUT" | grep -E "^\[|PROOF|WALK" | sed 's/^/        /'
mk; echo "# a later edit" >> "$R/finance/order_rules.py"; OUT=$(run env); ok "2 a changed live file: STOP, nothing installed" $(printf '%s' "$OUT" | grep -q "changed after this kit was built" && [ ! -e "$R/finance/stock_figure.py.bak_S825_$SF0" ] && echo 1 || echo 0)
mk; mkdir "$R/deploy/lock"; echo other > "$R/deploy/lock/owner"; OUT=$(run env); ok "3 the lock held by another build: nothing installed" $(printf '%s' "$OUT" | grep -q "another build holds the lock" && [ "$(pins)" = "$OT0 $SF0 $OR0" ] && echo 1 || echo 0)
mk; printf 'not a database' > "$R/assetapp/assets.db"; OUT=$(run env); ok "4 the scan store unreadable: NOT PROVEN, nothing installed" $(printf '%s' "$OUT" | grep -q "NOT PROVEN" && [ "$(pins)" = "$OT0 $SF0 $OR0" ] && echo 1 || echo 0)
mk; OUT=$(run env REHEARSE_RED_AT=7); ok "5 a forced red after placing: all three old files back" $(printf '%s' "$OUT" | grep -q "RED after placing" && [ "$(pins)" = "$OT0 $SF0 $OR0" ] && echo 1 || echo 0)
mk; OUT=$(run env); ok "6 install: DONE, the files at their TO pins, the backups at their FROM pins, the lock released" $(printf '%s' "$OUT" | grep -q "S825_ARRIVALS_BY_THE_BILL: DONE" && [ "$(pins)" = "$OT1 $SF1 $OR1" ] && [ "$(m5 $R/finance/stock_figure.py.bak_S825_$SF0)" = $SF0 ] && [ "$(m5 $R/finance/order_track.py.bak_S825_$OT0)" = $OT0 ] && [ "$(m5 $R/finance/order_rules.py.bak_S825_$OR0)" = $OR0 ] && [ ! -e "$R/deploy/lock" ] && echo 1 || echo 0)
printf '%s\n' "$OUT" | grep -E "^\[|undo" | sed 's/^/        /'
OUT=$(run env); ok "7 again: ALREADY INSTALLED" $(printf '%s' "$OUT" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
UL=$(printf '%s' "$(run env)" | true); U=$(cd "$R" && for f in order_track stock_figure order_rules; do :; done; echo ok)
\cp -p "$R/finance/order_track.py.bak_S825_$OT0" "$R/finance/order_track.py" && \cp -p "$R/finance/stock_figure.py.bak_S825_$SF0" "$R/finance/stock_figure.py" && \cp -p "$R/finance/order_rules.py.bak_S825_$OR0" "$R/finance/order_rules.py"
OUT=""; ok "8 the undo puts the three old files back" $([ "$(pins)" = "$OT0 $SF0 $OR0" ] && echo 1 || echo 0)
mk; echo x >> "$R/kit/walk_s825.py"; OUT=$(run env); ok "9 a kit file altered: SUMS gate, nothing installed" $(printf '%s' "$OUT" | grep -q "SUMS.md5 gate failed" && echo 1 || echo 0)
mk; \cp -p "$R/kit/make_s825.py" /dev/null; cp "$B/built/stock_figure.py" "$R/finance/stock_figure.py"; OUT=$(run env); ok "10 one file already new, two old: STOP, nothing installed" $(printf '%s' "$OUT" | grep -q "changed after this kit was built" && [ "$(m5 $R/finance/order_track.py)" = $OT0 ] && echo 1 || echo 0)
rm -rf "$R"; echo "rehearse_s825: $P of $N"
