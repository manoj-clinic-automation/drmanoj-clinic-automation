#!/bin/bash
# rehearse_s827.sh -- S827: the installer on a STAND-IN root in the device VM (the 14-Nov bundle's files, the database copy, Mannat's line of bill 502 as it stands); systemctl / journalctl / health stubbed. Never the live box.
#   bash rehearse_s827.sh <kit dir> <bench dir: /tmp/s455w>
set -u
K="$1"; B="$2"; R="$B/stand"; OUT=""
mk() { rm -rf "$R"; mkdir -p "$R/finance" "$R/shared" "$R/assetapp" "$R/deploy" "$R/bin"
  cp -rp "$B/root/finance/." "$R/finance/"; cp -rp "$B/root/shared/." "$R/shared/"; cp "$B/finance.db" "$R/finance/finance.db"; cp "$B/fake_assets.db" "$R/assetapp/assets.db"
  printf '#!/bin/sh\n[ "$1" = show ] && { echo 0; exit 0; }\nexit 0\n' > "$R/bin/sysctl"; printf '#!/bin/sh\nexit 0\n' > "$R/bin/jctl"
  printf '#!/bin/sh\ncase "$1" in */healthz) printf 200;; *) printf 302;; esac\n' > "$R/bin/health"; chmod +x "$R/bin/"*; rm -rf "$R/kit"; cp -rp "$K" "$R/kit"; }
run() { (ROOT="$R" APY=$(command -v python3) VPY="$B/venv/bin/python" LOCK="$R/deploy/lock" SYSTEMCTL="$R/bin/sysctl" JOURNALCTL="$R/bin/jctl" HEALTH_CMD="$R/bin/health" \
  SKIP_WINDOW=1 TMPW="$R" "$@" bash "$R/kit/install_S827_LINES_TO_THE_LIVE_BILL.sh" 2>&1); }
m5() { md5sum "$1" | cut -c1-8; }
N=0; P=0
ok() { N=$((N+1)); if [ "$2" = 1 ]; then P=$((P+1)); echo "  ok   $1"; else echo "  FAIL $1"; printf '%s\n' "$OUT" | tail -4 | sed 's/^/        /'; fi; }
mk; OUT=$(run env DRY=1); ok "1 DRY: green, nothing written" $([ "$(m5 $R/finance/purchase_app.py)" = 98ae8f76 ] && printf '%s' "$OUT" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
mk; echo "# a later edit" >> "$R/finance/purchase_app.py"; OUT=$(run env); ok "2 a changed live file: STOP, nothing installed" $(printf '%s' "$OUT" | grep -q "changed after this kit was built" && [ ! -e "$R/finance/purchase_app.py.bak_S827_98ae8f76" ] && echo 1 || echo 0)
mk; mkdir "$R/deploy/lock"; echo other > "$R/deploy/lock/owner"; OUT=$(run env); ok "3 the lock held by another build: nothing installed" $(printf '%s' "$OUT" | grep -q "another build holds the lock" && [ "$(m5 $R/finance/purchase_app.py)" = 98ae8f76 ] && echo 1 || echo 0)
mk; python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"DELETE FROM purchase_bill WHERE supplier_norm='DEEPAM PHARMA' AND bill_no='502'\"); c.commit()" "$R/finance/finance.db"; OUT=$(run env); ok "4 the repair's dry run refused (Deepam's 502 not live): nothing installed" $(printf '%s' "$OUT" | grep -q "the repair's dry run" && [ "$(m5 $R/finance/purchase_app.py)" = 98ae8f76 ] && echo 1 || echo 0)
mk; OUT=$(run env REHEARSE_RED_AT=7); ok "5 a forced red after placing: the old file back" $(printf '%s' "$OUT" | grep -q "RED after placing" && [ "$(m5 $R/finance/purchase_app.py)" = 98ae8f76 ] && echo 1 || echo 0)
mk; OUT=$(run env); ok "6 install: DONE, the file at its TO pin, the backup at its FROM pin, the lock released" $(printf '%s' "$OUT" | grep -q "S827_LINES_TO_THE_LIVE_BILL: DONE" && [ "$(m5 $R/finance/purchase_app.py)" = d1999929 ] && [ "$(m5 $R/finance/purchase_app.py.bak_S827_98ae8f76)" = 98ae8f76 ] && [ ! -e "$R/deploy/lock" ] && echo 1 || echo 0)
printf '%s\n' "$OUT" | grep -E "^\[|PROOF|REPAIR" | sed 's/^/        /'
OUT=$(run env); ok "7 again: ALREADY INSTALLED" $(printf '%s' "$OUT" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
U=$(printf '%s' "$(cd /tmp; ROOT=$R bash -c 'true')"); OUT2=$( \cp -p "$R/finance/purchase_app.py.bak_S827_98ae8f76" "$R/finance/purchase_app.py" && echo ok); ok "8 the undo line puts the old file back" $([ "$OUT2" = ok ] && [ "$(m5 $R/finance/purchase_app.py)" = 98ae8f76 ] && echo 1 || echo 0)
mk; echo x >> "$R/kit/walk_s827.py"; OUT=$(run env); ok "9 a kit file altered: SUMS gate, nothing installed" $(printf '%s' "$OUT" | grep -q "SUMS.md5 gate failed" && echo 1 || echo 0)
rm -rf "$R"; echo "rehearse_s827: $P of $N"
