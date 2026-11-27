#!/bin/bash
# install_S966_WA_BSUID.sh -- S966 (the parent, S531, 27-Nov-2026): MyOperator's mail of 26-Nov 20:30 IST -- from 1-Dec-2026 a
#   WhatsApp event may carry Meta's Business-Scoped User ID (BSUID, 'IN.' + 128 characters) in customer_identifier instead of
#   the patient's mobile, with meta_bsuid beside it. A value is a mobile only when it has no letter; a BSUID is never cut into
#   digits, never sent to, never dialled; a BSUID seen with a mobile is remembered so the chat stays on that mobile.
#   FIVE files: /root/wa/wa_receiver.py 793f0182 . /root/wa/wa_alert.py 89c08929 . /root/portal/portal_inbox.py 1c1fc915 (S959)
#   . /root/finance/records.py 274460dc . /root/portal/calls_console.py 19023822 (S959) -> TO. With no BSUID in a push every
#   file behaves exactly as before (the 'same' walk on made-up pushes, and 'replay' on the REAL pushes of the last 30 days).
#   wa-receiver, clinic-portal and clinic-finance are restarted (a few seconds each; the receiver at a quiet moment, no push
#   in the last 20 s). The doctor's auto-fix is paused for the run. Runs at any hour.
#   [1/5] kit sums  [2/5] the ground (all five FROM, or all five already S966's)  [3/5] HERE, with the box's own python:
#   make_s966.py remakes the five TO files from the live bytes; walk_s966 all green on the TO and red on the FROM (the control);
#   'same' green: no BSUID -> the receiver's row, the alert, the inbox's read and store, records' sender all unchanged;
#   'replay' green: the real raw pushes of 30 days, read-only, the same on both sides (counts only are printed)
#   [4/5] backups + swaps + read-backs + restarts + the services answer  [5/5] the journals hold no "wa_alert NOT loaded" and
#   no "records NOT mounted"; the WhatsApp Inbox page is not broken.  Any red after [4/5] began, or the run killed: all five
#   put back, the three services restarted.  DRY=1: [1]-[3] only.  --undo: the five backups back, only where still S966's
#   (it says how many chats are kept under a BSUID -- the old code would read those as numbers).
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s966kit && cp -rp /root/deploy/repo/deploy_kits/S966_WA_BSUID /tmp/s966kit && bash /tmp/s966kit/install_S966_WA_BSUID.sh
set -u
KIT="S966_WA_BSUID"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; WD="${WD:-$ROOT/wa}"; PD="${PD:-$ROOT/portal}"; FD="${FD:-$ROOT/finance}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
RX_PORT="${RX_PORT:-8095}"; PPORT="${PPORT:-8099}"; FIN_PORT="${FIN_PORT:-8106}"
RSVC="${RSVC:-wa-receiver}"; PSVC="${PSVC:-clinic-portal}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"; RAWLOG="${RAWLOG:-$WD/wa_logs}"
N1="wa_receiver.py";  P1="$WD/$N1"; F1_FROM="793f01820709653587fbee366ea46f17"
N2="wa_alert.py";     P2="$WD/$N2"; F2_FROM="89c08929a4d3c98cecba3e2994eef92c"
N3="portal_inbox.py"; P3="$PD/$N3"; F3_FROM="1c1fc915c53a589150ce6653e71b80b3"
N4="records.py";      P4="$FD/$N4"; F4_FROM="274460dcba60b4063d40ba38e70b2ed8"
N5="calls_console.py"; P5="$PD/$N5"; F5_FROM="190238220e8ee5e309c7bc1c650e9ee5"; INBOX_DB="${INBOX_DB:-$WD/wa_inbox/inbox.db}"
to_of() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
F1_TO="$(to_of $N1)"; F2_TO="$(to_of $N2)"; F3_TO="$(to_of $N3)"; F4_TO="$(to_of $N4)"; F5_TO="$(to_of $N5)"
B1="$P1.bak_S966_${F1_FROM:0:8}"; B2="$P2.bak_S966_${F2_FROM:0:8}"; B3="$P3.bak_S966_${F3_FROM:0:8}"; B4="$P4.bak_S966_${F4_FROM:0:8}"; B5="$P5.bak_S966_${F5_FROM:0:8}"
SCR="$(mktemp -d /tmp/s966_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date '+%F %T')"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
hget() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD "$1" "$2"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$1$2"; fi; }
rxget() { if [ -n "${RX_CMD:-}" ]; then $RX_CMD; else curl -s -m 5 "http://127.0.0.1:$RX_PORT/"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(hget "$1" "$2"); [ "$h" = 200 ] && break; done; echo "$h"; }
waitrx() { local c=""; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-2}"; c="$(rxget)"; [ "$c" = "wa_receiver alive" ] && break; done; echo "$c"; }
quiet() { # wait (up to 5 min) for 20 s with no push written to the receiver's raw log, so no message lands mid-restart
  local f n=0; while [ $n -lt "${QUIET_TRIES:-60}" ]; do f="$(ls -t "$RAWLOG"/*.jsonl 2>/dev/null | head -1)"
    if [ -z "$f" ] || [ $(( $(date +%s) - $(stat -c %Y "$f") )) -ge 20 ]; then return 0; fi; sleep "${QUIET_NAP:-5}"; n=$((n+1)); done; return 0; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s966"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local p="$1" bak="$2" from="$3"
  [ "$(m5 "$p")" = "$from" ] && { say "   $(basename "$p") is the FROM: $(m8 "$p")"; return 0; }
  if [ "$(m5 "$bak")" = "$from" ] && swap_in "$p" "$bak" && [ "$(m5 "$p")" = "$from" ]; then say "   $(basename "$p") back: $(m8 "$p")"; return 0; fi
  say "   !! $p NOT back: $(m8 "$p") (backup $(m8 "$bak"), expected ${from:0:8})"; return 1; }
