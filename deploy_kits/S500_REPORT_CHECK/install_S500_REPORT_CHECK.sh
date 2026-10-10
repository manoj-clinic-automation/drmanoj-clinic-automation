#!/bin/bash
# =============================================================================
#  install_S500_REPORT_CHECK.sh · kit S500_REPORT_CHECK (Sanjeevni, session 301 brief of 08-Oct-2026; D694; F-799, F-788, F-801)
#  The two morning Marg reports: the steps on the page with Marg's own screens, each report judged RIGHT or WRONG with the step to
#  redo, two tries, a SHORT closing stock refused everywhere (the page and /api/snapshot), the owner told on his phone only on failure
#  (wrong twice, or not right by the hour) by reports_watch.tick riding the ten-minute job; Amir's voucher proof reads the NEWEST closing.
#
#  Run by (on the VPS):   bash <kit>/install_S500_REPORT_CHECK.sh
#     DRY=1 : every gate, the build, the compiles and the whole walk on scratch copies; no lock, no backup, nothing placed, nothing
#             written to the live database, no message.
#
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED / HALF-INSTALLED) · the lock · gates (flask, the four FROM pins, the three new files
#  absent, the duty map v9 twice, the read-only and must-not-move md5s and the crontab recorded) · build (make_s500.py) · compile all seven
#  on both pythons · scratch copies · the walk (DRY stops here) · re-check lock and pins · finance.db.bak_S500_<stamp> (backup API) ·
#  .bak_S500_<from8> beside each edited file · place (three new, reports_tile, stock_app, amir_day, order_rules LAST) · md5 read-back ·
#  the data (reports_watch.ensure: one table, five settings) · ONE restart of clinic-finance · healthz · the gated curls · the journal ·
#  the read-back (--say) · nothing else moved · the test message LAST.  Red after placing -> restore (order_rules.py FIRST), remove the
#  three new files, restart, healthz, report.
#  Every python this script starts carries ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a real phone
#  except the ONE test message at the very end, sent on purpose with the stubs unset for that one command.
# =============================================================================
set -u
KIT="S500_REPORT_CHECK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DUTYMAP="${S500_DUTY_MAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
CLONEMAP=/root/deploy/repo/claude_code_briefs/DUTY_MAP.json
MAP9=2016244829b4c70c00f1c59b0250ee35
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; MIG=/root/marg_ingest; AST=/root/assetapp
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s500_walk_$STAMP"
SVC=clinic-finance
ORDER=(reports_tile.py stock_app.py amir_day.py order_rules.py)          # placed in this order; order_rules.py LAST (the ten-minute job runs it)
NEWF=(reports_watch.py reports_guide.py reports_guide_pics.py)
declare -A FROM=( [reports_tile.py]=6f7cf490c949495e3e714b7dd688b7af [stock_app.py]=cc06dac9e3ab60a85d76e2409815b5af
                  [amir_day.py]=59b035da84a6648b94c1977d0c810b9d [order_rules.py]=ee17c1872acd0c440868a915fa5014df )
declare -A TO
declare -A RO=( ["$FIN/aaj_floor.py"]=1f53b8dad8be65e0c507efdd38464eb8 ["$FIN/spine/marg_read.py"]=96f565a8d138d9ce75c0ed228b471495
                ["$FIN/export_watch.py"]=f6845ec5ae1dc8fe200ebf5f4c3ad173 ["$FIN/shelf_figure.py"]=a1e87d1ff758e8f9a8206205a457b875
                ["$FIN/item_alias.py"]=5168c3c05df63a674a8dcab59f74365f ["$MIG/marg_take.py"]=a86a0f26d4fc86a51e963b6a1b561323 )
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/aaj_kaam.py" "$FIN/aaj_kaam.html" "$FIN/aaj_duties.json" "$FIN/owner_console.py"
      "$FIN/porders_s454.py" "$FIN/porders.py" "$FIN/porders.html" "$FIN/darpan_kal.py" "$FIN/darpan_kal.html" "$FIN/order_sheet.py" "$FIN/order_sheet_pdf.py"
      "$FIN/finance_ui/finance_approvals.html" "$FIN/spine/spine_read.py" "$FIN/spine/order_rehearsal.py" "$FIN/spine/selftest_spine.py" "$CLONEMAP")
declare -A NOTT_PIN=( ["$FIN/finance_app.py"]=bff362c3 ["$POR/portal.py"]=63df9d49 ["$POR/tile_grants.json"]=f9441311 ["$FIN/order_sheet.py"]=012e21c9
                      ["$FIN/porders_s454.py"]=9c463e7c ["$FIN/porders.py"]=a5a823bf ["$FIN/porders.html"]=7a6799ae ["$FIN/darpan_kal.py"]=fd799a56
                      ["$FIN/darpan_kal.html"]=f5e279eb ["$FIN/order_sheet_pdf.py"]=6e7a5e1a ["$FIN/finance_ui/finance_approvals.html"]=b32da7ff
                      ["$FIN/spine/spine_read.py"]=712a1e4e ["$FIN/spine/order_rehearsal.py"]=104d366d ["$FIN/spine/selftest_spine.py"]=fc63d2c6 ["$CLONEMAP"]=20162448 )
mkdir -p "$WALK/noring" || exit 1
export ORDER_PUSH_STUB="$WALK/installer_pushes.jsonl" RING_PORTAL_DIR="$WALK/noring" REPORTS_NTFY_STUB="$WALK/installer_ntfy_stub.jsonl"
unset ORDER_PUSH_NONE ORDER_TODAY ORDER_TICK ORDER_CLOCK
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
state_now() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
n=c.execute(\"SELECT COUNT(*) FROM setting WHERE key LIKE 'reports.%'\").fetchone()[0]
t=c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='marg_report_alert'\").fetchone()[0]
a=c.execute('SELECT day, key, kind, sent_at IS NOT NULL FROM marg_report_alert ORDER BY day DESC, key LIMIT 4').fetchall() if t else []
print('reports.* settings %d · marg_report_alert %s · newest alert rows %s' % (n, 'yes' if t else 'no', a))
" "$DBF"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/15] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/15] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/15] PINS.sh missing - nothing done"; exit 1; }
for f in "${NEWF[@]}"; do [ "$(m5 "$KDIR/$f")" = "${TO[$f]}" ] || { say "!! [0/15] the kit's $f is $(m5 "$KDIR/$f"), not its pin ${TO[$f]} - nothing done"; exit 1; }; done
ALL=1; for f in "${ORDER[@]}" "${NEWF[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done

# ---- the steps after the placing, shared by the full install and the HALF-INSTALLED finish ------------------------------------------
take_lock() {
  if mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/15] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
  elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/15] the build lock is already held by $KIT"
  else say "!! [1/15] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
}
db_backup() {
  copydb "$DBF" "$FIN/finance.db.bak_S500_$STAMP" && [ -s "$FIN/finance.db.bak_S500_$STAMP" ] || { say "!! database backup failed - nothing placed (the lock stays: $KIT)"; rm -rf "$WALK"; exit 1; }
  say "[9/15] $FIN/finance.db.bak_S500_$STAMP made by the backup API ($(stat -c %s "$FIN/finance.db.bak_S500_$STAMP") bytes)"
}
putfile() { \cp -p "$1" "$2.s500_new" && mv -f "$2.s500_new" "$2"; }      # a rename: a running reader never sees half a file
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically (order_rules.py FIRST), removing the three new files"
  for f in order_rules.py amir_day.py stock_app.py reports_tile.py; do
    b="$FIN/$f.bak_S500_${FROM[$f]:0:8}"; [ -f "$b" ] && putfile "$b" "$FIN/$f"
  done
  for f in "${NEWF[@]}"; do rm -f "$FIN/$f" "$FIN/__pycache__/${f%.py}".*; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  for f in "${NEWF[@]}"; do say "   $FIN/$f $( [ -e "$FIN/$f" ] && echo STILL THERE || echo removed)"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  say "   DATA: the table marg_report_alert and the five reports.* setting rows stay (harmless: nothing reads them without the files); the database backup stays"
  rm -rf "$WALK"; exit 1
}
data_step() {
  DATA="$( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B -c "import sqlite3, reports_watch as w; c = sqlite3.connect('$DBF', timeout=60); w.ensure(c); print('DATA_OK', c.execute(\"SELECT COUNT(*) FROM setting WHERE key LIKE 'reports.%'\").fetchone()[0], c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='marg_report_alert'\").fetchone()[0])" 2>&1 )"; rc=$?
  echo "$DATA" | mask | sed 's/^/   /'
  echo "$DATA" | grep -q "^DATA_OK 5 1$" && [ "$rc" = 0 ] || restore "the data step (reports_watch.ensure)"
  say "[12/15] DATA_OK 5 1: the table marg_report_alert and the five reports.* setting rows (INSERT OR IGNORE)"
}
restart_step() {
  T0="$(date '+%Y-%m-%d %H:%M:%S')"
  systemctl restart "$SVC" || restore "restart"
  sleep 8
  systemctl is-active --quiet "$SVC" || restore "$SVC not active"
  c1=$(health http://127.0.0.1:8106/finance/healthz)
  say "health : finance healthz $c1"
  [ "$c1" = 200 ] || restore "finance healthz"
  for p in /finance/reports/aaj /finance/reports/aaj/kaise/sale /finance/reports/aaj/pic/sale_two.jpg; do
    c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
    [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
  done
  journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  [ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
  say "[13/15] $SVC active (restarted once, $T0); healthz 200; the three gated pages answer the gate; no error in its journal"
}
readback_step() {
  mkdir -p "$WALK/rb/nosso" && copydb "$DBF" "$WALK/rb/now.db" || restore "no copy of the database for the read-back"
  RB="$( cd "$FIN" && FINANCE_DB="$WALK/rb/now.db" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$WALK/rb/nosso" timeout 300 "$VPY" -B - <<'PYEOF' 2>&1
import sys
sys.path.insert(0, ".")
import finance_app as fa
import reports_guide
c = fa.app.test_client()
H = {"X-Clinic-User": "shavez", "X-Clinic-Role": "manager"}
r = c.get("/finance/reports/aaj", headers=H)
h = r.get_data(as_text=True)
print("as shavez: /finance/reports/aaj %s, 'Signed in: shavez' %s, 'Aaj ki reports' %s" % (r.status_code, "Signed in: shavez" in h, "Aaj ki reports" in h))
g = c.get("/finance/reports/aaj/kaise/stock", headers=H)
print("as shavez: /kaise/stock %s, six steps %s" % (g.status_code, g.get_data(as_text=True).count("<li>") >= 6))
p = c.get("/finance/reports/aaj/pic/only_total.jpg", headers=H)
print("as shavez: /pic/only_total.jpg %s %s, %d bytes, equals the module's %s" % (p.status_code, p.mimetype, len(p.get_data()), p.get_data() == reports_guide.pic("only_total")))
ok = r.status_code == 200 and "Signed in: shavez" in h and g.status_code == 200 and p.status_code == 200 and p.mimetype == "image/jpeg"
print("READ_BACK %s" % ("OK" if ok else "RED"))
PYEOF
)"
  echo "$RB" | mask | cut -c1-600 | sed 's/^/   /'
  echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the placed files on a copy of the database as it is now"
  SAY="$( cd "$FIN" && FINANCE_DB="$WALK/rb/now.db" timeout 300 "$VPY" -B reports_watch.py --say 2>&1 )"
  say "   reports_watch.py --say on the copy (the first two lines are what the live page says of today's two reports):"
  echo "$SAY" | mask | cut -c1-400 | sed 's/^/      /'
  echo "$SAY" | grep -q "^would tell the owner now:" || restore "reports_watch.py --say did not run on the copy"
  say "[14/15] read back (the placed files on a copy of the database as it is now, the live spine and archive read only): the page, the guide, a picture; --say above"
}
notmoved_step() {
  for f in "${!RO[@]}"; do [ "$(m5 "$f")" = "${RO0[$f]}" ] || restore "$f moved -- read only for this kit"; done
  for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
  [ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
  [ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
  say "[15/15] nothing else moved (the six read-only files, the nineteen must-not-move files incl. the clone's DUTY_MAP.json, the crontab); healthz 200"
}
testmsg_step() {
  TM="$( unset ORDER_PUSH_STUB ORDER_PUSH_NONE REPORTS_NTFY_STUB; cd "$FIN" && FINANCE_DB="$DBF" timeout 60 "$VPY" -B reports_watch.py --test-message 2>&1 )"; trc=$?
  echo "$TM" | mask | sed 's/^/   /'
  if [ "$trc" = 0 ] && echo "$TM" | grep -q "pushed to the owner's phone"; then say "   TEST MESSAGE: pushed to the owner's phone (one message, says it is a test)"
  else say "   TEST MESSAGE NOT SENT (exit $trc) -- the install stands; the page works without it; until this is put right he is NOT told. First line of the report."; fi
}
record_pins() {
  declare -gA RO0 NT0
  for f in "${!RO[@]}"; do RO0[$f]="$(m5 "$f")"; done
  for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
  CRON0="$(cron5)"
}

# ---- gate 0b: already / half installed ---------------------------------------------------------------------------------------------------
if [ "$ALL" = 1 ]; then
  if [ "${DRY:-0}" = 1 ]; then say "-- ALREADY INSTALLED: the seven files are at the kit's pins (DRY); $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"; rm -rf "$WALK"; exit 0; fi
  CNT="$("$SPY" -c "import sqlite3; c=sqlite3.connect('file:$DBF?mode=ro',uri=True); print(c.execute(\"SELECT COUNT(*) FROM setting WHERE key LIKE 'reports.%'\").fetchone()[0], c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='marg_report_alert'\").fetchone()[0])" 2>/dev/null)"
  SVC_T="$(date -d "$(systemctl show -p ActiveEnterTimestamp --value "$SVC")" +%s 2>/dev/null || echo 0)"
  NEWEST=0; for f in "${ORDER[@]}" "${NEWF[@]}"; do t=$(stat -c %Y "$FIN/$f"); [ "$t" -gt "$NEWEST" ] && NEWEST=$t; done
  if [ "$CNT" = "5 1" ] && [ "$SVC_T" -gt "$NEWEST" ]; then
    say "-- ALREADY INSTALLED: the seven files are at the kit's pins; the data reads 5 1; $SVC started after the newest file; healthz $(health http://127.0.0.1:8106/finance/healthz)"
    say "   $(state_now)"; rm -rf "$WALK"; exit 0
  fi
  say "-- HALF-INSTALLED: the seven files are at their pins but the data reads '$CNT' or the service is older than the files -- finishing"
  take_lock; record_pins; db_backup; data_step; restart_step; readback_step; notmoved_step; testmsg_step
  say "   $(state_now)"; rm -rf "$WALK"; say "$KIT: DONE (finished a half install) · the lock stays held by $KIT until the report is written"; exit 0
fi

# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/15] DRY RUN: no lock, no backup, nothing placed, nothing written, no message"; else take_lock; fi
# ---- 2: gates, pins --------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || { say "!! [2/15] the venv python lacks flask; nothing placed"; rm -rf "$WALK"; exit 1; }
for k in "$DUTYMAP" "$CLONEMAP" "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json" "$MIG/marg_take.py"; do
  [ -f "$k" ] || { say "!! [2/15] $k must be reachable - nothing placed"; rm -rf "$WALK"; exit 1; }
done
[ "$(m5 "$DUTYMAP")" = "$MAP9" ] || { say "!! [2/15] the duty map beside the kit is $(m5 "$DUTYMAP"), not v9 $MAP9 - nothing placed"; rm -rf "$WALK"; exit 1; }
[ "$(m5 "$CLONEMAP")" = "$MAP9" ] || { say "!! [2/15] the clone's duty map is $(m5 "$CLONEMAP"), not v9 $MAP9 - nothing placed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/15] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"; rm -rf "$WALK"; exit 1; }
done
for f in "${NEWF[@]}"; do
  if [ -e "$FIN/$f" ]; then
    [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || { say "!! [2/15] $FIN/$f is present and is $(m5 "$FIN/$f"), not the kit's $f - STOP; nothing placed"; rm -rf "$WALK"; exit 1; }
    say "   $FIN/$f is already present at its TO pin (a re-run): it is placed again, byte-identical"
  fi
done
record_pins
say "[2/15] gates green (SUMS, KIT_ID, PINS, the venv's flask, the duty map v9 beside the kit and in the clone, the databases, the portal, marg_take); the four live files at their FROM pins; the three new files absent"
for f in $(printf '%s\n' "${!RO[@]}" | sort); do say "   read only: $f ${RO0[$f]} $( [ "${RO0[$f]}" = "${RO[$f]}" ] && echo '(the brief pin)' || echo "(NOT the brief pin ${RO[$f]}: the walk reads it as it is)")"; done
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p…: moved by another kit before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s500.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/15] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; rm -rf "$WALK"; exit 1; }; done
for f in "${NEWF[@]}"; do cp -p "$KDIR/$f" "$WALK/built/$f"; done
say "[3/15] live bytes + anchored edits give the four pinned files; the three new files beside them (seven at their TO pins)"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/15] compile on both pythons failed - nothing placed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/15] the seven files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
  [ -f "$R/$side/finance_app.py" ] && [ -f "$R/$side/aaj_duties.json" ] || { say "!! [5/15] no scratch copy of the finance folder - nothing placed"; rm -rf "$WALK"; exit 1; }
done
for f in "${ORDER[@]}" "${NEWF[@]}"; do cp -p "$WALK/built/$f" "$R/new/$f"; done
for f in "${NEWF[@]}"; do rm -f "$R/old/$f"; done                          # the OLD side: the box as it was before this kit (a re-run has them live)
mkdir -p "$R/por" "$R/marg_ingest" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
cp -p "$MIG"/*.py "$R/marg_ingest/" 2>/dev/null
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/15] no scratch copies - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[5/15] scratch copies: the finance folder twice (NEW with the seven files, OLD as the box was -- the three new files absent), the portal's code, marg_ingest's code; finance.db, assets.db and spine.db by the backup API"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s500.py" --kit "$KDIR" --work "$R/w" --fin-new "$R/new" --fin-old "$R/old" --por "$R/por" --marg-ingest "$R/marg_ingest" \
         --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S500 GREEN" || { say "!! [6/15] walk_s500 red - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[6/15] walk_s500 sections 1-10 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written, no message"; rm -rf "$WALK"; exit 0; fi
# ---- 7-8: re-check, file backups ---------------------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/15] the build lock is not held by $KIT - nothing placed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [7/15] $FIN/$f moved during the walk - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/15] the lock is held by $KIT; the four FROM pins still stand after the walk"
say "   before: $(state_now)"
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S500_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [8/15] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[8/15] a .bak_S500_<from8> beside each of the four edited files, read back"
# ---- 9-11: database backup, place, read back ---------------------------------------------------------------------------------------------
db_backup
for f in "${NEWF[@]}"; do putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
say "[10/15] placed by copy-then-rename: the three new files, then reports_tile.py, stock_app.py, amir_day.py and order_rules.py last (the ten-minute job runs the new code from now)"
for f in "${NEWF[@]}" "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
for f in "${ORDER[@]}" "${NEWF[@]}"; do cmp -s "$FIN/$f" "$R/new/$f" || restore "the placed $f is not the walk's file"; done
say "[11/15] md5 read back = the seven TO pins; each placed file is byte-identical to the walk's NEW copy"
# ---- 12-15: the data, restart, read-back, nothing else moved, the test message -----------------------------------------------------------
data_step
restart_step
readback_step
notmoved_step
say "   after : $(state_now)"
for f in "${NEWF[@]}" "${ORDER[@]}"; do md5sum "$FIN/$f"; done
testmsg_step
rm -rf "$WALK"
say "   done · healthz 200 · backups: $FIN/finance.db.bak_S500_$STAMP and a .bak_S500_<from8> beside each of the four edited files · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
