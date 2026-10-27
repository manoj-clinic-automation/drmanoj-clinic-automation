#!/bin/bash
# =============================================================================
#  install_S665_EXPIRY_DAYTIME.sh · kit S665 (27-Oct-2026, Sanjeevni session 359) · the owner 11:58 IST: the expiry watch lists VOM L
#  after Shavez's morning export -- its last strips sold on 26-Oct, but the watch was made only at 23:57.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s665kit && cp -rp /root/deploy/repo/deploy_kits/S665_EXPIRY_DAYTIME /tmp/s665kit && bash /tmp/s665kit/install_S665_EXPIRY_DAYTIME.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#   /root/finance/spine/near_expiry.py  c12284f3 -> TO   --if-newer: make the watch when the spine holds a newer sale day than the last run
#   the crontab                          + ONE line      every ten minutes 09:05-23:55 IST, under the spine's own lock (S665_EXPIRY_DAYTIME)
#  The 23:57 line is unchanged. No service restart (no service imports near_expiry.py). After placing, the line is run ONCE now, so the
#  list catches up at once; then the walk again on the placed file.
#  Red after placing: the file and the crontab back from their backups.
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S665_EXPIRY_DAYTIME"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
SLOCK="${SLOCK:-/tmp/spine.lock}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
CRONTAB="${CRONTAB:-crontab}"
REL="finance/spine/near_expiry.py"
FROM=c12284f33770318088c7584b4de9ca0c
TO="$(awk '{print $1}' "$KDIR/TO_PINS.md5")"
MARK="S665_EXPIRY_DAYTIME"
LINE="5-59/10 9-23 * * * cd $ROOT/finance/spine && flock -n $SLOCK $VPY -B near_expiry.py --if-newer >> $ROOT/finance/spine/near_expiry.log 2>&1 # $MARK"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s665_inst_$STAMP"
PLACED=0; TOOK_LOCK=0
GREEN="8 of 8 green"
CONTROL="6 S665 check(s) red · 0 older red · 2 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/$REL.bak_S665_${FROM:0:8}"
BAKC="$ROOT/deploy/crontab.bak_S665_$STAMP"
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
q() { "$APY" -c "import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); print(c.execute(sys.argv[2]).fetchone()[0])" "$1" "$2"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -B "$KDIR/walk_s665.py" "$@" 2>&1); }
ncron() { "$CRONTAB" -l 2>/dev/null | grep -c -F "$1" || true; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the file and the crontab back"
  \cp -p "$BAK" "$ROOT/$REL" || say "   !! could not put back $ROOT/$REL"
  rm -f "$ROOT"/finance/spine/.near_expiry.py.s665
  [ -f "$BAKC" ] && "$CRONTAB" "$BAKC" || say "   !! could not put back the crontab from $BAKC"
  say "   $ROOT/$REL $(m5 "$ROOT/$REL") (expected $FROM); crontab S665 lines: $(ncron "$MARK") (expected 0). Send a photo of this screen to Claude."
  release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date grep find sed timeout flock "$CRONTAB"; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:30 IST (the 23:57 run must not meet the install) - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -f "$ROOT/$REL" ] && [ -f "$DB" ] && [ -f "$SPINE" ] || { say "!! [1/8] $ROOT/$REL, $DB or $SPINE is missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$REL")" = "$TO" ] && [ "$(ncron "$MARK")" = 1 ]; then say "-- ALREADY INSTALLED: near_expiry.py is the kit's and the crontab carries its line once. Nothing written."; exit 0; fi
