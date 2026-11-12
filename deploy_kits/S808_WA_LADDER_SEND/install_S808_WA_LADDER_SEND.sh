#!/bin/bash
# =============================================================================
#  install_S808_WA_LADDER_SEND.sh . kit S808 (13-Nov-2026, session S442, the parent) . D940, D946, D947.
#  THE SENDING from /portal/messages (plan: S440_WA_SENDING_PLAN.md). After this kit the WhatsApp messages page has a switch
#  for each of the five automatic messages, a test to the doctor's own phone for each, the ticked "long overdue" names, and a
#  record of everything that went. EVERY SWITCH IS OFF AT INSTALL -- this installer sends nothing to anyone, not even a test.
#  TWO files: /root/portal/wa_ladder.py (cb197293 -> the kit's: the page and its doors) and the NEW /root/portal/wa_ladder_send.py
#  (the sending). ONE cron line (every 5 minutes; it does nothing while every switch is OFF). The doctor's own mobile number,
#  for the tests, is given at the END of the line and kept in the store only -- never in the repository (F-185); while the
#  installer runs it is on its own command line, and it stays in root's shell history on the server:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s808kit && cp -rp /root/deploy/repo/deploy_kits/S808_WA_LADDER_SEND /tmp/s808kit && bash /tmp/s808kit/install_S808_WA_LADDER_SEND.sh <your own 10-digit mobile>
#  DRY=1 runs every gate and writes nothing.   Undo: ... --undo   (every switch is set OFF first; the store keeps its record)
# =============================================================================
set -u
KIT="S808_WA_LADDER_SEND"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
F1="$ROOT/portal/wa_ladder.py"; FROM1=cb19729379836550183bad91736559d5; TO1=5189a155cded969d0aa8fa75c29e0d47; BAK1="$F1.bak_S808_${FROM1:0:8}"
N1="$ROOT/portal/wa_ladder_send.py"; TON1=d8f16f00aecac80c9dd16971383d8163
PWA="$ROOT/portal/portal_wa.py"
WALK_WANT="WALK OK 68/68"
CTAG='# S808_WA_LADDER_SEND'
CRONLINE="1-59/5 * * * * [ -e $ROOT/finance/_off/ALL_OFF ] || $VPY -B $N1 --tick >> $ROOT/portal/wa_ladder_send.log 2>&1 $CTAG"
RUNLOCK="${WA_LADDER_SEND_LOCK:-$ROOT/portal/wa_ladder_send.lock}"   # the timed run's own lock (taken inside wa_ladder_send.py)
U_PAGE="http://127.0.0.1:$PPORT/portal/messages"
# the module's places, all under ROOT (on the server these are its own defaults)
export FINANCE_DB="${FINANCE_DB:-$ROOT/finance/finance.db}" WA_LADDER_DB="${WA_LADDER_DB:-$ROOT/portal/wa_ladder.db}"
export WA_LADDER_INBOX_DB="${WA_LADDER_INBOX_DB:-$ROOT/wa/wa_inbox/inbox.db}" WA_LADDER_OLD_OPTOUT="${WA_LADDER_OLD_OPTOUT:-$ROOT/wa/wa_opt_outs.csv}"
export WA_LADDER_CONSOLE_DB="${WA_LADDER_CONSOLE_DB:-$ROOT/wa/console.db}" WA_LADDER_ALL_OFF="${WA_LADDER_ALL_OFF:-$ROOT/finance/_off/ALL_OFF}"
export WA_LADDER_PORTAL_CONFIG="${WA_LADDER_PORTAL_CONFIG:-$ROOT/portal/portal_config.py}" PORTAL_WA_DIR="${PORTAL_WA_DIR:-$ROOT/wa/wa_portal}"
export WA_LADDER_INGEST=0
STOREDB="$WA_LADDER_DB"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""; PB=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
pcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H 'X-Messages: 1' -d '{"list":"tomorrow","on":false}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${WAITS:-3}"; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
closed() { case "$1" in 302|303|401|403) return 0;; *) return 1;; esac; }
# a lock or a pause switch left by a run of THIS kit is cleared only when that run is no longer alive; returns 1 while it is
stale_mine() { local pid=""
  if [ -f "$LOCK/owner" ] && grep -q "^$KIT " "$LOCK/owner" 2>/dev/null; then
    pid=$(awk '{print $2}' "$LOCK/owner" 2>/dev/null)
    if [ -n "$pid" ] && [ "$pid" != "$$" ] && kill -0 "$pid" 2>/dev/null; then return 1; fi
    rm -rf "$LOCK"; echo "   (a lock left by an earlier, interrupted run of this kit was cleared)"
  fi
  if [ ! -e "$LOCK" ] && [ -f "$OFFSW" ] && grep -q "^$KIT " "$OFFSW" 2>/dev/null; then rm -f "$OFFSW"; echo "   (the pause switch left by an earlier, interrupted run of this kit was cleared)"; fi
  return 0; }
