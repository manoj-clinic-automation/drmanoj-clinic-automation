#!/bin/bash
# undo_s976.sh · kit S976_WHOLE_UNIT_PACK: the five files back to their FROM (each only when still at the kit's TO), every row fix_s976.py
# changed put back from its before-image (s976_fix), the stock record rebuilt by the old files, clinic-finance restarted.
#    bash /root/deploy/repo/deploy_kits/S976_WHOLE_UNIT_PACK/undo_s976.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"; RLOCK="${RLOCK:-/tmp/stock_record.lock}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FILES=("finance/stock_figure.py 0d8cab560d19783febf134058f447763" "finance/stock_watch.py fe0a89cd0206b19ccf5439c9f364fb5e"
       "finance/stockmatch.py 1f5a15bade4f6e002e61b883eadcaee0" "finance/voucher_judge.py 59a68bb15c24261f533a48a33457fccb"
       "finance/stock_check.py 6b8d077cd2e30b18dd02e42551a2d83f")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
inf() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" PYTHONDONTWRITEBYTECODE=1 timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S976 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; c="$(m5 "$f")"
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$f.bak_S976_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   $n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S976_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   $n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
echo "   the data: $(inf "$KDIR/fix_s976.py" "$LIVE_DB" --undo | tail -1)"
echo "   the record: $(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" flock -w 120 "$RLOCK" timeout 900 "$VPY" -W ignore -B -c "import sqlite3,stock_record as SR; c=sqlite3.connect('$LIVE_DB',timeout=30); print('rebuilt', SR.build(c).get('ok'))" 2>&1 | tail -1)"
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S976 UNDONE."