[ "$(ncron "near_expiry.py >> ")" = 1 ] && [ "$(ncron S343_NEAR_EXPIRY)" = 1 ] && [ "$(ncron "$MARK")" = 0 ] \
  || { say "!! [1/8] the crontab is not as this kit read it (the 23:57 S343_NEAR_EXPIRY line once, no $MARK line) - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window, the crontab as read); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi
C="$(m5 "$ROOT/$REL")"; [ "$C" = "$FROM" ] || stop_unlocked "!! [2/8] $ROOT/$REL is ${C:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed"
say "[2/8] live pin exact: near_expiry.py at its FROM; the crontab as read ($("$CRONTAB" -l | wc -l | awk '{print $1}') lines)"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s665.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused the live file - nothing installed"; }
[ "$(m5 "$SCR/built/$REL")" = "$TO" ] || stop_unlocked "!! [3/8] rebuilt, near_expiry.py is $(m5 "$SCR/built/$REL" | cut -c1-8), not ${TO:0:8} - nothing installed"
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$REL" || stop_unlocked "!! [3/8] the built file does not compile on $py - nothing installed"; done
say "[3/8] rebuilt here from this box's live bytes: at its TO pin; compiles under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --spine "$SPINE" --scratch "$SCR/w1")
L1="$(echo "$R" | tail -1)"; [ "$L1" = "$GREEN" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/8] the walk is not green ($L1) - nothing installed"; }
R=$(walk --old "$ROOT" --db "$SCR/walk.db" --spine "$SPINE" --scratch "$SCR/w0" | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live file is not as expected ($R) - nothing installed"
say "[4/8] the walk on copies of the database and the spine: $L1; the control on the live file: $R"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi

\cp -p "$ROOT/$REL" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || stop_unlocked "!! [5/8] could not write the backup of $ROOT/$REL - nothing placed"
mkdir -p "$(dirname "$BAKC")" && "$CRONTAB" -l > "$BAKC" 2>/dev/null && [ -s "$BAKC" ] || stop_unlocked "!! [5/8] could not back the crontab up to $BAKC - nothing placed"
N0="$(wc -l < "$BAKC")"
STG="$ROOT/finance/spine/.near_expiry.py.s665"
{ cat "$SCR/built/$REL" > "$STG" && [ "$(m5 "$STG")" = "$TO" ]; } || { rm -f "$STG"; stop_unlocked "!! [5/8] could not stage the file - nothing placed"; }
chmod --reference="$ROOT/$REL" "$STG" 2>/dev/null; chown --reference="$ROOT/$REL" "$STG" 2>/dev/null
PLACED=1
mv -f "$STG" "$ROOT/$REL" || restore "the rename"; [ "$(m5 "$ROOT/$REL")" = "$TO" ] || restore "the md5 read back"
say "[5/8] placed and read back: near_expiry.py at its TO pin (backup $BAK); the crontab saved to $BAKC ($N0 lines)"

{ cat "$BAKC"; echo "$LINE"; } > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" || restore "the crontab could not be written"
"$CRONTAB" -l > "$SCR/cron.now" 2>/dev/null
[ "$(wc -l < "$SCR/cron.now")" = "$((N0 + 1))" ] && [ "$(ncron "$MARK")" = 1 ] && [ "$(head -n "$N0" "$SCR/cron.now" | md5sum)" = "$(md5sum < "$BAKC")" ] \
  || restore "the crontab read back is not the old one plus the one line"
say "[6/8] the crontab: $N0 lines + the one line $MARK, read back; every other line exactly as it was"

say "       the line run ONCE now, as the crontab runs it (waits up to two minutes for the spine's own lock):"
OUT=$(cd "$ROOT/finance/spine" && timeout 600 flock -w 120 "$SLOCK" "$VPY" -B near_expiry.py --if-newer 2>&1 | tail -3)
echo "$OUT" | sed 's/^/         | /'
S=$(q "$SPINE" "SELECT MAX(date) FROM sp_sale_line"); T=$(q "$DB" "SELECT sales_to FROM stock_expiry_run WHERE ok=1 ORDER BY id DESC LIMIT 1")
[ -n "$S" ] && [ "$S" = "$T" ] || restore "after the run, the newest good run reaches $T, the spine $S"
say "[7/8] the watch is current: its newest run reaches $T, the spine's newest sale day"
copydb "$DB" "$SCR/walk2.db" || restore "no copy of the database for the walk on the placed file"
R=$(walk --new "$ROOT" --db "$SCR/walk2.db" --spine "$SPINE" --scratch "$SCR/w2" | tail -1)
[ "$R" = "$GREEN" ] || restore "the walk on the placed file: $R"
release_lock
say "[8/8] the walk on the placed file: $R; the build lock released"
say "undo (one line): \\cp -p $BAK $ROOT/$REL && $CRONTAB $BAKC"
say ""
say "$KIT: DONE. The expiry watch now catches up within ten minutes of the morning's sales reaching the server; the 23:57 run stays."
exit 0
