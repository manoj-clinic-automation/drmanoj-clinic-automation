#!/bin/bash
# =============================================================================
#  install_S485_DARPAN_ORDER_TAB.sh · kit S485_DARPAN_ORDER_TAB (Sanjeevni, session 295, 05-Oct-2026; D677)
#  Darpan reviews the system's order list on his own page (the second tab of Kal ka hisaab), from 09:30; his Pakka is the hand-over to
#  reception. The Marg sheet road stays, one setting away.
#
#  Run by (on the VPS, holding the build lock /root/deploy/.claude_code_build.lock with owner S485_DARPAN_ORDER_TAB):
#    bash <kit>/install_S485_DARPAN_ORDER_TAB.sh       (DRY=1: every gate, the build, the compiles and the whole walk; nothing placed.
#                                                       DUTYMAP=<file>: the duty map the walk reads -- default this kit's own, v7.)
#
#  PATCHED ON THE BOX from the live bytes (make_s485.py; every anchor exactly once; FROM -> TO pinned), SIX files of /root/finance:
#     darpan_kal.py  darpan_kal_schema.sql  darpan_kal.html  order_sheet.py  order_rules.py  porders_s454.py
#  DATA (finance.db, backed up by the backup API first): the new table order_darpan_edit; the setting order.darpan_list_time seeded
#  (09:30); and order.source = darpan, written through order_rules._set_setting (audited in order_rule_audit).
#  RESTARTS clinic-finance once.
#  NOT TOUCHED (md5 before = after, or the install is undone): finance_app.py, porders.py, purchase_app.py, shelf_figure.py,
#  spine/spine_read.py, /root/portal/portal.py, /root/portal/tile_grants.json, the crontab.
# =============================================================================
set -u
KIT="S485_DARPAN_ORDER_TAB"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DUTYMAP="${DUTYMAP:-$KDIR/DUTY_MAP.json}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp
DBF="${FINANCE_DB:-$FIN/finance.db}"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s485_walk_$STAMP"
SVC=clinic-finance
ORDER=(darpan_kal.py darpan_kal_schema.sql darpan_kal.html order_sheet.py order_rules.py porders_s454.py)
declare -A FROM=( [darpan_kal.py]=911cf637a288fad85c75e54227149633 [darpan_kal_schema.sql]=ecc6f0c53db4ea7e48bf8e3b1120e6b4
                  [darpan_kal.html]=c20ab05d8484e37a667ddae32a4c792b [order_sheet.py]=a5408df0fac852391d5845c5ae4d8865
                  [order_rules.py]=dac12be4c4a537d7ad2e4584a3423e6a [porders_s454.py]=3681622b11043116f40bc0d4c3b557ad )
declare -A TO
declare -A RO=( [$FIN/porders.py]=a5a823bf30661a4bf65ced39b2355500 [$FIN/purchase_app.py]=254b77939ca40d20e46509a678bcb5d8
                [$FIN/spine/spine_read.py]=712a1e4ef827f6be4e8b23415c3ceb62 [$FIN/shelf_figure.py]=23c34ebb1149996e1053c26573077460 )
NOTT=("$FIN/finance_app.py" "$FIN/porders.py" "$FIN/purchase_app.py" "$FIN/shelf_figure.py" "$FIN/spine/spine_read.py" "$POR/portal.py" "$POR/tile_grants.json")
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
state_now() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
g=lambda k: (c.execute('SELECT value FROM setting WHERE key=?',(k,)).fetchone() or [None])[0]
t=c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='order_darpan_edit'\").fetchone()[0]
p=dict(c.execute(\"SELECT status, COUNT(*) FROM order_proposal WHERE day=date('now','localtime') GROUP BY 1\").fetchall())
print('order.source=%s · order.darpan_list_time=%s · table order_darpan_edit=%s · the proposals of today by status: %s' % (g('order.source'), g('order.darpan_list_time'), 'yes' if t else 'no', p))
" "$DBF"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/13] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/13] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/13] the venv python lacks flask; nothing installed"; exit 1; }
for k in "$DUTYMAP" "$DBF" "$ADB" "$SPD" "$FIN/spine/order_rules.json"; do
  [ -f "$k" ] || { say "!! [1/13] $k must be reachable - nothing installed"; exit 1; }
done
. "$KDIR/PINS.sh" || { say "!! [1/13] PINS.sh missing - nothing installed"; exit 1; }
for f in "${!RO[@]}"; do
  [ "$(m5 "$f")" = "${RO[$f]}" ] || { say "!! [1/13] $f is $(m5 "$f"), not the brief's pin ${RO[$f]} (read only here; this kit was walked against that file) - nothing installed"; exit 1; }
done
say "[1/13] kit gates green (SUMS, KIT_ID, the venv's flask, the duty map v7 of this kit, the databases, the spine's order_rules.json; porders.py, purchase_app.py, spine_read.py and shelf_figure.py at the brief's pins)"
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then
  say "-- ALREADY INSTALLED: the six files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   $(state_now)"; exit 0
fi
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/13] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing installed"; exit 1; }
done
declare -A NT0; for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/13] the six live files at their FROM pins"
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s485.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [3/13] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "[3/13] live bytes + anchored edits give the six pinned files"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do case "$f" in *.py) cp -p "$WALK/built/$f" "$WALK/cc/built_$f";; esac; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/13] compile on both pythons failed - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
JSN="not checked here (no node on this box): the page is run by the walk's own reading and by a browser at build time"
if command -v node >/dev/null 2>&1; then
  "$SPY" -c "import re,sys; h=open(sys.argv[1],encoding='utf-8').read(); open(sys.argv[2],'w',encoding='utf-8').write(re.search(r'<script>(.*)</script>', h, re.S).group(1))" "$WALK/built/darpan_kal.html" "$WALK/cc/page.js"
  node --check "$WALK/cc/page.js" 2>/dev/null && JSN="parses (node --check)" || { say "!! [4/13] the page's script does not parse - nothing installed"; rm -rf "$WALK"; exit 1; }
