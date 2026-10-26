#!/bin/bash
# =============================================================================
#  install_S663_PORTAL_CONSOLIDATE.sh · kit S663 (26-Oct-2026, the parent, session 358) · START_HERE_SESSION_358 §0 B (drift 5 on portal.py)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s663kit && cp -rp /root/deploy/repo/deploy_kits/S663_PORTAL_CONSOLIDATE /tmp/s663kit && bash /tmp/s663kit/install_S663_PORTAL_CONSOLIDATE.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#   /root/portal/portal.py   fe9cc368 (S660's TO) -> TO   E1 the Expiry watch box hides when told to; E2 the Gist page's Reports pending card
#                                                         hides when told to; E3 two folder faces (Patients, System); E4 the Call Console
#                                                         Staff tab's unused five queries and their function gone
#  tile_grants.json NOT touched (read by the walk only). No data step. No crontab change. Restarts clinic-portal only. finance untouched.
#  ORDER: gates (window 08:02-23:49 IST, SUMS, KIT_ID) -> ALREADY INSTALLED? -> the build lock -> the FROM pin -> rebuilt here from the live
#  bytes (make_s663.py) = TO_PINS -> compile (both pythons) -> the walk on scratch + its control -> portal healthy -> DRY stops -> backup ->
#  DOCTOR_AUTO_OFF -> staged + renamed + read back -> restart portal (health) -> the walk on the placed file -> DOCTOR_AUTO_OFF removed -> lock released.
#  Red after placing: the file back from its backup, the portal restarted. Under set -u, not set -e: every gate is a test.
# =============================================================================
set -u
KIT="S663_PORTAL_CONSOLIDATE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
REL="portal/portal.py"
declare -A FROM TO
FROM[portal/portal.py]=fe9cc3680b078e1fc6806c28a5f136a2
while read -r h f; do TO[$f]=$h; done < "$KDIR/TO_PINS.md5"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s663_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
CONTROL="7 S663 check(s) red · 0 older red · 4 green"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$ROOT/$1.bak_S663_${FROM[$1]:0:8}"; }
phealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PPORT/portal/health"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the file back"
  for r in $REL; do \cp -p "$(bak "$r")" "$ROOT/$r" || say "   !! could not put back $ROOT/$r"; done
  rm -f "$ROOT"/portal/.*.s663
  "$SYSTEMCTL" restart "$PSVC" || true
  local p; p=$(wait200 phealth)
  for r in $REL; do say "   $ROOT/$r $(m5 "$ROOT/$r") (expected ${FROM[$r]})"; done
  say "   portal health $p. Send a photo of this screen to Claude."
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
"$APY" -c "import flask" 2>/dev/null || { say "!! preflight: $APY has no flask (the walk loads the portal) - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${DRY:-0}${SKIP_WINDOW:-0}" = 11 ] || { { [ "$HH" -gt 8 ] || { [ "$HH" -eq 8 ] && [ "$MM" -ge 2 ]; }; } && { [ "$HH" -lt 23 ] || [ "$MM" -le 49 ]; }; } \
  || { say "!! [1/8] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 08:02-23:49 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for r in $REL; do [ -f "$ROOT/$r" ] || { say "!! [1/8] $ROOT/$r is not there - nothing installed"; exit 1; }; done
ALL=1; for r in $REL; do [ "$(m5 "$ROOT/$r")" = "${TO[$r]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: portal.py is the kit's. Nothing written. portal $(phealth)"; exit 0; fi
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

for r in $REL; do C="$(m5 "$ROOT/$r")"; [ "$C" = "${FROM[$r]}" ] || stop_unlocked "!! [2/8] $ROOT/$r is ${C:0:8}, expected ${FROM[$r]:0:8} (S660's TO) - the file changed after this kit was built: STOP, nothing installed"; done
[ -f "$ROOT/portal/tile_grants.json" ] || stop_unlocked "!! [2/8] $ROOT/portal/tile_grants.json is not there (the walk reads it) - nothing installed"
say "[2/8] the live pin exact: portal.py at its FROM (S660's TO)"

mkdir -p "$SCR/built" "$SCR/old" "$SCR/pyc" || stop_unlocked "!! cannot make $SCR - nothing installed"
"$APY" -B make_s663.py "$ROOT" "$SCR/built" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop_unlocked "!! [3/8] the builder refused a live file - nothing installed"; }
for r in $REL; do [ "$(m5 "$SCR/built/$r")" = "${TO[$r]}" ] || stop_unlocked "!! [3/8] rebuilt, $r is $(m5 "$SCR/built/$r" | cut -c1-8), not ${TO[$r]:0:8} - nothing installed"; done
for py in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore::SyntaxWarning -m py_compile "$SCR/built/portal/portal.py" || stop_unlocked "!! [3/8] the built portal.py does not compile on $py - nothing installed"; done
mkdir -p "$SCR/old/portal"; for r in $REL; do \cp -p "$ROOT/$r" "$SCR/old/$r"; done
\cp -p "$ROOT/portal/tile_grants.json" "$SCR/old/portal/tile_grants.json" && \cp -p "$ROOT/portal/tile_grants.json" "$SCR/built/portal/tile_grants.json" || stop_unlocked "!! [3/8] could not copy tile_grants.json for the walk - nothing installed"
say "[3/8] rebuilt here from this box's live bytes: at its TO pin; the Python compiles under both pythons"

R=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s663.py" --new "$SCR/built" --base "$SCR/old" --lib "$ROOT" --scratch "$SCR/w1" 2>&1)
L1="$(echo "$R" | tail -1)"; [ "$L1" = "11 of 11 green" ] || { echo "$R" | grep -E 'RED|Error|Traceback' | head -20; stop_unlocked "!! [4/8] the walk is not green ($L1) - nothing installed"; }
R=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s663.py" --new "$SCR/built" --base "$SCR/old" --lib "$ROOT" --scratch "$SCR/w0" --old 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop_unlocked "!! [4/8] the control on the live files is not as expected ($R) - nothing installed"
say "[4/8] the walk: $L1; the control on the live files: $R"
p0=$(phealth); [ "$p0" = 200 ] || stop_unlocked "!! [5/8] portal health $p0 before the install - not healthy: nothing installed"
say "[5/8] the portal healthy before the install ($p0)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for r in $REL; do \cp -p "$ROOT/$r" "$(bak "$r")" && [ "$(m5 "$(bak "$r")")" = "${FROM[$r]}" ] || stop_unlocked "!! [6/8] could not write the backup of $ROOT/$r - nothing placed"; done
if [ -e "$OFFSW" ]; then
  say "       $OFFSW was already on ($(head -c 120 "$OFFSW" 2>/dev/null)) -- left exactly as found"
else
  mkdir -p "$(dirname "$OFFSW")" && echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restart below is this kit's; S578 must not restart a part it finds down" > "$OFFSW" && OFF_MINE=1 || stop_unlocked "!! [6/8] could not write $OFFSW - nothing placed"
fi
for r in $REL; do
  Lf="$ROOT/$r"; STG="$(dirname "$Lf")/.$(basename "$Lf").s663"
  { cat "$SCR/built/$r" > "$STG" && [ "$(m5 "$STG")" = "${TO[$r]}" ]; } || { rm -f "$ROOT"/portal/.*.s663; [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; stop_unlocked "!! [6/8] could not stage $Lf - nothing placed"; }
  chmod --reference="$Lf" "$STG" 2>/dev/null; chown --reference="$Lf" "$STG" 2>/dev/null
done
PLACED=1
for r in $REL; do Lf="$ROOT/$r"; mv -f "$(dirname "$Lf")/.$(basename "$Lf").s663" "$Lf" || restore "the rename of $Lf"; [ "$(m5 "$Lf")" = "${TO[$r]}" ] || restore "the md5 read back of $Lf"; done
say "[6/8] placed and read back: portal.py at its TO pin (backup portal.py.bak_S663_fe9cc368)"

"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
c4=$(wait200 phealth); [ "$c4" = 200 ] || restore "portal health $c4"
R=$(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$APY" -B "$KDIR/walk_s663.py" --new "$ROOT" --base "$SCR/old" --lib "$ROOT" --scratch "$SCR/w2" 2>&1 | tail -1)
[ "$R" = "11 of 11 green" ] || restore "the walk on the placed file: $R"
say "[7/8] $PSVC restarted and healthy ($c4); the walk on the placed file: $R"
if [ "$OFF_MINE" = 1 ]; then rm -f "$OFFSW"; fi
release_lock
UNDO=""; for r in $REL; do UNDO="$UNDO\\cp -p $(bak "$r") $ROOT/$r && "; done
say "[8/8] the build lock released"
say "undo (one line): ${UNDO}$SYSTEMCTL restart $PSVC"
say ""
say "$KIT: DONE. Nobody's tiles moved; Dr Bhawna's top row sits on one line again."
exit 0
