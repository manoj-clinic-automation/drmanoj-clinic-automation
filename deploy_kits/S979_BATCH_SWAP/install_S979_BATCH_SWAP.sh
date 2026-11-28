#!/bin/bash
# =============================================================================
#  install_S979_BATCH_SWAP.sh · kit S979 (28-Nov-2026, Sanjeevni session 546) · D1113, F-1752: THE BATCH SWAP (kit A of S543_BATCH_SWAP_DESIGN)
#   NEW /root/finance/batch_swap.py        : the cases (an expiring batch with no sale since the export beside a newer batch), Darpan's
#                                            shelf answer, the two STOCK bills, closed by the sale report, the pushes, the owner's section
#   /root/finance/expiry_watch.py 5db83cbc : every run finds the cases (never a push); 'Batch swaps' collapsed above Near expiry; Near
#                                            expiry marks Darpan's 'Hai'; one Needs-you line when a swap is red
#   /root/finance/stockmatch.py   91b5193f : the card's state + POST /api/swap, /api/swap/bills (the same door as every Stock milaan tap)
#   /root/finance/stockmatch.html bc67e102 : the card above Aaj ki ginti (Expiry batch -- shelf par dekhiye · Batch badlo · STOCK bill adhoora)
#   the crontab: one line # S979_BATCH_SWAP (every 10 min 08:00-21:50: judge, missed, the pushes); the live cases found at once.
#  One line:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s979kit && \cp -rp /root/deploy/repo/deploy_kits/S979_BATCH_SWAP /tmp/s979kit && bash /tmp/s979kit/install_S979_BATCH_SWAP.sh
#  (DRY=1 before bash: every gate, the walks and the proof on copies; NOTHING written.)
# =============================================================================
set -u
KIT="S979_BATCH_SWAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"; ARCHIVE="${ARCHIVE:-$ROOT/marg_ingest/archive}"
FILES=("finance/expiry_watch.py 5db83cbcd25b57fdbd52ab3077623f21" "finance/stockmatch.py 91b5193ff21848274da94ef8dcebf82c"
       "finance/stockmatch.html bc67e10238047204e90df933773d3e08")
NEWF="finance/batch_swap.py"
READS=("finance/stock_watch.py 02894900" "finance/order_rules.py 21e7cbee" "finance/sanjeevni_approvals.py b9d27f27" "finance/spine/near_expiry.py 41afc06e"
       "finance/stock_app.py 5d83a852")
