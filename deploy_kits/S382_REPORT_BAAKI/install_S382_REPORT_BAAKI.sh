#!/bin/bash
# =============================================================================
#  install_S382_REPORT_BAAKI.sh · kit S382_REPORT_BAAKI (session 279, 24-Sep-2026)
#
#  THE OWNER, 24-Sep-2026 (GO on the plan): a list of the blood reports the lab has not mailed -- date, clinic ID,
#  name, all three compulsory -- for Sukhveer at the pathology desk (with his attendance), both receptionists and
#  Shavez; the same flow for the X-ray photos (Shavez does Awdhesh's part); one tap when mailed; mismatches flagged.
#  His rulings: late at the end of the same day (next morning for a test after 5 pm); '+ Naya' walk-ins are
#  reception's; Sukhveer is already on the staff list.
#
#  FILES:  /root/finance/slip_log.py   S379 f1de035f -> 3e6cb9b0  (block appended + one Parchi menu line)
#          /root/portal/portal.py      S370 5876225d -> f9c7e306  (one tile 'Report baaki')
#  DATA:   /root/portal/tile_grants.json  'Report baaki' granted by name to sukhveer, alisha, shivani, shavez (+1 version)
#          finance.db unit_role ('slips','sukhveer','viewer') -- he sees the blood list and taps; nothing else of the tile
#          finance.db blood_order + mailed_by/mailed_at/later_until/name_by, NEW table pend_mark (added on first use)
#  Restarts clinic-finance and clinic-portal.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S382_REPORT_BAAKI/install_S382_REPORT_BAAKI.sh
# =============================================================================
set -u
KIT="S382_REPORT_BAAKI"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"; PD="${PD:-/root/portal}"; DBF="${FINANCE_DB:-$FIN/finance.db}"
FPORT="${FIN_PORT:-8106}"; PPORT="${PORTAL_PORT:-8099}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s382_walk_$STAMP"
S_FROM=f1de035fa4dfbfa8a69511f3a14e8083; S_TO=3e6cb9b04b283fda89e67aebb958eb42
P_FROM=5876225db99894d74270be1829761661; P_TO=f9c7e306a1c49f606c30e9292cc8cbc9
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 slip_log.py)" = "$S_TO" ] && [ "$(m5 portal.py)" = "$P_TO" ] || { say "!! [1/8] kit files not at their pins - nothing installed"; exit 1; }
say "[1/8] kit gates green"
if [ "$(m5 "$FIN/slip_log.py")" = "$S_TO" ] && [ "$(m5 "$PD/portal.py")" = "$P_TO" ]; then
  say "-- code ALREADY INSTALLED; grants and role:"; "$SPY" -B grants_s382.py "$PD/tile_grants.json"
  "$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"INSERT OR IGNORE INTO unit_role(unit,username,role,active,note) VALUES ('slips','sukhveer','viewer',1,'S382 Report baaki')\"); c.commit(); print('   sukhveer in slips:', [r[0] for r in c.execute(\"SELECT role FROM unit_role WHERE unit='slips' AND username='sukhveer' AND active=1\")])" "$DBF"
  exit 0; fi
