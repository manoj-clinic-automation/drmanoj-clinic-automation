#!/bin/bash
# =============================================================================
#  install_S626_AMIR_PACK_STAYS.sh · kit S626 (22-Oct-2026, Sanjeevni session 338) · F-988
#  Amir's month pack stays on his page: the newest ready month is always listed (seen or not) until the next month's pack is ready;
#  a seen month keeps its links, only the Dekh liya button goes. Every ready UNSEEN month still shows, as before.
#
#   /root/finance/amir_day.py   1169a3d6 -> 2c99c29e   (_s446_packs and the pack row in _card_rows; nothing else)
#  finance.db: not written. No setting, no DDL, no crontab change, no other file. One restart of clinic-finance.
#  ORDER: gates (window 08:02-23:49 IST, SUMS, KIT_ID) -> the build lock -> ALREADY INSTALLED? -> the FROM pin -> build from the live
#  bytes (make_s626.py) -> compile (both pythons) -> scratch: the live finance folder twice (OLD, NEW) and two copies of finance.db ->
#  walk OLD (must be red on F-988) then NEW (12/0) -> DRY stops -> backup -> DOCTOR_AUTO_OFF -> staged + renamed -> md5 read back -> ONE
#  restart -> healthz 200, /finance/amir 302 without a login -> journal clean -> DOCTOR_AUTO_OFF removed -> lock released -> DONE.
#  Red after placing: the backup back, one restart, healthz.  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S626_AMIR_PACK_STAYS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
N="amir_day.py"
FROM=1169a3d6ae451ebb4c9806052de0856c
TO=2c99c29eff254c9abfe1374b2e3f8ba3
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s626_inst_$STAMP"
BAK="$FIN/$N.bak_S626_${FROM:0:8}"
STG="$FIN/.$N.s626"
PLACED=0
TOOK_LOCK=0
OFF_MINE=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting $N back from $BAK"
  \cp -p "$BAK" "$FIN/$N" || say "   !! could not put back $N"
  rm -f "$STG"
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  say "   $FIN/$N $(m5 "$FIN/$N") (expected $FROM); finance healthz $h"
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep sleep find; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
{ { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -f "$FIN/$N" ] && [ -f "$DB" ] || { say "!! [1/8] $FIN/$N or $DB is not there - nothing installed"; exit 1; }
if [ "$(m5 "$FIN/$N")" = "$TO" ]; then say "-- ALREADY INSTALLED: $N is the kit's ($TO). Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null); healthz $(health /finance/healthz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
  exit 3
fi
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

C="$(m5 "$FIN/$N")"
[ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $FIN/$N is $C, expected $FROM - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pin exact: $N ${FROM:0:8}; read only (not pinned): packs.py $(m5 "$FIN/packs.py" | cut -c1-8) . supplier_msg.py $(m5 "$FIN/supplier_msg.py" | cut -c1-8)"

mkdir -p "$SCR/built" "$SCR/old" "$SCR/new" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B "$KDIR/make_s626.py" "$FIN/$N" "$SCR/built/$N" || stop_unlocked "!! [3/8] the build from the live bytes failed - nothing installed"
[ "$(m5 "$SCR/built/$N")" = "$TO" ] || stop_unlocked "!! [3/8] the built file is not at TO - nothing installed"
"$APY" -m py_compile "$SCR/built/$N" && "$VPY" -m py_compile "$SCR/built/$N" || stop_unlocked "!! [3/8] the built file does not compile - nothing installed"
say "[3/8] built from the live bytes: $N $TO; compiles under both pythons"

\cp -p "$FIN"/*.py "$SCR/old/" && \cp -p "$FIN"/*.py "$SCR/new/" && \cp -p "$SCR/built/$N" "$SCR/new/$N" || stop_unlocked "!! [4/8] could not lay the scratch folders - nothing installed"
copydb "$DB" "$SCR/old.db" && copydb "$DB" "$SCR/new.db" || stop_unlocked "!! [4/8] could not copy the database - nothing installed"
( cd "$SCR" && "$VPY" -B "$KDIR/walk_s626.py" "$SCR/old" "$SCR/old.db" OLD ) > "$SCR/walk_old.txt" 2>&1; WO=$?
( cd "$SCR" && "$VPY" -B "$KDIR/walk_s626.py" "$SCR/new" "$SCR/new.db" NEW ) > "$SCR/walk_new.txt" 2>&1; WN=$?
say "       walk OLD: $(grep '^WALK' "$SCR/walk_old.txt") (the control: red on F-988 is the pass) . walk NEW: $(grep '^WALK' "$SCR/walk_new.txt")"
grep -E 'the copy:' "$SCR/walk_new.txt" | sed 's/^/       /'
[ "$WO" = 0 ] || { cat "$SCR/walk_old.txt"; stop_unlocked "!! [4/8] the negative control is not red on the OLD file - nothing installed"; }
[ "$WN" = 0 ] || { cat "$SCR/walk_new.txt"; stop_unlocked "!! [4/8] the walk on the NEW file is red - nothing installed"; }
say "[4/8] the walks: OLD red on F-988 (the control), NEW green"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and both walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$FIN/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || stop_unlocked "!! [5/8] could not write the backup $BAK - nothing placed"
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [5/8] could not write $OFFSW - nothing placed"
fi
{ \cp -p "$FIN/$N" "$STG" && cat "$SCR/built/$N" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [5/8] could not stage $N - nothing placed"; }
PLACED=1
mv -f "$STG" "$FIN/$N" || restore "the rename"
[ "$(m5 "$FIN/$N")" = "$TO" ] || restore "the md5 read back"
say "[5/8] placed: $FIN/$N $TO (backup $BAK)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/amir)
case "$c2" in 302|401|303) ;; *) restore "/finance/amir answered $c2 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $SVC restarted at $T0 (the box's clock) and active - healthz $c1 - /finance/amir $c2 without a login; journal clean"
copydb "$DB" "$SCR/after.db" || restore "could not copy the database for the read-back walk"
( cd "$SCR" && "$VPY" -B "$KDIR/walk_s626.py" "$FIN" "$SCR/after.db" NEW ) > "$SCR/walk_live.txt" 2>&1 || { cat "$SCR/walk_live.txt"; restore "the walk on the PLACED file is red"; }
say "       the placed file walked (imported from $FIN, on a fresh copy of the database): $(grep '^WALK' "$SCR/walk_live.txt"); $(grep 'the copy:' "$SCR/walk_live.txt" | sed 's/^ *//')"
if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; say "[7/8] $OFFSW removed (this kit's); nothing else changed (no database write, no setting, no crontab line)"
else say "[7/8] $OFFSW not this kit's -- left as found; nothing else changed (no database write, no setting, no crontab line)"; fi
release_lock
say "[8/8] the build lock released"
say "undo (one line): \\cp -p $BAK $FIN/$N && $SYSTEMCTL restart $SVC"
say "$KIT: DONE"
exit 0
