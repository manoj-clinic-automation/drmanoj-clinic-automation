#!/bin/bash
# =============================================================================
#  install_S698_CALLS_R1.sh · kit S698 (02-Nov-2026, the parent, session 379) · D819, D820, F-1083, F-1084, AF-35.
#  THE CALL CONSOLE, round 1: the page in the month page's look (the approved mock-up v12) and the doubled call rows mended.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s698kit && cp -rp /root/deploy/repo/deploy_kits/S698_CALLS_R1 /tmp/s698kit && bash /tmp/s698kit/install_S698_CALLS_R1.sh
#  (DRY=1 before bash: every gate, the make on the live bytes, the selftests, the walk, the control and the trace; nothing written.)
#  THREE live files are EDITED by make_s698.py on the box (counted edits, the result pinned to the kit's TO bytes) and ONE is new:
#   /root/portal/portal.py                      4ff31351 -> TO   the old console at /portal/console/old; the digest's last build (F-1084); the new module registered
#   /root/wa/portal_console.py                  552135b5 -> TO   the builder folds the doubled rows (F-1083); its selftest
#   /root/wa/call-hook/call_hook_capture.py     b8a1a293 -> TO   v3.2: the verified row (F-1083); its selftest
#   /root/portal/calls_console.py               NEW      -> TO   the page (reads console.db only; the click-to-call; the transcript on tap)
#  TWO tools placed beside the hook (never run by the services): repair_call_durations_s698.py, trace_s698.py.
#  THEN, on the box: the trace of the doubled rows (read-only, counts) -> the repair of the Call_Durations tab from the raw log
#  (backup CSV first, verified, restored on a failure) -> the console cron 07:00-22:50 (was 09-21) -> console.db rebuilt once.
#  Restarts call-hook (twice: the new code, then after the repair) and clinic-portal.
#  ORDER: gates -> the live pins -> the make on the live bytes = the kit's TO -> compile on both pythons -> the three selftests ->
#  the walk on made-up data + the control on the live files + the trace -> backups -> DOCTOR_AUTO_OFF -> stage + atomic move ->
#  call-hook restarted (alive, v3.2 in its journal) -> clinic-portal restarted (health 200, the gates, the new master's journal
#  clean) -> the repair -> the cron line -> the rebuild -> the walk on the placed files. Red after placing: the three files back,
#  the new file removed, both services restarted. The repair's undo is its own CSV (printed).
# =============================================================================
set -u
KIT="S698_CALLS_R1"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
PD="$ROOT/portal"; WA="$ROOT/wa"; HK="$WA/call-hook"
CDB="${CDB:-$WA/console.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
OFFSW="${OFFSW:-/root/deploy/_off/DOCTOR_AUTO_OFF}"
PPORT="${PPORT:-8099}"; PSVC="${PSVC:-clinic-portal}"
HPORT="${HPORT:-8098}"; HSVC="${HSVC:-call-hook}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"; CRONTAB="${CRONTAB:-crontab}"
CRON_LOCK="${CRON_LOCK:-$WA/console_cron.lock}"
SKIP_REPAIR="${SKIP_REPAIR:-0}"
REPAIRED="the tab's repair did not run"
# the edited files: name -> live path
declare -A LIVE=( [portal.py]="$PD/portal.py" [portal_console.py]="$WA/portal_console.py" [call_hook_capture.py]="$HK/call_hook_capture.py" )
declare -A WHICH=( [portal.py]=portal [portal_console.py]=builder [call_hook_capture.py]=hook )
declare -A FROM=( [portal.py]=4ff313516f0521533dff1851d8b018ba [portal_console.py]=552135b53564491dfe5629b2311b2076 [call_hook_capture.py]=b8a1a293c54dfb6528e04fdf31f8d3e6 )
EDITED="portal.py portal_console.py call_hook_capture.py"
NEWF="calls_console.py"; NEWLIVE="$PD/calls_console.py"
TOOLS="repair_call_durations_s698.py trace_s698.py"
ALLTO="$EDITED $NEWF $TOOLS"
declare -A TO
for n in $ALLTO; do TO[$n]="$(awk -v f="$n" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s698_inst_$STAMP"
PLACED=0; TOOK_LOCK=0; OFF_MINE=0
GREEN="WALK S698: 82 of 82 green · mutants caught 9 of 9 · "
CONTROL="CONTROL: 82 red"
OLDCRON='*/10 9-21 * * * /usr/bin/flock -n /root/wa/console_cron.lock'
NEWCRON='*/10 7-22 * * * /usr/bin/flock -n /root/wa/console_cron.lock'

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "${LIVE[$1]}.bak_S698_${FROM[$1]:0:8}"; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
halive() { curl -s -m 8 "http://127.0.0.1:$HPORT/" 2>/dev/null | grep -q "alive" && echo alive || echo down; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$($1); [ "$h" = 200 ] && break; done; echo "$h"; }
waitalive() { local h=down; for _t in 1 2 3 4 5 6 7 8; do sleep 2; h=$(halive); [ "$h" = alive ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null || say "   !! the lock could not be released -- run: rm -f $LOCK/owner; rmdir $LOCK"; TOOK_LOCK=0; }
off_clear() { [ "$OFF_MINE" = 1 ] && rm -f "$OFFSW"; OFF_MINE=0; }
on_exit() { [ "${KEEP:-0}" = 1 ] || rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
walk() { (cd "$SCR" && PYTHONPYCACHEPREFIX="$SCR/pyc" WALK_TMPDIR="$SCR/wtmp" timeout 900 "$VPY" -B "$KDIR/walk_s698.py" "$@" 2>&1); }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the three files back and removing the new one"
  PLACED=2
  for n in $EDITED; do \cp -p "$(bak $n)" "${LIVE[$n]}" || say "   !! could not put back ${LIVE[$n]}"; done
  rm -f "$NEWLIVE" "$PD"/.*.s698 "$WA"/.*.s698 "$HK"/.*.s698
  "$SYSTEMCTL" restart "$HSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
  for n in $EDITED; do say "   ${LIVE[$n]} $(m5 "${LIVE[$n]}" | cut -c1-8) (expected ${FROM[$n]:0:8})"; done
  say "   call-hook $(waitalive) · portal health $(wait200 phz). Send a photo of this screen to Claude."
  off_clear; release_lock
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; off_clear; release_lock; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP
stop_unlocked() { say "$1"; off_clear; release_lock; exit "${2:-1}"; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl grep find sed timeout sleep; do command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }; done
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
HH="$(TZ=Asia/Kolkata date +%H)"; MM="$(TZ=Asia/Kolkata date +%M)"; HH=$((10#$HH)); MM=$((10#$MM))
[ "${SKIP_WINDOW:-0}" = 1 ] || { [ "$HH" -ge 4 ] && { [ "$HH" -lt 23 ] || [ "$MM" -le 30 ]; }; } \
  || { say "!! [1/9] $(TZ=Asia/Kolkata date '+%H:%M IST') is outside the install window 04:00-23:30 IST - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $ALLTO; do [ -n "${TO[$n]}" ] || { say "!! [1/9] TO_PINS.md5 does not name $n - nothing installed"; exit 1; }; done
for n in $NEWF $TOOLS; do [ "$(m5 "$KDIR/$n")" = "${TO[$n]}" ] || { say "!! [1/9] the kit's $n is not at its TO pin - nothing installed"; exit 1; }; done
for n in $EDITED; do [ -f "${LIVE[$n]}" ] || { say "!! [1/9] ${LIVE[$n]} is missing - nothing installed"; exit 1; }; done
AT=0; for n in $EDITED; do [ "$(m5 "${LIVE[$n]}")" = "${TO[$n]}" ] && AT=$((AT+1)); done
[ -f "$NEWLIVE" ] && [ "$(m5 "$NEWLIVE")" = "${TO[$NEWF]}" ] && AT=$((AT+1))
lock_pid() { awk -v k="$KIT" '$1==k{print $2}' "$LOCK/owner" 2>/dev/null; }
lock_stale() { local p; p="$(lock_pid)"; [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null; }
if [ "$AT" = 4 ]; then
  STALE=0
  if [ -d "$LOCK" ] && lock_stale; then rm -f "$LOCK/owner"; rmdir "$LOCK" 2>/dev/null; STALE=1; say "   (a build lock left by an earlier $KIT run that was stopped was released)"; fi
  if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ] && ! [ -d "$LOCK" ]; then
    rm -f "$OFFSW"; STALE=1; say "   (a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped was removed)"
  fi
  if [ "$STALE" = 1 ] && [ "${DRY:-0}" != 1 ]; then
    "$SYSTEMCTL" restart "$HSVC" || true; "$SYSTEMCTL" restart "$PSVC" || true
    say "   both services restarted after the stopped run: call-hook $(waitalive) · portal health $(wait200 phz)"
  fi
  say "-- ALREADY INSTALLED: the four files are the kit's. Nothing written. call-hook $(halive) · portal health $(phz)"; exit 0
fi
if [ "$AT" != 0 ]; then
  say "!! [1/9] $AT of the four files are already at the kit's TO and the rest are not - HALF PLACED: nothing installed. Tell Claude."; exit 1
fi
[ -e "$NEWLIVE" ] && { say "!! [1/9] $NEWLIVE exists and is not the kit's - STOP, nothing installed. Tell Claude."; exit 1; }
if [ "${DRY:-0}" = 1 ]; then
  say "[1/9] DRY RUN: kit gates green (SUMS, KIT_ID, the window, the kit's files at their TO pins); no lock"
elif mkdir "$LOCK" 2>/dev/null; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock taken $(date '+%Y-%m-%d %H:%M:%S %Z') by $KIT"
elif lock_stale; then
  TOOK_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/9] kit gates green; the build lock left by an earlier $KIT run that was stopped is taken over"
elif [ -n "$(lock_pid)" ]; then
  say "!! [1/9] another $KIT run (process $(lock_pid)) is still going - nothing installed. Wait for it to finish."; exit 3
else
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3
fi
if [ "$TOOK_LOCK" = 1 ] && [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "      a DOCTOR_AUTO_OFF left by an earlier $KIT run that was stopped is this run's to clear"
fi
for n in $EDITED; do C=$(m5 "${LIVE[$n]}"); [ "$C" = "${FROM[$n]}" ] || stop_unlocked "!! [2/9] ${LIVE[$n]} is ${C:0:8}, expected ${FROM[$n]:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
say "[2/9] live pins exact: $(for n in $EDITED; do printf '%s %s  ' "$n" "${FROM[$n]:0:8}"; done); calls_console.py not there yet"

mkdir -p "$SCR/built" "$SCR/pyc" "$SCR/wtmp" "$SCR/old" && chmod 700 "$SCR" || stop_unlocked "!! cannot make $SCR - nothing installed"
for n in $EDITED; do
  "$APY" "$KDIR/make_s698.py" "${WHICH[$n]}" "${LIVE[$n]}" "$SCR/built/$n" || stop_unlocked "!! [3/9] make_s698.py could not apply its edits to the live $n - nothing installed. Tell Claude."
  [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || stop_unlocked "!! [3/9] the live $n edited on the box is not the kit's TO ($(m5 "$SCR/built/$n" | cut -c1-8) vs ${TO[$n]:0:8}) - nothing installed. Tell Claude."
done
for n in $NEWF $TOOLS; do \cp -p "$KDIR/$n" "$SCR/built/$n"; done
for py in "$APY" "$VPY"; do for n in $ALLTO; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" 2>/dev/null || stop_unlocked "!! [3/9] $n does not compile on $py - nothing installed"
done; done
S1="$(cd "$SCR/built" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -B portal_console.py --selftest 2>&1 | tail -1)"
[ "$S1" = "SELFTEST PASSED (54 checks, 0 failed)" ] || stop_unlocked "!! [3/9] the builder's selftest: $S1 - nothing installed"
S2="$(cd "$SCR/wtmp" && PYTHONPYCACHEPREFIX="$SCR/pyc" CALLHOOK_REJECT_DIR="$SCR/wtmp/rej" CALLHOOK_RAW_LOG_DIR="$SCR/wtmp/raw" timeout 300 "$VPY" -B "$SCR/built/call_hook_capture.py" --selftest 2>&1 | tail -1)"
[ "$S2" = "selftest: 69/69 passed" ] || stop_unlocked "!! [3/9] the hook's selftest: $S2 - nothing installed"
S3="$(cd "$SCR/built" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -B repair_call_durations_s698.py --selftest 2>&1 | tail -1)"
[ "$S3" = "selftest: PASSED" ] || stop_unlocked "!! [3/9] the repair tool's selftest: $S3 - nothing installed"
say "[3/9] the three live files edited on the box = the kit's TO bytes; every file compiles on both pythons; selftests: builder 54/54, hook 69/69, repair tool PASSED"

WOUT="$(walk "$SCR/built")"; R="$(echo "$WOUT" | tail -1)"
[ "$R" = "$GREEN" ] || { echo "$WOUT" | grep -E '^  RED|^  MISSED' | head -12; stop_unlocked "!! [4/9] the walk on the new files is not green ($R) - nothing installed"; }
for n in $EDITED; do \cp -p "${LIVE[$n]}" "$SCR/old/$n"; done
COUT="$(walk "$SCR/old" --control)"; R0="$(echo "$COUT" | tail -1)"
[ "$R0" = "$CONTROL" ] || stop_unlocked "!! [4/9] the control on the live files is not as expected ($R0) - nothing installed"
TR="$(PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -B "$SCR/built/trace_s698.py" --db "$CDB" --builder "$SCR/built/portal_console.py" 2>&1)" || TR="$TR (the trace could not run)"
say "[4/9] the walk on made-up data: $GREEN; the control on the live files: $R0"
printf '%s\n' "$TR" | sed 's/^/      /'
for n in $EDITED; do [ "$(m5 "${LIVE[$n]}")" = "${FROM[$n]}" ] || stop_unlocked "!! [4/9] ${LIVE[$n]} changed during the walk - nothing installed"; done
p0=$(phz); h0=$(halive); [ "$p0" = 200 ] && [ "$h0" = alive ] || stop_unlocked "!! [4/9] portal health $p0 / call-hook $h0 before the install - nothing installed"
if [ "${DRY:-0}" = 1 ]; then
  RD="$(cd "$HK" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -B "${REPAIR_PY:-$SCR/built/repair_call_durations_s698.py}" --dry-run --hook "$HK/call_hook_capture.py" 2>&1 | grep -v '^\[call_hook_capture\]')"
  printf '%s\n' "$RD" | sed 's/^/      /'
  say "-- DRY RUN: every gate, the make, the selftests, the walk, the control, the trace and the repair's plan; NOTHING written"; exit 0
fi

for n in $EDITED; do
  [ -e "$(bak $n)" ] && [ "$(m5 "$(bak $n)")" != "${FROM[$n]}" ] && stop_unlocked "!! [5/9] a backup $(bak $n) is there and is not the FROM bytes - left as it is; nothing placed. Tell Claude."
  { \cp -p "${LIVE[$n]}" "$(bak $n)" && [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ]; } || stop_unlocked "!! [5/9] could not write the backup $(bak $n) - nothing placed"
done
if [ -e "$OFFSW" ] && [ "$(awk 'NR==1{print $1}' "$OFFSW" 2>/dev/null)" = "$KIT" ]; then
  OFF_MINE=1; say "[5/9] DOCTOR_AUTO_OFF was left by an earlier $KIT run that was stopped - this run takes it as its own and removes it at the end"
elif [ -e "$OFFSW" ]; then
  say "[5/9] DOCTOR_AUTO_OFF is already on ($(head -c 120 "$OFFSW" 2>/dev/null)) - left exactly as it is; this kit will not remove it"
else
  mkdir -p "$(dirname "$OFFSW")" || stop_unlocked "!! [5/9] could not make the folder of $OFFSW - nothing placed"
  if (set -o noclobber; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S') -- the restarts below are this kit's" > "$OFFSW") 2>/dev/null; then OFF_MINE=1
  else stop_unlocked "!! [5/9] could not write $OFFSW (or someone else set it just now) - nothing placed"; fi
fi
stage() {  # $1 name, $2 live path, $3 reference for mode/owner
  local STG="$(dirname "$2")/.$1.s698"
  { cat "$SCR/built/$1" > "$STG" && [ "$(m5 "$STG")" = "${TO[$1]}" ]; } || { rm -f "$PD"/.*.s698 "$WA"/.*.s698 "$HK"/.*.s698; stop_unlocked "!! [5/9] could not stage $1 - nothing placed"; }
  chmod --reference="$3" "$STG" 2>/dev/null; chown --reference="$3" "$STG" 2>/dev/null
}
for n in $EDITED; do stage "$n" "${LIVE[$n]}" "${LIVE[$n]}"; done
stage "$NEWF" "$NEWLIVE" "$PD/portal.py"
for n in $TOOLS; do stage "$n" "$HK/$n" "$HK/call_hook_capture.py"; done
PLACED=1
mv -f "$PD/.$NEWF.s698" "$NEWLIVE" || restore "the rename of $NEWF"
for n in $TOOLS; do mv -f "$HK/.$n.s698" "$HK/$n" || restore "the rename of $n"; done
for n in call_hook_capture.py portal_console.py portal.py; do mv -f "$(dirname "${LIVE[$n]}")/.$n.s698" "${LIVE[$n]}" || restore "the rename of $n"; done
for n in $EDITED; do [ "$(m5 "${LIVE[$n]}")" = "${TO[$n]}" ] || restore "read back $n"; done
[ "$(m5 "$NEWLIVE")" = "${TO[$NEWF]}" ] || restore "read back $NEWF"
chmod 700 "$HK/repair_call_durations_s698.py" "$HK/trace_s698.py" 2>/dev/null
say "[5/9] placed and read back: $(for n in $EDITED $NEWF; do printf '%s %s  ' "$n" "${TO[$n]:0:8}"; done)(backups *.bak_S698_<from8>; the tools beside the hook)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$HSVC" || restore "restart $HSVC"
h1=$(waitalive); [ "$h1" = alive ] || restore "call-hook $h1 after the restart"
sleep 2
HJ="$("$JOURNALCTL" -u "$HSVC" --since "$T0" --no-pager 2>/dev/null)"
printf '%s\n' "$HJ" | grep -q "receiver v3.2" || restore "the hook's journal does not say v3.2 after the restart"
HR="$(printf '%s\n' "$HJ" | grep -c -i -E 'Traceback|ImportError|SyntaxError')"
[ "${HR:-0}" = 0 ] || { printf '%s\n' "$HJ" | grep -i -E 'Traceback|ImportError|SyntaxError' | head -5; restore "the hook's journal: $HR error line(s)"; }
KNOWN="$(printf '%s\n' "$HJ" | grep -o '[0-9]* rows known' | tail -1)"
"$SYSTEMCTL" restart "$PSVC" || restore "restart $PSVC"
p1=$(wait200 phz); [ "$p1" = 200 ] || restore "portal health $p1"
c2=$(hcode "http://127.0.0.1:$PPORT/portal/console"); case "$c2" in 302|401|403|303) ;; *) restore "/portal/console answered $c2 without a login";; esac
c3=$(hcode "http://127.0.0.1:$PPORT/portal/console/old"); case "$c3" in 302|401|403|303) ;; *) restore "/portal/console/old answered $c3 without a login";; esac
c4=$(hcode "http://127.0.0.1:$PPORT/portal/console/api/call"); case "$c4" in 302|401|403|303|405) ;; *) restore "/portal/console/api/call answered $c4 without a login";; esac
sleep 2
JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null | awk '/Starting gunicorn|Listening at:/{f=1} f{print} END{if(!f)exit 9}')" || JL="$("$JOURNALCTL" -u "$PSVC" --since "$T0" --no-pager 2>/dev/null)"
JR="$(printf '%s\n' "$JL" | grep -c -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback')"
[ "${JR:-0}" = 0 ] || { printf '%s\n' "$JL" | grep -i -E 'calls_console|failed to load|ImportError|ModuleNotFoundError|Traceback' | head -5; restore "journal: $JR line(s) naming the new module, an import error or a traceback since the restart"; }
say "[6/9] $HSVC restarted ($h1, v3.2, $KNOWN); $PSVC restarted at $T0: health $p1; /portal/console $c2, /old $c3, the call api $c4 without a login (the gate); the new master's journal ($(printf '%s\n' "$JL" | grep -c .) line(s)) names no module of this kit, import error or traceback"

