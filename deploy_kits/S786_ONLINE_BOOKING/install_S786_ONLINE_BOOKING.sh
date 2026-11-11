#!/bin/bash
# =============================================================================
#  install_S786_ONLINE_BOOKING.sh . kit S786 (11-Nov-2026, session S428, the parent) . the owner 07:15 / 07:59 IST: online bookings
#  paid on Docterz shown to staff -- name, clinic ID, FULL mobile, Rs 600 paid online, the booked time; outside Mon-Sat 11:00-13:30 /
#  19:00-20:30 staff call the patient.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s786kit && cp -rp /root/deploy/repo/deploy_kits/S786_ONLINE_BOOKING /tmp/s786kit && bash /tmp/s786kit/install_S786_ONLINE_BOOKING.sh
#  NEW /root/finance/online_booking.py (+ cron every 3 min) . NEW /root/portal/online_booking_portal.py (/portal/booking)
#  /root/portal/portal.py 34750b24 -> TO (the tile + the mount) . /root/finance/owner_console.py 1a3d4fd4 -> TO (a Needs-you line)
#  /root/portal/tile_grants.json 66de5e20 (v45) -> TO (v46: the tile to reception, shivani, alisha, shavez)
#  DRY=1 runs every gate and reads the clinic Gmail once (yes/no per mail, no values); writes nothing.
#  Undo:  bash /tmp/s786kit/install_S786_ONLINE_BOOKING.sh --undo
# =============================================================================
set -u
KIT="S786_ONLINE_BOOKING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
F1="$ROOT/portal/portal.py";         FROM1=34750b241d6e4bb9fb57bd52beebe1ee; TO1=8b7239192db3f77493b829a618fb33e9; BAK1="$F1.bak_S786_${FROM1:0:8}"
F2="$ROOT/finance/owner_console.py"; FROM2=1a3d4fd4a212429f3d7f604680a1cc32; TO2=97d63d71479a7a4598c1e8395d0516d0; BAK2="$F2.bak_S786_${FROM2:0:8}"
F3="$ROOT/portal/tile_grants.json";  FROM3=66de5e20771d3b7e1ad49d026b511540; TO3=b7b1fabfa4106ce1041fa13b9ac2bbcf; BAK3="$F3.bak_S786_${FROM3:0:8}"
N1="$ROOT/finance/online_booking.py";         TON1=eecc44593c0d286385ed16a4767422fd
N2="$ROOT/portal/online_booking_portal.py";   TON2=aa1642e110cf1dc9f55b01c45a35e13a
DB="${FINANCE_DB:-$ROOT/finance/finance.db}"
CRONLINE="*/3 * * * * flock -n /tmp/online_booking.lock $VPY -B $N1 >> $ROOT/finance/online_booking.log 2>&1 # S786_ONLINE_BOOKING"
HAVE_LOCK=0; OFF_MINE=0; PLACED=0; SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
fhz() { hcode "http://127.0.0.1:$FIN_PORT/finance/healthz"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
release() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$SCR" ] && rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
cron_off() { "$CRONTAB" -l 2>/dev/null | grep -v '# S786_ONLINE_BOOKING' | "$CRONTAB" - ; }
putback() {
  [ -f "$BAK1" ] && \cp -p "$BAK1" "$F1"; [ -f "$BAK2" ] && \cp -p "$BAK2" "$F2"; [ -f "$BAK3" ] && \cp -p "$BAK3" "$F3"
  [ -f "$N1" ] && mv -f "$N1" "$N1.undone_S786"; [ -f "$N2" ] && mv -f "$N2" "$N2.undone_S786"; cron_off
  find "$ROOT/portal" "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
  [ "$(m5 "$F1")" = "$FROM1" ] && [ "$(m5 "$F2")" = "$FROM2" ] && [ "$(m5 "$F3")" = "$FROM3" ] && [ ! -e "$N1" ] && [ ! -e "$N2" ] && echo 1 || echo 0
}
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting everything back"
  local ok; ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "   portal.py, owner_console.py and tile_grants.json are back byte-identically; the two new files and the cron line are off" \
                || echo "   !! NOT all back -- copy $BAK1, $BAK2, $BAK3 back by hand"
  echo "   finance healthz $(wait200 fhz) . portal health $(wait200 phz). Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 portal/portal.py)" = "$TO1" ] && [ "$(m5 finance/owner_console.py)" = "$TO2" ] && [ "$(m5 portal/tile_grants.json.s786)" = "$TO3" ] \
  && [ "$(m5 finance/online_booking.py)" = "$TON1" ] && [ "$(m5 portal/online_booking_portal.py)" = "$TON2" ] || stop "the kit's files are not the built ones"
