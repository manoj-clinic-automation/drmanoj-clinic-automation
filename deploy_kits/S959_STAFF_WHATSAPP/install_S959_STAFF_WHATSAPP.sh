#!/bin/bash
# install_S959_STAFF_WHATSAPP.sh -- S959 (the parent, S524, 26-Nov-2026; roadmap B2): the staff Call Console's WhatsApp tab
#   replies -- the chat read on the page, a text reply inside 24 hours (his saved replies one tap away), the Enquiry
#   acknowledgement after it -- through portal_inbox's own sender, signed with the staff login; his Accept on a verdict
#   dispute now reads "Accepted — the verdict was wrong".
#   THREE files: /root/portal/calls_staff.py a93cdc86 (S955) -> TO . /root/portal/portal_inbox.py 6abc6461 (S871) -> the same
#   bytes + one block appended (no route) . /root/portal/calls_console.py f484cbc2 (S948) -> one script line.
#   clinic-portal is restarted (a few seconds); the doctor's auto-fix is paused for the run. Runs at any hour.
#   [1/5] kit sums  [2/5] the ground (all three FROM, or all three already S959's)  [3/5] HERE, with the box's own python and the
#   live ring_*.py / callback_clock.py / presence.py / portal_wa.py: make_s959.py remakes the three TO files from the live bytes;
#   walk_s959 all green on the TO (a stubbed sender, temp stores) and red on the FROM (the control); portal_inbox.py's TO begins
#   with its live bytes; S948's, S951's, S953's, S955's walks green on the TO; his page equal but for the Accept line; Shivani's
#   lists byte-equal; the LIVE settings read in words (reply on, templates offered, LIVE or TEST, the key named)
#   [4/5] backups + swaps + read-backs + restart + the pages and the new routes answer  [5/5] the journal holds no
#   "calls_staff NOT mounted".  Any red after [4/5] began, or the run killed: all three put back, the portal restarted.
#   DRY=1: [1]-[3] only.  --undo: the three backups back, only where the files are still S959's.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s959kit && cp -rp /root/deploy/repo/deploy_kits/S959_STAFF_WHATSAPP /tmp/s959kit && bash /tmp/s959kit/install_S959_STAFF_WHATSAPP.sh
set -u
KIT="S959_STAFF_WHATSAPP"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"
F1="calls_staff.py"; F1_FROM="a93cdc86b9870e6c6f92738cd95a2b22"
F2="portal_inbox.py"; F2_FROM="6abc6461846a408b47f7f4ceff493c21"
F3="calls_console.py"; F3_FROM="f484cbc23e85817c32cd7a6c9004dd3e"
to_of() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
F1_TO="$(to_of $F1)"; F2_TO="$(to_of $F2)"; F3_TO="$(to_of $F3)"
SCR="$(mktemp -d /tmp/s959_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date '+%F %T')"
F1_BAK="$PD/$F1.bak_S959_a93cdc86"; F2_BAK="$PD/$F2.bak_S959_6abc6461"; F3_BAK="$PD/$F3.bak_S959_f484cbc2"
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
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s959"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local f="$1" bak="$2" from="$3"
  [ "$(m5 "$PD/$f")" = "$from" ] && { say "   $f is the FROM: $(m8 "$PD/$f")"; return 0; }
  if [ "$(m5 "$bak")" = "$from" ] && swap_in "$PD/$f" "$bak" && [ "$(m5 "$PD/$f")" = "$from" ]; then say "   $f back: $(m8 "$PD/$f")"; return 0; fi
  say "   !! $f NOT back: $(m8 "$PD/$f") (backup $(m8 "$bak"), expected ${from:0:8})"; return 1; }
put_back() { local r=0; put_one "$F1" "$F1_BAK" "$F1_FROM" || r=1; put_one "$F2" "$F2_BAK" "$F2_FROM" || r=1; put_one "$F3" "$F3_BAK" "$F3_FROM" || r=1
  [ "$r" = 0 ] && CHANGED=0; return $r; }
restore() { say "!! RED ($1) - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true
  say "   $PSVC restarted, portal health $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; "$SYSTEMCTL" restart "$PSVC" || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$PD/.$F1.s959" "$PD/.$F2.s959" "$PD/.$F3.s959"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }
probe() { if [ -n "${PROBE_CMD:-}" ]; then $PROBE_CMD "$1"; else pya "$KDIR/probe_s959.py" "$1" | tail -1; fi; }

