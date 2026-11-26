#!/bin/bash
# rehearse_s960.sh -- S960_EVENING_CHECK's installer on a MADE-UP root, every path. Nothing on a real box is touched.
#   bash rehearse_s960.sh <finance_code_dir (the FROM set)> <callback_clock.py (live)>
set -u
KSRC="$(cd "$(dirname "$0")" && pwd)"; CODE="$1"; CC="$2"
T="$(mktemp -d /tmp/r960.XXXXXX)"; PASSN=0; FAILN=0
chk() { if eval "$2"; then PASSN=$((PASSN+1)); echo "PASS  $1"; else FAILN=$((FAILN+1)); echo "FAIL  $1"; fi; }
m5() { [ -f "$1" ] && md5sum "$1" | awk '{print $1}' || echo ABSENT; }
A_FROM=a6cbdb8ba255c5f640aa402a653e401a; B_FROM=1053255360f821e0007759edd9cf685b
A_TO=$(awk '$2=="to/docterz_pickup.py"{print $1}' "$KSRC/TO_PINS.md5"); B_TO=$(awk '$2=="to/parchi_desk.py"{print $1}' "$KSRC/TO_PINS.md5"); C_TO=$(awk '$2=="to/evening_check.py"{print $1}' "$KSRC/TO_PINS.md5")
setup() {
  rm -rf "$T/r"; mkdir -p "$T/r/finance" "$T/r/portal" "$T/r/deploy" "$T/bin"
  cp "$CODE"/*.py "$T/r/finance/"; cp "$CC" "$T/r/portal/callback_clock.py"
  python3 -c "import sqlite3,sys; sqlite3.connect(sys.argv[1]).execute('CREATE TABLE x(a)')" "$T/r/finance/finance.db"
  printf '*/15 * * * * echo pickup # S443_DOCTERZ_PICKUP the reception PC exports\n0 1 * * * echo other\n' > "$T/cron"
  cat > "$T/bin/crontab" <<EOF
#!/bin/bash
if [ "\$1" = "-l" ]; then n=\$(cat "$T/ccount" 2>/dev/null || echo 0); n=\$((n+1)); echo \$n > "$T/ccount"
  [ -n "\${CRON_SHIFT_AT:-}" ] && [ "\$n" = "\$CRON_SHIFT_AT" ] && echo "5 5 * * * echo someone-else" >> "$T/cron"; cat "$T/cron"; else cp "\$1" "$T/cron"; fi
EOF
  echo 0 > "$T/hcount"; echo 0 > "$T/ccount"
  cat > "$T/bin/health" <<EOF
#!/bin/bash
n=\$(cat "$T/hcount"); echo \$((n+1)) > "$T/hcount"
if [ -n "\${H_BAD_AFTER:-}" ] && [ "\$n" -ge "\$H_BAD_AFTER" ]; then echo 502; else echo 200; fi
EOF
  printf '#!/bin/bash\necho "${DOOR_CODE:-302}"\n' > "$T/bin/door"
  printf '#!/bin/bash\necho "${LOGLINE:-}"\n' > "$T/bin/log"
  printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$T" > "$T/bin/systemctl"
  chmod +x "$T/bin/"*
  rm -rf "$T/k"; cp -rp "$KSRC" "$T/k"
}
run() { (export PROBE_MIN_DAYS="${PROBE_MIN_DAYS:-0}" ROOT="$T/r" LOCK="$T/r/deploy/lock" APY="$(command -v python3)" VPY="$(command -v python3)" CRONTAB="$T/bin/crontab" \
  HEALTH_CMD="$T/bin/health" DOOR_CMD="$T/bin/door" LOG_CMD="$T/bin/log" SYSTEMCTL="$T/bin/systemctl" NAP=0; bash "$T/k/install_S960_EVENING_CHECK.sh" "$@") > "$T/out.txt" 2>&1; echo $? > "$T/rc"; }
