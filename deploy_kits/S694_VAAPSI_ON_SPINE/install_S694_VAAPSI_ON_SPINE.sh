#!/bin/bash
# =============================================================================
#  install_S694_VAAPSI_ON_SPINE.sh · kit S694 (01-Nov-2026, Sanjeevni session 375) · Darpan's Vaapsi desk reads a patient's bill lines from
#  the spine (one read door, S677) instead of the old sale store; the patient stays on sale_item; the old store answers only when the spine
#  cannot be opened (plan section 9, step 1).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s694kit && cp -rp /root/deploy/repo/deploy_kits/S694_VAAPSI_ON_SPINE /tmp/s694kit && bash /tmp/s694kit/install_S694_VAAPSI_ON_SPINE.sh
#  (DRY=1 before bash: every gate, the walk, the control and the proof on copies -- nothing written.)
#   /root/finance/returns_desk.py   dffbe8fb -> TO   the spine adapter; items / history / catalog / allocate read the spine; source on every answer
#  THE GATE THAT DECIDES: on this box, on COPIES of the database and the spine (read only), the OLD and the NEW desk answer items, history
#  and catalog for every patient with a ref in the last 61 days -- identical, or a difference the kit explains (a bill or line the spine
#  holds and the old store had not; a name the spine's alias folds; same-day bills ordered by number; Marg's own unit) -- else nothing is placed.
#  Data step: any older desk line re-keyed to the spine's key (0 rows today). Restarts clinic-finance. Red after placing: the file back.
# =============================================================================
set -u
KIT="S694_VAAPSI_ON_SPINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F="finance/returns_desk.py"
FROM="dffbe8fba15a6e9f37f8aba0ee546034"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s694_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="25 of 25 green"
CONTROL="14 S694 check(s) red . 11 green"
BAK="$ROOT/$F.bak_S694_${FROM:0:8}"
STG="$ROOT/finance/.returns_desk.py.s694"

REKEY="import re,sqlite3,sys,os
db,spine_dir,spine_db=sys.argv[1],sys.argv[2],sys.argv[3]
K=lambda n: re.sub(r'\\s+',' ',str(n or '').strip())[:20].strip()
key=K
try:
    sys.path.insert(0,spine_dir); from spine_read import Spine; key=Spine(spine_db).key   # the spine's key: K(name), alias-folded as the desk's lines are
except Exception: pass
import json
undo=sys.argv[4]
con=sqlite3.connect(db,timeout=60); n=0; was=[]
with con:
    for rid,name,k in con.execute('SELECT id,item_name,item_key FROM return_line').fetchall():
        want=key(name)
        if k != want: was.append([rid,k]); con.execute('UPDATE return_line SET item_key=? WHERE id=?',(want,rid)); n+=1
json.dump(was, open(undo,'w'))
print('desk lines re-keyed to the spine\\'s key: %d of %d' % (n, con.execute('SELECT COUNT(*) FROM return_line').fetchone()[0]))"
UNDOKEY="import json,sqlite3,sys
con=sqlite3.connect(sys.argv[1],timeout=60); was=json.load(open(sys.argv[2]))
with con:
    for rid,k in was: con.execute('UPDATE return_line SET item_key=? WHERE id=?',(k,rid))
print('re-key undone: %d' % len(was))"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s694.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting returns_desk.py back"
  PLACED=2
  \cp -p "$BAK" "$ROOT/$F" || say "   !! could not put back $ROOT/$F"; rm -f "$STG"
  [ -s "$SCR/rekey_undo.json" ] && { "$APY" -c "$UNDOKEY" "$DB" "$SCR/rekey_undo.json" 2>&1 | tail -1 | sed 's/^/   /' || say "   !! the re-key could not be undone (see $SCR/rekey_undo.json)"; }
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8})"
  say "   finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
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
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] || { say "!! [1/8] TO_PINS.md5 does not name $F - nothing installed"; exit 1; }
[ -f "$ROOT/$F" ] && [ -f "$ROOT/finance/returns_desk.html" ] && [ -f "$DB" ] && [ -f "$SPINE" ] && [ -f "$ROOT/finance/spine/spine_read.py" ] || { say "!! [1/8] $ROOT/$F, returns_desk.html, $DB, $SPINE or spine_read.py is missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && { say "-- ALREADY INSTALLED: returns_desk.py is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
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
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pin exact: returns_desk.py at its FROM ${FROM:0:8}"

mkdir -p "$SCR/built/finance" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s694.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$F")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, returns_desk.py is $(m5 "$SCR/built/$F" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$F" || stop_unlocked "!! [3/8] returns_desk.py does not compile on $py - nothing installed"; done
# the rebuilt file's root: the live neighbours (read only) beside the kit's file
mkdir -p "$SCR/newroot/finance/spine" && for f in "$ROOT"/finance/*.py; do ln -s "$f" "$SCR/newroot/finance/$(basename "$f")"; done
for f in "$ROOT"/finance/*.html "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json; do [ -f "$f" ] || continue; case "$f" in */spine/*) ;; *) ln -s "$f" "$SCR/newroot/finance/$(basename "$f")"; continue;; esac; ln -s "$f" "$SCR/newroot/finance/spine/$(basename "$f")"; done
rm -f "$SCR/newroot/$F" && cp -p "$SCR/built/$F" "$SCR/newroot/$F"
say "[3/8] rebuilt here from this box's live bytes: at its TO pin ${TO:0:8}; compiles under both pythons"

R=$(walk --new "$SCR/newroot" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || { walk --new "$SCR/newroot" --scratch "$SCR/w1b" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt file is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live file is not as expected ($R0) - nothing installed (kept in $SCR)"; }
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
copydb "$SPINE" "$SCR/spine.db" || stop_unlocked "!! [4/8] no copy of the spine - nothing installed"
P1=$(walk --proof --old-root "$ROOT" --new "$SCR/newroot" --db "$SCR/walk.db" --spine "$SCR/spine.db" --scratch "$SCR/wp1")
echo "$P1" | grep -E '^  --  ' | grep -v -E "only in the spine|the spine holds|merged by|same-day|unit rule|20-name cut" | head -20 | sed 's/^/         /'
PL1="$(echo "$P1" | tail -1)"
case "$PL1" in "proof: patients "*" . unexplained 0 . CLEAN . source spine") ;; *) PLACED=2; stop_unlocked "!! [4/8] the proof is not clean ($PL1) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk: $GREEN; the control on the live file: $R0; $PL1; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK - nothing placed"
{ cat "$SCR/built/$F" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage returns_desk.py - nothing placed"; }
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
find "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/8] placed and read back: returns_desk.py at ${TO:0:8} (backup $BAK)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/returns/desk/api/items?pid=1); case "$c2" in 302|401|303|403) ;; *) restore "the desk answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; the desk $c2 without a login (the login gate, expected); journal clean"
"$APY" -c "$REKEY" "$DB" "$ROOT/finance/spine" "$SPINE" "$SCR/rekey_undo.json" > "$SCR/rekey.txt" 2>&1 || { tail -3 "$SCR/rekey.txt"; restore "the re-key of the desk's older lines failed"; }
RK="$(tail -1 "$SCR/rekey.txt")"
case "$RK" in "desk lines re-keyed"*) ;; *) restore "the re-key did not report ($RK)";; esac
say "[7/8] data step: $RK"
R=$(walk --new "$ROOT" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
release_lock
say "[8/8] the walk on the placed file: $R; the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$F && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. The Vaapsi desk reads every bill line from the spine; the old store answers only when the spine cannot be opened."
exit 0
