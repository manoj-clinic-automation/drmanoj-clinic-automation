#!/bin/bash
# =============================================================================
#  install_S969_STOCKCHECK_DESK_WRITES.sh · kit S969 (27-Nov-2026, Sanjeevni session 536) · kit A2 of S534_FINAL_BUILD_PLAN
#  His "ok" 09:25 IST 27-Nov on mock-up v9 (D1090, D1092) and his "build" 12:10 IST 27-Nov: THE DESK'S WRITES -- his two taps, no dialog.
#   /root/finance/stock_check.py   5f1b239e -> v1.7 : POST /api/desk/act -- Write off . Pursue . the allowance group . old counts onto
#                                                     Darpan's next list (F-1712); its own table stock_desk_action (made by this installer).
#   /root/finance/stock_check.html a9f7b682 : the buttons on the rows (two taps: the first arms, the second does it).
#   /root/finance/stock_watch.py   e205f889 -> v1.15 : every morning list reaches Darpan's phone (F-1712; setting count.push_every_list).
#   /root/finance/voucher_judge.py aea43633 -> v1.2 : a desk Write off's units from the desk's own row.
#   /root/finance/amir_day.py      1cf0f13f : the day's write-offs as ONE card on Amir's page, one 'Kar diya' for the card.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s969kit && cp -rp /root/deploy/repo/deploy_kits/S969_STOCKCHECK_DESK_WRITES /tmp/s969kit && bash /tmp/s969kit/install_S969_STOCKCHECK_DESK_WRITES.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S969_STOCKCHECK_DESK_WRITES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/stock_check.py 5f1b239e6af3c931cc15adb17fd2edb2" "finance/stock_check.html a9f7b6827e590cd63a3e2cc053334d0c"
       "finance/stock_watch.py e205f889b456f4c6c61b07389073943e" "finance/voucher_judge.py aea436338fc138b1ff1e27b552b328bc"
       "finance/amir_day.py 1cf0f13f70cb7bafb4c34359c7b54285")
