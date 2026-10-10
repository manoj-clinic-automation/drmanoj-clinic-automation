#!/bin/bash
# =============================================================================
#  install_S520_AMIR_PROOF_ANY_CLOSING.sh · kit S520_AMIR_PROOF_ANY_CLOSING (Sanjeevni, session 303, 10-Oct-2026; F-830)
#  Amir's voucher check: an item is PROVEN when the FIRST closing after the vouchers, or the NEWEST one, shows it moved by exactly its
#  vouchers -- so his card stops telling him to "correct" vouchers that were keyed right (the two L S BELT CONT GRAY UNISON belts).
#
#  Run by (on the VPS):   bash <kit>/install_S520_AMIR_PROOF_ANY_CLOSING.sh        DRY=1 : gates, build, compile, walk on scratch copies only.
#  ORDER: gate 0 (SUMS, KIT_ID, PINS; ALREADY INSTALLED) · the lock · gates (flask, the FROM pin, the must-not-move md5s recorded) · build
#  (make_s520.py) · compile both pythons · scratch copies · the walk (DRY stops) · re-check · stock_app.py.bak_S520_bfc2a40b · finance.db.bak_S520
#  (backup API, before the one read of the live card that the existing code may answer with a stage event) · place · md5 read-back · ONE restart
#  · healthz · the gated curl · the journal · the live card read once as the owner and as amir (the existing code writes the stage-A verified
#  event when the proof passes) · nothing else moved.  Red after placing -> stock_app.py restored byte-identically, restart, healthz, report.
#  No database write by the kit itself.  Every python this script starts carries ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB.
# =============================================================================
set -u
KIT="S520_AMIR_PROOF_ANY_CLOSING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN=/root/finance; POR=/root/portal; AST=/root/assetapp
DBF="$FIN/finance.db"; ADB="$AST/assets.db"; SPD="$FIN/spine/spine.db"
LOCK="/root/deploy/.claude_code_build.lock"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s520_walk_$STAMP"
SVC=clinic-finance
F=stock_app.py
FROM=bfc2a40bff0d8f0050078ea49f990eda
declare -A TO
NOTT=("$FIN/amir_day.py" "$FIN/reports_tile.py" "$FIN/order_rules.py" "$FIN/finance_app.py" "$FIN/stock_watch.py" "$FIN/stockmatch.py" "$FIN/stockmatch.html"
      "$FIN/reports_watch.py" "$FIN/reports_guide.py" "$FIN/reports_guide_pics.py" "$POR/portal.py" "$POR/tile_grants.json")
