#!/bin/bash
# =============================================================================
#  install_S934_COUNT_NOW.sh · kit S934 (23-Nov-2026, Sanjeevni session 505) · the owner's word 08:16-08:22 IST
#   His Count button on the Stock check page offers two choices: COUNT NOW (Darpan's screen at once, 'Abhi ginti', with the LAST SALE BILL
#   number) or NEXT LIST (the head of his next morning list, as before). A Count now is placed to the bill: the sales billed up to that number
#   left the shelf before he counted, the rest after; the point waits for that day's sale report and is then judged (expected = the end of
#   the day + the sales billed after the number). His open asks carry a two-tap Withdraw. The install withdraws every ask open now (his word).
#   /root/finance/stock_watch.py    0dd0a40a -> TO : ask(mode), withdraw_ask, now_view, answer_now, _s934_settle, the morning roster skips a Count now
#   /root/finance/stock_figure.py   5d15e77d -> TO : a count placed to its bill is carried forward without the day's sales up to that bill
#   /root/finance/stock_check.py    bf68c55b -> TO : /api/count {mode}, NEW /api/withdraw, the asks with id + mode, a count waiting for its report
#   /root/finance/stock_check.html  4d6cbc6f -> TO : Count -> Count now / Next list; Your open asks with Withdraw (two taps, no dialog)
#   /root/finance/stockmatch.py     57d04d3e -> TO : NEW /finance/stockmatch/api/now (Darpan's answer + the last bill number); the mount line
#   /root/finance/stockmatch.html   0ec2e32d -> TO : the 'Abhi ginti' card above Aaj ki ginti (Hindi)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s934kit && cp -rp /root/deploy/repo/deploy_kits/S934_COUNT_NOW /tmp/s934kit && bash /tmp/s934kit/install_S934_COUNT_NOW.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S934_COUNT_NOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE_DB_LIVE="${SPINE_DB_LIVE:-$ROOT/finance/spine/spine.db}"
NAMES=("finance/stock_watch.py" "finance/stock_figure.py" "finance/stock_check.py" "finance/stock_check.html" "finance/stockmatch.py" "finance/stockmatch.html")
FROMS=("0dd0a40a238f0cfeb3c907cd488dd791" "5d15e77dae11c7ee0799290e1a442760" "bf68c55b20f90673b134e8d25c23aaa5" "4d6cbc6f8733226663688371473c0ff0" "57d04d3e9c272ebafdcae2e77086f6fc" "0ec2e32d74d5d9167b38b1786eca6032")
KF=("stock_watch.py" "stock_figure.py" "stock_check.py" "stock_check.html" "stockmatch.py" "stockmatch.html")
IDX="0 1 2 3 4 5"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s934_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S934_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s934"; }
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
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1500 "$VPY" -u -W ignore -B "$@" 2>&1); }
reds() { { echo "$1" | grep -E '^(FAIL|RED)' | sed -E 's/^(FAIL|RED) +//' | cut -d'[' -f1 | sed 's/ *$//'; echo "$1" | grep -qE '^RESULT:|ok, [0-9]+ red' || echo "the walk did not finish"; } | sort -u; }

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
for kk in S933_STOCK_OF_RECORD/synth_s933.py S928_STOCK_ONE_RULE/synth_s928.py S930_STOCK_CHECK_PAGE/walk_s930.py S927_HUB_NEEDS_YOU_INLINE/walk_s927.py S894_ASKED_COUNT_BACK/synth_s894.py; do
  [ -f "$REPO_KITS/$kk" ] || stop "!! [2/6] the repo has no $kk (an earlier proof) - nothing installed"; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_watch.py" "$KDIR/stock_figure.py" "$KDIR/stock_check.py" "$KDIR/stockmatch.py" "$KDIR/synth_s934.py" "$KDIR/liveshape_s934.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/new/spine" "$SCR/old/spine" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
