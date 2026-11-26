#!/bin/bash
# install_S960_EVENING_CHECK.sh -- S960 (the parent, S527, 26-Nov-2026; D1080, the Morning Match kit A): the evening check.
#   A consultation report of today, taken in the evening by either road, is checked AT ONCE against the day's slips; Shavez and
#   reception get one push per export ("N parchi Docterz mein nahi" + names / "sab parchi Docterz mein" / "kaam poora"); the slip
#   desk shows the list with "Paise nahi liye"; the Drive pickup runs every minute 19:00-22:59 Mon-Sat.
#   FILES: /root/finance/docterz_pickup.py a6cbdb8b -> TO (one hook) · /root/finance/parchi_desk.py 10532553 -> TO (the box, its
#   doors) · NEW /root/finance/evening_check.py · crontab + one line '# S960_EVENING_PICKUP'. clinic-finance is restarted (seconds).
#   [1/5] kit sums  [2/5] the ground (each file its FROM, no evening_check.py, no S960 cron line)  [3/5] HERE: make_s960.py remakes
#   the two TO files from the live bytes; the walk ALL PASS on the live code with the TO laid over it (the live callback_clock.py's
#   real send road included), red on the live code as it is (the control); the probe on the live database, read-only, counts only
#   [4/5] backups, swap, read-backs, the cron line, clinic-finance restarted, healthz 200, the desk's new door answers (login-gated,
#   not 404 -- the finance gate answers 302 to any unsigned path, so the real proof of the mount is the log: parchi_desk prints
#   'evening_check NOT mounted' on a failure, and the walk mounted the doors with the live code), the service log clean,
#   evening_check --status and --sweep run on the box's python  [5/5] the words.  Any red after [4/5] began: everything put back.
#   DRY=1: [1]-[3] only.  --undo: the two files back, evening_check.py removed (its table kept), the cron line removed, restarted.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s960kit && cp -rp /root/deploy/repo/deploy_kits/S960_EVENING_CHECK /tmp/s960kit && bash /tmp/s960kit/install_S960_EVENING_CHECK.sh
set -u
KIT="S960_EVENING_CHECK"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; FD="${FD:-$ROOT/finance}"; PD="${PD:-$ROOT/portal}"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-$ROOT/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CRONTAB="${CRONTAB:-crontab}"; LIVE_DB="${LIVE_DB:-$FD/finance.db}"
A="$FD/docterz_pickup.py"; A_FROM="a6cbdb8ba255c5f640aa402a653e401a"
B="$FD/parchi_desk.py";    B_FROM="1053255360f821e0007759edd9cf685b"
C="$FD/evening_check.py"
MARK="# S960_EVENING_PICKUP"
CLINE="* 19-22 * * 1-6 [ -e /root/finance/_off/ALL_OFF ] || { flock -n /tmp/docterz_pickup.lock /root/wa/venv/bin/python3 -B /root/finance/docterz_pickup.py >> /root/finance/logs/docterz_pickup.log 2>&1; /root/wa/venv/bin/python3 -B /root/finance/evening_check.py --sweep >> /root/finance/logs/evening_check.log 2>&1; } $MARK the Docterz exports from Drive every minute at closing (Mon-Sat 19:00-22:59), then the evening check's sweep"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
A_TO="$(to docterz_pickup.py)"; B_TO="$(to parchi_desk.py)"; C_TO="$(to evening_check.py)"
SCR="$(mktemp -d /tmp/s960_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; CHANGED=0; FINISHED=0; T0="$(date +%s)"
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
bak() { echo "$1.bak_S960_${2:0:8}"; }
CBAK="$FD/crontab.bak_S960"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
has_cron() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
release() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s960"
  if [ -f "$1" ]; then \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"
  else \cp "$2" "$t" && chmod --reference="$A" "$t" && chown --reference="$A" "$t" && mv -f "$t" "$1"; fi; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
