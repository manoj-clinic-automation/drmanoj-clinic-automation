#!/bin/bash
# install_S978_STAFF_TAPS.sh -- S978 (the parent, S545, 28-Nov-2026; D1100 -- K2b of S537_MORNING_CHECK_FINAL_BUILD_PLAN; his
#   "Next blank paper" 17:4x). THE STAFF TAPS on the morning's two money cards: on 'nf:' the late parchi (a patient of the card, the
#   service from the price-filtered list, the book's next number) made by slip_log itself and kept outside Docterz; on 'nf:' and
#   'less:' the register one-tap (the one cell, audited, Undo; never cash when the drawer count proves it); 'Refund tha (cash)' on
#   'less:'; 'Pata nahi' -> his push; 'Sab ho gaya' -> the existing per-card ticks; the Day check tile for Shavez, Shivani, Alisha;
#   the register opens on the last working day until it is saved. DAYCHK_TAPS=0 hides every new button.
#   FILES: /root/finance/day_check.py 5843d3d5 (S977) . register_push.py 2ba0d63b (S977) . clinic_register.py ba56418d (S968) .
#   /root/portal/tile_grants.json 8a3cff12 (v49, S955) -> TO.
#   [1/6] kit sums  [2/6] the ground (four FROM)  [3/6] HERE, with the box's own python: make_s978.py remakes the TO from the live
#   bytes; the walk green on the TO, red on the FROM (the control); the live shape on a COPY of finance.db (0700 scratch, counts;
#   every offered tap tried on a second scratch copy)  [4/6] a quiet minute between the 5-minute push runs; backups, swaps,
#   read-backs  [5/6] restart, healthz 200, the day check and the register answer, the log clean, --status, the tile file reads
#   [6/6] ON.  Any red after [4/6] began, or the run killed: all put back.  DRY=1: [1]-[3] only.  --undo: the four files back.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s978kit && \cp -rp /root/deploy/repo/deploy_kits/S978_STAFF_TAPS /tmp/s978kit && bash /tmp/s978kit/install_S978_STAFF_TAPS.sh
set -u
KIT="S978_STAFF_TAPS"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"; PD="${PD:-$ROOT/portal}"
VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$FD/finance.db}"
B="$FD/day_check.py";        B_FROM="5843d3d579c1571d058bd6e25d8585d4"
C="$FD/register_push.py";    C_FROM="2ba0d63b5c277113cbcfa9f40e2c1d3f"
R="$FD/clinic_register.py";  R_FROM="ba56418d46e029391a70556949c4e363"
G="$PD/tile_grants.json";    G_FROM="8a3cff12f66f5ad1ef73627b49091599"
NAMES="day_check.py register_push.py clinic_register.py tile_grants.json"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
B_TO="$(to day_check.py)"; C_TO="$(to register_push.py)"; R_TO="$(to clinic_register.py)"; G_TO="$(to tile_grants.json)"
SCR="$(mktemp -d /tmp/s978_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$1.bak_S978_${2:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s978"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
put_back() { local r=0; put_one "$G" "$G_FROM" || r=1; put_one "$C" "$C_FROM" || r=1; put_one "$R" "$R_FROM" || r=1; put_one "$B" "$B_FROM" || r=1
  [ "$r" = 0 ] && CHANGED=0; return $r; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$FD/.day_check.py.s978" "$FD/.register_push.py.s978" "$FD/.clinic_register.py.s978" "$PD/.tile_grants.json.s978"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local x="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-900}" "$x" -W ignore -B "$@" 2>&1); }
