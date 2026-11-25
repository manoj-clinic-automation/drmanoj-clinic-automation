#!/bin/bash
# install_S953_STAFF_NOTIFY.sh -- S953 (the parent, S520, 25-Nov-2026; D1067 "notifications first"): the call-back clock's taps
#   open the new staff Call Console on the right tab; its 30/60-minute stages follow the page's Incoming missed tab (today's +
#   yesterday's carried misses); two new pushes to the phone staff on duty -- "Call again due" and "WhatsApp waiting".
#   TWO files: /root/portal/callback_clock.py 70eb1197 (S796) -> TO, /root/portal/calls_staff.py 1cb4941f (S951) -> TO (the page
#   reads ?tab=). clinic-portal is restarted (a few seconds); the doctor's auto-fix is paused for the run. Runs at any hour.
#   [1/5] kit sums  [2/5] the ground (both files S796 / S951's, or both already S953's)  [3/5] the walks HERE (made-up stores, the
#   box's own python, the live calls_console.py / ring_*.py): walk_s953 all green on the TO and red on the FROM (the control);
#   S951's and S948's own walks green on the TO; his page and the staff lists byte-equal FROM vs TO; make_s953.py remade both TO
#   files from the live bytes; the new clock --dry on the REAL stores (read-only, counts only) says "lists ok"  [4/5] backups +
#   swaps + read-backs + restart + the pages answer + the installed clock --dry says "lists ok"  [5/5] the journal holds no
#   "calls_staff NOT mounted".  Any red after [4/5] began, or the run killed: both files put back, the portal restarted.
#   DRY=1: [1]-[3] only.  --undo: both backups back, only where both files are still S953's.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s953kit && cp -rp /root/deploy/repo/deploy_kits/S953_STAFF_NOTIFY /tmp/s953kit && bash /tmp/s953kit/install_S953_STAFF_NOTIFY.sh
set -u
KIT="S953_STAFF_NOTIFY"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"
CCDB="${CCDB:-$ROOT/wa/console.db}"; CCRV="${CCRV:-$ROOT/wa/console_reviews.db}"
A="calls_staff.py"; A_FROM="1cb4941f3d387abba93f76e650d78fa1"
B="callback_clock.py"; B_FROM="70eb11972362eee87a9f7d056e04cae5"
A_TO="$(awk -v f="to/$A" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; B_TO="$(awk -v f="to/$B" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
SCR="$(mktemp -d /tmp/s953_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date '+%F %T')"
A_BAK="$PD/$A.bak_S953_1cb4941f"; B_BAK="$PD/$B.bak_S953_70eb1197"
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
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s953"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local f="$1" bak="$2" from="$3"
  [ "$(m5 "$PD/$f")" = "$from" ] && { say "   $f is the FROM: $(m8 "$PD/$f")"; return 0; }
  if [ "$(m5 "$bak")" = "$from" ] && swap_in "$PD/$f" "$bak" && [ "$(m5 "$PD/$f")" = "$from" ]; then say "   $f back: $(m8 "$PD/$f")"; return 0; fi
  say "   !! $f NOT back: $(m8 "$PD/$f") (backup $(m8 "$bak"), expected ${from:0:8})"; return 1; }
put_back() { local r=0; put_one "$A" "$A_BAK" "$A_FROM" || r=1; put_one "$B" "$B_BAK" "$B_FROM" || r=1; [ "$r" = 0 ] && CHANGED=0; return $r; }
restore() { say "!! RED ($1) - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true
  say "   $PSVC restarted, portal health $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$PD/.$A.s953" "$PD/.$B.s953"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }
clockdry() { if [ -n "${CLOCKDRY_CMD:-}" ]; then $CLOCKDRY_CMD "$1"; else (cd "$SCR" && CC_CONSOLE_DB="$CCDB" CC_REVIEWS_DB="$CCRV" CC_STORE="$SCR/never_written.db" \
  RING_PORTAL_DIR="$PD" TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 120 "$APY" -B "$1" --dry 2>&1 | tail -3); fi; }

