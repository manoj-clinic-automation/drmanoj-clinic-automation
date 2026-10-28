#!/bin/bash
# =============================================================================
#  install_S672_NONCASH_AT_INGEST.sh · kit S672 (28-Oct-2026, Sanjeevni session 361) · F-1037 · the owner 08:53 IST: procedure bill
#  A004474 (27-Oct, Rs 98) not counted. The home / procedure deduction was made only by day_resync every 30 min on UNAPPROVED days;
#  27-Oct was approved before the 09:00 run. Now the sale ingest makes it in its own transaction; 27-Oct corrected once.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s672kit && cp -rp /root/deploy/repo/deploy_kits/S672_NONCASH_AT_INGEST /tmp/s672kit && bash /tmp/s672kit/install_S672_NONCASH_AT_INGEST.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#   /root/finance/day_resync.py      c62e98b9 -> TO   noncash_day(commit=, via=); at_ingest()
#   /root/finance/finance_ingest.py  d7b07fb6 -> TO   one call at the end of ingest_day, under a savepoint, fail-soft
#   finance.db  DATA STEP (last)  27-Oct: one day_noncash_bill row for A004474 (procedure medicine), one audit row
#  Restarts clinic-finance. Red after placing: both files back, finance restarted (the data step runs only after everything is green).
# =============================================================================
set -u
KIT="S672_NONCASH_AT_INGEST"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
ARCH="${ARCH:-$ROOT/marg_ingest/archive}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
R1="finance/day_resync.py";     F1=c62e98b971fab7c6802b74b9029c291e
R2="finance/finance_ingest.py"; F2=d7b07fb6514da7129b969b878ce5fbbd
T1="$(awk -v f="$R1" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
T2="$(awk -v f="$R2" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s672_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="14 of 14 green"
CONTROL="7 S672 check(s) red · 0 older red · 7 green"
B1="$ROOT/$R1.bak_S672_${F1:0:8}"; B2="$ROOT/$R2.bak_S672_${F2:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
q() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(c.execute(sys.argv[2]).fetchone()[0])" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1200 "$VPY" -B "$KDIR/walk_s672.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  \cp -p "$B1" "$ROOT/$R1" || say "   !! could not put back $ROOT/$R1"
  \cp -p "$B2" "$ROOT/$R2" || say "   !! could not put back $ROOT/$R2"
  rm -f "$ROOT"/finance/.day_resync.py.s672 "$ROOT"/finance/.finance_ingest.py.s672
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $R1 $(m5 "$ROOT/$R1" | cut -c1-8) (expected ${F1:0:8}); $R2 $(m5 "$ROOT/$R2" | cut -c1-8) (expected ${F2:0:8}); finance healthz $(wait200 fhz). Nothing was written to the database. Send a photo of this screen to Claude."
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
[ -n "$T1" ] && [ -n "$T2" ] || { say "!! [1/8] TO_PINS.md5 incomplete - nothing installed"; exit 1; }
[ -f "$ROOT/$R1" ] && [ -f "$ROOT/$R2" ] && [ -f "$DB" ] && [ -d "$ARCH" ] || { say "!! [1/8] $ROOT/$R1, $ROOT/$R2, $DB or $ARCH is missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$R1")" = "$T1" ] && [ "$(m5 "$ROOT/$R2")" = "$T2" ]; then
  say "-- ALREADY INSTALLED: both files are the kit's. 27-Oct: $("$VPY" -B "$KDIR/fix_s672.py" --db "$DB" --lib "$ROOT/finance" 2>&1 | tail -1). finance healthz $(fhz)"; exit 0
fi
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
C1="$(m5 "$ROOT/$R1")"; C2="$(m5 "$ROOT/$R2")"
[ "$C1" = "$F1" ] && [ "$C2" = "$F2" ] || stop_unlocked "!! [2/8] day_resync.py ${C1:0:8} / finance_ingest.py ${C2:0:8}, expected ${F1:0:8} / ${F2:0:8} - a file changed after this kit was built: STOP, nothing installed"
say "[2/8] live pins exact: day_resync.py and finance_ingest.py at their FROM"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s672.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live files - nothing installed"; }
[ "$(m5 "$SCR/built/$R1")" = "$T1" ] && [ "$(m5 "$SCR/built/$R2")" = "$T2" ] || stop_unlocked "!! [3/8] rebuilt, the files are not at their TO pins - nothing installed"
for py in "$APY" "$VPY"; do for f in "$R1" "$R2"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done; done
say "[3/8] rebuilt here from this box's live bytes: both at their TO pins; both compile under both pythons"

