#!/bin/bash
# =============================================================================
#  install_S657_HOME_FOLDERS.sh · kit S657 (26-Oct-2026, Sanjeevni session 353) · the owner's "build" on the mock-up 7YXMpfkuiU4awTHHkNSNfu
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s657kit && cp -rp /root/deploy/repo/deploy_kits/S657_HOME_FOLDERS /tmp/s657kit && bash /tmp/s657kit/install_S657_HOME_FOLDERS.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#   /root/portal/portal.py                          844166b1 -> TO  (THE PARENT'S FILE) folders open in place; the Expiry watch box; his Sanjeevni split
#   /root/portal/tile_grants.json                   025f8ab9 -> TO  (THE PARENT'S FILE) v40: manoj's mask (4 tiles) and folder order
#   /root/finance/sanjeevni_approvals.py            bf86c8c8 -> TO  GET /finance/sanjeevni/expiry/api/count (checker, read only)
#   /root/finance/finance_ui/finance_approvals.html 885f6f31 -> TO  (THE PARENT'S TEMPLATE) three links in Other pages
#  No data step. No crontab change. Restarts clinic-finance, then clinic-portal. finance_app.py is NOT touched.
#  ORDER: gates (window 08:02-23:49 IST, SUMS, KIT_ID) -> ALREADY INSTALLED? -> the build lock -> the FROM pins -> rebuilt here from the
#  live bytes (make_s657.py) = TO_PINS -> compile (both pythons) -> the walk on scratch + its control -> both services healthy -> DRY stops
#  -> backups -> DOCTOR_AUTO_OFF -> staged + renamed + read back -> restart finance (healthz, the door 302/401 without a login, journal)
#  -> restart portal (health) -> the walk on the placed files -> DOCTOR_AUTO_OFF removed -> lock released -> DONE.
#  Red after placing: all four files back from their backups, both services restarted.
#  Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S657_HOME_FOLDERS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
DB="${DB:-$ROOT/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
REL="portal/portal.py portal/tile_grants.json finance/sanjeevni_approvals.py finance/finance_ui/finance_approvals.html"
declare -A FROM TO
FROM[portal/portal.py]=844166b11f6d62ece43b42fde8e11094
FROM[portal/tile_grants.json]=025f8ab9a2691023148ccc6deeac4f50
FROM[finance/sanjeevni_approvals.py]=bf86c8c8f30a7b223326f6f1d68fbb28
FROM[finance/finance_ui/finance_approvals.html]=885f6f31571ae19d20b8cb065080ad0b
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s657_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
CONTROL="19 S657 check(s) red · 0 older red · 7 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S657_${FROM[$1]:0:8}"; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
phealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT/portal/health"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting all four files back"
  for r in $REL; do \cp -p "$(bak "$r")" "$ROOT/$r" || say "   !! could not put back $ROOT/$r"; done
  rm -f "$ROOT"/portal/.*.s657 "$ROOT"/finance/.*.s657 "$ROOT"/finance/finance_ui/.*.s657
  "$SYSTEMCTL" restart "$FSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  local f p; f=$(wait200 "fhealth /finance/healthz"); p=$(wait200 phealth)
  for r in $REL; do say "   $ROOT/$r $(m5 "$ROOT/$r") (expected ${FROM[$r]})"; done
  say "   finance healthz $f, portal health $p. Send a photo of this screen to Claude."
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
"$APY" -c "import flask" 2>/dev/null || { say "!! preflight: $APY has no flask (the walk loads the portal and the finance blueprint) - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }   # SKIP_WINDOW only with DRY=1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for r in $REL; do [ -f "$ROOT/$r" ] || { say "!! [1/9] $ROOT/$r is not there - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [1/9] $DB is missing - nothing installed"; exit 1; }
ALL=1; for r in $REL; do [ "$(m5 "$ROOT/$r")" = "${TO[$r]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. finance healthz $(fhealth /finance/healthz), portal $(phealth)"; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif [ "$(awk '{print $1}' "$LOCK/owner" 2>/dev/null)" = "$KIT" ]; then
  TOOK_LOCK=1; say "[1/9] kit gates green; the build lock is already held by $KIT"
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."
  exit 3
fi

for r in $REL; do C="$(m5 "$ROOT/$r")"; [ "$C" = "${FROM[$r]}" ] || stop_unlocked "!! [2/9] $ROOT/$r is ${C:0:8}, expected ${FROM[$r]:0:8} - it changed after this kit was built: STOP, nothing installed"; done
say "[2/9] live pins exact: the four files at their FROM"

mkdir -p "$SCR/built" "$SCR/old" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s657.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/9] the builder refused a live file - nothing installed"; }
for r in $REL; do [ "$(m5 "$SCR/built/$r")" = "${TO[$r]}" ] || stop_unlocked "!! [3/9] rebuilt, $r is $(m5 "$SCR/built/$r" | cut -c1-8), not ${TO[$r]:0:8} - nothing installed"; done
for py in "$APY" "$VPY"; do for r in portal/portal.py finance/sanjeevni_approvals.py; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore::SyntaxWarning -m py_compile "$SCR/built/$r" || stop_unlocked "!! [3/9] the built $r does not compile on $py - nothing installed"; done; done
"$APY" -c "import json,sys; json.load(open(sys.argv[1]))" "$SCR/built/portal/tile_grants.json" || stop_unlocked "!! [3/9] the built tile_grants.json is not valid JSON - nothing installed"
for r in $REL; do mkdir -p "$(dirname "$SCR/old/$r")"; \cp -p "$ROOT/$r" "$SCR/old/$r"; done
say "[3/9] rebuilt here from this box's live bytes: each at its TO pin; the Python compiles under both pythons; the JSON reads"

copydb "$DB" "$SCR/walk.db" || stop_unlocked "!! [4/9] no copy of the database - nothing installed"
R=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s657.py" --new "$SCR/built" --live "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w1" 2>&1)
L1="$(echo "$R" | tail -1)"; [ "$L1" = "26 of 26 green" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/9] the walk is not green ($L1) - nothing installed"; }
R=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s657.py" --new "$SCR/built" --live "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w0" --old 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/9] the control on the live files is not as expected ($R) - nothing installed"
say "[4/9] the walk on a copy of the database: $L1; the control on the live files: $R"
f0=$(fhealth /finance/healthz); p0=$(phealth)
[ "$f0" = 200 ] && [ "$p0" = 200 ] || stop_unlocked "!! [5/9] finance healthz $f0, portal $p0 before the install - not healthy: nothing installed"
say "[5/9] both services healthy before the install (finance $f0, portal $p0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for r in $REL; do \cp -p "$ROOT/$r" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop_unlocked "!! [6/9] could not write the backup of $ROOT/$r - nothing placed"; done
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restarts below are this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [6/9] could not write $OFFSW - nothing placed"
fi
for r in $REL; do
  Lf="$ROOT/$r"; STG="$(dirname "$Lf")/.$(basename "$Lf").s657"
  { cat "$SCR/built/$r" > "$STG" && [ "$(m5 "$STG")" = "${TO[$r]}" ]; } || { rm -f "$ROOT"/portal/.*.s657 "$ROOT"/finance/.*.s657 "$ROOT"/finance/finance_ui/.*.s657; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [6/9] could not stage $Lf - nothing placed"; }
  chmod --reference="$Lf" "$STG" 2>/dev/null; chown --reference="$Lf" "$STG" 2>/dev/null
done
PLACED=1
for r in $REL; do Lf="$ROOT/$r"; mv -f "$(dirname "$Lf")/.$(basename "$Lf").s657" "$Lf" || restore "the rename of $Lf"; [ "$(m5 "$Lf")" = "${TO[$r]}" ] || restore "the md5 read back of $Lf"; done
say "[6/9] placed and read back: four files at their TO pins (backups *.bak_S657_<from8>)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
c1=$(wait200 "fhealth /finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(fhealth /finance/sanjeevni/expiry/api/count); c3=$(fhealth /finance/sanjeevni/expiry)
case "$c2" in 302|401|303|403) ;; *) restore "the count door answered $c2 without a login (302 = the login gate, expected)";; esac
case "$c3" in 302|401|303|403) ;; *) restore "the expiry page answered $c3 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  "$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -q -i "not mounted" && restore "a finance module not mounted"
  JR="$("$JOURNALCTL" -u "$FSVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[7/9] $FSVC restarted at $T0 (the box's clock): healthz $c1; the count door $c2 and the expiry page $c3 without a login; journal clean"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c4=$(wait200 phealth); [ "$c4" = 200 ] || restore "portal health $c4"
R=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s657.py" --new "$ROOT" --live "$SCR/old" --lib "$ROOT" --db "$SCR/walk.db" --scratch "$SCR/w2" 2>&1 | tail -1)
[ "$R" = "26 of 26 green" ] || restore "the walk on the placed files: $R"
say "[8/9] $PSVC restarted and healthy ($c4); the walk on the placed files: $R"
if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; fi
release_lock
UNDO=""; for r in $REL; do UNDO="$UNDO\\cp -p $(bak "$r") $ROOT/$r && "; done
say "[9/9] the build lock released"
say "undo (one line): ${UNDO}$SYSTEMCTL restart $FSVC && $SYSTEMCTL restart $PSVC"
say ""
say "$KIT: DONE. Your home: folders open in place; the Expiry watch box sits beside 'Sanjeevni to approve'."
exit 0
