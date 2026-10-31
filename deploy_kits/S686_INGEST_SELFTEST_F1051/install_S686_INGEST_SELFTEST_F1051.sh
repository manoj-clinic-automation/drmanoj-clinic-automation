#!/bin/bash
# =============================================================================
#  install_S686_INGEST_SELFTEST_F1051.sh · kit S686 (31-Oct-2026, the parent, session 372) · F-1051
#  finance_ingest.py's own selftest becomes a REPORT, never a crash: the anonymous return checked under BOTH
#  positions of the owner's setting ingest.anonymous_to_walkin; every lookup that can find no row a failed
#  check; the throwaway copy of finance.db removed in a finally; made-up patients on IDs the clinic never issues.
#  NOTHING above the selftest changes -- ingest_day, the adapters, the ladder are byte-identical (the walk's M2/M4).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s686kit && cp -rp /root/deploy/repo/deploy_kits/S686_INGEST_SELFTEST_F1051 /tmp/s686kit && bash /tmp/s686kit/install_S686_INGEST_SELFTEST_F1051.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#   /root/finance/finance_ingest.py   ce01a9e1 -> TO   the selftest section only
#  NO RESTART: the running finance app's import step is unchanged byte for byte; it reads the new selftest
#  the next time it starts for any reason. The one data step: throwaway copies left in /tmp by earlier
#  crashed runs (/tmp/finance_ingest_smoke_*.db, older than 10 minutes) are removed -- they hold patients.
#  Red after placing: the file back.
# =============================================================================
set -u
KIT="S686_INGEST_SELFTEST_F1051"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FHZ_URL="${FHZ_URL:-http://127.0.0.1:8106/finance/healthz}"
SMOKE_DIRS="${SMOKE_DIRS:-/tmp /var/tmp $(ls -d /tmp/systemd-private-*/tmp 2>/dev/null | tr '\n' ' ')}"
F="finance/finance_ingest.py"
FROM="ce01a9e1f8acd82370477a7468a6412b"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s686_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="24 of 24 green"
CONTROL="5 S686 check(s) red . 2 green"
GREEN_PLACED="17 of 17 green"
BAK="$ROOT/$F.bak_S686_${FROM:0:8}"
STG="$ROOT/finance/.finance_ingest.py.s686"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhz() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$FHZ_URL"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s686.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting finance_ingest.py back"
  PLACED=2
  \cp -p "$BAK" "$ROOT/$F" || say "   !! could not put back $ROOT/$F"; rm -f "$STG"
  say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8}); finance healthz $(fhz). Send a photo of this screen to Claude."
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
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] || { say "!! [1/7] TO_PINS.md5 does not name $F - nothing installed"; exit 1; }
[ -f "$ROOT/$F" ] && [ -f "$DB" ] || { say "!! [1/7] $ROOT/$F or $DB is missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && { say "-- ALREADY INSTALLED: finance_ingest.py is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/7] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/7] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop_unlocked "!! [2/7] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/7] live pin exact: finance_ingest.py at its FROM ${FROM:0:8}"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s686.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/7] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$F")" = "$TO" ] || stop_unlocked "!! [3/7] rebuilt, finance_ingest.py is $(m5 "$SCR/built/$F" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$F" || stop_unlocked "!! [3/7] finance_ingest.py does not compile on $py - nothing installed"; done
say "[3/7] rebuilt here from this box's live bytes: at its TO pin ${TO:0:8}; compiles under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/7] no copy of the database - nothing installed"
R=$(walk --new "$SCR/built" --old-root "$ROOT" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || stop_unlocked "!! [4/7] the walk on the rebuilt file is not green ($R) - nothing installed"
R0=$(walk --old "$ROOT" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || stop_unlocked "!! [4/7] the control on the live file is not as expected ($R0) - nothing installed"
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] the walk on a copy of the database: $GREEN (the import step byte-identical, 6 mutants caught); the control on the live file: $R0; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop_unlocked "!! [5/7] could not write the backup $BAK - nothing placed"
{ cat "$SCR/built/$F" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/7] could not stage finance_ingest.py - nothing placed"; }
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
say "[5/7] placed and read back: finance_ingest.py at ${TO:0:8} (backup $BAK)"
c1=$(fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
say "[6/7] no restart (the running import step is unchanged byte for byte); finance healthz $c1"

N=0; B=0
for d in $SMOKE_DIRS; do
  [ -d "$d" ] || continue
  while IFS= read -r -d '' p; do
    s=$(stat -c %s "$p" 2>/dev/null || echo 0); rm -f "$p" "$p-journal" "$p-wal" "$p-shm" && { N=$((N+1)); B=$((B+s)); }
  done < <(find "$d" -maxdepth 1 -type f -name 'finance_ingest_smoke_*.db' -mmin +10 -print0 2>/dev/null)
done
say "[7/7] data step: $N throwaway database copy(ies) left by earlier crashed selftests removed ($B bytes; looked in: $SMOKE_DIRS)"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed file"
R=$(walk --new "$ROOT" --lib "$ROOT" --db "$SCR/walk2.db" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN_PLACED" ] || restore "the walk on the placed file: $R"
mkdir -p "$SCR/st"; S=$(cd "$ROOT/finance" && TMPDIR="$SCR/st" timeout 600 "$VPY" -B finance_ingest.py "$SCR/walk2.db" 2>&1 | head -1)
echo "$S" | grep -qE '^INGEST ([0-9]+)/\1 passed' || restore "its own selftest in $ROOT/finance: $S"
[ -z "$(ls -A "$SCR/st" 2>/dev/null)" ] || restore "its own selftest left a copy behind"
release_lock
say "      the walk on the placed file: $R; its own selftest on a copy: $S; the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$F"
say ""
say "$KIT: DONE. F-1051 closed: the ingest selftest reports, never crashes, and leaves no copy of the database behind."
exit 0
