#!/bin/bash
# =============================================================================
#  install_S488_DATES_AND_WAITS.sh · kit S488_DATES_AND_WAITS (Sanjeevni, session 296, 06-Oct-2026; F-753, F-754; no D-number)
#  Dates compared as dates; a waiting card says since when and for what; the owner's own Marg lists become his duties; a learnt item
#  name can be struck; (the medical PC's marg_watch.py is packed here, NOT placed -- deliver_S488.ps1, run by the owner later).
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S488_DATES_AND_WAITS):
#    bash <kit>/install_S488_DATES_AND_WAITS.sh     (DRY=1: every gate, the build, the compiles, the whole walk and the measures on
#                                                    scratch copies; nothing placed, nothing written)
#
#  PATCHED ON THE BOX from the live bytes (make_s488.py; every anchor exactly once; FROM -> TO pinned), NINE files of /root/finance:
#     stock_app.py darpan_app.py owner_sheets.py (the parent's: one statement) stock_watch.py shelf_figure.py amir_day.py item_check.py
#     purchase_app.py (the Items check block only) reports_tile.py
#  DATA (finance.db, backed up by the backup API first): four setting rows seeded (INSERT OR IGNORE); the table s454_item_name_struck
#  (item_check.ensure); s454_shelf_gap re-judged ONCE (rejudge_s488.py: flags the filed vouchers explain are cleared; idempotent).
#  RESTARTS clinic-finance once.
#  NOT TOUCHED (md5 before = after, or the install is undone): finance_app.py, portal.py, tile_grants.json, aaj_kaam.py, aaj_duties.json,
#  owner_console.py, the twelve files S486 parked, the crontab. READ ONLY: /root/marg_ingest/marg_ingest.py (Part F: its pin is confirmed).
# =============================================================================
set -u
KIT="S488_DATES_AND_WAITS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DUTYMAP="$KDIR/DUTY_MAP.json"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp; ING=/root/marg_ingest
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s488_walk_$STAMP"
SVC=clinic-finance
ORDER=(stock_app.py darpan_app.py owner_sheets.py stock_watch.py shelf_figure.py amir_day.py item_check.py purchase_app.py reports_tile.py)
declare -A FROM=( [stock_app.py]=7e159de737c0ec03cea890053f1bcd58 [darpan_app.py]=5bfabbecf1e0fbf86ff142e3cd07543e
                  [owner_sheets.py]=8b1aea31fc1d7dd231fbb45f87c2c6d2 [stock_watch.py]=6d4d660f20a0e441fb1082597e5fd96c
                  [shelf_figure.py]=23c34ebb1149996e1053c26573077460 [amir_day.py]=709f20c1078cbcb36fc1108e452c40c1
                  [item_check.py]=9000e3768086e0935d88bec8c8b1cd07 [purchase_app.py]=254b77939ca40d20e46509a678bcb5d8
                  [reports_tile.py]=ea15aacbb6a00131d3f02664b0c1df42 )
declare -A TO
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/aaj_kaam.py" "$FIN/aaj_duties.json" "$FIN/owner_console.py"
      "$FIN/order_rules.py" "$FIN/porders_s454.py" "$FIN/porders.py" "$FIN/porders.html" "$FIN/darpan_kal.py" "$FIN/darpan_kal.html"
      "$FIN/order_sheet.py" "$FIN/order_sheet_pdf.py" "$FIN/finance_approvals.html" "$FIN/spine/spine_read.py" "$FIN/spine/order_rehearsal.py"
      "$FIN/spine/selftest_spine.py" "$ING/marg_ingest.py")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
