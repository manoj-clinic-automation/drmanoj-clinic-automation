#!/bin/bash
# undo_s958.sh · kit S958_DARPAN_LISTS: today's list it wrote taken back (rows not yet counted), the ten files back to their FROM (each only
# when still at the kit's TO), clinic-finance restarted. Carries the carry pass dropped by the new rule stay dropped (each has its reason).
#    bash /root/deploy/repo/deploy_kits/S958_DARPAN_LISTS/undo_s958.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/order_track.py 9baf057e45c38840381293933021193a" "finance/stock_watch.py 23873a1bc7d7ae78f533f34b19162eaa"
       "finance/stock_check.py 686845f8ec895506a51892d3fbf629d9" "finance/order_rules.py eac7ec3721fb729b9f3f45c0ce2510b3"
       "finance/darpan_kal.html 0165bcb329f0bcd70ecea477f7322d57" "finance/stockmatch.html 8ba51618ff8a35c2474285367ed81026"
       "finance/aaj_seed.py 6f4784ae945d8daba2c4296334aa669e" "portal/portal_sw.js ab728b08ccfdc2f0e904b223a7c28cc0"
       "finance/porders_s454.py 4e98e82e44be62d5164072e1ad87dd58" "finance/order_track_page.py 2d7384306c009c290dbe2a9cd048e7e1")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S958 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
ATF="$ROOT/finance/.s958_roster_ids"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; c="$(m5 "$ROOT/$n")"
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$ROOT/$n.bak_S958_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
if [ -f "$ATF" ]; then
  U=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" timeout 300 "$VPY" -W ignore -B "$KDIR/roster_s958.py" undo "$ATF" 2>&1 | tail -1); echo "   today's list: $U"
fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   $n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S958_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   $n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
rm -f "$ATF"; "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S958 undo: done."
