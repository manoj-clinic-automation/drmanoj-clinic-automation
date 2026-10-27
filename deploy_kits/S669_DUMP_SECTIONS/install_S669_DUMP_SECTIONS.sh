#!/bin/bash
# =============================================================================
#  install_S669_DUMP_SECTIONS.sh · kit S669 (28-Oct-2026, Sanjeevni session 359) · the owner 05:09 IST: orthotics under "Medicines and
#  others" in the expiry watch's dump. Ours, not Marg's: (1) his section rulings keyed on one Marg report width, the Batch Stock prints
#  another; (2) the S268 seed filed the two cast shoes as Consumables.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s669kit && cp -rp /root/deploy/repo/deploy_kits/S669_DUMP_SECTIONS /tmp/s669kit && bash /tmp/s669kit/install_S669_DUMP_SECTIONS.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#   /root/finance/expiry_watch.py  7ba3b0bc -> TO   ortho_of: a Marg-width twin of a table key stands for it (unique, >= 12 letters)
#   finance.db stock_item_section    DATA STEP        CAST SHOE S TYNOR, PRIME CAST SHOE S: Consumables (seed) -> Orthotics (owner, 28-Oct)
#  Restarts clinic-finance. The watch made ONCE now so the page is right at once. Red after placing: the file back, the two rows back
#  (their seed values), finance restarted.
# =============================================================================
set -u
KIT="S669_DUMP_SECTIONS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
ARCH="${ARCH:-$ROOT/marg_ingest/archive}"
SLOCK="${SLOCK:-/tmp/spine.lock}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
REL="finance/expiry_watch.py"
FROM=7ba3b0bcc0131cb7258ef0dd63afb5b5
TO="$(awk '{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s669_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; DATA_DONE=0
GREEN="11 of 11 green"
CONTROL="2 S669 check(s) red · 0 older red · 9 green"
BAK="$ROOT/$REL.bak_S669_${FROM:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
sqlw() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1],timeout=60); c.executescript(sys.argv[2]); c.commit(); c.close()" "$1" "$2"; }   # no sqlite3 CLI on the box
q() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(c.execute(sys.argv[2]).fetchone()[0])" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s669.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the file back"
  \cp -p "$BAK" "$ROOT/$REL" || say "   !! could not put back $ROOT/$REL"
  rm -f "$ROOT"/finance/.expiry_watch.py.s669
  [ "$DATA_DONE" = 1 ] && { sqlw "$DB" "$UNDO_SQL" && say "   the two cast-shoe rows put back to the seed's Consumables" || say "   !! the two rows could not be put back: $UNDO_SQL"; }
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$REL $(m5 "$ROOT/$REL") (expected $FROM); finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout flock; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST (clear of the night's jobs, 23:50-03:30) - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -f "$ROOT/$REL" ] && [ -f "$DB" ] && [ -f "$SPINE" ] && [ -d "$ARCH" ] || { say "!! [1/8] $ROOT/$REL, $DB, $SPINE or $ARCH is missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$REL")" = "$TO" ]; then say "-- ALREADY INSTALLED: expiry_watch.py is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
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
C="$(m5 "$ROOT/$REL")"; [ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $ROOT/$REL is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pin exact: expiry_watch.py at its FROM"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s669.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$REL")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, expiry_watch.py is $(m5 "$SCR/built/$REL" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$REL" || stop_unlocked "!! [3/8] the built file does not compile on $py - nothing installed"; done
say "[3/8] rebuilt here from this box's live bytes: at its TO pin; compiles under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
BATCH="$(q "$DB" "SELECT export_name FROM stock_expiry_run WHERE ok=1 AND whole=1 ORDER BY id DESC LIMIT 1")"
BATCHF="$(find "$ARCH" -iname "$BATCH" -print -quit 2>/dev/null)"
[ -n "$BATCHF" ] && [ -f "$BATCHF" ] || stop_unlocked "!! [4/8] the newest run's Batch Stock ($BATCH) is not in $ARCH - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --batch "$BATCHF" --scratch "$SCR/w1")
L1="$(echo "$R" | tail -1)"; [ "$L1" = "$GREEN" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/8] the walk is not green ($L1) - nothing installed"; }
R=$(walk --old "$ROOT" --db "$SCR/walk.db" --batch "$BATCHF" --scratch "$SCR/w0" | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live file is not as expected ($R) - nothing installed"
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk on copies of the database and the spine: $L1; the control on the live file: $R; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi

\cp -p "$ROOT/$REL" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || stop_unlocked "!! [5/8] could not write the backup of $ROOT/$REL - nothing placed"
STG="$ROOT/finance/.expiry_watch.py.s669"
{ cat "$SCR/built/$REL" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage the file - nothing placed"; }
chmod --reference="$ROOT/$REL" "$STG" 2>/dev/null; chown --reference="$ROOT/$REL" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$REL" || restore "the rename"; [ "$(m5 "$ROOT/$REL")" = "$TO" ] || restore "the md5 read back"
say "[5/8] placed and read back: expiry_watch.py at its TO pin (backup $BAK)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/sanjeevni/expiry); case "$c2" in 302|401|303|403) ;; *) restore "the expiry page answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; the expiry page $c2 without a login; journal clean"
DATA_SQL="UPDATE stock_item_section SET section='Orthotics', source='owner', by_user='manoj (28-Oct-2026, S359)', at='$(date +%Y-%m-%dT%H:%M:%S)' WHERE item_key IN ('CAST SHOE S TYNOR','PRIME CAST SHOE S') AND section='Consumables' AND source='seed';"
UNDO_SQL="UPDATE stock_item_section SET section='Consumables', source='seed', by_user='manoj', at='2026-09-18T07:03:44' WHERE item_key IN ('CAST SHOE S TYNOR','PRIME CAST SHOE S') AND source='owner' AND by_user LIKE 'manoj (28-Oct-2026%';"
B0=$(q "$DB" "SELECT COUNT(*) FROM stock_item_section WHERE item_key IN ('CAST SHOE S TYNOR','PRIME CAST SHOE S') AND section='Consumables' AND source='seed'")
[ "$B0" = 2 ] || restore "the two cast-shoe rows are not as this kit read them (seed Consumables: $B0 of 2)"
sqlw "$DB" "$DATA_SQL" || restore "the data step could not be written"
B1=$(q "$DB" "SELECT COUNT(*) FROM stock_item_section WHERE item_key IN ('CAST SHOE S TYNOR','PRIME CAST SHOE S') AND section='Orthotics' AND source='owner'")
[ "$B1" = 2 ] || restore "the data step read back $B1 of 2 rows"
DATA_DONE=1
say "       the data step: CAST SHOE S TYNOR and PRIME CAST SHOE S -> Orthotics (owner, 28-Oct); read back"
N0=$(q "$DB" "SELECT COUNT(*) FROM stock_expiry_run")
OUT=$(cd "$ROOT/finance/spine" && timeout 600 flock -w 120 "$SLOCK" "$VPY" -B near_expiry.py 2>&1 | tail -2)
echo "$OUT" | sed 's/^/         | /'
N1=$(q "$DB" "SELECT COUNT(*) FROM stock_expiry_run"); OK1=$(q "$DB" "SELECT ok FROM stock_expiry_run ORDER BY id DESC LIMIT 1")
[ "$N1" = "$((N0 + 1))" ] && [ "$OK1" = 1 ] || restore "the watch made once now: runs $N0 -> $N1, ok $OK1"
say "[7/8] the watch made once now, as the 23:57 line makes it: one good run"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed file"
R=$(walk --new "$ROOT" --db "$SCR/walk2.db" --batch "$BATCHF" --scratch "$SCR/w2" --after-data | tail -1)
[ "$R" = "12 of 12 green" ] || restore "the walk on the placed file and the changed rows: $R"
release_lock
say "[8/8] the walk on the placed file: $R; the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$REL && $APY -c \"import sqlite3; c=sqlite3.connect('$DB'); c.executescript(\\\"$UNDO_SQL\\\"); c.commit()\" && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Your section rulings hold under every Marg report width; the two cast shoes are orthotics; the list is made again."
exit 0
