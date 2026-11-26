#!/bin/bash
# =============================================================================
#  install_S965_VOUCHER_JUDGE.sh · kit S965 (26-Nov-2026, Sanjeevni session 532) · his "Ok" 20:30 IST on mock-up v5 (D1083, D1086)
#   NEW  /root/finance/voucher_judge.py : Marg's Stock Issue / Stock Receive lines (S963) judged against every correction asked of Amir.
#   /root/finance/stock_check.py  26665c78 -> v1.5 : /api/vouchers.   /root/finance/stock_check.html 13e348a9 : the two boxes, the tags.
#   /root/finance/item_ledger.py  d2f68ee9 : Marg's own voucher lines, judged, each voucher's lines folded under its row.
#   /root/marg_ingest/marg_vouchers.py 92318068 : F-1701 -- a retried text keeps its export's own stamp.
#   Data: mi_voucher_name (AD00010's two lines named from his Marg screen); the kept sheets restamped by their export.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s965kit && cp -rp /root/deploy/repo/deploy_kits/S965_VOUCHER_JUDGE /tmp/s965kit && bash /tmp/s965kit/install_S965_VOUCHER_JUDGE.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S965_VOUCHER_JUDGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; MLOCK="${MLOCK:-/tmp/marg_ingest.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/stock_check.py 26665c78e59ecf4872a21eedbda7b531" "finance/stock_check.html 13e348a97a25c51fdff8ef9ddc5122a5"
       "finance/item_ledger.py d2f68ee900dfbcb40a25f570f6782c58" "marg_ingest/marg_vouchers.py 923180680678a0480c1b2d1a1300830a"
       "finance/voucher_judge.py NEW")
READS=("finance/marg_billwatch.py 9edda626" "finance/marg_hand_change.py 8f3c268a")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s965_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; HELD_M=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
take_m() { exec 9>>"$MLOCK" && flock -w "${MWAIT:-120}" 9 && HELD_M=1; }
free_m() { [ "$HELD_M" = 1 ] || return 0; flock -u 9; exec 9>&-; HELD_M=0; }
release_lock() { free_m; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s965"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  [ "$HELD_M" = 1 ] || take_m || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"
    if [ "$fr" = NEW ]; then [ -f "$f" ] && mv -f "$f" "$f.bak_S965_removed"; else b="$f.bak_S965_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; fi; done
  free_m; "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $( [ -f "$ROOT/$n" ] && m5 "$ROOT/$n" | cut -c1-8 || echo absent) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). The name table, if made, stays (nothing reads it). Send a photo of this screen to Claude."
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
  if [ "$fr" = NEW ]; then [ ! -e "$ROOT/$n" ] || stop "!! [2/6] $ROOT/$n already exists - STOP, nothing installed. Tell Claude."
  else [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - changed after this kit was built. STOP, nothing installed. Tell Claude."; fi; done
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/6] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_check.py" "$KDIR/item_ledger.py" "$KDIR/voucher_judge.py" \
  "$KDIR/marg_vouchers.py" "$KDIR/walk_s965.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the four files at their FROM pins, voucher_judge.py new; marg_billwatch / marg_hand_change at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice on one layout), the control red on the live files, the judge on a copy of the live database (counts only)
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -p "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null; done
\cp -p "$KDIR/stock_check.py" "$KDIR/stock_check.html" "$KDIR/item_ledger.py" "$KDIR/voucher_judge.py" "$SCR/new/finance/" && \cp -p "$KDIR/marg_vouchers.py" "$SCR/new/marg_ingest/" \
  || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s965.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 32 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s965.py" "$SCR/new/finance" "$SCR/new/marg_ingest"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s965.py" "$SCR/old/finance" "$SCR/old/marg_ingest"); R0=$(echo "$W0" | tail -1)
echo "$W0" | grep -q "^FAIL  the judge is beside the finance files" || stop "!! [3/6] the control on the live files did not go red ($R0) - nothing installed"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"
LS=$(cd "$SCR/new/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import sqlite3,sys; sys.path.insert(0,'.'); import voucher_judge as V
c=sqlite3.connect(sys.argv[1]); V.ensure_names(c); P=V.page(c); t=P.get('totals') or {}
print('LIVE-SHAPE ok=%s vouchers=%s lines=%s asks=%s chips=%s cut=%d named=%d' % (P.get('ok'), t.get('vouchers'), t.get('lines'), t.get('asks'), P.get('chips'), len(P.get('cut') or []), len(P.get('named') or [])))" "$SCR/copy.db" 2>&1 | tail -1)
rm -f "$SCR/copy.db"; echo "    $LS" | cut -c1-220
case "$LS" in "LIVE-SHAPE ok=True "*) ;; *) stop "!! [3/6] the judge on a copy of the live database: $LS - nothing installed";; esac
say "[3/6] the walk on made-up data: $R1, twice on one layout; the control red on the live files; the judge reads the live data (above)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; [ "$fr" = NEW ] && continue; b="$ROOT/$n.bak_S965_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s965"; f="$ROOT/$n"; ref="$f"; [ -f "$ref" ] || ref="$ROOT/finance/stock_check.py"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$ref" "$S" 2>/dev/null; chown --reference="$ref" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
take_m || stop "!! [4/6] the Marg collection holds its lock beyond ${MWAIT:-120} s - nothing placed. Run it again in five minutes."
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s965" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
free_m
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/vouchers /finance/sanjeevni/ledger; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "
import sys; sys.path.insert(0,'$ROOT/marg_ingest'); import voucher_judge,stock_check,item_ledger,marg_vouchers
print('S965 modules ok', voucher_judge.KIT, stock_check.VERSION, hasattr(item_ledger,'_s965_vouchers'), hasattr(marg_vouchers,'export_stamp'))" 2>&1 | tail -1)
case "$TK" in "S965 modules ok S965_VOUCHER_JUDGE 1.5 True True") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "voucher_judge\.py|stock_check\.py|item_ledger\.py|marg_vouchers\.py|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
say "[4/6] five files placed and read back (marg_vouchers under the Marg collection's lock); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the three doors answer, the modules load, the log clean"
DT=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'$ROOT/marg_ingest'); import voucher_judge as V, marg_vouchers as MV
c=sqlite3.connect('$LIVE_DB', timeout=30); V.ensure_names(c); n=MV.restamp(c); c.commit()
print('S965 data: names %d, sheets restamped %d' % (c.execute('SELECT COUNT(*) FROM mi_voucher_name').fetchone()[0], n))" | tail -1)
case "$DT" in "S965 data: "*) ;; *) restore "the name table ($(echo "$DT" | cut -c1-120))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
PLACING=0
say "[5/6] $DT"
RD=$(fin -c "
import sqlite3,sys; sys.path.insert(0,'.'); import voucher_judge as V
P=V.page(sqlite3.connect('file:$LIVE_DB?mode=ro', uri=True)); print('S965 now:', P.get('ok'), P.get('chips'))" | tail -1)
say "[6/6] $RD"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s965.sh"
say ""
say "$KIT: DONE."
exit 0
