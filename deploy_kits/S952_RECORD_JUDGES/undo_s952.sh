#!/bin/bash
# undo_s952.sh · kit S952_RECORD_JUDGES: the two switches OFF and the data back first (every re-judged count and loss line, then every order
# line the scan repair changed and nobody touched since -- from s952_point_undo / s952_line_undo, newest first), then the four files back to their FROM bytes (each only when still at the
# kit's TO), record_judges.py removed, the cron line # S952_RECORD_CHECK taken out, clinic-finance restarted. S950 and earlier stay.
#    bash /root/deploy/repo/deploy_kits/S952_RECORD_JUDGES/undo_s952.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; CRONTAB="${CRONTAB:-crontab}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S952 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
NAMES=("finance/stock_figure.py" "finance/porders.py" "finance/stock_watch.py" "finance/stock_check.py" "finance/record_judges.py")
FROMS=("07bca1df78b6f9d3725eda94351158d8" "eeaad33783725305a3712de88650260d" "c7584585faf0fc786e4f09ce606989c5" "14ca39be464b14a5797f41103b8a448b" "absent")
if [ -f "$ROOT/finance/record_judges.py" ]; then
  U=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" timeout 900 "$VPY" -W ignore -B "$ROOT/finance/record_judges.py" --undo 2>&1 | tail -1)
  case "$U" in "S952 undo: "*) echo "   the data: $U";; *) echo "!! the data undo did not finish ($U) -- the files are left at the new version so it can run again. Tell Claude."; exit 1;; esac
fi
"$CRONTAB" -l 2>/dev/null | grep -v '# S952_RECORD_CHECK' | "$CRONTAB" - && echo "   the cron line # S952_RECORD_CHECK taken out"
did=0
for k in 0 1 2 3 4; do
  F="$ROOT/${NAMES[$k]}"; FROM="${FROMS[$k]}"; TO="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; c="$(m5 "$F")"; [ -f "$F" ] || c=absent
  if [ "$FROM" = absent ]; then
    if [ "$c" = absent ]; then echo "   ${NAMES[$k]} already absent"
    elif [ "$c" = "$TO" ]; then mv -f "$F" "$F.removed_S952_$(date +%Y%m%d_%H%M%S)" && { echo "   ${NAMES[$k]} taken out (kept beside it as .removed_S952_*)"; did=1; }
    else echo "!! ${NAMES[$k]} is ${c:0:8} -- not the kit's; left as it is. Tell Claude."; fi
    continue
  fi
  B="$F.bak_S952_${FROM:0:8}"
  if [ "$c" = "$FROM" ]; then echo "   ${NAMES[$k]} already at ${FROM:0:8}"
  elif [ "$c" != "$TO" ]; then echo "!! ${NAMES[$k]} is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."
  elif [ "$(m5 "$B")" != "$FROM" ]; then echo "!! the backup $B is missing or changed; ${NAMES[$k]} left as it is. Tell Claude."
  else \cp -p "$B" "$F" && [ "$(m5 "$F")" = "$FROM" ] && { echo "   ${NAMES[$k]} back to ${FROM:0:8}"; did=1; } || echo "!! could not put ${NAMES[$k]} back"; fi
done
if [ "$did" = 1 ]; then "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"; fi
echo "   the stock of record rebuilt by the old code: $(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" timeout 900 "$VPY" -W ignore -B "$ROOT/finance/stock_record.py" --build --force 2>&1 | tail -1 | cut -c1-90)"
echo "S952 undo: done. (The settings count.judge_by_record and arrival.pair_by_scan stay at 0; a re-install turns them on.)"
