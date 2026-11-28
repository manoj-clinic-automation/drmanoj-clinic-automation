#!/bin/bash
# install_S977_MORNING_REVENUE_MATCH.sh -- S977 (the parent, S544, 28-Nov-2026; D1099, D1100 -- K2a; his word 14:03 "build K2
#   today"). The morning day check becomes a match of MONEY against MONEY: register total vs Docterz total (net of refunds / radd).
#   No payment-mode card; no Docterz edit asked the next morning (a slip whose money the register holds is kept outside Docterz by
#   itself); register MORE -> one card naming the day's patients with no paid bill; register LESS by exactly one bill of one head ->
#   reception's card (register wrong / who did not pay -> the existing 'money never taken' radd); else HIS push, once per line.
#   The clean push carries the day's sum. F-1732: an empty consultation report after the day's good one is no longer 'set aside'.
#   DAYCHK_REVENUE=0 puts the old morning back; REGPUSH_OWNER=0 stops his push alone.
#   FILES: /root/finance/day_check.py 946f0408 (S970) . register_push.py 9b1fbc29 (S970) . docterz_pickup.py 8ffb93aa (S960) -> TO.
#   [1/6] kit sums  [2/6] the ground (three FROM)  [3/6] HERE, with the box's own python: make_s977.py remakes the TO from the live
#   bytes; the walk green on the TO, red on the FROM (the control); the live shape on a COPY of finance.db (0700 scratch, counts)
#   [4/6] waits for a quiet minute between the 5-minute push runs; backups, swaps, read-backs  [5/6] ONE quiet sweep (the week
#   recorded as told under the new line names -- nothing pushed about an old day); restart, healthz 200, the day check answers,
#   the log clean, --status  [6/6] ON.  Any red after [4/6] began, or the run killed: all put back.  DRY=1: [1]-[3] only.
#   --undo: the three files back; the old register_push records the week under its own line names (no push); restarted
#   (the owner_sent column stays: additive, unread by the old code). A full return to the S970 morning without an undo:
#   DAYCHK_REVENUE=0 and REGPUSH_OWNER=0.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s977kit && \cp -rp /root/deploy/repo/deploy_kits/S977_MORNING_REVENUE_MATCH /tmp/s977kit && bash /tmp/s977kit/install_S977_MORNING_REVENUE_MATCH.sh
set -u
KIT="S977_MORNING_REVENUE_MATCH"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"
VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$FD/finance.db}"
B="$FD/day_check.py";      B_FROM="946f0408bd9763bfd1578648bd07ab1b"
C="$FD/register_push.py";  C_FROM="9b1fbc29aff1472a1a4dfb2ad4cfcf3a"
P="$FD/docterz_pickup.py"; P_FROM="8ffb93aa461c74ca4dbbeabdff1d2081"
NAMES="day_check.py register_push.py docterz_pickup.py"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
B_TO="$(to day_check.py)"; C_TO="$(to register_push.py)"; P_TO="$(to docterz_pickup.py)"
SCR="$(mktemp -d /tmp/s977_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$1.bak_S977_${2:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s977"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
put_back() { local r=0; put_one "$C" "$C_FROM" || r=1; put_one "$B" "$B_FROM" || r=1; put_one "$P" "$P_FROM" || r=1; [ "$r" = 0 ] && CHANGED=0; return $r; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
reseed_old() {   # review S5: after a put-back the old register_push records the week under ITS line names, pushing nothing
  [ "$(m5 "$C")" = "$C_FROM" ] || return 0
  (cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 120 "$VPY" -W ignore -B "$C" --sweep --no-push --db "$LIVE_DB" >/dev/null 2>&1) || true; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; [ "${QS_DONE:-0}" = 1 ] && reseed_old; restart || true
  say "   $FSVC restarted, healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; [ "${QS_DONE:-0}" = 1 ] && reseed_old; restart || true; fi
  release; rm -rf "${SCR:?}"; for n in $NAMES; do rm -f "$FD/.$n.s977"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local x="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-900}" "$x" -W ignore -B "$@" 2>&1); }
