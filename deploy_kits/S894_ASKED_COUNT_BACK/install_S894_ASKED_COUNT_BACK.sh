#!/bin/bash
# =============================================================================
#  install_S894_ASKED_COUNT_BACK.sh · kit S894 (20-Nov-2026, Sanjeevni session 490) · the owner 14:44 IST: "1 - to be done through Amir.
#  He will enter stock vouchers for the same to balance their quantities. 2,3 - ok"
#   /root/finance/stock_watch.py f0d9092a -> TO : a count the owner ASKED for ('Count this') reaches his Needs-you the moment Darpan
#        enters it, beside Marg's closing figure, and the ask closes -- also when answered on a later day's list (a carried row),
#        which never closed it before. Built by make_s894.py from the live bytes (3 anchors + one function).
#   data (s894_job.py): two tap jobs on Amir's card from Darpan's 18-Nov counts -- ZIBON EXTRA STOCK ISSUE 15:3, GEMCAL XT 0:4 --
#        and the three asks Darpan answered on 18-Nov closed.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s894kit && cp -rp /root/deploy/repo/deploy_kits/S894_ASKED_COUNT_BACK /tmp/s894kit && bash /tmp/s894kit/install_S894_ASKED_COUNT_BACK.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S894_ASKED_COUNT_BACK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
N1="finance/stock_watch.py"; F1="f0d9092a051c4cd043645e4510ef4cee"
T1="$(awk -v f="$N1" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s894_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
B1="$ROOT/$N1.bak_S894_${F1:0:8}"; S1="$ROOT/finance/.stock_watch.py.s894"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$S1"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting stock_watch.py back"
  \cp -p "$B1" "$ROOT/$N1"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   $N1 $(m5 "$ROOT/$N1" | cut -c1-8) (expected ${F1:0:8}); $FSVC restarted, finance healthz $(wait200). Nothing was added to Amir's card. Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
lay() { local d="$SCR/root_$1"; rm -rf "$d"; mkdir -p "$d/finance/spine" \
  && find "$ROOT/finance" -maxdepth 1 -type f \( -name '*.py' -o -name '*.json' \) -exec cp -p {} "$d/finance/" \; \
  && \cp -p "$ROOT"/finance/spine/*.py "$d/finance/spine/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.json "$d/finance/spine/" 2>/dev/null; \
  [ -f "$d/finance/stock_watch.py" ]; }
py() { (cd /tmp && TMPDIR="$SCR" SPINE_DB="$SCR/spine.db" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
CPDB='import sqlite3,sys;s=sqlite3.connect("file:%s?mode=ro"%sys.argv[1],uri=True,timeout=60);d=sqlite3.connect(sys.argv[2]);s.backup(d);d.close();s.close();print("copied")'

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$T1" ] && [ "$(m5 "$KDIR/stock_watch.py")" = "$T1" ] || { say "!! [1/5] the kit's stock_watch.py is not at its TO pin - nothing installed"; exit 1; }
[ -f "$DB" ] || { say "!! [1/5] $DB missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$N1")" = "$T1" ]; then
  say "-- stock_watch.py is ALREADY at the new version; the data step only:"
  [ "${DRY:-0}" = 1 ] && { (cd /tmp && "$VPY" -B "$KDIR/s894_job.py" "$DB" --dry); exit 0; }
  R=$(cd /tmp && "$VPY" -B "$KDIR/s894_job.py" "$DB" 2>&1); echo "$R"; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$ROOT/$N1")" = "$F1" ] || stop "!! [2/5] $ROOT/$N1 is $(m5 "$ROOT/$N1" | cut -c1-8), expected ${F1:0:8} - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_watch.py" "$KDIR/s894_job.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] the live file is at its FROM pin (${F1:0:8}); the new one compiles on both pythons"
"$VPY" -c "$CPDB" "$DB" "$SCR/f_new.db" >/dev/null && "$VPY" -c "$CPDB" "$DB" "$SCR/f_old.db" >/dev/null || stop "!! [3/5] could not copy the database for the walk - nothing installed"
[ -f "$SPDB" ] && { "$VPY" -c "$CPDB" "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/5] could not copy the spine for the walk - nothing installed"; }
lay new && \cp -p "$KDIR/stock_watch.py" "$SCR/root_new/$N1" && lay old || stop "!! [3/5] could not lay out the walk - nothing installed"
R1=$(py "$KDIR/synth_s894.py" --code "$SCR/root_new/finance" --finance "$SCR/f_new.db" | tail -1)
case "$R1" in "synth_s894: "*" ok, 0 red") ;; *) stop "!! [3/5] synth_s894 on a copy of the live database: $R1 - nothing installed";; esac
R0=$(py "$KDIR/synth_s894.py" --code "$SCR/root_old/finance" --finance "$SCR/f_old.db" | tail -1)
case "$R0" in "synth_s894: "*" ok, 0 red") stop "!! [3/5] the control on the live file did not go red ($R0) - nothing installed";; esac
JD=$(cd /tmp && "$VPY" -B "$KDIR/s894_job.py" "$SCR/f_new.db" --dry 2>&1)
echo "$JD" | grep -q "S894: REFUSED" && stop "!! [3/5] $(echo "$JD" | grep REFUSED) - nothing installed"
say "[3/5] $R1 (a copy of the live database); the control on the live file: red ($R0)"
say "$(echo "$JD" | sed 's/^/      /')"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$N1" "$B1" && [ "$(m5 "$B1")" = "$F1" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
{ cat "$KDIR/stock_watch.py" > "$S1" && chmod --reference="$ROOT/$N1" "$S1" 2>/dev/null; chown --reference="$ROOT/$N1" "$S1" 2>/dev/null; [ "$(m5 "$S1")" = "$T1" ]; } || stop "!! [4/5] could not stage stock_watch.py - nothing placed"
PLACING=1
mv -f "$S1" "$ROOT/$N1" || restore "the rename of stock_watch.py"
[ "$(m5 "$ROOT/$N1")" = "$T1" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
PLACING=0
JR=$(cd /tmp && "$VPY" -B "$KDIR/s894_job.py" "$DB" 2>&1)
release_lock
say "[4/5] placed and read back (${T1:0:8}); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
say "$(echo "$JR" | sed 's/^/      /')"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s894.sh  (the file back, $FSVC restarted, the two jobs off Amir's card)"
say ""
echo "$JR" | grep -q "S894: added\|S894: ALREADY" && say "$KIT: DONE. Amir's card asks for the two stock issues; an asked count now reaches your Needs-you." \
  || say "$KIT: DONE for the file; the data step said the above -- tell Claude."
exit 0
