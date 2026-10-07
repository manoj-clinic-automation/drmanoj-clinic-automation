#!/bin/bash
# =============================================================================
#  install_S494_AMIR_JOBS_NOTICE_FLAGS.sh · kit S494_AMIR_JOBS_NOTICE_FLAGS (Sanjeevni, session 299, 07-Oct-2026; D686; F-765, F-767, F-771)
#  Amir's one-time Marg jobs on his own Marg sudhar card; the order sheet's arrival notice sent by the tick (the process that can send it);
#  a stock flag judged again when its reports arrive; one spot-count line on the owner's list, not one a day.
#
#  Run by (on the VPS):   bash <kit>/install_S494_AMIR_JOBS_NOTICE_FLAGS.sh
#     DRY=1 : every gate, the build, the compiles and the whole walk on scratch copies (the empty table made on the COPY only);
#             no lock, no backup, nothing placed, nothing written to the live database.
#
#  THE ORDER IS THE BRIEF'S (4.7, a ruled deviation from CLAUDE.md's usual one): the duty map read from the server's clone carries a
#  due_sql on the new table amir_job, so the table must exist before any reader can ask for it --
#     1 the build lock  ·  2 finance.db.bak_S494_<stamp> (backup API)  ·  3 CREATE TABLE IF NOT EXISTS amir_job on the live database
#     then the gates, the pin check, the build, the compile on both pythons, the walk (on copies taken AFTER step 3), the file backups,
#     the placing (md5 read back), the data (settings, the eight jobs, one refresh), ONE restart of clinic-finance, healthz, the read-back.
#  PATCHED ON THE BOX from the live bytes (make_s494.py; every anchor exactly once; FROM -> TO pinned): order_sheet.py stock_watch.py
#  shelf_figure.py amir_day.py (/root/finance). READ ONLY (md5 before = after): order_rules.py stock_app.py purchase_app.py
#  sanjeevni_approvals.py spine/spine_read.py /root/portal/ring_common.py /root/assetapp/asset_register.py.
#  NOT TOUCHED (md5 before = after, or the install is undone): finance_app.py portal.py tile_grants.json aaj_kaam.py aaj_kaam.html
#  aaj_duties.json owner_console.py packs.py porders_s454.py darpan_kal.py and the crontab.
#  Every python this script starts carries ORDER_PUSH_STUB (a scratch file) and a scratch RING_PORTAL_DIR: nothing reaches a real phone.
# =============================================================================
set -u
KIT="S494_AMIR_JOBS_NOTICE_FLAGS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DUTYMAP="${S494_DUTY_MAP:-$KDIR/../../claude_code_briefs/DUTY_MAP.json}"
MAP9=2016244829b4c70c00f1c59b0250ee35
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s494_walk_$STAMP"
SVC=clinic-finance
DDL494="CREATE TABLE IF NOT EXISTS amir_job (id INTEGER PRIMARY KEY, key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, subject TEXT NOT NULL, text_hi TEXT, sub_hi TEXT, created_at TEXT NOT NULL, created_by TEXT, show_from TEXT, said_at TEXT, said_by TEXT, said_what TEXT, done_at TEXT, done_how TEXT)"
ORDER=(order_sheet.py stock_watch.py shelf_figure.py amir_day.py)
declare -A FROM=( [order_sheet.py]=16f21a6515a1317e1f6e31cb0a280513 [stock_watch.py]=4fc0f6017825975e75ebacfdc2f122d2
                  [shelf_figure.py]=0d836de54672f3e624fcc763311ab22c [amir_day.py]=08d058a765278d6e119e70f8f0adeedd )
declare -A TO
declare -A RO=( ["$FIN/order_rules.py"]=ee17c1872acd0c440868a915fa5014df ["$FIN/stock_app.py"]=cc06dac9e3ab60a85d76e2409815b5af
                ["$FIN/purchase_app.py"]=c29050c18795a059e3cfbfae252efc21 ["$FIN/sanjeevni_approvals.py"]=792f4a9af1728c76e8d5a656f5662421
                ["$FIN/spine/spine_read.py"]=712a1e4ef827f6be4e8b23415c3ceb62 ["$POR/ring_common.py"]=4344b59277d94b2d11d8d7cc23328677
                ["$AST/asset_register.py"]=e774be89193472dfa4b142d85bdcc46c )
NOTT=("$FIN/finance_app.py" "$POR/portal.py" "$POR/tile_grants.json" "$FIN/aaj_kaam.py" "$FIN/aaj_kaam.html" "$FIN/aaj_duties.json"
      "$FIN/owner_console.py" "$FIN/packs.py" "$FIN/porders_s454.py" "$FIN/darpan_kal.py")
