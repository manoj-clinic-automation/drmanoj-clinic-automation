#!/bin/bash
# install_S955_RECEPTION_CONSOLE.sh -- S955 (the parent, S521, 25-Nov-2026; D1068, his word 17:05 IST 25-Nov "Reception mobile
#   required"): the reception mobile's login opens the staff Call Console (My Call Console); its "Handled today" is the reception
#   mobile's own calls of today; its tile is granted by name; the call-back clock's taps for reception now open the new page
#   (no clock change -- the clock asks the page whom it admits).
#   TWO files: /root/portal/calls_staff.py f7e77203 (S953) -> TO, /root/portal/tile_grants.json v48 4a23e3c4 -> v49 TO.
#   clinic-portal is restarted (a few seconds); the doctor's auto-fix is paused for the run. Runs at any hour.
#   [1/5] kit sums  [2/5] the ground (both files S953's / v48, or both already S955's)  [3/5] HERE, with the box's own python and
#   the live calls_console.py / ring_*.py / callback_clock.py: make_s955.py remakes both TO files from the live bytes; walk_s955
#   all green on the TO and red on the FROM (the control); S948's, S951's walks green on the TO; S953's walk green on the TO with
#   PORTAL_STAFF_CONSOLE_RECEPTION=0 (everything but reception's landing unchanged); his page and the staff lists byte-equal FROM
#   vs TO; with the LIVE settings the TO page admits the reception login, and the clock --dry on the real stores says "lists ok"
#   [4/5] backups + swaps + read-backs + restart + the pages answer + the installed clock --dry says "lists ok" and admits
#   reception  [5/5] the journal holds no "calls_staff NOT mounted".  Any red after [4/5] began, or the run killed: both files
#   put back, the portal restarted.  DRY=1: [1]-[3] only.  --undo: both backups back, only where both files are still S955's.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s955kit && cp -rp /root/deploy/repo/deploy_kits/S955_RECEPTION_CONSOLE /tmp/s955kit && bash /tmp/s955kit/install_S955_RECEPTION_CONSOLE.sh
set -u
KIT="S955_RECEPTION_CONSOLE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"
CCDB="${CCDB:-$ROOT/wa/console.db}"; CCRV="${CCRV:-$ROOT/wa/console_reviews.db}"
A="calls_staff.py"; A_FROM="f7e77203bec9e58274af16c1475b9911"
B="tile_grants.json"; B_FROM="4a23e3c410754e1a5ba2a74b35cf14fb"
C="callback_clock.py"
A_TO="$(awk -v f="to/$A" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; B_TO="$(awk -v f="to/$B" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"
SCR="$(mktemp -d /tmp/s955_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date '+%F %T')"
A_BAK="$PD/$A.bak_S955_f7e77203"; B_BAK="$PD/$B.bak_S955_4a23e3c4"
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
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s955"
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
  release; rm -rf "${SCR:?}"; rm -f "$PD/.$A.s955" "$PD/.$B.s955"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }
# the clock --dry (read-only, counts only) and the reception check, with the page code of dir $1 and the LIVE settings
clockdry() { if [ -n "${CLOCKDRY_CMD:-}" ]; then $CLOCKDRY_CMD "$1"; else (cd "$SCR" && CC_CONSOLE_DB="$CCDB" CC_REVIEWS_DB="$CCRV" CC_STORE="$SCR/never_written.db" \
  RING_PORTAL_DIR="$1" TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 120 "$APY" -B "$1/$C" --dry 2>&1 | tail -3); fi; }
