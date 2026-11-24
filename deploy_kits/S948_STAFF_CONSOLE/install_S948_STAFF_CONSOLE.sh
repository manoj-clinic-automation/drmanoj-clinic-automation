#!/bin/bash
# install_S948_STAFF_CONSOLE.sh -- S948 (the parent, S515, 24-Nov-2026): B1, the staff's own Call Console (D1059, D1060).
#   NEW /root/portal/calls_staff.py (the page /portal/console/staff, six tabs, the owner's approved screens v5.1);
#   /root/portal/calls_console.py eb13790d -> TO (FIGS gains "verdict"; calls_staff registered at the END of register(),
#   in a try: a fault there never takes his page down); /root/portal/tile_grants.json v47 -> v48 (the tile
#   "My Call Console" granted by name to shivani, alisha, shavez, and to manoj for his picker). clinic-portal is restarted; the doctor's auto-fix is
#   paused for the run.
#   [1/5] kit sums  [2/5] the ground (each live file is the 24-Nov bundle's, or already S948's; calls_staff.py absent or
#   S948's)  [3/5] the walk HERE (made-up stores, the box's own python and ring_*.py): the TO side all green, his page +
#   his ?as= cards BYTE-EQUAL before/after, a mutant (a reached patient left on the lists) red (the control), and
#   make_s948.py remade from the live bytes = the kit's TO  [4/5] backups + the swap + read-back + the live portal
#   imported with the staff routes and the tile + restart + the pages answer  [5/5] the journal holds no
#   "calls_staff NOT mounted".  Any red after [4/5] began, or the run killed: every file put back, the portal restarted.
#   DRY=1: [1]-[3] only.  --undo: the backups back (calls_staff.py moved aside), only where each file is still S948's.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s948kit && cp -rp /root/deploy/repo/deploy_kits/S948_STAFF_CONSOLE /tmp/s948kit && bash /tmp/s948kit/install_S948_STAFF_CONSOLE.sh
set -u
KIT="S948_STAFF_CONSOLE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"
NAMES="calls_console.py tile_grants.json calls_staff.py"
from_of() { case "$1" in calls_console.py) echo eb13790d1a761fedf6d5b0e2faa37d50;; tile_grants.json) echo 8299e8d44b5938343d2a2c66315f3f67;;
  calls_staff.py) echo ABSENT;; esac; }
to_of() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
SCR="$(mktemp -d /tmp/s948_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=""; FINISHED=0; T0="$(date '+%F %T')"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$PD/$1.bak_S948_$(from_of "$1" | cut -c1-8)"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT$1"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hget /portal/health); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() {   # $1 live path, $2 source, $3 a file whose mode/owner to copy (the live file, or a sibling for a new one)
  local t="$(dirname "$1")/.$(basename "$1").s948"
  \cp "$2" "$t" && chmod --reference="$3" "$t" && chown --reference="$3" "$t" && mv -f "$t" "$1"; }
put_back() {  # every changed file back to its FROM; a new file moved aside (never deleted); says each with its md5
  local n b bad=0
  for n in $CHANGED; do
    if [ "$(from_of $n)" = ABSENT ]; then
      [ -f "$PD/$n" ] && mv -f "$PD/$n" "$PD/$n.bak_S948_off_$(date +%Y%m%d_%H%M%S)"   # .bak: the nightly bundle takes none
      [ -f "$PD/$n" ] && { say "   !! $n still in place"; bad=1; } || say "   $n moved aside"
    else b="$(bak $n)"
      if [ "$(m5 "$b")" = "$(from_of $n)" ] && swap_in "$PD/$n" "$b" "$PD/$n" && [ "$(m5 "$PD/$n")" = "$(from_of $n)" ]; then say "   $n back: $(m8 "$PD/$n")"
      else say "   !! $n NOT back: $(m8 "$PD/$n") (backup $(m8 "$b"), expected $(from_of $n | cut -c1-8))"; bad=1; fi
    fi; done
  CHANGED=""; return $bad; }