READS=("finance/record_judges.py 85c0d3e3" "finance/stock_record.py 14caf248" "finance/loss_piles.py ad0454ae" "finance/item_ledger.py 6735167f"
       "finance/order_rules.py 21e7cbee" "finance/qty_words.py 706db7cc")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s969_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s969"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; b="$f.bak_S969_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing else was changed (an empty stock_desk_action table may stay; nothing reads it then). Send a photo of this screen to Claude."
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
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the five files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"
  [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - changed after this kit was built. STOP, nothing installed. Tell Claude."; done
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/6] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_check.py" "$KDIR/stock_watch.py" "$KDIR/voucher_judge.py" "$KDIR/amir_day.py" \
  "$KDIR/walk_s969.py" "$KDIR/walk_s967.py" "$KDIR/walk_s965_regress.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the five files at their FROM pins; record_judges / stock_record / loss_piles / item_ledger / order_rules / qty_words at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice on one layout), the control red on the live files, S967's and S965's walks on the new files, the desk on a copy
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
\cp -p "$KDIR/stock_check.py" "$KDIR/stock_check.html" "$KDIR/stock_watch.py" "$KDIR/voucher_judge.py" "$KDIR/amir_day.py" "$SCR/new/finance/" || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s969.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 49 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s969.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s969.py" "$SCR/old/finance" "$SCR/old/marg_ingest")
echo "$W0" | grep -q "^FAIL  the desk's writes are in stock_check.py" || stop "!! [3/6] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
W7=$(py "$KDIR/walk_s967.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); F7=$(echo "$W7" | grep "^FAIL" | grep -v "^FAIL  W4 the healthz says v1.6")
[ -z "$F7" ] && echo "$W7" | tail -1 | grep -q "^WALK 40/41" || { echo "$F7" | head -3 | cut -c1-200; stop "!! [3/6] S967's own walk on the new files: $(echo "$W7" | tail -1) - nothing installed"; }
W5=$(py "$KDIR/walk_s965_regress.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); F5=$(echo "$W5" | grep "^FAIL" | grep -v "^FAIL  C14c the healthz says v1.5")
[ -z "$F5" ] && echo "$W5" | tail -1 | grep -q "^WALK 31/32" || { echo "$F5" | head -3 | cut -c1-200; stop "!! [3/6] S965's own walk on the new files: $(echo "$W5" | tail -1) - nothing installed"; }
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"
LS=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copy.db" SHARED_LIB_DIR="$ROOT/shared" ORDER_PUSH_STUB="$SCR/push.jsonl" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S, voucher_judge as V
c=sqlite3.connect(sys.argv[1]); K=S.desk(c); t=K.get('totals') or {}
wo=[r for r in K.get('box1') or [] if 'wo' in (r.get('acts') or [])][:1]; w='none'
if wo:
    m,_s=S._write_off(c, wo, 'install-check', 'short'); a=[x for x in V.judge(c)['asks'] if str(x.get('ref','')).startswith('S969:wo:') and x['item']==wo[0]['item']]
    w='%s:%s=%s' % (wo[0]['item'], wo[0]['short'], a[0]['units'] if a else 'unread')
print('LIVE-SHAPE ok=%s short=%s allow=%s way=%s old=%s moves=%s recount=%s writeoff_on_the_copy=%s' % (K.get('ok'), t.get('short'), t.get('allow'), t.get('way'), t.get('old'), t.get('moves'), t.get('recount'), w))" "$SCR/copy.db" 2>&1 | grep "^LIVE-SHAPE" | tail -1)
rm -f "$SCR/copy.db"; echo "    $LS" | cut -c1-220
case "$LS" in "LIVE-SHAPE ok=True "*) ;; *) stop "!! [3/6] the desk on a copy of the live database: ${LS:-no answer} - nothing installed";; esac
case "$LS" in *"writeoff_on_the_copy=none"*) ;; *"writeoff_on_the_copy="*":"*"=unread"*) stop "!! [3/6] a write-off on the copy was not read by the voucher judge - nothing installed";; esac
say "[3/6] the walk on made-up data: $R1, twice on one layout; the control red on the live files; S967's walk 40/41 and S965's 31/32 (only their version lines); the desk and one write-off on a COPY of the live database (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S969_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s969"; f="$ROOT/$n"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s969" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/desk /finance/amir /finance/stockmatch; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "
import sys; import voucher_judge,stock_check,stock_watch,amir_day
print('S969 modules ok', voucher_judge.VERSION, stock_check.VERSION, hasattr(stock_check,'r_desk_act'), stock_watch.VERSION, hasattr(amir_day,'S969_WO'))" 2>&1 | tail -1)
case "$TK" in "S969 modules ok 1.2 1.7 True 1.15 True") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; LG=$(flog); bad=$(echo "$LG" | grep -iE "voucher_judge\.py|stock_check\.py|stock_watch\.py|amir_day\.py|stock_check not mounted|S969 stock_desk_action not made" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
echo "$LG" | grep -q "S930 stock_check mounted v1.7" || restore "the service log does not show 'S930 stock_check mounted v1.7' (the doors answer 302 unsigned, so the log is the mount's proof)"
say "[4/6] five files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors answer, the modules load, the log clean"
MK=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S
c=sqlite3.connect('$LIVE_DB', timeout=30); S._ensure_desk(c); c.commit(); print('S969 table ok')" | tail -1)
[ "$MK" = "S969 table ok" ] || restore "the table stock_desk_action could not be made ($(echo "$MK" | cut -c1-120))"
RD=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S
c=sqlite3.connect('file:$LIVE_DB?mode=ro', uri=True); K=S.desk(c)
tb=c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='stock_desk_action'\").fetchone()[0]
print('S969 the desk on the live database:', K.get('ok'), K.get('totals'), 'stock_desk_action', 'made' if tb else 'MISSING')" | tail -1)
case "$RD" in "S969 the desk on the live database: True "*"stock_desk_action made") ;; *) restore "the desk on the live database ($(echo "$RD" | cut -c1-140))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
PLACING=0
say "[5/6] $RD"
say "[6/6] the database: only the empty table stock_desk_action (made by this installer); nothing is written until your tap. Backups: $ROOT/finance/*.bak_S969_*"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s969.sh"
say ""
say "$KIT: DONE."
exit 0