if [ "$SKIP_REPAIR" = 1 ]; then
  say "[7/9] the repair of the Call_Durations tab SKIPPED at your word (SKIP_REPAIR=1); run it later: cd $HK && $VPY repair_call_durations_s698.py --apply && $SYSTEMCTL restart $HSVC"; REPAIRED="the tab's repair skipped at your word"
else
  RP="$(cd "$HK" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -B "${REPAIR_PY:-$HK/repair_call_durations_s698.py}" --apply 2>&1 | grep -v '^\[call_hook_capture\]')"; RC=$?
  printf '%s\n' "$RP" | sed 's/^/      /'
  if printf '%s\n' "$RP" | grep -q "VERIFIED"; then
    "$SYSTEMCTL" restart "$HSVC" || restore "restart $HSVC after the repair"
    h2=$(waitalive); [ "$h2" = alive ] || restore "call-hook $h2 after the second restart"
    say "[7/9] the Call_Durations tab repaired from the raw log and VERIFIED; call-hook restarted ($h2) so its row index is fresh"; REPAIRED="the tab repaired and verified"
  elif printf '%s\n' "$RP" | grep -q "nothing to repair"; then
    say "[7/9] the Call_Durations tab needed no repair"; REPAIRED="the tab needed no repair"
  elif printf '%s\n' "$RP" | grep -q "REPAIR GUARD"; then
    say "!! [7/9] the repair stopped at its 21-day guard (the region reaches further back than expected) -- nothing was written to the tab; the code stays. Tell Claude."; REPAIRED="the tab's repair stopped at its guard -- tell Claude"
  else
    say "!! [7/9] THE REPAIR DID NOT VERIFY (see above) -- the code stays (the builder folds the doubled rows anyway); its backup CSV is named above. Tell Claude."; REPAIRED="THE TAB'S REPAIR DID NOT VERIFY -- tell Claude"
    "$SYSTEMCTL" restart "$HSVC" || true; sleep 3
  fi
