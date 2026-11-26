#!/bin/bash
# install_S962_MORNING_MATCH.sh -- S962 (the parent, S529, 26-Nov-2026; D1080, the Morning Match kit C part 1; F-1678, F-1679).
#   The day check: a radd after billing is matched both ways (Docterz kept the bill / cancelled it too) -- no false parchi card;
#   a slip Docterz does not carry goes to HIS back-date list by itself (no staff 'Added'); the staff see that list with
#   'Paise liye hi nahi' and 'Dr sahab ko yaad dilayein'; the day in one line; his console line 'all matched' or the counts;
#   the slip desk's 'Fee lautai' asks Cash / UPI and the slip carries the Refunded tag at once.
#   FILES: /root/finance/day_check.py d5c95ea9 -> TO · /root/finance/slip_adjust.py 41c55a99 -> TO (refund_t, added to
#   slip_adjust on first use) · /root/finance/slip_log.py 3553a965 -> TO (the radd form only). clinic-finance is restarted (seconds).
#   [1/5] kit sums  [2/5] the ground (each file its FROM)  [3/5] HERE: make_s962.py remakes the three TO files from the live bytes;
#   the walk ALL PASS on the live code with the TO laid over it, red at T1 on the live code as it is (the control); the probe on
#   the live database, read-only, counts only: every day of 40 read with no error  [4/5] backups, swap, read-backs, clinic-finance
#   restarted, healthz 200, the doors answer (login-gated, not 404), the service log clean  [5/5] the words.
#   Any red after [4/5] began: everything put back.  DRY=1: [1]-[3] only.  --undo: the three files back (the column stays; harmless).
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s962kit && cp -rp /root/deploy/repo/deploy_kits/S962_MORNING_MATCH /tmp/s962kit && bash /tmp/s962kit/install_S962_MORNING_MATCH.sh
set -u
KIT="S962_MORNING_MATCH"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$FD/finance.db}"
A="$FD/day_check.py";   A_FROM="d5c95ea9868b5dba27cdd5bf0ea6d3db"
B="$FD/slip_adjust.py"; B_FROM="41c55a991478a89057902f8cbbea46d2"
C="$FD/slip_log.py";    C_FROM="3553a9653ab8682908d7a3f2f9c62833"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
A_TO="$(to day_check.py)"; B_TO="$(to slip_adjust.py)"; C_TO="$(to slip_log.py)"
SCR="$(mktemp -d /tmp/s962_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$1.bak_S962_${2:0:8}"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s962"
  \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
