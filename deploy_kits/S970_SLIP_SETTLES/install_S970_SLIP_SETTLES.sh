#!/bin/bash
# install_S970_SLIP_SETTLES.sh -- S970 (the parent, S531, 27-Nov-2026; his "YES" 12:46 IST). A slip on his 'Slips not in Docterz'
#   list whose money the register holds is answered "Not entering in Docterz" by itself (login 'auto'): the day matches with no
#   tap and no back-dated Docterz entry. Never a row answered or undone before (an Undo is final); a slip Docterz carries later
#   leaves the list by itself, its answer with it. REGPUSH_AUTO_OUTSIDE=0 turns it off.
#   FILES: /root/finance/register_push.py a4e2549e (S968) -> TO . /root/finance/day_check.py b8007892 (S968) -> TO (the note's
#   words). clinic-finance is restarted (seconds). Any hour. The 5-minute check (cron # S968_REGISTER_PUSH, unchanged) does it.
#   [1/5] kit sums  [2/5] the ground (both FROM)  [3/5] HERE, with the box's own python: make_s970.py remakes both TO files from
#   the live bytes; the walk green on the TO and red on the FROM (the control); the live shape (a COPY of finance.db in the 0700
#   scratch, no push, counts only)  [4/5] backups, swaps, read-backs, restart, healthz 200, the day check answers, --status runs
#   [5/5] ON.  Any red after [4/5] began, or the run killed: all put back.  DRY=1: [1]-[3] only.  --undo: both files back,
#   restarted (answers already given stay on his list, each with its Undo).
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s970kit && cp -rp /root/deploy/repo/deploy_kits/S970_SLIP_SETTLES /tmp/s970kit && bash /tmp/s970kit/install_S970_SLIP_SETTLES.sh
set -u
KIT="S970_SLIP_SETTLES"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"
VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$FD/finance.db}"
B="$FD/day_check.py";     B_FROM="b80078927cfb481d24b3a7ae77f2348e"
C="$FD/register_push.py"; C_FROM="a4e2549e72954d1ed60599a77d20b6a1"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
B_TO="$(to day_check.py)"; C_TO="$(to register_push.py)"
SCR="$(mktemp -d /tmp/s970_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$1.bak_S970_${2:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s970"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
put_back() { local r=0; put_one "$C" "$C_FROM" || r=1; put_one "$B" "$B_FROM" || r=1; [ "$r" = 0 ] && CHANGED=0; return $r; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$FD/.day_check.py.s970" "$FD/.register_push.py.s970"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local x="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-600}" "$x" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$B")" = "$B_FROM" ] && [ "$(m5 "$C")" = "$C_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  for x in "$B $B_TO $B_FROM" "$C $C_TO $C_FROM"; do set -- $x; h="$(m5 "$1")"
    [ "$h" = "$2" ] || [ "$h" = "$3" ] || stop "!! --undo: $1 is ${h:0:8}, not S970's (a later kit?) - not undoing. Tell Claude."
    [ "$h" = "$3" ] || [ "$(m5 "$(bak "$1" "$3")")" = "$3" ] || stop "!! --undo: the backup of $(basename "$1") is not the FROM bytes - not undoing. Tell Claude."; done
  take_lock "--undo:" undo; CHANGED=1
  put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || true; h=$(wait200); release
  say "$KIT: UNDONE ($FSVC restarted, healthz $h; answers already given stay on your list, each with its Undo)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in day_check.py register_push.py; do [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/5] the kit's TO files are not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/5] $VPY is not there - STOP. Tell Claude."
if [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ]; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
[ "$(m5 "$B")" = "$B_FROM" ] || stop "!! [2/5] $B is $(m8 "$B"), not ${B_FROM:0:8} (S968's) - it changed after this kit was built: STOP. Tell Claude."
[ "$(m5 "$C")" = "$C_FROM" ] || stop "!! [2/5] $C is $(m8 "$C"), not ${C_FROM:0:8} (S968's) - it changed after this kit was built: STOP. Tell Claude."
for n in "$FD/not_in_docterz.py" "$LIVE_DB"; do [ -f "$n" ] || stop "!! [2/5] $n is missing - STOP. Tell Claude."; done
say "   [2/5] the ground: day_check ${B_FROM:0:8}, register_push ${C_FROM:0:8} (S968's)"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" || stop "!! [3/5] could not lay out the walk - nothing installed"
mkdir -p "$SCR/live_from" && \cp -p "$C" "$B" "$SCR/live_from/" || stop "!! [3/5] could not copy the live files - nothing installed"
py "$VPY" "$KDIR/make_s970.py" "$SCR/live_from" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s970.py refused the live files - nothing installed"; }
for n in day_check.py register_push.py; do [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/5] $n remade from the live bytes is not the kit's TO - nothing installed"; done
\cp "$KDIR/to/day_check.py" "$KDIR/to/register_push.py" "$SCR/new/"
(cd "$SCR" && "$VPY" -c 'import py_compile,sys
for f in sys.argv[2:]: py_compile.compile(f, cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/day_check.py" "$SCR/new/register_push.py") \
  || stop "!! [3/5] a file does not compile under $VPY - nothing installed"
W="$(py "$VPY" "$KDIR/walk_s970.py" walk "$SCR/new")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q "^ALL PASS" || { echo "$W" | grep -E "FAIL|Error" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
WC="$(py "$VPY" "$KDIR/walk_s970.py" walk "$SCR/old")"; rc=$?
[ "$rc" != 0 ] && echo "$WC" | tail -1 | grep -q "^RED" || stop "!! [3/5] the control (the walk on the live code as it is) did not go red - nothing installed"
if [ -n "${LIVE_CMD:-}" ]; then LV="$($LIVE_CMD)"; else LV="$(py "$VPY" "$KDIR/walk_s970.py" live "$KDIR/to" "$SCR/old" "$LIVE_DB")"; fi
echo "$LV" | tail -1 | grep -q "^ALL PASS" || { echo "$LV" | grep -E "^LIVE|FAIL" | head -4; stop "!! [3/5] the live shape (a copy of the database, no push) is not green - nothing installed. Send a photo to Claude."; }
say "   [3/5] walk $(echo "$W" | tail -1); control red; both TO remade from the live bytes"
say "         the live shape (a copy, no push, counts only): $(echo "$LV" | tail -1); $(echo "$LV" | grep '^LIVE' | head -1)"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for p in "B:$B_FROM" "C:$C_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || stop "!! [4/5] the backup of $(basename "$f") did not read back - nothing placed"; done
CHANGED=1
swap_in "$B" "$KDIR/to/day_check.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/5] day_check.py did not read back"
swap_in "$C" "$KDIR/to/register_push.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/5] register_push.py did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d2=$(door /finance/clinic/check/mine); case "$d2" in 404|000|5*) restore "the day check answers $d2";; esac
d3=$(door /finance/clinic/not-in-docterz); case "$d3" in 404|000|5*) restore "his not-in-Docterz list answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|day_check NOT mounted|register_push" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
st=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$C" --status --db "$LIVE_DB" 2>&1 | tail -1)
echo "$st" | grep -q "^REGPUSH S970 1: " || restore "[4/5] register_push --status did not run on the box's python ($st)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [4/5] placed and read back: day_check $(m8 "$B"), register_push $(m8 "$C");"
say "         $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the day check $d2, his list $d3 (login-gated); the log clean"
FINISHED=1; CHANGED=0; release
say "   [5/5] ON: within 5 minutes, each slip whose money is in the register is answered 'Not entering in Docterz' by itself. ($st)"
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S970_SLIP_SETTLES.sh --undo"