WALKS=("walk_s975.py 1" "walk_s973.py 1" "walk_s971.py 0" "walk_s969.py 0" "walk_s967.py 0" "walk_s965_regress.py 0")
CRON_LINE='*/10 8-21 * * * [ -e /root/finance/_off/ALL_OFF ] || (cd /root/finance && flock -n /tmp/s979_swap.lock /root/wa/venv/bin/python3 -B batch_swap.py tick >> /root/finance/spine/batch_swap.log 2>&1) # S979_BATCH_SWAP the batch swap: judge, missed, the pushes (IST)'
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s979_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; CRON_DONE=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}" "$NEWF x"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s979"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="$SCR/none_spine.db" ORDER_PUSH_STUB="$SCR/push_stub.jsonl" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -q '# S979_BATCH_SWAP'; }
cron_out() { "$CRONTAB" -l 2>/dev/null | grep -v '# S979_BATCH_SWAP' | "$CRONTAB" -; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; b="$f.bak_S979_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; done
  [ -f "$ROOT/$NEWF" ] && mv -f "$ROOT/$NEWF" "$ROOT/$NEWF.removed_S979_$STAMP"
  [ "$CRON_DONE" = 1 ] && cron_out
  "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   batch_swap.py moved aside; the crontab line $(cron_has && echo STILL THERE || echo out); the table expiry_swap_case stays (nothing reads it)"
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
fails() { echo "$1" | grep -E "^FAIL|Traceback|Error" | cut -c1-90 | sort; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
ALL=1
for e in "${FILES[@]}" "$NEWF x"; do n="${e%% *}"; to="$(to_of "$n")"
  [ -n "$to" ] && [ "$(m5 "$KDIR/$(basename "$n")")" = "$to" ] || { say "!! [1/6] the kit's $(basename "$n") is not at its TO pin - nothing installed"; exit 1; }
  [ "$(m5 "$ROOT/$n")" = "$to" ] || ALL=0; done
cron_has || ALL=0
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the four files are at the new version and the crontab line is in."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"
  [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/6] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - changed after this kit was built. STOP, nothing installed. Tell Claude."; done
[ ! -e "$ROOT/$NEWF" ] || [ "$(m5 "$ROOT/$NEWF")" = "$(to_of "$NEWF")" ] || stop "!! [2/6] $ROOT/$NEWF exists and is not this kit's - STOP, nothing installed. Tell Claude."
for r in "${READS[@]}"; do n="${r% *}"; p="${r#* }"; [ "$(m5 "$ROOT/$n" | cut -c1-8)" = "$p" ] || stop "!! [2/6] $ROOT/$n is not at $p - STOP, nothing installed. Tell Claude."; done
"$CRONTAB" -l >/dev/null 2>&1 || stop "!! [2/6] the crontab cannot be read - nothing installed"
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/expiry_watch.py" "$KDIR/stockmatch.py" "$KDIR/batch_swap.py" \
  "$KDIR/walk_s979.py" "$KDIR/live_s979.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the three files at their FROM pins, batch_swap.py new; stock_watch / order_rules / sanjeevni_approvals / near_expiry / stock_app at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice), the control red on the live files, the earlier walks the SAME on old and new, the watch's own run on two copies
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
rm -f "$SCR/old/finance/batch_swap.py"
\cp -p "$KDIR/expiry_watch.py" "$KDIR/stockmatch.py" "$KDIR/stockmatch.html" "$KDIR/batch_swap.py" "$SCR/new/finance/" || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s979.py" "$SCR/new/finance"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 74 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s979.py" "$SCR/new/finance"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s979.py" "$SCR/old/finance")
echo "$W0" | grep -q "^FAIL  A1 batch_swap.py present" || stop "!! [3/6] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
for w in "${WALKS[@]}" "walk_s976.py K"; do wn="${w% *}"; ex="${w#* }"; for side in old new; do
    if [ "$ex" = 1 ]; then o=$(py "$KDIR/$wn" "$SCR/$side/finance" "$SCR/$side/marg_ingest" "$KDIR/walk_s971.py")
    elif [ "$ex" = K ]; then o=$(py "$REPO_KITS/S976_WHOLE_UNIT_PACK/$wn" "$SCR/$side/finance" "$SCR/$side/marg_ingest" "$REPO_KITS/S976_WHOLE_UNIT_PACK")
    else o=$(py "$KDIR/$wn" "$SCR/$side/finance" "$SCR/$side/marg_ingest"); fi
    echo "$o" | tail -1 | grep -q "^WALK " || stop "!! [3/6] $wn on the $side files did not finish ($(echo "$o" | tail -1 | cut -c1-120)) - nothing installed"
    eval "F_$side=\"\$(fails \"\$o\")\""; done
  [ "$F_old" = "$F_new" ] || { diff <(echo "$F_old") <(echo "$F_new") | head -4 | cut -c1-160; stop "!! [3/6] $wn answers differently on the new files - nothing installed"; }; done
for c in A B; do py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy$c.db" >/dev/null
  [ -s "$SCR/copy$c.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"; done
RA=$(cd "$SCR/old/finance" && FINANCE_DB="$SCR/copyA.db" ORDER_PUSH_STUB="$SCR/push_stub.jsonl" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/live_s979.py" run "$SCR/copyA.db" "$SPINE" "$ARCHIVE" "$SCR/runA.json" 2>&1 | tail -1)
RB=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copyB.db" ORDER_PUSH_STUB="$SCR/push_stub.jsonl" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -W ignore -B "$KDIR/live_s979.py" run "$SCR/copyB.db" "$SPINE" "$ARCHIVE" "$SCR/runB.json" 2>&1 | tail -1)
LS=$("$VPY" -W ignore -B "$KDIR/live_s979.py" compare "$SCR/runA.json" "$SCR/runB.json" 2>&1 | tail -1)
rm -f "$SCR"/copy?.db; echo "    old: $RA" | cut -c1-220; echo "    new: $RB" | cut -c1-260; echo "    $LS" | cut -c1-300
case "$RA $RB" in "RUN rc=0 ok=1 "*"RUN rc=0 ok=1 "*) ;; *) stop "!! [3/6] the watch's run on a copy did not finish - nothing installed";; esac
case "$LS" in "LIVE-SHAPE same_lists=True same_batches=True old_cases="*" new_cases="[0-9]*) ;; *) stop "!! [3/6] the watch's lists on a copy differ between the old and new files - nothing installed";; esac
case "$RB" in *"swaplog=batch_swap S979_BATCH_SWAP: run "*) ;; *) stop "!! [3/6] the new files' run on a copy did not reach the batch swap - nothing installed";; esac
[ -s "$SCR/push_stub.jsonl" ] && stop "!! [3/6] a run on a copy tried to push - nothing installed"
say "[3/6] the walk on made-up data: $R1, twice; the control red on the live files; seven earlier walks the same on old and new; the watch's own run on a COPY of the live database (above): every list and batch as before"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the copies green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S979_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
"$CRONTAB" -l > "$ROOT/deploy/crontab.bak_S979_$STAMP" 2>/dev/null && [ -s "$ROOT/deploy/crontab.bak_S979_$STAMP" ] || stop "!! [4/6] could not back up the crontab - nothing placed"
for e in "${FILES[@]}" "$NEWF x"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s979"; f="$ROOT/$n"; ref="$f"; [ -e "$f" ] || ref="$ROOT/finance/expiry_watch.py"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$ref" "$S" 2>/dev/null; chown --reference="$ref" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1
for e in "$NEWF x" "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s979" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockmatch/ /finance/stockmatch/api/healthz /finance/stockmatch/api/state /finance/sanjeevni/expiry /finance/stockcheck/ /finance/approvals; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B -c "
import expiry_watch,stockmatch,batch_swap
print('S979 modules ok', expiry_watch.KIT_S979, stockmatch.KIT, batch_swap.KIT, hasattr(stockmatch,'api_swap'))" 2>&1 | tail -1)
case "$TK" in "S979 modules ok S979_BATCH_SWAP S979_BATCH_SWAP S979_BATCH_SWAP True") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; LG=$(flog); bad=$(echo "$LG" | grep -iE "expiry_watch\.py|stockmatch\.py|batch_swap\.py|not mounted" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
say "[4/6] four files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors answer, the modules load, the log clean"
{ "$CRONTAB" -l 2>/dev/null; echo "$CRON_LINE"; } | "$CRONTAB" - && CRON_DONE=1 && cron_has || restore "the crontab line"
AP=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B batch_swap.py find --db "$LIVE_DB" --spine "$SPINE" 2>&1 | tail -1)
case "$AP" in "{"*'"new":'*) ;; *) restore "the first find on the live database ($(echo "$AP" | cut -c1-160))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
RD=$(cd "$ROOT/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/live_s979.py" read "$LIVE_DB" 2>&1 | tail -1)
case "$RD" in "READ ok=True "*) ;; *) restore "the live read ($(echo "$RD" | cut -c1-140))";; esac
PLACING=0
say "[5/6] the crontab line in (# S979_BATCH_SWAP); the first find: $AP" | cut -c1-300
say "      $RD" | cut -c1-400
say "[6/6] Backups: $ROOT/finance/*.bak_S979_*  ·  $ROOT/deploy/crontab.bak_S979_$STAMP"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s979.sh"
say ""
say "$KIT: DONE."
exit 0
