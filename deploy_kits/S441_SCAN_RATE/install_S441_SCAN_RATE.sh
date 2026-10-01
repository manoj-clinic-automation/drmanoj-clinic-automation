#!/bin/bash
# =============================================================================
#  install_S441_SCAN_RATE.sh · kit S441_SCAN_RATE (session 287, 01-Oct-2026, D643 · F-665 · F-666 · F-667) · PARENT
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S441_SCAN_RATE/install_S441_SCAN_RATE.sh
#  (DRY=1 runs every gate, the walk and the first pass on fresh scratch copies, and places nothing.)
#
#  THE OWNER, 01-Oct: the scan flow "smooth, friction-free ... staff not held ... no extra confirmations".
#   * Every photo is a page by itself (no "Add this page"); one Save; each thumbnail has a small Retake.
#   * The stamp shows at once, big; the camera is ready for the next bill. A slow upload retries by itself under one
#     client_token, so a retry can never make a second bill. "PDF / file" stays: one bill, one stamp.
#   * After the fact, on the server: a forgotten page joins its bill; a sure double scan (same supplier, same bill-number
#     tail, amount within 2%) is set aside -- kept, never deleted, out of counts and packs; anything unsure (a near match,
#     a pharmacy supplier in the clinic lane) is ONE line on "Scan ka kaam" for Shavez AND reception; the first answer
#     settles it and shows who answered.
#   * The shared "Reception" login asks once "Kaun kaam kar raha hai?" (Shivani, Alisha, Darpan, Sukhveer, Shavez),
#     remembered until 30 minutes idle or "badlo"; every stamp, order sent and arrival marked carries the name; reception
#     becomes an order sender. Personal logins are never asked.
#   * The X-ray & procedure rate page: one short line per item, tap to edit, consumables folded, saves in place, and an
#     X-ray save no longer lands on the procedures view (F-665).
#
#  FILES (full-file replacements, each checked at its FROM pin and read back at its TO pin):
#          /root/assetapp/asset_register.py   0deaa531 -> 446c671d   PARENT
#          /root/assetapp/scanner_widget.js   4ae2d29a -> e2bca602   PARENT (four opt-in switches; other callers unchanged)
#          /root/finance/owner_sheets.py      b354d893 -> 6a04071d   PARENT
#          /root/finance/porders.py           e43adfb0 -> af4a6f57   SANJEEVNI'S, declared on board/_numbers (S286 PLANNED line)
#          /root/finance/porders.html         792aebba -> 7a6799ae   SANJEEVNI'S, declared
#          /root/portal/tile_grants.json      df73b84a (shipped as built/tile_grants.json.txt -- .gitignore blocks *.json) -> acc9cc1b   v29 -> v30: 'Purchase orders' to the shared reception login
#          /root/shared/scan_checks_s441.py   NEW      -> b9ba6839
#  DATA:   finance.db (backed up first): unit_role (porders, reception, maker) and 'reception' added to porders.senders.
#          assets.db (backed up first): three additive columns on bills, two new tables, made by the asset app's migrate.
#  Restarts clinic-finance AND assetapp. The portal reads tile_grants.json by its mtime (no restart).
# =============================================================================
set -u
KIT="S441_SCAN_RATE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; AST="$ROOT/assetapp"; POR="$ROOT/portal"; SHR="$ROOT/shared"
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s441_walk_$STAMP"
declare -A FROM=( [asset_register.py]=0deaa531a412979d523ae0d4fd000946 [scanner_widget.js]=4ae2d29aa73943c6f772189b56be6307
                  [owner_sheets.py]=b354d89326116ce71ef2c7adeda6b23a [porders.py]=e43adfb03f11b1b658805553b8441ae5
                  [porders.html]=792aebbacc377198f7081b6129429f6f [tile_grants.json]=df73b84a0bde3917b97c233647ffe0a5 [scan_checks_s441.py]=NEW )
declare -A DIR=( [asset_register.py]="$AST" [scanner_widget.js]="$AST" [owner_sheets.py]="$FIN" [porders.py]="$FIN" [porders.html]="$FIN"
                 [tile_grants.json]="$POR" [scan_checks_s441.py]="$SHR" )
