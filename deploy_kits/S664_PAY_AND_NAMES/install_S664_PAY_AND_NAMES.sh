#!/bin/bash
# =============================================================================
#  install_S664_PAY_AND_NAMES.sh · kit S664 (26-Oct-2026, Sanjeevni session 359) · the owner's "Do all 5": the S335 list, its code part
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s664kit && cp -rp /root/deploy/repo/deploy_kits/S664_PAY_AND_NAMES /tmp/s664kit && bash /tmp/s664kit/install_S664_PAY_AND_NAMES.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#   /root/finance/supplier_msg.py  f208d2b5 -> TO  the backup Bhejo asks first when the message was handed to the reception phone
#   /root/finance/bank_sms.py      4ddbdd16 -> TO  the NEFT portion counts only payable lines, as the advice does
#   /root/finance/purchase_app.py  82654e0c -> TO  (on kit S662's bytes) the S446 page and the Needs-you line say Scan reading, not Sarvam
#  No data step. No crontab change. Restarts clinic-finance only. The portal: nothing.
#  ORDER: gates -> ALREADY INSTALLED? -> lock -> FROM pins -> rebuilt here = TO_PINS -> compile -> walk + control -> healthy -> DRY stops
#  -> backups -> DOCTOR_AUTO_OFF -> staged, renamed, read back -> restart finance (healthz, two pages 302/401, journal)
#  -> the walk on the placed files -> switch off, lock released -> DONE. Red after placing: all three files back, finance restarted.
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S664_PAY_AND_NAMES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
REL="finance/supplier_msg.py finance/bank_sms.py finance/purchase_app.py"
declare -A FROM TO
FROM[finance/supplier_msg.py]=f208d2b52abf866eda6a138c266ec1f8
FROM[finance/bank_sms.py]=4ddbdd16acb4d8198a2f7111b960c43c
FROM[finance/purchase_app.py]=82654e0c6e8f18225067bd04fc4329ea
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s664_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
GREEN="11 of 11 green"
CONTROL="7 S664 check(s) red · 0 older red · 4 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S664_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
fpost() { curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$FIN_PORT$1"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
fhz() { fhealth /finance/healthz; }
walk() { (cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s664.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting all three files back"
  for r in $REL; do \cp -p "$(bak "$r")" "$ROOT/$r" || say "   !! could not put back $ROOT/$r"; done
  rm -f "$ROOT"/finance/.*.s664
  "$SYSTEMCTL" restart "$FSVC" || true
  local f; f=$(wait200 fhz)
  for r in $REL; do say "   $ROOT/$r $(m5 "$ROOT/$r") (expected ${FROM[$r]})"; done
  say "   finance healthz $f. Send a photo of this screen to Claude."
  [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep sleep find sed timeout; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
"$APY" -c "import flask" 2>/dev/null || { say "!! preflight: $APY has no flask (the walk mounts the finance blueprints) - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }   # SKIP_WINDOW only with DRY=1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for r in $REL; do [ -f "$ROOT/$r" ] || { say "!! [1/8] $ROOT/$r is not there - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/8] $DB is missing - nothing installed"; exit 1; }
ALL=1; for r in $REL; do [ "$(m5 "$ROOT/$r")" = "${TO[$r]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the three files are the kit's. Nothing written. finance healthz $(fhz)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/8] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/8] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/8] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi

for r in $REL; do C="$(m5 "$ROOT/$r")"; [ "$C" = "${FROM[$r]}" ] || stop_unlocked "!! [2/8] $ROOT/$r is ${C:0:8}, expected ${FROM[$r]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/8] live pins exact: the three files at their FROM"

mkdir -p "$SCR/built" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s664.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for r in $REL; do [ "$(m5 "$SCR/built/$r")" = "${TO[$r]}" ] || stop_unlocked "!! [3/8] rebuilt, $r is $(m5 "$SCR/built/$r" | cut -c1-8), not ${TO[$r]:0:8} - nothing installed"; done
for py in "$APY" "$VPY"; do for r in $REL; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore::SyntaxWarning -m py_compile "$SCR/built/$r" || stop_unlocked "!! [3/8] the built $r does not compile on $py - nothing installed"; done; done
say "[3/8] rebuilt here from this box's live bytes: each at its TO pin; all three compile under both pythons"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/8] no copy of the database - nothing installed"
R=$(walk --new "$SCR/built" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1")
L1="$(echo "$R" | tail -1)"; [ "$L1" = "$GREEN" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/8] the walk is not green ($L1) - nothing installed"; }
R=$(walk --old "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live files is not as expected ($R) - nothing installed"
say "[4/8] the walk on a copy of the database: $L1; the control on the live files: $R"
f0=$(fhz)
[ "$f0" = 200 ] || stop_unlocked "!! [5/8] finance healthz $f0 before the install - not healthy: nothing installed"
say "[5/8] finance healthy before the install ($f0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for r in $REL; do \cp -p "$ROOT/$r" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop_unlocked "!! [6/8] could not write the backup of $ROOT/$r - nothing placed"; done
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [6/8] could not write $OFFSW - nothing placed"
fi
for r in $REL; do
  Lf="$ROOT/$r"; STG="$(dirname "$Lf")/.$(basename "$Lf").s664"
  { cat "$SCR/built/$r" > "$STG" && [ "$(m5 "$STG")" = "${TO[$r]}" ]; } || { rm -f "$ROOT"/finance/.*.s664; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [6/8] could not stage $Lf - nothing placed"; }
  chmod --reference="$Lf" "$STG" 2>/dev/null; chown --reference="$Lf" "$STG" 2>/dev/null
done
PLACED=1
for r in $REL; do Lf="$ROOT/$r"; mv -f "$(dirname "$Lf")/.$(basename "$Lf").s664" "$Lf" || restore "the rename of $Lf"; [ "$(m5 "$Lf")" = "${TO[$r]}" ] || restore "the md5 read back of $Lf"; done
say "[6/8] placed and read back: three files at their TO pins (backups *.bak_S664_<from8>)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 fhz); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/purchase/page/pay); c3=$(fhealth /finance/purchase/page/sarvam)
case "$c2" in 302|401|303|403) ;; *) restore "the Vendor payments page answered $c2 without a login (302 = the login gate, expected)";; esac
case "$c3" in 302|401|303|403) ;; *) restore "the Scan reading page answered $c3 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -q -i "not mounted" && restore "a finance module not mounted"
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[7/8] $FSVC restarted at $T0 (the box's clock): healthz $c1; both pages $c2/$c3 without a login; journal clean"
R=$(walk --new "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w2" | tail -1)
[ "$R" = "$GREEN" ] || restore "the walk on the placed files: $R"
if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; fi
release_lock
UNDO=""; for r in $REL; do UNDO="$UNDO\\cp -p $(bak "$r") $ROOT/$r && "; done
say "[8/8] the walk on the placed files: $R; the build lock released"
say "undo (one line): ${UNDO}$SYSTEMCTL restart $FSVC"
say ""
say "$KIT: DONE. Bhejo asks first when the phone already has the message; the NEFT figure counts payable lines only; the page says Scan reading."
exit 0