fi

CB="$("$CRONTAB" -l 2>/dev/null)" || CB=""
if [ -z "$CB" ]; then
  say "[8/9] no crontab could be read - the console cron line is left as it is. Tell Claude."
elif [ "$(printf '%s\n' "$CB" | grep -c -F "$NEWCRON")" = 1 ]; then
  say "[8/9] the console cron already runs 07:00-22:50"
elif [ "$(printf '%s\n' "$CB" | grep -c -F "$OLDCRON")" = 1 ]; then
  printf '%s\n' "$CB" > "$WA/crontab.bak_S698_$STAMP" && chmod 600 "$WA/crontab.bak_S698_$STAMP"
  NB="$(printf '%s\n' "$CB" | awk -v o="$OLDCRON" -v n="$NEWCRON" 'index($0,o)==1{ $0 = n substr($0, length(o)+1) } {print}')"
  if [ "$(printf '%s\n' "$NB" | grep -c .)" = "$(printf '%s\n' "$CB" | grep -c .)" ] && [ "$(printf '%s\n' "$NB" | grep -c -F "$NEWCRON")" = 1 ] && [ "$(printf '%s\n' "$NB" | grep -c -F "$OLDCRON")" = 0 ]; then
    printf '%s\n' "$NB" | "$CRONTAB" - && say "[8/9] the console cron now runs 07:00-22:50 (was 09-21); the crontab as it was: $WA/crontab.bak_S698_$STAMP" \
      || say "!! [8/9] the crontab could not be installed - left as it was. Tell Claude."
  else
    say "!! [8/9] the crontab edit did not come out as one changed line - left as it was. Tell Claude."
  fi