mkdir -p "$SCR/new/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/new/" 2>/dev/null   # S927's walk reads it beside the code
\cp -rp "$SCR/new/." "$SCR/old/"
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2" >/dev/null && [ -s "$2" ]; }
copydb "$LIVE_DB" "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database - nothing installed"
# (a) the synth: made-up spines and asks on a scratch database with the copy's schema; the control (the live files) must go red
W1=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s934.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep -E "^FAIL|Traceback|Error" | cut -c1-220; stop "!! [3/6] the walk on the new files: $R1 - nothing installed"; }
W0=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s934.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | grep -c '^FAIL')
[ "$R0" -ge 10 ] || stop "!! [3/6] the control did not go red ($R0 red) - nothing installed"
say "[3/6] S934's walk: $(echo "$W1" | grep -c '^ok') checks pass on the new files; the control goes red as it must ($R0 red)"
# (b) the live shape: the stock of record built on copies of the live databases with the old and the new files -- identical row for row
[ -f "$SPINE_DB_LIVE" ] || stop "!! [3/6] no spine at $SPINE_DB_LIVE - the live-shape build cannot run; nothing installed"
copydb "$SPINE_DB_LIVE" "$SCR/spine.db" || stop "!! [3/6] could not copy the spine - nothing installed"
LS=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/liveshape_s934.py" "$SCR/new" "$SCR/old" "$SCR/copy.db" "$SCR/spine.db"); RL=$(echo "$LS" | tail -1)
echo "$LS" | grep -E "^INFO|^ok|^FAIL" | cut -c1-220
[ "$RL" = "RESULT: ALL PASS" ] || stop "!! [3/6] the live shape: $RL - nothing installed"
rm -f "$SCR/spine.db"
# (c) the earlier kits' proofs are not worse on the new files (S837 rule)
WORSE=""
notworse() { local label="$1" O="$2" Nn="$3" skip="$4" extra
  extra=$(comm -13 <(reds "$O") <(reds "$Nn") | grep -v '^$'); [ -n "$skip" ] && extra=$(echo "$extra" | grep -v -F "$skip")
  say "   $label: old $(echo "$O" | tail -1 | cut -c1-60) / new $(echo "$Nn" | tail -1 | cut -c1-60)"
  [ -z "$extra" ] || WORSE="$WORSE
$label: $extra"; }
fresh() { rm -f "$SCR/c1.db" "$SCR/c2.db"; copydb "$LIVE_DB" "$SCR/c1.db" && copydb "$LIVE_DB" "$SCR/c2.db"; }
fresh; notworse synth_s933 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S933_STOCK_OF_RECORD/synth_s933.py" "$SCR/old" "$SCR/c1.db")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S933_STOCK_OF_RECORD/synth_s933.py" "$SCR/new" "$SCR/c2.db")" ""
fresh; notworse synth_s928 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" "$SCR/old" "$SCR/c1.db")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" "$SCR/new" "$SCR/c2.db")" ""
# walk_s930's door list is a fixed set of three; S934 adds /api/withdraw -- that one line is SUPERSEDED, not worse
fresh; notworse walk_s930 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" "$SCR/old" "$SCR/c1.db" "$REPO_KITS/S928_STOCK_ONE_RULE")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" "$SCR/new" "$SCR/c2.db" "$REPO_KITS/S928_STOCK_ONE_RULE")" "C: every door the page calls exists in the module"
fresh; notworse walk_s927 "$(py "$REPO_KITS/S927_HUB_NEEDS_YOU_INLINE/walk_s927.py" "$SCR/old" "$SCR/c1.db")" "$(py "$REPO_KITS/S927_HUB_NEEDS_YOU_INLINE/walk_s927.py" "$SCR/new" "$SCR/c2.db")" ""
fresh; notworse synth_s894 "$(py "$REPO_KITS/S894_ASKED_COUNT_BACK/synth_s894.py" --code "$SCR/old" --finance "$SCR/c1.db")" "$(py "$REPO_KITS/S894_ASKED_COUNT_BACK/synth_s894.py" --code "$SCR/new" --finance "$SCR/c2.db")" ""
rm -f "$SCR/c1.db" "$SCR/c2.db" "$SCR/copy.db"
[ -z "$WORSE" ] || stop "!! [3/6] an earlier kit's proof is WORSE on the new files than on the live ones - nothing installed:$WORSE"
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
d1=$(door /finance/stockcheck/api/healthz); case "$d1" in 404|000|5*) restore "the Stock check healthz answers $d1";; esac   # login-gated: 302 says nothing (F-1439); the log proves the mount
d2=$(door /finance/stockcheck/); case "$d2" in 404|000|5*) restore "the Stock check page answers $d2";; esac
d3=$(door /finance/stockmatch/api/healthz); case "$d3" in 404|000|5*) restore "Darpan's Stock milaan healthz answers $d3";; esac
d4=$(door /finance/stockmatch); case "$d4" in 404|000|5*) restore "Darpan's Stock milaan page answers $d4";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "stock_check not mounted|section_count NOT mounted|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
flog | grep -q "S930 stock_check mounted v1.3" || restore "the service log since the restart does not say stock_check mounted v1.3 (F-1554)"
flog | grep -q "S934 stockmatch mounted v1.3" || restore "the service log since the restart does not say stockmatch mounted v1.3 (F-1554)"
PLACING=0
say "[4/6] the six files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors $d1 / $d2 / $d3 / $d4 (login-gated), the service log says stock_check v1.3 and stockmatch v1.3 mounted and is clean since the restart"
# the one-off (his word 08:22, "clear whatever counts I have raised"): every ask open now is withdrawn; a rostered row Darpan has not counted leaves its list
WD=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" timeout 120 "$VPY" -B -c "
import sqlite3, stock_watch as SW
con = sqlite3.connect('$LIVE_DB', timeout=60)
out = SW.withdraw_all_open(con, 'manoj')
print('WITHDRAWN %d: %s' % (len(out), ' . '.join(out)))
" 2>&1 | tail -1)
case "$WD" in WITHDRAWN*) say "   your open asks: $WD";; *) say "   !! your open asks were NOT cleared ($WD) -- the files are installed; withdraw them on the page, each with Withdraw";; esac
release_lock
say "[5/6] what changes now: on the Stock check page every Count button asks 'Count now' or 'Next list'; your open asks show with Withdraw (tap twice). Darpan's Stock milaan screen shows 'Abhi ginti' with the last-bill box; his count is judged when that day's sale report is in."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s934.sh  (the six files back, $FSVC restarted; the new columns stay, harmless; the withdrawn asks stay withdrawn)"
say ""
say "$KIT: DONE."
exit 0
