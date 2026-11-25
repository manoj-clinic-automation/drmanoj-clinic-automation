#!/bin/bash
# =============================================================================
#  install_S954_FULL_COUNT_PENDING.sh · kit S954 (25-Nov-2026, Sanjeevni session 519) · after S952 (installed 17:08)
#   /root/finance/record_judges.py (S952's 06d317a5) -> v1.1 : the 06-Sep full count's shortfalls read as they were CLOSED -- FOUND / reconciled
#        / billing / reconciled are no loss; one Amir wrote off counts as done when Marg's own stock dropped by it (around the day he keyed
#        it, or net since the count). Only what Marg never took stays as "Marg still holds the older loss" (3 items on 25-Nov: KT ROS DT,
#        VINBACTUM DS, NORTIMER TAB). Then every count since 18-11 judged again by it.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s954kit && cp -rp /root/deploy/repo/deploy_kits/S954_FULL_COUNT_PENDING /tmp/s954kit && bash /tmp/s954kit/install_S954_FULL_COUNT_PENDING.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S954_FULL_COUNT_PENDING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
F="$ROOT/finance/record_judges.py"; FROM="06d317a5e4b6b0c0d58ece78b3940846"
TO="$(awk '$2=="finance/record_judges.py"{print $1}' "$KDIR/TO_PINS.md5")"
READS=("finance/stock_figure.py 500a7d46" "finance/porders.py daf6f92b" "finance/stock_watch.py 401684ea" "finance/stock_check.py 686845f8" "finance/stock_record.py 14caf248")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s954_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; DATA=""
BAK="$F.bak_S954_${FROM:0:8}"; ATF="$ROOT/finance/.s954_rejudged_at"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$(dirname "$F")/.record_judges.py.s954"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  if [ -n "$DATA" ]; then say "   the judgments first: $(fin "$F" --undo-rejudge-from "$DATA" | tail -1)"; fi
  [ -f "$BAK" ] && \cp -p "$BAK" "$F"; rm -f "$ATF"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   finance/record_judges.py $(m5 "$F" | cut -c1-8) (expected ${FROM:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ "$(m5 "$KDIR/record_judges.py")" = "$TO" ] || { say "!! [1/5] the kit's record_judges.py is not at its TO pin - nothing installed"; exit 1; }
if [ "$(m5 "$F")" = "$TO" ]; then say "$KIT: ALREADY INSTALLED - the file is at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$F")" = "$FROM" ] || stop "!! [2/5] $F is $(m5 "$F" | cut -c1-8), expected ${FROM:0:8} (S952) - STOP, nothing installed. Tell Claude."
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/5] $ROOT/$n is not at $p (S952 as installed) - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/record_judges.py" "$KDIR/walk_s954.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] record_judges.py at S952's ${FROM:0:8}; S952's four files and stock_record.py at their pins; the kit compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
mkdir -p "$SCR/new/spine" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"; \cp -p "$KDIR/record_judges.py" "$SCR/new/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/5] could not take a copy of the database for the walk - nothing installed"
\cp -p "$SCR/copy.db" "$SCR/copy0.db"
W1=$(py "$KDIR/walk_s954.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk on a copy: $R1 - nothing installed"; }
W2=$(py "$KDIR/walk_s954.py" "$SCR/new" "$SCR/copy.db"); R2=$(echo "$W2" | tail -1)
[ "$R2" = "RESULT: ALL PASS" ] || { echo "$W2" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk a second time on the same copy: $R2 - nothing installed"; }
W0=$(py "$KDIR/walk_s954.py" "$SCR/old" "$SCR/copy0.db" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/5] the control did not go red ($R0) - nothing installed";; esac
rm -f "$SCR/copy.db" "$SCR/copy0.db"
say "[3/5] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass, twice on one copy; the control goes red as it must ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$F" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
S="$(dirname "$F")/.record_judges.py.s954"; { cat "$KDIR/record_judges.py" > "$S" && chmod --reference="$F" "$S" 2>/dev/null; chown --reference="$F" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$TO" ]; } || stop "!! [4/5] could not stage the file - nothing placed"
PLACING=1
mv -f "$S" "$F" || restore "the rename"; [ "$(m5 "$F")" = "$TO" ] || restore "the read back"
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/stockcheck/); case "$d1" in 404|000|5*) restore "his Stock check page answers $d1";; esac
d2=$(door /finance/stockcheck/api/rows); case "$d2" in 404|000|5*) restore "the Stock check rows answer $d2";; esac
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "import stock_watch,record_judges; print('S954 module ok', record_judges.VERSION, record_judges.KIT)" 2>&1 | tail -1)
case "$TK" in "S954 module ok 1.1 S954_FULL_COUNT_PENDING") ;; *) restore "the module does not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "record_judges\.py|stock_watch\.py|S952 |Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
DATA="$(TZ=Asia/Kolkata date -d '-2 seconds' '+%Y-%m-%dT%H:%M:%S')"; echo "$DATA" > "$ATF"   # the moment BEFORE the judge-again: its undo reaches every row it writes
ONE=$(fin "$F" --rejudge | tail -1)
case "$ONE" in "S954 rejudge at "*) ;; *) restore "the judge-again did not finish ($(echo "$ONE" | cut -c1-120))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/5]"
PLACING=0
say "[4/5] record_judges.py placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Stock check $d1 / rows $d2, the module loads, the log clean"
say "[5/5] $ONE"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s954.sh"
say ""
say "$KIT: DONE."
exit 0
