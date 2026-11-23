#!/bin/bash
# =============================================================================
#  install_S940_ORDER_MESSAGES.sh · kit S940 (23-Nov-2026, Sanjeevni session 509) · D1053 -- AFTER kit S939 (its TO is this kit's FROM)
#   THE PURCHASE ORDER FLOW, PART 2 -- the messages and his four steps:
#   /root/finance/order_d1053_msg.py     NEW : A sheet in (Darpan, staff) · B final (staff, doctor) · C sent (doctor, Darpan) · D each
#        delivery (Darpan), made and sent by order_rules' ten-minute tick; his page's four steps.
#   /root/finance/porders_s454.py  (S939's TO) -> TO : the S940 block appended (his page's steps; the old sheet notice gives way).
#   /root/finance/order_rules.py   0964c6b2 -> TO : the S940 block before its __main__ line (the tick makes and sends the messages).
#   AFTER the install: s940_on.py -- the messages start now (nothing earlier is announced).
#    (one line with S939:) see S939's header
# =============================================================================
set -u
KIT="S940_ORDER_MESSAGES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
NAMES=("finance/porders_s454.py" "finance/order_rules.py" "finance/order_d1053_msg.py")
FROMS=("0adab6a280d97c70f7b14fa5e6fec0eb" "0964c6b2d8b2c46b243a8501ba3a5350" "absent")
KF=("porders_s454.py" "order_rules.py" "order_d1053_msg.py")
N=3; IDX="0 1 2"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s940_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S940_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s940"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
# the service's own log since the restart: a module that failed to mount (porders' fail-soft prints) or a traceback (every door is
# login-gated, so a page cannot prove the new module loaded -- S921's first install went red on exactly that, nothing harmed)
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in $IDX; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then rm -f "$ROOT/${NAMES[$k]}"; elif [ -f "$(bak $k)" ]; then \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; fi; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for k in $IDX; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$@" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/5] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the file is at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/5] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/porders_s454.py" "$KDIR/order_rules.py" "$KDIR/order_d1053_msg.py" "$KDIR/walk_s940.py" "$KDIR/s940_on.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] the live file at its FROM pin; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
for k in $IDX; do [ "${FROMS[$k]}" = absent ] && rm -f "$SCR/old/${KF[$k]}"; \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/5] could not lay out the walk - nothing installed"; done
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/5] could not take a copy of the database for the walk - nothing installed"
W1=$(py "$KDIR/walk_s940.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-160; stop "!! [3/5] the walk on a copy: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s940.py" "$SCR/old" "$SCR/copy.db" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/5] the control did not go red ($R0) - nothing installed";; esac
FX=$(py "$KDIR/s940_on.py" "$KDIR" "$SCR/copy.db"); echo "$FX" | cut -c1-200
echo "$FX" | grep -q "^S940 start: messages from" || stop "!! [3/5] the start's dry run on the copy did not finish - nothing installed"
rm -f "$SCR/copy.db"
say "[3/5] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass; the control goes red as it must (the copy removed)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do [ "${FROMS[$k]}" = absent ] && continue; { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/5] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && R="$ROOT/${NAMES[$k]}"; [ -f "$R" ] || R="$ROOT/finance/porders_s454.py"; chmod --reference="$R" "$s" 2>/dev/null; chown --reference="$R" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/5] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/porders); case "$d1" in 404|000|5*) restore "reception's page answers $d1";; esac
d2=$(door /finance/porders/flow); case "$d2" in 404|000|5*) restore "his flow page answers $d2";; esac
d3=$(door /finance/porders/s454/order); case "$d3" in 404|000|5*) restore "reception's order screen answers $d3";; esac
d4=$(door /finance/darpan/kal/api/order); case "$d4" in 404|000|5*) restore "Darpan's order tab answers $d4";; esac
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "import order_rules,order_d1053_msg; print('S940 tick module ok', hasattr(order_rules,'_s940_s454_pass_before'))" 2>&1 | tail -1)
case "$TK" in "S940 tick module ok True") ;; *) restore "the tick's module does not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "order_flow NOT mounted|S921 home failed|order_flow\.py|porders\.py|porders_s454\.py|order_s778\.py|order_d1053\.py|darpan_kal\.py|S939 |S940 |darpan_kal not|supplier_msg NOT mounted|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
PLACING=0
say "[4/5] the three files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, reception's page $d1, his flow page $d2, reception's order screen $d3, Darpan's tab $d4 (login-gated), the service log clean since the restart"
FX=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -u -W ignore -B "$KDIR/s940_on.py" "$KDIR" "$LIVE_DB" 2>&1)
echo "$FX" | cut -c1-200
echo "$FX" | grep -q "^S940 start: messages from" && say "[4/5] the messages start now (the tick sends them, every ten minutes)" || say "!! [4/5] the start did not finish (the files are installed) - send a photo of this screen to Claude"
release_lock
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s940.sh  (the files back, $FSVC restarted; S939 stays)"
say ""
say "$KIT: DONE."
exit 0
