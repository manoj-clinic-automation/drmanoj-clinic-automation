#!/bin/bash
# install_S957_PUNCH_DOOR.sh -- S957 (the parent, S523, 26-Nov-2026; roadmap E0, F-773): the punch listener admits only the
#   attendance machine's own mark (a punch without it is KEPT ASIDE, never lost, and the health leg "punch door" turns red);
#   NEW presence.py (punched in / out today, the roster when no punch by 09:30 or the machine is silent); the call-back clock reads
#   the duty through it; the nightly source summary matches the listener's corrected rows (S792) and leaves refused punches out.
#   FILES: /root/attlistener_v2.py 588ea08e -> TO · /root/att_source_summary.py 2aa34b88 -> TO · /root/portal/callback_clock.py
#   5fbcd29c -> TO · NEW /root/portal/presence.py · /root/finance/freshness_legs.json f5c68b24 -> TO (46 legs) · NEW
#   /root/punch_door.json (0600, written HERE from the watch's own evidence -- the mark is never in the kit or the repository).
#   The listener (attlistener.service) is restarted: a second or two; the machine re-sends anything it was sending.
#   [1/6] kit sums  [2/6] the ground (every file its FROM, or all already S957's)  [3/6] HERE, with the box's own pythons and the
#   live calls_console.py / freshness.py: make_s957.py remakes the four TO files from the live bytes; walk_s957 all green on the TO,
#   red on the FROM (the control); S953's walk green on the TO (reception 0, roster 0); the listener and the summary compile under
#   /usr/bin/python3; THE EVIDENCE: the new summary run read-only on the LIVE source log + punch file decides the door (enforce |
#   watch | none); THE REPLAY: every punch the machine sent in the last 7 days, through the new listener with that door, in a temp
#   folder: all admitted (else the door goes in as watch), and a punch without the mark and one with a wrong mark refused;
#   presence.py read-only on the live files says ok  [4/6] backups + swaps + read-backs, the door file, the listener restarted, it
#   answers, its state says the door's mode  [5/6] the clock --dry with presence.py, the legs file loads 46 legs, the listener's
#   journal clean  [6/6] the words.  Any red after [4/6] began, or the run killed: every file put back, the new ones removed, the
#   listener restarted.  DRY=1: [1]-[3] only.  --undo: every backup back, presence.py and the door file removed (the refused
#   file and the door's state are kept), the listener restarted.
#   cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s957kit && cp -rp /root/deploy/repo/deploy_kits/S957_PUNCH_DOOR /tmp/s957kit && bash /tmp/s957kit/install_S957_PUNCH_DOOR.sh
set -u
KIT="S957_PUNCH_DOOR"; KDIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="${ROOT:-/root}"; PD="${PD:-$ROOT/portal}"; FD="${FD:-$ROOT/finance}"
APY="${APY:-$ROOT/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
LSVC="${LSVC:-attlistener}"; LPORT="${LPORT:-8041}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNAL="${JOURNAL:-journalctl}"
SRCLOG="${SRCLOG:-$ROOT/attlistener_sources.jsonl}"; PUNCHES="${PUNCHES:-$ROOT/punches.csv}"; CONF="${CONF:-$ROOT/punch_door.json}"
DSTATE="${DSTATE:-$ROOT/punch_door.state.json}"
A="$ROOT/attlistener_v2.py";      A_FROM="588ea08e744d11fc9fbbee7e41d7515c"
B="$ROOT/att_source_summary.py";  B_FROM="2aa34b8862c178c236bc38b3dba73847"
C="$PD/callback_clock.py";        C_FROM="5fbcd29cb50a97ce46854d97addba9cd"
D="$PD/presence.py"
E="$FD/freshness_legs.json";      E_FROM="f5c68b240f179a8aaee7d6e730dfcd07"
to() { awk -v f="to/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
A_TO="$(to attlistener_v2.py)"; B_TO="$(to att_source_summary.py)"; C_TO="$(to callback_clock.py)"; D_TO="$(to presence.py)"; E_TO="$(to freshness_legs.json)"
SCR="$(mktemp -d /tmp/s957_inst.XXXXXX)"; chmod 700 "$SCR"; TOOK_LOCK=0; OFF_MINE=0; CHANGED=0; FINISHED=0; T0="$(date '+%F %T')"; CONF_MINE=0
bak() { echo "$1.bak_S957_${2:0:8}"; }
m5() { if [ -f "$1" ]; then md5sum "$1" | awk '{print $1}'; else echo ABSENT; fi; }
m8() { m5 "$1" | cut -c1-8; }
say() { echo "$@"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
stop() { say "$1"; release; exit 1; }
take_lock() { [ -d "$(dirname "$LOCK")" ] || stop "!! $1 $(dirname "$LOCK") does not exist - STOP. Tell Claude."
  mkdir "$LOCK" 2>/dev/null || stop "!! $1 another build holds $LOCK - try again in five minutes. Nothing changed."; TOOK_LOCK=1; echo "$KIT $2" > "$LOCK/owner"
  if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi; }
swap_in() { local t="$(dirname "$1")/.$(basename "$1").s957"
  if [ -f "$1" ]; then \cp "$2" "$t" && chmod --reference="$1" "$t" && chown --reference="$1" "$t" && mv -f "$t" "$1"
  else \cp "$2" "$t" && chmod 644 "$t" && mv -f "$t" "$1"; fi; }
put_one() { local f="$1" from="$2"; local b; b="$(bak "$f" "$from")"
  [ "$(m5 "$f")" = "$from" ] && return 0
  if [ "$(m5 "$b")" = "$from" ] && swap_in "$f" "$b" && [ "$(m5 "$f")" = "$from" ]; then say "   $(basename "$f") back: $(m8 "$f")"; return 0; fi
  say "   !! $(basename "$f") NOT back: $(m8 "$f") (backup $(m8 "$b"), expected ${from:0:8})"; return 1; }
put_back() { local r=0
  put_one "$A" "$A_FROM" || r=1; put_one "$B" "$B_FROM" || r=1; put_one "$E" "$E_FROM" || r=1; put_one "$C" "$C_FROM" || r=1
  if [ -f "$D" ]; then if [ "$(m5 "$D")" = "$D_TO" ]; then rm -f "$D" && say "   presence.py removed"; else say "   !! presence.py is $(m8 "$D"), not S957's - left"; r=1; fi; fi
  if [ "$CONF_MINE" = 1 ] || [ "${UNDO:-0}" = 1 ]; then [ -f "$CONF" ] && grep -q '"kit": "S957"' "$CONF" && rm -f "$CONF" && say "   the door file removed (the door open again)"; fi
  [ "$r" = 0 ] && CHANGED=0; return $r; }
lsvc_up() { "$SYSTEMCTL" restart "$LSVC" || return 1; local a=x; for _t in 1 2 3 4 5 6 7 8; do sleep "${NAP:-2}"; a="$("$SYSTEMCTL" is-active "$LSVC" 2>/dev/null)"; [ "$a" = active ] && break; done; [ "$a" = active ]; }
ack() { if [ -n "${ACK_CMD:-}" ]; then $ACK_CMD; else "$SPY" -c '
import http.client, sys
c = http.client.HTTPConnection("127.0.0.1", int(sys.argv[1]), timeout=5)
c.request("POST", "/", body=b"\x00\x00\x00\x00{}\x00", headers={"request_code": "receive_cmd", "Content-Type": "application/octet-stream"})
r = c.getresponse(); r.read(); print(dict((k.lower(), v) for k, v in r.getheaders()).get("response_code"))' "$LPORT" 2>&1 | tail -1; fi; }
restore() { say "!! RED ($1) - putting back"; put_back; lsvc_up || true
  say "   $LSVC $("$SYSTEMCTL" is-active "$LSVC" 2>/dev/null), ack $(ack). Send a photo of this screen to Claude."; release; exit 1; }
on_exit() { trap '' INT TERM HUP
  if [ "$FINISHED" = 0 ] && [ "$CHANGED" = 1 ]; then say "!! the run ended before its proof - putting back"; put_back; lsvc_up || true; fi
  release; rm -rf "${SCR:?}"; rm -f "$CONF.s957tmp"; for f in "$A" "$B" "$C" "$D" "$E"; do rm -f "$(dirname "$f")/.$(basename "$f").s957"; done
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
trap 'exit 130' INT TERM HUP
pya() { (cd "$SCR" && TMPDIR="$SCR" PYTHONDONTWRITEBYTECODE=1 TZ=Asia/Kolkata timeout "${PYA_TIMEOUT:-600}" "$APY" -W ignore -B "$@" 2>&1); }
clockdry() { if [ -n "${CLOCKDRY_CMD:-}" ]; then $CLOCKDRY_CMD "$1"; else (cd "$SCR" && CC_STORE="$SCR/never_written.db" RING_PORTAL_DIR="$1" TZ=Asia/Kolkata \
  PYTHONDONTWRITEBYTECODE=1 timeout 120 "$APY" -B "$1/callback_clock.py" --dry 2>&1 | tail -2); fi; }
pres() { if [ -n "${PRES_CMD:-}" ]; then $PRES_CMD "$1"; else (cd "$SCR" && TZ=Asia/Kolkata PYTHONDONTWRITEBYTECODE=1 timeout 60 "$APY" -B "$1/presence.py" 2>&1 | tail -1); fi; }

if [ "${1:-}" = "--undo" ]; then
  UNDO=1
  for p in "A:$A_FROM:$A_TO" "B:$B_FROM:$B_TO" "C:$C_FROM:$C_TO" "E:$E_FROM:$E_TO"; do
    n="${p%%:*}"; r="${p#*:}"; fr="${r%%:*}"; t="${r#*:}"; f="${!n}"; h="$(m5 "$f")"
    [ "$h" = "$t" ] || [ "$h" = "$fr" ] || stop "!! --undo: $f is ${h:0:8}, not S957's (a later change?) - not undoing. Tell Claude."
    [ "$h" = "$fr" ] || [ "$(m5 "$(bak "$f" "$fr")")" = "$fr" ] || stop "!! --undo: the backup of $f is not its FROM - not undoing. Tell Claude."
  done
  [ "$(m5 "$A")" = "$A_FROM" ] && [ "$(m5 "$B")" = "$B_FROM" ] && [ "$(m5 "$C")" = "$C_FROM" ] && [ "$(m5 "$E")" = "$E_FROM" ] && [ ! -f "$D" ] \
    && ! grep -qs '"kit": "S957"' "$CONF" && { say "-- $KIT is not installed; nothing to undo"; exit 0; }
  take_lock "--undo:" undo; CHANGED=1; put_back || { lsvc_up || true; release; say "!! --undo incomplete - tell Claude"; exit 1; }
  lsvc_up || { release; say "!! --undo: $LSVC did not come back - tell Claude"; exit 1; }
  release; say "$KIT: UNDONE ($LSVC $("$SYSTEMCTL" is-active "$LSVC" 2>/dev/null), ack $(ack); the refused file and the door's state are kept)"; exit 0
fi

cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || stop "!! [1/6] KIT_ID.txt names another kit - nothing installed"
for n in attlistener_v2.py att_source_summary.py callback_clock.py presence.py freshness_legs.json; do
  [ -n "$(to $n)" ] && [ "$(m5 "$KDIR/to/$n")" = "$(to $n)" ] || stop "!! [1/6] the kit's TO $n is not as built - nothing installed"; done
say "   [1/6] kit sums ok"
[ -x "$APY" ] || stop "!! [2/6] $APY is not there - STOP. Tell Claude."
[ -x "$SPY" ] || stop "!! [2/6] $SPY is not there - STOP. Tell Claude."
for n in "$PD/calls_console.py" "$PD/calls_staff.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$FD/freshness.py" "$SRCLOG" "$PUNCHES"; do
  [ -f "$n" ] || stop "!! [2/6] $n is missing - STOP. Tell Claude."; done
if [ "$(m5 "$A")" = "$A_TO" ] && [ "$(m5 "$B")" = "$B_TO" ] && [ "$(m5 "$C")" = "$C_TO" ] && [ "$(m5 "$D")" = "$D_TO" ] && [ "$(m5 "$E")" = "$E_TO" ]; then
  say "$KIT: ALREADY in place - nothing to do (door: $(grep -o '"mode": "[a-z]*"' "$CONF" 2>/dev/null | cut -d'"' -f4 || echo open))"; exit 0; fi
for p in "A:$A_FROM" "B:$B_FROM" "C:$C_FROM" "E:$E_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; h="$(m5 "$f")"
  [ "$h" = "$fr" ] || stop "!! [2/6] $f is ${h:0:8}, not ${fr:0:8} - it changed after this kit was built: STOP. Tell Claude."; done
[ -f "$D" ] && stop "!! [2/6] $D already exists and is not S957's - STOP. Tell Claude."
[ -f "$CONF" ] && stop "!! [2/6] $CONF already exists - STOP. Tell Claude."
say "   [2/6] the ground: the listener 588ea08e, the summary 2aa34b88, the clock 5fbcd29c, the legs f5c68b24; no presence.py, no door file"
mkdir -p "$SCR/from" "$SCR/to" "$SCR/remade" "$SCR/r53"
for d in from to; do \cp "$PD/calls_console.py" "$FD/freshness.py" "$SCR/$d/"; done
\cp "$A" "$B" "$C" "$SCR/from/"; \cp "$KDIR/to/attlistener_v2.py" "$KDIR/to/att_source_summary.py" "$KDIR/to/callback_clock.py" "$KDIR/to/presence.py" "$SCR/to/"
pya "$KDIR/make_s957.py" "$A" "$B" "$C" "$E" "$SCR/remade" > "$SCR/make.txt" || { cat "$SCR/make.txt"; stop "!! [3/6] make_s957.py refused the live files - nothing installed"; }
for n in attlistener_v2.py att_source_summary.py callback_clock.py freshness_legs.json; do
  [ "$(m5 "$SCR/remade/$n")" = "$(to $n)" ] || stop "!! [3/6] $n remade from the live bytes is not the kit's TO - nothing installed"; done
pya "$KDIR/walk_s957.py" walk "$SCR/to" "$KDIR/to/freshness_legs.json" > "$SCR/walk.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/walk.txt" | grep -q "^ALL PASS$" || { grep -E "^FAIL" "$SCR/walk.txt" | head -8; stop "!! [3/6] the walk is not all green here - nothing installed"; }
pya "$KDIR/walk_s957.py" walk "$SCR/from" "$E" > "$SCR/ctl.txt"; rc=$?
[ "$rc" != 0 ] && grep -q "^FAIL  A3 ... and NOT in punches.csv" "$SCR/ctl.txt" && ! grep -q "^Traceback" "$SCR/ctl.txt" \
  || stop "!! [3/6] the control (the walk on the FROM code) did not go red - the walk proves nothing here; nothing installed"
\cp "$PD/calls_console.py" "$PD/calls_staff.py" "$PD/ring_outcome.py" "$PD/ring_common.py" "$KDIR/to/callback_clock.py" "$KDIR/to/presence.py" "$SCR/r53/"
(export PORTAL_STAFF_CONSOLE_RECEPTION=0 PORTAL_PRESENCE_ROSTER=0 PRESENCE_SILENCE_STATE="$SCR/none.json" SR_DB_PATH="$SCR/none.db"; pya "$KDIR/walk_s953.py" walk "$SCR/r53") > "$SCR/w53.txt"; rc=$?
[ "$rc" = 0 ] && tail -1 "$SCR/w53.txt" | grep -q "^ALL PASS$" || { grep -E "FAIL|Error" "$SCR/w53.txt" | head -8; stop "!! [3/6] S953's own walk is not all green on the TO clock - nothing installed"; }
for n in attlistener_v2.py att_source_summary.py; do (cd "$SCR" && "$SPY" -c 'import py_compile,sys; py_compile.compile(sys.argv[1], cfile=sys.argv[2], doraise=True)' "$SCR/to/$n" "$SCR/x.pyc") \
  || stop "!! [3/6] $n does not compile under $SPY - nothing installed"; done
# THE EVIDENCE -- the new summary, read-only on the live files, into the 0700 scratch; it decides the door
(cd "$SCR" && ATT_SUMMARY_KEEP=1 ATT_SOURCE_LOG="$SRCLOG" ATT_PUNCH_CSV="$PUNCHES" ATT_SOURCE_SUMMARY="$SCR/summary.json" timeout 120 "$SPY" -B "$SCR/to/att_source_summary.py" > "$SCR/sum.txt" 2>&1) \
  || { tail -2 "$SCR/sum.txt"; stop "!! [3/6] the new summary could not read the live source log - nothing installed"; }
dec="$(pya "$KDIR/door_s957.py" decide "$SCR/summary.json" "$SCR/door.json" | tail -1)"
MODE="$(echo "$dec" | awk '{print $2}')"
case "$MODE" in enforce|watch|none) ;; *) echo "$dec"; stop "!! [3/6] the evidence could not be judged - nothing installed";; esac
REP="(no door: no replay)"
if [ "$MODE" != none ]; then
  REP="$(pya "$KDIR/door_s957.py" replay "$SCR/to/attlistener_v2.py" "$SRCLOG" "$SCR/door.json" 7 | grep '^REPLAY punches')"
  echo "$REP" | grep -q "^REPLAY punches" || stop "!! [3/6] the replay of the last 7 days did not run - nothing installed"
  rm_="$(echo "$REP" | awk '{print $5}')"; rs="$(echo "$REP" | awk '{print $7}')"; rr="$(echo "$REP" | awk '{print $9}')"
  sn="$(echo "$REP" | awk '{print $11}')"; sw="$(echo "$REP" | awk '{print $13}')"
  if [ "$MODE" = enforce ]; then
    if [ "${rm_:-0}" -lt 1 ] || [ "$rs" != "$rm_" ] || [ "$rr" != 0 ]; then
      MODE=watch; sed -i 's/"mode": "enforce"/"mode": "watch"/' "$SCR/door.json"; dec="DECIDE watch (the replay refused a genuine punch: $REP)"
    elif [ "$sn" != refused ] || [ "$sw" != refused ]; then stop "!! [3/6] the replay: a punch without the right mark was ADMITTED - nothing installed. Tell Claude."; fi
  fi
fi
pr="$(pres "$SCR/to")"
echo "$pr" | grep -q "^PRESENCE .* ok True" || { echo "$pr"; stop "!! [3/6] presence.py could not read today's live files - nothing installed"; }
say "   [3/6] walk ALL PASS ($(grep -c '^PASS' "$SCR/walk.txt")); control red; S953's walk ALL PASS on the TO clock; four TO remade from the live bytes"
say "         THE EVIDENCE: $(head -c 160 "$SCR/sum.txt" | sed 's/^[0-9-]* [0-9:]*  //')"
say "         -> $dec"
say "         THE REPLAY (last 7 days, temp folder): $REP"
say "         today, read-only: $(echo "$pr" | sed 's/^PRESENCE [^:]*: //')"
[ "${DRY:-0}" = 1 ] && { say "$KIT: DRY ok - nothing changed (the door would be: $MODE)"; exit 0; }

take_lock "[4/6]" install
for p in "A:$A_FROM" "B:$B_FROM" "C:$C_FROM" "E:$E_FROM"; do n="${p%%:*}"; fr="${p#*:}"; f="${!n}"; b="$(bak "$f" "$fr")"
  \cp -p "$f" "$b" && chmod 600 "$b" && [ "$(m5 "$b")" = "$fr" ] || restore "[4/6] the backup of $(basename "$f") did not read back"; done
CHANGED=1
swap_in "$D" "$KDIR/to/presence.py" && [ "$(m5 "$D")" = "$D_TO" ] || restore "[4/6] presence.py did not read back"
swap_in "$E" "$KDIR/to/freshness_legs.json" && [ "$(m5 "$E")" = "$E_TO" ] || restore "[4/6] the legs did not read back"
swap_in "$B" "$KDIR/to/att_source_summary.py" && [ "$(m5 "$B")" = "$B_TO" ] || restore "[4/6] the summary did not read back"
# the nightly file is rewritten now by the new summary (the mark's value and the full addresses out of it at once, not at 01:25)
(cd "$SCR" && ATT_SOURCE_LOG="$SRCLOG" ATT_PUNCH_CSV="$PUNCHES" ATT_SOURCE_SUMMARY="$FD/punch_sources_summary.json" timeout 120 "$SPY" -B "$B" > "$SCR/sum2.txt" 2>&1) \
  && [ -n "$(sed -n 's/.*"value"[^"]*"\([^"]*\)".*/\1/p' "$SCR/door.json" 2>/dev/null)" ] && ! grep -qF "$(sed -n 's/.*"value"[^"]*"\([^"]*\)".*/\1/p' "$SCR/door.json")" "$FD/punch_sources_summary.json" \
  || [ "$MODE" = none ] || restore "[4/6] the nightly summary could not be rewritten without the mark"
