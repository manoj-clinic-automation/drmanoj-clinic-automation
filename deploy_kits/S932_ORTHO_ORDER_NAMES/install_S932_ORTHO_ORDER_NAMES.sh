#!/bin/bash
# =============================================================================
#  install_S932_ORTHO_ORDER_NAMES.sh · kit S932 (22-Nov-2026, Sanjeevni session 503) · F-1579 (the stock plan, D1037)
#   /root/finance/order_sheet.py 85ce2148 -> TO : an orthotic ORDER LINE (Darpan's kept 'yes' row on reception's card, the dealer's sheet and
#        message) carries Marg's CURRENT name -- the ticked rename's new name (item_alias) -- never the count's old spelling (ANKLE BINDER
#        BAMBOO M was ordered under it thrice); the kept rule reads the order book under BOTH names, so a line ordered under the new name
#        clears the kept row; reception's quantity edit under either name applies.
#   /root/finance/porders.py     ea014fbd -> TO : the on-order picture folds a line under the new name back to the lane's own (old) key.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s932kit && cp -rp /root/deploy/repo/deploy_kits/S932_ORTHO_ORDER_NAMES /tmp/s932kit && bash /tmp/s932kit/install_S932_ORTHO_ORDER_NAMES.sh
#  (DRY=1 before bash: every gate and every walk; NOTHING written.)
# =============================================================================
set -u
KIT="S932_ORTHO_ORDER_NAMES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE_DB_LIVE="${SPINE_DB_LIVE:-$ROOT/finance/spine/spine.db}"
NAMES=("finance/order_sheet.py" "finance/porders.py")
FROMS=("85ce21480858bae6c373fb218e64ffc2" "ea014fbd9b90c81244e52940b10adf27")   # read whole from the live bytes (the 22-Nov bundle; porders.py = S925's TO), never typed from a prefix (F-1480)
KF=("order_sheet.py" "porders.py")
N=2; IDX="0 1"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s932_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S932_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s932"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
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
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1200 "$VPY" -u -W ignore -B "$@" 2>&1); }
reds() { { echo "$1" | grep -E '^(FAIL|RED)' | sed -E 's/^(FAIL|RED) +//' | cut -d'[' -f1 | sed -E 's/\([0-9]+\)/(N)/g; s/ *$//'; echo "$1" | grep -q '^RESULT:' || echo "the walk did not finish"; } | sort -u; }   # a count inside a label is not a new red (walk_s924's 'every other line unchanged (N)': the orthotic line itself moves)

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/6] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/order_sheet.py" "$KDIR/porders.py" "$KDIR/walk_s932.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/new/spine" "$SCR/old/spine" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
mkdir -p "$SCR/new/finance_ui" "$SCR/old/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/* "$SCR/old/finance_ui/" 2>/dev/null
\cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/old/" 2>/dev/null   # S927's walk reads it beside the code
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2" >/dev/null && [ -s "$2" ]; }
copydb "$LIVE_DB" "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database - nothing installed"
# (a) the walk: a scratch database with the copy's schema, one ticked rename, Darpan's yes rows, the vendor's orders; the control (the live files) must go red
W1=$(py "$KDIR/walk_s932.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep -E "^FAIL" | cut -c1-200; stop "!! [3/6] the walk on the new files: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s932.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
say "[3/6] S932's walk: $(echo "$W1" | grep -c '^ok') checks pass on the new files; the control goes red as it must ($(echo "$W0" | grep -c '^FAIL') red)"
# (b) the purchase flow's own proofs (S920-S926), old files vs new on copies of the live database: stop only on a check WORSE than the live files (the S837 rule)
WORSE=""
for kk in S920_PURCHASE_FLOW_1/walk_s920.py S921_PURCHASE_FLOW_2/walk_s921.py S922_PURCHASE_FLOW_3/walk_s922.py S923_PURCHASE_FLOW_4/walk_s923.py S924_PURCHASE_FLOW_5/walk_s924.py S925_OWNER_TILE_TO_FLOW/walk_s925.py S926_SHORTAGES_AND_RENAMES/walk_s926.py; do
  [ -f "$REPO_KITS/$kk" ] || { say "   (no $kk in the repo - skipped)"; continue; }
  copydb "$LIVE_DB" "$SCR/c_old.db"; copydb "$LIVE_DB" "$SCR/c_new.db"
  O=$(py "$REPO_KITS/$kk" "$SCR/old" "$SCR/c_old.db"); Nn=$(py "$REPO_KITS/$kk" "$SCR/new" "$SCR/c_new.db")
  extra=$(comm -13 <(reds "$O") <(reds "$Nn") | grep -v '^$')
  say "   $(basename "$kk" .py): old $(echo "$O" | grep -c -E '^(ok|PASS)') ok / new $(echo "$Nn" | grep -c -E '^(ok|PASS)') ok$( [ -z "$extra" ] || echo ' -- WORSE')"
  [ -z "$extra" ] || WORSE="$WORSE
$(basename "$kk" .py): $extra"
  rm -f "$SCR/c_old.db" "$SCR/c_new.db"
done
[ -z "$WORSE" ] || stop "!! [3/6] an earlier kit's proof is WORSE on the new files than on the live ones - nothing installed:$WORSE"
rm -f "$SCR/copy.db"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; ref="$ROOT/${NAMES[$k]}"
  { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ref" "$s" 2>/dev/null; chown --reference="$ref" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/porders/flow); case "$d1" in 404|000|5*) restore "the flow page answers $d1";; esac   # login-gated: 302 says nothing (F-1439)
d2=$(door /finance/porders/api/summary); case "$d2" in 404|000|5*) restore "the porders summary door answers $d2";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|Error:" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
PLACING=0
say "[4/6] the two files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors $d1 / $d2 (login-gated), the service log clean since the restart"
release_lock
say "[5/6] what changes now: an orthotic line on reception's order card, the dealer's sheet and message carries the name Marg prints TODAY (Amir's ticked rename), never the old count spelling; a line ordered under the new name is not offered again; the on-order picture reads both names."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s932.sh  (the two files back to their FROM pins, $FSVC restarted)"
say ""
say "$KIT: DONE."
exit 0
