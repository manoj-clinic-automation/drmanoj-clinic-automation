#!/bin/bash
# install_S972_EVENING_WIDENED.sh -- S972 (the parent, S539, 27-Nov-2026; D1099, D1100; K1 of S537_MORNING_CHECK_FINAL_BUILD_PLAN):
#   the evening check widened. On the same export and the same push, beside the slips Docterz does not carry, the evening now names
#   the money shapes of each patient's X-ray / procedure slip lines against Docterz: chhoot not applied · a slip line short in
#   Docterz · a line twice on one side (dono taraf hua tha?) · Docterz more than the slip (kaunsa sahi?). Payment mode is not compared.
#   FILE: /root/finance/evening_check.py b3c5bebb -> TO (TO_PINS.md5). clinic-finance is restarted (seconds). parchi_desk.py unchanged.
#   [1/5] kit sums  [2/5] the ground (evening_check.py its FROM)  [3/5] HERE: make_s972.py remakes the TO from the live bytes; the
#   walk ALL PASS on the live code with the TO laid over it, red at S1 on the live code as it is (the control); S960's own walk on
#   the TO with the shapes off ALL PASS with the live clock's send road (nothing of S960 changed); the probe on the live database,
#   read-only, counts only -- the last 30 exported days: no error, a day it could read, not more than 3 lines a day on average nor 8
#   on any one day, the reader's money within a quarter of the tracker's own lines on at least 5 pairs  [4/5] backup, swap, read-back, clinic-finance restarted, healthz 200, the
#   desk's doors answer (not 404), the service log clean, --status on the box's python  [5/5] the words.
#   Any red after [4/5] began: everything put back.  DRY=1: [1]-[3] only.  --undo: the file back, restarted (the table column kept).
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s972kit && cp -rp /root/deploy/repo/deploy_kits/S972_EVENING_WIDENED /tmp/s972kit && bash /tmp/s972kit/install_S972_EVENING_WIDENED.sh
set -u
KIT="S972_EVENING_WIDENED"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$FD/finance.db}"
A="$FD/evening_check.py"; A_FROM="b3c5bebb"
A_TO="$(awk '$2=="to/evening_check.py"{print $1}' "$KDIR/TO_PINS.md5")"
SCR="$(mktemp -d /tmp/s972_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
BAK="$A.bak_S972_$A_FROM"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s972"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_back() { [ "$(m8 "$A")" = "$A_FROM" ] && { CHANGED=0; return 0; }
  if [ "$(m8 "$BAK")" = "$A_FROM" ] && swap_in "$A" "$BAK" && [ "$(m8 "$A")" = "$A_FROM" ]; then say "   evening_check.py back: $(m8 "$A")"; CHANGED=0; return 0; fi
  say "   !! evening_check.py NOT back: $(m8 "$A") (backup $(m8 "$BAK"), expected $A_FROM)"; return 1; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$(dirname "$A")/.$(basename "$A").s972"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local p="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-600}" "$p" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  h="$(m8 "$A")"
  [ "$h" = "$A_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$(m5 "$A")" = "$A_TO" ] || stop "!! --undo: $A is $h, not S972's (a later change?) - not undoing. Tell Claude."
  [ "$(m8 "$BAK")" = "$A_FROM" ] || stop "!! --undo: the backup of evening_check.py is not its FROM - not undoing. Tell Claude."
  take_lock "--undo:" undo; CHANGED=1; put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || { release; say "!! --undo: $FSVC did not restart - tell Claude"; exit 1; }
  h="$(wait200)"; FINISHED=1; release; say "$KIT: UNDONE ($FSVC restarted, finance healthz $h; the column evening_check_push.shapes is kept, unused)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
[ -n "$A_TO" ] && [ "$(m5 "$KDIR/to/evening_check.py")" = "$A_TO" ] || stop "!! [1/5] the kit's TO is not as built - nothing installed"
say "   [1/5] kit sums ok"
for x in "$APY" "$VPY"; do [ -x "$x" ] || stop "!! [2/5] $x is not there - STOP. Tell Claude."; done
for n in "$PD/callback_clock.py" "$FD/parchi_desk.py" "$FD/slip_log.py" "$FD/not_in_docterz.py" "$FD/slip_adjust.py" "$FD/docterz_pickup.py" "$FD/docterz_ingest.py" "$FD/dx_feed.py" "$LIVE_DB"; do
  [ -f "$n" ] || stop "!! [2/5] $n is missing - STOP. Tell Claude."; done
