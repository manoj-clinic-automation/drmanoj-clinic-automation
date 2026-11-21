#!/bin/bash
# =============================================================================
#  install_S920_PURCHASE_FLOW_1.sh · kit S920 (21-Nov-2026, Sanjeevni session 499) · D1030 (the owner's mock-up v4 FINAL, 19:20 IST 21-Nov)
#   /root/finance/order_flow.py  (NEW)          : the ONE reader of the purchase flow (late / on the way / arrived, not in Marg / medicines
#        still missing / done, and the team list of out of stock and substitutes) and his buttons (Order again · Out of stock · Close: never
#        came · Chase now · Order from <dealer> · Wait a week · Drop it · Substitute OK / Not OK). Writes only its own table order_flow_mark
#        and through order_s778's existing doors; never Marg, purchase_line, purchase_bill or stock.
#   /root/finance/porders.py c495f812 -> TO     : one block appended (the file's own wrapper pattern): init mounts order_flow (fail-soft);
#        the owner's /finance/porders?old=1 opens on the grouped view, the S454 cards, settings and the old ledger folded below, unchanged.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s920kit && cp -rp /root/deploy/repo/deploy_kits/S920_PURCHASE_FLOW_1 /tmp/s920kit && bash /tmp/s920kit/install_S920_PURCHASE_FLOW_1.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S920_PURCHASE_FLOW_1"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
NAMES=("finance/porders.py" "finance/order_flow.py")
FROMS=("c495f81265b190284c148196850f5fb6" "absent")
KF=("porders.py" "order_flow.py")
TOS=(); for k in 0 1; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s920_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S920_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s920"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in 0 1; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  [ -f "$(bak 0)" ] && \cp -p "$(bak 0)" "$ROOT/${NAMES[0]}"
  [ -f "$ROOT/${NAMES[1]}" ] && mv -f "$ROOT/${NAMES[1]}" "$ROOT/${NAMES[1]}.removed_S920_$STAMP"
  "$SYSTEMCTL" restart "$FSVC" || true
  say "   ${NAMES[0]} $(cur 0 | cut -c1-8) (expected ${FROMS[0]:0:8}); ${NAMES[1]} $(cur 1)"
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$@" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in 0 1; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/5] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in 0 1; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
[ "$ALL" = 1 ] && { say "$KIT: ALREADY INSTALLED - both files are at the new version; nothing to do."; exit 0; }
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in 0 1; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/5] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/porders.py" "$KDIR/order_flow.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] porders.py at its FROM pin, order_flow.py absent; the two new files compile on both pythons"
mkdir -p "$SCR/new" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$SCR/new/" 2>/dev/null; \cp -p "$KDIR/porders.py" "$KDIR/order_flow.py" "$SCR/new/" \
  || stop "!! [3/5] could not lay out the walk - nothing installed"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/5] could not take a copy of the database for the walk - nothing installed"
W1=$(py "$KDIR/walk_s920.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-160; stop "!! [3/5] the walk on a copy: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s920.py" "$SCR/new" "$SCR/copy.db" control); R0=$(echo "$W0" | tail -1)
[ "$R0" = "CONTROL RESULT: RED (as it must)" ] || stop "!! [3/5] the control did not go red ($R0) - nothing installed"
rm -f "$SCR/copy.db"
say "[3/5] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass; the control goes red as it must (the copy removed)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/${NAMES[0]}" "$(bak 0)" && [ "$(m5 "$(bak 0)")" = "${FROMS[0]}" ]; } || stop "!! [4/5] could not write the backup of ${NAMES[0]} - nothing placed"
for k in 0 1; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ROOT/${NAMES[0]}" "$s" 2>/dev/null; chown --reference="$ROOT/${NAMES[0]}" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/5] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in 1 0; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/porders/flow); case "$d1" in 404|000|5*) restore "the grouped page answers $d1 (not mounted)";; esac
d2=$(door "/finance/porders?old=1"); case "$d2" in 404|000|5*) restore "the orders page answers $d2";; esac
PLACING=0
release_lock
say "[4/5] two files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the grouped page answers $d1 and the orders page $d2 (mounted, login-gated)"
say "[5/5] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s920.sh  (porders.py back, order_flow.py set aside, $FSVC restarted)"
say ""
say "$KIT: DONE."
exit 0
