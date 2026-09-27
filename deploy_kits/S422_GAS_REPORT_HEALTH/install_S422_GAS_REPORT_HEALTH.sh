#!/bin/bash
# install_S422_GAS_REPORT_HEALTH.sh -- session 284, 27-Sep-2026 -- F-595: the Sunday Apps Script comparison
# gets readers: ONE row on the health page (finance_app.py, one block before the B2 marker, read whole this
# session) and ONE freshness leg on its result file. Proven on scratch copies first; RED after placing = restore.
set -u
KIT="S422_GAS_REPORT_HEALTH"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FD="${FD:-/root/finance}"
CONF=/root/state_backup/clinic_state_backup.conf; APP="$FD/finance_app.py"; LEGS="$FD/freshness_legs.json"
READ_WHOLE=5d9f2703b0142950fa2a0ee56c5938bd    # the finance_app.py bytes read whole at S284 (27-Sep bundle)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/6] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
say "      green"
say "[2/6] the live files"
A0="$(m5 "$APP")"; L0="$(m5 "$LEGS")"
grep -q "S422 (F-595)" "$APP" && grep -q "Apps Script weekly comparison" "$LEGS" && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
if [ "$A0" = "$READ_WHOLE" ]; then say "      finance_app.py $A0 = the bytes read whole this session"
else say "      finance_app.py $A0 -- NOT the bytes read whole ($READ_WHOLE); the Sanjeevni chat has moved it since. The patcher proceeds only if its anchor is exact."; fi
GD="$(grep -m1 '^GAS_DIR=' "$CONF" 2>/dev/null | cut -d= -f2- | tr -d "\"'" )"; GD="${GD:-/root/state_backup/gas}"
say "      the comparison's folder: $GD $( [ -f "$GD/_DRIFT.json" ] && echo "(_DRIFT.json present)" || echo "(no _DRIFT.json yet)")"
say "[3/6] scratch: apply + walk on copies"
W="/tmp/s422_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W" && \cp -p "$APP" "$LEGS" "$W/" || { say "!! [3/6] scratch copy failed"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s422.py" "$KDIR" "$W/finance_app.py" "$W/freshness_legs.json" "$FD" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT"
say "[4/6] backup + apply to the live files"
B1="$APP.bak_S422_${A0:0:8}"; B2="$LEGS.bak_S422_${L0:0:8}"
\cp -p "$APP" "$B1" && \cp -p "$LEGS" "$B2" || { say "!! [4/6] backup failed"; exit 1; }
restore() { say "!! RED after placing ($1) - restoring"; \cp -p "$B1" "$APP"; \cp -p "$B2" "$LEGS"; systemctl restart clinic-finance || true; sleep 4; say "   finance_app.py $(m5 "$APP") (was $A0) · legs $(m5 "$LEGS") (was $L0)"; exit 1; }
"$VPY" -B "$KDIR/apply_s422.py" "$APP" "$LEGS" "$GD" | sed 's/^/      /' || restore "apply"
/usr/bin/python3 -B -m py_compile "$APP" || restore "py_compile (the service runs /usr/bin/python3)"
"$VPY" -B -c "import json;json.load(open('$LEGS'))" || restore "legs json"
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
say "[6/6] what the health page now says (the placed block, run read-only against the real result file)"
"$VPY" -B - "$APP" <<'PY' | sed 's/^/      /'
import datetime as dt, json, os, sys
s = open(sys.argv[1], encoding="utf-8").read()
a = s.index("    # ---- S422 (F-595)"); b = s.index("    # ---- B2: THE NEVER-FIRED WITNESS")
rows = []
ns = {}
exec("def _h(add, os, dt, json):\n" + s[a:b], ns)
ns["_h"](lambda *x, **k: rows.append(x), os, dt, json)
for r in rows: print("row: %s · %s · %s" % (r[1], r[2], r[3]))
PY
"$VPY" -B "$FD/freshness.py" list 2>/dev/null | grep -i "Apps Script weekly" | sed 's/^/      leg: /'
say "      all green -- $KIT: DONE"
say "      backups: $B1 · $B2"
md5sum "$APP" "$LEGS"
