#!/bin/bash
# rehearse_s828.sh -- S828 on a STAND-IN root in the device VM (the 14-Nov bundle, a database copy); services stubbed. Never the live box.
set -u
K="$1"; B="$2"; R="$B/stand828"; OUT=""
FROM8=471859b3; TO8=$(cut -c1-8 "$K/TO_PINS.md5")
mk() { rm -rf "$R"; mkdir -p "$R/finance" "$R/shared" "$R/deploy" "$R/bin"; cp -rp "$B/b/root/finance/." "$R/finance/"; cp -rp "$B/b/root/shared/." "$R/shared/"
  cp "$B/finance.db" "$R/finance/finance.db"
  printf '#!/bin/sh\n[ "$1" = show ] && { echo 0; exit 0; }\nexit 0\n' > "$R/bin/sysctl"; printf '#!/bin/sh\nexit 0\n' > "$R/bin/jctl"
  printf '#!/bin/sh\ncase "$1" in */healthz) printf 200;; *) printf 302;; esac\n' > "$R/bin/health"; chmod +x "$R/bin/"*; cp -rp "$K" "$R/kit"; }
run() { (ROOT="$R" APY=$(command -v python3) VPY="$B/venv/bin/python3" LOCK="$R/deploy/lock" SYSTEMCTL="$R/bin/sysctl" JOURNALCTL="$R/bin/jctl" HEALTH_CMD="$R/bin/health" \
  SKIP_WINDOW=1 TMPW="$R" "$@" bash "$R/kit/install_S828_BATCH_NOTICE_TRUE.sh" 2>&1); }
m5() { md5sum "$1" | cut -c1-8; }
N=0; P=0
ok() { N=$((N+1)); if [ "$2" = 1 ]; then P=$((P+1)); echo "  ok   $1"; else echo "  FAIL $1"; printf '%s\n' "$OUT" | tail -5 | sed 's/^/        /'; fi; }
mk; OUT=$(run env DRY=1); ok "1 DRY: green, nothing written" $([ "$(m5 $R/finance/owner_notice.py)" = $FROM8 ] && printf '%s' "$OUT" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
mk; echo "# later" >> "$R/finance/owner_notice.py"; OUT=$(run env); ok "2 a changed live file: STOP" $(printf '%s' "$OUT" | grep -q "changed after this kit was built" && echo 1 || echo 0)
mk; OUT=$(run env REHEARSE_RED_AT=7); ok "3 a red after placing: the old file back" $(printf '%s' "$OUT" | grep -q "RED after placing" && [ "$(m5 $R/finance/owner_notice.py)" = $FROM8 ] && echo 1 || echo 0)
mk; OUT=$(run env); ok "4 install: DONE at the TO pin, backup at FROM, lock released" $(printf '%s' "$OUT" | grep -q "S828_BATCH_NOTICE_TRUE: DONE" && [ "$(m5 $R/finance/owner_notice.py)" = $TO8 ] && [ "$(m5 $R/finance/owner_notice.py.bak_S828_$FROM8)" = $FROM8 ] && [ ! -e "$R/deploy/lock" ] && echo 1 || echo 0)
printf '%s\n' "$OUT" | grep -E "^\[|undo" | sed 's/^/        /'
OUT=$(run env); ok "5 again: ALREADY INSTALLED" $(printf '%s' "$OUT" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
mk; echo x >> "$R/kit/walk_s828.py"; OUT=$(run env); ok "6 a kit file altered: SUMS gate" $(printf '%s' "$OUT" | grep -q "SUMS.md5 gate failed" && echo 1 || echo 0)
rm -rf "$R"; echo "rehearse_s828: $P of $N"
