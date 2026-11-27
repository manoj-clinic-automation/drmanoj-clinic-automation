#!/bin/bash
# =============================================================================
#  install_S971_AMIR_BY_HIMSELF.sh · kit S971 (27-Nov-2026, Sanjeevni session 538) · kit B of S534_FINAL_BUILD_PLAN (D1090, D1091)
#  His "proceed" 15:10 IST 27-Nov; his word 17:17 IST (the loss register). AMIR BY HIMSELF:
#   /root/finance/voucher_inquiry.py  NEW     : the claim cards, the export line, the inquiry of a voucher nobody asked for, his taps, the loss register
#   /root/finance/stock_losses.html   NEW     : the loss register page (/finance/stockcheck/losses), his only
#   /root/finance/stock_check.py      5a8bde22 -> v1.8 : box 2 claims + the export line, box 4 the inquiry, Withdraw, the settings, the loss register doors
#   /root/finance/stock_check.html    ac3de342 : the rows and buttons above; F-1725 (the intro line)
#   /root/finance/voucher_judge.py    768adaa9 -> v1.3 : a reversal's units from its own row; a withdrawn job asks nothing; keyed-before-the-ask; his cancel window
#   /root/finance/amir_day.py         6212fbf0 : the voucher questions (one tap), the reversal card; the sync before his page; the Hub's lines
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s971kit && cp -rp /root/deploy/repo/deploy_kits/S971_AMIR_BY_HIMSELF /tmp/s971kit && bash /tmp/s971kit/install_S971_AMIR_BY_HIMSELF.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S971_AMIR_BY_HIMSELF"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/stock_check.py 5a8bde2284172cb3f77df40e87f52d62" "finance/stock_check.html ac3de34295801051fd2d481295294d35"
       "finance/voucher_judge.py 768adaa9c08c4398ae95a035841ec373" "finance/amir_day.py 6212fbf092c9d4afb6a7efba10a992a2"
       "finance/voucher_inquiry.py NEW" "finance/stock_losses.html NEW")
READS=("finance/stock_watch.py fe0a89cd" "finance/record_judges.py 85c0d3e3" "finance/stock_record.py 14caf248" "finance/loss_piles.py ad0454ae"
       "finance/item_ledger.py 6735167f" "finance/order_rules.py 21e7cbee" "finance/qty_words.py 706db7cc")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s971_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s971"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
    if [ "$fr" = NEW ]; then [ -f "$f" ] && mv -f "$f" "$f.bak_S971_removed_$STAMP"; else b="$f.bak_S971_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; fi; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $( [ -f "$ROOT/$n" ] && m5 "$ROOT/$n" | cut -c1-8 || echo absent) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Nothing else was changed (S971's empty tables may stay; nothing reads them then). Send a photo of this screen to Claude."
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
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the six files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"
  if [ "$fr" = NEW ]; then [ ! -e "$ROOT/$n" ] || stop "!! [2/6] $ROOT/$n already exists ($(m5 "$ROOT/$n" | cut -c1-8)) - not this kit's; STOP, nothing installed. Tell Claude."
  else [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - changed after this kit was built. STOP, nothing installed. Tell Claude."; fi; done
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/6] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_check.py" "$KDIR/voucher_judge.py" "$KDIR/amir_day.py" "$KDIR/voucher_inquiry.py" \
  "$KDIR/walk_s971.py" "$KDIR/walk_s969.py" "$KDIR/walk_s967.py" "$KDIR/walk_s965_regress.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the four files at their FROM pins, the two new ones absent; stock_watch / record_judges / stock_record / loss_piles / item_ledger / order_rules / qty_words at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice on one layout), the control red on the live files, S969's / S967's / S965's walks on the new files, a copy of the database
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
\cp -p "$KDIR/stock_check.py" "$KDIR/stock_check.html" "$KDIR/voucher_judge.py" "$KDIR/amir_day.py" "$KDIR/voucher_inquiry.py" "$KDIR/stock_losses.html" "$SCR/new/finance/" \
  || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s971.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 85 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s971.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s971.py" "$SCR/old/finance" "$SCR/old/marg_ingest")