fi
say "[4/13] the four built .py compile on /usr/bin/python3 and the venv python (a scratch copy); the page's script: $JSN"
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
  [ -f "$R/$side/finance_app.py" ] && [ -f "$R/$side/spine/order_rules.json" ] || { say "!! [5/13] no scratch copy of the finance folder - nothing installed"; rm -rf "$WALK"; exit 1; }
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/new/$f"; done
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/13] no scratch copies - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/13] scratch copies: the finance folder twice (NEW with the six built files, OLD as it is); finance.db, assets.db and spine.db by the backup API"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s485.py" --work "$R/w" --fin-new "$R/new" --fin-old "$R/old" --db "$R/scratch.db" --adb "$R/scratch_assets.db" \
         --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | cut -c1-1500 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S485 GREEN" || { say "!! [6/13] walk_s485 red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[6/13] walk_s485 sections 1-8, 10 and the machine half of 9 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/13] the build lock is not held by $KIT - nothing installed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [7/13] $FIN/$f moved during the walk - nothing installed"; rm -rf "$WALK"; exit 1; }; done
say "   before: $(state_now)"
copydb "$DBF" "$FIN/finance.db.bak_S485_$STAMP" && [ -s "$FIN/finance.db.bak_S485_$STAMP" ] || { say "!! [7/13] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S485_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [7/13] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[7/13] the lock is held by $KIT; finance.db.bak_S485_$STAMP made (backup API); a .bak_S485_<from8> beside each of the six files, read back"
putfile() { \cp -p "$1" "$2.s485_new" && mv -f "$2.s485_new" "$2"; }      # a rename: the ten-minute tick never reads half a file
SRC0=""
set_source() { ( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B -c "
import sqlite3, sys
sys.path.insert(0, '.')
import order_rules as OR
con = sqlite3.connect(sys.argv[1], timeout=60); con.row_factory = sqlite3.Row
OR._set_setting(con, 'order.source', sys.argv[2], sys.argv[3]); con.commit()
print(OR._setting(con, 'order.source', ''))
" "$DBF" "$1" "$2" ); }
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$FIN/$f"; done
  if [ -n "$SRC0" ]; then say "   order.source put back: $(set_source "$SRC0" "S485 install (undone)" 2>&1 | tail -1)"; fi
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  say "   DATA: the table order_darpan_edit and the setting order.darpan_list_time, if made, stay (the old files read neither); the database backup stays"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[8/13] the six files placed, each by a rename; md5 read back = the six TO pins"
# ---- the data: the table, the list time, and the switch (the owner's word of 05-Oct 12:1x is the OK)
DATA="$( cd "$FIN" && FINANCE_DB="$DBF" "$VPY" -B - "$DBF" <<'PYEOF' 2>&1
import re, sqlite3, sys
sys.path.insert(0, ".")
import order_rules as OR
con = sqlite3.connect(sys.argv[1], timeout=60)
con.row_factory = sqlite3.Row
con.executescript(open("darpan_kal_schema.sql", encoding="utf-8").read())
OR.ensure(con)
lt = OR._setting(con, "order.darpan_list_time", "")
if not re.match(r"^([01]\d|2[0-3]):[0-5]0$", lt):
    print("LIST_TIME_REFUSED %r" % lt)
    sys.exit(3)
before = OR._setting(con, "order.source", "") or "marg_sheet"
OR._set_setting(con, "order.source", "darpan", "S485 install")
con.commit()
a = con.execute("SELECT at, who, field, old, new FROM order_rule_audit WHERE field='order.source' ORDER BY id DESC LIMIT 1").fetchone()
print("SOURCE_BEFORE %s" % before)
print("table order_darpan_edit: %s; order.darpan_list_time = %s; order.source %s -> %s (audit: %s)" % (
    "made" if con.execute("SELECT 1 FROM sqlite_master WHERE name='order_darpan_edit'").fetchone() else "MISSING", lt, before, OR._setting(con, "order.source", ""), tuple(a) if a else None))
print("DATA_OK")
PYEOF
)"; rc=$?
echo "$DATA" | grep -v '^SOURCE_BEFORE' | sed 's/^/   /'
SRC0="$(echo "$DATA" | awk '/^SOURCE_BEFORE/{print $2}')"
echo "$DATA" | grep -q "^DATA_OK" && [ "$rc" = 0 ] || restore "the table / the list time / the switch (a list time that is not HH:M0 is refused)"
say "[9/13] order_darpan_edit made; order.darpan_list_time seeded; order.source = darpan through order_rules._set_setting (audited)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/darpan/kal /finance/darpan/kal/api/order /finance/porders; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[10/13] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- read back: the placed files (the same bytes as the walk's NEW copy) on a copy of the database AS IT IS NOW, signed in as each reader
for f in "${ORDER[@]}"; do cmp -s "$FIN/$f" "$R/new/$f" || restore "the placed $f is not the walk's file"; done
mkdir -p "$R/rb/nosso" "$R/rb/nomarg" && copydb "$DBF" "$R/rb/now.db" || restore "no copy of the database for the read-back"
RB="$( cd "$R/new" && FINANCE_DB="$R/rb/now.db" ASSETS_DB="$R/scratch_assets.db" SPINE_DB="$R/scratch_spine.db" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" \
       MARG_INGEST_DIR="$R/rb/nomarg" RING_PORTAL_DIR="$R/rb/nosso" ORDER_PUSH_STUB="$R/rb/pushes.jsonl" timeout 300 "$VPY" -B - <<'PYEOF' 2>&1
import html, re, sys
sys.path.insert(0, ".")
import finance_app as fa
c = fa.app.test_client()
H = lambda u, r: {"X-Clinic-User": u, "X-Clinic-Role": r}
p = c.get("/finance/darpan/kal", headers=H("manoj", "doctor"))
t = p.get_data(as_text=True)
print("as manoj: /finance/darpan/kal %s; the tab's marker on the page: %s" % (p.status_code, "yes" if 'id="tabOrder">आज का ऑर्डर<' in t else "NO"))
a = c.get("/finance/darpan/kal/api/order", headers=H("manoj", "doctor"))
j = a.get_json(silent=True) or {}
print("as manoj: api/order %s; source %s; list time %s; opened %s; %s supplier(s), %s line(s): %s%s" % (
    a.status_code, j.get("source"), j.get("list_time"), j.get("opened"), j.get("n_suppliers"), j.get("n_lines"),
    ", ".join("%s %d (%s)" % (b["display"], b["n"], b["status"]) for b in j.get("suppliers") or []) or "आज कोई ऑर्डर नहीं बनता",
    "" if j.get("opened") else " -- the list opens at %s" % j.get("list_time")))
d = c.get("/finance/darpan/kal/api/order", headers=H("darpan", "staff"))
print("as darpan: api/order %s; editable %s" % (d.status_code, (d.get_json(silent=True) or {}).get("editable")))
o = c.get("/finance/porders/s454/order?all=1", headers=H("shivani", "staff"))
h = o.get_data(as_text=True)
m = re.search(r'id="whose">([^<]*)<', h)
print("as shivani (a sender): 'Order karna hai' %s; heading '%s'; supplier cards now: %s (a proposal's supplier comes only after Darpan's Pakka)" % (
    o.status_code, html.unescape(m.group(1)) if m else "", sorted(set(html.unescape(x) for x in re.findall(r'<div class="card" data-sn="([^"]*)"', h))) or "none"))
ok = p.status_code == 200 and 'id="tabOrder"' in t and a.status_code == 200 and j.get("ok") and j.get("source") == "darpan" and d.status_code == 200 and o.status_code == 200
print("READ_BACK %s" % ("OK" if ok else "RED"))
PYEOF
)"
echo "$RB" | cut -c1-900 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the placed files on the database as it is now"
say "[11/13] read back (the placed files, a copy of the database as it is now): the page serves the tab, the API answers, reception's cards wait for a Pakka"
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[12/13] nothing else moved (finance_app.py, porders.py, purchase_app.py, shelf_figure.py, spine_read.py, portal.py, tile_grants.json, the crontab); healthz 200"
say "   after : $(state_now)"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "   THE WAY BACK, one tap: your Purchase orders page -> the card 'Who decides the order' -> 'Change to Darpan's sheet'   (or one setting: order.source = marg_sheet)"
say "[13/13] done · healthz 200 · backups: $FIN/finance.db.bak_S485_$STAMP and a .bak_S485_<from8> beside each of the six files"
say "$KIT: DONE"
