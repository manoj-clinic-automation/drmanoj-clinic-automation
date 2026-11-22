#!/bin/bash
# =============================================================================
#  install_S928_STOCK_ONE_RULE.sh · kit S928 (22-Nov-2026, Sanjeevni session 503) · the owner's word 22-Nov 07:01 / 07:49 IST (D1036, D1037)
#   /root/finance/stock_figure.py cc1cef5d -> TO : THE ONE ARRIVALS RULE counts a delivery by the dealer's SCANNED BILL's quantity, never by
#        reception's tap (bill_units / _count_units; a tap above the bill is a short supply -- short_supplies(); a tapped medicine the bill does
#        not carry counts nothing; no usable read scan -> the tap stands as before); a count saved at or after the evening hour is the END of
#        its day (its day's sales not taken off again; evening_count); an uncounted item's spot count is judged with its scan-tied delivery.
#   /root/finance/stock_watch.py   5acf3cf0 -> TO : two settings on his page (arrival.bill_over_tap on/off, count.evening_hour 17); every count
#        Darpan writes reaches the owner as ONE line a day on his Needs-you ('Darpan counted N items today: ...'), rewritten after each count.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s928kit && cp -rp /root/deploy/repo/deploy_kits/S928_STOCK_ONE_RULE /tmp/s928kit && bash /tmp/s928kit/install_S928_STOCK_ONE_RULE.sh
#  (DRY=1 before bash: every gate and every walk; NOTHING written.)
# =============================================================================
set -u
KIT="S928_STOCK_ONE_RULE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; SPINE_DB_LIVE="${SPINE_DB_LIVE:-$ROOT/finance/spine/spine.db}"
NAMES=("finance/stock_figure.py" "finance/stock_watch.py")
FROMS=("cc1cef5dbc29694b2cf4de70b2dffc1a" "5acf3cf0ca8f927df5ef69bb804815f8")   # read from the live bytes (the 22-Nov bundle + S927's TO), never typed from a prefix (F-1480)
KF=("stock_figure.py" "stock_watch.py")
N=2; IDX="0 1"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s928_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S928_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s928"; }
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
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 1200 "$VPY" -u -W ignore -B "$@" 2>&1); }
reds() { { echo "$1" | grep -E '^(FAIL|RED)' | sed -E 's/^(FAIL|RED) +//' | cut -d'[' -f1 | sed 's/ *$//'; echo "$1" | grep -q '^RESULT:' || echo "the walk did not finish"; } | sort -u; }

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
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/stock_figure.py" "$KDIR/stock_watch.py" "$KDIR/synth_s928.py" "$KDIR/regress_s928.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/new/spine" "$SCR/old/spine" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
mkdir -p "$SCR/new/finance_ui" "$SCR/old/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/* "$SCR/old/finance_ui/" 2>/dev/null
\cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/old/" 2>/dev/null   # S927's walk reads it beside the code
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2" >/dev/null && [ -s "$2" ]; }
copydb "$LIVE_DB" "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database - nothing installed"
# (a) the synth: made-up spine, scans and orders on a scratch database with the copy's schema; the control (the live files) must go red
W1=$(py "$KDIR/synth_s928.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep -E "^FAIL" | cut -c1-200; stop "!! [3/6] the synth on the new files: $R1 - nothing installed"; }
W0=$(py "$KDIR/synth_s928.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
say "[3/6] S928's synth: $(echo "$W1" | grep -c '^ok') checks pass on the new files; the control goes red as it must ($(echo "$W0" | grep -c '^FAIL') red)"
# (b) the live shape: the figures of record on copies of the live finance.db and spine.db, old files vs new -- every difference explained by S928
if [ -f "$SPINE_DB_LIVE" ]; then
  copydb "$SPINE_DB_LIVE" "$SCR/spine.db" || stop "!! [3/6] could not copy the spine - nothing installed"
  copydb "$LIVE_DB" "$SCR/c_old.db" || stop "!! [3/6] could not copy the database - nothing installed"; copydb "$LIVE_DB" "$SCR/c_new.db" || stop "!! [3/6] could not copy the database - nothing installed"
  D0=$(py "$KDIR/regress_s928.py" dump "$SCR/old" "$SCR/c_old.db" "$SCR/spine.db" "$SCR/old.json"); echo "$D0" | tail -1 | cut -c1-160
  D1=$(py "$KDIR/regress_s928.py" dump "$SCR/new" "$SCR/c_new.db" "$SCR/spine.db" "$SCR/new.json"); echo "$D1" | tail -1 | cut -c1-160
  C=$(py "$KDIR/regress_s928.py" compare "$SCR/old.json" "$SCR/new.json"); RC=$(echo "$C" | tail -1)
  echo "$C" | grep -E "^INFO|^  explained|^  RED" | head -40 | cut -c1-200
  [ "$RC" = "RESULT: ALL PASS" ] || stop "!! [3/6] the live-shape compare: $RC - an unexplained change in a figure of record; nothing installed"
  say "   the figures of record on copies of the live databases: $(echo "$C" | grep '^INFO' | cut -c6-)"
  rm -f "$SCR/c_old.db" "$SCR/c_new.db" "$SCR/spine.db"
else
  say "   (no spine at $SPINE_DB_LIVE - the live-shape compare skipped)"
fi
# (c) the earlier kits' own proofs, old files vs new on the same copy: stop only on a check WORSE than the live files (the S837 rule)
WORSE=""
if [ -f "$REPO_KITS/S927_HUB_NEEDS_YOU_INLINE/walk_s927.py" ]; then
  copydb "$LIVE_DB" "$SCR/c_old.db"; copydb "$LIVE_DB" "$SCR/c_new.db"
  O=$(py "$REPO_KITS/S927_HUB_NEEDS_YOU_INLINE/walk_s927.py" "$SCR/old" "$SCR/c_old.db"); Nn=$(py "$REPO_KITS/S927_HUB_NEEDS_YOU_INLINE/walk_s927.py" "$SCR/new" "$SCR/c_new.db")
  extra=$(comm -13 <(reds "$O") <(reds "$Nn") | grep -v '^$')
  say "   walk_s927: old $(echo "$O" | grep -c '^ok') ok / new $(echo "$Nn" | grep -c '^ok') ok"
  [ -z "$extra" ] || WORSE="$WORSE
walk_s927: $extra"
  rm -f "$SCR/c_old.db" "$SCR/c_new.db"
else say "   (no walk_s927 in the repo - skipped)"; fi
if [ -f "$REPO_KITS/S894_ASKED_COUNT_BACK/synth_s894.py" ]; then
  copydb "$LIVE_DB" "$SCR/c_old.db"; copydb "$LIVE_DB" "$SCR/c_new.db"
  O=$(py "$REPO_KITS/S894_ASKED_COUNT_BACK/synth_s894.py" --code "$SCR/old" --finance "$SCR/c_old.db"); Nn=$(py "$REPO_KITS/S894_ASKED_COUNT_BACK/synth_s894.py" --code "$SCR/new" --finance "$SCR/c_new.db")
  o_red=$(echo "$O" | tail -1 | sed -E 's/.* ([0-9]+) red.*/\1/'); n_red=$(echo "$Nn" | tail -1 | sed -E 's/.* ([0-9]+) red.*/\1/')
  say "   synth_s894: old $(echo "$O" | tail -1 | cut -c1-60) / new $(echo "$Nn" | tail -1 | cut -c1-60)"
  case "$o_red$n_red" in *[!0-9]*) WORSE="$WORSE
synth_s894: could not read its result";; *) [ "${n_red:-0}" -le "${o_red:-0}" ] || WORSE="$WORSE
synth_s894: $n_red red on the new files, $o_red on the live ones";; esac
  rm -f "$SCR/c_old.db" "$SCR/c_new.db"
else say "   (no synth_s894 in the repo - skipped)"; fi
[ -z "$WORSE" ] || stop "!! [3/6] an earlier kit's proof is WORSE on the new files than on the live ones - nothing installed:$WORSE"
rm -f "$SCR/copy.db"
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
d1=$(door /finance/sanjeevni/api/needs-you); case "$d1" in 404|000|5*) restore "the Needs-you door answers $d1";; esac   # login-gated: 302 says nothing (F-1439)
d2=$(door /finance/stock/api/now); case "$d2" in 404|000|5*) restore "the stock-now door answers $d2";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|Error:" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
PLACING=0
say "[4/6] the two files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, the doors $d1 / $d2 (login-gated), the service log clean since the restart"
release_lock
say "[5/6] what changes now: a delivery counts by the dealer's scanned bill, never reception's tap (a tap above the bill reads as a short supply); a count saved after 17:00 is the end of its day; every count Darpan writes reaches your Needs-you as one line a day. Two new rows on your stock settings page (the bill over the tap: on/off; the evening hour)."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s928.sh  (the two files back to their FROM pins, $FSVC restarted; the two settings rows stay unread, harmless)"
say ""
say "$KIT: DONE."
exit 0
