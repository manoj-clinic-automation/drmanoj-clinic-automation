#!/bin/bash
# rehearse_s972.sh -- S972_EVENING_WIDENED's installer on a MADE-UP root, every path. Nothing on a real box is touched.
#   bash rehearse_s972.sh <finance_code_dir (the FROM set)> <callback_clock.py (live)>
set -u
KSRC="$(cd "$(dirname "$0")" && pwd)"; CODE="$1"; CC="$2"
T="$(mktemp -d /tmp/r972.XXXXXX)"; PASSN=0; FAILN=0
chk() { if eval "$2"; then PASSN=$((PASSN+1)); echo "PASS  $1"; else FAILN=$((FAILN+1)); echo "FAIL  $1"; tail -5 "$T/out.txt" | sed 's/^/        /'; fi; }
m5() { [ -f "$1" ] && md5sum "$1" | awk '{print $1}' || echo ABSENT; }
A_TO=$(awk '$2=="to/evening_check.py"{print $1}' "$KSRC/TO_PINS.md5")
setup() {
  rm -rf "$T/r"; mkdir -p "$T/r/finance" "$T/r/portal" "$T/r/deploy" "$T/bin"
  cp "$CODE"/*.py "$T/r/finance/"; cp "$CC" "$T/r/portal/callback_clock.py"
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
  rm -f "$T/sysctl.log"; chmod +x "$T/bin/"*
  rm -rf "$T/k"; cp -rp "$KSRC" "$T/k"
}
run() { (export PROBE_MIN_DAYS="${PROBE_MIN_DAYS:-0}" PROBE_MIN_PAIRS="${PROBE_MIN_PAIRS:-0}" ROOT="$T/r" LOCK="$T/r/deploy/lock" APY="$(command -v python3)" VPY="$(command -v python3)" \
  HEALTH_CMD="$T/bin/health" DOOR_CMD="$T/bin/door" LOG_CMD="$T/bin/log" SYSTEMCTL="$T/bin/systemctl" NAP=0; bash "$T/k/install_S972_EVENING_WIDENED.sh" "$@") > "$T/out.txt" 2>&1; echo $? > "$T/rc"; }
F="$T/r/finance"
state_from() { [ "$(m5 $F/evening_check.py | cut -c1-8)" = b3c5bebb ] && [ ! -d "$T/r/deploy/lock" ]; }
state_to() { [ "$(m5 $F/evening_check.py)" = "$A_TO" ] && [ ! -d "$T/r/deploy/lock" ]; }
part() { [ -z "${PART:-}" ] || [ "$PART" = "$1" ]; }   # PART=1 or 2 runs half (each half under 3 minutes); none runs all
if part 1; then
setup; DRY=1 run; chk "R1 dry: walk green, control red at S1, S960's walk green, the probe ran; nothing changed" "grep -q 'DRY ok' $T/out.txt && grep -q 'control red at S1' $T/out.txt && grep -q 'PROBE972 days 0' $T/out.txt && state_from"
run; chk "R2 install: INSTALLED; the file at TO, the backup 0600, one restart" "grep -q 'INSTALLED' $T/out.txt && state_to && [ \"\$(stat -c %a $F/evening_check.py.bak_S972_b3c5bebb)\" = 600 ] && [ \"\$(grep -c 'restart clinic-finance' $T/sysctl.log)\" = 1 ]"
run; chk "R3 again: ALREADY, nothing changed" "grep -q 'ALREADY' $T/out.txt && state_to"
run --undo; chk "R4 undo: the file back" "grep -q 'UNDONE' $T/out.txt && state_from"
run --undo; chk "R5 undo twice: not installed" "grep -q 'not installed' $T/out.txt && state_from"
run; chk "R6 re-install after undo" "grep -q 'INSTALLED' $T/out.txt && state_to"
echo "# later" >> $F/evening_check.py; run --undo; chk "R7 undo over a later change: refused, the file left" "grep -q 'not S972' $T/out.txt && grep -q '# later' $F/evening_check.py"
fi
if part 2; then
setup; FORCE_RED_AT=4 run; chk "R8 red at [4/5]: put back" "grep -q 'RED' $T/out.txt && state_from"
setup; FORCE_RED_AT=5 run; chk "R9 red at [5/5]: put back" "grep -q 'RED' $T/out.txt && state_from"
setup; FORCE_KILL_AT=4 run; chk "R10 killed at [4/5]: put back on the way out" "grep -q 'putting back' $T/out.txt && state_from"
setup; H_BAD_AFTER=1 run; chk "R11 healthz 502 after the restart: put back" "grep -q 'healthz 502' $T/out.txt && state_from"
setup; DOOR_CODE=404 run; chk "R12 a door 404 (not mounted): put back" "grep -q 'not mounted' $T/out.txt && state_from"
setup; LOGLINE="Traceback (most recent call last)" run; chk "R13 a Traceback in the service log: put back" "grep -q 'service log' $T/out.txt && state_from"
setup; echo "# later" >> $F/evening_check.py; run; chk "R14 drift: evening_check changed -> STOP, nothing changed" "grep -q 'changed after this kit was built' $T/out.txt && grep -q '# later' $F/evening_check.py"
setup; mkdir -p "$T/r/deploy/lock"; run; chk "R15 another build holds the lock -> nothing changed" "grep -q 'another build holds' $T/out.txt && [ \"\$(m5 $F/evening_check.py | cut -c1-8)\" = b3c5bebb ]"
setup; echo "#" >> "$T/k/to/evening_check.py"; run; chk "R16 a corrupt kit -> STOP at [1/5]" "grep -q '\[1/5\]' $T/out.txt && state_from"
setup; PROBE_CMD="echo PROBE972 days 30 unread 0 errors 1 lines 10 chhoot 2 kam 3 tdoc 1 tslip 1 more 3 head 0 reader_same 90 reader_diff 2 maxday 2" run
chk "R17 the live probe met an error -> STOP" "grep -q 'met an error' $T/out.txt && state_from"
setup; PROBE_CMD="echo PROBE972 days 10 unread 0 errors 0 lines 31 chhoot 2 kam 20 tdoc 1 tslip 1 more 7 head 0 reader_same 90 reader_diff 2 maxday 5" run
chk "R18 the live probe: more than 3 lines a day -> STOP (too noisy)" "grep -q 'too noisy' $T/out.txt && state_from"
setup; PROBE_CMD="echo PROBE972 days 10 unread 0 errors 0 lines 8 chhoot 2 kam 3 tdoc 1 tslip 1 more 1 head 0 reader_same 60 reader_diff 21 maxday 2" run
chk "R19 the live probe: the reader differs on over a quarter -> STOP" "grep -q 'more than a quarter' $T/out.txt && state_from"
setup; PROBE_CMD="echo PROBE972 days 30 unread 0 errors 0 lines 20 chhoot 4 kam 6 tdoc 2 tslip 1 more 7 head 0 reader_same 140 reader_diff 3 maxday 12" run
chk "R20a the live probe: one day with 12 lines -> STOP (too noisy)" "grep -q 'too noisy' $T/out.txt && state_from"
setup; PROBE_MIN_PAIRS=5 PROBE_CMD="echo PROBE972 days 30 unread 0 errors 0 lines 2 chhoot 0 kam 2 tdoc 0 tslip 0 more 0 head 0 reader_same 0 reader_diff 0 maxday 1" run
chk "R20b the live probe: no money pairs to compare -> STOP (reader unproven)" "grep -q 'unproven' $T/out.txt && state_from"
setup; PROBE_MIN_DAYS=1 run; chk "R20 the live probe read no day -> STOP (it proves nothing)" "grep -q 'proves nothing' $T/out.txt && state_from"
setup; PROBE_MIN_DAYS=1 PROBE_CMD="echo PROBE972 days 30 unread 2 errors 0 lines 20 chhoot 4 kam 6 tdoc 2 tslip 1 more 7 head 0 reader_same 140 reader_diff 3 maxday 4" DRY=1 run
chk "R21 the live probe within bounds -> on (dry)" "grep -q 'DRY ok' $T/out.txt && grep -q 'days 30 unread 2' $T/out.txt"
fi
rm -rf "$T"
echo "REHEARSAL $PASSN pass, $FAILN fail"
[ "$FAILN" = 0 ]
