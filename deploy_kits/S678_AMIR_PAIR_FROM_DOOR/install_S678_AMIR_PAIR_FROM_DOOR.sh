#!/bin/bash
# =============================================================================
#  install_S678_AMIR_PAIR_FROM_DOOR.sh · kit S678 (29-Oct-2026, Sanjeevni session 367) · Amir's step 4: a report the server's OWN door
#  holds (mi_file, VERIFIED, today's Marg stamp, covering the 1st..today) is "at the server -- being read", never "nahi aayi -- Dobara
#  banaiye ... file band kijiye".  The tick and the bill list still wait for purchase_export's rows (manojz's leg).  No data step.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s678kit && cp -rp /root/deploy/repo/deploy_kits/S678_AMIR_PAIR_FROM_DOOR /tmp/s678kit && bash /tmp/s678kit/install_S678_AMIR_PAIR_FROM_DOOR.sh
#  (DRY=1 before bash: every gate, the walk and the old = new proof, nothing written.)
#   /root/finance/amir_day.py   3b7dae35 -> TO   _door_receipt; _export_state (today only); _step4: the door line, the head, a bad report still rules
#  THE GATE THAT DECIDES: on this box, on a copy of the database, every real day since 1-Sep with a step-3 tap or a purchase export is
#  read under the OLD and the NEW file -- identical, or the one allowed difference (today, the door holding a covering file).
#  Restarts clinic-finance only. Red after placing: the file back, finance restarted.
# =============================================================================
set -u
KIT="S678_AMIR_PAIR_FROM_DOOR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
SINCE="${SINCE:-2026-09-01}"
F="finance/amir_day.py"
FROM="3b7dae35699548b4db9c2dac498cda6a"
TO="$(awk -v f="$F" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s678_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN_BOX="22 of 22 green"; GREEN="21 of 21 green"
CONTROL="6 S678 check(s) red · 0 older red · 15 green"
BAK="$ROOT/$F.bak_S678_${FROM:0:8}"
STG="$ROOT/finance/.amir_day.py.s678"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fhz() { fhealth /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || [ "$PLACED" = 2 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s678.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting amir_day.py back"
  PLACED=2
  \cp -p "$BAK" "$ROOT/$F" || say "   !! could not put back $ROOT/$F"; rm -f "$STG"
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
[ -f "$ROOT/$F" ] && [ -f "$DB" ] || { say "!! [1/8] $ROOT/$F or $DB is missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/$F")" = "$TO" ] && { say "-- ALREADY INSTALLED: amir_day.py is the kit's. Nothing written. finance healthz $(fhz)"; exit 0; }
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
say "[2/8] live pin exact: amir_day.py at its FROM ${FROM:0:8}"

mkdir -p "$SCR/built" "$SCR/pyc" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s678.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$F")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, amir_day.py is $(m5 "$SCR/built/$F" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$F" || stop_unlocked "!! [3/8] amir_day.py does not compile on $py - nothing installed"; done
say "[3/8] rebuilt here from this box's live bytes: at its TO pin ${TO:0:8}; compiles under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1" --old-root "$ROOT" --since "$SINCE")
L1="$(echo "$R" | tail -1)"
echo "$R" | grep -E '^  --  |^      ' | head -30 | sed 's/^/         /'
[ "$L1" = "$GREEN_BOX" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; PLACED=2; stop_unlocked "!! [4/8] the walk, or the old = new proof since $SINCE, is not green ($L1) - nothing installed (kept in $SCR)"; }
R=$(walk --old "$ROOT" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" | tail -1)
[ "$R" = "$CONTROL" ] || { PLACED=2; stop_unlocked "!! [4/8] the control on the live file is not as expected ($R) - nothing installed (kept in $SCR)"; }
f0=$(fhz); [ "$f0" = 200 ] || stop_unlocked "!! [4/8] finance healthz $f0 before the install - nothing installed"
say "[4/8] the walk on a copy of the database: $L1 (old = new since $SINCE above); the control on the live file: $R; finance healthy ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walk and the proof green; NOTHING written"; exit 0; fi

{ \cp -p "$ROOT/$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop_unlocked "!! [5/8] could not write the backup $BAK - nothing placed"
{ cat "$SCR/built/$F" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage amir_day.py - nothing placed"; }
chmod --reference="$ROOT/$F" "$STG" 2>/dev/null; chown --reference="$ROOT/$F" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$F" || restore "the rename"
[ "$(m5 "$ROOT/$F")" = "$TO" ] || restore "read back"
say "[5/8] placed and read back: amir_day.py at ${TO:0:8} (backup $BAK)"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/amir/day); case "$c2" in 302|401|303|403) ;; *) restore "Amir's day page answered $c2 without a login";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[6/8] $FSVC restarted at $T0: healthz $c1; Amir's day page $c2 without a login (the login gate, expected); journal clean"
say "[7/8] no data step"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed file"
R=$(walk --new "$ROOT" --lib "$ROOT" --db "$SCR/walk2.db" --scratch "$SCR/w2" | tail -1)
[ "${REHEARSE_RED_AT:-}" = 8 ] && R="rehearsal: a forced red at [8/8]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
release_lock
say "[8/8] the walk on the placed file: $R; the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$F && $SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. A report the server already holds is never 'nahi aayi' on Amir's screen."
exit 0