quiet_minute() {   # the 5-minute push (cron # S968_REGISTER_PUSH, */5) has just run: start in minute 1 or 2 of the five
  [ "${NO_WAIT:-0}" = 1 ] && return 0
  for _w in $(seq 1 70); do m=$((10#$(TZ=Asia/Kolkata date +%M) % 5)); { [ "$m" = 1 ] || [ "$m" = 2 ]; } && return 0; sleep 5; done; return 0; }
ALL4() { echo "$B:$B_FROM:$B_TO $C:$C_FROM:$C_TO $R:$R_FROM:$R_TO $G:$G_FROM:$G_TO"; }

if [ "${1:-}" = "--undo" ]; then
  [ "$(m5 "$B")" = "$B_FROM" ] && [ "$(m5 "$C")" = "$C_FROM" ] && [ "$(m5 "$R")" = "$R_FROM" ] && [ "$(m5 "$G")" = "$G_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  for x in $(ALL4); do f="${x%%:*}"; r_="${x#*:}"; fr="${r_%%:*}"; tt="${r_#*:}"; h="$(m5 "$f")"
    [ "$h" = "$tt" ] || [ "$h" = "$fr" ] || stop "!! --undo: $f is ${h:0:8}, not S978's (a later kit?) - not undoing. Tell Claude."
    [ "$h" = "$fr" ] || [ "$(m5 "$(bak "$f" "$fr")")" = "$fr" ] || stop "!! --undo: the backup of $(basename "$f") is not the FROM bytes - not undoing. Tell Claude."; done
  take_lock "--undo:" undo; CHANGED=1
  put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || true; h=$(wait200); release
  say "$KIT: UNDONE ($FSVC restarted, healthz $h; the morning check is as S977 left it)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/6] KIT_ID.txt names another kit - nothing installed"
for n in $NAMES; do [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/6] the kit's TO files are not as built - nothing installed"; done
say "   [1/6] kit sums ok"
[ -x "$VPY" ] || stop "!! [2/6] $VPY is not there - STOP. Tell Claude."
if [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ] && [ "$(m5 "$R")" = "$R_TO" ] && [ "$(m5 "$G")" = "$G_TO" ]; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
for x in $(ALL4); do f="${x%%:*}"; r_="${x#*:}"; fr="${r_%%:*}"
  [ "$(m5 "$f")" = "$fr" ] || stop "!! [2/6] $f is $(m8 "$f"), not ${fr:0:8} - it changed after this kit was built: STOP. Tell Claude."; done
for n in "$FD/not_in_docterz.py" "$FD/evening_check.py" "$FD/slip_adjust.py" "$FD/slip_log.py" "$LIVE_DB"; do [ -f "$n" ] || stop "!! [2/6] $n is missing - STOP. Tell Claude."; done
say "   [2/6] the ground: day_check ${B_FROM:0:8}, register_push ${C_FROM:0:8}, clinic_register ${R_FROM:0:8}, tile_grants ${G_FROM:0:8}"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade" "$SCR/live_from" "$SCR/pnew"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" && \cp -p "$B" "$C" "$R" "$G" "$SCR/live_from/" || stop "!! [3/6] could not lay out the walk - nothing installed"
"$VPY" -c 'import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close()' "$LIVE_DB" "$SCR/db.copy" && chmod 600 "$SCR/db.copy" \
  || stop "!! [3/6] could not copy the database into the scratch - nothing installed"
py "$VPY" "$KDIR/make_s978.py" "$SCR/live_from" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/6] make_s978.py refused the live files - nothing installed"; }
for n in $NAMES; do [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/6] $n remade from the live bytes is not the kit's TO - nothing installed"; done
for n in day_check.py register_push.py clinic_register.py; do \cp "$KDIR/to/$n" "$SCR/new/"; done; \cp "$KDIR/to/tile_grants.json" "$SCR/pnew/"
(cd "$SCR" && "$VPY" -c 'import py_compile,sys
for f in sys.argv[2:]: py_compile.compile(f, cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/day_check.py" "$SCR/new/register_push.py" "$SCR/new/clinic_register.py") \
  || stop "!! [3/6] a file does not compile under $VPY - nothing installed"
"$VPY" -c 'import json,sys; j=json.load(open(sys.argv[1],encoding="utf-8")); assert j["version"]==50' "$SCR/pnew/tile_grants.json" || stop "!! [3/6] the tile file does not read - nothing installed"
W="$(py "$VPY" "$KDIR/walk_s978.py" "$SCR/new" "$SCR/db.copy" "$SCR/pnew")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q ", 0 FAIL" || { echo "$W" | grep -E "FAIL|Error" | head -8; stop "!! [3/6] the walk is not all green here - nothing installed"; }
WC="$(py "$VPY" "$KDIR/walk_s978.py" "$SCR/old" "$SCR/db.copy")"; rc=$?
[ "$rc" != 0 ] || stop "!! [3/6] the control (the walk on the live code as it is) did not go red - nothing installed"
if [ -n "${LIVE_CMD:-}" ]; then LV="$($LIVE_CMD)"; else LV="$(py "$VPY" "$KDIR/probe_s978.py" "$SCR/old" "$SCR/new" "$SCR/db.copy" 60)"; fi
echo "$LV" | tail -1 | grep -q "^ALL PASS" || { echo "$LV" | tail -4; stop "!! [3/6] the live shape (a copy of the database, no push) is not green - nothing installed. Send a photo to Claude."; }
rm -f "$SCR/db.copy"
say "   [3/6] walk $(echo "$W" | tail -1 | sed 's/^WALK S978: //'); control red; four TO remade from the live bytes"
say "         the live shape (a copy, counts only): $(echo "$LV" | grep '^LIVE' | head -1 | cut -c1-230)"
say "         $(echo "$LV" | grep '^TRIAL (' | head -1 | cut -c1-200)"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/6]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for x in $(ALL4); do f="${x%%:*}"; r_="${x#*:}"; fr="${r_%%:*}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || stop "!! [4/6] the backup of $(basename "$f") did not read back - nothing placed"; done
quiet_minute
CHANGED=1
swap_in "$B" "$KDIR/to/day_check.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/6] day_check.py did not read back"
swap_in "$R" "$KDIR/to/clinic_register.py" && [ "$(m5 "$R")" = "$R_TO" ] || restore "[4/6] clinic_register.py did not read back"
swap_in "$C" "$KDIR/to/register_push.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/6] register_push.py did not read back"
swap_in "$G" "$KDIR/to/tile_grants.json" && [ "$(m5 "$G")" = "$G_TO" ] || restore "[4/6] tile_grants.json did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/6] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d2=$(door /finance/clinic/check/mine); case "$d2" in 404|000|5*) restore "the day check answers $d2";; esac
d3=$(door /finance/clinic/register); case "$d3" in 404|000|5*) restore "the register answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|day_check NOT mounted|register_push|SyntaxError" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
st=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$C" --status --db "$LIVE_DB" 2>&1 | tail -1)
echo "$st" | grep -q "^REGPUSH S978 1: " || restore "[5/6] register_push --status did not run on the box's python ($st)"
"$VPY" -c 'import json,sys; j=json.load(open(sys.argv[1],encoding="utf-8")); assert j["version"]==50 and all("Day check" in j["users"][w]["extra"] for w in ("shavez","shivani","alisha"))' "$G" \
  || restore "[5/6] the placed tile file does not read"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/6] forced red (rehearsal)"
say "   [4/6] placed and read back: day_check $(m8 "$B"), register_push $(m8 "$C"), clinic_register $(m8 "$R"), tile_grants $(m8 "$G") (v50)"
say "   [5/6] $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the day check $d2, the register $d3 (login-gated); the log clean"
FINISHED=1; CHANGED=0; release
say "   [6/6] ON: the morning cards carry the staff taps. ($st)"
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S978_STAFF_TAPS.sh --undo"