[ "$(m5 "$FIN/slip_log.py")" = "$S_FROM" ] || { say "!! [2/8] slip_log.py is $(m5 "$FIN/slip_log.py"), not S379 - nothing installed"; exit 1; }
[ "$(m5 "$PD/portal.py")" = "$P_FROM" ] || { say "!! [2/8] portal.py is $(m5 "$PD/portal.py"), not S370 - nothing installed"; exit 1; }
[ -f "$PD/tile_grants.json" ] || { say "!! [2/8] no $PD/tile_grants.json - nothing installed"; exit 1; }
say "[2/8] live pins exact (slip_log S379 · portal S370) · grants file present ($(m5 "$PD/tile_grants.json"))"
mkdir -p "$WALK/fin" "$WALK/portal" || exit 1
\cp -p slip_log.py "$WALK/fin/" && \cp -p "$PD"/*.py "$WALK/portal/" 2>/dev/null; \cp -p "$PD"/*.js "$WALK/portal/" 2>/dev/null; \cp -p portal.py "$WALK/portal/portal.py" || exit 1
"$VPY" -B -m py_compile "$WALK/fin/slip_log.py" "$WALK/portal/portal.py" walk_s382.py grants_s382.py check_portal_s382.py || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/scratch.db" \
  || { say "!! [4/8] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && FINANCE_DB="$WALK/scratch.db" timeout 180 "$VPY" -B "$KDIR/walk_s382.py" "$WALK/fin" "$FIN/slip_log.py" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/8] walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] $WOUT (scratch copy of the live database; the live slip_log.py is the negative control)"
"$SPY" -B grants_s382.py "$PD/tile_grants.json" --out "$WALK/tile_grants.json" >/dev/null || { say "!! [5/8] the grants edit failed - nothing installed"; rm -rf "$WALK"; exit 1; }
POUT="$( cd /tmp && TILE_GRANTS_FILE="$WALK/tile_grants.json" timeout 60 "$VPY" -B "$KDIR/check_portal_s382.py" "$WALK/portal" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$POUT" | grep -q "^PORTAL_S382 OK" || { say "!! [5/8] portal check red: $POUT - nothing installed"; exit 1; }
say "[5/8] $POUT"
BS="$FIN/slip_log.py.bak_S382_f1de035f"; BP="$PD/portal.py.bak_S382_5876225d"; BG="$PD/tile_grants.json.bak_S382_$STAMP"
\cp -p "$FIN/slip_log.py" "$BS" && \cp -p "$PD/portal.py" "$BP" && \cp -p "$PD/tile_grants.json" "$BG" || { say "!! [6/8] backups failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BS" "$FIN/slip_log.py"; \cp -p "$BP" "$PD/portal.py"; \cp -p "$BG" "$PD/tile_grants.json"
  systemctl restart clinic-finance || true; systemctl restart clinic-portal || true; sleep 5
  say "   slip_log $(m5 "$FIN/slip_log.py") · portal $(m5 "$PD/portal.py") · finance $(code "http://127.0.0.1:$FPORT/finance/healthz")"; exit 1
}
\cp -p slip_log.py "$FIN/slip_log.py" && [ "$(m5 "$FIN/slip_log.py")" = "$S_TO" ] || restore
systemctl restart clinic-finance || restore; sleep 5; systemctl is-active --quiet clinic-finance || restore
H=$(code "http://127.0.0.1:$FPORT/finance/healthz"); PG=$(code "http://127.0.0.1:$FPORT/finance/slips/pending")
say "[6/8] slip_log placed; clinic-finance: healthz $H · /finance/slips/pending without login $PG (302 expected)"
[ "$H" = 200 ] && { [ "$PG" = 302 ] || [ "$PG" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "Traceback\|NOT mounted" && restore
\cp -p portal.py "$PD/portal.py" && [ "$(m5 "$PD/portal.py")" = "$P_TO" ] || restore
"$SPY" -B grants_s382.py "$PD/tile_grants.json" | sed 's/^/   /'
systemctl restart clinic-portal || restore; sleep 4; systemctl is-active --quiet clinic-portal || restore
PH=$(curl -s -m 8 "http://127.0.0.1:$PPORT/portal/health")
echo "$PH" | grep -q '"status": *"ok"' || restore
say "[7/8] portal placed; clinic-portal healthy; grants file $(m5 "$PD/tile_grants.json")"
"$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"INSERT OR IGNORE INTO unit_role(unit,username,role,active,note) VALUES ('slips','sukhveer','viewer',1,'S382 Report baaki')\"); c.commit(); print('   sukhveer in slips:', [r[0] for r in c.execute(\"SELECT role FROM unit_role WHERE unit='slips' AND username='sukhveer' AND active=1\")])" "$DBF" \
  || { say "!! [8/8] the role row was not written - the tile is live for reception; tell the assistant"; exit 1; }
say "[8/8] Sukhveer can open the blood list"
md5sum "$FIN/slip_log.py" "$PD/portal.py" "$PD/tile_grants.json"
say "$KIT: DONE -- read next: https://followup.dr-manoj.in/finance/slips/pending"
