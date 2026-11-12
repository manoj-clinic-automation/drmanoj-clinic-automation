#!/bin/bash
# =============================================================================
#  install_S798_WA_MESSAGES_SHOWONLY.sh . kit S798 (12-Nov-2026, session S437, the parent) . the owner (D934; his "ok" 10:12 IST):
#  the approved WhatsApp messages, SHOW ONLY first -- a page on his portal that lists who would get which message today, with the
#  rules applied, and a listener that puts a number on the stop list when it replies STOP. NOTHING IS SENT: no send code in the kit.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s798kit && cp -rp /root/deploy/repo/deploy_kits/S798_WA_MESSAGES_SHOWONLY /tmp/s798kit && bash /tmp/s798kit/install_S798_WA_MESSAGES_SHOWONLY.sh
#  NEW /root/portal/wa_ladder.py (/portal/messages; its own store /root/portal/wa_ladder.db; + cron every 5 min: the STOP listener)
#  /root/portal/portal.py 8b723919 -> TO (a tile for the doctors in Patients + the page mounted)
#  DRY=1 runs every gate and prints today's counts from the live records (counts only); writes nothing.
#  Undo:  bash /tmp/s798kit/install_S798_WA_MESSAGES_SHOWONLY.sh --undo
# =============================================================================
set -u
KIT="S798_WA_MESSAGES_SHOWONLY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
F1="$ROOT/portal/portal.py"; FROM1=8b7239192db3f77493b829a618fb33e9; TO1=3a0f7cd17803d8b74af7b67eb4d68964; BAK1="$F1.bak_S798_${FROM1:0:8}"
N1="$ROOT/portal/wa_ladder.py"; TON1=8b6bd64198a8f57e5d51f283fc372628
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"
STOREDB="${WA_LADDER_DB:-$ROOT/portal/wa_ladder.db}"
CRONLINE="*/5 * * * * flock -n /tmp/wa_ladder_stop.lock $VPY -B $N1 --stop-scan >> $ROOT/portal/wa_ladder.log 2>&1 # S798_WA_STOP_LISTENER"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
CTAG='# S798_WA_STOP_LISTENER'
# The crontab is touched only from a GOOD read of it: a failed or empty read changes nothing, and every other line must survive.
cron_off() {
  local t; t=$(mktemp /tmp/s798cron.XXXX) || return 0
  if "$CRONTAB" -l > "$t" 2>/dev/null && grep -q "$CTAG" "$t"; then
    grep -v "$CTAG" "$t" > "$t.new"
    [ "$(grep -c . "$t.new")" -eq "$(( $(grep -c . "$t") - $(grep -c "$CTAG" "$t") ))" ] && "$CRONTAB" - < "$t.new"
  fi
  rm -f "$t" "$t.new"; return 0
}
cron_add() {
  local t rc; t=$(mktemp /tmp/s798cron.XXXX) || return 1
  "$CRONTAB" -l > "$t" 2>/dev/null || { rm -f "$t"; return 1; }
  [ -s "$t" ] || { rm -f "$t"; return 1; }
  grep -v "$CTAG" "$t" > "$t.new"; echo "$CRONLINE" >> "$t.new"
  [ "$(grep -c . "$t.new")" -eq "$(( $(grep -c . "$t") - $(grep -c "$CTAG" "$t") + 1 ))" ] || { rm -f "$t" "$t.new"; return 1; }
  "$CRONTAB" - < "$t.new"; rc=$?; rm -f "$t" "$t.new"; return $rc
}
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"
  [ -f "$N1" ] && mv -f "$N1" "$N1.undone_S798"; cron_off; rm -f "$F1.s798new" "$N1.s798new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && [ ! -e "$N1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting everything back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal.py is back byte-identically; the new file and the cron line are off" \
                || echo "   !! NOT all back -- copy $BAK1 back over $F1 by hand"
  echo "   portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/portal.py)" = "$TO1" ] && [ "$(m5 portal/wa_ladder.py)" = "$TON1" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup of portal.py ($BAK1) -- nothing to undo"
  LU=$(m5 "$F1")
  [ "$LU" = "$TO1" ] || [ "$LU" = "$FROM1" ] || stop "portal.py has been changed since this kit (live ${LU:0:8}) -- a later kit is on top; not undone"
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: portal.py is back, the page and the STOP listener are off (the stop list $STOREDB is kept); portal $(wait200 phz)"; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ] && [ "$(m5 "$N1")" = "$TON1" ]; then
  if "$CRONTAB" -l 2>/dev/null | grep -q "$CTAG"; then echo "-- ALREADY INSTALLED. Nothing written. portal $(phz)"; exit 0; fi
  [ "${DRY:-0}" = 1 ] && { echo "DRY=1: the two files are in place but the listener's cron line is missing; a real run adds it."; exit 0; }
  cron_add && "$CRONTAB" -l 2>/dev/null | grep -q "$CTAG" || stop "the two files are in place but the cron line could not be added" "The page works; the STOP listener is not running."
  echo "-- The two files were already in place; the STOP listener's cron line was missing and is now added. portal $(phz)"; exit 0
fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ -e "$N1" ] && stop "a file of this kit is already there ($N1) -- not this kit's bytes"
[ -f "$DB" ] || stop "finance.db is not at $DB"
CT0=$(mktemp /tmp/s798cron.XXXX); "$CRONTAB" -l > "$CT0" 2>/dev/null && [ -s "$CT0" ] || { rm -f "$CT0"; stop "root's crontab could not be read (or is empty) -- the listener's line cannot be added safely"; }
rm -f "$CT0"
SCR=$(mktemp -d /tmp/s798.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal"
"$APY" -B "$KDIR/make_s798.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal.py")" = "$TO1" ] \
  || stop "make_s798.py on the live bytes does not give the kit's portal.py"