ORDER=(scan_checks_s441.py asset_register.py scanner_widget.js owner_sheets.py porders.py porders.html tile_grants.json)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask, pypdf" 2>/dev/null || { say "!! [1/9] the venv python lacks flask / pypdf; nothing installed"; exit 1; }
for f in "$DBF" "$ADB"; do [ -f "$f" ] || { say "!! [1/9] $f is not there; nothing installed"; exit 1; }; done
say "[1/9] kit gates green (SUMS, KIT_ID, the venv's flask + pypdf, finance.db, assets.db)"
declare -A TO
while read -r h f; do TO[$(basename "$f" .txt)]="$h"; done < <(grep ' built/' SUMS.md5)   # tile_grants ships as .json.txt (.gitignore blocks every .json)
src() { [ -f "built/$1" ] && echo "built/$1" || echo "built/$1.txt"; }
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the seven files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance) · assetapp $(systemctl is-active assetapp)"; exit 0; fi
for f in "${ORDER[@]}"; do
  if [ "${FROM[$f]}" = NEW ]; then [ ! -e "${DIR[$f]}/$f" ] || { say "!! [2/9] ${DIR[$f]}/$f already exists - nothing installed"; exit 1; }
  else [ "$(m5 "${DIR[$f]}/$f")" = "${FROM[$f]}" ] || { say "!! [2/9] ${DIR[$f]}/$f is $(m5 "${DIR[$f]}/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the build; nothing installed"; exit 1; }; fi
done
say "[2/9] the six live files at their FROM pins; scan_checks_s441.py not there yet"
( "$SPY" -m py_compile built/*.py walk_s441.py && "$VPY" -m py_compile built/*.py walk_s441.py ) 2>/dev/null \
  || { say "!! [3/9] compile on both pythons failed - nothing installed"; clean; exit 1; }
clean
say "[3/9] compiles on /usr/bin/python3 and the venv python"
mkdir -p "$WALK/ast" "$WALK/ast_old" "$WALK/shared" "$WALK/portal" "$WALK/up/stub" || exit 1
for side in fin fin_old; do
  mkdir -p "$WALK/$side/finance_ui" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  [ -d "$FIN/spine" ] && { mkdir -p "$WALK/$side/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; }
done
cp -p "$AST"/*.py "$AST"/*.js "$WALK/ast/"; cp -p "$AST"/*.py "$AST"/*.js "$WALK/ast_old/"; cp -p "$SHR"/*.py "$WALK/shared/"; cp -p "$POR"/*.py "$POR"/*.json "$WALK/portal/" 2>/dev/null
for f in owner_sheets.py porders.py porders.html; do cp -p "built/$f" "$WALK/fin/$f"; done
for f in asset_register.py scanner_widget.js; do cp -p "built/$f" "$WALK/ast/$f"; done
cp -p built/scan_checks_s441.py "$WALK/shared/"
copydb "$DBF" "$WALK/scratch_fin.db" && copydb "$ADB" "$WALK/scratch_assets.db" || { say "!! [4/9] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK" && timeout 1500 "$VPY" -B "$KDIR/walk_s441.py" --new-fin "$WALK/fin" --old-fin "$WALK/fin_old" --new-ast "$WALK/ast" --old-ast "$WALK/ast_old" \
         --shared "$WALK/shared" --portal "$WALK/portal" --db "$WALK/scratch_fin.db" --adb "$WALK/scratch_assets.db" --uploads "$WALK/up" 2>&1 )"
echo "$WOUT" | grep -v '^-- ' | sed -E 's/[0-9]{10,}/##########/g' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S441 GREEN" || { say "!! [4/9] walk red - nothing installed"; echo "$WOUT" | grep '^-- ' | cut -c1-600; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/9] walk_s441 green on scratch copies of finance.db and assets.db, its negative control red on the box as it is (above)"
FIG="$WALK/fig"; mkdir -p "$FIG"
copydb "$ADB" "$FIG/assets.db" && ( cd "$WALK/ast" && ASSETS_DB="$FIG/assets.db" "$SPY" -B -c "
import sys; sys.path.insert(0,'$WALK/ast'); sys.path.insert(0,'$WALK/shared')
import asset_register as ar
with ar.app.app_context(): ar.init_db()
import scan_checks_s441 as S, sqlite3, json
S.FIN_DB='$DBF'
db=sqlite3.connect('$FIG/assets.db'); r=S.run_pass(db, upload_dir='$WALK/up')
print('first pass on a copy of today\'s scans:', json.dumps(r, sort_keys=True))
for q in db.execute(\"SELECT b.stamp_no, b.dup_of, (SELECT stamp_no FROM bills x WHERE x.id=b.dup_of) FROM bills b WHERE b.approved_by LIKE 'server (S441%' ORDER BY b.id\"): print('  set aside:', q[0], 'duplicate of', q[2])
for q in db.execute('SELECT q.kind, b.stamp_no, (SELECT stamp_no FROM bills x WHERE x.id=q.cand_id) FROM scan_question q JOIN bills b ON b.id=q.bill_id ORDER BY q.id'): print('  asked:', q[0], q[1], ('vs ' + q[2]) if q[2] else '')
" 2>&1 | sed 's/^/   /' )
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the first pass (on a copy) green; NOTHING placed, nothing restarted"; clean; rm -rf "$WALK"; exit 0; fi
copydb "$DBF" "$FIN/finance.db.bak_S441_$STAMP" || { say "!! [5/9] finance.db backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
copydb "$ADB" "$AST/assets.db.bak_S441_$STAMP" || { say "!! [5/9] assets.db backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  [ "${FROM[$f]}" = NEW ] && { BAK[$f]=""; continue; }
  BAK[$f]="${DIR[$f]}/$f.bak_S441_$(m5 "${DIR[$f]}/$f" | cut -c1-8)"; \cp -p "${DIR[$f]}/$f" "${BAK[$f]}" || { say "!! [5/9] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[5/9] finance.db.bak_S441_$STAMP and assets.db.bak_S441_$STAMP made (backup API); .bak_S441_<from8> beside the six files"
restore() {
  say "!! RED after placing ($1) - restoring the files byte-identically"
  for f in "${ORDER[@]}"; do if [ -n "${BAK[$f]}" ]; then \cp -p "${BAK[$f]}" "${DIR[$f]}/$f"; else rm -f "${DIR[$f]}/$f"; fi; done
  "$SPY" -c "import sqlite3; c=sqlite3.connect('$DBF'); c.execute(\"DELETE FROM unit_role WHERE unit='porders' AND username='reception' AND role='maker'\"); c.execute(\"UPDATE setting SET value=? WHERE key='porders.senders'\", ('$SENDERS0',)); c.commit()" 2>/dev/null
  systemctl restart clinic-finance || true; systemctl restart assetapp || true; sleep 6
  for f in "${ORDER[@]}"; do say "   ${DIR[$f]}/$f $(m5 "${DIR[$f]}/$f")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · asset app login $(health http://127.0.0.1:8030/login) · the database backups stay: $FIN/finance.db.bak_S441_$STAMP · $AST/assets.db.bak_S441_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
SENDERS0="$("$SPY" -c "import sqlite3; c=sqlite3.connect('$DBF'); r=c.execute(\"SELECT value FROM setting WHERE key='porders.senders'\").fetchone(); print(r[0] if r else '')")"
for f in "${ORDER[@]}"; do \cp "$(src "$f")" "${DIR[$f]}/$f" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DIR[$f]}/$f")" = "${TO[$f]}" ] || restore "md5 read-back"; done
say "[6/9] placed; all seven md5s read back = the kit's pins (the widget carries a new mtime, so phones fetch it fresh)"
"$SPY" -c "
import sqlite3, datetime
c = sqlite3.connect('$DBF', timeout=30)
c.execute(\"INSERT OR IGNORE INTO unit_role (unit, username, role, active) VALUES ('porders','reception','maker',1)\")
v = (c.execute(\"SELECT value FROM setting WHERE key='porders.senders'\").fetchone() or [''])[0] or ''
names = [x.strip() for x in v.replace(';', ',').split(',') if x.strip()]
if 'reception' not in [x.lower() for x in names]:
    c.execute(\"UPDATE setting SET value=?, note=? WHERE key='porders.senders'\", (','.join(names + ['reception']), 'S441 D643: the shared reception login sends orders once it names who works'))
c.commit()
print('   porders: reception maker row', c.execute(\"SELECT COUNT(*) FROM unit_role WHERE unit='porders' AND username='reception' AND active=1\").fetchone()[0], '· senders', c.execute(\"SELECT value FROM setting WHERE key='porders.senders'\").fetchone()[0])
" || restore "the porders data"
say "[7/9] reception is an order sender (unit_role porders maker + porders.senders)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
systemctl restart assetapp || restore "restart assetapp"
sleep 7
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
systemctl is-active --quiet assetapp || restore "assetapp not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/porders); c3=$(health http://127.0.0.1:8106/finance/clinic/sheets)
a1=$(health http://127.0.0.1:8030/login); a2=$(health http://127.0.0.1:8030/intake); a3=$(health http://127.0.0.1:8030/scan/widget.js)
say "health : finance healthz $c1 · /finance/porders $c2 · /finance/clinic/sheets $c3 (302/401 = the login gate) · asset login $a1 · /intake $a2 · widget.js $a3"
[ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ]; } && { [ "$c3" = 302 ] || [ "$c3" = 401 ] || [ "$c3" = 403 ]; } || restore "finance health"
[ "$a1" = 200 ] && [ "$a2" = 302 ] || restore "asset app health"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
JR="$(journalctl -u assetapp --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "$JR" = 0 ] || { journalctl -u assetapp --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "assetapp journal: $JR error line(s)"; }
say "[8/9] clinic-finance and assetapp active; healthz 200; the pages behind their gates; nothing 'NOT mounted'; the asset app's journal clean"
POUT="$( cd "$AST" && "$SPY" -B "$SHR/scan_checks_s441.py" pass "$ADB" "$AST/uploads" 2>&1 )" || { echo "$POUT" | tail -20; restore "the first pass"; }
echo "$POUT" | sed 's/^/   /'
echo "$POUT" | grep -q "^S441 pass" || restore "the first pass"
say "[9/9] the first pass ran on the live scans (above): every scan of the last 90 days judged once; anything unsure is on Scan ka kaam"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "${DIR[$f]}/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/scanapp/intake · https://followup.dr-manoj.in/finance/porders · https://followup.dr-manoj.in/finance/clinic/sheets"