recadm() { if [ -n "${RECADM_CMD:-}" ]; then $RECADM_CMD "$1"; else (cd "$SCR" && RING_PORTAL_DIR="$1" RING_AGENTS_FILE="$PD/ring_agents.json" TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$APY" -B -c '
import os, sys
d = os.environ["RING_PORTAL_DIR"]; sys.path.insert(0, d)
import callback_clock as CB
CB.PORTAL_DIR = d
a = CB.admitted()
import calls_staff as CS
try:
    import ring_outcome as RO
    ag = "yes" if RO.ivr_agent("reception") else "NO (its Call buttons will say so; tell Claude)"
except Exception:
    ag = "not read"
print("RECEPTION_ADMITTED %s (%s); its MyOperator agent for click-to-call: %s" % (bool(a and a("reception")), CS.reception_key() if hasattr(CS, "reception_key") else "-", ag))
' 2>&1 | tail -1); fi; }

if [ "${1:-}" = "--undo" ]; then
  ha="$(m5 "$PD/$A")"; hb="$(m5 "$PD/$B")"
  [ "$ha" = "$A_FROM" ] && [ "$hb" = "$B_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$ha" = "$A_TO" ] || [ "$ha" = "$A_FROM" ] || stop "!! --undo: $PD/$A is ${ha:0:8}, not S955's (a later kit?) - not undoing. Tell Claude."
  [ "$hb" = "$B_TO" ] || [ "$hb" = "$B_FROM" ] || stop "!! --undo: $PD/$B is ${hb:0:8}, not S955's (a later change?) - not undoing. Tell Claude."
  [ "$ha" = "$A_FROM" ] || [ "$(m5 "$A_BAK")" = "$A_FROM" ] || stop "!! --undo: the backup $A_BAK is $(m8 "$A_BAK"), not S953's bytes - not undoing. Tell Claude."
  [ "$hb" = "$B_FROM" ] || [ "$(m5 "$B_BAK")" = "$B_FROM" ] || stop "!! --undo: the backup $B_BAK is $(m8 "$B_BAK"), not v48's bytes - not undoing. Tell Claude."
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
for n in calls_console.py ring_outcome.py ring_common.py "$C"; do [ -f "$PD/$n" ] || stop "!! [2/5] $PD/$n is missing - STOP. Tell Claude."; done
ha="$(m5 "$PD/$A")"; hb="$(m5 "$PD/$B")"
[ "$ha" = "$A_TO" ] && [ "$hb" = "$B_TO" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$ha" = "$A_FROM" ] || stop "!! [2/5] $PD/$A is ${ha:0:8}, not f7e77203 (S953's) - it changed after this kit was built: STOP. Tell Claude."
[ "$hb" = "$B_FROM" ] || stop "!! [2/5] $PD/$B is ${hb:0:8}, not 4a23e3c4 (v48) - it changed after this kit was built: STOP. Tell Claude."
say "   [2/5] the ground: $A is S953's (f7e77203), $B is v48 (4a23e3c4)"
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade"
for d in from to; do \cp "$PD/calls_console.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$PD/$C" "$SCR/$d/"; done
\cp "$PD/$A" "$SCR/from/"; \cp "$KDIR/to/$A" "$SCR/to/"
pya "$KDIR/make_s955.py" "$PD/$A" "$PD/$B" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s955.py refused the live files - nothing installed"; }
[ "$(m5 "$SCR/remade/$A")" = "$A_TO" ] && [ "$(m5 "$SCR/remade/$B")" = "$B_TO" ] || stop "!! [3/5] the files remade from the live bytes are not the kit's TO - nothing installed"
pya "$KDIR/walk_s955.py" walk "$SCR/to" "$PD/$B" "$KDIR/to/$B" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
pya "$KDIR/walk_s955.py" walk "$SCR/from" "$PD/$B" "$PD/$B" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL  reception -> 200, its own page" "$SCR/ctl.txt" && ! grep -q Traceback "$SCR/ctl.txt" \
  || stop "!! [3/5] the control (the walk on the FROM code) did not go red - the walk proves nothing here; nothing installed"
pya "$KDIR/walk_s948.py" walk "$SCR/to" > "$SCR/w48.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w48.txt" | grep -qE "^[0-9]+ checks, 0 failed$" || { grep -E "FAIL|Error" "$SCR/w48.txt" | head -8; stop "!! [3/5] S948's own walk is not all green on the TO - nothing installed"; }
pya "$KDIR/walk_s951.py" walk "$SCR/to" > "$SCR/w51.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w51.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/w51.txt" | head -8; stop "!! [3/5] S951's own walk is not all green on the TO - nothing installed"; }
(export PORTAL_STAFF_CONSOLE_RECEPTION=0; pya "$KDIR/walk_s953.py" walk "$SCR/to") > "$SCR/w53.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w53.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/w53.txt" | head -8; stop "!! [3/5] S953's own walk (reception setting 0) is not all green on the TO - nothing installed"; }
pya "$KDIR/walk_s948.py" dump "$SCR/from" "$SCR/from.dump" >/dev/null && pya "$KDIR/walk_s948.py" dump "$SCR/to" "$SCR/to.dump" >/dev/null \
  && [ -s "$SCR/from.dump" ] && cmp -s "$SCR/from.dump" "$SCR/to.dump" || stop "!! [3/5] the owner's page is not byte-equal before/after - nothing installed"
pya "$KDIR/walk_s951.py" lists "$SCR/from" "$SCR/from.lists" >/dev/null && pya "$KDIR/walk_s951.py" lists "$SCR/to" "$SCR/to.lists" >/dev/null \
  && [ -s "$SCR/from.lists" ] && cmp -s "$SCR/from.lists" "$SCR/to.lists" || stop "!! [3/5] Shivani's staff lists are not byte-equal before/after - nothing installed"
# the LIVE settings (portal_config.py, 0600) are read only here, in the 0700 scratch that is removed on exit
[ -f "$PD/portal_config.py" ] && \cp -p "$PD/portal_config.py" "$SCR/to/"
r1="$(recadm "$SCR/to")"
echo "$r1" | grep -q "^RECEPTION_ADMITTED True" || { echo "$r1"; stop "!! [3/5] with the live settings the new page would not admit the reception login - nothing installed. Tell Claude."; }
d1="$(clockdry "$SCR/to")"
echo "$d1" | grep -q "^DRY .*lists ok" || { echo "$d1"; stop "!! [3/5] the clock's --dry with the new page did not read the staff lists - nothing installed"; }
say "   [3/5] walk ALL PASS ($(grep -c PASS "$SCR/walk.txt")); control red; S948's $(tail -1 "$SCR/w48.txt"); S951's and S953's (reception 0) ALL PASS;"
say "         his page and Shivani's lists byte-equal; both TO remade from the live bytes; live settings: $r1"
say "         the clock with the new page, on the real stores (read-only): $(echo "$d1" | grep '^DRY' | sed 's/^DRY [0-9-]* [0-9:]*: //')"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
\cp -p "$PD/$A" "$A_BAK" && chmod 600 "$A_BAK" && [ "$(m5 "$A_BAK")" = "$A_FROM" ] || restore "[4/5] the backup of $A did not read back"
\cp -p "$PD/$B" "$B_BAK" && chmod 600 "$B_BAK" && [ "$(m5 "$B_BAK")" = "$B_FROM" ] || restore "[4/5] the backup of $B did not read back"
CHANGED=1
swap_in "$PD/$B" "$KDIR/to/$B" && [ "$(m5 "$PD/$B")" = "$B_TO" ] || restore "[4/5] $B did not read back as S955's"
swap_in "$PD/$A" "$KDIR/to/$A" && [ "$(m5 "$PD/$A")" = "$A_TO" ] || restore "[4/5] $A did not read back as S955's"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1 after the restart"
for u in /portal/console /portal/console/staff /portal/console/staff/api/lists /portal/console/api/mycard /portal/; do pg=$(hget "$u")
  case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
r2="$(recadm "$PD")"
echo "$r2" | grep -q "^RECEPTION_ADMITTED True" || { echo "$r2"; restore "[4/5] the installed page does not admit the reception login"; }
d2="$(clockdry "$PD")"
echo "$d2" | grep -q "^DRY .*lists ok" || { echo "$d2"; restore "[4/5] the installed clock's --dry did not read the staff lists"; }
say "   [4/5] placed and read back: $A $(m8 "$PD/$A"), $B $(m8 "$PD/$B"); $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $p1, the pages answer, reception admitted, the clock reads the lists"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else jr="$("$JOURNAL" -u "$PSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "calls_staff NOT mounted" && restore "[5/5] the journal says calls_staff NOT mounted"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [5/5] the journal holds no 'calls_staff NOT mounted'"
FINISHED=1; release
say "$KIT: INSTALLED - the reception mobile opens My Call Console (its own Handled today); its call-back taps land there. Undo: bash $KDIR/install_S955_RECEPTION_CONSOLE.sh --undo"
