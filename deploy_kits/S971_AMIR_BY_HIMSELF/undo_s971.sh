#!/bin/bash
# undo_s971.sh · kit S971_AMIR_BY_HIMSELF: the four files back to their FROM (each only when still at the kit's TO), the two new files moved
# aside (.bak_S971_removed_*), clinic-finance restarted. Every S971 card still open on Amir's page is withdrawn first (the old page could not
# answer it: review S4). Every withdrawn S971 reversal and S969 desk write-off is set aside as kind 'tap_wd' (the old judge reads every
# 'tap' as an ask and would call a withdrawn one "Amir said done -- not in Marg": second look S1). The tables stay (nothing reads them after the undo).
#    bash /root/deploy/repo/deploy_kits/S971_AMIR_BY_HIMSELF/undo_s971.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FILES=("finance/stock_check.py 5a8bde2284172cb3f77df40e87f52d62" "finance/stock_check.html ac3de34295801051fd2d481295294d35"
       "finance/voucher_judge.py 768adaa9c08c4398ae95a035841ec373" "finance/amir_day.py 6212fbf092c9d4afb6a7efba10a992a2"
       "finance/voucher_inquiry.py NEW" "finance/stock_losses.html NEW")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S971 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
ST="$(date +%Y%m%d_%H%M%S)"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; PYU="${VPY:-/root/wa/venv/bin/python3}"; [ -x "$PYU" ] || PYU=python3
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; c="$(m5 "$f")"
  if [ "$fr" = NEW ]; then [ -z "$c" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- not the kit's; nothing undone. Tell Claude."; exit 1; }; continue; fi
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$f.bak_S971_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
WD=$("$PYU" -c "
import sqlite3,sys,datetime as dt
c=sqlite3.connect(sys.argv[1], timeout=30); ts=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).strftime('%Y-%m-%d %H:%M:%S')
n=c.execute(\"UPDATE amir_job SET said_at=?, said_by='undo_s971', said_what='withdrawn', done_at=?, done_how='withdrawn' WHERE key LIKE 'S971:%' AND done_at IS NULL\", (ts, ts)).rowcount
m=c.execute(\"UPDATE amir_job SET kind='tap_wd' WHERE kind='tap' AND done_how='withdrawn' AND (key LIKE 'S971:rev:%' OR key LIKE 'S969:wo:%')\").rowcount
c.commit(); print('S971 cards withdrawn:', n, '- withdrawn lines set aside:', m)" "$LIVE_DB" 2>&1 | tail -1)
case "$WD" in "S971 cards withdrawn:"*) echo "   $WD";; *) echo "!! could not withdraw the S971 cards ($WD) - nothing undone. Tell Claude."; exit 1;; esac
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
  if [ "$fr" = NEW ]; then if [ -f "$f" ]; then mv -f "$f" "$f.bak_S971_removed_$ST" && echo "   $n moved aside"; else echo "   $n already absent"; fi; continue; fi
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   $n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S971_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   $n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
"$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S971 UNDONE."
