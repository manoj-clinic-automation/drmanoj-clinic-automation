#!/bin/bash
# =============================================================================
#  install_S918_FREE_XRAY_TAP.sh · kit S918 (the parent, S498, 21-Nov-2026) · a free X-ray closed in one tap
#  A parked X-ray photo of someone registered nowhere (three of September) closes with ONE tap,
#  'Free X-ray', on Shavez's Check karein card and on the owner's waiting card -- marked not in Docterz AND explained
#  'free X-ray' at once, so it leaves every list (his 'Not in Docterz' keeps it as explained).   check_screens.py 5d00b2e8 -> TO
#  clinic-finance restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s918kit && cp -rp /root/deploy/repo/deploy_kits/S918_FREE_XRAY_TAP /tmp/s918kit && bash /tmp/s918kit/install_S918_FREE_XRAY_TAP.sh
#  DRY=1 before bash: every gate and walk, nothing changed. --undo: the file back.
# =============================================================================
set -u
KIT="S918_FREE_XRAY_TAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N="check_screens.py"; FROM="5d00b2e80f25875a431b97b0a0331515"
TO="$(awk '$2=="finance/check_screens.py"{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s918_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$ROOT/finance/$N.bak_S918_${FROM:0:8}"
fget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
fhz() { fget /finance/healthz; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$ROOT/finance/.$N.s918"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { say "!! RED after placing ($1) - putting the file back"
  \cp -p "$BAK" "$ROOT/finance/$N"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N $(m5 "$ROOT/finance/$N" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1" && find "$ROOT/finance" -maxdepth 1 -type f -name '*.py' -exec cp -p {} "$SCR/fin_$1/" \; && find "$ROOT/finance" -maxdepth 1 -type f -name '*.html' -exec cp -p {} "$SCR/fin_$1/" \; && [ -f "$SCR/fin_$1/$N" ]; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$@" 2>&1); }
copydb() { "$VPY" -c "import sqlite3,sys;s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=30);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close()" "$DB" "$1"; }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$ROOT/finance/$N")" = "$FROM" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! no good backup $BAK - nothing undone"; exit 1; }
  [ "$(m5 "$ROOT/finance/$N")" = "$TO" ] || { say "!! $ROOT/finance/$N is $(m5 "$ROOT/finance/$N" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  \cp -p "$BAK" "$ROOT/finance/$N"; "$SYSTEMCTL" restart "$FSVC"; say "   $N $(m5 "$ROOT/finance/$N" | cut -c1-8) (expected ${FROM:0:8})"
  h=$(wait200); release_lock
  [ "$h" = 200 ] || { say "!! UNDONE but finance healthz is $h - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz 200). The answers already given stay (a closed free X-ray stays closed)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 "$KDIR/$N")" = "$TO" ] || { say "!! [1/5] the kit's $N is not as built - nothing installed"; exit 1; }
[ -f "$ROOT/finance/$N" ] && [ -f "$DB" ] || { say "!! [1/5] $ROOT/finance/$N or $DB missing - nothing installed"; exit 1; }
[ "$(m5 "$ROOT/finance/$N")" = "$TO" ] && { say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/finance/$N")" = "$FROM" ] || stop "!! [2/5] $ROOT/finance/$N is $(m5 "$ROOT/finance/$N" | cut -c1-8), expected ${FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/$N" || stop "!! [2/5] $N does not compile on $p - nothing installed"; done
say "[2/5] the live pin exact; the file compiles on both pythons"
copydb "$SCR/finance.db" || stop "!! [3/5] could not copy the database for the walks - nothing installed"
for x in a b c d e; do \cp -p "$SCR/finance.db" "$SCR/$x.db" || stop "!! [3/5] could not copy the database - nothing installed"; done
{ mkfin old && mkfin new && \cp -p "$KDIR/$N" "$SCR/fin_new/$N"; } || stop "!! [3/5] could not lay out the walks - nothing installed"
W1=$(py "$KDIR/walk_s918.py" "$SCR/fin_new" "$SCR/a.db"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK 14/14") ;; *) echo "$W1" | grep '^FAIL' | cut -c1-160 | head -6 | sed 's/^/      /'; stop "!! [3/5] walk_s918 (a copy of the live data) on the new file: $R1 - nothing installed";; esac
R1c=$(py "$KDIR/walk_s918.py" "$SCR/fin_old" "$SCR/b.db" | tail -1)
case "$R1c" in "WALK 14/14") stop "!! [3/5] walk_s918's control (the live file) did not go red - nothing installed";; esac
R2=$(py "$KDIR/walk_s854.py" "$SCR/fin_new" "$SCR/fin_new" "$SCR/c.db" | tail -1)
[ "$R2" = "WALK OK 31/31" ] || stop "!! [3/5] walk_s854 on the new file: $R2 - nothing installed"
W3n=$(py "$KDIR/walk_s836.py" "$SCR/fin_new" "$SCR/d.db" | grep -E '^BAD|^WALK' | sed -E 's/^(BAD [A-Z0-9]+).*/\1/' | tr '\n' ' ' | sed 's/ *$//')
W3o=$(py "$KDIR/walk_s836.py" "$SCR/fin_old" "$SCR/e.db" | grep -E '^BAD|^WALK' | sed -E 's/^(BAD [A-Z0-9]+).*/\1/' | tr '\n' ' ' | sed 's/ *$//')
[ -n "$W3n" ] && [ "$W3n" = "$W3o" ] || stop "!! [3/5] walk_s836 differs: new '$W3n', live '$W3o' - nothing installed"
say "[3/5] walk_s918 $R1 (on a copy; control red: ${R1c:-crashed}); walk_s854 $R2; walk_s836 the same on both ('$W3n')"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; nothing live changed"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/finance/$N" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup of $N - nothing placed"
st="$ROOT/finance/.$N.s918"; { cat "$KDIR/$N" > "$st" && chmod --reference="$ROOT/finance/$N" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$N" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$TO" ]; } || stop "!! [4/5] could not stage $N - nothing placed"
mv -f "$st" "$ROOT/finance/$N" || restore "the rename of $N"
[ "$(m5 "$ROOT/finance/$N")" = "$TO" ] || restore "read back of $N"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
ck=$(fget /finance/checks); case "$ck" in 200|302|303|401|403) ;; *) restore "Check karein answered $ck";; esac
release_lock
say "[4/5] placed and read back: $N at its TO pin; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Check karein $ck"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
