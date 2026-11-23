#!/bin/bash
# =============================================================================
#  install_S936_RECOUNT_SITTING.sh · kit S936 (23-Nov-2026, Sanjeevni session 506) · the owner's D1046 (11:18) and D1047 (11:41)
#   D1046 THE RECOUNT RULE: a count short of the expected figure by about a delivery received in the days before it is HELD as a recount --
#   never the shelf figure (so never the order list's 'on hand'), no loss line, no trace, out of the month's leakage -- and goes on Darpan's
#   Abhi ginti by itself: "was the carton of bill N on the shelf?". His next count of the item answers it and is judged as any count.
#   First repair: TRAMATEE P (Saturday's 9:4 without Mannat's carton of bill 502): point 388 recounted, loss line 7 void, trace 35 closed.
#   D1047 ONE BILL PER SITTING: Darpan's Abhi ginti card takes the last sale bill ONCE at the top and carries it to every item he saves;
#   'Sale hui? Naya bill likhiye' asks again. The server takes the sitting's bill when an item comes without one.
#   /root/finance/stock_watch.py    048b51df -> TO : the hold, the recount ask, the sitting's bill, the three settings, the TRAMATEE repair's doors
#   /root/finance/stock_figure.py   d7fac10c -> TO : points() leaves out a held count (the shelf base -- the order engine, the record, every judgment)
#   /root/finance/stockmatch.py     e459af2a -> TO : the person passed to Darpan's view; /api/now takes no_bill; mount line S936 v1.4
#   /root/finance/stockmatch.html   2a985d94 -> TO : the Abhi ginti card: one bill box for the sitting; a recount shows its question (Hindi)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s936kit && cp -rp /root/deploy/repo/deploy_kits/S936_RECOUNT_SITTING /tmp/s936kit && bash /tmp/s936kit/install_S936_RECOUNT_SITTING.sh
#  (DRY=1 before bash: every gate and the walks; NOTHING written.)
# =============================================================================
set -u
KIT="S936_RECOUNT_SITTING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE_DB_LIVE="${SPINE_DB_LIVE:-$ROOT/finance/spine/spine.db}"
BEFORE_JSON="${BEFORE_JSON:-$ROOT/finance/.s936_repair_before.json}"
NAMES=("finance/stock_watch.py" "finance/stock_figure.py" "finance/stockmatch.py" "finance/stockmatch.html")
FROMS=("048b51df91a5dc8babbbc6bca983d5de" "d7fac10cec56b0db170da3d40326a0c6" "e459af2a05a0451d81e6c6fc0c62082f" "2a985d94217b05cdb9b5e657db3b1290")
KF=("stock_watch.py" "stock_figure.py" "stockmatch.py" "stockmatch.html")
IDX="0 1 2 3"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s936_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S936_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s936"; }
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
repair() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -B -W ignore "$KDIR/repair_s936.py" "$LIVE_DB" --before "$BEFORE_JSON" 2>&1); }
say_repair() { local R; R=$(repair); echo "$R" | grep -v '^RESULT' | sed 's/^/   /' | cut -c1-260
  case "$(echo "$R" | tail -1)" in "RESULT: REPAIRED"*|"RESULT: ALREADY"*) say "   TRAMATEE repair: $(echo "$R" | tail -1 | sed 's/^RESULT: //')";;
    *) say "   !! the TRAMATEE repair did NOT run ($(echo "$R" | tail -1 | cut -c1-160)) -- the files are installed; tell Claude";; esac; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/6] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the files are at the new version."
  if [ "${DRY:-0}" != 1 ]; then
    if mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say_repair; release_lock
    else say "   another build holds the lock $LOCK - the TRAMATEE repair was not run now; run this line again in five minutes"; fi
  fi; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done
for kk in S934_COUNT_NOW/synth_s934.py S933_STOCK_OF_RECORD/synth_s933.py S928_STOCK_ONE_RULE/synth_s928.py S930_STOCK_CHECK_PAGE/walk_s930.py S927_HUB_NEEDS_YOU_INLINE/walk_s927.py S894_ASKED_COUNT_BACK/synth_s894.py; do
  [ -f "$REPO_KITS/$kk" ] || stop "!! [2/6] the repo has no $kk (an earlier proof) - nothing installed"; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_watch.py" "$KDIR/stock_figure.py" "$KDIR/stockmatch.py" "$KDIR/synth_s936.py" "$KDIR/liveshape_s936.py" "$KDIR/repair_s936.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/new/spine" "$SCR/old/spine" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
