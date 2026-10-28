#!/bin/bash
# =============================================================================
#  install_S676_SECTIONS_BY_FAMILY.sh · kit S676 (28-Oct-2026, Sanjeevni session 362) · F-1035's residue, the owner's "All three" 12:37 IST.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s676kit && cp -rp /root/deploy/repo/deploy_kits/S676_SECTIONS_BY_FAMILY /tmp/s676kit && bash /tmp/s676kit/install_S676_SECTIONS_BY_FAMILY.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#   /root/finance/section_map.py  abef2baf -> TO   the family rule: his ruling on one size decides its sisters; on_closing seeds new names
#   /root/finance/stock_app.py    8413ee55 -> TO   ONE edit in api_snapshot: section_map.on_closing after a closing lands, fail-soft
#   finance.db stock_item_section   DATA STEP      the newest closing's names seeded; the family sweep (the three cast shoes S669 left)
#  Restarts clinic-finance. Red after placing: both files back, the table back to its copy, finance restarted.
# =============================================================================
set -u
KIT="S676_SECTIONS_BY_FAMILY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
R1="finance/section_map.py"; R2="finance/stock_app.py"
FROM1=abef2baf91ccb00288e2960b071ba0d1; FROM2=8413ee5577cc7dac0f0897fbe5a6231d
TO1="$(awk '$2=="'$R1'"{print $1}' "$KDIR/TO_PINS.md5")"; TO2="$(awk '$2=="'$R2'"{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s676_inst_$STAMP"
DEPLOY="${DEPLOY:-$ROOT/deploy}"
TABLE_BAK="$DEPLOY/s676_section_before_$STAMP.json"
PLACED=0; TOOK_LOCK=0; DATA_DONE=0
GREEN="31 of 31 green"; GREEN2="30 of 30 green"
CONTROL="20 S676 check(s) red · 0 older red · 10 green"
BAK1="$ROOT/$R1.bak_S676_${FROM1:0:8}"; BAK2="$ROOT/$R2.bak_S676_${FROM2:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s676.py" "$@" 2>&1); }
table_dump() { "$APY" -c "import sqlite3,json,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); json.dump([list(r) for r in c.execute('SELECT item_key,item,section,source,seeded_as,by_user,at FROM stock_item_section ORDER BY item_key')], open(sys.argv[2],'w'))" "$1" "$2"; }
table_restore() { "$APY" -c "import sqlite3,json,sys; c=sqlite3.connect(sys.argv[1],timeout=60); rows=json.load(open(sys.argv[2])); c.execute('DELETE FROM stock_item_section'); c.executemany('INSERT INTO stock_item_section (item_key,item,section,source,seeded_as,by_user,at) VALUES (?,?,?,?,?,?,?)', rows); c.commit(); print(len(rows))" "$1" "$2"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the files back"
  \cp -p "$BAK1" "$ROOT/$R1" || say "   !! could not put back $ROOT/$R1"
  \cp -p "$BAK2" "$ROOT/$R2" || say "   !! could not put back $ROOT/$R2"
  rm -f "$ROOT"/finance/.section_map.py.s676 "$ROOT"/finance/.stock_app.py.s676
  [ "$DATA_DONE" = 1 ] && { n=$(table_restore "$DB" "$TABLE_BAK") && say "   stock_item_section put back from $TABLE_BAK ($n rows)" || say "   !! the table could not be put back: $TABLE_BAK"; }
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$R1 $(m5 "$ROOT/$R1") (expected $FROM1); $ROOT/$R2 $(m5 "$ROOT/$R2") (expected $FROM2); finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! preflight: $VPY has no flask (the walk mounts the stock pages) - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST (clear of the night's jobs, 23:50-03:30) - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO1" ] && [ -n "$TO2" ] || { say "!! [1/8] TO_PINS.md5 does not name both files - nothing installed"; exit 1; }
[ -f "$ROOT/$R1" ] && [ -f "$ROOT/$R2" ] && [ -f "$DB" ] && [ -d "$DEPLOY" ] || { say "!! [1/8] $ROOT/$R1, $ROOT/$R2, $DB or $DEPLOY is missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$R1")" = "$TO1" ] && [ "$(m5 "$ROOT/$R2")" = "$TO2" ]; then say "-- ALREADY INSTALLED: both files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
C1=$(m5 "$ROOT/$R1"); C2=$(m5 "$ROOT/$R2")
if { [ "$C1" = "$TO1" ] && [ "$C2" = "$FROM2" ]; } || { [ "$C1" = "$FROM1" ] && [ "$C2" = "$TO2" ]; }; then
  stop_unlocked "!! [2/8] HALF PLACED: one file is already the kit's and the other is not (an earlier run was cut between the two placements). Put the placed one back from its .bak_S676_* copy, then run this again. Nothing written."
fi
[ "$C1" = "$FROM1" ] || stop_unlocked "!! [2/8] $ROOT/$R1 is ${C1:0:8}, expected ${FROM1:0:8} - it changed after this kit was built: STOP, nothing installed"
[ "$C2" = "$FROM2" ] || stop_unlocked "!! [2/8] $ROOT/$R2 is ${C2:0:8}, expected ${FROM2:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pins exact: section_map.py and stock_app.py at their FROM"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s676.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live files - nothing installed"; }
[ "$(m5 "$SCR/built/$R1")" = "$TO1" ] || stop_unlocked "!! [3/8] rebuilt, section_map.py is $(m5 "$SCR/built/$R1" | cut -c1-8), not ${TO1:0:8} - nothing installed"
[ "$(m5 "$SCR/built/$R2")" = "$TO2" ] || stop_unlocked "!! [3/8] rebuilt, stock_app.py is $(m5 "$SCR/built/$R2" | cut -c1-8), not ${TO2:0:8} - nothing installed"
for py in "$APY" "$VPY"; do for f in "$R1" "$R2"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done; done
say "[3/8] rebuilt here from this box's live bytes: both at their TO pins; both compile under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1")
L1="$(echo "$R" | tail -1)"; [ "$L1" = "$GREEN" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/8] the walk is not green ($L1) - nothing installed"; }
R=$(walk --old "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live files is not as expected ($R) - nothing installed"
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk on a copy of the database: $L1; the control on the live files: $R; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi

\cp -p "$ROOT/$R1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop_unlocked "!! [5/8] could not write the backup of $ROOT/$R1 - nothing placed"
\cp -p "$ROOT/$R2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ] || stop_unlocked "!! [5/8] could not write the backup of $ROOT/$R2 - nothing placed"
table_dump "$DB" "$TABLE_BAK" && [ -s "$TABLE_BAK" ] || stop_unlocked "!! [5/8] could not copy stock_item_section to $TABLE_BAK - nothing placed"
STG1="$ROOT/finance/.section_map.py.s676"; STG2="$ROOT/finance/.stock_app.py.s676"
{ cat "$SCR/built/$R1" > "$STG1" && [ "$(m5 "$STG1")" = "$TO1" ] && cat "$SCR/built/$R2" > "$STG2" && [ "$(m5 "$STG2")" = "$TO2" ]; } || { rm -f "$STG1" "$STG2"; stop_unlocked "!! [5/8] could not stage the files - nothing placed"; }
for p in "$R1:$STG1" "$R2:$STG2"; do f="${p%%:*}"; s="${p#*:}"; chmod --reference="$ROOT/$f" "$s" 2>/dev/null; chown --reference="$ROOT/$f" "$s" 2>/dev/null; done
PLACED=1
mv -f "$STG1" "$ROOT/$R1" || restore "the rename of section_map.py"; [ "$(m5 "$ROOT/$R1")" = "$TO1" ] || restore "section_map.py read back"
mv -f "$STG2" "$ROOT/$R2" || restore "the rename of stock_app.py"; [ "$(m5 "$ROOT/$R2")" = "$TO2" ] || restore "stock_app.py read back"
say "[5/8] placed and read back: both at their TO pins (backups $BAK1, $BAK2; the table's copy $TABLE_BAK)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/stock/page/sections); case "$c2" in 302|401|303|403) ;; *) restore "the sections page answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; the sections page $c2 without a login; journal clean"
OUT=$(cd "$ROOT/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -B -c "
import sqlite3, sys, json
sys.path.insert(0, '.')
import section_map as sm
con = sqlite3.connect('$DB', timeout=60)
got = sm.snapshot_items(con)
as_on, items = (got or ('', []))
added, _k = sm.seed(con, items, by_user='S676 install (closing %s)' % as_on)
moves = sm.sweep_families(con, by_user='S676 install')
con.commit()
print('closing %s: %d names; %d row(s) added; %d moved: %s' % (as_on, len(items), added, len(moves), '; '.join('%s %s -> %s (as %s)' % m for m in moves) or 'none'))
" 2>&1)
RC=$?; echo "$OUT" | sed 's/^/         | /'
[ "$RC" = 0 ] && echo "$OUT" | grep -q "row(s) added" || restore "the data step did not run clean"
DATA_DONE=1
say "[7/8] the data step done (every name of the newest closing has its row; his rulings reached the sisters)"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed files"
R=$(walk --new "$ROOT" --db "$SCR/walk2.db" --scratch "$SCR/w2" --after-data | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN2" ] || restore "the walk on the placed files and the changed rows: $R"
release_lock
say "[8/8] the walk on the placed files: $R; the build lock released"
say "undo (one line, the files only -- the table keeps every row; it self-heals at the next closing): \\cp -p $BAK1 $ROOT/$R1 && \\cp -p $BAK2 $ROOT/$R2 && $SYSTEMCTL restart $FSVC"
say "       (the table as it was before this install is in $TABLE_BAK -- put back only within the same minute, never later: a closing or a tap since would be lost)"
say ""
say "$KIT: DONE. Every name Marg prints has its section the day it lands; your ruling on one size reaches its sisters."
exit 0