state_now() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
s=dict(c.execute(\"SELECT key, value FROM setting WHERE key IN ('amir.proof_wait_hours','amir.refused_keep_hours','owner.salt_list_days','owner.item_lists_days')\").fetchall())
t=c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='s454_item_name_struck'\").fetchone()[0]
g=c.execute('SELECT as_on, SUM(flagged) FROM s454_shelf_gap GROUP BY as_on ORDER BY as_on DESC LIMIT 4').fetchall()
print('settings %s · table s454_item_name_struck=%s · shelf-gap flags by closing (newest first) %s' % (s or 'none', 'yes' if t else 'no', g))
" "$DBF"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/13] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/13] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/13] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DUTYMAP" "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json"; do
  [ -f "$k" ] || { say "!! [1/13] $k must be reachable - nothing installed"; exit 1; }
done
"$SPY" -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); sys.exit(0 if d.get('version')==8 and d.get('kit')=='$KIT' else 1)" "$DUTYMAP" \
  || { say "!! [1/13] the kit's DUTY_MAP.json is not v8 of $KIT - nothing installed"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [1/13] PINS.sh missing - nothing installed"; exit 1; }
MI="$(m5 "$ING/marg_ingest.py")"
say "[1/13] kit gates green (SUMS, KIT_ID, the venv's flask, the duty map v8 of this kit, the databases, the portal)"
say "   Part F (read only): /root/marg_ingest/marg_ingest.py is $MI -- $( [ "$MI" = 828c4dad6b159207b034d8129aed3ab7 ] && echo 'the pin 828c4dad: S482 closed both lines (confirmed)' || echo 'NOT the pin 828c4dad (reported; nothing done)')"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the nine files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   $(state_now)"; exit 0
fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/13] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/13] the nine live files at their FROM pins"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s488.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/13] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/13] live bytes + anchored edits give the nine pinned files"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/13] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/13] the nine built files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
  [ -f "$R/$side/finance_app.py" ] && [ -f "$R/$side/aaj_duties.json" ] || { say "!! [5/13] no scratch copy of the finance folder - nothing installed"; rm -rf "$WALK"; exit 1; }
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/new/$f"; done
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/13] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
TS="$( cd "$R/new" && timeout 600 "$VPY" -B reports_tile.py 2>&1 | tail -1 )"
TO_="$( cd "$R/old" && timeout 600 "$VPY" -B reports_tile.py 2>&1 | tail -1 )"
[ "$TS" = "$TO_" ] || { say "!! [5/13] reports_tile.py's own selftest on the built file says '$TS', the box as it is says '$TO_' - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/13] scratch copies: the finance folder twice (NEW with the nine built files, OLD as it is), the portal's code; finance.db, assets.db and spine.db by the backup API; reports_tile.py's own selftest on the built file: $(echo "$TS" | cut -c1-80) (the same line as the box as it is)"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s488.py" --kit "$KDIR" --work "$R/w" --fin-new "$R/new" --fin-old "$R/old" --por "$R/por" \
         --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1500 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S488 GREEN" || { say "!! [6/13] walk_s488 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/13] walk_s488 sections 1-7 green on scratch copies; every named control red on the old files (above)"
# ---- the measures the brief asks, on a fresh scratch copy (read only of the live data)
M="$R/measure"; mkdir -p "$M" && copydb "$DBF" "$M/m.db" || { say "!! [6/13] no copy for the measures - nothing installed"; rm -rf "$WALK"; exit 1; }
MOUT="$( { cd "$M" && export SPINE_DB="$R/scratch_spine.db"
  "$SPY" -B "$KDIR/rejudge_s488.py" figures --db "$M/m.db" --fin "$R/old" > "$M/fig_old.txt" 2>&1
  "$SPY" -B "$KDIR/rejudge_s488.py" figures --db "$M/m.db" --fin "$R/new" > "$M/fig_new.txt" 2>&1
  "$SPY" - "$M/fig_old.txt" "$M/fig_new.txt" <<'PYEOF'
import json, sys
o = json.loads(open(sys.argv[1]).read().split("S488JSON ", 1)[1])
n = json.loads(open(sys.argv[2]).read().split("S488JSON ", 1)[1])
mv = [(k, o[k]["shelf"], n[k]["shelf"]) for k in sorted(o) if o[k]["shelf"] != n[k]["shelf"]]
print("shelf figures of the %d items with a filed voucher, figures() OLD -> NEW: %d moved%s" % (len(o), len(mv), "".join("\n      %s: %s -> %s" % x for x in mv)))
PYEOF
  "$SPY" -B "$KDIR/rejudge_s488.py" rejudge --db "$M/m.db" --fin "$R/new" | grep -v '^S488JSON'
  "$SPY" -B "$KDIR/rejudge_s488.py" stay --db "$M/m.db" --fin "$R/new" | sed 's/^S488JSON /the flags that stay (first-flagged at their own closing), and how many the spine explains NOW: /'; } 2>&1 )"