EXPF="$(find "$ARCH" -iname 'SALE_BILLWISE_DETAIL__2026-10-27__*' -type f -printf '%T@ %p\n' 2>/dev/null | sort -n | tail -1 | cut -d' ' -f2-)"
[ -n "$EXPF" ] && [ -f "$EXPF" ] || stop_unlocked "!! [4/8] the 27-Oct sale export is not in $ARCH - nothing installed"
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --export "$EXPF" --scratch "$SCR/w1" --fix "$KDIR/fix_s672.py")
L1="$(echo "$R" | tail -1)"; [ "$L1" = "$GREEN" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/8] the walk is not green ($L1) - nothing installed"; }
R=$(walk --old "$ROOT" --db "$SCR/walk.db" --export "$EXPF" --scratch "$SCR/w0" --fix "$KDIR/fix_s672.py" | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live files is not as expected ($R) - nothing installed"
FX="$("$VPY" -B "$KDIR/fix_s672.py" --db "$SCR/walk.db" --lib "$ROOT/finance" 2>&1 | tail -1)"
case "$FX" in WOULD_ADD:*A004474*|ALREADY:*) ;; *) stop_unlocked "!! [4/8] the 27-Oct step on a copy of the live data: $FX - nothing installed";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
rm -f "$SCR/walk.db"
say "[4/8] the walk on copies of the database with the real 27-Oct export: $L1; the control on the live files: $R; 27-Oct on a copy: $FX; finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi

\cp -p "$ROOT/$R1" "$B1" && [ "$(m5 "$B1")" = "$F1" ] && \cp -p "$ROOT/$R2" "$B2" && [ "$(m5 "$B2")" = "$F2" ] || stop_unlocked "!! [5/8] could not write the backups - nothing placed"
S1="$ROOT/finance/.day_resync.py.s672"; S2="$ROOT/finance/.finance_ingest.py.s672"
{ cat "$SCR/built/$R1" > "$S1" && [ "$(m5 "$S1")" = "$T1" ] && cat "$SCR/built/$R2" > "$S2" && [ "$(m5 "$S2")" = "$T2" ]; } || { rm -f "$S1" "$S2"; stop_unlocked "!! [5/8] could not stage the files - nothing placed"; }
chmod --reference="$ROOT/$R1" "$S1" 2>/dev/null; chown --reference="$ROOT/$R1" "$S1" 2>/dev/null
chmod --reference="$ROOT/$R2" "$S2" 2>/dev/null; chown --reference="$ROOT/$R2" "$S2" 2>/dev/null
PLACED=1
mv -f "$S1" "$ROOT/$R1" || restore "the rename of day_resync.py"
mv -f "$S2" "$ROOT/$R2" || restore "the rename of finance_ingest.py"
[ "$(m5 "$ROOT/$R1")" = "$T1" ] && [ "$(m5 "$ROOT/$R2")" = "$T2" ] || restore "the md5 read back"
say "[5/8] placed and read back: both at their TO pins (backups $B1, $B2)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; journal clean"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed files"
R=$(walk --new "$ROOT" --lib "$ROOT" --db "$SCR/walk2.db" --export "$EXPF" --scratch "$SCR/w2" --fix "$KDIR/fix_s672.py" | tail -1)
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
rm -f "$SCR/walk2.db"
say "[7/8] the walk on the placed files: $R"
FX="$("$VPY" -B "$KDIR/fix_s672.py" --db "$DB" --lib "$ROOT/finance" --apply 2>&1 | tail -1)"
N1=$(q "$DB" "SELECT COUNT(*) FROM day_noncash_bill WHERE unit='medical' AND bill_no='A004474' AND bill_date='2026-10-27' AND head='procedure_medicine'")
release_lock
case "$FX" in ADDED:*|ALREADY:*) [ "$N1" = 1 ] || { say "!! [8/8] the 27-Oct step said '$FX' but reads back $N1 row(s). The code is installed and proven; send a photo of this screen to Claude."; exit 1; } ;;
  *) say "!! [8/8] the 27-Oct step: $FX. The code is installed and proven; nothing written for 27-Oct. Send a photo of this screen to Claude."; exit 1;; esac
say "[8/8] 27-Oct: $FX -- read back; the build lock released"
say "undo (one line): \\cp -p $B1 $ROOT/$R1 && \\cp -p $B2 $ROOT/$R2 && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Home and procedure medicine bills are deducted the moment the sale export lands; 27-Oct carries A004474."
exit 0
