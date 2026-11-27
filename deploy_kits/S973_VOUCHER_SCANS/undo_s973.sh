#!/bin/bash
# undo_s973.sh · kit S973_VOUCHER_SCANS: the seven files back to their FROM (each only when still at the kit's TO), voucher_scan.py moved aside
# (.bak_S973_removed_*), clinic-finance and assetapp restarted. First every S973 print card still open on Amir's page is withdrawn (the old page
# could not draw it), and every claim waiting for its print and scan goes back to the owner's call ('yours' -- kit B's road, as before this kit).
# The table stays (nothing reads it after the undo). Papers already marked 'Stock voucher' in the scan app stay so (never a dealer's bill).
#    bash /root/deploy/repo/deploy_kits/S973_VOUCHER_SCANS/undo_s973.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; ASVC="${ASVC:-assetapp}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"; A_PORT="${A_PORT:-8030}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FILES=("finance/voucher_inquiry.py ac76b9d339de6b58b7835cab7e46e08d" "finance/voucher_judge.py 6c7259418481cd9f37099f93a9ca7b17"
       "finance/amir_day.py 27a2a128f8e6fbdbf0c015727db70538" "finance/porders_s454.py 3f52d1f390ff704d152fd3b96bba5afc" "finance/voucher_scan.py NEW"
       "assetapp/asset_register.py a325d0f400923e1989ff4cd2a4df408d" "assetapp/claude_reader.py 5b27b2269f4f358a36cd62aef6b0eb7a"
       "shared/scan_quality.py 505a114f34452b5be994b04eca36e4b7")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
ahz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$A_PORT/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S973 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
ST="$(date +%Y%m%d_%H%M%S)"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; PYU="${VPY:-/root/wa/venv/bin/python3}"; [ -x "$PYU" ] || PYU=python3
KEEP="shared/scan_quality.py"   # never put back: papers already filed 'Stock voucher' stay out of the bill checks (second look M2)
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; c="$(m5 "$f")"; [ "$n" = "$KEEP" ] && continue
  if [ "$fr" = NEW ]; then [ -z "$c" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- not the kit's; nothing undone. Tell Claude."; exit 1; }; continue; fi
  [ "$c" = "$fr" ] || [ "$c" = "$(to_of "$n")" ] || { echo "!! $n is ${c:0:8} -- neither the kit's TO nor its FROM; nothing undone. Tell Claude."; exit 1; }
  [ "$c" = "$fr" ] || [ "$(m5 "$f.bak_S973_${fr:0:8}")" = "$fr" ] || { echo "!! the backup of $n is missing or changed; nothing undone. Tell Claude."; exit 1; }; done
WD=$("$PYU" -c "
import sqlite3,sys,datetime as dt
c=sqlite3.connect(sys.argv[1], timeout=30); ts=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).strftime('%Y-%m-%d %H:%M:%S')
n=c.execute(\"UPDATE amir_job SET said_at=?, said_by='undo_s973', said_what='withdrawn', done_at=?, done_how='withdrawn' WHERE key LIKE 'S973:%' AND done_at IS NULL\", (ts, ts)).rowcount
has=c.execute(\"SELECT 1 FROM sqlite_master WHERE name='stock_voucher_claim'\").fetchone()
m=c.execute(\"UPDATE stock_voucher_claim SET state='yours' WHERE state='print'\").rowcount if has else 0
k=c.execute(\"UPDATE stock_voucher_scanask SET state='closed', closed_at=?, closed_how='undo' WHERE state IN ('card','printed')\", (ts,)).rowcount if c.execute(\"SELECT 1 FROM sqlite_master WHERE name='stock_voucher_scanask'\").fetchone() else 0
c.commit(); print('S973 cards withdrawn:', n, '- claims back to his call:', m, '- print asks closed:', k)" "$LIVE_DB" 2>&1 | tail -1)
case "$WD" in "S973 cards withdrawn:"*) echo "   $WD";; *) echo "!! could not withdraw the S973 cards ($WD) - nothing undone. Tell Claude."; exit 1;; esac
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
  if [ "$n" = "$KEEP" ]; then echo "   $n kept at its new version (a stock voucher is never judged as a bill)"; continue; fi
  if [ "$fr" = NEW ]; then if [ -f "$f" ]; then mv -f "$f" "$f.bak_S973_removed_$ST" && echo "   $n moved aside"; else echo "   $n already absent"; fi; continue; fi
  if [ "$(m5 "$f")" = "$fr" ]; then echo "   $n already at ${fr:0:8}"; continue; fi
  \cp -p "$f.bak_S973_${fr:0:8}" "$f" && [ "$(m5 "$f")" = "$fr" ] && echo "   $n back to ${fr:0:8}" || { echo "!! could not put $n back. Tell Claude."; exit 1; }; done
"$SYSTEMCTL" restart "$FSVC"; "$SYSTEMCTL" restart "$ASVC"
h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done
a=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; a=$(ahz); [ "$a" = 200 ] && break; done
echo "   $FSVC + $ASVC restarted, finance healthz $h, scan app healthz $a"
echo "S973 UNDONE."
