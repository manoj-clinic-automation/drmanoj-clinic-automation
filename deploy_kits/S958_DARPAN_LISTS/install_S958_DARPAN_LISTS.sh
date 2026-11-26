#!/bin/bash
# =============================================================================
#  install_S958_DARPAN_LISTS.sh · kit S958 (26-Nov-2026, Sanjeevni session 522) · his word 10:22 / 10:24 ("build" · next list every day: yes)
#   /root/finance/order_track.py  9baf057e -> v1.3 : ONE not-needed rule -- his stop, Darpan's 'Ab nahi milta' / 'Abhi nahi chahiye' take a line or carry
#        off every list (the call list, Maal aaya, purani dawa, the carry); a bill's extra packs fill the same item's other line (the XL).
#   /root/finance/stock_watch.py  23873a1b -> v1.14: his next-list asks reach Darpan the next morning, every day; his counts pushed to Darpan.
#   /root/finance/stock_check.py  686845f8 : the next-list day on his page. /root/finance/order_rules.py eac7ec37 : Darpan's order notices open his page.
#   /root/finance/darpan_kal.html 0165bcb3 · stockmatch.html 8ba51618 : a tap lands even when the page is already open.
#   the parent's /root/finance/aaj_seed.py 6f4784ae : Aaj ka kaam's count line also counts his Count-now asks.
#   the parent's /root/portal/portal_sw.js ab728b08 : the app's tap brings up Darpan's open page and tells it where to go.
#   then today's list (his waiting asks) written now.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s958kit && cp -rp /root/deploy/repo/deploy_kits/S958_DARPAN_LISTS /tmp/s958kit && bash /tmp/s958kit/install_S958_DARPAN_LISTS.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S958_DARPAN_LISTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
FILES=("finance/order_track.py 9baf057e45c38840381293933021193a" "finance/stock_watch.py 23873a1bc7d7ae78f533f34b19162eaa"
       "finance/stock_check.py 686845f8ec895506a51892d3fbf629d9" "finance/order_rules.py eac7ec3721fb729b9f3f45c0ce2510b3"
       "finance/darpan_kal.html 0165bcb329f0bcd70ecea477f7322d57" "finance/stockmatch.html 8ba51618ff8a35c2474285367ed81026"
       "finance/aaj_seed.py 6f4784ae945d8daba2c4296334aa669e" "portal/portal_sw.js ab728b08ccfdc2f0e904b223a7c28cc0"
       "finance/porders_s454.py 4e98e82e44be62d5164072e1ad87dd58" "finance/order_track_page.py 2d7384306c009c290dbe2a9cd048e7e1")