F="$T/r/finance"
state_from() { [ "$(m5 $F/docterz_pickup.py)" = $A_FROM ] && [ "$(m5 $F/parchi_desk.py)" = $B_FROM ] && [ ! -f $F/evening_check.py ] && ! grep -q S960_EVENING "$T/cron"; }
state_to() { [ "$(m5 $F/docterz_pickup.py)" = $A_TO ] && [ "$(m5 $F/parchi_desk.py)" = $B_TO ] && [ "$(m5 $F/evening_check.py)" = $C_TO ] && [ "$(grep -c S960_EVENING "$T/cron")" = 1 ] && [ "$(grep -c . "$T/cron")" = 3 ]; }
go() { [ "$1" -ge "${FROM:-1}" ] && [ "$1" -le "${UPTO:-99}" ]; }
if go 1; then
  setup; DRY=1 run; chk "R1 dry: walk green, control red, the probe ran; nothing changed" "grep -q 'DRY ok' $T/out.txt && grep -q 'control red' $T/out.txt && grep -q 'PROBE days 0' $T/out.txt && state_from"
  run; chk "R2 install: INSTALLED; three files at TO, one cron line, backups 0600" "grep -q 'INSTALLED' $T/out.txt && state_to && [ \"\$(stat -c %a $F/docterz_pickup.py.bak_S960_a6cbdb8b)\" = 600 ] && [ -f $F/crontab.bak_S960 ]"
  chk "R2b the service was restarted once" "[ \"\$(grep -c 'restart clinic-finance' $T/sysctl.log)\" = 1 ]"
  run; chk "R3 again: ALREADY, nothing changed" "grep -q 'ALREADY' $T/out.txt && state_to"
  run --undo; chk "R4 undo: everything back, the cron line gone" "grep -q 'UNDONE' $T/out.txt && state_from"
  run --undo; chk "R5 undo twice: not installed" "grep -q 'not installed' $T/out.txt && state_from"
  run; chk "R6 re-install after undo" "grep -q 'INSTALLED' $T/out.txt && state_to"
fi
go 7 && { setup; FORCE_RED_AT=4 run; chk "R7 red at [4/5]: everything put back" "grep -q 'RED' $T/out.txt && state_from"; }
go 8 && { setup; FORCE_RED_AT=5 run; chk "R8 red at [5/5]: everything put back" "grep -q 'RED' $T/out.txt && state_from"; }
go 9 && { setup; FORCE_KILL_AT=4 run; chk "R9 killed at [4/5]: put back on the way out" "grep -q 'putting back' $T/out.txt && state_from"; }
go 10 && { setup; H_BAD_AFTER=1 run; chk "R10 healthz 502 after the restart: put back" "grep -q 'healthz 502' $T/out.txt && state_from"; }
go 11 && { setup; DOOR_CODE=404 run; chk "R11 the new door 404 (not mounted): put back" "grep -q 'not mounted' $T/out.txt && state_from"; }
go 12 && { setup; LOGLINE="Traceback (most recent call last)" run; chk "R12 a Traceback in the service log: put back" "grep -q 'service log' $T/out.txt && state_from"; }
go 13 && { setup; echo "# later" >> $F/docterz_pickup.py; run; chk "R13 drift: docterz_pickup changed -> STOP, nothing changed" "grep -q 'changed after this kit was built' $T/out.txt && ! grep -q S960 $T/cron && [ ! -f $F/evening_check.py ]"; }
go 14 && { setup; echo x > $F/evening_check.py; run; chk "R14 an evening_check.py already there -> STOP" "grep -q 'already exists' $T/out.txt && ! grep -q S960 $T/cron"; }
go 15 && { setup; mkdir -p "$T/r/deploy/lock"; run; chk "R15 another build holds the lock -> nothing changed" "grep -q 'another build holds' $T/out.txt && state_from"; }
go 16 && { setup; echo "#" >> "$T/k/to/evening_check.py"; run; chk "R16 a corrupt kit -> STOP at [1/5]" "grep -q '\[1/5\]' $T/out.txt && state_from"; }
go 17 && { setup; echo "* * * * * x # S960_EVENING_PICKUP" >> "$T/cron"; run; chk "R17 an S960 cron line already there -> STOP" "grep -q 'already holds an S960 line' $T/out.txt"; }
go 18 && { setup; sed -i '/S443_DOCTERZ_PICKUP/d' "$T/cron"; run; chk "R18 no S443 pickup line -> STOP" "grep -q 'no S443' $T/out.txt && state_from"; }
go 19 && { setup; CRON_SHIFT_AT=3 run; chk "R19 the crontab changed while the kit checked: put back, the other change kept, no S960 line" "grep -q 'crontab changed' $T/out.txt && grep -q someone-else $T/cron && ! grep -q S960 $T/cron && [ ! -f $F/evening_check.py ]"; }
go 20 && { setup; PROBE_CMD="echo PROBE days 6 same 3 mine_only 2 his_only 0 unread 0" run; chk "R20 the live probe: the check names slips his list does not -> STOP" "grep -q 'mine_only' $T/out.txt && grep -q 'his own list does not' $T/out.txt && state_from"; }
go 21 && { setup; PROBE_MIN_DAYS=1 run; chk "R21 the live probe read no day -> STOP (it proves nothing)" "grep -q 'proves nothing' $T/out.txt && state_from"; }
go 22 && { setup; PROBE_MIN_DAYS=1 PROBE_CMD="echo PROBE days 6 same 9 mine_only 0 his_only 1 unread 0" DRY=1 run; chk "R22 the live probe agrees on six days -> on (dry)" "grep -q 'DRY ok' $T/out.txt && grep -q 'days 6 same 9' $T/out.txt"; }
rm -rf "$T"
echo "REHEARSAL $PASSN pass, $FAILN fail"
[ "$FAILN" = 0 ]