restore() { say "!! RED ($1) - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true
  say "   $PSVC restarted, portal health $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ -n "$CHANGED" ]; then say "!! the run ended before its proof - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true; fi
  release; rm -rf "${SCR:?}"; for n in $NAMES; do rm -f "$PD/.$n.s948"; done; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  todo=""
  for n in $NAMES; do h="$(m5 "$PD/$n")"
    [ "$h" = "$(from_of $n)" ] && continue
    [ "$h" = "$(to_of $n)" ] || stop "!! --undo: $PD/$n is ${h:0:8}, not S948's (a later kit?) - not undoing. Tell Claude."
    if [ "$(from_of $n)" != ABSENT ]; then
      [ "$(m5 "$(bak $n)")" = "$(from_of $n)" ] || stop "!! --undo: the backup $(bak $n) is $(m8 "$(bak $n)"), not the 24-Nov bytes - not undoing. Tell Claude."
    fi
    todo="$todo $n"; done
  [ -z "$todo" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  take_lock "--undo:" undo; CHANGED="$todo"; put_back || { "$SYSTEMCTL" restart "$PSVC" || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  "$SYSTEMCTL" restart "$PSVC" || true; h=$(wait200); release
  say "$KIT: UNDONE ($(echo $todo | wc -w) file(s); $PSVC restarted, portal health $h)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in $NAMES; do [ "$(m5 "$KDIR/to/$n")" = "$(to_of $n)" ] || stop "!! [1/5] the kit's $n is not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
for n in ring_outcome.py ring_common.py; do [ -f "$PD/$n" ] || stop "!! [2/5] $PD/$n is missing - STOP. Tell Claude."; done
todo=""; already=0
for n in $NAMES; do h="$(m5 "$PD/$n")"
  if [ "$h" = "$(to_of $n)" ]; then already=$((already+1))
  elif [ "$h" = "$(from_of $n)" ]; then todo="$todo $n"
  else stop "!! [2/5] $PD/$n is ${h:0:8}, not $(from_of $n | cut -c1-8) (the 24-Nov bundle's) - it changed after this kit was built: STOP. Tell Claude."; fi; done
say "   [2/5] the ground: $(echo $todo | wc -w) to place, $already already S948's"
[ -z "$todo" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$(echo $todo | wc -w)" = 3 ] || stop "!! [2/5] only part of the kit is in place ($already of 3) - STOP. Tell Claude."
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade"
\cp "$PD/calls_console.py" "$SCR/from/"; \cp "$PD/ring_outcome.py" "$PD/ring_common.py" "$SCR/from/"
\cp "$KDIR/to/calls_console.py" "$KDIR/to/calls_staff.py" "$SCR/to/"; \cp "$PD/ring_outcome.py" "$PD/ring_common.py" "$SCR/to/"
pya "$KDIR/make_s948.py" "$PD/calls_console.py" "$PD/tile_grants.json" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s948.py refused the live files - nothing installed"; }
for n in calls_console.py tile_grants.json; do [ "$(m5 "$SCR/remade/$n")" = "$(to_of $n)" ] || stop "!! [3/5] $n remade from the live bytes is not the kit's TO - nothing installed"; done
pya "$KDIR/walk_s948.py" walk "$SCR/to" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -qE "^[0-9]+ checks, 0 failed$" || { grep -E "FAIL|Error" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
mkdir -p "$SCR/ctl"; \cp "$SCR/to/"*.py "$SCR/ctl/"
pya - "$SCR/ctl/calls_staff.py" > "$SCR/mut.txt" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
a = '            if any(x["answered"] for x in calls):\n                continue'
assert s.count(a) == 1, "anchor"
open(p, "w", encoding="utf-8").write(s.replace(a, '            if False:\n                continue'))
print("MUTATED")
PYEOF
grep -q MUTATED "$SCR/mut.txt" || stop "!! [3/5] the control could not be made - nothing installed"
pya "$KDIR/walk_s948.py" walk "$SCR/ctl" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL reached today" "$SCR/ctl.txt" || stop "!! [3/5] the control (a reached patient left on the lists) did not go red - the walk proves nothing here; nothing installed"
pya "$KDIR/walk_s948.py" dump "$SCR/from" "$SCR/from.dump" >/dev/null && pya "$KDIR/walk_s948.py" dump "$SCR/to" "$SCR/to.dump" >/dev/null \
  && [ -s "$SCR/from.dump" ] && cmp -s "$SCR/from.dump" "$SCR/to.dump" || stop "!! [3/5] the owner's page is not byte-equal before/after - nothing installed"
say "   [3/5] $(tail -1 "$SCR/walk.txt"); control red ($(grep -c '^  FAIL' "$SCR/ctl.txt")); his page byte-equal ($(m8 "$SCR/to.dump")); the TO remade from the live bytes"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
for n in calls_console.py tile_grants.json; do b="$(bak $n)"
  \cp -p "$PD/$n" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$(from_of $n)" ] || restore "[4/5] the backup of $n did not read back"; done
for n in tile_grants.json calls_staff.py calls_console.py; do
  CHANGED="$CHANGED $n"
  swap_in "$PD/$n" "$KDIR/to/$n" "$( [ -f "$PD/$n" ] && echo "$PD/$n" || echo "$PD/calls_console.py")" && [ "$(m5 "$PD/$n")" = "$(to_of $n)" ] \
    || restore "[4/5] $n did not read back as S948's"
  [ "${FORCE_KILL_AT:-}" = "4:$n" ] && kill -TERM $$
done
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
# the live portal imported as gunicorn imports it, before the restart: every route mounted and the tile there
if [ -n "${IMPORT_CHECK_CMD:-}" ]; then ic="$($IMPORT_CHECK_CMD)"; else
  ic="$(cd "$PD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 120 "$APY" -W ignore -B -c "
import sys; sys.path.insert(0, '.')
import portal as p
r = {x.rule for x in p.app.url_map.iter_rules()}
need = {'/portal/console', '/portal/console/staff', '/portal/console/staff/api/lists', '/portal/console/staff/api/call', '/portal/console/staff/api/dispute'}
assert need <= r, sorted(need - r)
assert [t['name'] for t in p.TILES].count('My Call Console') == 1
print('IMPORT OK')" 2>&1)"; fi
echo "$ic" | grep -qx "IMPORT OK" || { echo "$ic" | tail -4; restore "[4/5] the portal imported here lacks the staff routes or the tile"; }
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200); [ "$p1" = 200 ] || restore "portal health $p1 after the restart"
for u in /portal/console /portal/console/staff /portal/console/staff/api/lists /portal/console/api/mycard /portal/; do pg=$(hget "$u")
  case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
say "   [4/5] the portal imports with the four staff routes and the tile; placed and read back:$(for n in $NAMES; do printf ' %s %s' $n "$(m8 "$PD/$n")"; done); $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $p1, the pages answer"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else jr="$("$JOURNAL" -u "$PSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "calls_staff NOT mounted" && restore "[5/5] the journal says calls_staff NOT mounted"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [5/5] the journal holds no 'calls_staff NOT mounted'"
FINISHED=1; release
say "$KIT: INSTALLED - the staff Call Console at /portal/console/staff, the tile 'My Call Console' for shivani, alisha, shavez (and his picker). Undo: bash $KDIR/install_S948_STAFF_CONSOLE.sh --undo"