cron_out() { has_cron || return 0; "$CRONTAB" -l 2>/dev/null | grep -vF "$MARK" > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" && ! has_cron && say "   the S960 cron line removed"; }
put_back() { local r=0
  put_one "$A" "$A_FROM" || r=1; put_one "$B" "$B_FROM" || r=1
  if [ -f "$C" ]; then if [ "$(m5 "$C")" = "$C_TO" ]; then rm -f "$C" && say "   evening_check.py removed"; else say "   !! evening_check.py is $(m8 "$C"), not S960's - left"; r=1; fi; fi
  cron_out || r=1
  [ "$r" = 0 ] && CHANGED=0; return $r; }
restart() { "$SYSTEMCTL" restart "$FSVC"; }
restore() { trap '' INT TERM HUP; say "!! RED ($1) - putting back"; put_back; restart || true
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; restart || true; fi
  release; rm -rf "${SCR:?}"; for f in "$A" "$B" "$C"; do rm -f "$(dirname "$f")/.$(basename "$f").s960"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
py() { local p="$1"; shift; (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Kolkata timeout "${PY_TIMEOUT:-600}" "$p" -W ignore -B "$@" 2>&1); }

if [ "${1:-}" = "--undo" ]; then
  for p in "A:$A_FROM:$A_TO" "B:$B_FROM:$B_TO"; do n="${p%%:*}"; r="${p#*:}"; fr="${r%%:*}"; t="${r#*:}"; f="${!n}"; h="$(m5 "$f")"
    [ "$h" = "$t" ] || [ "$h" = "$fr" ] || stop "!! --undo: $f is ${h:0:8}, not S960's (a later change?) - not undoing. Tell Claude."
    [ "$h" = "$fr" ] || [ "$(m5 "$(bak "$f" "$fr")")" = "$fr" ] || stop "!! --undo: the backup of $f is not its FROM - not undoing. Tell Claude."; done
  [ "$(m5 "$A")" = "$A_FROM" ] && [ "$(m5 "$B")" = "$B_FROM" ] && [ ! -f "$C" ] && ! has_cron && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  take_lock "--undo:" undo; CHANGED=1; put_back || { restart || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  restart || { release; say "!! --undo: $FSVC did not restart - tell Claude"; exit 1; }
  h="$(wait200)"; FINISHED=1; release; say "$KIT: UNDONE ($FSVC restarted, finance healthz $h; the table evening_check_push and any 'Paise nahi liye' answers are kept)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/5] KIT_ID.txt names another kit - nothing installed"
for n in docterz_pickup.py parchi_desk.py evening_check.py; do
  [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/5] the kit's TO $n is not as built - nothing installed"; done
say "   [1/5] kit sums ok"
for x in "$APY" "$VPY"; do [ -x "$x" ] || stop "!! [2/5] $x is not there - STOP. Tell Claude."; done
for n in "$PD/callback_clock.py" "$FD/slip_log.py" "$FD/not_in_docterz.py" "$FD/slip_adjust.py" "$FD/docterz_ingest.py" "$FD/dx_feed.py" "$LIVE_DB"; do
  [ -f "$n" ] || stop "!! [2/5] $n is missing - STOP. Tell Claude."; done
if [ "$(m5 "$A")" = "$A_TO" ] && [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ] && has_cron; then say "$KIT: ALREADY in place - nothing to do"; exit 0; fi
for p in "A:$A_FROM" "B:$B_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; h="$(m5 "$f")"
  [ "$h" = "$fr" ] || stop "!! [2/5] $f is ${h:0:8}, not ${fr:0:8} - it changed after this kit was built: STOP. Tell Claude."; done
[ -f "$C" ] && stop "!! [2/5] $C already exists and is not S960's - STOP. Tell Claude."
has_cron && stop "!! [2/5] the crontab already holds an S960 line - STOP. Tell Claude."
"$CRONTAB" -l > "$SCR/cron.now" 2>/dev/null || stop "!! [2/5] the crontab could not be read - STOP. Tell Claude."
grep -q "S443_DOCTERZ_PICKUP" "$SCR/cron.now" || stop "!! [2/5] the crontab has no S443 Docterz pickup line - STOP. Tell Claude."
say "   [2/5] the ground: docterz_pickup a6cbdb8b, parchi_desk 10532553; no evening_check.py; no S960 cron line; the clock $(m8 "$PD/callback_clock.py")"
mkdir -p "$SCR/new" "$SCR/old" "$SCR/remade"
\cp -p "$FD"/*.py "$SCR/new/" && \cp -p "$FD"/*.py "$SCR/old/" || stop "!! [3/5] could not lay out the walk - nothing installed"
py "$APY" "$KDIR/make_s960.py" "$A" "$B" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/5] make_s960.py refused the live files - nothing installed"; }
for n in docterz_pickup.py parchi_desk.py; do [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/5] $n remade from the live bytes is not the kit's TO - nothing installed"; done
\cp "$KDIR/to/docterz_pickup.py" "$KDIR/to/parchi_desk.py" "$KDIR/to/evening_check.py" "$SCR/new/"
for x in "$APY" "$VPY"; do (cd "$SCR" && "$x" -c 'import py_compile,sys
for f in sys.argv[2:]: py_compile.compile(f, cfile=sys.argv[1], doraise=True)' "$SCR/x.pyc" "$SCR/new/evening_check.py" "$SCR/new/docterz_pickup.py" "$SCR/new/parchi_desk.py") \
  || stop "!! [3/5] a file does not compile under $x - nothing installed"; done
W="$(W960_REAL_CC="$PD/callback_clock.py" py "$APY" "$KDIR/walk_s960.py" "$SCR/new")"; rc=$?
[ "$rc" = 0 ] && echo "$W" | tail -1 | grep -q "^ALL PASS$" || { echo "$W" | grep -E "^FAIL|Error" | head -8; stop "!! [3/5] the walk is not all green here - nothing installed"; }
echo "$W" | grep -q "^PASS  C1 " || stop "!! [3/5] the walk did not try the live clock's send road - nothing installed"
WC="$(py "$APY" "$KDIR/walk_s960.py" "$SCR/old")"; rc=$?
[ "$rc" != 0 ] && echo "$WC" | grep -q "^FAIL  T1 " && ! echo "$WC" | grep -q "^Traceback" || stop "!! [3/5] the control (the walk on the live code as it is) did not go red at T1 - nothing installed"
if [ -n "${PROBE_CMD:-}" ]; then PR="$($PROBE_CMD)"; else PR="$(py "$APY" "$KDIR/probe_s960.py" "$SCR/new" "$LIVE_DB" 6 | tail -1)"; fi
echo "$PR" | grep -q "^PROBE days " || { echo "$PR"; stop "!! [3/5] the probe on the live database did not run - nothing installed"; }
pd="$(echo "$PR" | awk '{print $3}')"; pu="$(echo "$PR" | awk '{print $11}')"
[ "$(( ${pd:-0} - ${pu:-0} ))" -ge "${PROBE_MIN_DAYS:-1}" ] || { echo "         $PR"; stop "!! [3/5] the probe found no exported day it could read on the live database - it proves nothing; nothing installed. Send a photo to Claude."; }
[ "$(echo "$PR" | awk '{print $7}')" = 0 ] || { echo "         $PR"; stop "!! [3/5] on the live shape the evening check names slips his own list does not (mine_only) - nothing installed. Send a photo to Claude."; }
say "   [3/5] walk ALL PASS ($(echo "$W" | grep -c '^PASS')) with the live clock's send road; control red; two TO remade from the live bytes"
say "         the live shape (read-only, counts only): $PR"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed"; exit 0; }

take_lock "[4/5]" install
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/5] finance healthz $f0 before the install - nothing installed"
for p in "A:$A_FROM" "B:$B_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || stop "!! [4/5] the backup of $(basename "$f") did not read back - nothing placed"; done
\cp "$SCR/cron.now" "$CBAK" && chmod 600 "$CBAK" || stop "!! [4/5] the crontab backup could not be written - nothing placed"
CHANGED=1
swap_in "$C" "$KDIR/to/evening_check.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/5] evening_check.py did not read back"
swap_in "$A" "$KDIR/to/docterz_pickup.py" && [ "$(m5 "$A")" = "$A_TO" ] || restore "[4/5] docterz_pickup.py did not read back"
swap_in "$B" "$KDIR/to/parchi_desk.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/5] parchi_desk.py did not read back"
"$CRONTAB" -l > "$SCR/cron.again" 2>/dev/null && cmp -s "$SCR/cron.now" "$SCR/cron.again" || restore "[4/5] the crontab changed while the kit was checking - nothing of the crontab touched; run the line again"
{ cat "$SCR/cron.now"; echo "$CLINE"; } > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" && has_cron || restore "[4/5] the cron line was not added"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" = "$(( $(grep -c . "$SCR/cron.now") + 1 ))" ] || restore "[4/5] the crontab is not the old one plus one line"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/5] forced red (rehearsal)"
restart || restore "$FSVC did not restart"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/slips/desk/api/evening); case "$d1" in 404|000|5*) restore "the desk's new door answers $d1 (not mounted)";; esac
d2=$(door /finance/slips/desk); case "$d2" in 404|000|5*) restore "the slip desk answers $d2";; esac
d3=$(door /finance/api/reception/report); case "$d3" in 404|000|5*) restore "reception's upload door answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "Traceback|evening_check|parchi_desk|docterz_pickup|NOT mounted" | head -3)   # 'evening_check NOT mounted' is printed by parchi_desk.init
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
st=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$C" --status --db "$LIVE_DB" 2>&1 | tail -1)
echo "$st" | grep -q "^EVENING S960 1 " || restore "[4/5] evening_check --status did not run on the box's python ($st)"
sw=$(cd "$FD" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$VPY" -W ignore -B "$C" --sweep --no-push --db "$SCR/sweep_none.db" 2>&1 | tail -1)
[ -z "$sw" ] || restore "[4/5] evening_check --sweep did not run quietly on the box's python ($sw)"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/5] forced red (rehearsal)"
say "   [4/5] placed and read back: docterz_pickup $(m8 "$A"), parchi_desk $(m8 "$B"), evening_check $(m8 "$C"); the cron line in; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), healthz $c1, the desk's new door $d1, the desk $d2, reception's door $d3 (login- or key-gated); the log clean"
say "         today: $(echo "$st" | sed 's/^EVENING S960 1 //')"
FINISHED=1; CHANGED=0; release
say "   [5/5] ON: tonight's export is checked the moment it reaches the server; Shavez and reception get the push; the desk shows the list."
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S960_EVENING_CHECK.sh --undo"
