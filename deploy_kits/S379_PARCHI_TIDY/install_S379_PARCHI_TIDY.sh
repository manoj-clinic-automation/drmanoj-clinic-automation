#!/bin/bash
# =============================================================================
#  install_S379_PARCHI_TIDY.sh · kit S379_PARCHI_TIDY (session 279, 23-Sep-2026)
#
#  THE OWNER, 23-Sep-2026:
#    "In the Parchi system, doctor's upload is no longer relevant, but it is still there. Please remove it."
#    "the slips numbering in the ... day statement should come in an incremental order and not randomly. That is
#     how the physical register is designed. If any number is skipped, mention it there."
#    "for the Naya Mareez, the overnight report gives you the name of that patient so you can populate the name"
#    "few x rays need to be added, and procedures get a discount sometimes, build what's needed"
#
#  FILES (all this project's; finance_app.py untouched):
#    /root/finance/slip_log.py            S330 0b3195d2 -> f1de035f   (anchored edits, make_s379.py)
#    /root/finance/slip_lookup.py         S372 06e06cd0 -> 46e67c65   (two functions added)
#    /root/finance/finance_clinic_day.py  S372 738308b3 -> f6729d83   (anchored edits)
#    /root/finance/clinic_day_pdf.py      S372 ce843733 -> 150192e2   (anchored edits)
#  DATA: finance.db owner_service +6 X-ray rows (add_xrays_s379.py, after a sqlite backup of finance.db);
#        slip_item gains discount_p (added by the tile itself on first use, default 0).
#  WALK: walk_s379.py -- 31 checks on a synthetic day + a scratch copy of the live database; the live four
#        modules are the negative control. Restarts clinic-finance.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S379_PARCHI_TIDY/install_S379_PARCHI_TIDY.sh
# =============================================================================
set -u
KIT="S379_PARCHI_TIDY"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"; FIN="${FIN:-/root/finance}"
DBF="${FINANCE_DB:-$FIN/finance.db}"; PORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s379_walk_$STAMP"
FILES="slip_log.py slip_lookup.py finance_clinic_day.py clinic_day_pdf.py"
declare -A FROM=( [slip_log.py]=0b3195d2610e64a4b637e0ed89eb8454 [slip_lookup.py]=06e06cd0986c9cb862d8cb7895cfcc1f
                  [finance_clinic_day.py]=738308b3af38db09d98b25a450d98bef [clinic_day_pdf.py]=ce843733539bb091d86abf1f664c43d7 )
declare -A TO=( [slip_log.py]=f1de035fa4dfbfa8a69511f3a14e8083 [slip_lookup.py]=46e67c65b4ee778cc6c9e488e4f24976
                [finance_clinic_day.py]=f6729d8345a3d77adacfecd4e33475b4 [clinic_day_pdf.py]=150192e227bbeb539e6df686e25ae2b2 )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
probe() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in $FILES; do [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [1/8] kit $f is not its pin - nothing installed"; exit 1; }; done
say "[1/8] kit gates green"
all=1; for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || all=0; done
if [ $all = 1 ]; then say "-- files ALREADY INSTALLED; the X-ray lines:"; "$SPY" -B add_xrays_s379.py "$DBF" | tail -1; exit 0; fi
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/8] $FIN/$f is $(m5 "$FIN/$f"), not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
say "[2/8] live pins exact (slip_log S330 · slip_lookup, day page, PDF S372)"
mkdir -p "$WALK/new" "$WALK/live" || exit 1
\cp -p $FILES add_xrays_s379.py "$WALK/new/" && for f in $FILES; do \cp -p "$FIN/$f" "$WALK/live/"; done || { say "!! [3/8] scratch copy failed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile "$WALK"/new/*.py walk_s379.py || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/scratch.db" \
  || { say "!! [4/8] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && FINANCE_DB="$WALK/scratch.db" timeout 180 "$VPY" -B "$KDIR/walk_s379.py" "$WALK/new" "$WALK/live" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/8] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/8] $WOUT (a synthetic day + a scratch copy of the live database; the live modules are the negative control)"
for f in $FILES; do \cp -p "$FIN/$f" "$FIN/$f.bak_S379_${FROM[$f]:0:8}" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }; done
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in $FILES; do \cp -p "$FIN/$f.bak_S379_${FROM[$f]:0:8}" "$FIN/$f"; done
  systemctl restart clinic-finance || true; sleep 4
  say "   slip_log.py $(m5 "$FIN/slip_log.py") · finance $(probe "http://127.0.0.1:$PORT/finance/healthz")"; exit 1
}
\cp -p $FILES "$FIN/" || restore
for f in $FILES; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[5/8] placed; backups .bak_S379_<from8> beside each file"
systemctl restart clinic-finance || restore
sleep 5
systemctl is-active --quiet clinic-finance || restore
H=$(probe "http://127.0.0.1:$PORT/finance/healthz"); SL=$(probe "http://127.0.0.1:$PORT/finance/slips"); DY=$(probe "http://127.0.0.1:$PORT/finance/clinic/day")
say "[6/8] healthz $H · /finance/slips without login $SL · /finance/clinic/day without login $DY (302/401 expected: locked)"
[ "$H" = 200 ] && { [ "$SL" = 302 ] || [ "$SL" = 401 ]; } && { [ "$DY" = 302 ] || [ "$DY" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "Traceback\|NOT mounted" && restore
say "[7/8] clinic-finance active, no import error"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$FIN/finance.db.bak_S379_$STAMP" \
  || { say "!! [8/8] database backup failed - the six X-rays were NOT added (the code is live); tell the assistant"; exit 1; }
"$SPY" -B add_xrays_s379.py "$DBF" | sed 's/^/   /'
say "[8/8] database backup $FIN/finance.db.bak_S379_$STAMP"
md5sum $(for f in $FILES; do echo "$FIN/$f"; done)
say "$KIT: DONE -- read next: https://followup.dr-manoj.in/finance/slips and https://followup.dr-manoj.in/finance/clinic/day"
