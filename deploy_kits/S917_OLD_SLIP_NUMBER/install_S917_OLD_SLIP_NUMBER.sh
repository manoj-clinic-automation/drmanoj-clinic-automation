#!/bin/bash
# =============================================================================
#  install_S917_OLD_SLIP_NUMBER.sh · kit S917 (the parent, S498, 21-Nov-2026) · a 14-Nov X-ray slip whose number was taken
#  1. ONE-OFF (data): slip 1190 -- a 9-Nov replacement slip saved 15-Nov under 1546, the 14-Nov X-ray paper's number --
#     takes 1481, that patient's own voided 9-Nov paper; the discount ask left on the voided 1481 is withdrawn. 1546 is free.
#  2. GUARD: an OLD day's parchi whose number is past a LATER day's saved parchi asks 'Haan, yahi number'   slip_log.py 5cfaf728 -> TO
#  clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s917kit && cp -rp /root/deploy/repo/deploy_kits/S917_OLD_SLIP_NUMBER /tmp/s917kit && bash /tmp/s917kit/install_S917_OLD_SLIP_NUMBER.sh
#  DRY=1 before bash: every gate and walk, nothing changed. --undo: the file back and the two rows back (while 1546 is still free).
# =============================================================================
set -u
KIT="S917_OLD_SLIP_NUMBER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="slip_log.py"; FROM="5cfaf728ffa65cbe7f65522863744238"
TO="$(awk '$2=="finance/slip_log.py"{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s917_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/finance/$N.bak_S917_${FROM:0:8}"
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$ROOT/finance/.$N.s917"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"
  \cp -p "$BAK" "$ROOT/finance/$N"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N $(m5 "$ROOT/finance/$N" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). The data one-off was NOT run. Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && find "$ROOT/finance" -maxdepth 1 -type f -name '*.html' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/slip_log.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$@" 2>&1); }
copydb() { "$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$1"; }

if [ "${1:-}" = "--undo" ]; then
  if [ "$(m5 "$ROOT/finance/$N")" = "$FROM" ]; then case "$("$VPY" "$KDIR/s917_fix.py" "$DB")" in "S917_FIX: WOULD"*) say "-- $KIT is not installed - nothing to undo."; exit 0;; esac; fi
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  if [ "$(m5 "$ROOT/finance/$N")" = "$TO" ]; then
    [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || stop "!! no good backup $BAK - nothing undone"
    \cp -p "$BAK" "$ROOT/finance/$N"; "$SYSTEMCTL" restart "$FSVC"; say "   $N $(m5 "$ROOT/finance/$N" | cut -c1-8) (expected ${FROM:0:8})"
  elif [ "$(m5 "$ROOT/finance/$N")" != "$FROM" ]; then stop "!! $ROOT/finance/$N is $(m5 "$ROOT/finance/$N" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; fi
  say "   $("$VPY" "$KDIR/s917_fix.py" "$DB" --revert)"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/$N")" = "$TO" ] || { say "!! [1/6] the kit's $N is not as built - nothing installed"; exit 1; }
