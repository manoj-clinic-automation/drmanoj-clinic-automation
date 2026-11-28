#!/bin/bash
# =============================================================================
#  install_S975_STOCKCHECK_V10.sh · kit S975 (28-Nov-2026, Sanjeevni session 542) · D1106: the Stock check page v10 (mock-up v10, his "OK" 11:52 IST)
#   /root/finance/stock_check.py    623c1052 -> v1.9 : the three bands (your write-offs . today's counts . waiting on others); F-1738 in box 3
#   /root/finance/stock_check.html  225af840         : the page drawn in the three bands; the boxes as before inside band 3's folds
#   /root/finance/voucher_judge.py  0a066f96 -> v1.5 : F-1738 -- a fresh count with more on the shelf than in Marg is 'surplus', never a loss
#   /root/finance/item_ledger.py    6735167f         : F-1739 -- a whole-unit item's count (CCM = bottle) told in its bottles
#  READ ONLY: no table, no setting, no staff screen. One line:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s975kit && cp -rp /root/deploy/repo/deploy_kits/S975_STOCKCHECK_V10 /tmp/s975kit && bash /tmp/s975kit/install_S975_STOCKCHECK_V10.sh
#  (DRY=1 before bash: every gate and the walks; NOTHING written.)
# =============================================================================
set -u
KIT="S975_STOCKCHECK_V10"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/stock_check.py 623c10528fead13397ac7e7067eb9935" "finance/stock_check.html 225af840770e22779bd5b670f15fb22a"
       "finance/voucher_judge.py 0a066f960fba1a110084121a82d4ede3" "finance/item_ledger.py 6735167f3b56793ae6edbfd504f5584e")
READS=("finance/voucher_inquiry.py 56780986" "finance/amir_day.py 164dbceb" "finance/stock_watch.py fe0a89cd" "finance/voucher_scan.py 9c5ff7ef"
       "finance/loss_piles.py ad0454ae" "finance/qty_words.py 706db7cc" "finance/stock_record.py 14caf248" "finance/record_judges.py 85c0d3e3")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s975_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s975"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; b="$f.bak_S975_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing else was changed (this kit writes no table). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
