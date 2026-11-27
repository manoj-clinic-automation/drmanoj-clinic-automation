#!/bin/bash
# =============================================================================
#  install_S967_STOCKCHECK_ONE_PAGE.sh · kit S967 (27-Nov-2026, Sanjeevni session 535) · kit A1 of S534_FINAL_BUILD_PLAN
#  His "ok" 09:25 IST 27-Nov on mock-up v9 (D1090, D1091, D1092): THE ONE PAGE, READ ONLY -- no write path in this kit.
#   /root/finance/stock_check.py   83bbed0d -> v1.6 : /api/desk -- the five boxes (short in a fresh count + the allowance group . on its way
#                                                     to Marg . old corrections re-judged on the whole item . vouchers nobody asked . settled).
#   /root/finance/stock_check.html 69d1fabe : the boxes on top, every row opening in place (path . voucher lines . item ledger).
#   /root/finance/voucher_judge.py 81d04b41 -> v1.1 : F-1706 (a re-ask after the done tap waits again) + the whole-item re-judge.
#   /root/finance/item_ledger.py   fe31f2c3 : F-1707 (the counts are ledger rows), /api/fold, ?embed=1, F-1708 ('one of' bill words).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s967kit && cp -rp /root/deploy/repo/deploy_kits/S967_STOCKCHECK_ONE_PAGE /tmp/s967kit && bash /tmp/s967kit/install_S967_STOCKCHECK_ONE_PAGE.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S967_STOCKCHECK_ONE_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/stock_check.py 83bbed0dc396573fa2d0a53d2e12ba93" "finance/stock_check.html 69d1fabe4848d7f0fda5828eb12fb176"
       "finance/item_ledger.py fe31f2c3a5c41412ccbfc7746a255b89" "finance/voucher_judge.py 81d04b411db72820932835c7a43024cf")
READS=("finance/record_judges.py 85c0d3e3" "finance/stock_watch.py e205f889" "finance/stock_record.py 14caf248" "finance/loss_piles.py ad0454ae")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s967_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s967"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; b="$f.bak_S967_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing else was changed. Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

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
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_check.py" "$KDIR/item_ledger.py" "$KDIR/voucher_judge.py" \
  "$KDIR/walk_s967.py" "$KDIR/walk_s965_regress.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the four files at their FROM pins; record_judges / stock_watch / stock_record / loss_piles at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice on one layout), the control red on the live files, S965's walk on the new files, the desk on a copy of the live database
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
\cp -p "$KDIR/stock_check.py" "$KDIR/stock_check.html" "$KDIR/item_ledger.py" "$KDIR/voucher_judge.py" "$SCR/new/finance/" || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s967.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 41 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s967.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s967.py" "$SCR/old/finance" "$SCR/old/marg_ingest")
echo "$W0" | grep -q "^FAIL  the one page's desk is in stock_check.py" || stop "!! [3/6] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
W5=$(py "$KDIR/walk_s965_regress.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); F5=$(echo "$W5" | grep "^FAIL" | grep -v "^FAIL  C14c the healthz says v1.5")
[ -z "$F5" ] && echo "$W5" | tail -1 | grep -q "^WALK 31/32" || { echo "$F5" | head -3 | cut -c1-200; stop "!! [3/6] S965's own walk on the new files: $(echo "$W5" | tail -1) - nothing installed"; }
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"
LS=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copy.db" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S, voucher_judge as V
c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); K=S.desk(c); t=K.get('totals') or {}
kt=[a['state'] for a in V.judge(c)['asks'] if a['item']=='KT ROS DT' and a['src']=='count']
print('LIVE-SHAPE ok=%s short=%s allow=%s way=%s old=%s moves=%s settled=%s ktros=%s' % (K.get('ok'), t.get('short'), t.get('allow'), t.get('way'), t.get('old'), t.get('moves'), t.get('settled'), ','.join(kt) or 'none'))" "$SCR/copy.db" 2>&1 | grep "^LIVE-SHAPE" | tail -1)
rm -f "$SCR/copy.db"; echo "    $LS" | cut -c1-220
case "$LS" in "LIVE-SHAPE ok=True "*) ;; *) stop "!! [3/6] the desk on a copy of the live database: ${LS:-no answer} - nothing installed";; esac
say "[3/6] the walk on made-up data: $R1, twice on one layout; the control red on the live files; S965's walk 31/32 (only its version line); the desk reads the live data (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S967_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s967"; f="$ROOT/$n"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s967" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/desk /finance/sanjeevni/ledger /finance/sanjeevni/ledger/api/fold; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "
import sys; import voucher_judge,stock_check,item_ledger
print('S967 modules ok', voucher_judge.VERSION, stock_check.VERSION, hasattr(stock_check,'desk'), getattr(item_ledger,'KIT4',''))" 2>&1 | tail -1)
case "$TK" in "S967 modules ok 1.1 1.6 True S967_STOCKCHECK_ONE_PAGE") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; LG=$(flog); bad=$(echo "$LG" | grep -iE "voucher_judge\.py|stock_check\.py|item_ledger\.py|stock_check not mounted|item_ledger not mounted" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
echo "$LG" | grep -q "S930 stock_check mounted v1.6" || restore "the service log does not show 'S930 stock_check mounted v1.6' (the doors answer 302 unsigned, so the log is the mount's proof)"
say "[4/6] four files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the four doors answer, the modules load, the log clean"
RD=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S
K=S.desk(sqlite3.connect('file:$LIVE_DB?mode=ro', uri=True)); print('S967 the desk on the live database:', K.get('ok'), K.get('totals'))" | tail -1)
case "$RD" in "S967 the desk on the live database: True "*) ;; *) restore "the desk on the live database ($(echo "$RD" | cut -c1-120))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
PLACING=0
say "[5/6] $RD"
say "[6/6] nothing written to the database by this kit (read only); the backups are $ROOT/finance/*.bak_S967_*"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s967.sh"
say ""
say "$KIT: DONE."
exit 0
