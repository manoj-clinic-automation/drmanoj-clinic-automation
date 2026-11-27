#!/bin/bash
# install_S968_REGISTER_PUSH.sh -- S968 (the parent, S531, 27-Nov-2026; his "PROCEED" 10:40 IST). 26-Nov: a dressing (Rs 100 cash)
#   had no parchi and no Docterz entry; the day check carded it in the morning, but nobody was told. Now:
#   (1) Shavez and reception get a push the moment the register is saved (and every 5 min 08:00-21:55, when a day's lines change):
#       "<day>: N galti -- din ki jaanch" with the lines / "sab mile" / "sab galtiyan theek"; it opens their day check;
#   (2) the three records' heading no longer says "all agree" when cash or card differ (it read UPI alone);
#   (3) the "patient not found" card asks for the parchi too, and gives Shavez / Bhati "Parchi banayein".
#   FILES: /root/finance/clinic_register.py 321f659a -> TO . /root/finance/day_check.py 6f17979a (S962) -> TO . NEW
#   /root/finance/register_push.py . crontab + one line '# S968_REGISTER_PUSH'. clinic-finance is restarted (seconds). Any hour.
#   [1/5] kit sums  [2/5] the ground (both FROM, no register_push.py, no S968 cron line)  [3/5] HERE, with the box's own python:
#   make_s968.py remakes the two TO files from the live bytes; the walk all green on the TO and red on the FROM (the control); the
#   live shape (a COPY of finance.db in the 0700 scratch, no push, counts only)  [4/5] backups, swaps, read-backs, the cron line,
#   restart, healthz 200, the register and the day check answer  [5/5] the log clean; register_push --status runs.
#   Any red after [4/5] began, or the run killed: all put back.  DRY=1: [1]-[3] only.  --undo: both files back, register_push.py
#   removed (its table kept), the cron line removed, restarted.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s968kit && cp -rp /root/deploy/repo/deploy_kits/S968_REGISTER_PUSH /tmp/s968kit && bash /tmp/s968kit/install_S968_REGISTER_PUSH.sh
set -u
KIT="S968_REGISTER_PUSH"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"; PD="${PD:-$ROOT/portal}"
VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"; LIVE_DB="${LIVE_DB:-$FD/finance.db}"
A="$FD/clinic_register.py"; A_FROM="321f659a7310323c7c3003bc044a595a"
B="$FD/day_check.py";       B_FROM="6f17979a3e108b2e61f427b44aa78b96"
C="$FD/register_push.py"
MARK="# S968_REGISTER_PUSH"
CLINE="*/5 8-21 * * * [ -e /root/finance/_off/ALL_OFF ] || TZ=Asia/Kolkata /root/wa/venv/bin/python3 -B /root/finance/register_push.py --sweep >> /root/finance/logs/register_push.log 2>&1 $MARK the day check told to Shavez + reception when a day's lines change (every 5 min, 08:00-21:55)"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
A_TO="$(to clinic_register.py)"; B_TO="$(to day_check.py)"; C_TO="$(to register_push.py)"
SCR="$(mktemp -d /tmp/s968_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$1.bak_S968_${2:0:8}"; }
CBAK="$FD/crontab.bak_S968"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
has_cron() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s968"
  if [ -f "$1" ]; then \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"
  else \cp "$2" "$t" && chmod --reference="$A" "$t" && chown --reference="$A" "$t" && mv -f "$t" "$1"; fi; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
cron_out() { has_cron || return 0; "$CRONTAB" -l 2>/dev/null | grep -vF "$MARK" > "$SCR/cron.out" && "$CRONTAB" "$SCR/cron.out" && ! has_cron && say "   the S968 cron line removed"; }
put_back() { local r=0
  cron_out || r=1
  put_one "$A" "$A_FROM" || r=1; put_one "$B" "$B_FROM" || r=1
  if [ -f "$C" ]; then if [ "$(m5 "$C")" = "$C_TO" ]; then rm -f "$C" && say "   register_push.py removed"; else say "   !! register_push.py is $(m8 "$C"), not S968's - left"; r=1; fi; fi
  [ "$r" = 0 ] && CHANGED=0; return $r; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$FD/.clinic_register.py.s968" "$FD/.day_check.py.s968" "$FD/.register_push.py.s968"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local x="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-600}" "$x" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$A")" = "$A_FROM" ] && [ "$(m5 "$B")" = "$B_FROM" ] && [ ! -f "$C" ] && ! has_cron && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  for x in "$A $A_TO $A_FROM" "$B $B_TO $B_FROM"; do set -- $x; h="$(m5 "$1")"
    [ "$h" = "$2" ] || [ "$h" = "$3" ] || stop "!! --undo: $1 is ${h:0:8}, not S968's (a later kit?) - not undoing. Tell Claude."
    [ "$h" = "$3" ] || [ "$(m5 "$(bak "$1" "$3")")" = "$3" ] || stop "!! --undo: the backup of $(basename "$1") is not the FROM bytes - not undoing. Tell Claude."; done
  take_lock "--undo:" undo; CHANGED=1
  put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || true; h=$(wait200); release
  say "$KIT: UNDONE ($FSVC restarted, healthz $h; the register_push table is kept)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in clinic_register.py day_check.py register_push.py; do [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/5] the kit's TO files are not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/5] $VPY is not there - STOP. Tell Claude."