if [ "${1:-}" = "--undo" ]; then
  ha="$(m5 "$PD/$A")"; hb="$(m5 "$PD/$B")"
  [ "$ha" = "$A_FROM" ] && [ "$hb" = "$B_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$ha" = "$A_TO" ] || [ "$ha" = "$A_FROM" ] || stop "!! --undo: $PD/$A is ${ha:0:8}, not S953's (a later kit?) - not undoing. Tell Claude."
  [ "$hb" = "$B_TO" ] || [ "$hb" = "$B_FROM" ] || stop "!! --undo: $PD/$B is ${hb:0:8}, not S953's (a later kit?) - not undoing. Tell Claude."
  [ "$ha" = "$A_FROM" ] || [ "$(m5 "$A_BAK")" = "$A_FROM" ] || stop "!! --undo: the backup $A_BAK is $(m8 "$A_BAK"), not S951's bytes - not undoing. Tell Claude."
  [ "$hb" = "$B_FROM" ] || [ "$(m5 "$B_BAK")" = "$B_FROM" ] || stop "!! --undo: the backup $B_BAK is $(m8 "$B_BAK"), not S796's bytes - not undoing. Tell Claude."
  take_lock "--undo:" undo; CHANGED=1; put_back || { "$SYSTEMCTL" restart "$PSVC" || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  "$SYSTEMCTL" restart "$PSVC" || true; h=$(wait200); release
  say "$KIT: UNDONE ($PSVC restarted, portal health $h)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
[ -n "$A_TO" ] && [ "$(m5 "$KDIR/to/$A")" = "$A_TO" ] && [ -n "$B_TO" ] && [ "$(m5 "$KDIR/to/$B")" = "$B_TO" ] || stop "!! [1/5] the kit's TO files are not as built - nothing installed"
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
for n in calls_console.py ring_outcome.py ring_common.py; do [ -f "$PD/$n" ] || stop "!! [2/5] $PD/$n is missing - STOP. Tell Claude."; done
ha="$(m5 "$PD/$A")"; hb="$(m5 "$PD/$B")"
[ "$ha" = "$A_TO" ] && [ "$hb" = "$B_TO" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$ha" = "$A_FROM" ] || stop "!! [2/5] $PD/$A is ${ha:0:8}, not 1cb4941f (S951's) - it changed after this kit was built: STOP. Tell Claude."
[ "$hb" = "$B_FROM" ] || stop "!! [2/5] $PD/$B is ${hb:0:8}, not 70eb1197 (S796's) - it changed after this kit was built: STOP. Tell Claude."
cl="$(if [ -n "${CRON_CMD:-}" ]; then $CRON_CMD; else crontab -l 2>/dev/null; fi | grep -v '^[[:space:]]*#' | grep "$PD/$B")"
[ -n "$cl" ] || stop "!! [2/5] no crontab line runs $PD/$B - STOP. Tell Claude."
echo "$cl" | grep -q "$APY " || stop "!! [2/5] the crontab line for $B does not run $APY (the python with the portal's modules) - STOP. Tell Claude."
say "   [2/5] the ground: $A is S951's (1cb4941f), $B is S796's (70eb1197); its crontab line runs $APY"
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade"
\cp "$PD/$A" "$PD/$B" "$PD/calls_console.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$SCR/from/"
\cp "$KDIR/to/$A" "$KDIR/to/$B" "$PD/calls_console.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$SCR/to/"
pya "$KDIR/make_s953.py" "$PD/$A" "$PD/$B" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s953.py refused the live files - nothing installed"; }
[ "$(m5 "$SCR/remade/$A")" = "$A_TO" ] && [ "$(m5 "$SCR/remade/$B")" = "$B_TO" ] || stop "!! [3/5] the files remade from the live bytes are not the kit's TO - nothing installed"
pya "$KDIR/walk_s953.py" walk "$SCR/to" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
pya "$KDIR/walk_s953.py" walk "$SCR/from" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL  stage 1 -> the phone staff, tap opens /portal/console/staff?tab=missed" "$SCR/ctl.txt" && ! grep -q Traceback "$SCR/ctl.txt" \
  || stop "!! [3/5] the control (the walk on the FROM code) did not go red - the walk proves nothing here; nothing installed"
pya "$KDIR/walk_s951.py" walk "$SCR/to" > "$SCR/w51.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w51.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/w51.txt" | head -8; stop "!! [3/5] S951's own walk is not all green on the TO - nothing installed"; }
pya "$KDIR/walk_s948.py" walk "$SCR/to" > "$SCR/w48.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w48.txt" | grep -qE "^[0-9]+ checks, 0 failed$" || { grep -E "FAIL|Error" "$SCR/w48.txt" | head -8; stop "!! [3/5] S948's own walk is not all green on the TO - nothing installed"; }
pya "$KDIR/walk_s948.py" dump "$SCR/from" "$SCR/from.dump" >/dev/null && pya "$KDIR/walk_s948.py" dump "$SCR/to" "$SCR/to.dump" >/dev/null \
  && [ -s "$SCR/from.dump" ] && cmp -s "$SCR/from.dump" "$SCR/to.dump" || stop "!! [3/5] the owner's page is not byte-equal before/after - nothing installed"
pya "$KDIR/walk_s951.py" lists "$SCR/from" "$SCR/from.lists" >/dev/null && pya "$KDIR/walk_s951.py" lists "$SCR/to" "$SCR/to.lists" >/dev/null \
  && [ -s "$SCR/from.lists" ] && cmp -s "$SCR/from.lists" "$SCR/to.lists" || stop "!! [3/5] the staff lists are not byte-equal before/after - nothing installed"
d1="$(clockdry "$KDIR/to/$B")"
echo "$d1" | grep -q "^DRY .*lists ok" || { echo "$d1"; stop "!! [3/5] the new clock's --dry on the real stores did not read the staff lists - nothing installed"; }
say "   [3/5] walk ALL PASS ($(grep -c PASS "$SCR/walk.txt")); control red; S951's ALL PASS; S948's $(tail -1 "$SCR/w48.txt"); his page and the lists byte-equal; both TO remade from the live bytes"
say "         the new clock on the real stores (read-only): $(echo "$d1" | grep '^DRY' | sed 's/^DRY [0-9-]* [0-9:]*: //')"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
\cp -p "$PD/$A" "$A_BAK" && chmod 600 "$A_BAK" && [ "$(m5 "$A_BAK")" = "$A_FROM" ] || restore "[4/5] the backup of $A did not read back"
\cp -p "$PD/$B" "$B_BAK" && chmod 600 "$B_BAK" && [ "$(m5 "$B_BAK")" = "$B_FROM" ] || restore "[4/5] the backup of $B did not read back"
CHANGED=1
swap_in "$PD/$B" "$KDIR/to/$B" && [ "$(m5 "$PD/$B")" = "$B_TO" ] || restore "[4/5] $B did not read back as S953's"
swap_in "$PD/$A" "$KDIR/to/$A" && [ "$(m5 "$PD/$A")" = "$A_TO" ] || restore "[4/5] $A did not read back as S953's"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1 after the restart"
for u in /portal/console /portal/console/staff /portal/console/staff/api/lists /portal/console/api/mycard /portal/; do pg=$(hget "$u")
  case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
d2="$(clockdry "$PD/$B")"
echo "$d2" | grep -q "^DRY .*lists ok" || { echo "$d2"; restore "[4/5] the installed clock's --dry did not read the staff lists"; }
say "   [4/5] placed and read back: $A $(m8 "$PD/$A"), $B $(m8 "$PD/$B"); $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $p1, the pages answer, the clock reads the lists"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else jr="$("$JOURNAL" -u "$PSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "calls_staff NOT mounted" && restore "[5/5] the journal says calls_staff NOT mounted"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [5/5] the journal holds no 'calls_staff NOT mounted'"
FINISHED=1; release
say "$KIT: INSTALLED - the clock's taps open the staff Call Console; Call again due and WhatsApp waiting go to the staff on duty. Undo: bash $KDIR/install_S953_STAFF_NOTIFY.sh --undo"
