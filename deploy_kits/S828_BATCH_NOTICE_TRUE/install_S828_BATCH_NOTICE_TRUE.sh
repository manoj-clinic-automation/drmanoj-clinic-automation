#!/bin/bash
# =============================================================================
#  install_S828_BATCH_NOTICE_TRUE.sh · kit S828 (14-Nov-2026, Sanjeevni session 457)
#  The owner's phone said "Batch fixes: 0 done today, 18 left" at ~09:01 while Amir's card said 8 fixed, 5 left: the message went before
#  the Batch Stock's Issues were judged against the day's sales (09:05), and it counted raw voucher rows. /root/finance/owner_notice.py
#  471859b3 -> TO: "Amir's work" waits while a batch row waits for the day's sales (at most owner_notice.batch_hold_min = 180 minutes, a
#  setting), and says Amir's card's own two numbers. REBUILT HERE from the live bytes by make_s828.py.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s828kit && cp -rp /root/deploy/repo/deploy_kits/S828_BATCH_NOTICE_TRUE /tmp/s828kit && bash /tmp/s828kit/install_S828_BATCH_NOTICE_TRUE.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S828_BATCH_NOTICE_TRUE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"; ADB="${ADB:-$ROOT/assetapp/assets.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F="finance/owner_notice.py"
FROM="471859b3848eab1b2057f3b2af378242"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s828_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
SCHEMA="$ROOT/finance/purchase_schema.sql"
GREEN="walk_s828: 0 check(s) failed"
CONTROL="walk_s828: 5 check(s) failed"
BAK="$ROOT/$F.bak_S828_${FROM:0:8}"; STG="$ROOT/finance/.owner_notice.py.s828"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhealth() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { rm -f "$STG"; release_lock; [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$1" "$2" "$SCR/new/shared" "$DB" 2>&1); }
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
[ -n "$TO" ] && [ -f "$ROOT/$F" ] && [ -f "$DB" ] && [ -f "$ROOT/finance/expiry_watch.py" ] || { say "!! [1/7] the TO pin, $ROOT/$F, $DB or expiry_watch.py is missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$F")" = "$TO" ]; then say "-- $KIT is ALREADY INSTALLED (owner_notice.py ${TO:0:8}); nothing to do. finance healthz $(fhz)"; exit 0; fi
mkdir -p "$SCR/built" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken $(TZ=Asia/Kolkata date '+%d-%m %H:%M IST') by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
C=$(m5 "$ROOT/$F"); [ "$C" = "$FROM" ] || stop "!! [2/7] $ROOT/$F is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
"$APY" -B make_s828.py "$ROOT/$F" "$SCR/built/owner_notice.py" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused - nothing installed"; }
[ "$(m5 "$SCR/built/owner_notice.py")" = "$TO" ] || stop "!! [2/7] rebuilt, the file is not at its TO pin - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/owner_notice.py" || stop "!! [2/7] owner_notice.py does not compile on $py - nothing installed"; done
mkdir -p "$SCR/new/finance" "$SCR/new/shared" "$SCR/old/finance"
for f in "$ROOT"/finance/*.py "$ROOT"/finance/*.json "$ROOT"/finance/*.sql; do [ -f "$f" ] && cp -p "$f" "$SCR/new/finance/" && cp -p "$f" "$SCR/old/finance/"; done
for f in "$ROOT"/shared/*.py; do [ -f "$f" ] && cp -p "$f" "$SCR/new/shared/"; done
cp -p "$SCR/built/owner_notice.py" "$SCR/new/finance/owner_notice.py"
say "[2/7] live pin exact (${FROM:0:8}); rebuilt here from the live bytes at its TO pin (${TO:0:8}); it compiles on both pythons"

R=$(walk walk_s828.py "$SCR/new/finance" | tail -1)
[ "$R" = "$GREEN" ] || { walk walk_s828.py "$SCR/new/finance" | grep -E 'FAIL|raised' | head -10 | sed 's/^/         /'; PLACED=2; stop "!! [3/7] the walk on the rebuilt file: $R - nothing installed (kept in $SCR)"; }
R0=$(walk walk_s828.py "$SCR/old/finance" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop "!! [3/7] the control on the live file: $R0 (expected $CONTROL) - nothing installed (kept in $SCR)"; }
say "[3/7] walk_s828: $R; its control on the live file: $R0"

f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
say "[4/7] finance healthy before the install"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [5/7] could not write the backup - nothing placed"
{ cat "$SCR/built/owner_notice.py" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || stop "!! [5/7] could not stage the file - nothing placed"
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
OLDPIDS="$(pids_of | tr '\n' ' ')"
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
find "$ROOT/finance" -maxdepth 2 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[5/7] placed and read back: owner_notice.py ${TO:0:8} (backup ${BAK##*/})"
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
R=$(walk walk_s828.py "$SCR/placed/finance" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 7 ] && R="rehearsal: a forced red at [7/7]"
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
say "[7/7] by the placed file: the walk $R"
release_lock
say "undo (one line): \\cp -p $BAK $ROOT/$F && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Your Amir's-work message now waits for the batch check and gives the same two numbers as Amir's card."
exit 0