# the settings as the timed run will see them: cron's bare environment, the settings file only
cronlike() { ( unset MYOP_AUTH_TOKEN PORTAL_WA_DRYRUN PORTAL_WA_USERS; runmod "$@" ); }
modeof() { printf '%s' "$1" | sed -n 's/^ok mode \([A-Z]*\) .*/\1/p'; }
# wait until no timed run is going (its own lock is free), at most 3 minutes
runfree() { command -v flock >/dev/null 2>&1 || return 0; [ -e "$RUNLOCK" ] || return 0; flock -w 180 "$RUNLOCK" true 2>/dev/null; }
# the gates after a restart of the portal; prints the first thing that is wrong, or nothing
aftergates() { local c t0="$1" jl jr
  c=$(wait200 phz); [ "$c" = 200 ] || { echo "portal health $c"; return; }
  c=$(hcode "$U_PAGE"); closed "$c" || { echo "the page's door answers $c without a login"; return; }
  c=$(pcode "$U_PAGE/api/send/switch"); closed "$c" || { echo "the send door answers $c without a login -- it must be closed"; return; }
  sleep "${WAITS:-2}"
  jl="$("$JOURNALCTL" -u "$PSVC" --since "$t0" --no-pager 2>/dev/null)" || { echo "the portal's journal could not be read after the restart"; return; }
  jr="$(printf '%s\n' "$jl" | grep -v -i 'reentrant call' | grep -c -i -E 'NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
  [ "${jr:-0}" = 0 ] || echo "journal: $jr error line(s) since the restart"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
# The crontab is touched only from a GOOD read of it: a failed or empty read changes nothing, and every other line must survive.
cron_off() {
  local t; t=$(mktemp /tmp/s808cron.XXXX) || return 0
  if "$CRONTAB" -l > "$t" 2>/dev/null && grep -q "$CTAG" "$t"; then
    grep -v "$CTAG" "$t" > "$t.new"
    [ "$(grep -c . "$t.new")" -eq "$(( $(grep -c . "$t") - $(grep -c "$CTAG" "$t") ))" ] && "$CRONTAB" - < "$t.new"
  fi
  rm -f "$t" "$t.new"; return 0
}
cron_add() {
  local t rc; t=$(mktemp /tmp/s808cron.XXXX) || return 1
  "$CRONTAB" -l > "$t" 2>/dev/null || { rm -f "$t"; return 1; }
  [ -s "$t" ] || { rm -f "$t"; return 1; }
  grep -v "$CTAG" "$t" > "$t.new"; echo "$CRONLINE" >> "$t.new"
  [ "$(grep -c . "$t.new")" -eq "$(( $(grep -c . "$t") - $(grep -c "$CTAG" "$t") + 1 ))" ] || { rm -f "$t" "$t.new"; return 1; }
  "$CRONTAB" - < "$t.new"; rc=$?; rm -f "$t" "$t.new"; return $rc
}
putback() {
  cron_off; runfree
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"
  [ -f "$N1" ] && mv -f "$N1" "$N1.undone_S808"; rm -f "$F1.s808new" "$N1.s808new"
  find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && [ ! -e "$N1" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting everything back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   wa_ladder.py is back byte-identically; wa_ladder_send.py is set aside; the cron line is out" || echo "   !! NOT back -- copy $BAK1 over $F1 and remove $N1 by hand"
  echo "   portal health $(wait200 phz). Nothing was sent to anyone. Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP
# run the sending file of a given folder, read-only uses; $1 = the folder, the rest = its arguments
runmod() { local d="$1"; shift; ( cd /tmp && PYTHONPATH="$ROOT/portal" timeout 60 "$VPY" -W ignore -B "$d/wa_ladder_send.py" "$@" 2>&1 | tail -1 ); }
numok() { ( cd /tmp && timeout 20 "$VPY" -W ignore -B -c 'import sys; sys.path.insert(0, sys.argv[1]); import wa_ladder as L; print("ok" if L.m10(sys.argv[2]) else "bad")' "$KDIR/portal" "$1" 2>/dev/null | tail -1 ); }
have_num() { ( cd /tmp && timeout 20 "$VPY" -W ignore -B -c '
import sqlite3, sys
try:
    c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
    r = c.execute("SELECT v FROM meta WHERE k=?", ("send_test_mobile",)).fetchone()
    print("yes" if r and r[0] else "no")
except Exception:
    print("no")
' "$STOREDB" 2>/dev/null | tail -1 ); }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/wa_ladder.py)" = "$TO1" ] && [ "$(m5 portal/wa_ladder_send.py)" = "$TON1" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ] || stop "no good backup -- nothing to undo"
  L1=$(m5 "$F1"); [ "$L1" = "$TO1" ] || [ "$L1" = "$FROM1" ] || stop "wa_ladder.py has been changed since this kit (a later kit is on top) -- not undone"
  if [ -e "$N1" ] && [ "$(m5 "$N1")" != "$TON1" ]; then stop "wa_ladder_send.py has been changed since this kit (a later kit is on top) -- not undone"; fi
  stale_mine || stop "an install of this kit is still running -- not undone"
  if [ -e "$N1" ]; then SA=$(runmod "$ROOT/portal" --stop-all); case "$SA" in "ok "*) echo "   every switch set OFF first: ${SA#ok }";; *) stop "the switches could not be set OFF ($SA) -- not undone";; esac; fi
  ok=$(putback); "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && { echo "UNDONE: the WhatsApp messages page is show-only again, as before S808; the timed run's cron line is out; portal $(wait200 phz). The record of what went stays in the store."; exit 0; }
  echo "!! not back -- send a photo"; exit 1
fi
NUM="${1:-}"
echo "[1/6] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
if [ -n "$NUM" ] && [ "$(numok "$NUM")" != ok ]; then stop "what stands at the end of the line is not a plain 10-digit mobile number. Paste the line again and type your own mobile after it"; fi
L1=$(m5 "$F1")
if [ "$L1" = "$TO1" ] && [ "$(m5 "$N1")" = "$TON1" ]; then
  echo "-- ALREADY INSTALLED. No file written. portal $(phz)"
  stale_mine || { echo "   an install of this kit is still running -- wait for it to finish. Nothing done."; exit 0; }
  S1=$(runmod "$ROOT/portal" --selftest); CN1=$(runmod "$ROOT/portal" --contract)
  { [ "$S1" = "selftest OK" ] && case "$CN1" in "ok "*) true;; *) false;; esac; } || { echo "!! the placed files do not pass their own checks ($S1 | $CN1). Send a photo of this screen to Claude."; exit 1; }
  if [ -n "$NUM" ] && [ "${DRY:-0}" != 1 ]; then echo "   $(runmod "$ROOT/portal" --set-test-mobile "$NUM")"; fi
  if "$CRONTAB" -l 2>/dev/null | grep -q "$CTAG"; then echo "   the timed run's cron line is in place"
  elif [ "${DRY:-0}" != 1 ]; then                        # an earlier run was cut short after placing: finish it -- restart, the gates, the cron line
    T0=$(date '+%Y-%m-%d %H:%M:%S'); "$SYSTEMCTL" restart "$PSVC" || true
    AG=$(aftergates "$T0")
    if [ -n "$AG" ]; then PLACED=1; restore "an earlier run was cut short, and after a restart: $AG"; fi
    if cron_add && "$CRONTAB" -l 2>/dev/null | grep -q "$CTAG"; then echo "   an earlier run was cut short after placing: the portal was restarted and checked, and the timed run's cron line added now"
    else echo "!! the timed run's cron line could NOT be added. Send a photo of this screen to Claude."; exit 1; fi
  else echo "!! the timed run's cron line is NOT in the crontab (DRY: nothing done)."; fi
  echo "   now: $(cronlike "$ROOT/portal" --status)"; exit 0
fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ -e "$N1" ] && stop "a file is already at $N1 and it is not this kit's"
[ -f "$PWA" ] || stop "the portal's sender is not at $PWA"
[ -f "$FINANCE_DB" ] || stop "finance.db is not at $FINANCE_DB"
[ -f "$STOREDB" ] || stop "the stop list's store is not at $STOREDB (the listener of S798 makes it)"
if [ -z "$NUM" ] && [ "$(have_num)" != yes ]; then stop "your own mobile number is not at the end of the line. Paste the line again, type your own 10-digit mobile after it, then Enter"; fi
CT0=$(mktemp /tmp/s808cron.XXXX); "$CRONTAB" -l > "$CT0" 2>/dev/null && [ -s "$CT0" ] || { rm -f "$CT0"; stop "root's crontab could not be read (or is empty) -- the timed run's line cannot be added safely"; }
rm -f "$CT0"
SCR=$(mktemp -d /tmp/s808.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$SCR" ] && [ -d "$SCR" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal" "$SCR/try"
"$APY" -B "$KDIR/make_s808.py" "$F1" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/wa_ladder.py")" = "$TO1" ] || stop "make_s808.py on the live bytes does not give the kit's wa_ladder.py"
for f in portal/wa_ladder.py portal/wa_ladder_send.py; do
  "$APY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null && "$VPY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile"