echo "$MOUT" | mask | cut -c1-2400 | sed 's/^/   /'
echo "$MOUT" | grep -q "^closing " || { say "!! [6/13] the measures did not run - nothing installed"; rm -rf "$WALK"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/13] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [7/13] $FIN/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "   before: $(state_now)"
copydb "$DBF" "$FIN/finance.db.bak_S488_$STAMP" && [ -s "$FIN/finance.db.bak_S488_$STAMP" ] || { say "!! [7/13] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S488_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [7/13] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[7/13] the lock is held by $KIT; finance.db.bak_S488_$STAMP made (backup API); a .bak_S488_<from8> beside each of the nine files, read back"
putfile() { \cp -p "$1" "$2.s488_new" && mv -f "$2.s488_new" "$2"; }      # a rename: a running reader never sees half a file
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$FIN/$f"; done
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  say "   DATA: the four setting rows and the table s454_item_name_struck, if made, stay (the old files do not read them); a re-judge, if run,"
  say "   stays in s454_shelf_gap -- the database backup finance.db.bak_S488_$STAMP holds the rows as they were (used only if the report says why)"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[8/13] the nine files placed, each by a rename; md5 read back = the nine TO pins"
DATA="$( cd "$FIN" && "$SPY" -B - "$DBF" <<'PYEOF' 2>&1
import sqlite3, sys
sys.path.insert(0, ".")
import item_check
con = sqlite3.connect(sys.argv[1], timeout=60)
ROWS = (("amir.proof_wait_hours", "48", "S488: hours a count's voucher proof may wait before the owner's warn line"),
        ("amir.refused_keep_hours", "36", "S488: hours a refused report stays on the owner's Needs-you list (kept past midnight)"),
        ("owner.salt_list_days", "8", "S488: days after which the owner's salt-wise list from Marg is overdue"),
        ("owner.item_lists_days", "35", "S488: days after which his category-wise list or item list from Marg is overdue"))
n = 0
for k, v, note in ROWS:
    n += con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note)).rowcount or 0
con.commit()
item_check.ensure(con)
con.commit()
print("settings seeded: %d new of 4 -- %s" % (n, dict(con.execute("SELECT key, value FROM setting WHERE key IN (%s)" % ",".join("?" * 4), [r[0] for r in ROWS]).fetchall())))
print("item_check.ensure: s454_item_name_struck %s; learnt names %d" % ("made" if con.execute("SELECT 1 FROM sqlite_master WHERE name='s454_item_name_struck'").fetchone() else "MISSING",
                                                                           con.execute("SELECT COUNT(*) FROM s454_item_name").fetchone()[0]))
