#!/bin/bash
# undo_s957.sh · kit S957_COUNT_LEFTOVERS: the judgments it re-made put back (from its own moment), the three files back to their FROM
# (each only when still at the kit's TO), clinic-finance restarted. S952 / S954 / S956 stay.
#    bash /root/deploy/repo/deploy_kits/S957_COUNT_LEFTOVERS/undo_s957.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("record_judges.py 5c5cca265812183968c3509e40ffd2a8" "stock_figure.py df35fc932fe936e3543edd3ae47e0d53" "stock_watch.py 401684eaafc35f10d622046db856246c")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S957 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
RJ="$ROOT/finance/record_judges.py"; ATF="$ROOT/finance/.s957_rejudged_at"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; c="$(m5 "$ROOT/finance/$n")"
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! finance/$n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$ROOT/finance/$n.bak_S957_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
if [ -s "$ATF" ] && [ "$(m5 "$RJ")" = "$(to_of record_judges.py)" ]; then
  U=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" timeout 900 "$VPY" -W ignore -B "$RJ" --undo-rejudge-from "$(cat "$ATF")" 2>&1 | tail -1)
  case "$U" in "S954 undo: "*) echo "   the judgments: $U";; *) echo "!! the judgments could not be put back ($U) -- the files are left at the new version. Tell Claude."; exit 1;; esac
fi
A=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" timeout 60 "$VPY" -W ignore -B "$KDIR/amir_s957.py" remove 2>&1 | tail -1); echo "   Amir's card: $A (a job he tapped done stays)"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/finance/$n"
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   finance/$n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S957_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   finance/$n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
rm -f "$ATF"; "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S957 undo: done."