mkdir -p "$SCR/new/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/new/" 2>/dev/null   # S927's walk reads it beside the code
\cp -rp "$SCR/new/." "$SCR/old/"
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2" >/dev/null && [ -s "$2" ]; }
copydb "$LIVE_DB" "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database - nothing installed"
# (a) the synth: made-up spines, counts and deliveries on a scratch database with the copy's schema; the control (the live files) must go red
W1=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s936.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
case "$R1" in "RESULT: ALL PASS"*) ;; *) echo "$W1" | grep -E "^FAIL|Traceback|Error" | cut -c1-220; stop "!! [3/6] the walk on the new files: $R1 - nothing installed";; esac
W0=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s936.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | grep -c '^FAIL')
[ "$R0" -ge 15 ] || stop "!! [3/6] the control did not go red ($R0 red) - nothing installed"
say "[3/6] S936's walk: $(echo "$W1" | grep -c '^ok') checks pass on the new files; the control goes red as it must ($R0 red)"
# (b) the live shape: the stock of record on copies of the live databases, old files vs new -- identical; the TRAMATEE repair on the copy
[ -f "$SPINE_DB_LIVE" ] || stop "!! [3/6] no spine at $SPINE_DB_LIVE - the live-shape build cannot run; nothing installed"
copydb "$SPINE_DB_LIVE" "$SCR/spine.db" || stop "!! [3/6] could not copy the spine - nothing installed"
LS=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/liveshape_s936.py" "$SCR/new" "$SCR/old" "$SCR/copy.db" "$SCR/spine.db" "$KDIR/repair_s936.py"); RL=$(echo "$LS" | tail -1)
echo "$LS" | grep -E "^INFO|^ok|^FAIL" | cut -c1-260
[ "$RL" = "RESULT: ALL PASS" ] || stop "!! [3/6] the live shape: $RL - nothing installed"
rm -f "$SCR/spine.db"
# (c) the earlier kits' proofs are not worse on the new files (S837 rule)
WORSE=""
notworse() { local label="$1" O="$2" Nn="$3" skip="$4" extra
  extra=$(comm -13 <(reds "$O") <(reds "$Nn") | grep -v '^$'); [ -n "$skip" ] && extra=$(echo "$extra" | grep -v -F -f <(printf '%s\n' "$skip"))
  say "   $label: old $(echo "$O" | tail -1 | cut -c1-60) / new $(echo "$Nn" | tail -1 | cut -c1-60)"
  [ -z "$extra" ] || WORSE="$WORSE
$label: $extra"; }
fresh() { rm -f "$SCR/c1.db" "$SCR/c2.db"; copydb "$LIVE_DB" "$SCR/c1.db" && copydb "$LIVE_DB" "$SCR/c2.db"; }
# S934's five lines that D1047 SUPERSEDES by the owner's word: a blank bill in a sitting now takes the sitting's bill; the card's label reads 'Aakhri sale bill no.'
S934_SUPERSEDED="T17b no bill number keyed
T17 no bill number -> judged now by its time
T18 before the count day's sale report
T20 with the count day's sales in
T32b the pages"
fresh; notworse synth_s934 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S934_COUNT_NOW/synth_s934.py" "$SCR/old" "$SCR/c1.db")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S934_COUNT_NOW/synth_s934.py" "$SCR/new" "$SCR/c2.db")" "$S934_SUPERSEDED"
fresh; W2=$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$KDIR/synth_s934_under_s936.py" "$SCR/new" "$SCR/c2.db"); say "   synth_s934 with its two superseded lines put to D1047: $(echo "$W2" | tail -1)"
case "$(echo "$W2" | tail -1)" in "RESULT: ALL PASS"*) ;; *) WORSE="$WORSE
synth_s934_under_s936: $(echo "$W2" | tail -1)";; esac
fresh; notworse synth_s933 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S933_STOCK_OF_RECORD/synth_s933.py" "$SCR/old" "$SCR/c1.db")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S933_STOCK_OF_RECORD/synth_s933.py" "$SCR/new" "$SCR/c2.db")" ""
fresh; notworse synth_s928 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" "$SCR/old" "$SCR/c1.db")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S928_STOCK_ONE_RULE/synth_s928.py" "$SCR/new" "$SCR/c2.db")" ""
fresh; notworse walk_s930 "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" "$SCR/old" "$SCR/c1.db" "$REPO_KITS/S928_STOCK_ONE_RULE")" "$(SHARED_LIB_DIR="${SHARED_LIB_DIR:-/root/shared}" py "$REPO_KITS/S930_STOCK_CHECK_PAGE/walk_s930.py" "$SCR/new" "$SCR/c2.db" "$REPO_KITS/S928_STOCK_ONE_RULE")" ""
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
flog | grep -q "S936 stockmatch mounted v1.4" || restore "the service log since the restart does not say stockmatch mounted v1.4 (F-1554)"
PLACING=0
say "[4/6] the four files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors $d1 / $d2 / $d3 / $d4 (login-gated), the service log says stock_check v1.3 and stockmatch v1.4 mounted and is clean since the restart"
say "[5/6] the first repair (D1046), TRAMATEE P:"
say_repair
release_lock
say "   what changes now: a count short by about a fresh delivery is held for a recount -- not the shelf, not a loss, not the order list -- and Darpan gets it back on Abhi ginti with the bill's carton named. On Abhi ginti he types the last sale bill once for the sitting; 'Sale hui? Naya bill likhiye' asks again."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s936.sh  (the four files back, $FSVC restarted, TRAMATEE's four rows as they were; the new columns stay, harmless)"
say ""
say "$KIT: DONE."
exit 0