declare -A NOTT_PIN=( ["$FIN/amir_day.py"]=f1ce78e8 ["$FIN/reports_tile.py"]=01f67f4d ["$FIN/order_rules.py"]=79f21c1e ["$FIN/stock_watch.py"]=c960f6c8
                      ["$FIN/stockmatch.py"]=fc1caf44 ["$FIN/stockmatch.html"]=02826136 )
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
print('stage events of count 1: %s' % c.execute(\"SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=1 ORDER BY id\").fetchall())
" "$DBF"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [0/12] SUMS.md5 gate failed - nothing done"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [0/12] KIT_ID.txt names another kit - nothing done"; exit 1; }
. "$KDIR/PINS.sh" || { say "!! [0/12] PINS.sh missing - nothing done"; exit 1; }
if [ "$(m5 "$FIN/$F")" = "${TO[$F]}" ]; then
  say "-- ALREADY INSTALLED: $F is at the kit's pin; $SVC $(systemctl is-active "$SVC"); healthz $(health http://127.0.0.1:8106/finance/healthz)"; say "   $(state_now)"; rm -rf "$WALK"; exit 0
fi
# ---- 1: the lock -----------------------------------------------------------------------------------------------------------------------
if [ "${DRY:-0}" = 1 ]; then say "[1/12] DRY RUN: no lock, no backup, nothing placed, nothing written"
elif mkdir "$LOCK" 2>/dev/null; then echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/12] build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then say "[1/12] the build lock is already held by $KIT"
else say "!! [1/12] the build lock is held by '$(cat "$LOCK/owner" 2>/dev/null)' (made $(stat -c %y "$LOCK" 2>/dev/null)) - another build is installing; nothing done"; rm -rf "$WALK"; exit 3; fi
# ---- 2: gates --------------------------------------------------------------------------------------------------------------------------
"$VPY" -c "import flask" 2>/dev/null || { say "!! [2/12] the venv python lacks flask; nothing placed"; rm -rf "$WALK"; exit 1; }
for k in "$DBF" "$ADB" "$SPD" "$POR/portal.py" "$POR/tile_grants.json"; do [ -f "$k" ] || { say "!! [2/12] $k must be reachable - nothing placed"; rm -rf "$WALK"; exit 1; }; done
[ "$(m5 "$FIN/$F")" = "$FROM" ] || { say "!! [2/12] $FIN/$F is $(m5 "$FIN/$F"), not its FROM pin $FROM - someone changed it since the brief; nothing placed"; rm -rf "$WALK"; exit 1; }
declare -A NT0
for f in "${NOTT[@]}"; do NT0[$f]="$(m5 "$f")"; done
CRON0="$(cron5)"
say "[2/12] gates green (SUMS, KIT_ID, PINS, the venv's flask, the databases, the portal); $FIN/$F at its FROM pin $FROM"
for f in "${NOTT[@]}"; do p="${NOTT_PIN[$f]:-}"; [ -n "$p" ] && [ "${NT0[$f]:0:8}" != "$p" ] && say "   must not move: $f is ${NT0[$f]} (the brief read $p…: moved before this run -- recorded; only a change DURING this install is a fault)"; done
# ---- 3-4: build, compile ---------------------------------------------------------------------------------------------------------------
mkdir -p "$WALK/built" || exit 1
"$SPY" -B make_s520.py --finance "$FIN" --out "$WALK/built" | sed 's/^/   /'
[ "$(m5 "$WALK/built/$F")" = "${TO[$F]}" ] || { say "!! [3/12] the built $F is $(m5 "$WALK/built/$F"), not the kit's pin ${TO[$F]} - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[3/12] live bytes + the one anchored span give the pinned $F"
mkdir -p "$WALK/cc" && cp -p "$KDIR"/*.py "$WALK/cc/" && cp -p "$WALK/built/$F" "$WALK/cc/built_$F"
( cd "$WALK/cc" && "$SPY" -m py_compile *.py 2>/dev/null && "$VPY" -m py_compile *.py 2>/dev/null ) || { say "!! [4/12] compile on both pythons failed - nothing placed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK/cc/__pycache__"
say "[4/12] the built $F and the kit's scripts compile on /usr/bin/python3 and the venv python (a scratch copy)"
# ---- 5-6: scratch copies, the walk ------------------------------------------------------------------------------------------------------
R="$WALK/run"
for side in new old; do
  mkdir -p "$R/$side/finance_ui" "$R/$side/spine" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$R/$side/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$R/$side/finance_ui/"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$R/$side/spine/" 2>/dev/null
  [ -f "$R/$side/finance_app.py" ] || { say "!! [5/12] no scratch copy of the finance folder - nothing placed"; rm -rf "$WALK"; exit 1; }
done
cp -p "$WALK/built/$F" "$R/new/$F"
mkdir -p "$R/por" || exit 1
for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/por/"; done   # never the live secret, never the user store
cp -p "$POR/tile_grants.json" "$R/por/"
copydb "$DBF" "$R/scratch.db" && copydb "$ADB" "$R/scratch_assets.db" && copydb "$SPD" "$R/scratch_spine.db" || { say "!! [5/12] no scratch copies - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[5/12] scratch copies: the finance folder twice (NEW with the built $F, OLD as it is), the portal's code; finance.db, assets.db and spine.db by the backup API"
WOUT="$( cd "$R" && timeout 2400 "$VPY" -B "$KDIR/walk_s520.py" --kit "$KDIR" --work "$R/w" --fin-new "$R/new" --fin-old "$R/old" --por "$R/por" \
         --db "$R/scratch.db" --adb "$R/scratch_assets.db" --spine "$R/scratch_spine.db" 2>&1 )"
echo "$WOUT" | mask | cut -c1-1600 | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S520 GREEN" || { say "!! [6/12] walk_s520 red - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[6/12] walk_s520 green on scratch copies; every named control red on the old file (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: nothing placed, nothing written"; rm -rf "$WALK"; exit 0; fi
# ---- 7-9: re-check, backups, place ----------------------------------------------------------------------------------------------------------
[ -d "$LOCK" ] && [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ] || { say "!! [7/12] the build lock is not held by $KIT - nothing placed"; rm -rf "$WALK"; exit 1; }
[ "$(m5 "$FIN/$F")" = "$FROM" ] || { say "!! [7/12] $FIN/$F moved during the walk - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[7/12] the lock is held by $KIT; the FROM pin still stands after the walk"
say "   before: $(state_now)"
BAK="$FIN/$F.bak_S520_${FROM:0:8}"
\cp -p "$FIN/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [8/12] the backup of $F does not read back - nothing placed"; rm -rf "$WALK"; exit 1; }
copydb "$DBF" "$FIN/finance.db.bak_S520_$STAMP" && [ -s "$FIN/finance.db.bak_S520_$STAMP" ] || { say "!! [8/12] database backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
say "[8/12] $BAK read back; $FIN/finance.db.bak_S520_$STAMP by the backup API ($(stat -c %s "$FIN/finance.db.bak_S520_$STAMP") bytes; the kit writes nothing, the live card's first render may)"
putfile() { \cp -p "$1" "$2.s520_new" && mv -f "$2.s520_new" "$2"; }
restore() {
  say "!! RED after placing ($1) - restoring $F byte-identically"
  putfile "$BAK" "$FIN/$F"; systemctl restart "$SVC" || true; sleep 8
  say "   $FIN/$F $(m5 "$FIN/$F") (FROM $FROM) · finance healthz $(health http://127.0.0.1:8106/finance/healthz) · $SVC $(systemctl is-active "$SVC") · $(state_now)"
  rm -rf "$WALK"; exit 1
}
putfile "$WALK/built/$F" "$FIN/$F" || restore "copy"
[ "$(m5 "$FIN/$F")" = "${TO[$F]}" ] || restore "md5 read-back"
cmp -s "$FIN/$F" "$R/new/$F" || restore "the placed $F is not the walk's file"
say "[9/12] $F placed by rename; md5 read back = the TO pin ${TO[$F]}; byte-identical to the walk's NEW copy"
# ---- 10: restart, health ------------------------------------------------------------------------------------------------------------------
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "restart"
sleep 8
systemctl is-active --quiet "$SVC" || restore "$SVC not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); say "health : finance healthz $c1"
[ "$c1" = 200 ] || restore "finance healthz"
c=$(health http://127.0.0.1:8106/finance/amir/step/6); say "         /finance/amir/step/6 $c (302/401 = the login gate, expected)"
[ "$c" = 302 ] || [ "$c" = 401 ] || restore "the gated page answered $c"
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
[ "$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')" = 0 ] || restore "$SVC journal errors"
say "[10/12] $SVC active (restarted once, $T0); healthz 200; the gated page answers the gate; no error in its journal"
# ---- 11: the live card, read once as the owner and as amir (the brief: the existing code writes the stage-A verified event when the proof passes)
mkdir -p "$R/rb/nosso"
RB="$( cd "$FIN" && FINANCE_DB="$DBF" FINANCE_ALLOW_HEADER_AUTH=1 FINANCE_SSO_DIR="$R/rb/nosso" timeout 300 "$VPY" -B - <<'PYEOF' 2>&1
import html, re, sqlite3, sys
sys.path.insert(0, ".")
import finance_app as fa
import stock_app as SA
c = fa.app.test_client()
def spans(h):
    return [html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<(?:span|p|b|li)[^>]*>(.*?)</(?:span|p|b|li)>", h or "", re.S)]
BELTS = ("L S BELT CONT GRAY UNISON L", "L S BELT CONT GRAY UNISON XXL")
for who, role in (("manoj", "doctor"), ("amir", "staff")):
    r = c.get("/finance/amir/step/6", headers={"X-Clinic-User": who, "X-Clinic-Role": role})
    h = r.get_data(as_text=True)
    sp = [x for x in spans(h) if x]
    print("as %s: /finance/amir/step/6 %s; belts named %s; 'Marg mein yeh abhi sahi nahi hain' %s; Orthotic lines %s; naam lines %s"
          % (who, r.status_code, [b for b in BELTS if b in h], "Marg mein yeh abhi sahi nahi hain" in h, [x for x in sp if x.startswith("Orthotic")][:3],
             [x for x in sp if "aam badl" in x][:3]))
con = sqlite3.connect("file:/root/finance/finance.db?mode=ro", uri=True)
ev = con.execute("SELECT stage, event, ref, at, detail FROM stock_stage_event WHERE count_id=1 ORDER BY id").fetchall()
print("stage events of count 1 after the read: %s" % ev)
lots = [e for e in ev if e[0] == "C" and e[1] == "release"]
print("stage-C lots released: %d%s" % (len(lots), (" -- " + "; ".join("%s: %d voucher(s)" % (e[3], len((e[2] or "").split(","))) for e in lots)) if lots else ""))
st = SA.amir_stage(con)
print("amir_stage now: stage %s, A verified_at %s, renames_visible %s, B %s" % (st.get("stage"), (st.get("A") or {}).get("verified_at"), st.get("renames_visible"), {k: v for k, v in (st.get("B") or {}).items() if k in ("total", "verified", "ticked")}))
print("READ_BACK OK")
PYEOF
)"
echo "$RB" | mask | cut -c1-900 | sed 's/^/   /'
echo "$RB" | grep -q "^READ_BACK OK" || restore "the read of the live card"
say "[11/12] the live card read once as the owner and as amir (above: what it shows and the event the existing code wrote)"
# ---- 12: nothing else moved -------------------------------------------------------------------------------------------------------------
for f in "${NOTT[@]}"; do [ "$(m5 "$f")" = "${NT0[$f]}" ] || restore "$f moved -- the kit must not touch it"; done
[ "$(cron5)" = "$CRON0" ] || restore "the crontab moved -- the kit must not touch it"
[ "$(health http://127.0.0.1:8106/finance/healthz)" = 200 ] || restore "healthz at the end"
say "[12/12] nothing else moved (the twelve must-not-move files, the crontab); healthz 200"
say "   after : $(state_now)"
md5sum "$FIN/$F"
rm -rf "$WALK"
say "   done · healthz 200 · backups: $BAK and $FIN/finance.db.bak_S520_$STAMP · the lock stays held by $KIT until the report is written"
say "$KIT: DONE"
