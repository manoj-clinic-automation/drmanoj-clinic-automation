#!/bin/bash
# =============================================================================
#  install_S801_WA_LIST_MOBILES.sh . kit S801 (12-Nov-2026, session S437, the parent) . S798's show-only list holds every row for
#  "no mobile number": finance.db patient_ref carries no full mobile on the box. This reads the mobile from the Call Console's
#  patient mirror (/root/wa/console.db, read-only) instead. Still SHOW ONLY: no send code.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s801kit && cp -rp /root/deploy/repo/deploy_kits/S801_WA_LIST_MOBILES /tmp/s801kit && bash /tmp/s801kit/install_S801_WA_LIST_MOBILES.sh
#  /root/portal/wa_ladder.py 8b6bd641 -> TO. Placed ONLY IF today's count of rows without a mobile gets smaller on the live records.
#  DRY=1 runs every gate and prints the before / after counts; writes nothing.   Undo: ... --undo
# =============================================================================
set -u
KIT="S801_WA_LIST_MOBILES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
F1="$ROOT/portal/wa_ladder.py"; FROM1=8b6bd64198a8f57e5d51f283fc372628; TO1=ca0334b4eca5a2e0e382767c79281ac7; BAK1="$F1.bak_S801_${FROM1:0:8}"
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"; STOREDB="${WA_LADDER_DB:-$ROOT/portal/wa_ladder.db}"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; rm -f "$F1.s801new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the file back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   wa_ladder.py is back byte-identically" || echo "   !! NOT back -- copy $BAK1 over $F1 by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
counts() { ( cd /tmp && FINANCE_DB="$DB" WA_LADDER_DB="$2" WA_LADDER_INGEST=0 timeout 60 "$VPY" -B "$1" --counts 2>&1 | tail -1 ); }
nomob() { printf '%s' "$1" | sed -n 's/.*| no mobile \([0-9][0-9]*\) |.*/\1/p'; }
rowsn() { printf '%s' "$1" | grep -o '[0-9][0-9]* \(go\|held\|for his tick\)' | awk '{s+=$1} END {print s+0}'; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/wa_ladder.py)" = "$TO1" ] || stop "the kit's file is not the built one"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup -- nothing to undo"
  L1=$(m5 "$F1"); [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ] || stop "wa_ladder.py has been changed since this kit (a later kit is on top) -- not undone"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: wa_ladder.py is back as S798 left it; portal $(wait200 phz)"; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ]; then echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; echo "   now: $(counts "$F1" "$STOREDB")"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
SCR=$(mktemp -d /tmp/s801.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal"
"$APY" -B "$KDIR/make_s801.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/wa_ladder.py")" = "$TO1" ] || stop "make_s801.py on the live bytes does not give the kit's file"
"$APY" -W ignore -B -m py_compile "$KDIR/portal/wa_ladder.py" 2>/dev/null && "$VPY" -W ignore -B -m py_compile "$KDIR/portal/wa_ladder.py" 2>/dev/null || stop "wa_ladder.py does not compile"
"$VPY" -B "$KDIR/portal/wa_ladder.py" --selftest >/dev/null 2>&1 || stop "the STOP rule's selftest is not green"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/5] the live wa_ladder.py is ${FROM1:0:8}; the kit's is that + the S801 edits (remade on the box); it compiles; the selftest green"
\cp -p "$F1" "$SCR/live/portal/wa_ladder.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s801.py" "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s801.py" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S801 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s801.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/5] the walk (made-up patients only): $R | the live file: $R2"
CB=$(counts "$F1" "$SCR/none.db"); CA=$(counts "$KDIR/portal/wa_ladder.py" "$SCR/none.db")
NB=$(nomob "$CB"); NA=$(nomob "$CA"); TOT=$(rowsn "$CA")
echo "[4/5] today from the live records, read-only (counts only):"
echo "      as it is now : $CB"
echo "      with this kit: $CA"
[ -n "$NB" ] && [ -n "$NA" ] || stop "the counts could not be read from the live records"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: rows without a mobile $NB -> $NA (of $TOT rows); nothing written."; exit 0; }
if [ "$NB" -gt 0 ] && [ "$NA" -ge "$NB" ]; then
  echo "[5/5] NOT APPLIED -- rows without a mobile stay at $NA of $TOT: the Call Console's list does not give them either."
  echo "      $KIT: NOTHING CHANGED. Send a photo of this screen to Claude."
  exit 0
fi
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
PLACED=1
\cp "$KDIR/portal/wa_ladder.py" "$F1.s801new" && chmod --reference="$BAK1" "$F1.s801new" && chown --reference="$BAK1" "$F1.s801new" 2>/dev/null; mv -f "$F1.s801new" "$F1" || restore "wa_ladder.py could not be placed"
[ "$(m5 "$F1")" = "$TO1" ] || restore "the read-back did not match"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "http://127.0.0.1:$PPORT/portal/messages"); case "$c3" in 302|303|401|403) ;; *) restore "the page answered $c3 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'wa_ladder|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'wa_ladder|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
SS=$(cd "$ROOT/portal" && FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 120 "$VPY" -B "$F1" --stop-scan >/dev/null 2>&1; FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 30 "$VPY" -B "$F1" --stop-status 2>&1 | tail -1)
case "$SS" in "ok "*) ;; *) restore "the STOP listener is not hearing the Inbox with the new file ($SS)";; esac
PLACED=0
echo "[5/5] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; the page's door closed without a login ($c3); journal clean; the listener: $SS"
echo "      $KIT: DONE. Rows without a mobile today: $NB -> $NA of $TOT. Still nothing is sent."