if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK1" ] && [ -f "$BAK2" ] && [ -f "$BAK3" ] || stop "no backups -- nothing to undo"
  ok=$(putback); "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  [ "$ok" = 1 ] && echo "UNDONE: the three files are back, the page and the mail reader are off (table online_booking kept, unread); finance $(wait200 fhz) . portal $(wait200 phz)" || echo "!! not back -- send a photo"
  exit 0
fi
echo "[1/7] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
L1=$(m5 "$F1"); L2=$(m5 "$F2"); L3=$(m5 "$F3")
if [ "$L1" = "$TO1" ] && [ "$L2" = "$TO2" ] && [ "$L3" = "$TO3" ] && [ "$(m5 "$N1")" = "$TON1" ] && [ "$(m5 "$N2")" = "$TON2" ]; then
  echo "-- ALREADY INSTALLED. Nothing written. finance $(fhz) . portal $(phz)"; exit 0; fi
[ "$L1" = "$FROM1" ] || stop "the live $F1 is not the expected one (live ${L1:0:8}, kit expects ${FROM1:0:8})"
[ "$L2" = "$FROM2" ] || stop "the live $F2 is not the expected one (live ${L2:0:8}, kit expects ${FROM2:0:8})"
[ "$L3" = "$FROM3" ] || stop "the live $F3 is not the expected one (live ${L3:0:8}, kit expects ${FROM3:0:8})"
[ -e "$N1" ] || [ -e "$N2" ] && stop "a file of this kit is already there ($N1 or $N2) -- not this kit's bytes"
EACFG="${EMAIL_AGENT_CONFIG:-/root/deploy/email_agent.json}"; [ -f "$EACFG" ] || stop "the clinic Gmail login ($EACFG) is not there"
SCR=$(mktemp -d /tmp/s786.XXXX); chmod 700 "$SCR"; mkdir -p "$SCR/remake" "$SCR/live/portal" "$SCR/live/finance"
"$APY" -B "$KDIR/make_s786.py" "$F1" "$F2" "$F3" "$SCR/remake" >/dev/null 2>&1 && [ "$(m5 "$SCR/remake/portal/portal.py")" = "$TO1" ] \
  && [ "$(m5 "$SCR/remake/finance/owner_console.py")" = "$TO2" ] && [ "$(m5 "$SCR/remake/portal/tile_grants.json.s786")" = "$TO3" ] \
  || stop "make_s786.py on the live bytes does not give the kit's files"
for f in portal/portal.py finance/owner_console.py finance/online_booking.py portal/online_booking_portal.py; do
  "$APY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $APY"
  "$VPY" -W ignore -B -m py_compile "$KDIR/$f" 2>/dev/null || stop "$f does not compile with $VPY"
