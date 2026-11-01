#!/bin/bash
# =============================================================================
#  install_S690_AMIR_BATCH_FIX.sh · kit S690 (01-Nov-2026, Sanjeevni session 369) · Amir corrects a wrong or minus batch by a Marg voucher
#  pair (STOCK RECEIVE into the minus batch, STOCK ISSUE from the batch that has the stock), never by a sale bill; he saves the Batch Stock
#  (whole store) at the end of every visit as step 4's third report; the server rechecks within five minutes and tells him line by line.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s690kit && cp -rp /root/deploy/repo/deploy_kits/S690_AMIR_BATCH_FIX /tmp/s690kit && bash /tmp/s690kit/install_S690_AMIR_BATCH_FIX.sh
#  (DRY=1 before bash: every gate, the walk, the control and the proof on copies -- nothing written.)
#   /root/finance/expiry_watch.py   23e0a5bf -> TO   the pair, the fix table, the confirmation, run --if-new, the owner line
#   /root/finance/amir_day.py       a0907b74 -> TO   step 4's third report: Batch Stock (none / wait / ok / bad)
#   the crontab: ONE line added (every 5 minutes, expiry_watch.py run --if-new); nothing else touched; removed again on undo
#  THE GATE THAT DECIDES: on this box, on COPIES of the database and the spine and the live archive (read only), the OLD and the NEW watch
#  run once each -- the newest run's lines identical apart from the figures S690 adds; the walk 39 of 39 on its own rows; the control red.
#  Data step: the watch run once after placing, so Amir's card carries the vouchers at once.  Restarts clinic-finance only.
#  Red after placing: both files back, the cron line removed, finance restarted.
# =============================================================================
set -u
KIT="S690_AMIR_BATCH_FIX"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
ARCHIVE="${ARCHIVE:-$ROOT/marg_ingest/archive}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
F1="finance/expiry_watch.py"; F2="finance/amir_day.py"
FROM1="23e0a5bf92f9f697bfbbda87c91bdee5"; FROM2="a0907b74fb90584d9440551aa82f9928"
TO1="$(awk -v f="$F1" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; TO2="$(awk -v f="$F2" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
CRONLINE="*/5 * * * * cd $ROOT/finance && $VPY -B expiry_watch.py run --if-new >> $ROOT/finance/spine/near_expiry.log 2>&1"
CRONKEY="expiry_watch.py run --if-new"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s690_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; CRON_ADDED=0
GREEN="39 of 39 green"
CONTROL="1 S690 check(s) red . 0 green"
BAK1="$ROOT/$F1.bak_S690_${FROM1:0:8}"; BAK2="$ROOT/$F2.bak_S690_${FROM2:0:8}"
STG1="$ROOT/finance/.expiry_watch.py.s690"; STG2="$ROOT/finance/.amir_day.py.s690"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s690.py" "$@" 2>&1); }
CRONBAK="$ROOT/finance/spine/crontab.bak_S690_$STAMP"
cron_read() {   # the crontab to a file; 0 = read (maybe empty: 'no crontab' is not a fault), 1 = could not read -- a failed read is never piped back
  local out; out="$("$CRONTAB" -l 2>"$SCR/cron.err")"; local rc=$?
  if [ $rc -ne 0 ] && ! grep -q -i "no crontab" "$SCR/cron.err"; then return 1; fi
  printf '%s\n' "$out" | sed '/^$/d' > "$SCR/cron.now"; return 0
}
cron_has() { cron_read && grep -F -q -- "$CRONKEY" "$SCR/cron.now"; }
cron_add() { cron_read || return 1; \cp -p "$SCR/cron.now" "$CRONBAK" 2>/dev/null; { cat "$SCR/cron.now"; echo "$CRONLINE"; } | "$CRONTAB" - && CRON_ADDED=1; }
cron_del() { cron_read || return 1; grep -F -v -- "$CRONKEY" "$SCR/cron.now" | "$CRONTAB" - ; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  PLACED=2
  \cp -p "$BAK1" "$ROOT/$F1" || say "   !! could not put back $ROOT/$F1"; rm -f "$STG1"
  \cp -p "$BAK2" "$ROOT/$F2" || say "   !! could not put back $ROOT/$F2"; rm -f "$STG2"
  [ "$CRON_ADDED" = 1 ] && { cron_del && say "   the cron line removed again"; }
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   $ROOT/$F1 $(m5 "$ROOT/$F1" | cut -c1-8) (expected ${FROM1:0:8}); $ROOT/$F2 $(m5 "$ROOT/$F2" | cut -c1-8) (expected ${FROM2:0:8})"
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
[ -n "$TO1" ] && [ -n "$TO2" ] || { say "!! [1/8] TO_PINS.md5 does not name both files - nothing installed"; exit 1; }
[ -f "$ROOT/$F1" ] && [ -f "$ROOT/$F2" ] && [ -f "$DB" ] && [ -f "$SPINE" ] && [ -d "$ARCHIVE" ] || { say "!! [1/8] a live file, $DB, $SPINE or $ARCHIVE is missing - nothing installed"; exit 1; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$F1")" = "$TO1" ] && [ "$(m5 "$ROOT/$F2")" = "$TO2" ]; then
  cron_has || { [ "${DRY:-0}" = 1 ] || { cron_add && say "-- the files were already the kit's; the cron line was missing and is added now"; }; }
  say "-- ALREADY INSTALLED: both files are the kit's. Nothing else written. finance healthz $(fhz)"; exit 0
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
C1=$(m5 "$ROOT/$F1"); [ "$C1" = "$FROM1" ] || stop_unlocked "!! [2/8] $ROOT/$F1 is ${C1:0:8}, expected ${FROM1:0:8} - it changed after this kit was built: STOP, nothing installed"
C2=$(m5 "$ROOT/$F2"); [ "$C2" = "$FROM2" ] || stop_unlocked "!! [2/8] $ROOT/$F2 is ${C2:0:8}, expected ${FROM2:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pins exact: expiry_watch.py ${FROM1:0:8}, amir_day.py ${FROM2:0:8}"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s690.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live files - nothing installed"; }
[ "$(m5 "$SCR/built/$F1")" = "$TO1" ] || stop_unlocked "!! [3/8] rebuilt, expiry_watch.py is $(m5 "$SCR/built/$F1" | cut -c1-8), not ${TO1:0:8} - nothing installed"
[ "$(m5 "$SCR/built/$F2")" = "$TO2" ] || stop_unlocked "!! [3/8] rebuilt, amir_day.py is $(m5 "$SCR/built/$F2" | cut -c1-8), not ${TO2:0:8} - nothing installed"
for py in "$APY" "$VPY"; do for f in "$F1" "$F2"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$f" || stop_unlocked "!! [3/8] $f does not compile on $py - nothing installed"; done; done
# the walk needs the neighbours beside the files under test: a root of copies with the two rebuilt files in it
mkdir -p "$SCR/newroot/finance" && cp -rp "$ROOT/finance/." "$SCR/newroot/finance/" 2>/dev/null; rm -f "$SCR/newroot/finance/finance.db"* "$SCR/newroot/finance/spine/spine.db"*
\cp -p "$SCR/built/$F1" "$SCR/newroot/$F1" && \cp -p "$SCR/built/$F2" "$SCR/newroot/$F2" || stop_unlocked "!! [3/8] could not lay the walk's root - nothing installed"
say "[3/8] rebuilt here from this box's live bytes: at their TO pins ${TO1:0:8} / ${TO2:0:8}; both compile under both pythons"

R=$(walk --new "$SCR/newroot" --scratch "$SCR/w1" | tail -1)
[ "$R" = "$GREEN" ] || { walk --new "$SCR/newroot" --scratch "$SCR/w1b" | grep -E 'RED' | head -12 | sed 's/^/         /'; PLACED=2; stop_unlocked "!! [4/8] the walk on the rebuilt files is not green ($R) - nothing installed (kept in $SCR)"; }
R0=$(walk --old "$ROOT" --scratch "$SCR/w0" | tail -1)
[ "$R0" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live files is not as expected ($R0) - nothing installed (kept in $SCR)"; }
copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
copydb "$SPINE" "$SCR/spine.db" || stop_unlocked "!! [4/8] no copy of the spine - nothing installed"
P=$(walk --proof --old-root "$ROOT" --new "$SCR/newroot" --db "$SCR/walk.db" --spine "$SCR/spine.db" --archive "$ARCHIVE" --scratch "$SCR/wp")
PL="$(echo "$P" | tail -1)"
echo "$P" | grep -E '^  --  |RED' | head -30 | sed 's/^/         /'
case "$PL" in "proof: old "*" . IDENTICAL . report "*) ;; *) PLACED=2; stop_unlocked "!! [4/8] the old = new proof is not clean ($PL) - nothing installed (kept in $SCR)";; esac
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk: $R; the control on the live files: $R0; $PL (above); finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk, the control and the proof green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK1 - nothing placed"
{ \cp -p "$ROOT/$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK2 - nothing placed"
{ cat "$SCR/built/$F1" > "$STG1" && [ "$(m5 "$STG1")" = "$TO1" ]; } || { rm -f "$STG1"; stop_unlocked "!! [5/8] could not stage expiry_watch.py - nothing placed"; }
{ cat "$SCR/built/$F2" > "$STG2" && [ "$(m5 "$STG2")" = "$TO2" ]; } || { rm -f "$STG1" "$STG2"; stop_unlocked "!! [5/8] could not stage amir_day.py - nothing placed"; }
for p in "$STG1:$ROOT/$F1" "$STG2:$ROOT/$F2"; do chmod --reference="${p#*:}" "${p%%:*}" 2>/dev/null; chown --reference="${p#*:}" "${p%%:*}" 2>/dev/null; done
PLACED=1
mv -f "$STG1" "$ROOT/$F1" || restore "the rename of expiry_watch.py"
mv -f "$STG2" "$ROOT/$F2" || restore "the rename of amir_day.py"
[ "$(m5 "$ROOT/$F1")" = "$TO1" ] && [ "$(m5 "$ROOT/$F2")" = "$TO2" ] || restore "read back"
say "[5/8] placed and read back: expiry_watch.py ${TO1:0:8}, amir_day.py ${TO2:0:8} (backups $BAK1, $BAK2)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/step/4); case "$c2" in 302|401|303|403) ;; *) restore "Amir's step 4 answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; Amir's step 4 $c2 without a login (the login gate, expected); journal clean"
cron_has || cron_add || restore "the cron line could not be added"
( cd "$ROOT/finance" && timeout 600 "$VPY" -B expiry_watch.py run > "$SCR/run.txt" 2>&1 ) || { cat "$SCR/run.txt" | tail -5; restore "the watch's first run on the placed file"; }
say "[7/8] the cron line $( [ "$CRON_ADDED" = 1 ] && echo "added (the crontab as it was: $CRONBAK)" || echo 'was already there' ) (every 5 minutes, run --if-new); the watch run once: $(tail -1 "$SCR/run.txt" | cut -c1-160)"
R=$(walk --new "$ROOT" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
release_lock
say "[8/8] the walk on the placed files: $R; the build lock released"
say "undo (one line): \\cp -p $BAK1 $ROOT/$F1 && \\cp -p $BAK2 $ROOT/$F2 && (crontab -l | grep -F -v -- '$CRONKEY' | crontab -) && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Amir's card carries the voucher pairs; the Batch Stock is step 4's third report and confirms them within five minutes."
exit 0
