#!/bin/bash
# =============================================================================
#  install_S952_RECORD_JUDGES.sh · kit S952 (25-Nov-2026, Sanjeevni session 519) · D1065 -- kit 2 of the stock of record, after S950
#   /root/finance/stock_figure.py  (07bca1df) -> v1.6 : rule 0 in carried() -- an order whose scan is linked to a Marg bill is answered by THAT bill
#   /root/finance/porders.py       (eeaad337) -> detect_supplies: rule 0 accepted, a missing line never takes a bill, the scan repair first
#   /root/finance/stock_watch.py   (c7584585) -> v1.12 : every count judged against the one record (write_point, settle, Count now, the trace)
#   /root/finance/stock_check.py   (14ca39be) -> v1.4 : the counts list shows each judgment's words
#   /root/finance/record_judges.py (NEW)       : the judgment, the scan repair, judge-again, the daily self-check
#   + ONE-OFF on the live database (a backup first): pairs righted by the scanned bills, the record rebuilt, every count since 18-11 judged again
#   + one cron line: 06:40 IST the daily self-check (READ ONLY; one line on his Needs-you when it names anything)  # S952_RECORD_CHECK
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s952kit && cp -rp /root/deploy/repo/deploy_kits/S952_RECORD_JUDGES /tmp/s952kit && bash /tmp/s952kit/install_S952_RECORD_JUDGES.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S952_RECORD_JUDGES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
CRONTAB="${CRONTAB:-crontab}"
CRON_LINE="40 6 * * * [ -e /root/finance/_off/ALL_OFF ] || (cd /root/finance && FINANCE_DB=/root/finance/finance.db SHARED_LIB_DIR=/root/shared flock -n /tmp/record_judges.lock /root/wa/venv/bin/python3 -B /root/finance/record_judges.py --check --notice >> /root/finance/record_judges.log 2>&1) # S952_RECORD_CHECK"
NAMES=("finance/stock_figure.py" "finance/porders.py" "finance/stock_watch.py" "finance/stock_check.py" "finance/record_judges.py")
FROMS=("07bca1df78b6f9d3725eda94351158d8" "eeaad33783725305a3712de88650260d" "c7584585faf0fc786e4f09ce606989c5" "14ca39be464b14a5797f41103b8a448b" "absent")
KF=("stock_figure.py" "porders.py" "stock_watch.py" "stock_check.py" "record_judges.py")
IDX="0 1 2 3 4"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s952_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; DATA=0
DBBAK="$ROOT/finance/finance.db.bak_S952_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S952_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s952"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in $IDX; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  if [ "$(cur 4)" = "${TOS[4]}" ]; then say "   the data first (the switches off, then every repair and judgment back): $(fin "$ROOT/finance/record_judges.py" --undo | tail -1)"; fi
  "$CRONTAB" -l 2>/dev/null | grep -v '# S952_RECORD_CHECK' | "$CRONTAB" - 2>/dev/null
  for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then rm -f "$ROOT/${NAMES[$k]}"; elif [ -f "$(bak $k)" ]; then \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; fi; done
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   the stock of record rebuilt by the old code: $(fin "$ROOT/finance/stock_record.py" --build --force | tail -1 | cut -c1-90)"
  for k in $IDX; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200).$([ -f "$DBBAK" ] && echo " The database backup stays at $DBBAK.") Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/6] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - every file is at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
[ "$(m5 "$ROOT/finance/stock_record.py")" = "14caf2480dad320a966f50a97be9d209" ] || stop "!! [2/6] $ROOT/finance/stock_record.py (read by record_judges, not changed) is not at 14caf248 - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_figure.py" "$KDIR/porders.py" "$KDIR/stock_watch.py" "$KDIR/stock_check.py" \
  "$KDIR/record_judges.py" "$KDIR/walk_s952.py" "$KDIR/make_s952.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins (record_judges.py absent); the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