quiet_minute() {   # the 5-minute push (cron # S968_REGISTER_PUSH, */5) has just run: start in minute 1 or 2 of the five
  [ "${NO_WAIT:-0}" = 1 ] && return 0
  for _w in $(seq 1 70); do m=$((10#$(TZ=Asia/Kolkata date +%M) % 5)); { [ "$m" = 1 ] || [ "$m" = 2 ]; } && return 0; sleep 5; done; return 0; }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$B")" = "$B_FROM" ] && [ "$(m5 "$C")" = "$C_FROM" ] && [ "$(m5 "$P")" = "$P_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  for x in "$B $B_TO $B_FROM" "$C $C_TO $C_FROM" "$P $P_TO $P_FROM"; do set -- $x; h="$(m5 "$1")"
    [ "$h" = "$2" ] || [ "$h" = "$3" ] || stop "!! --undo: $1 is ${h:0:8}, not S977's (a later kit?) - not undoing. Tell Claude."
    [ "$h" = "$3" ] || [ "$(m5 "$(bak "$1" "$3")")" = "$3" ] || stop "!! --undo: the backup of $(basename "$1") is not the FROM bytes - not undoing. Tell Claude."; done
  take_lock "--undo:" undo; CHANGED=1
  put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  reseed_old; restart || true; h=$(wait200); release
  say "$KIT: UNDONE ($FSVC restarted, healthz $h; the morning check is as S970 left it)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/6] KIT_ID.txt names another kit - nothing installed"
for n in $NAMES; do [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/6] the kit's TO files are not as built - nothing installed"; done
say "   [1/6] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/6] $VPY is not there - STOP. Tell Claude."
if [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ] && [ "$(m5 "$P")" = "$P_TO" ]; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
for x in "$B:$B_FROM" "$C:$C_FROM" "$P:$P_FROM"; do f="${x%%:*}"; fr="${x#*:}"
  [ "$(m5 "$f")" = "$fr" ] || stop "!! [2/6] $f is $(m8 "$f"), not ${fr:0:8} - it changed after this kit was built: STOP. Tell Claude."; done
for n in "$FD/not_in_docterz.py" "$FD/evening_check.py" "$FD/slip_adjust.py" "$LIVE_DB"; do [ -f "$n" ] || stop "!! [2/6] $n is missing - STOP. Tell Claude."; done
say "   [2/6] the ground: day_check ${B_FROM:0:8}, register_push ${C_FROM:0:8}, docterz_pickup ${P_FROM:0:8}"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade" "$SCR/live_from"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" && \cp -p "$B" "$C" "$P" "$SCR/live_from/" || stop "!! [3/6] could not lay out the walk - nothing installed"
"$VPY" -c 'import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close()' "$LIVE_DB" "$SCR/db.copy" && chmod 600 "$SCR/db.copy" \
  || stop "!! [3/6] could not copy the database into the scratch - nothing installed"
py "$VPY" "$KDIR/make_s977.py" "$SCR/live_from" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/6] make_s977.py refused the live files - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/6] $n remade from the live bytes is not the kit's TO - nothing installed"; done
for n in $NAMES; do \cp "$KDIR/to/$n" "$SCR/new/"; done
(cd "$SCR" && "$VPY" -c 'import py_compile,sys
for f in sys.argv[2:]: py_compile.compile(f, cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/day_check.py" "$SCR/new/register_push.py" "$SCR/new/docterz_pickup.py") \
  || stop "!! [3/6] a file does not compile under $VPY - nothing installed"
W="$(py "$VPY" "$KDIR/walk_s977.py" "$SCR/new" "$SCR/db.copy")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q ", 0 FAIL" || { echo "$W" | grep -E "FAIL|Error" | head -8; stop "!! [3/6] the walk is not all green here - nothing installed"; }
WC="$(py "$VPY" "$KDIR/walk_s977.py" "$SCR/old" "$SCR/db.copy")"; rc=$?
[ "$rc" != 0 ] || stop "!! [3/6] the control (the walk on the live code as it is) did not go red - nothing installed"
if [ -n "${LIVE_CMD:-}" ]; then LV="$($LIVE_CMD)"; else LV="$(py "$VPY" "$KDIR/probe_s977.py" "$SCR/old" "$SCR/new" "$SCR/db.copy")"; fi
echo "$LV" | tail -1 | grep -q "^ALL PASS" || { echo "$LV" | tail -3; stop "!! [3/6] the live shape (a copy of the database, no push) is not green - nothing installed. Send a photo to Claude."; }
rm -f "$SCR/db.copy"
say "   [3/6] walk $(echo "$W" | tail -1 | sed 's/^WALK S977: //'); control red; three TO remade from the live bytes"
say "         the live shape (a copy, counts only): $(echo "$LV" | grep '^LIVE' | head -1 | cut -c1-230)"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/6]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for x in "$B:$B_FROM" "$C:$C_FROM" "$P:$P_FROM"; do f="${x%%:*}"; fr="${x#*:}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || stop "!! [4/6] the backup of $(basename "$f") did not read back - nothing placed"; done
quiet_minute
CHANGED=1
swap_in "$B" "$KDIR/to/day_check.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/6] day_check.py did not read back"
swap_in "$C" "$KDIR/to/register_push.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/6] register_push.py did not read back"
swap_in "$P" "$KDIR/to/docterz_pickup.py" && [ "$(m5 "$P")" = "$P_TO" ] || restore "[4/6] docterz_pickup.py did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/6] forced red (rehearsal)"
qs=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 120 "$VPY" -W ignore -B "$C" --sweep --quiet --db "$LIVE_DB" 2>&1); qrc=$?
QS_DONE=1
[ "$qrc" = 0 ] || restore "[5/6] the quiet sweep did not run ($(echo "$qs" | tail -1 | cut -c1-120))"
echo "$qs" | grep -q " error " && restore "[5/6] the quiet sweep met an error on a day ($(echo "$qs" | grep ' error ' | head -1 | cut -c1-120))"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d2=$(door /finance/clinic/check/mine); case "$d2" in 404|000|5*) restore "the day check answers $d2";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|day_check NOT mounted|register_push" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
st=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$C" --status --db "$LIVE_DB" 2>&1 | tail -1)
echo "$st" | grep -q "^REGPUSH S977 1: " || restore "[5/6] register_push --status did not run on the box's python ($st)"
pk=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B -c 'import docterz_pickup' 2>&1 | tail -1)
[ -z "$pk" ] || restore "[5/6] docterz_pickup.py does not import on the box's python ($pk)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/6] forced red (rehearsal)"
say "   [4/6] placed and read back: day_check $(m8 "$B"), register_push $(m8 "$C"), docterz_pickup $(m8 "$P")"
say "   [5/6] the quiet sweep: $(echo "$qs" | grep -c register_push) day(s) recorded, nothing pushed; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the day check $d2 (login-gated); the log clean"
FINISHED=1; CHANGED=0; release
say "   [6/6] ON: the next register Save is matched money to money. ($st)"
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S977_MORNING_REVENUE_MATCH.sh --undo"