done
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/6] the live wa_ladder.py is ${FROM1:0:8}; the kit's is that + the S808 edits (remade on the box); both files compile"
\cp -p "$F1" "$SCR/live/portal/wa_ladder.py"
R=$(cd "$SCR" && TMPDIR="$SCR" S808_PORTAL_WA="$ROOT/portal" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s808.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_WANT" ] || { (cd "$SCR" && TMPDIR="$SCR" S808_PORTAL_WA="$ROOT/portal" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s808.py" "$KDIR" 2>&1 | grep '^BAD' | head -6); stop "the S808 walk is not green ($R; wanted $WALK_WANT)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" S808_PORTAL_WA="$ROOT/portal" timeout 600 "$VPY" -W ignore -B "$KDIR/walk_s808.py" "$SCR/live" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live file did not go red ($R2)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/6] the walk (made-up patients and numbers only; the sender is a recorder; the live portal_wa.py read for the contract): $R | the live files, which cannot send: $R2"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
PB=$(hcode "$U_PAGE"); closed "$PB" || stop "the page's door answers $PB without a login before the install -- not as expected"
# the kit's files against the server's real settings, sender and send log -- on a COPY of the store, so nothing live is written
\cp -p "$KDIR/portal/wa_ladder.py" "$KDIR/portal/wa_ladder_send.py" "$SCR/try/" && \cp -p "$STOREDB" "$SCR/try/wa_ladder.db" || stop "the scratch copy could not be made"
CN=$(WA_LADDER_DB="$SCR/try/wa_ladder.db" runmod "$SCR/try" --contract)
case "$CN" in "ok "*) ;; *) stop "the portal's sender does not take this kit's calls ($CN)";; esac
ST0=$(WA_LADDER_DB="$SCR/try/wa_ladder.db" runmod "$SCR/try" --status)
case "$ST0" in "ok mode "*) ;; *) stop "the kit's file could not read the server's settings and stores ($ST0)";; esac
case "$ST0" in "ok mode ERR"*) stop "the portal's settings (its WhatsApp key or its settings file) cannot be read as this kit reads them ($ST0)";; esac
case "$ST0" in *"send log readable"*) ;; *) stop "the portal's send log cannot be read as this kit reads it ($ST0)";; esac
case "$ST0" in *"switches ON 0 of 5"*) ;; *) stop "a switch is ON before the install ($ST0) -- not as expected";; esac
ST0C=$(WA_LADDER_DB="$SCR/try/wa_ladder.db" cronlike "$SCR/try" --status)
[ -n "$(modeof "$ST0C")" ] && [ "$(modeof "$ST0C")" != ERR ] || stop "the timed run would not be able to read the portal's settings from the settings file ($ST0C) -- they may sit in the service's environment. Tell Claude"
[ "$(modeof "$ST0C")" = "$(modeof "$ST0")" ] || stop "the timed run would see mode $(modeof "$ST0C") while this shell sees $(modeof "$ST0") -- a setting sits outside the settings file. Tell Claude"
# the page runs inside the portal's service: none of the settings this kit reads may sit in the service's environment (names only are looked at)
SPID=$("$SYSTEMCTL" show -p MainPID --value "$PSVC" 2>/dev/null | tr -d '[:space:]')
{ [ -n "$SPID" ] && [ "$SPID" != 0 ] && [ -r "/proc/$SPID/environ" ]; } || stop "the portal service's own environment could not be looked at (no process found for $PSVC) -- so it cannot be said that the page and the timed run read the same settings. Tell Claude"
SN=$(tr '\0' '\n' < "/proc/$SPID/environ" 2>/dev/null | grep -c -E '^(MYOP_AUTH_TOKEN|PORTAL_WA_DRYRUN|PORTAL_WA_USERS|PORTAL_WA_DIR|FINANCE_DB|WA_LADDER_[A-Z_]*)=')
[ "${SN:-0}" = 0 ] || stop "the portal's service carries $SN of this kit's settings in its environment -- the page and the timed run could disagree. Tell Claude"
SVCENV="none of this kit's settings sit in it"
# the STOP listener as it stands now: it must be hearing, and its own reader of the Inbox must have run
SS0=$(cd "$ROOT/portal" && timeout 30 "$VPY" -W ignore -B "$F1" --stop-status 2>&1 | tail -1)
case "$SS0" in "ok "*" note:"*) stop "the STOP listener says the Inbox's own reader did not run ($SS0) -- with that, no list would ever go. Tell Claude";; "ok "*) ;; *) stop "the STOP listener is not hearing the Inbox ($SS0)";; esac
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[4/6] before: portal healthy | the page's door closed without a login ($PB) | $CN"
echo "      with the kit's files, on a copy of the store: $ST0"
echo "      the timed run's bare environment sees the same mode ($(modeof "$ST0C")) | the portal service's environment: $SVCENV"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
stale_mine || stop "an install of this kit is still running. Wait for it to finish"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
# another run may have placed the files between this run's first look and its lock: look again, now that the lock is held
{ [ "$(m5 "$F1")" = "$FROM1" ] && [ ! -e "$N1" ]; } || stop "the live files changed while this run was checking (another run of this kit has placed them?). Run the line once more -- it will say ALREADY INSTALLED"
if [ -f "$BAK1" ] && [ "$(m5 "$BAK1")" = "$FROM1" ]; then :; else { \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"; fi
"$CRONTAB" -l > "$ROOT/portal/crontab.bak_S808" 2>/dev/null && [ -s "$ROOT/portal/crontab.bak_S808" ] || stop "could not keep a copy of root's crontab"
PLACED=1
for pair in "portal/wa_ladder_send.py:$N1:$TON1" "portal/wa_ladder.py:$F1:$TO1"; do
  IFS=: read -r src dst to <<< "$pair"
  { \cp "$KDIR/$src" "$dst.s808new" && [ "$(m5 "$dst.s808new")" = "$to" ] && chmod --reference="$BAK1" "$dst.s808new"; } || restore "$src could not be copied beside its place"
  chown --reference="$BAK1" "$dst.s808new" 2>/dev/null
  mv -f "$dst.s808new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
AG=$(aftergates "$T0"); [ -z "$AG" ] || restore "$AG"
S1=$(runmod "$ROOT/portal" --selftest); [ "$S1" = "selftest OK" ] || restore "the placed file's self-test ($S1)"
CN1=$(runmod "$ROOT/portal" --contract); case "$CN1" in "ok "*) ;; *) restore "the placed file and the portal's sender ($CN1)";; esac
SS=$(cd "$ROOT/portal" && timeout 30 "$VPY" -W ignore -B "$F1" --stop-status 2>&1 | tail -1)
case "$SS" in "ok "*" note:"*) restore "the STOP listener says the Inbox's own reader did not run after the change ($SS)";; "ok "*) ;; *) restore "the STOP listener is not hearing the Inbox after the change ($SS)";; esac
NM="the doctor's own number was already in the store"
if [ -n "$NUM" ]; then NM=$(runmod "$ROOT/portal" --set-test-mobile "$NUM"); case "$NM" in "ok "*) ;; *) restore "the doctor's number could not be kept ($NM)";; esac; fi
ST1=$(cronlike "$ROOT/portal" --status)
case "$ST1" in "ok mode "*"switches ON 0 of 5"*"number set"*"send log readable"*) ;; *) restore "after placing, not as expected: $ST1";; esac
cron_add || restore "the cron line could not be added"
"$CRONTAB" -l 2>/dev/null | grep -q "$CTAG" || restore "the cron line is not in the crontab"
TK=$( cd /tmp && PYTHONPATH="$ROOT/portal" timeout 120 "$VPY" -W ignore -B "$N1" --tick 2>&1 | head -3 )
[ -z "$TK" ] || restore "the timed run said something with every switch OFF: $TK"
find "$ROOT/portal" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
echo "[5/6] placed (backup $BAK1); the portal restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): healthy; the page's door and the send door closed without a login; journal clean; the STOP listener: $SS"
echo "      ${NM#ok } | the timed run is on every 5 minutes (at :01, :06 ...) and did nothing (every switch is OFF)"
echo "      now: $ST1"
echo "[6/6] $KIT: DONE. EVERY SWITCH IS OFF. Nothing was sent to anyone, not even a test. Your portal -> Patients -> WhatsApp messages: send a test of a message to your phone, press 'It arrived', then its switch can be turned on."
