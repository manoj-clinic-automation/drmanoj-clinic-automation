#!/bin/bash
# =============================================================================
#  install_S926_SHORTAGES_AND_RENAMES.sh · kit S926 (22-Nov-2026, Sanjeevni session 502) · the owner's word 10:37 IST ("find a way, build accordingly")
#   /root/finance/order_flow.py  de570252 -> TO : v2.0 -- one shortage per medicine (its orders, what came, the taps, his words); a medicine a
#        dealer fails to send twice comes to him by itself; the substitute flow (choose -> on the dealer's next order -> arrived -> OK / return);
#        the identity check: a Marg rename the Marg watch found becomes his one-tap question (Yes same medicine / No two items), a name Marg no
#        longer prints is never a shortage; Stock & ledger inline on every row with the link to the full page; staff read his word as an instruction.
#   /root/finance/order_s778.py  e11eebee -> TO : hidden() also holds a dead name (not in Marg's newest closing, no known partner) off the order list.
#   /root/finance/darpan_kal.html cd88fac7 -> TO : Darpan's team block shows the doctor's word and the Marg stock.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s926kit && cp -rp /root/deploy/repo/deploy_kits/S926_SHORTAGES_AND_RENAMES /tmp/s926kit && bash /tmp/s926kit/install_S926_SHORTAGES_AND_RENAMES.sh
#  (DRY=1 before bash: every gate and the walks; NOTHING written.)
# =============================================================================
set -u
KIT="S926_SHORTAGES_AND_RENAMES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
NAMES=("finance/order_flow.py" "finance/order_s778.py" "finance/darpan_kal.html")
FROMS=("de5702520b9b1983c8e70f829f43adaa" "e11eebee03332d41eef28109c02ef3b6" "cd88fac746f3b93ee024a3be33f39c7c")
KF=("order_flow.py" "order_s778.py" "darpan_kal.html")
N=3; IDX="0 1 2"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s926_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
# the earlier kits' own proofs run on the new files too (the S837 rule: the install stops only on a check WORSE than the live files);
# these checks changed BY DESIGN with S926 (the team row is a shortage, not a tap; two texts) and are allowed to differ:
ALLOWED_DIFF="team = the open 'Ab nahi milta' rows|Wait — order next week|wait_pass: on the day it becomes keep ordering|the waited medicine is back on the list|Substitute aaya on the team list|its out-of-stock count is the team list's"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S926_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s926"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
# the service's own log since the restart proves the module loaded (F-1554): every door of the flow is login-gated, a page cannot prove it
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
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fails() { echo "$1" | grep '^FAIL' | sed 's/^FAIL //' | cut -d'(' -f1 | sed 's/ *$//' | sort -u; }

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
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/order_flow.py" "$KDIR/order_s778.py" "$KDIR/walk_s926.py" "$KDIR/walk_s920_s926guard.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$1" >/dev/null && [ -s "$1" ]; }
copydb "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database for the walk - nothing installed"
W1=$(py "$KDIR/walk_s926.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^RED" | cut -c1-160; stop "!! [3/6] the walk on a copy of the live database: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s926.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
say "[3/6] S926's walk on a copy of the live database: $(echo "$W1" | grep -c '^ok') checks pass; the control goes red as it must"
# the earlier kits' proofs, old files vs new files on the same copy: stop only on a check worse than the live files and not changed by design
WORSE=""
for kk in S920_PURCHASE_FLOW_1/walk_s920.py S921_PURCHASE_FLOW_2/walk_s921.py S922_PURCHASE_FLOW_3/walk_s922.py S923_PURCHASE_FLOW_4/walk_s923.py S924_PURCHASE_FLOW_5/walk_s924.py S925_OWNER_TILE_TO_FLOW/walk_s925.py; do
  w="$REPO_KITS/$kk"; [ -f "$w" ] || { say "   (no $kk in the repo - skipped)"; continue; }
  copydb "$SCR/c_old.db" || stop "!! [3/6] could not copy the database for $kk - nothing installed"; copydb "$SCR/c_new.db" || stop "!! [3/6] could not copy the database for $kk - nothing installed"
  O=$(py "$w" "$SCR/old" "$SCR/c_old.db"); Nn=$(py "$w" "$SCR/new" "$SCR/c_new.db")
  of=$(fails "$O"); nf=$(fails "$Nn")
  extra=$(comm -13 <(echo "$of") <(echo "$nf") | grep -v -E "^($ALLOWED_DIFF)$" | grep -v '^$')
  say "   $(basename "$w"): old $(echo "$O" | grep -c '^PASS') pass / new $(echo "$Nn" | grep -c '^PASS') pass; design differences $(comm -13 <(echo "$of") <(echo "$nf") | grep -c -E "^($ALLOWED_DIFF)$")"
  [ -z "$extra" ] || WORSE="$WORSE
$(basename "$w"): $extra"
  rm -f "$SCR/c_old.db" "$SCR/c_new.db"
done
# S920's walk stops itself at its superseded assumption (a team row = a tap row) before 20 more checks; the kit carries that walk with the
# one line guarded, run on the new files alone: every check but the design difference must pass
copydb "$SCR/c_g.db" || stop "!! [3/6] could not copy the database for the guarded S920 walk - nothing installed"
Gw=$(py "$KDIR/walk_s920_s926guard.py" "$SCR/new" "$SCR/c_g.db"); gf=$(fails "$Gw" | grep -v -E "^($ALLOWED_DIFF)$" | grep -v '^$')
say "   walk_s920 (guarded, new files): $(echo "$Gw" | grep -c '^PASS') pass, $(echo "$Gw" | grep -c '^FAIL') design difference(s)"
[ -z "$gf" ] || WORSE="$WORSE
walk_s920 (guarded): $gf"
rm -f "$SCR/c_g.db" "$SCR/copy.db"
[ -z "$WORSE" ] || stop "!! [3/6] the new files do WORSE than the live ones on:$WORSE
   - nothing installed. Tell Claude."
say "[3/6] the earlier kits' proofs: nothing worse than the live files (the copies removed)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; chown --reference="$ROOT/${NAMES[$k]}" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/porders/flow); case "$d1" in 404|000|5*) restore "his flow page answers $d1";; esac
d2=$(door /finance/porders/api/flow/items); case "$d2" in 404|000|5*) restore "the substitute picker's door answers $d2";; esac
d3=$(door /finance/darpan/kal/api/order/flow); case "$d3" in 404|000|5*) restore "Darpan's order-flow door answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "order_flow NOT mounted|S921 home failed|S922 dar_view failed|S924 .* failed|S926 .* failed|S926 .* not read|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
PLACING=0
say "[4/6] the three files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, his flow page $d1, the picker door $d2, Darpan's door $d3 (login-gated), the service log clean since the restart"
release_lock
say "[5/6] what changes on the pages now: his Purchase orders page -- the section 'Not delivered, out of stock and substitutes', one row per medicine, Stock & ledger on each; the Hub's purchase line counts the same rows; reception's and Darpan's team blocks read his word."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s926.sh  (the three files back, $FSVC restarted; his words stay in order_flow_word, harmless to the old code)"
say ""
say "$KIT: DONE."
exit 0
