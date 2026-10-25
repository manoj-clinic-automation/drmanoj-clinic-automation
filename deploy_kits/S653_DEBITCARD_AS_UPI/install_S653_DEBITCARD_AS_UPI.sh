#!/bin/bash
# =============================================================================
#  install_S653_DEBITCARD_AS_UPI.sh . kit S653 (25-Oct-2026, session S354, the parent) . D788 / F-1022
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s653kit && cp -rp /root/deploy/repo/deploy_kits/S653_DEBITCARD_AS_UPI /tmp/s653kit && bash /tmp/s653kit/install_S653_DEBITCARD_AS_UPI.sh
#  (DRY=1 before bash: every gate and both walks, nothing written.)
#
#  /root/finance/day_check.py  da63a580 -> c23e3f2f  3 counted edits: a Docterz Debit Card the bank shows as UPI is UPI
#  No data step. Restarts clinic-finance. Red after placing: the old file back byte-identically, restart.
#  Undo:  \cp -p /root/finance/day_check.py.bak_S653 /root/finance/day_check.py; systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S653_DEBITCARD_AS_UPI"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N=day_check.py; FROM=da63a5806f0264188a7872ed4b786d99; TO=c23e3f2f318fafa58582a9d3b19c91db
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
echo "2. the live $N is the one this kit was built from"
DB=$("$SYSTEMCTL" show -p Environment "$SVC" 2>/dev/null | sed 's/^Environment=//' | tr ' ' '\n' | sed -n 's/^FINANCE_DB=//p' | head -1); [ -n "$DB" ] || DB="$FIN/finance.db"
[ -f "$DB" ] || stop "the finance database was not found ($DB)"
SN=$(mktemp -d /tmp/s653new.XXXX); SO=$(mktemp -d /tmp/s653old.XXXX)
\cp "$KDIR/$N" "$SN/$N"; \cp "$FIN/$N" "$SO/$N"
"$PY" -B -m py_compile "$SN/$N" || stop "$N does not compile with $PY"
R=$("$PY" -B walk_s653.py "$SN" "$FIN" --db "$DB" --base "$SO" 2>&1 | tail -1)
case "$R" in "4 of 4 green") echo "3. walk on a copy of the live books, every day since 1-Oct: $R";; *) "$PY" -B walk_s653.py "$SN" "$FIN" --db "$DB" --base "$SO" 2>&1 | grep -E 'RED|Error|other'; stop "the walk is not green ($R)";; esac
R=$("$PY" -B walk_s653.py "$SO" "$FIN" --db "$DB" --base "$SO" --old 2>&1 | tail -1)
[ "$R" = "2 S653 check(s) red · 0 older red · 2 green" ] || { echo "$R"; stop "the control on the live file is not as expected ($R)"; }
echo "   control on the live file: $R"
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
\cp -p "$FIN/$N" "$FIN/$N.bak_S653" || stop "could not keep a backup of $N"
\cp "$KDIR/$N" "$FIN/$N" && chmod --reference="$FIN/$N.bak_S653" "$FIN/$N" 2>/dev/null
[ "$(m5 "$FIN/$N")" = "$TO" ] || { \cp -p "$FIN/$N.bak_S653" "$FIN/$N"; stop "read-back of $N did not match; the old file is back"; }
echo "4. placed $N (backup $N.bak_S653)"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
R=$("$PY" -B walk_s653.py "$FIN" "$FIN" --db "$DB" --base "$SO" 2>&1 | tail -1)
if [ "$h" != 200 ] || [ "$R" != "4 of 4 green" ]; then
  echo "!! RED after placing (finance $h; walk on the placed file: $R) - putting the old file back"
  \cp -p "$FIN/$N.bak_S653" "$FIN/$N"; "$SYSTEMCTL" restart "$SVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  [ "$(m5 "$FIN/$N")" = "$FROM" ] && echo "   the old $N is back (${FROM:0:8})" || echo "   !! the restored $N is NOT ${FROM:0:8} -- copy $FIN/$N.bak_S653 back by hand"
  echo "   after the restore: finance $h2. Send a photo of this screen to Claude."; exit 1
fi
echo "5. $SVC restarted and healthy; the walk on the placed file: $R"
echo ""
echo "INSTALLED. A Docterz Debit Card the bank shows as UPI is now UPI on the day's corrections -- no change asked of reception."
