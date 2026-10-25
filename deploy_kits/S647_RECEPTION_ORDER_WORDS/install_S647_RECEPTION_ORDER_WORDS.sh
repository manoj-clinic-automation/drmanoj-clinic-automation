#!/bin/bash
# =============================================================================
#  install_S647_RECEPTION_ORDER_WORDS.sh · kit S647 (25-Oct-2026, session S349, the parent) · the owner's wording
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s647kit && cp -rp /root/deploy/repo/deploy_kits/S647_RECEPTION_ORDER_WORDS /tmp/s647kit && bash /tmp/s647kit/install_S647_RECEPTION_ORDER_WORDS.sh
#  (DRY=1 before bash: every gate and both walks, nothing written.)
#
#  /root/finance/aaj_seed.py  2df0d3a9 -> 98f63364  1 counted edit: reception.order_arrival's words -- 'Order ka maal nahi aaya -- supplier ko call kijiye'
#  No data step. Restarts clinic-finance. Red after placing: the old file back byte-identically, restart.
#  Undo:  \cp -p /root/finance/aaj_seed.py.bak_S647 /root/finance/aaj_seed.py; systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S647_RECEPTION_ORDER_WORDS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
MAPF="${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"; export DUTY_MAP_JSON="$MAPF"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N=aaj_seed.py; FROM=2df0d3a91bfc9c024763b9a837dab904; TO=98f633640ada6e809ce60fa1f0b826a7; MAPMD5=78b5f07ef7cdd48b1a76d78db52107fc
HAVE_LOCK=0; SN=""; SO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$SN" ] && rm -rf "$SN" "$SO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
[ "$(m5 "$KDIR/$N")" = "$TO" ] || stop "the kit's $N is not the built file"
[ "$(m5 "$FIN/$N")" = "$TO" ] && { echo "ALREADY INSTALLED."; exit 0; }
L=$(m5 "$FIN/$N"); [ "$L" = "$FROM" ] || stop "the live $FIN/$N changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
[ "$(m5 "$MAPF")" = "$MAPMD5" ] || stop "the duty map $MAPF is not v20 (78b5f07e) -- it moved since this kit was built"
echo "2. the live $N and the duty map are the ones this kit was built from"
DB=$("$SYSTEMCTL" show -p Environment "$SVC" 2>/dev/null | sed 's/^Environment=//' | tr ' ' '\n' | sed -n 's/^FINANCE_DB=//p' | head -1); [ -n "$DB" ] || DB="$FIN/finance.db"
[ -f "$DB" ] || stop "the finance database was not found ($DB)"
SN=$(mktemp -d /tmp/s647new.XXXX); SO=$(mktemp -d /tmp/s647old.XXXX)
\cp "$KDIR/$N" "$SN/$N"; \cp "$FIN/$N" "$SO/$N"
"$PY" -B -m py_compile "$SN/$N" || stop "$N does not compile with $PY"
R=$("$PY" -B walk_s647.py "$SN" "$FIN" --db "$DB" 2>&1 | tail -1); case "$R" in "4 of 4 green") echo "3. walk on the live books: $R";; *) "$PY" -B walk_s647.py "$SN" "$FIN" --db "$DB" 2>&1 | grep -E 'RED|Error'; stop "the walk is not green ($R)";; esac
R=$("$PY" -B walk_s647.py "$SO" "$FIN" --db "$DB" --old 2>&1 | tail -1)
[ "$R" = "2 S647 check(s) red · 0 older red · 2 green" ] || { echo "$R"; stop "the control on the live file is not as expected ($R)"; }
echo "   control on the live file: $R"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
\cp -p "$FIN/$N" "$FIN/$N.bak_S647" || stop "could not keep a backup of $N"
\cp "$KDIR/$N" "$FIN/$N" && chmod --reference="$FIN/$N.bak_S647" "$FIN/$N" 2>/dev/null
[ "$(m5 "$FIN/$N")" = "$TO" ] || { \cp -p "$FIN/$N.bak_S647" "$FIN/$N"; stop "read-back of $N did not match; the old file is back"; }
echo "4. placed $N (backup $N.bak_S647)"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
R=$("$PY" -B walk_s647.py "$FIN" "$FIN" --db "$DB" 2>&1 | tail -1)
if [ "$h" != 200 ] || [ "$R" != "4 of 4 green" ]; then
  echo "!! RED after placing (finance $h; walk on the placed file: $R) - putting the old file back"
  \cp -p "$FIN/$N.bak_S647" "$FIN/$N"; "$SYSTEMCTL" restart "$SVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  [ "$(m5 "$FIN/$N")" = "$FROM" ] && echo "   the old $N is back (${FROM:0:8})" || echo "   !! the restored $N is NOT ${FROM:0:8} -- copy $FIN/$N.bak_S647 back by hand"
  echo "   after the restore: finance $h2. Send a photo of this screen to Claude."; exit 1
fi
echo "5. $SVC restarted and healthy; the walk on the placed file: $R"
echo ""
echo "INSTALLED. Reception's late-order line now reads: Order ka maal nahi aaya -- supplier ko call kijiye."
