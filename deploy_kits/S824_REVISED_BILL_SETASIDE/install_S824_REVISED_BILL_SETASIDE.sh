#!/bin/bash
# =============================================================================
#  install_S824_REVISED_BILL_SETASIDE.sh · kit S824 (14-Nov-2026, Sanjeevni session 455) · F-1378
#  Janta's revised bill JP21965 (scan B-0271, Rs 3,205 = Rs 4,450 less the Rs 1,245 return) was set aside on 08-Nov as a "second
#  scan" of B-0118; S740's revised-bill road reads only captured scans, so October's return shows pending.
#  /root/finance/scan_register.py 9262c5dc -> TO : _s740_revised also reads the pharmacy scans the scan app SET ASIDE as a second scan
#  (status 'rejected', dup_of set, not a page of a bill) -- by the same rules as a captured scan (the same dealer and bill number, the
#  paper less the return within _s740_tol, more than Rs 1 off the paper); a captured scan is always tried first. REBUILT HERE from the
#  live bytes by make_s824.py.  The proof reads the returns on this box's own databases (read-only) with the old and the new file and
#  places only on PROVEN: Janta settled by B-0271, every other return the same, B-0264 (the true double) settling nothing.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s824kit && cp -rp /root/deploy/repo/deploy_kits/S824_REVISED_BILL_SETASIDE /tmp/s824kit && bash /tmp/s824kit/install_S824_REVISED_BILL_SETASIDE.sh
#  (DRY=1 before bash: every gate, the walks and the proof; NOTHING written.)
# =============================================================================
set -u
KIT="S824_REVISED_BILL_SETASIDE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F="finance/scan_register.py"
FROM="9262c5dc05f0aa3cd52595b0894cd8ca"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s824_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
SCHEMA="$ROOT/finance/purchase_schema.sql"
GREEN="walk_s824: 0 check(s) failed (0 of them S824 checks, 0 S740 checks)"
CONTROL="walk_s824: 7 check(s) failed (7 of them S824 checks, 0 S740 checks)"
BAK="$ROOT/$F.bak_S824_${FROM:0:8}"; STG="$ROOT/finance/.scan_register.py.s824"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$1" "$2" "$SCHEMA" "$SCR/new/shared" 2>&1); }
pread() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/proof_s824.py" read "$1" "$SCR/new/shared" "$DB" "$ADB" "$2" 2>&1); }
pcomp() { "$APY" -B "$KDIR/proof_s824.py" compare "$1" "$2" 2>&1; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the file back"
  PLACED=2
  \cp -p "$BAK" "$ROOT/$F" || say "   !! could not put back $ROOT/$F -- the old file is $BAK"
  rm -f "$STG"
  find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$F $(m5 "$ROOT/$F" | cut -c1-8) (expected ${FROM:0:8}); finance healthz $(wait200 fhz). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop() { say "$1"; release_lock; exit "${2:-1}"; }
pids_of() { local m; m="$("$SYSTEMCTL" show -p MainPID --value "$FSVC" 2>/dev/null)"; [ -n "$m" ] && [ "$m" != 0 ] && { echo "$m"; pgrep -P "$m" 2>/dev/null; }; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout pgrep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/7] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ -f "$ROOT/$F" ] && [ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$SCHEMA" ] || { say "!! [1/7] the TO pin, $ROOT/$F, $DB, $ADB or purchase_schema.sql is missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$F")" = "$TO" ]; then say "-- $KIT is ALREADY INSTALLED (scan_register.py ${TO:0:8}); nothing to do. finance healthz $(fhz)"; exit 0; fi
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop "!! [2/7] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s824.py "$ROOT/$F" "$SCR/built/scan_register.py" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/scan_register.py")" = "$TO" ] || stop "!! [2/7] rebuilt, the file is not at its TO pin - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/scan_register.py" || stop "!! [2/7] scan_register.py does not compile on $py - nothing installed"; done
mkdir -p "$SCR/new/finance" "$SCR/new/shared" "$SCR/old/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/" && cp -p "$f" "$SCR/old/finance/"; done
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
cp -p "$SCR/built/scan_register.py" "$SCR/new/finance/scan_register.py"
say "[2/7] live pin exact (${FROM:0:8}); rebuilt here from the live bytes at its TO pin (${TO:0:8}); it compiles on both pythons"

