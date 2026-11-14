#!/bin/bash
# rehearse_s824.sh -- S824: the installer on a STAND-IN root in the device VM (the 14-Nov bundle's files, the database copy, a made-up
# assets store holding Janta's three scans); systemctl / journalctl / health stubbed. Never the live box.
#   bash rehearse_s824.sh <kit dir> <bench dir: /tmp/s455w>
set -u
K="$1"; B="$2"; R="$B/stand"; OUT=""
mk() { rm -rf "$R"; mkdir -p "$R/finance" "$R/shared" "$R/assetapp" "$R/deploy" "$R/bin"
  cp -rp "$B/root/finance/." "$R/finance/"; cp -rp "$B/root/shared/." "$R/shared/"; cp "$B/finance.db" "$R/finance/finance.db"; cp "$B/fake_assets.db" "$R/assetapp/assets.db"
  printf '#!/bin/sh\n[ "$1" = show ] && { echo 0; exit 0; }\nexit 0\n' > "$R/bin/sysctl"; printf '#!/bin/sh\nexit 0\n' > "$R/bin/jctl"
  printf '#!/bin/sh\ncase "$1" in */healthz) printf 200;; *) printf 302;; esac\n' > "$R/bin/health"; chmod +x "$R/bin/"*; rm -rf "$R/kit"; cp -rp "$K" "$R/kit"; }
run() { (ROOT="$R" APY=$(command -v python3) VPY="$B/venv/bin/python" LOCK="$R/deploy/lock" SYSTEMCTL="$R/bin/sysctl" JOURNALCTL="$R/bin/jctl" HEALTH_CMD="$R/bin/health" \
  SKIP_WINDOW=1 TMPW="$R" "$@" bash "$R/kit/install_S824_REVISED_BILL_SETASIDE.sh" 2>&1); }
m5() { md5sum "$1" | cut -c1-8; }
N=0; P=0
ok() { N=$((N+1)); if [ "$2" = 1 ]; then P=$((P+1)); echo "  ok   $1"; else echo "  FAIL $1"; printf '%s\n' "$OUT" | tail -4 | sed 's/^/        /'; fi; }
mk; OUT=$(run env DRY=1); ok "1 DRY: green, nothing written" $([ "$(m5 $R/finance/scan_register.py)" = 9262c5dc ] && printf '%s' "$OUT" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
mk; echo "# a later edit" >> "$R/finance/scan_register.py"; OUT=$(run env); ok "2 a changed live file: STOP, nothing installed" $(printf '%s' "$OUT" | grep -q "changed after this kit was built" && [ ! -e "$R/finance/scan_register.py.bak_S824_9262c5dc" ] && echo 1 || echo 0)
mk; mkdir "$R/deploy/lock"; echo other > "$R/deploy/lock/owner"; OUT=$(run env); ok "3 the lock held by another build: nothing installed" $(printf '%s' "$OUT" | grep -q "another build holds the lock" && [ "$(m5 $R/finance/scan_register.py)" = 9262c5dc ] && echo 1 || echo 0)
mk; python3 - "$R/assetapp/assets.db" <<'PY'
import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute("UPDATE bills SET status='captured', dup_of=NULL WHERE stamp_no='B-0264'"); c.execute("DELETE FROM bills WHERE stamp_no='B-0271'"); c.commit()
PY
OUT=$(run env); ok "4 no revised bill in the store: NOT PROVEN, nothing installed" $(printf '%s' "$OUT" | grep -q "NOT PROVEN" && [ "$(m5 $R/finance/scan_register.py)" = 9262c5dc ] && echo 1 || echo 0)
mk; OUT=$(run env REHEARSE_RED_AT=7); ok "5 a forced red after placing: the old file back" $(printf '%s' "$OUT" | grep -q "RED after placing" && [ "$(m5 $R/finance/scan_register.py)" = 9262c5dc ] && echo 1 || echo 0)
mk; OUT=$(run env); ok "6 install: DONE, the file at its TO pin, the backup at its FROM pin, the lock released" $(printf '%s' "$OUT" | grep -q "S824_REVISED_BILL_SETASIDE: DONE" && [ "$(m5 $R/finance/scan_register.py)" = f0bb05cd ] && [ "$(m5 $R/finance/scan_register.py.bak_S824_9262c5dc)" = 9262c5dc ] && [ ! -e "$R/deploy/lock" ] && echo 1 || echo 0)
printf '%s\n' "$OUT" | grep -E "^\[|PROOF|Janta" | sed 's/^/        /'
OUT=$(run env); ok "7 again: ALREADY INSTALLED" $(printf '%s' "$OUT" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
U=$(printf '%s' "$(cd /tmp; ROOT=$R bash -c 'true')"); OUT2=$( \cp -p "$R/finance/scan_register.py.bak_S824_9262c5dc" "$R/finance/scan_register.py" && echo ok); ok "8 the undo line puts the old file back" $([ "$OUT2" = ok ] && [ "$(m5 $R/finance/scan_register.py)" = 9262c5dc ] && echo 1 || echo 0)
mk; echo x >> "$R/kit/walk_s824.py"; OUT=$(run env); ok "9 a kit file altered: SUMS gate, nothing installed" $(printf '%s' "$OUT" | grep -q "SUMS.md5 gate failed" && echo 1 || echo 0)
rm -rf "$R"; echo "rehearse_s824: $P of $N"
