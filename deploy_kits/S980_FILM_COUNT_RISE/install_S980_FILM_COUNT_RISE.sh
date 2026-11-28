#!/bin/bash
# install_S980_FILM_COUNT_RISE.sh -- S980 (the parent, S545, 28-Nov-2026; his ask 18:15 "the film log is not showing the machine
#   counts"; his fact 18:39 "a new box goes in only when the current one comes down to 0, many times in the middle of the day").
#   No film count was saved since 09-Nov: the 8x10 box ran down to 21, a new box went in, and every staff save since was refused
#   (a rise only from a last count of 20 or less). Now a rise is a box load WITH the tick whatever the last count was; only a rise
#   of 20 films or fewer from above 20 is still refused (a typo); the tick is always offered; a rise saved from above 20 is told
#   to him once. FILE: /root/finance/xray_film.py 5e3a2bd1 -> TO.
#   [1/6] kit sums  [2/6] the FROM  [3/6] make_s980 remakes the TO from the live bytes; the walk green on the TO, red on the FROM;
#   the live shape on a COPY (the film pages by hash and status only)  [4/6] backup, swap, read-back  [5/6] restart, healthz, the
#   film page answers, the log clean  [6/6] ON.  Any red after [4/6] began, or the run killed: put back.  DRY=1: [1]-[3] only.
#   --undo: the file back.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s980kit && \cp -rp /root/deploy/repo/deploy_kits/S980_FILM_COUNT_RISE /tmp/s980kit && bash /tmp/s980kit/install_S980_FILM_COUNT_RISE.sh
set -u
KIT="S980_FILM_COUNT_RISE"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"
VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$FD/finance.db}"
B="$FD/xray_film.py"; B_FROM="5e3a2bd1a8fa63b5142c2c46a8fc5191"
B_TO="$(awk '$2=="to/xray_film.py"{print $1}' "$KDIR/TO_PINS.md5")"
SCR="$(mktemp -d /tmp/s980_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
BAK="$B.bak_S980_${B_FROM:0:8}"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s980"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_back() { [ "$(m5 "$B")" = "$B_FROM" ] && { CHANGED=0; return 0; }
  if [ "$(m5 "$BAK")" = "$B_FROM" ] && swap_in "$B" "$BAK" && [ "$(m5 "$B")" = "$B_FROM" ]; then say "   xray_film.py back: $(m8 "$B")"; CHANGED=0; return 0; fi
  say "   !! xray_film.py NOT back: $(m8 "$B") (backup $(m8 "$BAK"))"; return 1; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$FD/.xray_film.py.s980"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local x="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-600}" "$x" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  h="$(m5 "$B")"; [ "$h" = "$B_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  [ "$h" = "$B_TO" ] || stop "!! --undo: $B is ${h:0:8}, not S980's (a later kit?) - not undoing. Tell Claude."
  [ "$(m5 "$BAK")" = "$B_FROM" ] || stop "!! --undo: the backup is not the FROM bytes - not undoing. Tell Claude."
  take_lock "--undo:" undo; CHANGED=1
  put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || true; h=$(wait200); release
  say "$KIT: UNDONE ($FSVC restarted, healthz $h; the film morning count is as it was)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/6] KIT_ID.txt names another kit - nothing installed"
[ -n "$B_TO" ] && [ "$(m5 "$KDIR/to/xray_film.py")" = "$B_TO" ] || stop "!! [1/6] the kit's TO file is not as built - nothing installed"
say "   [1/6] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/6] $VPY is not there - STOP. Tell Claude."
[ "$(m5 "$B")" = "$B_TO" ] && { say "$KIT: ALREADY in place - nothing to do"; exit 0; }
[ "$(m5 "$B")" = "$B_FROM" ] || stop "!! [2/6] $B is $(m8 "$B"), not ${B_FROM:0:8} - it changed after this kit was built: STOP. Tell Claude."
for n in "$FD/day_check.py" "$LIVE_DB"; do [ -f "$n" ] || stop "!! [2/6] $n is missing - STOP. Tell Claude."; done
say "   [2/6] the ground: xray_film ${B_FROM:0:8}"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade" "$SCR/live_from"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" && \cp -p "$B" "$SCR/live_from/" || stop "!! [3/6] could not lay out the walk - nothing installed"
"$VPY" -c 'import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close()' "$LIVE_DB" "$SCR/db.copy" && chmod 600 "$SCR/db.copy" \
  || stop "!! [3/6] could not copy the database into the scratch - nothing installed"
py "$VPY" "$KDIR/make_s980.py" "$SCR/live_from" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/6] make_s980.py refused the live file - nothing installed"; }
[ "$(m5 "$SCR/remade/xray_film.py")" = "$B_TO" ] || stop "!! [3/6] xray_film.py remade from the live bytes is not the kit's TO - nothing installed"
\cp "$KDIR/to/xray_film.py" "$SCR/new/"
(cd "$SCR" && "$VPY" -c 'import py_compile,sys; py_compile.compile(sys.argv[2], cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/xray_film.py") \
  || stop "!! [3/6] the file does not compile under $VPY - nothing installed"
W="$(py "$VPY" "$KDIR/walk_s980.py" "$SCR/new" "$SCR/db.copy")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q ", 0 FAIL" || { echo "$W" | grep -E "FAIL|Error" | head -8; stop "!! [3/6] the walk is not all green here - nothing installed"; }
WC="$(py "$VPY" "$KDIR/walk_s980.py" "$SCR/old" "$SCR/db.copy")"; rc=$?
[ "$rc" != 0 ] || stop "!! [3/6] the control (the walk on the live code as it is) did not go red - nothing installed"
if [ -n "${LIVE_CMD:-}" ]; then LV="$($LIVE_CMD)"; else LV="$(py "$VPY" "$KDIR/probe_s980.py" "$SCR/old" "$SCR/new" "$SCR/db.copy")"; fi
echo "$LV" | tail -1 | grep -q "^ALL PASS" || { echo "$LV" | tail -3; stop "!! [3/6] the live shape (a copy of the database) is not green - nothing installed. Send a photo to Claude."; }
rm -f "$SCR/db.copy"
say "   [3/6] walk $(echo "$W" | tail -1 | sed 's/^WALK S980: //'); control red; the TO remade from the live bytes"
say "         the live shape (a copy): $(echo "$LV" | grep '^LIVE' | head -1 | cut -c1-200)"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/6]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
\cp -p "$B" "$BAK" && chmod 600 "$BAK" && [ "$(m5 "$BAK")" = "$B_FROM" ] || stop "!! [4/6] the backup did not read back - nothing placed"
CHANGED=1
swap_in "$B" "$KDIR/to/xray_film.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/6] xray_film.py did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/6] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d2=$(door /finance/slips/film/subah); case "$d2" in 404|000|5*) restore "the film morning page answers $d2";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|SyntaxError|xray_film" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/6] forced red (rehearsal)"
say "   [4/6] placed and read back: xray_film $(m8 "$B")"
say "   [5/6] $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the film morning page $d2 (login-gated); the log clean"
FINISHED=1; CHANGED=0; release
say "   [6/6] ON: a count after a new box is saved with the tick."
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S980_FILM_COUNT_RISE.sh --undo"