mkdir -p "$SCR/new/spine" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
for k in $IDX; do [ "${FROMS[$k]}" = absent ] && rm -f "$SCR/old/${KF[$k]}"; \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database for the walk - nothing installed"
\cp -p "$SCR/copy.db" "$SCR/copy0.db"
W1=$(py "$KDIR/walk_s952.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk on a copy: $R1 - nothing installed"; }
W2=$(py "$KDIR/walk_s952.py" "$SCR/new" "$SCR/copy.db"); R2=$(echo "$W2" | tail -1)
[ "$R2" = "RESULT: ALL PASS" ] || { echo "$W2" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk a second time on the same copy: $R2 - nothing installed"; }
W0=$(py "$KDIR/walk_s952.py" "$SCR/old" "$SCR/copy0.db" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
rm -f "$SCR/copy.db" "$SCR/copy0.db"
say "[3/6] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass, twice on one copy; the control goes red as it must ($R0) (the copies removed)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do [ "${FROMS[$k]}" = absent ] && continue; { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
py -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1], timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$DBBAK" >/dev/null && [ -s "$DBBAK" ] \
  || stop "!! [4/6] could not back up the database - nothing placed"
for k in $IDX; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && R="$ROOT/${NAMES[$k]}"; [ -f "$R" ] || R="$ROOT/finance/stock_record.py"; chmod --reference="$R" "$s" 2>/dev/null; chown --reference="$R" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/stockcheck/); case "$d1" in 404|000|5*) restore "his Stock check page answers $d1";; esac
d2=$(door /finance/stockcheck/api/rows); case "$d2" in 404|000|5*) restore "the Stock check rows answer $d2";; esac
d3=$(door /finance/porders); case "$d3" in 404|000|5*) restore "reception's page answers $d3";; esac
d4=$(door /finance/porders/flow); case "$d4" in 404|000|5*) restore "his flow page answers $d4";; esac
d5=$(door /finance/darpan/kal/api/order); case "$d5" in 404|000|5*) restore "Darpan's order tab answers $d5";; esac
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "import stock_figure,stock_watch,record_judges,porders,stock_check; print('S952 modules ok', record_judges.VERSION, stock_watch.VERSION, stock_figure.VERSION, stock_check.VERSION)" 2>&1 | tail -1)
case "$TK" in "S952 modules ok 1.0 1.12 1.6 1.4") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "NOT mounted|stock_figure\.py|stock_watch\.py|stock_check\.py|porders\.py|record_judges\.py|S952 |Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
say "[4/6] the five files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Stock check $d1 / rows $d2, reception's page $d3, his flow page $d4, Darpan's order tab $d5 (login-gated), the service log clean since the restart"
DATA=1
ONE=$(fin "$ROOT/finance/record_judges.py" --install | tail -1)
case "$ONE" in "S952 install: "*) ;; *) restore "the one-off did not finish ($(echo "$ONE" | cut -c1-120))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
"$CRONTAB" -l 2>/dev/null | grep -v '# S952_RECORD_CHECK' > "$SCR/cron.new"; echo "$CRON_LINE" >> "$SCR/cron.new"; "$CRONTAB" "$SCR/cron.new" || restore "the cron line could not be written"
"$CRONTAB" -l 2>/dev/null | grep -q '# S952_RECORD_CHECK' || restore "the cron line is not in the crontab"
CK=$(fin "$ROOT/finance/record_judges.py" --check | tail -1)
case "$CK" in *"--check: "*) ;; *) restore "the self-check does not run ($(echo "$CK" | cut -c1-120))";; esac
PLACING=0
say "[5/6] the database backed up before placing ($DBBAK); $ONE"
say "[5/6] the daily self-check 06:40 IST in the crontab (# S952_RECORD_CHECK); run once now: $(echo "$CK" | sed 's/.*--check: //')"
release_lock
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s952.sh  (the judgments and the order lines back, the five files back, the cron line off)"
say ""
say "$KIT: DONE."
exit 0