else
  say "!! [8/9] the console cron line was not found exactly once - left as it is. Tell Claude."
fi
if command -v flock >/dev/null 2>&1 && flock -n "$CRON_LOCK" true 2>/dev/null; then
  if (cd "$WA" && timeout 600 flock -n "$CRON_LOCK" "$VPY" "$WA/portal_console.py" --build --with-myop-reconcile --with-transcripts --days 60 >"$SCR/build.txt" 2>&1); then
    say "      console.db rebuilt once with the mended builder: $(grep -o 'BUILD complete.*' "$SCR/build.txt" | head -1)"
  else
    say "      the rebuild did not finish ($(tail -1 "$SCR/build.txt")) -- the cron's next run (every 10 min) makes it"
  fi
else
  say "      the console cron is building this moment; its run carries the fold"
fi

mkdir -p "$SCR/placed"
\cp -p "$PD/portal.py" "$PD/calls_console.py" "$WA/portal_console.py" "$HK/call_hook_capture.py" "$SCR/placed/"
POUT="$(walk "$SCR/placed")"; R="$(echo "$POUT" | tail -1)"
[ "${REHEARSE_RED_AT:-}" = 9 ] && R="rehearsal: a forced red at [9/9]"      # the rehearsal's hook only; unset on a real install
[ "$R" = "$GREEN" ] || { echo "$POUT" | grep -E '^  RED|^  MISSED' | head -8; restore "the walk on the placed files: $R"; }
say "[9/9] the walk on the placed files: $R"
PLACED=3
off_clear; release_lock
say "undo (one line): for n in $EDITED; do :; done; \\cp -p $(bak portal.py) $PD/portal.py; \\cp -p $(bak portal_console.py) $WA/portal_console.py; \\cp -p $(bak call_hook_capture.py) $HK/call_hook_capture.py; rm -f $NEWLIVE; $SYSTEMCTL restart $HSVC; $SYSTEMCTL restart $PSVC   (the tab's undo: the CSV named at [7/9]; the crontab: $WA/crontab.bak_S698_$STAMP)"
say ""
say "$KIT: DONE. The Call Console is at /portal/console in the new look; the old page is at /portal/console/old; the doubled call rows are mended in the receiver and the builder; $REPAIRED."
exit 0
