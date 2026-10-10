#!/bin/bash
# =============================================================================
#  install_S502_STOCK_MILAAN_TODAY.sh · kit S502_STOCK_MILAAN_TODAY (Sanjeevni, session 303, 10-Oct-2026; D699; F-812, F-813, F-814, F-815)
#  Darpan's Stock milaan shows only today's work; a morning-list count can be corrected the same day ('Galat likha? Badlo'); the 06-Sep count
#  is sealed for staff; a loss line can be voided; today's TRUECEPROL OD and the TYRO BR line put right (keyed, idempotent data fixes).
#
#  Run by (on the VPS):   bash <kit>/install_S502_STOCK_MILAAN_TODAY.sh
#     DRY=1 : every gate, the build, the compiles and the whole walk on scratch copies; no lock, no backup, nothing placed, nothing written.
#
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask, the three FROM pins, the duty map v9, the read-only and
#  must-not-move md5s recorded) · build (make_s502.py) · compile on both pythons · scratch copies · the walk (DRY stops) · re-check · .bak_S502
#  beside each file · finance.db.bak_S502_<stamp> (backup API) · place (copy-then-rename) · md5 read-back · the data fixes (fix_s502.py on the
#  live database: ensure's two columns, A TRUECEPROL OD, B TYRO BR) · ONE restart of clinic-finance · healthz · the gated curl · the journal ·
#  the read-back (darpan's state on a copy) · nothing else moved.  Red after placing -> the three files restored byte-identically, restart,
#  healthz, report; the database backup stays and the data fixes are reversed only if the owner says so.
#  The spine (the walk's copy; the live one read-only by the fixes), the portal and the asset app are never written.
#  PATCHED ON THE BOX from the live bytes (make_s502.py; every anchor exactly once): stock_watch.py stockmatch.py stockmatch.html (/root/finance).
#  READ ONLY (md5 before = after): loss_piles.py shelf_figure.py stock_app.py qty_words.py.  NOT TOUCHED: finance_app.py portal.py tile_grants.json
#  aaj_kaam.py aaj_duties.json, S500's four files (reports_tile.py order_rules.py amir_day.py and stock_app.py as S500 left them), the crontab.
# =============================================================================
set -u
KIT="S502_STOCK_MILAAN_TODAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DUTYMAP="${S502_DUTY_MAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
MAP9=2016244829b4c70c00f1c59b0250ee35
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s502_walk_$STAMP"
SVC=clinic-finance
ORDER=(stock_watch.py stockmatch.py stockmatch.html)
declare -A FROM=( [stock_watch.py]=d78c902e0d3258fd0c615cd9715346b6 [stockmatch.py]=f09d9516a9df73941033591af8878c3e [stockmatch.html]=0dc4d303434d6f87d9e470bccb79f54c )
declare -A TO
declare -A RO=( ["$FIN/loss_piles.py"]=202bfc4e3fd798501c6db95373c2a7d4 ["$FIN/shelf_figure.py"]=a1e87d1ff758e8f9a8206205a457b875
                ["$FIN/stock_app.py"]=bfc2a40bff0d8f0050078ea49f990eda ["$FIN/qty_words.py"]=706db7ccfa7489fb8d296f663590f107 )
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/aaj_kaam.py" "$FIN/aaj_duties.json" "$FIN/reports_tile.py" "$FIN/order_rules.py" "$FIN/amir_day.py"
      "$FIN/reports_watch.py" "$FIN/reports_guide.py" "$FIN/reports_guide_pics.py")
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
cols=[r[1] for r in c.execute('PRAGMA table_info(stock_watch_loss_line)')]
r=c.execute(\"SELECT qty_units, point_id FROM stock_spot_roster WHERE day='2026-10-10' AND item='TRUECEPROL OD'\").fetchone()
l=c.execute(\"SELECT id, void_at IS NOT NULL FROM stock_watch_loss_line WHERE item='TYRO BR' AND gap_units=707\").fetchall() if 'void_at' in cols else 'no void column'
a=c.execute(\"SELECT item FROM stock_watch_ask WHERE done_at IS NULL\").fetchall()
print('void columns %s · TRUECEPROL OD roster (qty, point) %s · TYRO BR 707 line (id, voided) %s · asks open %s' % ('void_at' in cols, tuple(r) if r else None, l, a))
" "$DBF"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/13] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/13] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/13] PINS.sh missing - nothing done"; exit 1; }
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the three files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   $(state_now)"; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/13] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/13] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/13] the build lock is already held by $KIT"
else say "!! [1/13] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates, pins --------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || { say "!! [2/13] the venv python lacks flask; nothing placed"; rm -rf "$WALK"; exit 1; }
for k in "$DUTYMAP" "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json"; do
  [ -f "$k" ] || { say "!! [2/13] $k must be reachable - nothing placed"; rm -rf "$WALK"; exit 1; }
done
[ "$(m5 "$DUTYMAP")" = "$MAP9" ] || { say "!! [2/13] the duty map beside the kit is $(m5 "$DUTYMAP"), not v9 $MAP9 - nothing placed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/13] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"; rm -rf "$WALK"; exit 1; }
done
declare -A RO0 NT0
for f in "${!RO[@]}"; do RO0[$f]="$(m5 "$f")"; done
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/13] gates green (SUMS, KIT_ID, PINS, the venv's flask, the duty map v9, the databases, the portal); the three live files at their FROM pins"
for f in $(printf '%s\n' "${!RO[@]}" | sort); do say "   read only: $f ${RO0[$f]} $( [ "${RO0[$f]}" = "${RO[$f]}" ] && echo '(the brief pin)' || echo "(NOT the brief pin ${RO[$f]}: the walk reads it as it is)")"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s502.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/13] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[3/13] live bytes + anchored edits give the three pinned files"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in stock_watch.py stockmatch.py; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/13] compile on both pythons failed - nothing placed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/13] the two built python files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
  [ -f "$R/$side/finance_app.py" ] && [ -f "$R/$side/aaj_duties.json" ] || { say "!! [5/13] no scratch copy of the finance folder - nothing placed"; rm -rf "$WALK"; exit 1; }
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/new/$f"; done
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/13] no scratch copies - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[5/13] scratch copies: the finance folder twice (NEW with the three built files, OLD as it is), the portal's code; finance.db, assets.db and spine.db by the backup API"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s502.py" --kit "$KDIR" --work "$R/w" --fin-new "$R/new" --fin-old "$R/old" --por "$R/por" \
         --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S502 GREEN" || { say "!! [6/13] walk_s502 red - nothing placed"; rm -rf "$WALK"; exit 1; }
