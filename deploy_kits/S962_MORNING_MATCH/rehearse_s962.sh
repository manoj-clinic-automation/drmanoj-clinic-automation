#!/bin/bash
# rehearse_s962.sh -- S962_MORNING_MATCH's installer on a MADE-UP root, every path. Nothing on a real box is touched.
#   bash rehearse_s962.sh <finance_code_dir (the FROM set)>        FROM=n UPTO=m runs a part (a background job dies with its call)
set -u
KSRC="$(cd "$(dirname "$0")" && pwd)"; CODE="$1"
T="$(mktemp -d /tmp/r962.XXXXXX)"; PASSN=0; FAILN=0
chk() { if eval "$2"; then PASSN=$((PASSN+1)); echo "PASS  $1"; else FAILN=$((FAILN+1)); echo "FAIL  $1"; fi; }
m5() { [ -f "$1" ] && md5sum "$1" | awk '{print $1}' || echo ABSENT; }
A_FROM=d5c95ea9868b5dba27cdd5bf0ea6d3db; B_FROM=41c55a991478a89057902f8cbbea46d2; C_FROM=3553a9653ab8682908d7a3f2f9c62833
pin() { awk -v f="to/$1" '$2==f{print $1}' "$KSRC/TO_PINS.md5"; }
A_TO=$(pin day_check.py); B_TO=$(pin slip_adjust.py); C_TO=$(pin slip_log.py)
setup() {
  rm -rf "$T/r"; mkdir -p "$T/r/finance" "$T/r/deploy" "$T/bin"
  cp "$CODE"/*.py "$T/r/finance/"
  python3 -c "import sqlite3,sys; sqlite3.connect(sys.argv[1]).execute('CREATE TABLE x(a)')" "$T/r/finance/finance.db"
  echo 0 > "$T/hcount"
  cat > "$T/bin/health" <<EOF
#!/bin/bash
n=\$(cat "$T/hcount"); echo \$((n+1)) > "$T/hcount"
if [ -n "\${H_BAD_AFTER:-}" ] && [ "\$n" -ge "\$H_BAD_AFTER" ]; then echo 502; else echo 200; fi
EOF
  printf '#!/bin/bash\necho "${DOOR_CODE:-302}"\n' > "$T/bin/door"
  printf '#!/bin/bash\necho "${LOGLINE:-}"\n' > "$T/bin/log"
  printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$T" > "$T/bin/systemctl"
  chmod +x "$T/bin/"*
  rm -f "$T/sysctl.log"
  rm -rf "$T/k"; cp -rp "$KSRC" "$T/k"
}
run() { (export PROBE_MIN_DAYS="${PROBE_MIN_DAYS:-0}" ROOT="$T/r" LOCK="$T/r/deploy/lock" APY="$(command -v python3)" VPY="$(command -v python3)" \
  HEALTH_CMD="$T/bin/health" DOOR_CMD="$T/bin/door" LOG_CMD="$T/bin/log" SYSTEMCTL="$T/bin/systemctl" NAP=0; bash "$T/k/install_S962_MORNING_MATCH.sh" "$@") > "$T/out.txt" 2>&1; echo $? > "$T/rc"; }
F="$T/r/finance"
state_from() { [ "$(m5 $F/day_check.py)" = $A_FROM ] && [ "$(m5 $F/slip_adjust.py)" = $B_FROM ] && [ "$(m5 $F/slip_log.py)" = $C_FROM ]; }
state_to() { [ "$(m5 $F/day_check.py)" = $A_TO ] && [ "$(m5 $F/slip_adjust.py)" = $B_TO ] && [ "$(m5 $F/slip_log.py)" = $C_TO ]; }
go() { [ "$1" -ge "${FROM:-1}" ] && [ "$1" -le "${UPTO:-99}" ]; }
if go 1; then
  setup; DRY=1 run; chk "R1 dry: walk green, control red, the probe ran; nothing changed" "grep -q 'DRY ok' $T/out.txt && grep -q 'control red' $T/out.txt && grep -q 'PROBE days 40' $T/out.txt && state_from"
  run; chk "R2 install: INSTALLED; three files at TO, backups 0600" "grep -q 'INSTALLED' $T/out.txt && state_to && [ \"\$(stat -c %a $F/day_check.py.bak_S962_d5c95ea9)\" = 600 ] && [ -f $F/slip_log.py.bak_S962_3553a965 ]"
  chk "R2b the service was restarted once" "[ \"\$(grep -c 'restart clinic-finance' $T/sysctl.log)\" = 1 ]"
  run; chk "R3 again: ALREADY, nothing changed" "grep -q 'ALREADY' $T/out.txt && state_to"
  run --undo; chk "R4 undo: everything back" "grep -q 'UNDONE' $T/out.txt && state_from"
  run --undo; chk "R5 undo twice: not installed" "grep -q 'not installed' $T/out.txt && state_from"
  run; chk "R6 re-install after undo" "grep -q 'INSTALLED' $T/out.txt && state_to"
fi
go 7 && { setup; FORCE_RED_AT=4 run; chk "R7 red at [4/5]: everything put back" "grep -q 'RED' $T/out.txt && state_from"; }
go 8 && { setup; FORCE_RED_AT=5 run; chk "R8 red at [5/5]: everything put back" "grep -q 'RED' $T/out.txt && state_from"; }
go 9 && { setup; FORCE_KILL_AT=4 run; chk "R9 killed at [4/5]: put back on the way out" "grep -q 'putting back' $T/out.txt && state_from"; }
go 10 && { setup; H_BAD_AFTER=1 run; chk "R10 healthz 502 after the restart: put back" "grep -q 'healthz 502' $T/out.txt && state_from"; }
go 11 && { setup; DOOR_CODE=404 run; chk "R11 the day check 404 (not mounted): put back" "grep -q 'not mounted' $T/out.txt && state_from"; }
go 12 && { setup; LOGLINE="Traceback (most recent call last)" run; chk "R12 a Traceback in the service log: put back" "grep -q 'service log' $T/out.txt && state_from"; }
go 13 && { setup; echo "# later" >> $F/slip_log.py; run; chk "R13 drift: slip_log changed -> STOP, nothing changed" "grep -q 'changed after this kit was built' $T/out.txt && [ \"\$(m5 $F/day_check.py)\" = $A_FROM ]"; }
go 14 && { setup; mkdir -p "$T/r/deploy/lock"; run; chk "R14 another build holds the lock -> nothing changed" "grep -q 'another build holds' $T/out.txt && state_from"; }
go 15 && { setup; echo "#" >> "$T/k/to/day_check.py"; run; chk "R15 a corrupt kit -> STOP at [1/5]" "grep -q '\[1/5\]' $T/out.txt && state_from"; }
go 16 && { setup; PROBE_CMD="echo PROBE days 40 checked 29 errors 2 cards 49 back 11 refunds 1 left_days 10" run; chk "R16 the live probe raised on a day -> STOP" "grep -q 'raised on a day' $T/out.txt && state_from"; }
go 17 && { setup; PROBE_MIN_DAYS=1 run; chk "R17 the live probe checked no day -> STOP (it proves nothing)" "grep -q 'proves nothing' $T/out.txt && state_from"; }
go 18 && { setup; PROBE_MIN_DAYS=1 PROBE_CMD="echo PROBE days 40 checked 29 errors 0 cards 49 back 11 refunds 1 left_days 10" DRY=1 run; chk "R18 the live probe green on 29 days -> on (dry)" "grep -q 'DRY ok' $T/out.txt && grep -q 'checked 29 errors 0' $T/out.txt"; }
go 19 && { setup; sed -i 's/def check_day(con, d):/def check_day(con, d, _x=0):/' $F/day_check.py; run; chk "R19 a live day_check that is not the FROM -> STOP before anything" "grep -q 'changed after this kit was built' $T/out.txt && [ ! -f $F/day_check.py.bak_S962_d5c95ea9 ]"; }
rm -rf "$T"
echo "REHEARSAL $PASSN pass, $FAILN fail"
[ "$FAILN" = 0 ]