if [ "${1:-}" = "--undo" ]; then
  h1="$(m5 "$PD/$F1")"; h2="$(m5 "$PD/$F2")"; h3="$(m5 "$PD/$F3")"
  [ "$h1" = "$F1_FROM" ] && [ "$h2" = "$F2_FROM" ] && [ "$h3" = "$F3_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  for x in "$F1 $h1 $F1_TO $F1_FROM $F1_BAK" "$F2 $h2 $F2_TO $F2_FROM $F2_BAK" "$F3 $h3 $F3_TO $F3_FROM $F3_BAK"; do set -- $x
    [ "$2" = "$3" ] || [ "$2" = "$4" ] || stop "!! --undo: $PD/$1 is ${2:0:8}, not S959's (a later kit?) - not undoing. Tell Claude."
    [ "$2" = "$4" ] || [ "$(m5 "$5")" = "$4" ] || stop "!! --undo: the backup $5 is $(m8 "$5"), not the FROM bytes - not undoing. Tell Claude."; done
  take_lock "--undo:" undo; CHANGED=1; put_back || { "$SYSTEMCTL" restart "$PSVC" || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  "$SYSTEMCTL" restart "$PSVC" || true; h=$(wait200); release
  say "$KIT: UNDONE ($PSVC restarted, portal health $h)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for x in "$F1 $F1_TO" "$F2 $F2_TO" "$F3 $F3_TO"; do set -- $x; [ -n "${2:-}" ] && [ "$(m5 "$KDIR/to/$1")" = "$2" ] || stop "!! [1/5] the kit's TO files are not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
for n in ring_outcome.py ring_common.py callback_clock.py presence.py portal_wa.py tile_grants.json; do [ -f "$PD/$n" ] || stop "!! [2/5] $PD/$n is missing - STOP. Tell Claude."; done
h1="$(m5 "$PD/$F1")"; h2="$(m5 "$PD/$F2")"; h3="$(m5 "$PD/$F3")"
[ "$h1" = "$F1_TO" ] && [ "$h2" = "$F2_TO" ] && [ "$h3" = "$F3_TO" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$h1" = "$F1_FROM" ] || stop "!! [2/5] $PD/$F1 is ${h1:0:8}, not a93cdc86 (S955's) - it changed after this kit was built: STOP. Tell Claude."
[ "$h2" = "$F2_FROM" ] || stop "!! [2/5] $PD/$F2 is ${h2:0:8}, not 6abc6461 (S871's) - it changed after this kit was built: STOP. Tell Claude."
[ "$h3" = "$F3_FROM" ] || stop "!! [2/5] $PD/$F3 is ${h3:0:8}, not f484cbc2 (S948's) - it changed after this kit was built: STOP. Tell Claude."
say "   [2/5] the ground: $F1 a93cdc86 (S955), $F2 6abc6461 (S871), $F3 f484cbc2 (S948)"
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade"
for d in from to; do \cp "$PD/ring_outcome.py" "$PD/ring_common.py" "$PD/callback_clock.py" "$PD/presence.py" "$PD/portal_wa.py" "$SCR/$d/"; done
\cp "$PD/$F1" "$PD/$F2" "$PD/$F3" "$SCR/from/"; \cp "$KDIR/to/$F1" "$KDIR/to/$F2" "$KDIR/to/$F3" "$SCR/to/"
pya "$KDIR/make_s959.py" "$PD/$F1" "$PD/$F3" "$PD/$F2" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s959.py refused the live files - nothing installed"; }
for x in "$F1 $F1_TO" "$F2 $F2_TO" "$F3 $F3_TO"; do set -- $x; [ "$(m5 "$SCR/remade/$1")" = "$2" ] || stop "!! [3/5] $1 remade from the live bytes is not the kit's TO - nothing installed"; done
pya "$KDIR/walk_s959.py" walk "$SCR/to" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
pya "$KDIR/walk_s959.py" walk "$SCR/from" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL  kit S959 marked" "$SCR/ctl.txt" && ! grep -q Traceback "$SCR/ctl.txt" \
  || stop "!! [3/5] the control (the walk on the FROM code) did not go red - the walk proves nothing here; nothing installed"
pya "$KDIR/walk_s959.py" prefix "$PD/$F2" "$SCR/to/$F2" > "$SCR/pre.txt" && tail -1 "$SCR/pre.txt" | grep -q "^ALL PASS$" || stop "!! [3/5] portal_inbox.py's TO does not begin with its live bytes - nothing installed"
pya "$KDIR/walk_s948.py" walk "$SCR/to" > "$SCR/w48.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w48.txt" | grep -qE "^[0-9]+ checks, 0 failed$" || { grep -E "FAIL|Error" "$SCR/w48.txt" | head -8; stop "!! [3/5] S948's own walk is not all green on the TO - nothing installed"; }
pya "$KDIR/walk_s951.py" walk "$SCR/to" > "$SCR/w51.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w51.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/w51.txt" | head -8; stop "!! [3/5] S951's own walk is not all green on the TO - nothing installed"; }
(export PORTAL_STAFF_CONSOLE_RECEPTION=0 PORTAL_PRESENCE_ROSTER=0 PRESENCE_SILENCE_STATE="$SCR/none.json" SR_DB_PATH="$SCR/none.db"; pya "$KDIR/walk_s953.py" walk "$SCR/to") > "$SCR/w53.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w53.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/w53.txt" | head -8; stop "!! [3/5] S953's own walk is not all green on the TO - nothing installed"; }
# S955's walk: its two grant checks compare v48 with v49 and are not this kit's (both given the live v49) -- every other check green
pya "$KDIR/walk_s955.py" walk "$SCR/to" "$PD/tile_grants.json" "$PD/tile_grants.json" > "$SCR/w55.txt"
grep "^  FAIL  " "$SCR/w55.txt" | grep -vE "FAIL  (tile_grants v48 -> v49|reception's other grants unchanged)$" | grep -q . && { grep FAIL "$SCR/w55.txt" | head -6; stop "!! [3/5] S955's own walk is not green on the TO - nothing installed"; }
grep -q "^ *PASS" "$SCR/w55.txt" && ! grep -q Traceback "$SCR/w55.txt" || stop "!! [3/5] S955's own walk did not run - nothing installed"
pya "$KDIR/walk_s948.py" dump "$SCR/from" "$SCR/from.dump" >/dev/null && pya "$KDIR/walk_s948.py" dump "$SCR/to" "$SCR/to.dump" >/dev/null \
  && pya "$KDIR/walk_s959.py" page "$SCR/from.dump" "$SCR/to.dump" | tail -1 | grep -q "^ALL PASS$" || stop "!! [3/5] the owner's page changed beyond the Accept line - nothing installed"
pya "$KDIR/walk_s951.py" lists "$SCR/from" "$SCR/from.lists" >/dev/null && pya "$KDIR/walk_s951.py" lists "$SCR/to" "$SCR/to.lists" >/dev/null \
  && [ -s "$SCR/from.lists" ] && cmp -s "$SCR/from.lists" "$SCR/to.lists" || stop "!! [3/5] Shivani's staff lists are not byte-equal before/after - nothing installed"
# the LIVE settings (portal_config.py, 0600) are read only here, in the 0700 scratch that is removed on exit; said in words
[ -f "$PD/portal_config.py" ] && \cp -p "$PD/portal_config.py" "$SCR/to/"
p1="$(probe "$SCR/to")"
echo "$p1" | grep -q "^PROBE reply " || { echo "$p1" | tail -2; stop "!! [3/5] the live settings could not be read with the new page - nothing installed. Tell Claude."; }
rm -f "$SCR/to/portal_config.py"
say "   [3/5] walk ALL PASS ($(grep -c PASS "$SCR/walk.txt")); control red; $F2 begins with its live bytes; S948's $(tail -1 "$SCR/w48.txt");"
say "         S951's, S953's, S955's walks green; his page equal but for the Accept line; Shivani's lists byte-equal; all three TO remade"
say "         from the live bytes. Live settings: ${p1#PROBE }"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
\cp -p "$PD/$F1" "$F1_BAK" && chmod 600 "$F1_BAK" && [ "$(m5 "$F1_BAK")" = "$F1_FROM" ] || restore "[4/5] the backup of $F1 did not read back"
\cp -p "$PD/$F2" "$F2_BAK" && chmod 600 "$F2_BAK" && [ "$(m5 "$F2_BAK")" = "$F2_FROM" ] || restore "[4/5] the backup of $F2 did not read back"
\cp -p "$PD/$F3" "$F3_BAK" && chmod 600 "$F3_BAK" && [ "$(m5 "$F3_BAK")" = "$F3_FROM" ] || restore "[4/5] the backup of $F3 did not read back"
CHANGED=1
swap_in "$PD/$F2" "$KDIR/to/$F2" && [ "$(m5 "$PD/$F2")" = "$F2_TO" ] || restore "[4/5] $F2 did not read back as S959's"
swap_in "$PD/$F3" "$KDIR/to/$F3" && [ "$(m5 "$PD/$F3")" = "$F3_TO" ] || restore "[4/5] $F3 did not read back as S959's"
swap_in "$PD/$F1" "$KDIR/to/$F1" && [ "$(m5 "$PD/$F1")" = "$F1_TO" ] || restore "[4/5] $F1 did not read back as S959's"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
q=$(wait200); [ "$q" = 200 ] || restore "portal health $q after the restart"
for u in /portal/console /portal/console/staff /portal/console/staff/api/lists /portal/inbox /portal/inbox/health /portal/; do pg=$(hget "$u")
  case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg";; esac; done
for u in /portal/console/staff/api/wa/chat; do pg=$(hget "$u")
  case "$pg" in 302|303|400|401|403) ;; *) restore "$u answered $pg (the new route is not mounted)";; esac; done
say "   [4/5] placed and read back: $F1 $(m8 "$PD/$F1"), $F2 $(m8 "$PD/$F2"), $F3 $(m8 "$PD/$F3"); $PSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), health $q, the pages and the new route answer"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else jr="$("$JOURNAL" -u "$PSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "calls_staff NOT mounted" && restore "[5/5] the journal says calls_staff NOT mounted"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [5/5] the journal holds no 'calls_staff NOT mounted'"
FINISHED=1; release
say "$KIT: INSTALLED - the staff reply to WhatsApp from My Call Console (signed with their login). Undo: bash $KDIR/install_S959_STAFF_WHATSAPP.sh --undo"