print("DATA_OK")
PYEOF
)"; rc=$?
echo "$DATA" | mask | sed 's/^/   /'
echo "$DATA" | grep -q "^DATA_OK" && [ "$rc" = 0 ] || restore "the settings / item_check.ensure"
RJ="$( cd "$FIN" && SPINE_DB="$SPD" "$SPY" -B "$KDIR/rejudge_s488.py" rejudge --db "$DBF" --fin "$FIN" 2>&1 )"; rc=$?
echo "$RJ" | grep -v '^S488JSON' | sed 's/^/   /'
echo "$RJ" | grep "^S488JSON" | cut -c1-1800 | sed 's/^/   /'
echo "$RJ" | grep -q "^closing " && [ "$rc" = 0 ] || restore "the re-judge of s454_shelf_gap"
say "[9/13] four settings seeded (INSERT OR IGNORE); s454_item_name_struck made; s454_shelf_gap re-judged once (counts per closing above)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/stock/page/now /finance/stock/api/now /finance/purchase/page/items /finance/amir; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[10/13] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
for f in "${ORDER[@]}"; do cmp -s "$FIN/$f" "$R/new/$f" || restore "the placed $f is not the walk's file"; done
mkdir -p "$R/rb/nosso" "$R/rb/nomarg" && copydb "$DBF" "$R/rb/now.db" || restore "no copy of the database for the read-back"
RB="$( cd "$R/new" && FINANCE_DB="$R/rb/now.db" ASSETS_DB="$R/scratch_assets.db" SPINE_DB="$R/scratch_spine.db" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" \
       MARG_INGEST_DIR="$R/rb/nomarg" RING_PORTAL_DIR="$R/rb/nosso" ORDER_PUSH_STUB="$R/rb/pushes.jsonl" DUTY_MAP_JSON="$DUTYMAP" timeout 300 "$VPY" -B - "$DBF" "$DUTYMAP" <<'PYEOF' 2>&1
import json, re, sqlite3, sys
sys.path.insert(0, ".")
import finance_app as fa
c = fa.app.test_client()
H = lambda u, r: {"X-Clinic-User": u, "X-Clinic-Role": r}
db = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
days = sorted({r[0] for r in db.execute("SELECT DISTINCT as_on FROM stock_feed")}, key=lambda s: s[6:10] + s[3:5] + s[0:2])
n = c.get("/finance/stock/api/now", headers=H("manoj", "doctor"))
j = n.get_json(silent=True) or {}
print("as manoj: Stock now %s; as_on %s (the newest day by date in stock_feed: %s)" % (n.status_code, j.get("as_on"), days[-1] if days else None))
r = c.get("/finance/stock/api/readiness", headers=H("manoj", "doctor")).get_json(silent=True) or {}
print("   readiness: %s" % ((r.get("stock") or {}).get("line")))
print("   warnings: %s" % [w for w in (r.get("warnings") or []) if w.startswith("The stock figure")])
p = c.get("/finance/purchase/page/items", headers=H("manoj", "doctor"))
t = p.get_data(as_text=True)
st = re.search(r"<summary>(Struck: \d+)</summary>", t)
print("as manoj: Items check %s; Wrong buttons %d; '%s'" % (p.status_code, t.count(">Wrong</button>"), st.group(1) if st else "no Struck line"))
s = c.post("/finance/purchase/api/items/strike", json=dict(supplier_norm="x", scan_norm="y", do="strike"), headers=H("amir", "staff"))
print("as amir: POST api/items/strike %s (refused)" % s.status_code)
m = json.load(open(sys.argv[2], encoding="utf-8"))
due = {d["id"]: tuple(db.execute(d["due_sql"]).fetchone()) for d in m["duties"] if d["id"] in ("manoj.salt_list", "manoj.item_lists")}
print("the two new duties' due_sql on the LIVE database (read only): %s" % due)
ok = (n.status_code == 200 and j.get("as_on") == (days[-1] if days else None) and p.status_code == 200 and t.count(">Wrong</button>") > 0
      and s.status_code in (302, 401, 403) and len(due) == 2)
print("READ_BACK %s" % ("OK" if ok else "RED"))
PYEOF
)"
echo "$RB" | mask | cut -c1-900 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the placed files on the database as it is now"
say "[11/13] read back (the placed files, a copy of the database as it is now): Stock now names the newest day; the Items check page carries Wrong; a staff login is refused on the strike"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[12/13] nothing else moved (finance_app.py, portal.py, tile_grants.json, aaj_kaam.py, aaj_duties.json, owner_console.py, S486's twelve parked files, marg_ingest.py, the crontab); healthz 200"
say "   after : $(state_now)"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "[13/13] done · healthz 200 · backups: $FIN/finance.db.bak_S488_$STAMP and a .bak_S488_<from8> beside each of the nine files"
say "$KIT: DONE"
