#!/bin/bash
# =============================================================================
#  install_S687_DARPAN_MONTH_JOBS.sh · kit S687 (31-Oct-2026, the parent, session 372) · Darpan's monthly jobs
#  Home medicines (the count for the coming month), Gaadi ki jaanch (and the vehicle papers' reminders), Expiry ki safai
#  -- four lines on Darpan's Aaj list, his Hinglish screens, the owner's English page. No rupee amount anywhere.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s687kit && cp -rp /root/deploy/repo/deploy_kits/S687_DARPAN_MONTH_JOBS /tmp/s687kit && bash /tmp/s687kit/install_S687_DARPAN_MONTH_JOBS.sh
#  (DRY=1 before bash: every gate, the rebuild, the walk and the control; nothing written.)
#   /root/finance/finance_app.py    1dd66af3 -> TO   ONE inserted mount block (month_jobs), after S579's
#   /root/finance/aaj_duties.json   1d085d58 -> TO   four 'extra' duties for darpan (kind sql)
#   /root/finance/aaj_seed.py       2121947f -> TO   darpan.paper_renewal in NO_HOLD; Darpan's four panel lines, on
#   /root/finance/month_jobs.py     NEW      -> TO   the pages (/finance/monthjobs/...), the mj_* tables
#  ORDER: gates -> pins (the three FROM files AND the duty map) -> rebuild from the live bytes (both pythons compile) -> walk on
#  scratch copies + the control on the live files -> the database backup (chmod 600) and the file backups -> stage + atomic move
#  -> the data step (mj_* tables; Darpan's saved panel, if any) -> restart clinic-finance -> healthz 200, the journal names no
#  month_jobs / ImportError / 'NOT mounted' line -> the walk on the placed files (the real app loaded from them: _MOUNT_FAILED empty).
#  Red after placing: ALL FOUR files back (month_jobs.py removed), finance restarted.
# =============================================================================
set -u
KIT="S687_DARPAN_MONTH_JOBS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
DUTY_MAP="${DUTY_MAP:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"
DMAP_PIN="78b5f07ef7cdd48b1a76d78db52107fc"         # the duty map the walk's counts were built against (S372, 31-Oct-2026)
export DUTY_MAP_JSON="$DUTY_MAP"                     # the walks read the same file aaj_kaam reads
EDITED="finance_app.py aaj_duties.json aaj_seed.py"
ALL="$EDITED month_jobs.py"
declare -A FROM=( [finance_app.py]=1dd66af3dee7f5724b360e8737c74f0a [aaj_duties.json]=1d085d5873d97beff138b01e15e11577 [aaj_seed.py]=2121947f27ce6c5e024b30b0926a898d )
declare -A TO
for n in $ALL; do TO[$n]="$(awk -v f="finance/$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s687_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="75 of 75 green"
CONTROL="42 S687 check(s) red . 5 green"
GREEN_PLACED="47 of 47 green"
DBBAK="$FIN/finance.db.bak_S687_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S687_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$APY" -B "$KDIR/walk_s687.py" "$@" 2>&1); }
mkscratch() {   # $1 = a folder: a copy of the live finance CODE (never the database, never a backup)
  mkdir -p "$1/finance_ui" "$1/spine"
  cp -p "$FIN"/*.py "$1/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$1/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$1/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$1/spine/" 2>/dev/null
  rm -f "$1"/*.bak_* 2>/dev/null; return 0
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting ALL FOUR files back"
  PLACED=2
  for n in $EDITED; do \cp -p "$(bak $n)" "$FIN/$n" || say "   !! could not put back $FIN/$n"; done
  rm -f "$FIN/month_jobs.py" "$FIN"/.*.s687
  "$SYSTEMCTL" restart "$FSVC" || true
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n" | cut -c1-8) (expected ${FROM[$n]:0:8})"; done
  [ -e "$FIN/month_jobs.py" ] && say "   !! $FIN/month_jobs.py is still there" || say "   $FIN/month_jobs.py removed"
  say "   the mj_* tables the data step made stay (empty or nearly; nothing reads them now); the database backup: $DBBAK"
  say "   finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout sleep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $ALL; do [ -n "${TO[$n]}" ] || { say "!! [1/9] TO_PINS.md5 does not name finance/$n - nothing installed"; exit 1; }; done
for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [1/9] $FIN/$n is missing - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/9] $DB is missing - nothing installed"; exit 1; }
AT=0; for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] && AT=$((AT+1)); done
[ "$AT" = 4 ] && { say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/9] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
for n in $EDITED; do
  C=$(m5 "$FIN/$n"); [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/9] $FIN/$n is ${C:0:8}, expected ${FROM[$n]:0:8} - it changed after this kit was built: STOP, nothing installed"
done
DM=$(m5 "$DUTY_MAP"); [ "$DM" = "$DMAP_PIN" ] || stop_unlocked "!! [2/9] the duty map $DUTY_MAP is ${DM:0:8}, the kit was built against ${DMAP_PIN:0:8} - it changed after this kit was built (a git pull?): STOP, nothing installed. Tell Claude."
[ -e "$FIN/month_jobs.py" ] && stop_unlocked "!! [2/9] $FIN/month_jobs.py is already there ($(m5 "$FIN/month_jobs.py" | cut -c1-8)) - STOP, nothing installed"
say "[2/9] live pins exact: finance_app.py ${FROM[finance_app.py]:0:8}, aaj_duties.json ${FROM[aaj_duties.json]:0:8}, aaj_seed.py ${FROM[aaj_seed.py]:0:8}, the duty map ${DMAP_PIN:0:8}; month_jobs.py not there yet"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s687.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused the live files - nothing installed"; }
for n in $ALL; do
  [ "$(m5 "$SCR/built/finance/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [3/9] rebuilt, $n is $(m5 "$SCR/built/finance/$n" | cut -c1-8), not ${TO[$n]:0:8} - nothing installed"
done
for py in "$APY" "$VPY"; do for n in finance_app.py aaj_seed.py month_jobs.py; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/finance/$n" || stop_unlocked "!! [3/9] $n does not compile on $py - nothing installed"
done; done
"$APY" -c "import json,sys; json.load(open(sys.argv[1],encoding='utf-8'))" "$SCR/built/finance/aaj_duties.json" || stop_unlocked "!! [3/9] aaj_duties.json does not read as JSON - nothing installed"
say "[3/9] rebuilt here from this box's live bytes ($(grep -c '^edit ok' "$SCR/make.txt") counted edits): all four at their TO pins; they compile under both pythons"

mkscratch "$SCR/old"; mkscratch "$SCR/new"
for n in $ALL; do \cp -p "$SCR/built/finance/$n" "$SCR/new/$n"; done
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/9] no copy of the database - nothing installed"
WOUT="$(walk --new "$SCR/new" --db "$SCR/walk.db" --scratch "$SCR/w1" --kit "$KDIR" --root "$ROOT" --old "$SCR/old")"; R="$(echo "$WOUT" | tail -1)"
[ "$R" = "$GREEN" ] || { echo "$WOUT" | grep -E '^  RED' | head -12; stop_unlocked "!! [4/9] the walk on the rebuilt files is not green ($R) - nothing installed"; }
COUT="$(walk --control "$SCR/old" --db "$SCR/walk.db" --scratch "$SCR/w0" --kit "$KDIR")"; R0="$(echo "$COUT" | tail -1)"
[ "$R0" = "$CONTROL" ] || stop_unlocked "!! [4/9] the control on the live files is not as expected ($R0) - nothing installed"
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || stop_unlocked "!! [4/9] $FIN/$n changed during the walk - nothing installed"; done
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/9] finance healthz $f0 before the install - nothing installed"
rm -f "$SCR/walk.db"
say "[4/9] the walk on a copy of the database: $GREEN (every route and role, every line at its dates, every other list unchanged, 15 mutants caught); the control on the live files: $R0; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the rebuild, the walk and the control green; NOTHING written"; exit 0; fi

{ (umask 077; copydb "$DB" "$DBBAK") && chmod 600 "$DBBAK"; } || { rm -f "$DBBAK"; stop_unlocked "!! [5/9] could not write the database backup $DBBAK - nothing placed"; }
for n in $EDITED; do { \cp -p "$FIN/$n" "$(bak $n)" && [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ]; } || stop_unlocked "!! [5/9] could not write the backup $(bak $n) - nothing placed"; done
for n in $ALL; do
  STG="$FIN/.$n.s687"
  { cat "$SCR/built/finance/$n" > "$STG" && [ "$(m5 "$STG")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s687; stop_unlocked "!! [5/9] could not stage $n - nothing placed"; }
  chmod --reference="$FIN/finance_app.py" "$STG" 2>/dev/null; chown --reference="$FIN/finance_app.py" "$STG" 2>/dev/null
done
PLACED=1
for n in month_jobs.py aaj_duties.json aaj_seed.py finance_app.py; do mv -f "$FIN/.$n.s687" "$FIN/$n" || restore "the rename of $n"; done
for n in $ALL; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "read back $n"; done
say "[5/9] placed and read back: $(for n in $ALL; do printf '%s %s  ' "$n" "${TO[$n]:0:8}"; done)(backups *.bak_S687_*; database $DBBAK, mode $(stat -c %a "$DBBAK"))"

SOUT="$("$APY" -B "$KDIR/cfg_s687.py" "$DB" "$FIN" 2>&1)" || { echo "$SOUT"; restore "the data step"; }
echo "$SOUT" | grep -q '^data step: tables: ' || { echo "$SOUT"; restore "the data step said nothing"; }
say "[6/9] $SOUT"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1"
# Without a login the front gate answers 302 for ANY path, a missing one too, so these two prove the gate, not the route.
c2=$(fhealth /finance/monthjobs); case "$c2" in 302|401|303) ;; *) restore "/finance/monthjobs answered $c2 without a login";; esac
c3=$(fhealth /finance/aaj); case "$c3" in 302|401|303) ;; *) restore "/finance/aaj answered $c3 without a login";; esac
# The live process says it: a mount that fails prints 'month_jobs NOT mounted: ...' to the journal (finance_app's guarded block).
command -v "$JOURNALCTL" >/dev/null 2>&1 || restore "no $JOURNALCTL to read the service's own word on the mount"
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'month_jobs|NOT mounted|ImportError|ModuleNotFoundError')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'month_jobs|NOT mounted|ImportError|ModuleNotFoundError' | head -5; restore "journal: $JR line(s) naming month_jobs, an import error or a part NOT mounted since the restart"; }
say "[7/9] $FSVC restarted at $T0: healthz $c1; /finance/monthjobs $c2 and /finance/aaj $c3 without a login (the gate); the journal since the restart ($(printf '%s\n' "$JL" | grep -c .) line(s)) names no month_jobs, import error or 'NOT mounted'"

mkscratch "$SCR/placed"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed files"
POUT="$(walk --new "$SCR/placed" --db "$SCR/walk2.db" --scratch "$SCR/w2" --kit "$KDIR" --only inner)"; R="$(echo "$POUT" | tail -1)"
rm -f "$SCR/walk2.db"
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/9]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN_PLACED" ] || { echo "$POUT" | grep -E '^  RED' | head -8; restore "the walk on the placed files: $R"; }
say "[8/9] the walk on the placed files (the real app as it now stands, on a copy): $R"
release_lock
say "[9/9] the build lock released"
say "undo (one line): \\cp -p $(bak finance_app.py) $FIN/finance_app.py && \\cp -p $(bak aaj_duties.json) $FIN/aaj_duties.json && \\cp -p $(bak aaj_seed.py) $FIN/aaj_seed.py && rm -f $FIN/month_jobs.py && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Darpan's Aaj list has the month's jobs; the owner's page is /finance/monthjobs/owner."
exit 0
