#!/bin/bash
# install_S951_YESTERDAY_CARRY.sh -- S951 (the parent, S517, 25-Nov-2026; D1063, his "yes" 20:43 IST 24-Nov, widened by his
#   word 10:02 IST 25-Nov): EVERY missed call of yesterday still unresolved (no connected call, no WhatsApp from him, no
#   Docterz visit since) comes onto today's lists on the staff Call Console (/portal/console/staff); from 21:00 it reads
#   "Missed after hours". ONE file: /root/portal/calls_staff.py 05caf1c3 (S948) -> TO. clinic-portal is restarted (a few
#   seconds); the doctor's auto-fix is paused for the run. Runs at any hour (his word 10:49 IST 25-Nov).
#   [1/5] kit sums  [2/5] the ground (the live file is S948's, or already S951's)  [3/5] the walk HERE (made-up stores,
#   the box's own python, the live calls_console.py / ring_*.py): walk_s951 all green on the TO, red on the FROM on the
#   carry itself (the control); S948's own walk still 0 failed on the TO; his page byte-equal FROM vs TO; the staff lists
#   byte-equal FROM vs TO when nobody missed yesterday; make_s951.py remade from the live bytes = the kit's TO  [4/5]
#   backup + swap + read-back + restart + the pages answer  [5/5] the journal holds no "calls_staff NOT mounted".  Any red
#   after [4/5] began, or the run killed: the file put back, the portal restarted.  DRY=1: [1]-[3] only.  --undo: the
#   backup back, only where the file is still S951's.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s951kit && cp -rp /root/deploy/repo/deploy_kits/S951_YESTERDAY_CARRY /tmp/s951kit && bash /tmp/s951kit/install_S951_YESTERDAY_CARRY.sh
set -u
KIT="S951_YESTERDAY_CARRY"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"
N="calls_staff.py"; FROM_MD5="05caf1c32db2e25b7b0723292c234572"
TO_MD5="$(awk -v f="to/$N" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
SCR="$(mktemp -d /tmp/s951_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date '+%F %T')"
BAK="$PD/$N.bak_S951_05caf1c3"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hget /portal/health); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s951"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_back() { if [ "$(m5 "$BAK")" = "$FROM_MD5" ] && swap_in "$PD/$N" "$BAK" && [ "$(m5 "$PD/$N")" = "$FROM_MD5" ]; then say "   $N back: $(m8 "$PD/$N")"; CHANGED=0; return 0; fi
  say "   !! $N NOT back: $(m8 "$PD/$N") (backup $(m8 "$BAK"), expected 05caf1c3)"; return 1; }
restore() { say "!! RED ($1) - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true
  say "   $PSVC restarted, portal health $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$PD/.$N.s951"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  h="$(m5 "$PD/$N")"
  [ "$h" = "$FROM_MD5" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$h" = "$TO_MD5" ] || stop "!! --undo: $PD/$N is ${h:0:8}, not S951's (a later kit?) - not undoing. Tell Claude."
  [ "$(m5 "$BAK")" = "$FROM_MD5" ] || stop "!! --undo: the backup $BAK is $(m8 "$BAK"), not S948's bytes - not undoing. Tell Claude."
  take_lock "--undo:" undo; CHANGED=1; put_back || { "$SYSTEMCTL" restart "$PSVC" || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  "$SYSTEMCTL" restart "$PSVC" || true; h=$(wait200); release
  say "$KIT: UNDONE ($PSVC restarted, portal health $h)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
[ -n "$TO_MD5" ] && [ "$(m5 "$KDIR/to/$N")" = "$TO_MD5" ] || stop "!! [1/5] the kit's $N is not as built - nothing installed"
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
for n in calls_console.py ring_outcome.py ring_common.py; do [ -f "$PD/$n" ] || stop "!! [2/5] $PD/$n is missing - STOP. Tell Claude."; done
h="$(m5 "$PD/$N")"
[ "$h" = "$TO_MD5" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$h" = "$FROM_MD5" ] || stop "!! [2/5] $PD/$N is ${h:0:8}, not 05caf1c3 (S948's) - it changed after this kit was built: STOP. Tell Claude."
say "   [2/5] the ground: $N is S948's (05caf1c3)"
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade"
\cp "$PD/$N" "$PD/calls_console.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$SCR/from/"
\cp "$KDIR/to/$N" "$PD/calls_console.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$SCR/to/"
pya "$KDIR/make_s951.py" "$PD/$N" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s951.py refused the live file - nothing installed"; }
[ "$(m5 "$SCR/remade/$N")" = "$TO_MD5" ] || stop "!! [3/5] $N remade from the live bytes is not the kit's TO - nothing installed"
pya "$KDIR/walk_s951.py" walk "$SCR/to" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
pya "$KDIR/walk_s951.py" walk "$SCR/from" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL  A 21:40 -> Incoming missed" "$SCR/ctl.txt" && ! grep -q Traceback "$SCR/ctl.txt" \
  || stop "!! [3/5] the control (the walk on the FROM code) did not go red on the carry itself - the walk proves nothing here; nothing installed"
pya "$KDIR/walk_s948.py" walk "$SCR/to" > "$SCR/w48.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w48.txt" | grep -qE "^[0-9]+ checks, 0 failed$" || { grep -E "FAIL|Error" "$SCR/w48.txt" | head -8; stop "!! [3/5] S948's own walk is not all green on the TO - nothing installed"; }
pya "$KDIR/walk_s948.py" dump "$SCR/from" "$SCR/from.dump" >/dev/null && pya "$KDIR/walk_s948.py" dump "$SCR/to" "$SCR/to.dump" >/dev/null \
  && [ -s "$SCR/from.dump" ] && cmp -s "$SCR/from.dump" "$SCR/to.dump" || stop "!! [3/5] the owner's page is not byte-equal before/after - nothing installed"
pya "$KDIR/walk_s951.py" lists "$SCR/from" "$SCR/from.lists" >/dev/null && pya "$KDIR/walk_s951.py" lists "$SCR/to" "$SCR/to.lists" >/dev/null \
  && [ -s "$SCR/from.lists" ] && cmp -s "$SCR/from.lists" "$SCR/to.lists" || stop "!! [3/5] the staff lists with nobody missed yesterday are not byte-equal before/after - nothing installed"
say "   [3/5] walk ALL PASS ($(grep -c PASS "$SCR/walk.txt")); control red; S948's $(tail -1 "$SCR/w48.txt"); his page and the plain lists byte-equal; the TO remade from the live bytes"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
\cp -p "$PD/$N" "$BAK" && chmod 600 "$BAK" && [ "$(m5 "$BAK")" = "$FROM_MD5" ] || restore "[4/5] the backup did not read back"
CHANGED=1
swap_in "$PD/$N" "$KDIR/to/$N" && [ "$(m5 "$PD/$N")" = "$TO_MD5" ] || restore "[4/5] $N did not read back as S951's"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1 after the restart"
for u in /portal/console /portal/console/staff /portal/console/staff/api/lists /portal/console/api/mycard /portal/; do pg=$(hget "$u")
  case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
say "   [4/5] placed and read back: $N $(m8 "$PD/$N"); $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $p1, the pages answer"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else jr="$("$JOURNAL" -u "$PSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "calls_staff NOT mounted" && restore "[5/5] the journal says calls_staff NOT mounted"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [5/5] the journal holds no 'calls_staff NOT mounted'"
FINISHED=1; release
say "$KIT: INSTALLED - yesterday's unresolved missed calls are on today's staff lists. Undo: bash $KDIR/install_S951_YESTERDAY_CARRY.sh --undo"