# a regression walk on the new files: it must finish, and fail only on the lines named (its own version lines)
reg() { local name="$1" out="$2"; shift 2; local bad; bad=$(echo "$out" | grep "^FAIL" | grep -v -x -F "$(printf '%s\n' "$@")")   # each allowed line matched WHOLE (cold review 7)
  echo "$out" | tail -1 | grep -q "^WALK " && [ -z "$bad" ] || { echo "$bad" | head -3 | cut -c1-200; stop "!! [3/6] $name's own walk on the new files: $(echo "$out" | tail -1) - nothing installed"; }; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
ALL=1
for e in "${FILES[@]}"; do n="${e%% *}"; to="$(to_of "$n")"
  [ -n "$to" ] && [ "$(m5 "$KDIR/$(basename "$n")")" = "$to" ] || { say "!! [1/6] the kit's $(basename "$n") is not at its TO pin - nothing installed"; exit 1; }
  [ "$(m5 "$ROOT/$n")" = "$to" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the four files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"
  [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - changed after this kit was built. STOP, nothing installed. Tell Claude."; done
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/6] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_check.py" "$KDIR/voucher_judge.py" "$KDIR/item_ledger.py" \
  "$KDIR/walk_s975.py" "$KDIR/walk_s973.py" "$KDIR/walk_s971.py" "$KDIR/walk_s969.py" "$KDIR/walk_s967.py" "$KDIR/walk_s965_regress.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the four files at their FROM pins; voucher_inquiry / amir_day / stock_watch / voucher_scan / loss_piles / qty_words / stock_record / record_judges at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice on one layout), the control red on the live files, the five earlier walks on the new files, a copy of the database
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
\cp -p "$KDIR/stock_check.py" "$KDIR/stock_check.html" "$KDIR/voucher_judge.py" "$KDIR/item_ledger.py" "$SCR/new/finance/" || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s975.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR/walk_s971.py"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 33 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s975.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR/walk_s971.py"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s975.py" "$SCR/old/finance" "$SCR/old/marg_ingest" "$KDIR/walk_s971.py")
echo "$W0" | grep -q "^FAIL  V1 the desk answers the three bands" || stop "!! [3/6] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
reg S973 "$(py "$KDIR/walk_s973.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR/walk_s971.py")" "FAIL  V1 the judge says v1.4" "FAIL  J4 the judge v1.3 is still read only"
reg S971 "$(py "$KDIR/walk_s971.py" "$SCR/new/finance" "$SCR/new/marg_ingest")" "FAIL  J4 the judge v1.3 is still read only" "FAIL  R3 healthz v1.8, kit B and the loss register  -- {'desk': True, 'kit': 'S930_STOCK_CHECK_PAGE', 'kit_b': 'S971_AMIR_BY_HIMSELF', 'kit_desk': 'S969_STOCKCHECK_DESK_WRITES', 'losses': True, 'ok': True, 'page': True, 'version': '1.9', 'writes': True}"
reg S969 "$(py "$KDIR/walk_s969.py" "$SCR/new/finance" "$SCR/new/marg_ingest")" "FAIL  R3 healthz v1.7 with writes  -- {'desk': True, 'kit': 'S930_STOCK_CHECK_PAGE', 'kit_b': 'S971_AMIR_BY_HIMSELF', 'kit_desk': 'S969_STOCKCHECK_DESK_WRITES', 'losses': True, 'ok': True, 'page': True, 'version': '1.9', 'writes': True}"
reg S967 "$(py "$KDIR/walk_s967.py" "$SCR/new/finance" "$SCR/new/marg_ingest")" "FAIL  W4 the healthz says v1.6 and the desk" "FAIL  D13 the rules panel: the allowance, the evening hour, the rule date, the batch check"
reg S965 "$(py "$KDIR/walk_s965_regress.py" "$SCR/new/finance" "$SCR/new/marg_ingest")" "FAIL  C14c the healthz says v1.5"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"
LS=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copy.db" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import sqlite3,sys,json; sys.path.insert(0,'.'); import stock_check as S
c=sqlite3.connect(sys.argv[1]); n0=c.total_changes; K=S.desk(c); B=S._desk_before_s975(c); ro=(c.total_changes==n0); t=K.get('v10_totals') or {}
same=all(json.dumps(K.get(k),sort_keys=True,default=str)==json.dumps(B.get(k),sort_keys=True,default=str) for k in ('box1','allow','way','moves','settled','recount'))
print('LIVE-SHAPE ok=%s v10=%s readonly=%s boxes_same=%s writeoffs=%s today=%s earlier=%s way3=%s' % (K.get('ok'), K.get('v10'), ro, same, t.get('band1'), t.get('today'), t.get('earlier'), t.get('way3')))" "$SCR/copy.db" 2>&1 | grep "^LIVE-SHAPE" | tail -1)
rm -f "$SCR/copy.db"; echo "    $LS" | cut -c1-240
case "$LS" in "LIVE-SHAPE ok=True v10=True readonly=True boxes_same=True "*) ;; *) stop "!! [3/6] the new page on a copy of the live database: ${LS:-no answer} - nothing installed";; esac
say "[3/6] the walk on made-up data: $R1, twice on one layout; the control red on the live files; S973's, S971's, S969's, S967's and S965's walks on the new files (only their version lines); the bands on a COPY of the live database (above), every box as before"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S975_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s975"; f="$ROOT/$n"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s975" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/desk /finance/stockcheck/losses /finance/sanjeevni/ledger /finance/amir /finance/approvals; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "
import sys; import voucher_judge,stock_check,item_ledger
print('S975 modules ok', voucher_judge.VERSION, stock_check.VERSION, item_ledger.VERSION, hasattr(stock_check,'_s975_bands'))" 2>&1 | tail -1)
case "$TK" in "S975 modules ok 1.5 1.9 S975-ITEM-LEDGER-1.6 True") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; LG=$(flog); bad=$(echo "$LG" | grep -iE "voucher_judge\.py|stock_check\.py|item_ledger\.py|stock_check not mounted|S975 bands stopped" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
echo "$LG" | grep -q "S930 stock_check mounted v1.9" || restore "the service log does not show 'S930 stock_check mounted v1.9' (the doors answer 302 unsigned, so the log is the mount's proof)"
say "[4/6] four files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors answer, the modules load, the log clean"
RD=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S
c=sqlite3.connect('file:$LIVE_DB?mode=ro', uri=True); K=S.desk(c); t=K.get('v10_totals') or {}
print('S975 the page on the live database:', K.get('ok'), K.get('v10'), '| your write-offs', t.get('band1'), '(Amir done', str(t.get('b1_done'))+')', '| counted today', t.get('today'), '| earlier waiting', t.get('earlier'), '| on their way', t.get('way3'), '| count first', t.get('recount'))" | tail -1)
case "$RD" in "S975 the page on the live database: True True "*) ;; *) restore "the page on the live database ($(echo "$RD" | cut -c1-140))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
PLACING=0
say "[5/6] $RD"
say "[6/6] Backups: $ROOT/finance/*.bak_S975_*  ·  nothing written to the database"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s975.sh"
say ""
say "$KIT: DONE."
exit 0
