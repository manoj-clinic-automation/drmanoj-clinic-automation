#!/bin/bash
# =============================================================================
#  install_S350_FRESHNESS_CLOCK.sh · kit S350_FRESHNESS_CLOCK (session 276 parent, 20-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S350_FRESHNESS_CLOCK/install_S350_FRESHNESS_CLOCK.sh
#
#  ONE FILE, FULL REPLACEMENT: /root/finance/freshness_page.py dc60a4c6 (S349) -> the kit's bytes.
#  The S349 page read live said "0 min ago" for a file four hours old: its banner took the clock
#  from datetime.utcnow().timestamp(), which on this box's IST clock is 5.5 h behind the epoch.
#  Now time.time(). finance_app.py is NOT touched. clinic-finance is restarted.
#  Gates: SUMS + KIT_ID -> the walk with the service's python (14 checks, incl. one on the REAL
#  clock under TZ=Asia/Kolkata and a negative control against the S349 bytes) -> the live file must
#  be S349's (dc60a4c6) or already this kit's -> place -> py_compile -> restart -> healthz 200 ·
#  /finance/freshness 302/401/403/200 -> read back. Any red puts the S349 file back and restarts.
# =============================================================================
set -u
KIT="S350_FRESHNESS_CLOCK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
MODULE="$FIN/freshness_page.py"
FROM="dc60a4c6fc0033bda1cc9548db1efa5d"
SVC="${SVC:-clinic-finance}"
PORT="${PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s350_$STAMP"
say() { echo "$@"; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$SPY" ] || { say "!! preflight: $SPY not executable - nothing changed"; exit 1; }
[ -f "$MODULE" ] || { say "!! preflight: $MODULE is not there - S349 is not installed, nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing changed"; exit 1; }
NEW="$(m5 "$KDIR/freshness_page.py")"; LIVE="$(m5 "$MODULE")"
if [ "$LIVE" = "$NEW" ]; then say "[1/5] kit gates green; $MODULE ALREADY carries this kit ($NEW)"; ALREADY=1
elif [ "$LIVE" = "$FROM" ]; then say "[1/5] kit gates green; live module is S349's ($FROM)"; ALREADY=0
else say "!! [1/5] $MODULE is neither S349's nor this kit's ($LIVE) - nothing changed"; exit 1; fi

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
WOUT="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/walk_s350.py" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$WOUT" in
  *"WALK OK"*) say "[2/5] $(echo "$WOUT" | grep -o 'WALK OK -- [0-9]* checks') with the service's python" ;;
  *) say "!! [2/5] the walk is red:"; say "    $WOUT"; rm -rf "$T"; exit 1 ;;
esac

BAK="$MODULE.bak_S350_$STAMP"
restore() { say "!! putting the S349 module back"; \cp -p "$BAK" "$MODULE"; systemctl restart "$SVC" >/dev/null 2>&1 || true; sleep 4;
            say "!! restored: freshness_page $(m5 "$MODULE") · $SVC $(systemctl is-active "$SVC")"; rm -rf "$T"; exit 1; }
if [ "$ALREADY" = "1" ]; then
  say "[3/5] nothing to place"
else
  \cp -p "$MODULE" "$BAK"
  \cp "$KDIR/freshness_page.py" "$MODULE" && chmod 644 "$MODULE"
  say "[3/5] placed $MODULE ($(m5 "$MODULE")); backup $BAK"
fi
"$SPY" -m py_compile "$MODULE" || restore
say "[4/5] py_compile green"
systemctl restart "$SVC" || restore
sleep 4
systemctl is-active --quiet "$SVC" || restore
C1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz")
C3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/freshness")
say "[5/5] $SVC restarted · healthz $C1 · /finance/freshness $C3 (302/401/403 = the login gate, expected)"
[ "$C1" = "200" ] || restore
case "$C3" in 200|302|401|403) : ;; *) say "!! /finance/freshness answered $C3"; restore ;; esac
rm -rf "$T"
say "freshness_page.py now $(m5 "$MODULE")"
say "$KIT: DONE -- the banner's age is the wall clock's now; open the page once and the line should read the real age."
