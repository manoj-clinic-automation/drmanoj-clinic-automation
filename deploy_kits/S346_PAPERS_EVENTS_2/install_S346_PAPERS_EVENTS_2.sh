#!/bin/bash
# =============================================================================
#  install_S346_PAPERS_EVENTS_2.sh · kit S346_PAPERS_EVENTS_2 (session 273, 20-Sep-2026)
#  S346 = S345's payload, byte-identical, with the walk corrected: S345 was REFUSED at its own walk on the box
#  (nothing installed) -- the live queue already held a real WhatsApp photo and the walk counted exactly two.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S346_PAPERS_EVENTS_2/install_S346_PAPERS_EVENTS_2.sh
#
#  THE OWNER (S271_BUILD_BRIEF §2.3/§2.7, step 5): outside MRI/CT reports and discharge papers, photographed or
#  scanned by staff with the clinic ID picked (Check karein -> Kagaz jodein) or added by the doctor on the patient
#  page; and "Add event" for hospital admissions and surgeries (date, hospital, what was done, note, the paper).
#  A file waits on the box (0700 /root/finance/records_inbox) only until the mailbox script carries it to Drive.
#
#  FILES:  /root/finance/records.py   S344 04af860f -> (TO below)
#          /root/finance/finance_app.py must be 7866b1ee (S342) -- checked, not changed
#  DATA:   tables record_upload, record_event, created on first use.
#  DOORS:  GET /api/upload-pending, GET /api/upload-file/<id>, POST /api/upload-done (X-Finance-Cron).
# =============================================================================
set -u
KIT="S346_PAPERS_EVENTS_2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s346_walk_$STAMP"
FA=7866b1ee6e70d19b5c096ef1b0099bd3
RC_FROM=04af860fc146d47e49344c67e025cf8c
RC_TO=8cdd334f2f1329899afd8fc09df145fd
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 records.py)" = "$RC_TO" ] || { say "!! [1/7] kit records.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
[ "$(m5 "$FIN/records.py")" = "$RC_TO" ] && { say "-- ALREADY INSTALLED (records.py $RC_TO). Nothing to do."; exit 0; }
[ "$(m5 "$FIN/records.py")" = "$RC_FROM" ] || { say "!! [2/7] records.py is $(m5 "$FIN/records.py"), not S344 - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_app.py")" = "$FA" ] || { say "!! [2/7] finance_app.py is not the S342 pin - nothing installed"; exit 1; }
say "[2/7] live pins exact"
"$SPY" -m py_compile records.py walk_s346.py || { say "!! [3/7] compile failed - nothing installed"; exit 1; }
say "[3/7] py_compile green"
mkdir -p "$WALK/app" "$WALK/stub" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
[ -d "$FIN/finance_ui" ] && cp -rp "$FIN/finance_ui" "$WALK/app/"
cp -p records.py "$WALK/app/records.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/7] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 RECORDS_DRIVE_STUB="$WALK/stub" \
         FINANCE_SSO_DIR="$POR" PETTY_UPLOAD_DIR="$WALK/uploads" timeout 170 "$VPY" -B "$KDIR/walk_s346.py" "$WALK/app" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/7] $WOUT"
BAK="$FIN/records.py.bak_S346_04af860f"
\cp -p "$FIN/records.py" "$BAK" || { say "!! [5/7] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$FIN/records.py"; systemctl restart clinic-finance || true; sleep 3
  say "   $FIN/records.py $(m5 "$FIN/records.py")"; exit 1
}
\cp -p records.py "$FIN/records.py" && [ "$(m5 "$FIN/records.py")" = "$RC_TO" ] || restore
say "[5/7] placed; backup $BAK"
systemctl restart clinic-finance || restore
sleep 4
systemctl is-active --quiet clinic-finance || restore
say "[6/7] clinic-finance active"
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/checks)
say "health : finance $c2 · /finance/checks without a login $c4 (302 expected)"
[ "$c2" = 200 ] && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore
say "[7/7] all green"
md5sum "$FIN/finance_app.py" "$FIN/records.py"
say "$KIT: DONE"
