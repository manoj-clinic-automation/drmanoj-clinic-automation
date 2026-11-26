#!/bin/bash
# =============================================================================
#  install_S957_COUNT_LEFTOVERS.sh · kit S957 (26-Nov-2026, Sanjeevni session 522) · after S952 / S954 / S956 (CONFIRMED by the 26-Nov bundle)
#   /root/finance/record_judges.py 5c5cca26 -> v1.2 : an item the owner settled for the 06-Sep count (NORTIMER TAB, 12-Oct) is never "Marg still
#        holds the older loss"; a voided voucher writes nothing off. Then every count since 18-11 judged again (NORTIMER's 23-11 count moves).
#   /root/finance/stock_figure.py df35fc93 -> v1.8 : S956's same-day rule names its bills (s956_after_bills); the shelf figure unchanged.
#   Amir's card: one tap job -- KT ROS DT STOCK ISSUE 7:11 (Darpan's 23-11 count against Marg), his word 26-Nov 09:31.
#   /root/finance/stock_watch.py  401684ea -> v1.13: the recount match keeps a bill dated a morning count's day that came after it (the S956 review).
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s957kit && cp -rp /root/deploy/repo/deploy_kits/S957_COUNT_LEFTOVERS /tmp/s957kit && bash /tmp/s957kit/install_S957_COUNT_LEFTOVERS.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S957_COUNT_LEFTOVERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("record_judges.py 5c5cca265812183968c3509e40ffd2a8" "stock_figure.py df35fc932fe936e3543edd3ae47e0d53" "stock_watch.py 401684eaafc35f10d622046db856246c")
READS=("finance/porders.py daf6f92b" "finance/stock_check.py 686845f8" "finance/stock_record.py 14caf248")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s957_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; DATA=""; AMIR=0
ATF="$ROOT/finance/.s957_rejudged_at"; RJ="$ROOT/finance/record_judges.py"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do rm -f "$ROOT/finance/.${e%% *}.s957"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  if [ "$AMIR" = 1 ]; then say "   Amir's card: $(fin "$KDIR/amir_s957.py" remove | tail -1)"; fi
  if [ -n "$DATA" ]; then say "   the judgments first: $(fin "$RJ" --undo-rejudge-from "$DATA" | tail -1)"; fi
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/finance/$n.bak_S957_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$ROOT/finance/$n"; done
  rm -f "$ATF"; "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   finance/$n $(m5 "$ROOT/finance/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
ALL=1; NONE=1
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; to="$(to_of "$n")"
  [ -n "$to" ] && [ "$(m5 "$KDIR/$n")" = "$to" ] || { say "!! [1/5] the kit's $n is not at its TO pin - nothing installed"; exit 1; }
  c="$(m5 "$ROOT/finance/$n")"; [ "$c" = "$to" ] || ALL=0; [ "$c" = "$to" ] && NONE=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the three files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; [ "$(m5 "$ROOT/finance/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/finance/$n is $(m5 "$ROOT/finance/$n" | cut -c1-8), expected ${fr:0:8} - STOP, nothing installed. Tell Claude."; done
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/5] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/record_judges.py" "$KDIR/stock_figure.py" "$KDIR/stock_watch.py" "$KDIR/walk_s957.py" "$KDIR/amir_s957.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
say "[2/5] the three files at their FROM pins (S954 / S956 / S952 as installed); porders, stock_check, stock_record at their pins; the kit compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
mkdir -p "$SCR/new/spine" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"; \cp -p "$KDIR/record_judges.py" "$KDIR/stock_figure.py" "$KDIR/stock_watch.py" "$SCR/new/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/5] could not take a copy of the database for the walk - nothing installed"
\cp -p "$SCR/copy.db" "$SCR/copy0.db"
W1=$(py "$KDIR/walk_s957.py" "$SCR/new" "$SCR/copy.db" "$SCR/old"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk on a copy: $R1 - nothing installed"; }
W2=$(py "$KDIR/walk_s957.py" "$SCR/new" "$SCR/copy.db" "$SCR/old"); R2=$(echo "$W2" | tail -1)
[ "$R2" = "RESULT: ALL PASS" ] || { echo "$W2" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk a second time on the same copy: $R2 - nothing installed"; }
W0=$(py "$KDIR/walk_s957.py" "$SCR/old" "$SCR/copy0.db" "$SCR/old" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/5] the control did not go red ($R0) - nothing installed";; esac
for w in "FAIL  NORTIMER TAB: settled" "FAIL  a voided voucher wrote nothing off" "FAIL  JAKMAC 5 short by 200"; do   # the review (SHOULD 1): red by the rules, not the version alone
  echo "$W0" | grep -q "^$w" || stop "!! [3/5] the control did not go red on: ${w#FAIL  } - nothing installed"; done
rm -f "$SCR/copy.db" "$SCR/copy0.db"
say "[3/5] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass, twice on one copy; the control goes red as it must ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/finance/$n.bak_S957_${fr:0:8}"
  { \cp -p "$ROOT/finance/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/finance/.$n.s957"; f="$ROOT/finance/$n"
  { cat "$KDIR/$n" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/finance/.$n.s957" "$ROOT/finance/$n" || restore "the rename of $n"; [ "$(m5 "$ROOT/finance/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/stockcheck/); case "$d1" in 404|000|5*) restore "his Stock check page answers $d1";; esac
d2=$(door /finance/stockcheck/api/rows); case "$d2" in 404|000|5*) restore "the Stock check rows answer $d2";; esac
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "import stock_watch,stock_figure,record_judges; print('S957 module ok', record_judges.VERSION, record_judges.KIT, stock_figure.VERSION, stock_watch.VERSION)" 2>&1 | tail -1)
case "$TK" in "S957 module ok 1.2 S957_COUNT_LEFTOVERS 1.8 1.13") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "record_judges\.py|stock_watch\.py|stock_figure\.py|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
DATA="$(TZ=Asia/Kolkata date -d '-2 seconds' '+%Y-%m-%dT%H:%M:%S')"; echo "$DATA" > "$ATF"   # the moment BEFORE the judge-again: its undo reaches every row it writes
ONE=$(fin "$RJ" --rejudge | tail -1)
case "$ONE" in "S954 rejudge at "*) ;; *) restore "the judge-again did not finish ($(echo "$ONE" | cut -c1-120))";; esac
AMIR=1; AJ=$(fin "$KDIR/amir_s957.py" add | tail -1)        # his word 26-Nov 09:31: KT ROS DT's issue on Amir's card
case "$AJ" in "S957 Amir: "*) ;; *) restore "Amir's card ($(echo "$AJ" | cut -c1-120))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/5]"
PLACING=0
say "[4/5] three files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, Stock check $d1 / rows $d2, the modules load, the log clean"
say "[5/5] $ONE · $AJ"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s957.sh"
say ""
say "$KIT: DONE."
exit 0