R=$(walk walk_s824.py "$SCR/new/finance" | tail -1)
[ "$R" = "$GREEN" ] || { walk walk_s824.py "$SCR/new/finance" | grep -E 'FAIL|raised' | head -10 | sed 's/^/         /'; PLACED=2; stop "!! [3/7] the walk on the rebuilt file: $R - nothing installed (kept in $SCR)"; }
R0=$(walk walk_s824.py "$SCR/old/finance" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop "!! [3/7] the control on the live file: $R0 (expected $CONTROL) - nothing installed (kept in $SCR)"; }
WN="$(walk walk_s740.py "$SCR/new/finance" | grep -E '^  FAIL |^walk_s740:')"; WO="$(walk walk_s740.py "$SCR/old/finance" | grep -E '^  FAIL |^walk_s740:')"
[ -n "$WN" ] && [ "$WN" = "$WO" ] || { PLACED=2; stop "!! [3/7] S740's own walk reads differently on the rebuilt file ($(printf '%s\n' "$WN" | tail -1)) than on the live one ($(printf '%s\n' "$WO" | tail -1)) - nothing installed (kept in $SCR)"; }
say "[3/7] walk_s824: $R; its control on the live file: $R0; S740's own walk the same on both ($(printf '%s\n' "$WN" | tail -1))"

pread "$SCR/old/finance" "$SCR/old.json" > "$SCR/p_old.txt"; pread "$SCR/new/finance" "$SCR/new.json" > "$SCR/p_new.txt"
pcomp "$SCR/old.json" "$SCR/new.json" > "$SCR/proof.txt"
P=$(tail -1 "$SCR/proof.txt")
say "---------------------------------------------------------------- the proof (read only)"
sed 's/^/   /' "$SCR/p_old.txt" "$SCR/p_new.txt" "$SCR/proof.txt"
say "----------------------------------------------------------------"
[ "$P" = "PROOF S824: PROVEN" ] || { PLACED=2; stop "!! [4/7] $P - nothing installed (kept in $SCR). Send a photo of this screen to Claude."; }
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] $P on this box's own databases (both opened read-only); finance healthy"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the proof green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [5/7] could not write the backup - nothing placed"
{ cat "$SCR/built/scan_register.py" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [5/7] could not stage the file - nothing placed"
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
OLDPIDS="$(pids_of | tr '\n' ' ')"
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] placed and read back: scan_register.py ${TO:0:8} (backup ${BAK##*/})"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/step/1); case "$c2" in 302|401|403) ;; *) restore "Amir's page answered $c2 without a login (expected 302, 401 or 403)";; esac
c3=$(fhealth /finance/purchase/page/check); case "$c3" in 302|401|403) ;; *) restore "the step view answered $c3 without a login (expected 302, 401 or 403)";; esac
c4=$(fhealth /finance/purchase/api/s738/scan/1); case "$c4" in 302|401|403) ;; *) restore "the scan door answered $c4 without a login (expected 302, 401 or 403)";; esac
NEWPIDS="$(pids_of | tr '\n' ' ')"
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JL="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager -o short 2>/dev/null)"
  for p in $OLDPIDS; do JL="$(printf '%s\n' "$JL" | grep -v -E "\[$p\]:")"; done
  JR="$(printf '%s\n' "$JL" | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|Logging error')"
  [ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'Traceback|Error' | head -6 | sed 's/^/         /'; restore "journal: $JR error line(s) from the new master ($NEWPIDS) since the restart"; }
fi
say "[6/7] $FSVC restarted at $(TZ=Asia/Kolkata date '+%H:%M IST'): healthz $c1; without a login Amir's page $c2, the step view $c3, the scan door $c4; journal clean"
mkdir -p "$SCR/placed/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$SCR/placed/finance/"; done
R=$(walk walk_s824.py "$SCR/placed/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
pread "$SCR/old/finance" "$SCR/old7.json" > /dev/null; pread "$SCR/placed/finance" "$SCR/placed.json" > /dev/null   # both read now (the live data moves)
P7=$(pcomp "$SCR/old7.json" "$SCR/placed.json" | tail -1)
[ "$P7" = "PROOF S824: PROVEN" ] || restore "the proof by the placed file: $P7"
say "[7/7] by the placed file: the walk $R; $P7"
release_lock
say "undo (one line): \\cp -p $BAK $ROOT/$F && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Janta's bill 21965 of 2 October now reads settled by its revised bill (scan B-0271) -- your step view: https://followup.dr-manoj.in/finance/purchase/page/check?month=2026-10"
exit 0