for f in portal/portal.py portal/wa_ladder.py; do
  "$APY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $APY"
  "$VPY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $VPY"
done
"$VPY" -B "$KDIR/portal/wa_ladder.py" --selftest >/dev/null 2>&1 || stop "the STOP rule's selftest is not green"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live portal.py is ${FROM1:0:8}; the kit's is that + the S798 edits (remade on the box); both files compile; the STOP rule's selftest green"
\cp -p "$F1" "$SCR/live/portal/portal.py"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s798.py" "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s798.py" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S798 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s798.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] the walk (made-up patients only): $R | the live files: $R2"
C=$(cd "$SCR" && FINANCE_DB="$DB" WA_LADDER_DB="$SCR/none.db" WA_LADDER_INGEST=0 timeout 60 "$VPY" -B "$KDIR/portal/wa_ladder.py" --counts 2>&1 | tail -1)
case "$C" in 20??-??-??:*) ;; *) stop "today's lists could not be read from the live records ($C)";; esac
IC=$(cd "$SCR" && WA_LADDER_DB="$SCR/none.db" timeout 60 "$VPY" -B "$KDIR/portal/wa_ladder.py" --inbox-check 2>&1 | tail -1)
case "$IC" in "ok "*) ;; *) stop "the WhatsApp Inbox's store cannot be read the way the STOP listener needs ($IC)";; esac
echo "[4/6] today from the live records, read-only (counts only): $C"
echo "      the Inbox store: $IC"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
"$CRONTAB" -l > "$ROOT/portal/crontab.bak_S798" 2>/dev/null && [ -s "$ROOT/portal/crontab.bak_S798" ] || stop "could not keep a copy of root's crontab"
PLACED=1
for pair in "portal/portal.py:$F1:$TO1" "portal/wa_ladder.py:$N1:$TON1"; do
  IFS=: read -r src dst to <<< "$pair"
  \cp "$KDIR/$src" "$dst.s798new" && chmod --reference="$BAK1" "$dst.s798new" && chown --reference="$BAK1" "$dst.s798new" 2>/dev/null; mv -f "$dst.s798new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "http://127.0.0.1:$PPORT/portal/messages"); case "$c3" in 302|303|401|403) ;; *) restore "the page answered $c3 without a login (not mounted?)";; esac
c4=$(hcode "http://127.0.0.1:$PPORT/portal/booking"); case "$c4" in 302|303|401|403) ;; *) restore "the booking page answered $c4 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'wa_ladder|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'wa_ladder|mounted|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restart"; }
( cd "$ROOT/portal" && FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 120 "$VPY" -B "$N1" --stop-scan ) >> "$ROOT/portal/wa_ladder.log" 2>&1 || restore "the first pass of the STOP listener failed (see $ROOT/portal/wa_ladder.log)"
[ -f "$STOREDB" ] || restore "the STOP listener did not make its store $STOREDB"
SS=$(cd "$ROOT/portal" && FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" timeout 30 "$VPY" -B "$N1" --stop-status 2>&1 | tail -1)
case "$SS" in "ok "*) ;; *) restore "the STOP listener is not hearing the Inbox ($SS)";; esac
cron_add || restore "the cron line could not be added"
"$CRONTAB" -l 2>/dev/null | grep -q "$CTAG" || restore "the cron line is not in the crontab"
PLACED=0
C2=$(cd "$ROOT/portal" && FINANCE_DB="$DB" WA_LADDER_DB="$STOREDB" WA_LADDER_INGEST=0 timeout 60 "$VPY" -B "$N1" --counts 2>&1 | tail -1)
echo "[5/6] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): health $c2; the page's door closed without a login ($c3); journal clean; the STOP listener ran once and is on every 5 minutes"
echo "      now: $C2"
echo "      the listener: $SS"
echo "[6/6] $KIT: DONE. Nothing is sent. Your portal -> Patients -> WhatsApp messages."