READS=("finance/order_s778.py" "finance/order_d1053.py" "finance/order_flow.py" "finance/aaj_kaam.py")
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s958_inst_$STAMP"; TOOK_LOCK=0; PLACING=0; DATA=""
ATF="$ROOT/finance/.s958_roster_ids"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
base() { basename "$1"; }
say() { echo "$@"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for e in "${FILES[@]}"; do n="${e%% *}"; rm -f "$ROOT/$(dirname "$n")/.$(base "$n").s958"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fin() { (cd "$ROOT/finance" && FINANCE_DB="$LIVE_DB" SHARED_LIB_DIR="$ROOT/shared" PYTHONPYCACHEPREFIX="$SCR/pyc" SPINE_DB="${SPINE_DB:-$ROOT/finance/spine/spine.db}" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting it back"
  if [ -n "$DATA" ]; then say "   today's list first: $(fin "$KDIR/roster_s958.py" undo "$ATF" | tail -1)"; fi
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S958_${fr:0:8}"; [ -f "$b" ] && \cp -p "$b" "$ROOT/$n"; done
  rm -f "$ATF"; "$SYSTEMCTL" restart "$FSVC" || true
  for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; say "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${fr:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
ALL=1
for e in "${FILES[@]}"; do n="${e%% *}"; to="$(to_of "$n")"
  [ -n "$to" ] && [ "$(m5 "$KDIR/$(base "$n")")" = "$to" ] || { say "!! [1/5] the kit's $(base "$n") is not at its TO pin - nothing installed"; exit 1; }
  [ "$(m5 "$ROOT/$n")" = "$to" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the ten files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; [ "$(m5 "$ROOT/$n")" = "$fr" ] || stop "!! [2/5] $ROOT/$n is $(m5 "$ROOT/$n" | cut -c1-8), expected ${fr:0:8} - STOP, nothing installed. Tell Claude."; done
for r in "${READS[@]}"; do [ -s "$ROOT/$r" ] || stop "!! [2/5] $ROOT/$r is missing - STOP, nothing installed. Tell Claude."; done
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/order_track.py" "$KDIR/stock_watch.py" "$KDIR/stock_check.py" "$KDIR/order_rules.py" "$KDIR/aaj_seed.py" "$KDIR/porders_s454.py" "$KDIR/order_track_page.py" "$KDIR/walk_s958.py" "$KDIR/roster_s958.py" || stop "!! [2/5] a file does not compile on $p - nothing installed"; done
if command -v node >/dev/null 2>&1; then node --check "$KDIR/portal_sw.js" || stop "!! [2/5] portal_sw.js does not parse - nothing installed"; fi
say "[2/5] the ten files at their FROM pins (stock_watch at S957's as installed); the kit compiles"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
mkdir -p "$SCR/new/spine" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/new/spine/" 2>/dev/null
\cp -p "$ROOT/portal/portal_sw.js" "$SCR/new/" || stop "!! [3/5] could not lay out the walk - nothing installed"
\cp -rp "$SCR/new/." "$SCR/old/"
for e in "${FILES[@]}"; do \cp -p "$KDIR/$(base "${e%% *}")" "$SCR/new/" || stop "!! [3/5] could not lay out the walk - nothing installed"; done
py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$SCR/copy.db" >/dev/null \
  && [ -s "$SCR/copy.db" ] || stop "!! [3/5] could not take a copy of the database for the walk - nothing installed"
\cp -p "$SCR/copy.db" "$SCR/copy0.db"
W1=$(py "$KDIR/walk_s958.py" "$SCR/new" "$SCR/copy.db" "$SCR/old"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk on a copy: $R1 - nothing installed"; }
W2=$(py "$KDIR/walk_s958.py" "$SCR/new" "$SCR/copy.db" "$SCR/old"); R2=$(echo "$W2" | tail -1)
[ "$R2" = "RESULT: ALL PASS" ] || { echo "$W2" | grep "^FAIL" | cut -c1-200; stop "!! [3/5] the walk a second time on the same copy: $R2 - nothing installed"; }
W0=$(py "$KDIR/walk_s958.py" "$SCR/old" "$SCR/copy0.db" "$SCR/old" control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/5] the control did not go red ($R0) - nothing installed";; esac
for w in "FAIL  TOLTRIS PLUS" "FAIL  KNEE SUPPORT XL HINGED" "FAIL  a non-spot morning builds" "FAIL  his Count now reaches" "FAIL  the order notice opens"; do   # red by the rules
  echo "$W0" | grep -q "^$w" || stop "!! [3/5] the control did not go red on: ${w#FAIL  } - nothing installed"; done
rm -f "$SCR/copy.db" "$SCR/copy0.db"
say "[3/5] the walk on a copy of the database: $(echo "$W1" | grep -c '^PASS') checks pass, twice on one copy; the control goes red by the rules ($R0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for e in "${FILES[@]}"; do n="${e%% *}"; fr="${e#* }"; b="$ROOT/$n.bak_S958_${fr:0:8}"
  { \cp -p "$ROOT/$n" "$b" && [ "$(m5 "$b")" = "$fr" ]; } || stop "!! [4/5] could not write the backup of $n - nothing placed"; done
for e in "${FILES[@]}"; do n="${e%% *}"; S="$ROOT/$(dirname "$n")/.$(base "$n").s958"; f="$ROOT/$n"
  { cat "$KDIR/$(base "$n")" > "$S" && chmod --reference="$f" "$S" 2>/dev/null; chown --reference="$f" "$S" 2>/dev/null; [ "$(m5 "$S")" = "$(to_of "$n")" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
PLACING=1
for e in "${FILES[@]}"; do n="${e%% *}"; mv -f "$ROOT/$(dirname "$n")/.$(base "$n").s958" "$ROOT/$n" || restore "the rename of $n"; [ "$(m5 "$ROOT/$n")" = "$(to_of "$n")" ] || restore "the read back of $n"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
for u in /finance/stockcheck/ /finance/stockcheck/api/rows /finance/darpan/kal /finance/stockmatch /finance/porders/s454/late /finance/aaj; do
  d=$(door "$u"); case "$d" in 404|000|5*) restore "$u answers $d";; esac; done
TK=$(cd "$ROOT/finance" && FINANCE_DB="$SCR/none.db" timeout 60 "$VPY" -W ignore -B -c "import order_track,stock_watch,stock_check,order_rules,aaj_seed,porders_s454,order_track_page; print('S958 module ok', order_track.VERSION, order_track.KIT, stock_watch.VERSION)" 2>&1 | tail -1)
case "$TK" in "S958 module ok 1.3 S958_DARPAN_LISTS 1.14") ;; *) restore "the modules do not load ($TK)";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "order_track\.py|stock_watch\.py|stock_check\.py|order_rules\.py|aaj_seed\.py|porders_s454\.py|order_track_page\.py|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
SWS=$(if [ -n "${PORTAL_SW_CMD:-}" ]; then $PORTAL_SW_CMD; else curl -s -m 8 http://127.0.0.1:8099/portal/sw.js; fi | md5sum | awk '{print $1}')   # the review: the bytes the app is served
[ "$SWS" = "$(to_of portal/portal_sw.js)" ] || restore "the portal serves sw.js as ${SWS:0:8}, not the new one"
DATA=1; : > "$ATF"                                              # the ids of the rows it writes (no clock)
ONE=$(fin "$KDIR/roster_s958.py" build "$ATF" | tail -1)
case "$ONE" in "S958 roster: "*) ;; *) restore "today's list was not written ($(echo "$ONE" | cut -c1-120))";; esac
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/5]"
PLACING=0
say "[4/5] ten files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, six pages answer, the modules load, the log clean"
say "[5/5] $ONE"
release_lock
say "    undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s958.sh"
say ""
say "$KIT: DONE."
exit 0