put_back() { local r=0
  put_one "$P1" "$B1" "$F1_FROM" || r=1; put_one "$P2" "$B2" "$F2_FROM" || r=1
  put_one "$P3" "$B3" "$F3_FROM" || r=1; put_one "$P4" "$B4" "$F4_FROM" || r=1; put_one "$P5" "$B5" "$F5_FROM" || r=1
  [ "$r" = 0 ] && CHANGED=0; return $r; }
restart_all() { "$SYSTEMCTL" restart "$RSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true; "$SYSTEMCTL" restart "$FSVC" || true; }
restore() { say "!! RED ($1) - putting back"; put_back; restart_all
  say "   restarted: receiver '$(waitrx)', portal health $(wait200 "$PPORT" /portal/health), finance health $(wait200 "$FIN_PORT" /finance/healthz). Send a photo of this screen to Claude."
  release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart_all; fi
  release; rm -rf "${SCR:?}"; rm -f "$WD/.$N1.s966" "$WD/.$N2.s966" "$PD/.$N3.s966" "$FD/.$N4.s966" "$PD/.$N5.s966"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  h1="$(m5 "$P1")"; h2="$(m5 "$P2")"; h3="$(m5 "$P3")"; h4="$(m5 "$P4")"; h5="$(m5 "$P5")"
  [ "$h1" = "$F1_FROM" ] && [ "$h2" = "$F2_FROM" ] && [ "$h3" = "$F3_FROM" ] && [ "$h4" = "$F4_FROM" ] && [ "$h5" = "$F5_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  for x in "$P1 $h1 $F1_TO $F1_FROM $B1" "$P2 $h2 $F2_TO $F2_FROM $B2" "$P3 $h3 $F3_TO $F3_FROM $B3" "$P4 $h4 $F4_TO $F4_FROM $B4" "$P5 $h5 $F5_TO $F5_FROM $B5"; do set -- $x
    [ "$2" = "$3" ] || [ "$2" = "$4" ] || stop "!! --undo: $1 is ${2:0:8}, not S966's (a later kit?) - not undoing. Tell Claude."
    [ "$2" = "$4" ] || [ "$(m5 "$5")" = "$4" ] || stop "!! --undo: the backup $5 is $(m8 "$5"), not the FROM bytes - not undoing. Tell Claude."; done
  take_lock "--undo:" undo; CHANGED=1; quiet
  put_back || { restart_all; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart_all; c="$(waitrx)"; hp=$(wait200 "$PPORT" /portal/health); hf=$(wait200 "$FIN_PORT" /finance/healthz); release
  say "$KIT: UNDONE (receiver '$c', portal health $hp, finance health $hf)"
  nb="$(pya "$KDIR/walk_s966.py" count "$INBOX_DB" | tail -1)"
  case "$nb" in "BSUID chats: 0") ;; "BSUID chats: unknown"*) say "   (the Inbox store could not be read for the BSUID count: $nb)";; *) say "   !! $nb in the WhatsApp Inbox - the old code reads those keys as numbers (the Inbox and both Call Consoles): do not reply to or call them. Tell Claude.";; esac
  exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for x in "$N1 $F1_TO" "$N2 $F2_TO" "$N3 $F3_TO" "$N4 $F4_TO" "$N5 $F5_TO"; do set -- $x; [ -n "${2:-}" ] && [ "$(m5 "$KDIR/to/$1")" = "$2" ] || stop "!! [1/5] the kit's TO files are not as built - nothing installed"; done
say "   [1/5] kit sums ok"
[ -x "$APY" ] || stop "!! [2/5] $APY is not there - STOP. Tell Claude."
h1="$(m5 "$P1")"; h2="$(m5 "$P2")"; h3="$(m5 "$P3")"; h4="$(m5 "$P4")"; h5="$(m5 "$P5")"
[ "$h1" = "$F1_TO" ] && [ "$h2" = "$F2_TO" ] && [ "$h3" = "$F3_TO" ] && [ "$h4" = "$F4_TO" ] && [ "$h5" = "$F5_TO" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$h1" = "$F1_FROM" ] || stop "!! [2/5] $P1 is ${h1:0:8}, not ${F1_FROM:0:8} - it changed after this kit was built: STOP. Tell Claude."
[ "$h2" = "$F2_FROM" ] || stop "!! [2/5] $P2 is ${h2:0:8}, not ${F2_FROM:0:8} - it changed after this kit was built: STOP. Tell Claude."
[ "$h3" = "$F3_FROM" ] || stop "!! [2/5] $P3 is ${h3:0:8}, not ${F3_FROM:0:8} (S959's) - it changed after this kit was built: STOP. Tell Claude."
[ "$h4" = "$F4_FROM" ] || stop "!! [2/5] $P4 is ${h4:0:8}, not ${F4_FROM:0:8} - it changed after this kit was built: STOP. Tell Claude."
[ "$h5" = "$F5_FROM" ] || stop "!! [2/5] $P5 is ${h5:0:8}, not ${F5_FROM:0:8} (S959's) - it changed after this kit was built: STOP. Tell Claude."
say "   [2/5] the ground: $N1 ${F1_FROM:0:8}, $N2 ${F2_FROM:0:8}, $N3 ${F3_FROM:0:8} (S959), $N4 ${F4_FROM:0:8}, $N5 ${F5_FROM:0:8} (S959)"
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade"
\cp "$P1" "$P2" "$P3" "$P4" "$P5" "$SCR/from/"; \cp "$KDIR/to/$N1" "$KDIR/to/$N2" "$KDIR/to/$N3" "$KDIR/to/$N4" "$KDIR/to/$N5" "$SCR/to/"
pya "$KDIR/make_s966.py" "$P1" "$P2" "$P3" "$P4" "$P5" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s966.py refused the live files - nothing installed"; }
for x in "$N1 $F1_TO" "$N2 $F2_TO" "$N3 $F3_TO" "$N4 $F4_TO" "$N5 $F5_TO"; do set -- $x; [ "$(m5 "$SCR/remade/$1")" = "$2" ] || stop "!! [3/5] $1 remade from the live bytes is not the kit's TO - nothing installed"; done
pya "$KDIR/walk_s966.py" walk "$SCR/to" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/walk.txt" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
pya "$KDIR/walk_s966.py" walk "$SCR/from" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "FAIL  kit S966 marked" "$SCR/ctl.txt" && ! grep -q Traceback "$SCR/ctl.txt" \
  || stop "!! [3/5] the control (the walk on the FROM code) did not go red - the walk proves nothing here; nothing installed"
pya "$KDIR/walk_s966.py" same "$SCR/from" "$SCR/to" > "$SCR/same.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/same.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/same.txt" | head -8; stop "!! [3/5] a push without a BSUID is not read the same before and after - nothing installed"; }
pya "$KDIR/walk_s966.py" replay "$SCR/from" "$SCR/to" "$RAWLOG" "${REPLAY_DAYS:-30}" > "$SCR/replay.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/replay.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|real pushes:" "$SCR/replay.txt" | head -8; stop "!! [3/5] the REAL pushes are not read the same before and after - nothing installed. Tell Claude."; }
say "   [3/5] walk ALL PASS ($(grep -c PASS "$SCR/walk.txt")); control red ($(grep -c FAIL "$SCR/ctl.txt") red on the FROM); no BSUID = the same row, alert,"
say "         inbox read and store, records' sender ($(grep -c PASS "$SCR/same.txt") checks); all five TO remade from the live bytes"
say "        $(grep "real pushes:" "$SCR/replay.txt" | head -1) -- every one read the same"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
\cp -p "$P1" "$B1" && chmod 600 "$B1" && [ "$(m5 "$B1")" = "$F1_FROM" ] || restore "[4/5] the backup of $N1 did not read back"
\cp -p "$P2" "$B2" && chmod 600 "$B2" && [ "$(m5 "$B2")" = "$F2_FROM" ] || restore "[4/5] the backup of $N2 did not read back"
\cp -p "$P3" "$B3" && chmod 600 "$B3" && [ "$(m5 "$B3")" = "$F3_FROM" ] || restore "[4/5] the backup of $N3 did not read back"
\cp -p "$P4" "$B4" && chmod 600 "$B4" && [ "$(m5 "$B4")" = "$F4_FROM" ] || restore "[4/5] the backup of $N4 did not read back"
\cp -p "$P5" "$B5" && chmod 600 "$B5" && [ "$(m5 "$B5")" = "$F5_FROM" ] || restore "[4/5] the backup of $N5 did not read back"
CHANGED=1
swap_in "$P3" "$KDIR/to/$N3" && [ "$(m5 "$P3")" = "$F3_TO" ] || restore "[4/5] $N3 did not read back as S966's"
swap_in "$P4" "$KDIR/to/$N4" && [ "$(m5 "$P4")" = "$F4_TO" ] || restore "[4/5] $N4 did not read back as S966's"
swap_in "$P5" "$KDIR/to/$N5" && [ "$(m5 "$P5")" = "$F5_TO" ] || restore "[4/5] $N5 did not read back as S966's"
swap_in "$P2" "$KDIR/to/$N2" && [ "$(m5 "$P2")" = "$F2_TO" ] || restore "[4/5] $N2 did not read back as S966's"
swap_in "$P1" "$KDIR/to/$N1" && [ "$(m5 "$P1")" = "$F1_TO" ] || restore "[4/5] $N1 did not read back as S966's"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
quiet
"$SYSTEMCTL" restart "$RSVC" || restore "restart $RSVC"
c="$(waitrx)"; [ "$c" = "wa_receiver alive" ] || restore "the receiver did not answer after the restart ('$c')"
"$SYSTEMCTL" is-active --quiet "$RSVC" || restore "$RSVC is not active"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
q=$(wait200 "$PPORT" /portal/health); [ "$q" = 200 ] || restore "portal health $q after the restart"
for u in /portal/inbox /portal/console /portal/console/staff /portal/console/staff/api/lists /portal/; do pg=$(hget "$PPORT" "$u")
  case "$pg" in 200|302|303|401|403) ;; *) restore "$u answered $pg (the WhatsApp Inbox did not load?)";; esac; done
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
f=$(wait200 "$FIN_PORT" /finance/healthz); [ "$f" = 200 ] || restore "finance health $f after the restart"
say "   [4/5] placed and read back: $N1 $(m8 "$P1"), $N2 $(m8 "$P2"), $N3 $(m8 "$P3"), $N4 $(m8 "$P4"), $N5 $(m8 "$P5"); restarted $(TZ=Asia/Kolkata date '+%H:%M IST'):"
say "         receiver '$c', portal health $q, finance health $f; the inbox and staff pages answer"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else
  jr="$("$JOURNAL" -u "$RSVC" -u "$FSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "wa_alert NOT loaded" && restore "[5/5] the receiver's journal says wa_alert NOT loaded"
echo "$jr" | grep -q "records NOT mounted" && restore "[5/5] the finance journal says records NOT mounted"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [5/5] the journals hold no 'wa_alert NOT loaded' and no 'records NOT mounted'"
FINISHED=1; release
say "$KIT: INSTALLED - Meta's WhatsApp ID is read as an ID, never as a number. Undo: bash $KDIR/install_S966_WA_BSUID.sh --undo"
