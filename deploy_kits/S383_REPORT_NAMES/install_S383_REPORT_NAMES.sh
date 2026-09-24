#!/bin/bash
# =============================================================================
#  install_S383_REPORT_NAMES.sh · kit S383_REPORT_NAMES (session 279, 24-Sep-2026) -- step 3 of the owner's plan
#
#  (1) the name on a lab report (the lab's e-mail subject, carried in the filed report's name) is checked against the
#      clinic ID's name; one that is nothing alike becomes a reception line on Report baaki: "Wahi mareez" / "ID galat"
#      (spelling, titles and short forms are forgiven -- Hindi names written by two desks);
#  (2) the doctors' counts carry it; the Clinic Gist tile line and the Gist page gain the reports line -- read in the
#      browser, hidden when unreadable, never shown as zero.
#  FILES:  /root/finance/slip_log.py  S382 3e6cb9b0 -> 30d799e1   ·   /root/portal/portal.py  S382 f9c7e306 -> 80d6dc44
#  Restarts clinic-finance and clinic-portal.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S383_REPORT_NAMES/install_S383_REPORT_NAMES.sh
# =============================================================================
set -u
KIT="S383_REPORT_NAMES"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"; PD="${PD:-/root/portal}"; DBF="${FINANCE_DB:-$FIN/finance.db}"
FPORT="${FIN_PORT:-8106}"; PPORT="${PORTAL_PORT:-8099}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s383_walk_$STAMP"
S_FROM=3e6cb9b04b283fda89e67aebb958eb42; S_TO=30d799e1080db7c50aa95257a869998c
P_FROM=f9c7e306a1c49f606c30e9292cc8cbc9; P_TO=80d6dc44acc07ebb0b974fb792507fee
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 slip_log.py)" = "$S_TO" ] && [ "$(m5 portal.py)" = "$P_TO" ] || { say "!! [1/7] kit files not at their pins - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/slip_log.py")" = "$S_TO" ] && [ "$(m5 "$PD/portal.py")" = "$P_TO" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
[ "$(m5 "$FIN/slip_log.py")" = "$S_FROM" ] || { say "!! [2/7] slip_log.py is $(m5 "$FIN/slip_log.py"), not S382 - nothing installed"; exit 1; }
[ "$(m5 "$PD/portal.py")" = "$P_FROM" ] || { say "!! [2/7] portal.py is $(m5 "$PD/portal.py"), not S382 - nothing installed"; exit 1; }
say "[2/7] live pins exact (slip_log S382 · portal S382)"
mkdir -p "$WALK/fin" "$WALK/portal" || exit 1
\cp -p slip_log.py "$WALK/fin/" && \cp -p "$PD"/*.py "$WALK/portal/" 2>/dev/null; \cp -p "$PD"/*.js "$WALK/portal/" 2>/dev/null; \cp -p portal.py "$WALK/portal/portal.py" || exit 1
"$VPY" -B -m py_compile "$WALK/fin/slip_log.py" "$WALK/portal/portal.py" walk_s383.py check_portal_s383.py || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] py_compile green"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/scratch.db" \
  || { say "!! [4/7] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && FINANCE_DB="$WALK/scratch.db" timeout 180 "$VPY" -B "$KDIR/walk_s383.py" "$WALK/fin" "$FIN/slip_log.py" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/7] $WOUT (scratch copy of the live database; the live slip_log.py is the negative control)"
POUT="$( cd /tmp && timeout 60 "$VPY" -B "$KDIR/check_portal_s383.py" "$WALK/portal" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$POUT" | grep -q "^PORTAL_S383 OK" || { say "!! [5/7] portal check red: $POUT - nothing installed"; exit 1; }
say "[5/7] $POUT"
BS="$FIN/slip_log.py.bak_S383_3e6cb9b0"; BP="$PD/portal.py.bak_S383_f9c7e306"
\cp -p "$FIN/slip_log.py" "$BS" && \cp -p "$PD/portal.py" "$BP" || { say "!! [6/7] backups failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BS" "$FIN/slip_log.py"; \cp -p "$BP" "$PD/portal.py"
  systemctl restart clinic-finance || true; systemctl restart clinic-portal || true; sleep 5
  say "   slip_log $(m5 "$FIN/slip_log.py") · portal $(m5 "$PD/portal.py") · finance $(code "http://127.0.0.1:$FPORT/finance/healthz")"; exit 1
}
\cp -p slip_log.py "$FIN/slip_log.py" && [ "$(m5 "$FIN/slip_log.py")" = "$S_TO" ] || restore
systemctl restart clinic-finance || restore; sleep 5; systemctl is-active --quiet clinic-finance || restore
H=$(code "http://127.0.0.1:$FPORT/finance/healthz"); PC=$(code "http://127.0.0.1:$FPORT/finance/slips/api/pending-counts")
[ "$H" = 200 ] && { [ "$PC" = 302 ] || [ "$PC" = 401 ] || [ "$PC" = 403 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "Traceback\|NOT mounted" && restore
\cp -p portal.py "$PD/portal.py" && [ "$(m5 "$PD/portal.py")" = "$P_TO" ] || restore
systemctl restart clinic-portal || restore; sleep 4; systemctl is-active --quiet clinic-portal || restore
PH=$(curl -s -m 8 "http://127.0.0.1:$PPORT/portal/health"); echo "$PH" | grep -q '"status": *"ok"' || restore
say "[6/7] placed; finance healthz $H · counts door without login $PC (locked) · portal healthy · backups beside each file"
md5sum "$FIN/slip_log.py" "$PD/portal.py"
say "[7/7] $KIT: DONE -- read next: https://followup.dr-manoj.in/portal/gist"
