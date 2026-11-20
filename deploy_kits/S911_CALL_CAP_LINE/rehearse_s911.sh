#!/bin/bash
# rehearse_s911.sh -- kit S911 walked on a MADE-UP root: stub systemctl, stub health (HEALTH_CMD), stub replay2 (run #7's content
# hash from the env), the VM's python3 as both venvs; the real call_cap_s911.py and the kit's owner_console.py. No live file.
# Scenes: A green install . B again (already) . C undo . D run #7's hash differs -> engine back, console untouched, no restart .
#         E forced red at [4/5] -> both back, restarted . F healthz not 200 before -> nothing . G tampered kit . H lock held -> nothing
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; R="$(mktemp -d /tmp/s911_reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
ENGINE="${ENGINE:?the PC engine processor.py}"; OCFROM="${OCFROM:?owner_console.py 500534f7}"
n=0; f=0; ok() { n=$((n+1)); if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; f=$((f+1)); fi; }
m8() { md5sum "$1" | cut -c1-8; }
mk() {
  rm -rf "$R/root"; mkdir -p "$R/root/finance" "$R/root/followup_tracker/logs" "$R/root/wa/followup-inbox" "$R/root/deploy"
  cp "$ENGINE" "$R/root/followup_tracker/processor.py"; cp "$OCFROM" "$R/root/finance/owner_console.py"; : > "$R/root/followup_tracker/OFF"
  echo "#7 PASS (code x)  [box 1/1B inbox 2/2B content aaaa1111bb | xlsx ok]" > "$R/root/followup_tracker/logs/REPLAY2_REPORT.txt"
  cat > "$R/root/followup_tracker/replay2_s897.py" <<'PY'
import os, sys
if "--import-check" in sys.argv: print("import-check: 0 error(s) under " + os.environ.get("VPY_SELF", "?")); sys.exit(0)
rep = sys.argv[sys.argv.index("--report")+1]
open(rep, "w").write("#7 PASS (code x)  [box 1/1B inbox 2/2B content %s | xlsx ok]\nRESULT: 1 pass\n" % os.environ.get("REH_H7", "aaaa1111bb"))
print("CALL CAP: kept 3 of 4 due for a call -- 1 wait for tomorrow")
PY
  cat > "$R/systemctl" <<EOF
#!/bin/bash
echo "\$*" >> "$R/systemctl.log"; exit 0
EOF
  cat > "$R/health" <<EOF
#!/bin/bash
[ -f "$R/health_code" ] && cat "$R/health_code" || echo 200
EOF
  chmod +x "$R/systemctl" "$R/health"; : > "$R/systemctl.log"; rm -f "$R/health_code"
}
run() { ROOT="$R/root" LOCK="$R/root/deploy/.lock" SYSTEMCTL="$R/systemctl" HEALTH_CMD="$R/health" NAP=0 VPY="$(command -v python3)" APY="$(command -v python3)" VPY_SELF="$(command -v python3)" bash "$KDIR/install_S911_CALL_CAP_LINE.sh" "$@" 2>&1; }
ENG="$R/root/followup_tracker/processor.py"; OC="$R/root/finance/owner_console.py"
echo "A  green install"; mk; out="$(run)"; echo "$out" | sed 's/^/     /' | tail -6
ok "A DONE"                         'echo "$out" | grep -q "S911_CALL_CAP_LINE: DONE"'
ok "A engine 64824680, bak beside"  '[ "$(m8 "$ENG")" = 64824680 ] && [ "$(m8 "$ENG.bak_S911_6929fc15")" = 6929fc15 ]'
ok "A console at its TO, bak beside" '[ "$(m8 "$OC")" = "$(awk "/owner_console/{print substr(\$1,1,8)}" "$KDIR/TO_PINS.md5")" ] && [ "$(m8 "$OC.bak_S911_500534f7")" = 500534f7 ]'
ok "A restarted once"               '[ "$(grep -c "restart" "$R/systemctl.log")" = 1 ]'
ok "A OFF still present, lock released" '[ -e "$R/root/followup_tracker/OFF" ] && [ ! -d "$R/root/deploy/.lock" ]'
echo "B  again"; out="$(run)"; ok "B already installed" 'echo "$out" | grep -q "already installed"'
echo "C  undo"; out="$(run --undo)"; ok "C both back, restarted" '[ "$(m8 "$ENG")" = 6929fc15 ] && [ "$(m8 "$OC")" = 500534f7 ] && echo "$out" | grep -q UNDONE && [ "$(grep -c restart "$R/systemctl.log")" = 2 ]'
echo "D  run #7 hash differs"; mk; out="$(REH_H7=deadbeef00 run)"; echo "$out" | grep "RED\|restored" | sed 's/^/     /'
ok "D engine back, console untouched, no restart" '[ "$(m8 "$ENG")" = 6929fc15 ] && [ "$(m8 "$OC")" = 500534f7 ] && [ ! -f "$ENG.bak_S911_6929fc15" ] && [ ! -s "$R/systemctl.log" ] && ! echo "$out" | grep -q ": DONE"'
ok "D lock released"                '[ ! -d "$R/root/deploy/.lock" ]'
echo "E  forced red at [4/5]"; mk; out="$(REHEARSE_RED_AT=4 run)"
ok "E both back, restarted, no DONE" '[ "$(m8 "$ENG")" = 6929fc15 ] && [ "$(m8 "$OC")" = 500534f7 ] && [ "$(grep -c restart "$R/systemctl.log")" = 2 ] && ! echo "$out" | grep -q ": DONE"'
echo "F  healthz 500 before"; mk; echo 500 > "$R/health_code"; out="$(run)"
ok "F nothing installed"            'echo "$out" | grep -q "\[2/5\] finance healthz 500" && [ "$(m8 "$ENG")" = 6929fc15 ]'
echo "G  tampered kit"; mk; cp -r "$KDIR" "$R/kit2"; echo "# x" >> "$R/kit2/call_cap_s911.py"; out="$(ROOT="$R/root" LOCK="$R/root/deploy/.lock" SYSTEMCTL="$R/systemctl" HEALTH_CMD="$R/health" bash "$R/kit2/install_S911_CALL_CAP_LINE.sh" 2>&1)"
ok "G refused by SUMS"              'echo "$out" | grep -q "SUMS.md5 gate failed"'
echo "I  undo after a later change refuses"; mk; out="$(run)"; echo "# later" >> "$ENG"; out="$(run --undo)"
ok "I undo refuses, nothing moved" 'echo "$out" | grep -q "not undoing" && [ -f "$ENG.bak_S911_6929fc15" ] && [ "$(m8 "$OC")" != 500534f7 ]'
echo "H  lock held"; mk; mkdir -p "$R/root/deploy/.lock"; out="$(run)"
ok "H stops on the lock, nothing changed" 'echo "$out" | grep -q "another build holds" && [ "$(m8 "$ENG")" = 6929fc15 ]'
echo "REHEARSAL: $((n-f)) of $n ok, $f failed"; [ "$f" = 0 ]
