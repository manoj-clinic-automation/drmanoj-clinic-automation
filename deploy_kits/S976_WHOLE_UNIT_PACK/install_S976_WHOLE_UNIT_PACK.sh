#!/bin/bash
# =============================================================================
#  install_S976_WHOLE_UNIT_PACK.sh · kit S976 (28-Nov-2026, Sanjeevni session 543) · F-1742: a whole-unit item (CCM = bottle) counted whole
#   /root/finance/stock_figure.py   0d8cab56 : a whole-unit item's pack is 1 (the stock record, shelf_figure, Stock check)
#   /root/finance/stock_watch.py    fe0a89cd : Darpan's count screen -- one Botal box for it, like a gel's Tube; the morning list put right
#   /root/finance/stockmatch.py     1f5a15ba : one line -- Stock batao / Kuchh gadbad hai search reads the same pack
#   /root/finance/voucher_judge.py  59a68bb1 : Marg's voucher line in the bottles Marg printed (3, not 120); S975's 'look' retired at pack 1
#   /root/finance/stock_check.py    6b8d077c : band 2 tells such a count in its bottles at pack 1 (D1107), never a bare "1"
#  THE DATA: the one count stored with a pack per bottle (CCM 28-11: 40 -> 1 bottle) put right by fix_s976.py, every row's before-image in
#  s976_fix (the undo puts it back); the stock record rebuilt; that count judged again (record_judges, its own undo rows). One line:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s976kit && \cp -rp /root/deploy/repo/deploy_kits/S976_WHOLE_UNIT_PACK /tmp/s976kit && bash /tmp/s976kit/install_S976_WHOLE_UNIT_PACK.sh
#  (DRY=1 before bash: every gate, the walks and the proof on copies; NOTHING written.)
# =============================================================================
set -u
KIT="S976_WHOLE_UNIT_PACK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; RLOCK="${RLOCK:-/tmp/stock_record.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE="${SPINE:-$ROOT/finance/spine/spine.db}"
FILES=("finance/stock_figure.py 0d8cab560d19783febf134058f447763" "finance/stock_watch.py fe0a89cd0206b19ccf5439c9f364fb5e"
       "finance/stockmatch.py 1f5a15bade4f6e002e61b883eadcaee0" "finance/voucher_judge.py 59a68bb15c24261f533a48a33457fccb"
       "finance/stock_check.py 6b8d077cd2e30b18dd02e42551a2d83f")
READS=("finance/qty_words.py 706db7cc" "finance/stock_record.py 14caf248" "finance/record_judges.py 85c0d3e3" "finance/loss_piles.py ad0454ae"
       "finance/item_ledger.py 4a485ccd" "marg_ingest/marg_vouchers.py 0f9b2f0a")
WALKS=("walk_s975.py 1" "walk_s973.py 1" "walk_s971.py 0" "walk_s969.py 0" "walk_s967.py 0" "walk_s965_regress.py 0")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s976_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; APPLIED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(basename "$n").s976"; done; release_lock; rm -rf "${SCR:?}"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="$SCR/none_spine.db" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
inf() { local d="$1"; shift; (cd "$d" && FINANCE_DB="$LIVE_DB" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; f="$ROOT/$n"; b="$f.bak_S976_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$f"; done
  if [ "$APPLIED" = 1 ]; then say "   the data: $(inf "$ROOT/finance" "$KDIR/fix_s976.py" "$LIVE_DB" --undo | tail -1)"
    say "   the record: $(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" flock -w 120 "$RLOCK" timeout 900 "$VPY" -W ignore -B -c "import sqlite3,stock_record as SR; c=sqlite3.connect('$LIVE_DB',timeout=30); print('rebuilt', SR.build(c).get('ok'))" 2>&1 | tail -1)"; fi
  "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
fails() { echo "$1" | grep -E "^FAIL|Traceback|Error" | cut -c1-90 | sort; }

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
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_figure.py" "$KDIR/stock_watch.py" "$KDIR/stockmatch.py" "$KDIR/voucher_judge.py" "$KDIR/stock_check.py" \
  "$KDIR/fix_s976.py" "$KDIR/live_s976.py" "$KDIR/walk_s976.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the five files at their FROM pins; qty_words / stock_record / record_judges / loss_piles / item_ledger / marg_vouchers at their pins; the kit compiles on both pythons"
# [3/6] the walk on made-up data (twice), the control red on the live files, six earlier walks the SAME on old and new, the proof on two copies
for side in new old; do mkdir -p "$SCR/$side/finance/spine" "$SCR/$side/marg_ingest"
  \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.json "$SCR/$side/finance/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/$side/finance/" 2>/dev/null
  \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/$side/finance/spine/" 2>/dev/null; \cp -rp "$ROOT"/marg_ingest/*.py "$SCR/$side/marg_ingest/" 2>/dev/null
  [ -d "$ROOT/marg_ingest/xlrd" ] && \cp -rp "$ROOT/marg_ingest/xlrd" "$SCR/$side/marg_ingest/"; done
\cp -p "$KDIR/stock_figure.py" "$KDIR/stock_watch.py" "$KDIR/stockmatch.py" "$KDIR/voucher_judge.py" "$KDIR/stock_check.py" "$SCR/new/finance/" || stop "!! [3/6] could not lay out the walk - nothing installed"
W1=$(py "$KDIR/walk_s976.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR"); R1=$(echo "$W1" | tail -1)
case "$R1" in "WALK "*) a=${R1#WALK }; [ "${a%/*}" = "${a#*/}" ] && [ "${a%/*}" -ge 40 ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/6] the walk: $R1 - nothing installed"; };;
  *) echo "$W1" | tail -5 | cut -c1-200; stop "!! [3/6] the walk did not finish - nothing installed";; esac
W2=$(py "$KDIR/walk_s976.py" "$SCR/new/finance" "$SCR/new/marg_ingest" "$KDIR"); [ "$(echo "$W2" | tail -1)" = "$R1" ] || stop "!! [3/6] the walk a second time: $(echo "$W2" | tail -1) - nothing installed"
W0=$(py "$KDIR/walk_s976.py" "$SCR/old/finance" "$SCR/old/marg_ingest" "$KDIR")
echo "$W0" | grep -q "^FAIL  A1 stock_figure: a whole-unit item's pack is 1" || stop "!! [3/6] the control on the live files did not go red ($(echo "$W0" | tail -1)) - nothing installed"
for w in "${WALKS[@]}"; do wn="${w% *}"; ex="${w#* }"; for side in old new; do
    if [ "$ex" = 1 ]; then o=$(py "$KDIR/$wn" "$SCR/$side/finance" "$SCR/$side/marg_ingest" "$KDIR/walk_s971.py"); else o=$(py "$KDIR/$wn" "$SCR/$side/finance" "$SCR/$side/marg_ingest"); fi
    echo "$o" | tail -1 | grep -q "^WALK " || stop "!! [3/6] $wn on the $side files did not finish ($(echo "$o" | tail -1 | cut -c1-120)) - nothing installed"
    eval "F_$side=\"\$(fails \"\$o\")\""; done
  [ "$F_old" = "$F_new" ] || { diff <(echo "$F_old") <(echo "$F_new") | head -4 | cut -c1-160; stop "!! [3/6] $wn answers differently on the new files - nothing installed"; }; done
for c in A B; do py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy$c.db" >/dev/null
  [ -s "$SCR/copy$c.db" ] || stop "!! [3/6] could not take a copy of the database - nothing installed"; done
DA=$(cd "$SCR/old/finance" && FINANCE_DB="$SCR/copyA.db" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/live_s976.py" dump "$SCR/copyA.db" "$SCR/recA.json" 2>&1 | tail -1)
DB_=$(cd "$SCR/new/finance" && FINANCE_DB="$SCR/copyB.db" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/live_s976.py" dump "$SCR/copyB.db" "$SCR/recB.json" --fix "$KDIR" 2>&1 | tail -1)
LS=$(cd "$SCR/new/finance" && "$VPY" -W ignore -B "$KDIR/live_s976.py" compare "$SCR/recA.json" "$SCR/recB.json" 2>&1 | head -2)
rm -f "$SCR"/copy?.db; echo "    $DA"; echo "    $DB_" | cut -c1-200; echo "$LS" | sed 's/^/    /' | cut -c1-300
case "$DA $DB_" in "DUMP ok=True "*"DUMP ok=True "*) ;; *) stop "!! [3/6] the record on a copy did not build - nothing installed";; esac
case "$DB_" in *"fix=FIXED n="*|*"fix=FIXED n=0"*) ;; *) stop "!! [3/6] the count fix on a copy: ${DB_:-no answer} - nothing installed";; esac
case "$LS" in "LIVE-SHAPE built=True/True same_others=True "*"whole_pack1=True "*) ;; *) stop "!! [3/6] the record on a copy of the live database differs beyond the whole-unit items - nothing installed";; esac
say "[3/6] the walk on made-up data: $R1, twice; the control red on the live files; six earlier walks the same on old and new; the record on a COPY of the live database (above): every other item as before"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the copies green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S976_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/6] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(basename "$n").s976"; f="$ROOT/$n"
  { cat "$KDIR/$(basename "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/6] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(basename "$n").s976" "$ROOT/$n" || restore "the rename of $n"
  [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/desk /finance/stockmatch/ /finance/sanjeevni/ledger /finance/amir /finance/approvals; do d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(inf "$ROOT/finance" -c "
import stock_figure,stock_watch,voucher_judge,stock_check
print('S976 modules ok', stock_figure.KIT_S976, stock_watch.KIT_S976, voucher_judge.KIT_S976, stock_check.KIT_S976, hasattr(stock_watch,'_s976_pack'))" | tail -1)
case "$TK" in "S976 modules ok S976_WHOLE_UNIT_PACK S976_WHOLE_UNIT_PACK S976_WHOLE_UNIT_PACK S976_WHOLE_UNIT_PACK True") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; LG=$(flog); bad=$(echo "$LG" | grep -iE "stock_figure\.py|stock_watch\.py|stockmatch\.py|voucher_judge\.py|stock_check\.py|not mounted|S975 bands stopped" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
say "[4/6] five files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors answer, the modules load, the log clean"
APPLIED=1
AP=$(cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SPINE_DB="$SPINE" SHARED_LIB_DIR="$ROOT/shared" TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" flock -w 120 "$RLOCK" timeout 900 "$VPY" -u -W ignore -B "$KDIR/live_s976.py" apply "$LIVE_DB" "$KDIR" 2>&1 | tail -1)
case "$AP" in "APPLY build=True "*"| FIXED n="*) ;; *) restore "the count fix / the record rebuild on the live database ($(echo "$AP" | cut -c1-160))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/6]"
RD=$(inf "$ROOT/finance" "$KDIR/live_s976.py" read "$LIVE_DB" | tail -1)
case "$RD" in "READ ok=True "*) ;; *) restore "the live read ($(echo "$RD" | cut -c1-140))";; esac
PLACING=0
say "[5/6] $AP"
say "      $RD" | cut -c1-400
say "[6/6] Backups: $ROOT/finance/*.bak_S976_*  ·  the data's before-images in finance.db table s976_fix"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s976.sh"
say ""
say "$KIT: DONE."
exit 0