done
"$VPY" -c "import json; json.load(open('$KDIR/portal/tile_grants.json.s786'))" 2>/dev/null || stop "the new tile_grants.json does not read"
"$VPY" -B "$KDIR/finance/online_booking.py" --selftest >/dev/null 2>&1 || stop "the mail reader's selftest is not green"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[2/7] the live files are ${FROM1:0:8}, ${FROM2:0:8}, ${FROM3:0:8}; the kit's are those + the S786 edits (remade on the box); all compile under both pythons; the reader's selftest green"
"$VPY" -c "import sqlite3; s=sqlite3.connect('file:$DB?mode=ro', uri=True); d=sqlite3.connect('$SCR/f.db'); s.backup(d); d.close(); s.close()" 2>/dev/null || stop "could not copy finance.db for the walk"
\cp -p "$F1" "$SCR/live/portal/portal.py"; \cp -p "$F2" "$SCR/live/finance/owner_console.py"; \cp -p "$F3" "$SCR/live/portal/tile_grants.json"
R=$(cd "$SCR" && TMPDIR="$SCR" S786_LIBS="$ROOT/finance:$ROOT/portal" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s786.py" "$KDIR" "$SCR/f.db" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) stop "the S786 walk is not green ($R)";; esac
R2=$(cd "$SCR" && TMPDIR="$SCR" S786_LIBS="$ROOT/finance:$ROOT/portal" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s786.py" "$SCR/live" "$SCR/f.db" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control on the live files did not go red ($R2)";; esac
rm -f "$SCR/f.db"; find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "[3/7] the walk (a copy of finance.db, made-up patients): $R | the live files: $R2"
echo "[4/7] the clinic Gmail, read-only (what each Docterz payment mail gives -- yes/no, never a value):"
( cd "$SCR" && FINANCE_DB="$SCR/none.db" OB_STATE="$SCR/st.json" timeout 90 "$VPY" -B "$KDIR/finance/online_booking.py" --dry 2>&1 | tail -12 | sed 's/^/      /' )
[ "$(fhz)" = 200 ] && [ "$(phz)" = 200 ] || stop "finance or portal is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
if [ ! -e "$OFFSW" ]; then mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%F %T')" > "$OFFSW" && OFF_MINE=1; fi
echo "[5/7] the build lock taken; the doctor's auto-fix paused for the restarts"
{ \cp -p "$F1" "$BAK1" && [ "$(m5 "$BAK1")" = "$FROM1" ]; } || stop "could not keep a backup of $F1"
{ \cp -p "$F2" "$BAK2" && [ "$(m5 "$BAK2")" = "$FROM2" ]; } || stop "could not keep a backup of $F2"
{ \cp -p "$F3" "$BAK3" && [ "$(m5 "$BAK3")" = "$FROM3" ]; } || stop "could not keep a backup of $F3"
"$CRONTAB" -l > "$ROOT/finance/crontab.bak_S786" 2>/dev/null
PLACED=1
for pair in "portal/portal.py:$F1:$BAK1:$TO1" "finance/owner_console.py:$F2:$BAK2:$TO2" "portal/tile_grants.json.s786:$F3:$BAK3:$TO3" \
            "finance/online_booking.py:$N1:$BAK2:$TON1" "portal/online_booking_portal.py:$N2:$BAK1:$TON2"; do
  IFS=: read -r src dst ref to <<< "$pair"
  \cp "$KDIR/$src" "$dst.s786new" && chmod --reference="$ref" "$dst.s786new" && chown --reference="$ref" "$dst.s786new" 2>/dev/null; mv -f "$dst.s786new" "$dst" || restore "$src could not be placed"
  [ "$(m5 "$dst")" = "$to" ] || restore "$src read-back did not match"
done
find "$ROOT/portal" "$ROOT/finance" -maxdepth 1 -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
T0=$(date '+%Y-%m-%d %H:%M:%S')
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c2=$(wait200 phz); [ "$c2" = 200 ] || restore "portal health $c2"
c3=$(hcode "http://127.0.0.1:$PPORT/portal/booking"); case "$c3" in 302|401|403|303) ;; *) restore "the booking page answered $c3 without a login (not mounted?)";; esac
c4=$(hcode "http://127.0.0.1:$FIN_PORT/finance/console"); case "$c4" in 302|401|403|303) ;; *) restore "the console answered $c4 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$FSVC" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -v -i 'reentrant call' | grep -c -i -E 'online_booking|portal\.py|owner_console|NOT mounted|failed to load|ImportError|ModuleNotFoundError|SyntaxError|NameError|AssertionError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'booking|portal|console|Error|Traceback' | head -5; restore "journal: $JR error line(s) since the restarts"; }
FIRST=$(cd "$ROOT/finance" && FINANCE_DB="$DB" OB_STATE="$ROOT/finance/online_booking_state.json" timeout 120 "$VPY" -B "$N1" 2>&1 | tail -2)
ST=$("$VPY" -c "import json; s=json.load(open('$ROOT/finance/online_booking_state.json')); print('found %s . new %s . pushed %s . %s' % (s.get('found'), s.get('new'), s.get('pushed'), ('ERROR ' + s['error']) if s.get('error') else 'no error'))" 2>&1)
case "$ST" in *"no error"*) ;; *) restore "the first pass of the mail reader: $ST $FIRST";; esac
{ "$CRONTAB" -l 2>/dev/null | grep -v '# S786_ONLINE_BOOKING'; echo "$CRONLINE"; } | "$CRONTAB" - || restore "the cron line could not be added"
"$CRONTAB" -l 2>/dev/null | grep -q '# S786_ONLINE_BOOKING' || restore "the cron line is not in the crontab"
PLACED=0
echo "[6/7] placed (backups *.bak_S786_*); restarted at $(TZ=Asia/Kolkata date "+%H:%M IST"): finance $c1 . portal $c2; the page's door closed without a login ($c3); journal clean; first pass: $ST; cron every 3 min"
echo "[7/7] $KIT: DONE. Staff: portal -> Patients -> Online booking. Your console: Needs you shows the booking line."
