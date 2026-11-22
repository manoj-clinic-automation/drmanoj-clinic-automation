#!/bin/bash
# =============================================================================
#  install_S930_STOCK_CHECK_PAGE.sh · kit S930 (22-Nov-2026, Sanjeevni session 503) · the owner's mock-up v5 OK (D1037) -- AFTER S928
#   NEW /root/finance/stock_check.py + stock_check.html : his Stock check page -- Marg against the shelf, Darpan's counts (every one), Count this,
#        deliveries waiting for Marg by the scanned bill, the items with no shelf figure yet, the count names Marg no longer prints, the items
#        that agree, the reports behind the page. /finance/stockcheck/ ; the retired Stock drift and Stock now addresses send here.
#   /root/finance/sanjeevni_day.py     c01bf05b -> TO : the mount (one try block, beside hub_panels).
#   /root/finance/stock_watch.py       02727b0f -> TO : a count line on his Needs-you opens the page (href).
#   /root/finance/finance_ui/finance_approvals.html bc5d52c9 -> TO : the Hub's Go to -- 'Stock check' first; the 06-Sep count's hub named as closed.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s930kit && cp -rp /root/deploy/repo/deploy_kits/S930_STOCK_CHECK_PAGE /tmp/s930kit && bash /tmp/s930kit/install_S930_STOCK_CHECK_PAGE.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S930_STOCK_CHECK_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE_DB_LIVE="${SPINE_DB_LIVE:-$ROOT/finance/spine/spine.db}"
NAMES=("finance/stock_check.py" "finance/stock_check.html" "finance/sanjeevni_day.py" "finance/stock_watch.py" "finance/finance_ui/finance_approvals.html")
FROMS=("absent" "absent" "c01bf05bd754c37b2f73d8d1e18b7091" "02727b0fba9d1dd030d15ae6a4811faa" "bc5d52c9aaf7df9ee5747e21083c8642")   # read from the live bytes / S928's TO, never typed from a prefix (F-1480)
KF=("stock_check.py" "stock_check.html" "sanjeevni_day.py" "stock_watch.py" "finance_approvals.html")
N=5; IDX="0 1 2 3 4"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s930_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S930_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s930"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in $IDX; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then rm -f "$ROOT/${NAMES[$k]}"; else [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; fi; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for k in $IDX; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1200 "$VPY" -u -W ignore -B "$@" 2>&1); }
reds() { { echo "$1" | grep -E '^(FAIL|RED)' | sed -E 's/^(FAIL|RED) +//' | cut -d'[' -f1 | sed 's/ *$//'; echo "$1" | grep -q '^RESULT:' || echo "the walk did not finish"; } | sort -u; }

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
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || { [ "${FROMS[$k]}" = absent ] && [ "$(cur $k)" = "${TOS[$k]}" ]; } || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. (stock_watch.py must be at S928's version: install S928 first.) Tell Claude."; done
[ -f "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" ] || stop "!! [2/6] the repo has no S928_STOCK_ONE_RULE/synth_s928.py (the walk's fixtures) - nothing installed"
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_check.py" "$KDIR/sanjeevni_day.py" "$KDIR/stock_watch.py" "$KDIR/walk_s930.py" "$KDIR/liveshape_s930.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/new/spine" "$SCR/old/spine" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
mkdir -p "$SCR/new/finance_ui" "$SCR/old/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/* "$SCR/old/finance_ui/" 2>/dev/null
for k in 0 1 2 3; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
\cp -p "$KDIR/finance_approvals.html" "$SCR/new/finance_ui/finance_approvals.html"; \cp -p "$KDIR/finance_approvals.html" "$SCR/new/"; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/old/" 2>/dev/null
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2" >/dev/null && [ -s "$2" ]; }
copydb "$LIVE_DB" "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database - nothing installed"
W1=$(py "$KDIR/walk_s930.py" "$SCR/new" "$SCR/copy.db" "$REPO_KITS/S928_STOCK_ONE_RULE"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep -E "^FAIL" | cut -c1-200; stop "!! [3/6] the walk on the new files: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s930.py" "$SCR/old" "$SCR/copy.db" "$REPO_KITS/S928_STOCK_ONE_RULE" --control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
say "[3/6] S930's walk: $(echo "$W1" | grep -c '^ok') checks pass on the new files; the control goes red as it must ($(echo "$W0" | grep -c '^FAIL') red)"
if [ -f "$SPINE_DB_LIVE" ]; then
  copydb "$SPINE_DB_LIVE" "$SCR/spine.db" || stop "!! [3/6] could not copy the spine - nothing installed"; copydb "$LIVE_DB" "$SCR/c_ls.db" || stop "!! [3/6] could not copy the database - nothing installed"
  LS=$(py "$KDIR/liveshape_s930.py" "$SCR/new" "$SCR/c_ls.db" "$SCR/spine.db"); RL=$(echo "$LS" | tail -1)
  echo "$LS" | grep -E "^INFO|^   " | head -16 | cut -c1-200
  [ "$RL" = "RESULT: ALL PASS" ] || stop "!! [3/6] the page on copies of the live databases: $RL - nothing installed"
  say "   the page builds on copies of the live databases"
  rm -f "$SCR/c_ls.db" "$SCR/spine.db"
else say "   (no spine at $SPINE_DB_LIVE - the live-shape build skipped)"; fi
WORSE=""
for kk in S927_HUB_NEEDS_YOU_INLINE/walk_s927.py; do
  w="$REPO_KITS/$kk"; [ -f "$w" ] || { say "   (no $kk in the repo - skipped)"; continue; }
  copydb "$LIVE_DB" "$SCR/c_old.db"; copydb "$LIVE_DB" "$SCR/c_new.db"
  O=$(py "$w" "$SCR/old" "$SCR/c_old.db"); Nn=$(py "$w" "$SCR/new" "$SCR/c_new.db")
  extra=$(comm -13 <(reds "$O") <(reds "$Nn") | grep -v '^$')
  say "   $(basename "$w"): old $(echo "$O" | grep -c '^ok') ok / new $(echo "$Nn" | grep -c '^ok') ok"
  [ -z "$extra" ] || WORSE="$WORSE
$(basename "$w"): $extra"
  rm -f "$SCR/c_old.db" "$SCR/c_new.db"
done
S8=$(py "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" "$SCR/new" "$SCR/copy.db"); R8=$(echo "$S8" | tail -1)
say "   synth_s928 on the new files: $R8"
[ "$R8" = "RESULT: ALL PASS" ] || WORSE="$WORSE
synth_s928: $R8"
[ -z "$WORSE" ] || stop "!! [3/6] an earlier kit's proof is WORSE on the new files than on the live ones - nothing installed:$WORSE"
rm -f "$SCR/copy.db"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then [ ! -e "$ROOT/${NAMES[$k]}" ] || [ "$(cur $k)" = "${TOS[$k]}" ] || stop "!! [4/6] $ROOT/${NAMES[$k]} already exists with other bytes - nothing placed"; continue; fi
  { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; ref="$ROOT/${NAMES[$k]}"; [ -e "$ref" ] || ref="$ROOT/finance/sanjeevni_day.py"
  { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ref" "$s" 2>/dev/null; chown --reference="$ref" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/stockcheck/api/healthz); case "$d1" in 404|000|5*) restore "the Stock check healthz answers $d1";; esac   # login-gated: 302 says nothing (F-1439); the log proves the mount
d2=$(door /finance/stockcheck/); case "$d2" in 404|000|5*) restore "the Stock check page answers $d2";; esac
d3=$(door /finance/stock/page/drift); case "$d3" in 404|000|5*) restore "the retired drift address answers $d3";; esac
d4=$(door /finance/sanjeevni/approvals); case "$d4" in 404|000|5*) restore "his Hub page answers $d4";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "stock_check not mounted|hub_panels not mounted|hub_cash not mounted|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
flog | grep -q "S930 stock_check mounted" || restore "the service log since the restart does not say stock_check mounted (F-1554)"
PLACING=0
say "[4/6] the five files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors $d1 / $d2 / $d3 / $d4 (login-gated), the service log says stock_check mounted and is clean since the restart"
release_lock
say "[5/6] what changes now: your Stock check page at /finance/stockcheck/ (the Hub's Go to, first under Stock & expiry); the old Stock drift and Stock now addresses open it; a count line on your Needs-you opens it."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s930.sh  (the three patched files back, the two new files removed, $FSVC restarted)"
say ""
say "$KIT: DONE."
exit 0