mkdir -p "$WALK/noring" || exit 1
export ORDER_PUSH_STUB="$WALK/installer_pushes.jsonl" RING_PORTAL_DIR="$WALK/noring"
unset ORDER_PUSH_NONE ORDER_TODAY ORDER_TICK ORDER_CLOCK
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
mask() { sed -E 's/[0-9]{10,}/##########/g'; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cron5() { crontab -l 2>/dev/null | md5sum | awk '{print $1}'; }
mktable() { "$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1], timeout=60); c.execute(sys.argv[2]); c.commit(); print('amir_job there: %s; rows %d' % (c.execute(\"SELECT sql FROM sqlite_master WHERE name='amir_job'\").fetchone() is not None, c.execute('SELECT COUNT(*) FROM amir_job').fetchone()[0])); c.close()" "$1" "$DDL494"; }
state_now() { "$SPY" -c "
import sqlite3,sys
c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True)
s=dict(c.execute(\"SELECT key, value FROM setting WHERE key IN ('order.sheet_notice_max_min','stock.gap_rejudge_days','amir.job_wait_days')\").fetchall())
t=c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='amir_job'\").fetchone()[0]
j=c.execute('SELECT COUNT(*), SUM(CASE WHEN done_at IS NULL AND said_at IS NULL AND show_from IS NOT NULL THEN 1 ELSE 0 END) FROM amir_job').fetchone() if t else None
g=c.execute('SELECT as_on, SUM(flagged), SUM(CASE WHEN why LIKE \"explained by a report%\" THEN 1 ELSE 0 END) FROM s454_shelf_gap GROUP BY as_on ORDER BY as_on DESC LIMIT 4').fetchall()
print('settings %s · amir_job %s (rows, open shown) %s · shelf-gap (closing, flagged, re-judged) newest first %s' % (s or 'none', 'yes' if t else 'no', j, g))
" "$DBF"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/14] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/14] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/14] PINS.sh missing - nothing done"; exit 1; }
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then                                    # read only: an install already made answers and writes nothing
  say "-- ALREADY INSTALLED: the four files are at the kit's pins; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"
  say "   $(state_now)"; rm -rf "$WALK"; exit 0
fi
# ---- 1-3: the lock, the database backup, the table (the brief's 4.7) -------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then
  say "[1-3/14] DRY RUN: no lock, no backup; the table amir_job is made on the walk's copies only"
else
  if mkdir "$LOCK" 2>/dev/null; then echo "$KIT" > "$LOCK/owner"; say "[1/14] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
  elif [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/14] the build lock is already held by $KIT"
  else say "!! [1/14] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
  copydb "$DBF" "$FIN/finance.db.bak_S494_$STAMP" && [ -s "$FIN/finance.db.bak_S494_$STAMP" ] || { say "!! [2/14] database backup failed - nothing done (the lock stays: $KIT)"; rm -rf "$WALK"; exit 1; }
  say "[2/14] $FIN/finance.db.bak_S494_$STAMP made by the backup API ($(stat -c %s "$FIN/finance.db.bak_S494_$STAMP") bytes)"
  T="$(mktable "$DBF" 2>&1)" || { say "!! [3/14] CREATE TABLE amir_job on the live database failed: $T - nothing else done"; rm -rf "$WALK"; exit 1; }
  say "[3/14] the live database: $T (empty: the map's due_sql reads (0, NULL) until the seed)"
fi
# ---- 4: gates, pins -------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || { say "!! [4/14] the venv python lacks flask; nothing placed"; rm -rf "$WALK"; exit 1; }
for k in "$DUTYMAP" "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json"; do
  [ -f "$k" ] || { say "!! [4/14] $k must be reachable - nothing placed"; rm -rf "$WALK"; exit 1; }
done
[ "$(m5 "$DUTYMAP")" = "$MAP9" ] || { say "!! [4/14] the duty map beside the kit is $(m5 "$DUTYMAP"), not v9 $MAP9 - nothing placed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [4/14] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the brief; nothing placed"; rm -rf "$WALK"; exit 1; }
done
declare -A RO0 NT0
for f in "${!RO[@]}"; do RO0[$f]="$(m5 "$f")"; done
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[4/14] gates green (SUMS, KIT_ID, the venv's flask, the duty map v9 $MAP9, the databases, the portal); the four live files at their FROM pins"
for f in $(printf '%s\n' "${!RO[@]}" | sort); do say "   read only: $f ${RO0[$f]} $( [ "${RO0[$f]}" = "${RO[$f]}" ] && echo '(the brief pin)' || echo "(NOT the brief pin ${RO[$f]}: the walk reads it as it is)")"; done
say "   import pywebpush: /usr/bin/python3 $("$SPY" -c 'import pywebpush' >/dev/null 2>&1 && echo IMPORTS || echo 'does not import'); the venv $("$VPY" -c 'import pywebpush' >/dev/null 2>&1 && echo imports || echo 'DOES NOT import')"
# ---- 5-6: build, compile ------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s494.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
for f in "${ORDER[@]}"; do [ "$(m5 "$WALK/built/$f")" = "${TO[$f]}" ] || { say "!! [5/14] the built $f is $(m5 "$WALK/built/$f"), not the kit's pin ${TO[$f]} - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "[5/14] live bytes + anchored edits give the four pinned files"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$WALK/cc/built_$f"; done
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [6/14] compile on both pythons failed - nothing placed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[6/14] the four built files and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 7-8: scratch copies (taken after step 3), the walk ------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
  [ -f "$R/$side/finance_app.py" ] && [ -f "$R/$side/aaj_duties.json" ] || { say "!! [7/14] no scratch copy of the finance folder - nothing placed"; rm -rf "$WALK"; exit 1; }
done
for f in "${ORDER[@]}"; do cp -p "$WALK/built/$f" "$R/new/$f"; done
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [7/14] no scratch copies - nothing placed"; rm -rf "$WALK"; exit 1; }
[ "${DRY:-0}" = 1 ] && { mktable "$R/scratch.db" >/dev/null || { say "!! [7/14] the table on the copy failed"; rm -rf "$WALK"; exit 1; }; }
say "[7/14] scratch copies: the finance folder twice (NEW with the four built files, OLD as it is), the portal's code; finance.db, assets.db and spine.db by the backup API (after step 3)"
WOUT="$( cd "$R" && timeout 3000 "$VPY" -B "$KDIR/walk_s494.py" --kit "$KDIR" --work "$R/w" --fin-new "$R/new" --fin-old "$R/old" --por "$R/por" \
         --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" --duty-map "$DUTYMAP" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S494 GREEN" || { say "!! [8/14] walk_s494 red - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[8/14] walk_s494 sections 1-6 green on scratch copies; every named control red on the old files (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 9-10: backups, placing ------------------------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(cat "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [9/14] the build lock is not held by $KIT - nothing placed"; rm -rf "$WALK"; exit 1; }
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [9/14] $FIN/$f moved during the walk - nothing placed"; rm -rf "$WALK"; exit 1; }; done
say "   before: $(state_now)"
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="$FIN/$f.bak_S494_${FROM[$f]:0:8}"
  \cp -p "$FIN/$f" "${BAK[$f]}" && [ "$(m5 "${BAK[$f]}")" = "${FROM[$f]}" ] || { say "!! [9/14] the backup of $f does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[9/14] the lock is held by $KIT; a .bak_S494_<from8> beside each of the four files, read back (finance.db.bak_S494_$STAMP from step 2)"
putfile() { \cp -p "$1" "$2.s494_new" && mv -f "$2.s494_new" "$2"; }      # a rename: a running reader never sees half a file
restore() {
  say "!! RED after placing ($1) - restoring every file byte-identically"
  for f in "${ORDER[@]}"; do putfile "${BAK[$f]}" "$FIN/$f"; done
  "$SPY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1], timeout=60); n=c.execute(\"UPDATE amir_job SET show_from=NULL WHERE created_by='S494'\").rowcount; c.commit(); print('   amir_job: show_from set back to NULL on %d S494 row(s) -- the map reads (0, NULL), no page shows the jobs' % n)" "$DBF" 2>&1
  systemctl restart "$SVC" || true; sleep 8
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f") (FROM ${FROM[$f]})"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  say "   DATA: the table amir_job and the setting rows stay (the old files do not read them); the database backup finance.db.bak_S494_$STAMP stays"
  rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do putfile "$WALK/built/$f" "$FIN/$f" || restore "copy $f"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back of $f"; done
say "[10/14] the four files placed, each by a rename; md5 read back = the four TO pins"
# ---- 11: the data ------------------------------------------------------------------------------------------------------------------------
DATA="$( cd "$FIN" && "$SPY" -B - "$DBF" "$DUTYMAP" <<'PYEOF' 2>&1
import json, sqlite3, sys
sys.path.insert(0, ".")
import order_sheet, amir_day
con = sqlite3.connect(sys.argv[1], timeout=60)
ROWS = (("stock.gap_rejudge_days", "7", "Stock flags: days a first flag is judged again as later reports arrive"),
        ("amir.job_wait_days", "10", "Amir's one-time Marg jobs: days before your Needs-you list names them"))
n = 0
for k, v, note in ROWS:
    n += con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, note)).rowcount or 0
con.commit()
order_sheet.ensure(con)
print("settings: %d new of 2 by the installer; order.sheet_notice_max_min by order_sheet.ensure() itself -- %s" % (n, [tuple(r) for r in con.execute(
    "SELECT key, value, note FROM setting WHERE key IN ('order.sheet_notice_max_min','stock.gap_rejudge_days','amir.job_wait_days') ORDER BY key")]))
print("seed: %s" % amir_day.s494_seed_jobs(con))
print("refresh: %d row(s) changed" % amir_day._s494_refresh(con))
for r in con.execute("SELECT key, kind, show_from IS NOT NULL, said_what, done_how FROM amir_job ORDER BY id"):
    print("   job %s (%s): shown %s, said %s, done %s" % tuple(r))
m = json.load(open(sys.argv[2], encoding="utf-8"))
d = [x for x in m["duties"] if x["id"] == "amir.marg_jobs"][0]
ro = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
print("the duty's due_sql on the live database: %s" % (tuple(ro.execute(d["due_sql"]).fetchone()),))
print("DATA_OK")
PYEOF
)"; rc=$?
echo "$DATA" | mask | sed 's/^/   /'
echo "$DATA" | grep -q "^DATA_OK" && [ "$rc" = 0 ] || restore "the settings / the seed / the refresh"
say "[11/14] three settings (two by the installer, INSERT OR IGNORE; one by order_sheet.ensure()); the jobs seeded (INSERT OR IGNORE) and refreshed once"
# ---- 12: restart, health -------------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz)
say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
for p in /finance/amir /finance/amir/step/6 /finance/approvals /finance/porders; do
  c=$(health "http://127.0.0.1:8106$p"); say "         $p $c (302/401 = the login gate, expected)"
  [ "$c" = 302 ] || [ "$c" = 401 ] || restore "a gated page answered $c ($p)"
done
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[12/14] $SVC active (restarted once, $T0); healthz 200; the gated pages answer the gate; no error in its journal"
# ---- 13: read-back on a copy of the database as it is now ----------------------------------------------------------------------------
for f in "${ORDER[@]}"; do cmp -s "$FIN/$f" "$R/new/$f" || restore "the placed $f is not the walk's file"; done
mkdir -p "$R/rb/nosso" "$R/rb/nomarg" && copydb "$DBF" "$R/rb/now.db" && copydb "$SPD" "$R/rb/spine.db" || restore "no copy of the database for the read-back"
RB="$( cd "$FIN" && FINANCE_DB="$R/rb/now.db" ASSETS_DB="$R/scratch_assets.db" SPINE_DB="$R/rb/spine.db" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" \
       MARG_INGEST_DIR="$R/rb/nomarg" DUTY_MAP_JSON="$DUTYMAP" timeout 300 "$VPY" -B - <<'PYEOF' 2>&1
import os, re, sqlite3, sys
sys.path.insert(0, ".")
import finance_app as fa
import amir_day
c = fa.app.test_client()
H = lambda u, r: {"X-Clinic-User": u, "X-Clinic-Role": r}
h = c.get("/finance/amir/step/6", headers=H("amir", "staff")).get_data(as_text=True)
lines = re.findall(r"<span class=big>([^<]*)</span>", h)
print("as amir, step 6: 'Ek baar ke kaam' %s; the job lines %s" % ("Ek baar ke kaam" in h, [x for x in lines if "vendor" in x or "bill" in x or "KEDAR" in x or "category" in x]))
d = c.get("/finance/amir/day", headers=H("manoj", "doctor")).get_data(as_text=True)
print("as manoj, Amir's day: %s" % [x for x in re.findall(r"<p class=big>([^<]*)</p>", d) if "one-time" in x])
con = sqlite3.connect(os.environ["FINANCE_DB"], timeout=60)
ol = [x["text"] for x in amir_day._s494_owner_lines(con)]
print("the owner's S494 lines: %s" % ol)
ok = ("Ek baar ke kaam" in h) and any("one-time Marg jobs" in x for x in re.findall(r"<p class=big>([^<]*)</p>", d))
print("READ_BACK %s" % ("OK" if ok else "RED"))
PYEOF
)"
echo "$RB" | mask | cut -c1-900 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read-back of the placed files on the database as it is now"
say "[13/14] read back (the placed files, a copy of the database as it is now): Amir's step 6 carries 'Ek baar ke kaam' and his jobs; the owner's view of his day names them"
# ---- 14: nothing else moved -------------------------------------------------------------------------------------------------------------
for f in "${!RO[@]}"; do [ "$(m5 "$f")" = "${RO0[$f]}" ] || restore "$f moved -- read only for this kit"; done
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[14/14] nothing else moved (the seven read-only files, finance_app.py, portal.py, tile_grants.json, aaj_kaam.py/.html, aaj_duties.json, owner_console.py, packs.py, porders_s454.py, darpan_kal.py, the crontab); healthz 200"
say "   after : $(state_now)"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
rm -rf "$WALK"
say "   done · healthz 200 · backups: $FIN/finance.db.bak_S494_$STAMP and a .bak_S494_<from8> beside each of the four files · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