if [ "$(m5 "$A")" = "$A_TO" ] && [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ] && has_cron; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
[ "$(m5 "$A")" = "$A_FROM" ] || stop "!! [2/5] $A is $(m8 "$A"), not ${A_FROM:0:8} - it changed after this kit was built: STOP. Tell Claude."
[ "$(m5 "$B")" = "$B_FROM" ] || stop "!! [2/5] $B is $(m8 "$B"), not ${B_FROM:0:8} (S962's) - it changed after this kit was built: STOP. Tell Claude."
[ -e "$C" ] && stop "!! [2/5] $C already exists - STOP. Tell Claude."
for n in "$FD/evening_check.py" "$PD/callback_clock.py" "$LIVE_DB"; do [ -f "$n" ] || stop "!! [2/5] $n is missing - STOP. Tell Claude."; done
has_cron && stop "!! [2/5] the crontab already holds an S968 line - STOP. Tell Claude."
"$CRONTAB" -l > "$SCR/cron.now" 2>/dev/null || stop "!! [2/5] the crontab could not be read - STOP. Tell Claude."
say "   [2/5] the ground: clinic_register ${A_FROM:0:8}, day_check ${B_FROM:0:8} (S962); no register_push.py; no S968 cron line"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py "$VPY" "$KDIR/make_s968.py" "$A" "$B" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s968.py refused the live files - nothing installed"; }
for n in clinic_register.py day_check.py; do [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/5] $n remade from the live bytes is not the kit's TO - nothing installed"; done
\cp "$KDIR/to/clinic_register.py" "$KDIR/to/day_check.py" "$KDIR/to/register_push.py" "$SCR/new/"
(cd "$SCR" && "$VPY" -c 'import py_compile,sys
for f in sys.argv[2:]: py_compile.compile(f, cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/clinic_register.py" "$SCR/new/day_check.py" "$SCR/new/register_push.py") \
  || stop "!! [3/5] a file does not compile under $VPY - nothing installed"
W="$(py "$VPY" "$KDIR/walk_s968.py" walk "$SCR/new")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q "^ALL PASS$" || { echo "$W" | grep -E "FAIL|Error" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
WC="$(py "$VPY" "$KDIR/walk_s968.py" walk "$SCR/old")"; rc=$?
[ "$rc" != 0 ] && echo "$WC" | grep -q "FAIL  kit S968 marked" && ! echo "$WC" | grep -q "^Traceback" || stop "!! [3/5] the control (the walk on the live code as it is) did not go red - nothing installed"
if [ -n "${LIVE_CMD:-}" ]; then LV="$($LIVE_CMD)"; else LV="$(py "$VPY" "$KDIR/walk_s968.py" live "$SCR/new" "$LIVE_DB")"; fi
echo "$LV" | tail -1 | grep -q "^ALL PASS$" || { echo "$LV" | grep -E "^LIVE|FAIL" | head -4; stop "!! [3/5] the live shape (a copy of the database, no push) did not judge every recent day - nothing installed. Send a photo to Claude."; }
say "   [3/5] walk ALL PASS ($(echo "$W" | grep -c 'PASS  ')); control red; both TO remade from the live bytes"
say "         the live shape (a copy, no push, counts only): $(echo "$LV" | grep '^LIVE' | head -1)"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for p in "A:$A_FROM" "B:$B_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || stop "!! [4/5] the backup of $(basename "$f") did not read back - nothing placed"; done
\cp "$SCR/cron.now" "$CBAK" && chmod 600 "$CBAK" || stop "!! [4/5] the crontab backup could not be written - nothing placed"
CHANGED=1
swap_in "$C" "$KDIR/to/register_push.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/5] register_push.py did not read back"
swap_in "$B" "$KDIR/to/day_check.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/5] day_check.py did not read back"
swap_in "$A" "$KDIR/to/clinic_register.py" && [ "$(m5 "$A")" = "$A_TO" ] || restore "[4/5] clinic_register.py did not read back"
"$CRONTAB" -l > "$SCR/cron.again" 2>/dev/null && cmp -s "$SCR/cron.now" "$SCR/cron.again" || restore "[4/5] the crontab changed while the kit was checking - run the line again"
{ cat "$SCR/cron.now"; echo "$CLINE"; } > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" && has_cron || restore "[4/5] the cron line was not added"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" = "$(( $(grep -c . "$SCR/cron.now") + 1 ))" ] || restore "[4/5] the crontab is not the old one plus one line"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/clinic/register); case "$d1" in 404|000|5*) restore "the register answers $d1";; esac
d2=$(door /finance/clinic/check/mine); case "$d2" in 404|000|5*) restore "the day check answers $d2";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|day_check NOT mounted|clinic_register|register_push" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
st=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$C" --status --db "$LIVE_DB" 2>&1 | tail -1)
echo "$st" | grep -q "^REGPUSH S968 1: " || restore "[4/5] register_push --status did not run on the box's python ($st)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [4/5] placed and read back: clinic_register $(m8 "$A"), day_check $(m8 "$B"), register_push $(m8 "$C"); the cron line in;"
say "         $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the register $d1, the day check $d2 (login-gated); the log clean"
FINISHED=1; CHANGED=0; release
say "   [5/5] ON: the next Save of a register, and the 5-minute check, tell Shavez and reception by push. ($st)"
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S968_REGISTER_PUSH.sh --undo"