swap_in "$C" "$KDIR/to/callback_clock.py" && [ "$(m5 "$C")" = "$C_TO" ] || restore "[4/6] the clock did not read back"
if [ "$MODE" != none ]; then \cp "$SCR/door.json" "$CONF.s957tmp" && chmod 600 "$CONF.s957tmp" && mv -f "$CONF.s957tmp" "$CONF" && CONF_MINE=1 \
  && [ "$(stat -c %a "$CONF")" = 600 ] || restore "[4/6] the door file was not written 0600"; fi
swap_in "$A" "$KDIR/to/attlistener_v2.py" && [ "$(m5 "$A")" = "$A_TO" ] || restore "[4/6] the listener did not read back"
[ "${FORCE_KILL_AT:-}" = "4" ] && kill -TERM $$
[ "${FORCE_RED_AT:-}" = "4" ] && restore "[4/6] forced red (rehearsal)"
lsvc_up || restore "$LSVC did not come back after the restart"
a1="$(ack)"; [ "$a1" = "ERROR_NO_CMD" ] || restore "[4/6] the listener does not answer (ack '$a1')"
WANT="$MODE"; [ "$MODE" = none ] && WANT=open
sm="$(grep -o '"mode": "[a-z]*"' "$DSTATE" 2>/dev/null | cut -d'"' -f4)"
[ "$sm" = "$WANT" ] || restore "[4/6] the door's state says '$sm', not '$WANT'"
say "   [4/6] placed and read back: listener $(m8 "$A"), summary $(m8 "$B"), clock $(m8 "$C"), presence $(m8 "$D"), legs $(m8 "$E")$([ "$MODE" != none ] && echo ", door file 0600"); $LSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), answers, door: $sm"
d2="$(clockdry "$PD")"
echo "$d2" | grep -q "^DRY " && ! echo "$d2" | grep -q "Traceback" || { echo "$d2"; restore "[5/6] the installed clock's --dry did not run"; }
p2="$(pres "$PD")"; echo "$p2" | grep -q "^PRESENCE .* ok True" || { echo "$p2"; restore "[5/6] the installed presence.py did not read today"; }
nl="$(pya -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["legs"]))' "$E" | tail -1)"; [ "$nl" = 46 ] || restore "[5/6] the legs file reads $nl legs, not 46"
if [ -n "${JOURNAL_CMD:-}" ]; then jr="$($JOURNAL_CMD)"; else jr="$("$JOURNAL" -u "$LSVC" --since "$T0" --no-pager 2>&1)"; fi
echo "$jr" | grep -q "Traceback" && restore "[5/6] the listener's journal holds a Traceback"
[ "${FORCE_RED_AT:-}" = "5" ] && restore "[5/6] forced red (rehearsal)"
say "   [5/6] the clock --dry runs with presence.py; presence reads today; 46 legs; the listener's journal clean"
FINISHED=1; release
case "$MODE" in
  enforce) W="THE DOOR IS SHUT: only the attendance machine's own punches are stored; any other is kept aside in $ROOT/punches_refused.csv, the health line 'punch door' turns red and the hourly health shout names it.";;
  watch)   W="THE DOOR IS WATCHING (not shut yet): every punch is stored; one without the mark is counted. Claude reads the evidence next session.";;
  *)       W="THE DOOR IS OPEN as before (the evidence named no mark). Presence and the clock are in.";;
esac
say "   [6/6] $W"
say "$KIT: INSTALLED. Undo: bash $KDIR/install_S957_PUNCH_DOOR.sh --undo"
