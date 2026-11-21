#!/bin/bash
# =============================================================================
#  install_S921_PURCHASE_FLOW_2.sh · kit S921 (21-Nov-2026, Sanjeevni session 500) · D1030 / D1034 (mock-up v4 FINAL, tab "Reception")
#   /root/finance/order_flow.py   f4ce2c93 -> TO : v1.1 -- reception's strip (rec_body, from groups() alone) and her doors
#        (POST /finance/porders/api/flow/rec: Call kiya -- aa raha hai · Out of stock · Nahi bhejenge · Dobara order karo · Substitute aaya);
#        his late row reads her word; his team list in English quantities (F-1551); /finance/porders/flow?rec=1 = his preview of her strip.
#        New table order_flow_rec (her word). Writes nothing else new.
#   /root/finance/porders_s454.py cdb9b65f -> TO : reception's home carries the strip in place of its two rows (late, maal aaya);
#        the September link off every staff home (F-1548); no alert() on his settings / test-message cards (F-1552). Switch:
#        setting order_flow.rec_on = 0 gives her home exactly as before.
#   /root/finance/order_s778.py   10842db6 -> TO : "Ab nahi milta" / "No longer available" read "Out of stock".
#   /root/finance/porders.html    cbe1a46a -> TO : the engine's practice lines never on a staff screen (F-1548).
#   F-1547, once, after the files are green: the 27 order messages of 12-20 Nov the phone sent (marked skipped) become sent.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s921kit && cp -rp /root/deploy/repo/deploy_kits/S921_PURCHASE_FLOW_2 /tmp/s921kit && bash /tmp/s921kit/install_S921_PURCHASE_FLOW_2.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S921_PURCHASE_FLOW_2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
NAMES=("finance/order_flow.py" "finance/porders_s454.py" "finance/order_s778.py" "finance/porders.html")
FROMS=("f4ce2c934f410944cf1816adb59f143b" "cdb9b65f9919a2203207771d074a4a6e" "10842db6389c010e0fbe87f6c9369819" "cbe1a46a72e0e82489c00397e303daab")
KF=("order_flow.py" "porders_s454.py" "order_s778.py" "porders.html")
N=4; IDX="0 1 2 3"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s921_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
IDS="$ROOT/finance/.s921_f1547_ids.txt"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S921_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s921"; }
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
  for k in $IDX; do [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for k in $IDX; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -u -W ignore -B "$@" 2>&1); }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/6] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - all four files are at the new version."; [ "${DRY:-0}" = 1 ] || { R=$(py "$KDIR/f1547_s921.py" "$LIVE_DB"); say "   F-1547 check: $R"; }; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/order_flow.py" "$KDIR/porders_s454.py" "$KDIR/order_s778.py" "$KDIR/walk_s921.py" "$KDIR/f1547_s921.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the four live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database for the walk - nothing installed"
W1=$(py "$KDIR/walk_s921.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-160; stop "!! [3/6] the walk on a copy: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s921.py" "$SCR/new" "$SCR/copy.db" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
F0=$(py "$KDIR/f1547_s921.py" "$SCR/copy.db")
rm -f "$SCR/copy.db"
say "[3/6] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass; the control goes red as it must; on the copy $F0 (the copy removed)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; chown --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in 3 2 0 1; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/porders); case "$d1" in 404|000|5*) restore "reception's page answers $d1";; esac
d2=$(door /finance/porders/flow); case "$d2" in 404|000|5*) restore "his grouped page answers $d2";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "order_flow NOT mounted|S921 home failed|order_flow\.py|porders_s454\.py|order_s778\.py" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
PLACING=0
say "[4/6] four files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, reception's page $d1, his page $d2 (login-gated), the service log clean since the restart"
F1=$(py "$KDIR/f1547_s921.py" "$LIVE_DB" --write)
case "$F1" in "F1547 n="*) echo "$F1" > "$IDS"; say "[5/6] F-1547 once: $F1 (the ids kept in $IDS for the undo)";;
  *) say "!! [5/6] F-1547 did not run ($(echo "$F1" | tail -1 | cut -c1-120)) - the four files are live and green; the messages are untouched. Tell Claude.";; esac
release_lock
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s921.sh  (the four files back, the 27 messages back to skipped, $FSVC restarted)"
say ""
say "$KIT: DONE."
exit 0
