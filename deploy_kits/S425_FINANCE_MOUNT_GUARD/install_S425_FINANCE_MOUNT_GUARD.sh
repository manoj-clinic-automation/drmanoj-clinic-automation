#!/bin/bash
# install_S425_FINANCE_MOUNT_GUARD.sh -- session 284, 27-Sep-2026 -- the hazard found when finance_app.py was read
# whole: the eleven oldest module mounts (S208 ... S241) were bare imports, so one broken part took the WHOLE finance
# app down at start. Each is now guarded as every later mount already is (S209), a failure is recorded, and ONE
# health-page row ('Parts of the finance app that did not load') names any part that did not load.
# FROM 7486f3e6 (S422, live) -> TO ac24fc5e, exact bytes only. Proven on scratch copies first; RED after placing = restore.
set -u
KIT="S425_FINANCE_MOUNT_GUARD"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FD="${FD:-/root/finance}"
APP="$FD/finance_app.py"; FROM=7486f3e652bdf777666af134da5b0054; TO=ac24fc5e4e312b0bf3718b42380d5e64
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/6] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
say "      green"
say "[2/6] the live file"
A0="$(m5 "$APP")"
[ "$A0" = "$TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
[ "$A0" = "$FROM" ] || { say "!! [2/6] live finance_app.py is $A0, not the S422 bytes $FROM - it has moved since; nothing installed (the kit is rebuilt from the new bytes)"; exit 1; }
say "      exact (S422)"
say "[3/6] scratch: apply + walk on a copy"
W="/tmp/s425_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W" && \cp -p "$APP" "$W/orig.py" && \cp -p "$APP" "$W/finance_app.py" || { say "!! [3/6] scratch copy failed"; exit 1; }
"$VPY" -B "$KDIR/apply_s425.py" "$W/finance_app.py" >/dev/null || { say "!! [3/6] apply on the copy failed - nothing installed"; rm -rf "$W"; exit 1; }
[ "$(m5 "$W/finance_app.py")" = "$TO" ] || { say "!! [3/6] the copy came out $(m5 "$W/finance_app.py"), not the predicted $TO - nothing installed"; rm -rf "$W"; exit 1; }
/usr/bin/python3 -B -m py_compile "$W/finance_app.py" || { say "!! [3/6] py_compile failed - nothing installed"; rm -rf "$W"; exit 1; }
WOUT="$( cd /tmp && timeout 120 /usr/bin/python3 -B "$KDIR/walk_s425.py" "$W/orig.py" "$W/finance_app.py" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT · the copy = the predicted $TO"
say "[4/6] backup + apply to the live file"
B1="$APP.bak_S425_${A0:0:8}"
\cp -p "$APP" "$B1" || { say "!! [4/6] backup failed"; exit 1; }
restore() { say "!! RED after placing ($1) - restoring"; \cp -p "$B1" "$APP"; systemctl restart clinic-finance || true; sleep 5; say "   finance_app.py $(m5 "$APP") (was $A0)"; exit 1; }
"$VPY" -B "$KDIR/apply_s425.py" "$APP" | sed 's/^/      /'
[ "$(m5 "$APP")" = "$TO" ] || restore "placed bytes $(m5 "$APP")"
/usr/bin/python3 -B -m py_compile "$APP" || restore "py_compile (the service runs /usr/bin/python3)"
say "[5/6] restart clinic-finance, then the probes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart"; sleep 6; systemctl is-active --quiet clinic-finance || restore "not active"
FP="$(grep -o '127.0.0.1:[0-9]*' /etc/systemd/system/clinic-finance.service | head -1 | cut -d: -f2)"; FP="${FP:-8106}"
HZ="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:$FP/finance/healthz)"
HP="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:$FP/finance/health)"
say "      healthz $HZ (200 expected) · health page without login $HP (302 expected, F-621)"
[ "$HZ" = 200 ] || restore "healthz"; { [ "$HP" = 302 ] || [ "$HP" = 401 ]; } || restore "health page gate"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u clinic-finance --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "journal: $JR error line(s)"; }
say "      journal since restart: clean"
say "[6/6] parts that did not load at this start (information: the app is up either way)"
NM="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -o '[a-z_+]* NOT mounted[^\"]*' | sort -u)"
if [ -z "$NM" ]; then say "      none - all 25 parts loaded"; else echo "$NM" | sed 's/^/      /'; fi
say "      all green -- $KIT: DONE"
say "      backup: $B1"
md5sum "$APP"
