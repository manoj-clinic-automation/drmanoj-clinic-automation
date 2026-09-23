#!/bin/bash
# =============================================================================
#  install_S373_XRAY_LIVE.sh · kit S373_XRAY_LIVE (session 279, 23-Sep-2026) -- the X-ray LIVE filing
#
#  THE OWNER, 23-Sep-2026: "The X-ray upload test period is over. Now incorporate it into the system."
#
#  THE CHANGE (records.py only; finance_app.py is not touched):
#    /finance/records/api/xray-plan  (GET, cron token)  -- what the mailbox script must do with each picture in
#                                     "X-ray inbox" and "X-ray test": file (copy into X-ray/Mon YYYY/DD-Mon under the
#                                     day + clinic ID + study name), check (to "X-ray check"), or dup
#    /finance/records/api/xray-done  (POST, cron token) -- the mailbox reports; each filed copy joins the patient
#    Check karein: a picture in "X-ray check" (staff type the clinic ID, the next run files it); an X-ray slip or
#                  Docterz X-ray line from 23-Sep with no picture by the next day
#    Patient page: "X-rays taken" -- the patient's pictures side by side
#  The Drive side (copy, move to _filed, never delete) is the mailbox script's -- VPS_Lab_Files.gs _fileXray(),
#  placed by the assistant after this is live (D574, D577, D583).
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S373_XRAY_LIVE/install_S373_XRAY_LIVE.sh
#
#  FILES:  /root/finance/records.py   S353 07ec9b41 -> 6492135c (full file; how it was made: make_s373.py + xray_live_block.py)
#  WALK:   walk_s373.py on a scratch copy of finance.db, its own day 2001-01-01 and IDs only (F-581), stub Drive
#          folders; the LIVE records.py (S353) is the negative control (no xray-plan door; +2 routes, none lost).
#  LIVE SHAPE: after the restart the plan is asked once with the service's own token against the real Drive
#          folders -- counts printed, no name, no token. Nothing is moved by that; only the mailbox moves files.
# =============================================================================
set -u
KIT="S373_XRAY_LIVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DBF="${FINANCE_DB:-$FIN/finance.db}"
PORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s373_walk_$STAMP"
RC_FROM=07ec9b41cb5bbded215dcd1b1916e3d0
RC_TO=6492135c9438093a257cf96ef91a9b32
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
probe() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 records.py)" = "$RC_TO" ] || { say "!! [1/7] kit records.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
[ "$(m5 "$FIN/records.py")" = "$RC_TO" ] && { say "-- ALREADY INSTALLED (records.py $RC_TO). Nothing to do."; exit 0; }
[ "$(m5 "$FIN/records.py")" = "$RC_FROM" ] || { say "!! [2/7] records.py is $(m5 "$FIN/records.py"), not S353 - nothing installed"; exit 1; }
say "[2/7] live pin exact (records.py S353)"
mkdir -p "$WALK/app" || exit 1
\cp -p records.py "$WALK/app/records.py"
"$VPY" -B -m py_compile "$WALK/app/records.py" "$KDIR/walk_s373.py" || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] py_compile green"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [4/7] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" timeout 120 "$VPY" -B "$KDIR/walk_s373.py" "$WALK/app" "$FIN/records.py" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/7] $WOUT (scratch copy of the live db; the live records.py is the negative control)"
BAK="$FIN/records.py.bak_S373_07ec9b41"
\cp -p "$FIN/records.py" "$BAK" || { say "!! [5/7] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$FIN/records.py"; systemctl restart clinic-finance || true; sleep 4
  say "   $FIN/records.py $(m5 "$FIN/records.py") · finance $(probe "http://127.0.0.1:$PORT/finance/healthz")"; exit 1
}
\cp -p records.py "$FIN/records.py" && [ "$(m5 "$FIN/records.py")" = "$RC_TO" ] || restore
say "[5/7] placed; backup $BAK"
systemctl restart clinic-finance || restore
sleep 5
systemctl is-active --quiet clinic-finance || restore
H=$(probe "http://127.0.0.1:$PORT/finance/healthz"); PL=$(probe "http://127.0.0.1:$PORT/finance/records/api/xray-plan"); CK=$(probe "http://127.0.0.1:$PORT/finance/checks")
say "[6/7] healthz $H · xray-plan without the token $PL (401 expected) · /finance/checks without login $CK (302/401/403 expected)"
[ "$H" = 200 ] && [ "$PL" = 401 ] && { [ "$CK" = 302 ] || [ "$CK" = 401 ] || [ "$CK" = 403 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "NOT mounted\|Traceback" && restore
TOK="$(systemctl show -p Environment clinic-finance 2>/dev/null | tr ' ' '\n' | sed -n 's/^\(Environment=\)\{0,1\}FINANCE_CRON_TOKEN=//p' | head -1)"
if [ -n "$TOK" ]; then
  LS="$(curl -s -m 60 -w '\n%{http_code}' -H "X-Finance-Cron: $TOK" "http://127.0.0.1:$PORT/finance/records/api/xray-plan")"; TOK=""
  LC="$(echo "$LS" | tail -1)"
  [ "$LC" = 200 ] || { say "!! [7/7] the plan on the real folders answered $LC"; restore; }
  echo "$LS" | sed '$d' | "$SPY" -c "import json,sys,collections; j=json.load(sys.stdin); c=collections.Counter(i.get('action') for i in j.get('items',[])); print('[7/7] LIVE SHAPE: the plan on the real folders -- ok=%s · to file %d · to the check folder %d · duplicates %d · notes %d%s' % (j.get('ok'), c['file'], c['check'], c['dup'], len(j.get('notes',[])), (' ('+'; '.join(j['notes'])+')') if j.get('notes') else ''))" || say "   (plan answer not readable as JSON)"
else
  say "[7/7] LIVE SHAPE skipped: the service carries no cron token in its unit (the mailbox cannot call either -- tell the assistant)"
fi
say "$KIT: DONE -- the assistant now places _fileXray() in the mailbox script. Read later: https://followup.dr-manoj.in/finance/checks"
md5sum "$FIN/records.py"
