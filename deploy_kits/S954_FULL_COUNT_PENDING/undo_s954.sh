#!/bin/bash
# undo_s954.sh · kit S954_FULL_COUNT_PENDING: the judgments it re-made put back (from its own moment), record_judges.py back to S952's
# 06d317a5 (only when still at the kit's TO), clinic-finance restarted. S952 stays.
#    bash /root/deploy/repo/deploy_kits/S954_FULL_COUNT_PENDING/undo_s954.sh
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; FIN_PORT="${FIN_PORT:-8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
mkdir "$LOCK" 2>/dev/null || { echo "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
echo "S954 undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; trap 'rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null' EXIT
F="$ROOT/finance/record_judges.py"; FROM="06d317a5e4b6b0c0d58ece78b3940846"; TO="$(awk '$2=="finance/record_judges.py"{print $1}' "$KDIR/TO_PINS.md5")"
ATF="$ROOT/finance/.s954_rejudged_at"; B="$F.bak_S954_${FROM:0:8}"; c="$(m5 "$F")"
if [ "$c" = "$FROM" ]; then echo "   finance/record_judges.py already at ${FROM:0:8}"; echo "S954 undo: done."; exit 0; fi
[ "$c" = "$TO" ] || { echo "!! finance/record_judges.py is ${c:0:8} -- neither the kit's TO nor its FROM; left as it is. Tell Claude."; exit 1; }
if [ -s "$ATF" ]; then
  U=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" timeout 900 "$VPY" -W ignore -B "$F" --undo-rejudge-from "$(cat "$ATF")" 2>&1 | tail -1)
  case "$U" in "S954 undo: "*) echo "   the judgments: $U";; *) echo "!! the judgments could not be put back ($U) -- the file is left at the new version. Tell Claude."; exit 1;; esac
fi
[ "$(m5 "$B")" = "$FROM" ] || { echo "!! the backup $B is missing or changed; left as it is. Tell Claude."; exit 1; }
\cp -p "$B" "$F" && [ "$(m5 "$F")" = "$FROM" ] && echo "   finance/record_judges.py back to ${FROM:0:8}" || { echo "!! could not put it back"; exit 1; }
rm -f "$ATF"; "$SYSTEMCTL" restart "$FSVC"; h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "   $FSVC restarted, finance healthz $h"
echo "S954 undo: done."
