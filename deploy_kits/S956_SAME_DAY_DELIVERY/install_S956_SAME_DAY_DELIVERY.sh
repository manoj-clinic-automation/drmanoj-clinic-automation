#!/bin/bash
# =============================================================================
#  install_S956_SAME_DAY_DELIVERY.sh · kit S956 (25-Nov-2026, Sanjeevni session 519) · after S952 + S954
#   /root/finance/stock_figure.py (S952's 500a7d46) -> v1.7 : a count before the evening hour stands for the START of its day -- the day's
#        purchases are added to the shelf figure after it, unless a delivery line shows the bill arrived before the count (JAKMAC 5: -20:0 -> 0).
#   then the stock of record rebuilt at once (the page reads it).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s956kit && cp -rp /root/deploy/repo/deploy_kits/S956_SAME_DAY_DELIVERY /tmp/s956kit && bash /tmp/s956kit/install_S956_SAME_DAY_DELIVERY.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S956_SAME_DAY_DELIVERY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
F="$ROOT/finance/stock_figure.py"; FROM8="500a7d46"
TO="$(awk '$2=="finance/stock_figure.py"{print $1}' "$KDIR/TO_PINS.md5")"
READS=("finance/record_judges.py 5c5cca26" "finance/stock_record.py 14caf248" "finance/stock_watch.py 401684ea")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s956_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
BAK="$F.bak_S956_$FROM8"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$(dirname "$F")/.stock_figure.py.s956"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$F"; "$SYSTEMCTL" restart "$FSVC" || true
  say "   the stock of record rebuilt by the old code: $(fin "$ROOT/finance/stock_record.py" --build --force | tail -1 | cut -c1-80)"
  say "   finance/stock_figure.py $(m5 "$F" | cut -c1-8) (expected $FROM8); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO" ] && [ "$(m5 "$KDIR/stock_figure.py")" = "$TO" ] || { say "!! [1/5] the kit's stock_figure.py is not at its TO pin - nothing installed"; exit 1; }
if [ "$(m5 "$F")" = "$TO" ]; then say "$KIT: ALREADY INSTALLED - the file is at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$F" | cut -c1-8)" = "$FROM8" ] || stop "!! [2/5] $F is $(m5 "$F" | cut -c1-8), expected $FROM8 (S952) - STOP, nothing installed. Tell Claude."
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/5] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_figure.py" "$KDIR/walk_s956.py" "$KDIR/make_s956.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] stock_figure.py at S952's $FROM8; record_judges (S954), stock_record and stock_watch at their pins; the kit compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
mkdir -p "$SCR/new/spine" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"; \cp -p "$KDIR/stock_figure.py" "$SCR/new/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/5] could not take a copy of the database for the walk - nothing installed"
\cp -p "$SCR/copy.db" "$SCR/copy0.db"
W1=$(py "$KDIR/walk_s956.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk on a copy: $R1 - nothing installed"; }
W2=$(py "$KDIR/walk_s956.py" "$SCR/new" "$SCR/copy.db"); R2=$(echo "$W2" | tail -1)
[ "$R2" = "RESULT: ALL PASS" ] || { echo "$W2" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk a second time: $R2 - nothing installed"; }
W0=$(py "$KDIR/walk_s956.py" "$SCR/old" "$SCR/copy0.db" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/5] the control did not go red ($R0) - nothing installed";; esac
rm -f "$SCR/copy.db" "$SCR/copy0.db"
say "[3/5] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass, twice; the control goes red as it must ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$F" "$BAK" && [ "$(m5 "$BAK" | cut -c1-8)" = "$FROM8" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
S="$(dirname "$F")/.stock_figure.py.s956"; { cat "$KDIR/stock_figure.py" > "$S" && chmod --reference="$F" "$S" 2>/dev/null; chown --reference="$F" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$TO" ]; } || stop "!! [4/5] could not stage the file - nothing placed"
PLACING=1
mv -f "$S" "$F" || restore "the rename"; [ "$(m5 "$F")" = "$TO" ] || restore "the read back"
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/stockcheck/); case "$d1" in 404|000|5*) restore "his Stock check page answers $d1";; esac
d2=$(door /finance/stockcheck/api/rows); case "$d2" in 404|000|5*) restore "the Stock check rows answer $d2";; esac
d3=$(door /finance/porders); case "$d3" in 404|000|5*) restore "reception's page answers $d3";; esac
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "import stock_figure,stock_watch,record_judges; print('S956 module ok', stock_figure.VERSION)" 2>&1 | tail -1)
case "$TK" in "S956 module ok 1.7") ;; *) restore "the module does not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "stock_figure\.py|stock_watch\.py|record_judges\.py|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
RB=$(fin "$ROOT/finance/stock_record.py" --build --force | tail -1)
case "$RB" in *'"ok": true'*) ;; *) restore "the record did not rebuild ($(echo "$RB" | cut -c1-100))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/5]"
PLACING=0
say "[4/5] stock_figure.py placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Stock check $d1 / rows $d2, reception's page $d3, the module loads, the log clean"
say "[5/5] the stock of record rebuilt by the new code: $(echo "$RB" | grep -o '"n": [0-9]*') rows"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s956.sh"
say ""
say "$KIT: DONE."
exit 0