if [ "$(m5 "$A")" = "$A_TO" ]; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
h="$(m8 "$A")"; [ "$h" = "$A_FROM" ] || stop "!! [2/5] $A is $h, not $A_FROM - it changed after this kit was built: STOP. Tell Claude."
say "   [2/5] the ground: evening_check $A_FROM; the clock $(m8 "$PD/callback_clock.py"), the desk $(m8 "$FD/parchi_desk.py")"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/s960" "$SCR/remade"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" && \cp -p "$FD"/*.py "$SCR/s960/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py "$APY" "$KDIR/make_s972.py" "$A" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s972.py refused the live file - nothing installed"; }
[ "$(m5 "$SCR/remade/evening_check.py")" = "$A_TO" ] || stop "!! [3/5] evening_check.py remade from the live bytes is not the kit's TO - nothing installed"
\cp "$KDIR/to/evening_check.py" "$SCR/new/"; \cp "$KDIR/to/evening_check.py" "$SCR/s960/"
for x in "$APY" "$VPY"; do (cd "$SCR" && "$x" -c 'import py_compile,sys
py_compile.compile(sys.argv[2], cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/evening_check.py") \
  || stop "!! [3/5] evening_check.py does not compile under $x - nothing installed"; done
W="$(py "$APY" "$KDIR/walk_s972.py" "$SCR/new")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q "^ALL PASS$" || { echo "$W" | grep -E "^FAIL|Error" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
WC="$(py "$APY" "$KDIR/walk_s972.py" "$SCR/old")"; rc=$?
[ "$rc" != 0 ] && echo "$WC" | grep -q "^FAIL  S1 " || stop "!! [3/5] the control (the walk on the live code as it is) did not go red at S1 - nothing installed"
W6="$(EVCHK_SHAPES=0 W960_REAL_CC="$PD/callback_clock.py" py "$APY" "$KDIR/walk_s960.py" "$SCR/s960")"; rc=$?
[ "$rc" = 0 ] && echo "$W6" | tail -1 | grep -q "^ALL PASS$" && echo "$W6" | grep -q "^PASS  C1 " || { echo "$W6" | grep -E "^FAIL|Error" | head -8; stop "!! [3/5] S960's own walk on the TO (shapes off, the live clock) is not all green - nothing installed"; }
if [ -n "${PROBE_CMD:-}" ]; then PR="$($PROBE_CMD)"; else PR="$(py "$APY" "$KDIR/probe_s972.py" "$SCR/new" "$LIVE_DB" 30 | tail -1)"; fi
echo "$PR" | grep -q "^PROBE972 days " || { echo "$PR" | tail -3; stop "!! [3/5] the probe on the live database did not run - nothing installed"; }
pd="$(echo "$PR" | awk '{print $3}')"; pu="$(echo "$PR" | awk '{print $5}')"; pe="$(echo "$PR" | awk '{print $7}')"; pl="$(echo "$PR" | awk '{print $9}')"
ps="$(echo "$PR" | awk '{print $23}')"; px="$(echo "$PR" | awk '{print $25}')"; pm="$(echo "$PR" | awk '{print $27}')"; rd=$(( ${pd:-0} - ${pu:-0} ))
say "         the live shape (read-only, counts only): $PR"
[ "$rd" -ge "${PROBE_MIN_DAYS:-1}" ] || stop "!! [3/5] the probe found no exported day it could read on the live database - it proves nothing; nothing installed. Send a photo to Claude."
[ "${pe:-1}" = 0 ] || stop "!! [3/5] the probe met an error on the live shape - nothing installed. Send a photo to Claude."
[ "${pl:-0}" -le $(( rd * ${PROBE_MAX_PER_DAY:-3} )) ] && [ -n "${pm:-}" ] && [ "${pm:-99}" -le "${PROBE_MAX_ONE_DAY:-8}" ] || stop "!! [3/5] on the live shape the evening would name more than ${PROBE_MAX_PER_DAY:-3} lines a day on average, or more than ${PROBE_MAX_ONE_DAY:-8} on one day - too noisy for the staff; nothing installed. Send a photo to Claude."
[ $(( ${ps:-0} + ${px:-0} )) -ge "${PROBE_MIN_PAIRS:-5}" ] || stop "!! [3/5] the probe found fewer than ${PROBE_MIN_PAIRS:-5} money pairs to compare with the tracker's own lines - the reader is unproven; nothing installed. Send a photo to Claude."
[ $(( ${px:-0} * 4 )) -le $(( ${ps:-0} + ${px:-0} )) ] || stop "!! [3/5] the reader's money differs from the tracker's own lines on more than a quarter of the pairs - nothing installed. Send a photo to Claude."
say "   [3/5] walk ALL PASS ($(echo "$W" | grep -c '^PASS')); control red at S1; S960's walk ALL PASS with the shapes off and the live clock; TO remade from the live bytes"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
\cp -p "$A" "$BAK" && chmod 600 "$BAK" && [ "$(m8 "$BAK")" = "$A_FROM" ] || stop "!! [4/5] the backup did not read back - nothing placed"
CHANGED=1
swap_in "$A" "$KDIR/to/evening_check.py" && [ "$(m5 "$A")" = "$A_TO" ] || restore "[4/5] evening_check.py did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/slips/desk/api/evening); case "$d1" in 404|000|5*) restore "the desk's evening door answers $d1 (not mounted)";; esac
d2=$(door /finance/slips/desk/api/evening/answer); case "$d2" in 404|000|5*) restore "the desk's new answer door answers $d2 (not mounted)";; esac
d3=$(door /finance/slips/desk); case "$d3" in 404|000|5*) restore "the slip desk answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|evening_check|NOT mounted" | head -3)   # 'evening_check NOT mounted' is printed by parchi_desk.init
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
st=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$A" --status --db "$LIVE_DB" 2>&1 | tail -1)
echo "$st" | grep -q "^EVENING S972 1 " || restore "[4/5] evening_check --status did not run on the box's python ($st)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [4/5] placed and read back: evening_check $(m8 "$A"); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the doors $d1 / $d2 / $d3 (login-gated); the log clean"
say "         today: $(echo "$st" | sed 's/^EVENING S972 1 //')"
FINISHED=1; CHANGED=0; release
say "   [5/5] ON: tonight's export is checked for the money too -- Shavez and reception see each difference on the push and the desk."
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S972_EVENING_WIDENED.sh --undo"