echo "$W0" | grep -q "^FAIL  kit B (voucher_inquiry.py) is in place" || stop "!! [3/6] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
W9=$(py "$KDIR/walk_s969.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); F9=$(echo "$W9" | grep "^FAIL" | grep -v "^FAIL  R3 healthz v1.7 with writes")
[ -z "$F9" ] && echo "$W9" | tail -1 | grep -q "^WALK 48/49" || { echo "$F9" | head -3 | cut -c1-200; stop "!! [3/6] S969's own walk on the new files: $(echo "$W9" | tail -1) - nothing installed"; }
W7=$(py "$KDIR/walk_s967.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); F7=$(echo "$W7" | grep "^FAIL" | grep -v "^FAIL  W4 the healthz says v1.6" | grep -v "^FAIL  D13 the rules panel")
[ -z "$F7" ] && echo "$W7" | tail -1 | grep -q "^WALK 39/41" || { echo "$F7" | head -3 | cut -c1-200; stop "!! [3/6] S967's own walk on the new files: $(echo "$W7" | tail -1) - nothing installed"; }
W5=$(py "$KDIR/walk_s965_regress.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); F5=$(echo "$W5" | grep "^FAIL" | grep -v "^FAIL  C14c the healthz says v1.5")
[ -z "$F5" ] && echo "$W5" | tail -1 | grep -q "^WALK 31/32" || { echo "$F5" | head -3 | cut -c1-200; stop "!! [3/6] S965's own walk on the new files: $(echo "$W5" | tail -1) - nothing installed"; }
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"
LS=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copy.db" SHARED_LIB_DIR="$ROOT/shared" ORDER_PUSH_STUB="$SCR/push.jsonl" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import sqlite3,sys,datetime as dt; sys.path.insert(0,'.'); import stock_check as S, voucher_inquiry as VI
c=sqlite3.connect(sys.argv[1]); n0=c.total_changes; K=S.desk(c); ro=(c.total_changes==n0); t=K.get('totals') or {}
VI.ensure(c); S._ensure_desk(c); c.commit(); nb=VI.backfill_values(c, 'at install')
today=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date().isoformat()
c.execute(\"INSERT INTO setting (key,value) VALUES ('stock.claim_from',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value\", (today,)); c.commit()
o=VI.sync(c); L=VI.losses(c)
print('LIVE-SHAPE ok=%s readonly=%s short=%s way=%s moves=%s claims_today=%s questions=%s priced=%s loss_months=%s runs=%s' % (K.get('ok'), ro, t.get('short'), t.get('way'), t.get('moves'), o.get('claims'), o.get('questions'), nb, len(L['months']), len(L['runs'])))" "$SCR/copy.db" 2>&1 | grep "^LIVE-SHAPE" | tail -1)
rm -f "$SCR/copy.db"; echo "    $LS" | cut -c1-240
case "$LS" in "LIVE-SHAPE ok=True readonly=True "*" questions=0 "*) ;; *) stop "!! [3/6] kit B on a copy of the live database: ${LS:-no answer} - nothing installed";; esac
say "[3/6] the walk on made-up data: $R1, twice on one layout; the control red on the live files; S969's 48/49, S967's 39/41, S965's 31/32 (only their version lines and S967's rules panel, now editable); kit B on a COPY of the live database (above): nothing old reaches Amir"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; [ "$fr" = NEW ] && continue; b="$ROOT/$n.bak_S971_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
REF="$ROOT/finance/stock_check.py"
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s971"; f="$ROOT/$n"; [ -f "$f" ] || f="$REF"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s971" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/desk /finance/stockcheck/losses /finance/stockcheck/api/losses /finance/amir /finance/approvals; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "
import sys; import voucher_judge,stock_check,amir_day,voucher_inquiry
print('S971 modules ok', voucher_judge.VERSION, stock_check.VERSION, voucher_inquiry.VERSION, hasattr(amir_day,'KIT_S971'), hasattr(stock_check,'r_losses'))" 2>&1 | tail -1)
case "$TK" in "S971 modules ok 1.3 1.8 1.0 True True") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; LG=$(flog); bad=$(echo "$LG" | grep -iE "voucher_judge\.py|stock_check\.py|amir_day\.py|voucher_inquiry\.py|stock_check not mounted" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
echo "$LG" | grep -q "S930 stock_check mounted v1.8" || restore "the service log does not show 'S930 stock_check mounted v1.8' (the doors answer 302 unsigned, so the log is the mount's proof)"
say "[4/6] six files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors answer, the modules load, the log clean"
MK=$(fin -c "
import sqlite3,sys,datetime as dt; sys.path.insert(0,'.'); import stock_check as S, voucher_inquiry as VI
c=sqlite3.connect('$LIVE_DB', timeout=30); VI.ensure(c); S._ensure_desk(c); c.commit()
d=dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date()
nb=VI.backfill_values(c, 'at install %s' % d.strftime('%d-%m'))
c.execute(\"INSERT OR IGNORE INTO setting (key,value,note) VALUES ('stock.claim_from',?,'S971: the install day -- nothing older reaches Amir')\", (d.isoformat(),)); c.commit()
print('S971 tables ok, write-offs priced at install:', nb, 'claim date', VI.setting(c,'stock.claim_from'), 'rule date', VI.setting(c,'stock.voucher_rule_from') or 'not set')" | tail -1)
case "$MK" in "S971 tables ok"*) ;; *) restore "the tables could not be made ($(echo "$MK" | cut -c1-120))";; esac
RD=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import stock_check as S, voucher_inquiry as VI
c=sqlite3.connect('file:$LIVE_DB?mode=ro', uri=True); K=S.desk(c); L=VI.losses(c)
print('S971 the desk on the live database:', K.get('ok'), 'claims', K['totals'].get('claims'), 'inquiry', K['totals'].get('inq_open'), 'export', bool(K.get('exportask')), '| loss register months', len(L['months']), 'lines', sum(len(m['lines']) for m in L['months']))" | tail -1)
case "$RD" in "S971 the desk on the live database: True "*) ;; *) restore "the desk on the live database ($(echo "$RD" | cut -c1-140))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
PLACING=0
say "[5/6] $MK"
say "[6/6] $RD"
say "    Backups: $ROOT/finance/*.bak_S971_*  ·  The rule date stays yours: set it on the Stock check page the day you tell Amir."
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s971.sh"
say ""
say "$KIT: DONE."
exit 0