SJ="$(echo "$WOUT" | grep -o 'rendered check: /tmp/[^ ]*state_darpan.json' | awk '{print $NF}')"
[ -n "$SJ" ] && [ -f "$SJ" ] && cp -p "$SJ" "/tmp/s502_state_darpan_$STAMP.json" && say "   the darpan state JSON of the fixed copy kept at /tmp/s502_state_darpan_$STAMP.json (for the PC's rendered check)"
say "[6/13] walk_s502 sections 1-5 and 7 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-9: re-check, backups ------------------------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/13] the build lock is not held by $KIT - nothing placed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [7/13] $FIN/$f moved during the walk - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[7/13] the lock is held by $KIT; the three FROM pins still stand after the walk"
say "   before: $(state_now)"
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S502_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [8/13] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[8/13] a .bak_S502_<from8> beside each of the three files, read back"
copydb "$DBF" "$FIN/finance.db.bak_S502_$STAMP" && [ -s "$FIN/finance.db.bak_S502_$STAMP" ] || { say "!! [9/13] database backup failed - nothing placed (the lock stays: $KIT)"; rm -rf "$WALK"; exit 1; }
say "[9/13] $FIN/finance.db.bak_S502_$STAMP made by the backup API ($(stat -c %s "$FIN/finance.db.bak_S502_$STAMP") bytes)"
# ---- 10: place -------------------------------------------------------------------------------------------------------------------------
putfile() { \cp -p "$1" "$2.s502_new" && mv -f "$2.s502_new" "$2"; }      # a rename: a running reader never sees half a file
restore() {
  say "!! RED after placing ($1) - restoring the three files byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  say "   DATA: the two columns and any data fix already applied STAY (they are the brief's data change; reversed only if the owner says so, from finance.db.bak_S502_$STAMP)"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
for f in "${ORDER[@]}"; do cmp -s "$FIN/$f" "$R/new/$f" || restore "the placed $f is not the walk's file"; done
say "[10/13] the three files placed by rename; md5 read back = the three TO pins; each byte-identical to the walk's NEW copy"
# ---- 11: the data fixes ----------------------------------------------------------------------------------------------------------------
cp -p "$KDIR/fix_s502.py" "$WALK/fix_s502_copy.py"
DATA="$( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B "$WALK/fix_s502_copy.py" --db "$DBF" --finance "$FIN" 2>&1 )"; rc=$?
echo "$DATA" | grep -v '^FIX_S502_JSON' | mask | cut -c1-700 | sed 's/^/   /'
echo "$DATA" | grep -q '^FIX_S502_JSON .*"ok": true' && [ "$rc" = 0 ] || restore "the data fixes (fix_s502.py)"
say "[11/13] the data fixes on the live database: ensure's two columns; A TRUECEPROL OD; B TYRO BR (keyed, idempotent -- what each did is above)"
# ---- 12: restart, health, read-back ------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
c=$(health http://127.0.0.1:8106/finance/stockmatch); say "         /finance/stockmatch $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated page answered $c"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
mkdir -p "$R/rb/nosso" && copydb "$DBF" "$R/rb/now.db" || restore "no copy of the database for the read-back"
RB="$( cd "$FIN" && FINANCE_DB="$R/rb/now.db" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" timeout 300 "$VPY" -B - <<'PYEOF' 2>&1
import sys
sys.path.insert(0, ".")
import finance_app as fa
c = fa.app.test_client()
H = {"X-Clinic-User": "darpan", "X-Clinic-Role": "staff"}
r = c.get("/finance/stockmatch", headers=H)
h = r.get_data(as_text=True)
j = c.get("/finance/stockmatch/api/state", headers=H).get_json(silent=True) or {}
W = j.get("watch") or {}
rows = [(x.get("item"), x.get("qty"), x.get("qty_hi"), x.get("can_fix")) for x in (W.get("roster") or {}).get("items", [])]
losses = [l.get("text_hi") for l in (W.get("losses") or [])]
print("as darpan: /finance/stockmatch %s, 'Aaj ki ginti' on it %s, 'Galat likha? Badlo' in the script %s" % (r.status_code, "Aaj ki ginti" in h, "Galat likha? Badlo" in h))
print("as darpan: today's roster %s" % rows)
print("as darpan: the last 7 days' loss lines %s" % losses)
ok = (r.status_code == 200 and W.get("ok") is True and any(x[0] == "TRUECEPROL OD" and x[1] == 137 for x in rows)
      and not any("TYRO BR" in (l or "") and "70 patte" in (l or "") for l in losses))
print("READ_BACK %s" % ("OK" if ok else "RED"))
PYEOF
)"
echo "$RB" | mask | cut -c1-700 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the placed files on a copy of the database as it is now"
say "[12/13] $SVC active (restarted once, $T0); healthz 200; the gated page answers the gate; no error in its journal; read back as darpan: TRUECEPROL OD 137 on today's list, no TYRO BR 70:7 line"
# ---- 13: nothing else moved -------------------------------------------------------------------------------------------------------------
for f in "${!RO[@]}"; do [ "$(m5 "$f")" = "${RO0[$f]}" ] || restore "$f moved -- read only for this kit"; done
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[13/13] nothing else moved (the four read-only files, the eleven must-not-move files, the crontab); healthz 200"
say "   after : $(state_now)"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "   done · healthz 200 · backups: $FIN/finance.db.bak_S502_$STAMP and a .bak_S502_<from8> beside each of the three files · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