[ -f "$ROOT/finance/$N" ] && [ -f "$DB" ] || { say "!! [1/6] $ROOT/finance/$N or $DB missing - nothing installed"; exit 1; }
FIXNOW="$("$VPY" "$KDIR/s917_fix.py" "$DB")"
if [ "$(m5 "$ROOT/finance/$N")" = "$TO" ] && case "$FIXNOW" in "S917_FIX: ALREADY DONE"*) true;; *) false;; esac; then say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
case "$FIXNOW" in "S917_FIX: WOULD"*|"S917_FIX: ALREADY DONE"*) ;; *) say "!! [1/6] the live rows are not as found: $FIXNOW - nothing installed. Tell Claude."; exit 1;; esac
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; the rows as found; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the rows as found; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
LIVE5="$(m5 "$ROOT/finance/$N")"; [ "$LIVE5" = "$FROM" ] || [ "$LIVE5" = "$TO" ] || stop "!! [2/6] $ROOT/finance/$N is ${LIVE5:0:8}, expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$N" "$KDIR/s917_fix.py" || stop "!! [2/6] the kit's python does not compile on $p - nothing installed"; done
say "[2/6] the live pin exact; the file and the one-off compile on both pythons"
copydb "$SCR/finance.db" || stop "!! [3/6] could not copy the database for the walks - nothing installed"
for x in w917n w917o w840n w840o w844; do \cp -p "$SCR/finance.db" "$SCR/$x.db" || stop "!! [3/6] could not copy the database - nothing installed"; done
{ mkfin old && mkfin new && \cp -p "$KDIR/$N" "$SCR/fin_new/$N" && \cp -p "$KDIR/parchi_desk_s912.py" "$SCR/fin_new/parchi_desk.py" && \cp -p "$KDIR/parchi_desk_s912.py" "$SCR/fin_old/parchi_desk.py"; } || stop "!! [3/6] could not lay out the walks - nothing installed"
[ "$LIVE5" = "$FROM" ] || \cp -p "$BAK" "$SCR/fin_old/$N"
W1=$(py "$KDIR/walk_s917.py" "$SCR/fin_new" "$SCR/w917n.db"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK 13/13") ;; *) echo "$W1" | grep '^FAIL' | cut -c1-160 | head -6 | sed 's/^/      /'; stop "!! [3/6] walk_s917 (a copy of the live data) on the new file: $R1 - nothing installed";; esac
R1c=$(py "$KDIR/walk_s917.py" "$SCR/fin_old" "$SCR/w917o.db" | tail -1)
case "$R1c" in "WALK 13/13") stop "!! [3/6] walk_s917's control (the live file) did not go red - nothing installed";; esac
R2=$(py "$KDIR/walk_s912.py" "$SCR/fin_new" "$SCR/w912" | tail -1)
[ "$R2" = "WALK 29/29" ] || stop "!! [3/6] walk_s912 (S912's rules) on the new file: $R2 - nothing installed"
R3n=$(py "$KDIR/walk_s840.py" "$SCR/fin_new" "$SCR/w840n.db" | tail -1); R3o=$(py "$KDIR/walk_s840.py" "$SCR/fin_old" "$SCR/w840o.db" | tail -1)
[ "$R3n" = "$R3o" ] || stop "!! [3/6] walk_s840 (the desk) differs: new '$R3n', live '$R3o' - nothing installed"
mkdir -p "$SCR/k844" && \cp -p "$KDIR/parchi_desk_s912.py" "$SCR/k844/parchi_desk.py" || stop "!! [3/6] could not lay out walk_s844 - nothing installed"
R4=$(py "$KDIR/walk_s844.py" "$SCR/k844" "$SCR/fin_new" "$SCR/w844.db" | tail -1)
case "$R4" in "WALK OK 31/31") ;; *) stop "!! [3/6] walk_s844 on the new file: $R4 - nothing installed";; esac
say "[3/6] walk_s917 $R1 (on a copy; control red: ${R1c:-crashed}); walk_s912 $R2; walk_s840 '$R3n' (live the same); walk_s844 $R4"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
if [ "$LIVE5" = "$FROM" ]; then
  { \cp -p "$ROOT/finance/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/6] could not write the backup of $N - nothing placed"
  st="$ROOT/finance/.$N.s917"; { cat "$KDIR/$N" > "$st" && chmod --reference="$ROOT/finance/$N" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$N" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$TO" ]; } || stop "!! [4/6] could not stage $N - nothing placed"
  mv -f "$st" "$ROOT/finance/$N" || restore "the rename of $N"
  [ "$(m5 "$ROOT/finance/$N")" = "$TO" ] || restore "read back of $N"
  "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
  [ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
  c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
  ap=$(fget /finance/slips); case "$ap" in 200|302|303|401|403) ;; *) restore "the slips page answered $ap";; esac
  say "[4/6] placed and read back: $N at its TO pin; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the slips page $ap"
else say "[4/6] $N already at its TO pin"; fi
DBB="$ROOT/finance/finance.db.bak_S917_$STAMP"
copydb "$DBB" || stop "!! [5/6] could not back up the database before the one-off - the file is placed, the rows NOT changed. Tell Claude."
FX="$("$VPY" "$KDIR/s917_fix.py" "$DB" --apply)"
case "$FX" in "S917_FIX: APPLIED"*|"S917_FIX: ALREADY DONE"*) ;; *) stop "!! [5/6] the one-off: $FX - the file is placed, the rows unchanged. Tell Claude.";; esac
release_lock
say "[5/6] $FX (database backed up first: $DBB)"
say "[6/6] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
