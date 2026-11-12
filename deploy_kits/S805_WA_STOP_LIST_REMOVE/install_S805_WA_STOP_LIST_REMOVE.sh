#!/bin/bash
# =============================================================================
#  install_S805_WA_STOP_LIST_REMOVE.sh . kit S805 (12-Nov-2026, session S439, the parent) . D939, the WhatsApp items (c).
#  On the owner's page /portal/messages each number on the stop list gets "Take off the stop list" (the doctor's login only, two
#  taps), and a number he took off gets "Put back on the stop list". A removal is RECORDED in the kit's own store (table
#  optout_removed) and never erased; the listener does not put the number back for a STOP it had already read; a NEW STOP
#  reply puts it back. Still SHOW ONLY: no send code.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s805kit && cp -rp /root/deploy/repo/deploy_kits/S805_WA_STOP_LIST_REMOVE /tmp/s805kit && bash /tmp/s805kit/install_S805_WA_STOP_LIST_REMOVE.sh
#  /root/portal/wa_ladder.py ca0334b4 -> cb197293. DRY=1 runs every gate and writes nothing.   Undo: ... --undo
# =============================================================================
set -u
KIT="S805_WA_STOP_LIST_REMOVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/wa_ladder.py"; FROM1=ca0334b4eca5a2e0e382767c79281ac7; TO1=cb19729379836550183bad91736559d5; BAK1="$F1.bak_S805_${FROM1:0:8}"
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"; STOREDB="${WA_LADDER_DB:-$ROOT/portal/wa_ladder.db}"
WALK_WANT="WALK OK 40/40"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""; PB=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; rm -f "$F1.s805new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the file back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   wa_ladder.py is back byte-identically (the store's new empty table is harmless to the old file)" || echo "   !! NOT back -- copy $BAK1 over $F1 by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
counts() { ( cd /tmp && FINANCE_DB="$DB" WA_LADDER_DB="$2" WA_LADDER_INGEST=0 timeout 60 "$VPY" -B "$1" --counts 2>&1 | tail -1 ); }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/wa_ladder.py)" = "$TO1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup -- nothing to undo"
  L1=$(m5 "$F1"); [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ] || stop "wa_ladder.py has been changed since this kit (a later kit is on top) -- not undone"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: wa_ladder.py is back as S801 left it; portal $(wait200 phz). Numbers already taken off the stop list stay recorded in the store, and the old file puts those of the older file back on the list."; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; echo "   now: $(counts "$F1" "$STOREDB")"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s805.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$SCR" ] && [ -d "$SCR" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal"
"$APY" -B "$KDIR/make_s805.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/wa_ladder.py")" = "$TO1" ] || stop "make_s805.py on the live bytes does not give the kit's file"
"$APY" -W ignore -B -m py_compile "$KDIR/portal/wa_ladder.py" 2>/dev/null && "$VPY" -W ignore -B -m py_compile "$KDIR/portal/wa_ladder.py" 2>/dev/null || stop "wa_ladder.py does not compile"
( cd "$SCR" && WA_LADDER_DB="$SCR/selftest.db" "$VPY" -B "$KDIR/portal/wa_ladder.py" --selftest >/dev/null 2>&1 ) || stop "the STOP rule's selftest is not green"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/5] the live wa_ladder.py is ${FROM1:0:8}; the kit's is that + the S805 edits (remade on the box); it compiles; the selftest green"
\cp -p "$F1" "$SCR/live/portal/wa_ladder.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s805.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_WANT" ] || { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s805.py" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S805 walk is not green ($R; wanted $WALK_WANT)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s805.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (made-up patients and numbers only): $R | the live file: $R2"
CB=$(counts "$F1" "$STOREDB")
case "$CB" in *"stop list"*) ;; *) stop "today's counts could not be read from the live records with the live file ($CB)";; esac
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
SS0=$(cd /tmp && FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 30 "$VPY" -B "$F1" --stop-status 2>&1 | tail -1)
case "$SS0" in "ok "*) ;; *) stop "the STOP listener is not well BEFORE the install ($SS0) -- that is repaired first";; esac
PB=$(hcode "http://127.0.0.1:$PPORT/portal/messages")
case "$PB" in 302|303|401|403) ;; *) stop "the page's door answers $PB without a login before the install -- not as expected";; esac
echo "[4/5] before: $CB | portal healthy | the listener: $SS0 | the page's door answers $PB without a login"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$KDIR/portal/wa_ladder.py" "$F1.s805new" && chmod --reference="$BAK1" "$F1.s805new" && chown --reference="$BAK1" "$F1.s805new" 2>/dev/null; mv -f "$F1.s805new" "$F1" || restore "wa_ladder.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "the read-back did not match"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "http://127.0.0.1:$PPORT/portal/messages"); [ "$c3" = "$PB" ] || restore "the page's door answers $c3 without a login (before: $PB)"
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'X-Messages: 1' -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$PPORT/portal/messages/api/unstop")
case "$c4" in 302|303|401|403) ;; *) restore "the new door (take off) answers $c4 without a login -- it must be closed";; esac
c5=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'X-Messages: 1' -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$PPORT/portal/messages/api/restop")
case "$c5" in 302|303|401|403) ;; *) restore "the new door (put back) answers $c5 without a login -- it must be closed";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'wa_ladder|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'wa_ladder|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
SS=$(cd "$ROOT/portal" && FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 120 "$VPY" -B "$F1" --stop-scan >/dev/null 2>&1; FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 30 "$VPY" -B "$F1" --stop-status 2>&1 | tail -1)
case "$SS" in "ok "*) ;; *) restore "the STOP listener is not hearing the Inbox with the new file ($SS)";; esac
CA=$(counts "$F1" "$STOREDB")
[ "$CA" = "$CB" ] || { case "$CA" in *"stop list"*) echo "      note: today's counts read differently a minute later (before: $CB)";; *) restore "today's counts cannot be read with the new file ($CA)";; esac; }
PLACED=0
echo "[5/5] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; the page's door $c3 and the two new doors $c4 $c5 closed without a login; journal clean; the listener: $SS"
echo "      now: $CA"
echo "      $KIT: DONE. Your WhatsApp messages page can take a number off the stop list and put it back. Still nothing is sent to anyone."