put_back() { local r=0
  put_one "$A" "$A_FROM" || r=1; put_one "$B" "$B_FROM" || r=1; put_one "$C" "$C_FROM" || r=1
  [ "$r" = 0 ] && CHANGED=0; return $r; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; for f in "$A" "$B" "$C"; do rm -f "$(dirname "$f")/.$(basename "$f").s962"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local p="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-600}" "$p" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  for p in "A:$A_FROM:$A_TO" "B:$B_FROM:$B_TO" "C:$C_FROM:$C_TO"; do n="${p%%:*}"; r="${p#*:}"; fr="${r%%:*}"; t="${r#*:}"; f="${!n}"; h="$(m5 "$f")"
    [ "$h" = "$t" ] || [ "$h" = "$fr" ] || stop "!! --undo: $f is ${h:0:8}, not S962's (a later change?) - not undoing. Tell Claude."
    [ "$h" = "$fr" ] || [ "$(m5 "$(bak "$f" "$fr")")" = "$fr" ] || stop "!! --undo: the backup of $f is not its FROM - not undoing. Tell Claude."; done
  [ "$(m5 "$A")" = "$A_FROM" ] && [ "$(m5 "$B")" = "$B_FROM" ] && [ "$(m5 "$C")" = "$C_FROM" ] && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  take_lock "--undo:" undo; CHANGED=1; put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || { release; say "!! --undo: $FSVC did not restart - tell Claude"; exit 1; }
  h="$(wait200)"; FINISHED=1; release
  [ "$h" = 200 ] || { say "!! --undo: the files are back but finance healthz is $h - send a photo of this screen to Claude"; exit 1; }
  say "$KIT: UNDONE ($FSVC restarted, finance healthz $h; slip_adjust's refund_t column and any answers are kept)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in day_check.py slip_adjust.py slip_log.py; do
  [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/5] the kit's TO $n is not as built - nothing installed"; done
say "   [1/5] kit sums ok"
for x in "$APY" "$VPY"; do [ -x "$x" ] || stop "!! [2/5] $x is not there - STOP. Tell Claude."; done
for n in "$FD/not_in_docterz.py" "$FD/clinic_register.py" "$FD/docterz_ingest.py" "$LIVE_DB"; do
  [ -f "$n" ] || stop "!! [2/5] $n is missing - STOP. Tell Claude."; done
if [ "$(m5 "$A")" = "$A_TO" ] && [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ]; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
for p in "A:$A_FROM" "B:$B_FROM" "C:$C_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; h="$(m5 "$f")"
  [ "$h" = "$fr" ] || stop "!! [2/5] $f is ${h:0:8}, not ${fr:0:8} - it changed after this kit was built: STOP. Tell Claude."; done
say "   [2/5] the ground: day_check d5c95ea9, slip_adjust 41c55a99, slip_log 3553a965"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py "$APY" "$KDIR/make_s962.py" "$A" "$B" "$C" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s962.py refused the live files - nothing installed"; }
for n in day_check.py slip_adjust.py slip_log.py; do [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/5] $n remade from the live bytes is not the kit's TO - nothing installed"; done
\cp "$KDIR/to/day_check.py" "$KDIR/to/slip_adjust.py" "$KDIR/to/slip_log.py" "$SCR/new/"
for x in "$APY" "$VPY"; do (cd "$SCR" && "$x" -c 'import py_compile,sys
for f in sys.argv[2:]: py_compile.compile(f, cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/day_check.py" "$SCR/new/slip_adjust.py" "$SCR/new/slip_log.py") \
  || stop "!! [3/5] a file does not compile under $x - nothing installed"; done
W="$(py "$VPY" "$KDIR/walk_s962.py" "$SCR/new")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q "^ALL PASS$" || { echo "$W" | grep -E "^FAIL|Error" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
WC="$(py "$VPY" "$KDIR/walk_s962.py" "$SCR/old")"; rc=$?
[ "$rc" != 0 ] && echo "$WC" | grep -q "^FAIL  T1 " && ! echo "$WC" | grep -q "^Traceback" || stop "!! [3/5] the control (the walk on the live code as it is) did not go red at T1 - nothing installed"
if [ -n "${PROBE_CMD:-}" ]; then PR="$($PROBE_CMD)"; else PR="$(py "$VPY" "$KDIR/probe_s962.py" "$SCR/new" "$LIVE_DB" 40 | tail -1)"; fi
echo "$PR" | grep -q "^PROBE days " || { echo "$PR"; stop "!! [3/5] the probe on the live database did not run - nothing installed"; }
pc="$(echo "$PR" | awk '{print $5}')"; pe="$(echo "$PR" | awk '{print $7}')"
[ "${pe:-1}" = 0 ] || { echo "         $PR"; stop "!! [3/5] on the live database the new day check raised on a day (errors $pe) - nothing installed. Send a photo to Claude."; }
[ "${pc:-0}" -ge "${PROBE_MIN_DAYS:-1}" ] || { echo "         $PR"; stop "!! [3/5] the probe checked no day on the live database - it proves nothing; nothing installed. Send a photo to Claude."; }
say "   [3/5] walk ALL PASS ($(echo "$W" | grep -c '^PASS')); control red; three TO remade from the live bytes"
say "         the live shape (read-only, counts only): $PR"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for p in "A:$A_FROM" "B:$B_FROM" "C:$C_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || stop "!! [4/5] the backup of $(basename "$f") did not read back - nothing placed"; done
CHANGED=1
swap_in "$B" "$KDIR/to/slip_adjust.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/5] slip_adjust.py did not read back"
swap_in "$C" "$KDIR/to/slip_log.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/5] slip_log.py did not read back"
swap_in "$A" "$KDIR/to/day_check.py" && [ "$(m5 "$A")" = "$A_TO" ] || restore "[4/5] day_check.py did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
YD="$(TZ=Asia/Kolkata date -d yesterday +%F 2>/dev/null || echo 2026-11-26)"
d1=$(door "/finance/clinic/check/$YD"); case "$d1" in 404|000|5*) restore "the day check answers $d1 (not mounted)";; esac
d2=$(door /finance/clinic/check/api/mine); case "$d2" in 404|000|5*) restore "the day check's staff door answers $d2 (not mounted)";; esac
d3=$(door /finance/slips/desk); case "$d3" in 404|000|5*) restore "the slip desk answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|day_check|slip_adjust|slip_log|NOT mounted" | head -3)   # 'day_check NOT mounted' is printed by clinic_register.init
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [4/5] placed and read back: day_check $(m8 "$A"), slip_adjust $(m8 "$B"), slip_log $(m8 "$C"); $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the day check $d1, its staff door $d2, the desk $d3 (login-gated); the log clean"
FINISHED=1; CHANGED=0; release
say "   [5/5] ON: the day check matches a radd both ways and sends a slip Docterz lacks to his back-date list; the desk's 'Fee lautai' asks Cash / UPI."
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S962_MORNING_MATCH.sh --undo"
