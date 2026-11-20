#!/bin/bash
# rehearse_s910.sh -- kit S910: the installer walked on a MADE-UP root (no live file, no real crontab, no patient data).
# Stubs: a crontab that reads/writes a file; a 'venv python' that answers the version question with the PC's versions and
# otherwise runs the real python3; a replay2 stub whose --run writes a report of 24 content hashes (equal to the 'S908' report,
# or different in scene D); a server_runner stub (--selftest / --dry-run). The real future_out_s910.py does the engine work.
# Scenes: A green install . B again (already) . C undo . D hashes differ -> put back, cron untouched . E wrong engine -> STOP .
#         F tampered kit refused . G selftest fails -> put back . H D twice: the live report never written, no false pass .
#         I a failing re-run never restores a stale backup . J undo with an unreadable crontab touches no file
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; R="$(mktemp -d /tmp/s910_reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
ENG_BOX="${ENG_BOX:?}"; OLD_BOX="${OLD_BOX:?}"   # the two S908-state files, given by path
n=0; f=0; ok() { n=$((n+1)); if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; f=$((f+1)); fi; }
mk() {  # a fresh made-up root
  rm -rf "$R/fut" "$R/wa"; mkdir -p "$R/fut/replay" "$R/fut/logs" "$R/fut/venv/bin" "$R/wa/followup-inbox" "$R/fut/intake"
  cp "$ENG_BOX" "$R/fut/processor.py"; cp "$OLD_BOX" "$R/fut/replay/processor.py.bak_S777_0e7c129f"
  echo seeded > "$R/fut/SEEDED_AT"; : > "$R/fut/OFF"
  for i in $(seq 1 24); do echo "#$i PASS (code x)  [box 11111111/100B inbox 22222222/100B content a$i$i$i$i$i$i$i$i | xlsx ok]"; done > "$R/fut/logs/REPLAY2_REPORT.txt"
  echo "RESULT: 24 pass, 0 order-only (identical rows in another order), 0 fail, 9 skipped of 33" >> "$R/fut/logs/REPLAY2_REPORT.txt"
  cat > "$R/fut/replay2_s897.py" <<'PY'
import os, sys  # stub: content_hash
if "--import-check" in sys.argv: print("import-check: 0 error(s) under " + os.environ.get("NPY_SELF","?")); sys.exit(0)
rep = sys.argv[sys.argv.index("--report")+1]; diff = os.environ.get("REH_DIFF","")
with open(rep,"w") as fh:
    for i in range(1,25):
        h = "a%d%d%d%d%d%d%d%d" % ((i,)*8)
        if diff and i == 9: h = "deadbeef"
        fh.write("#%d PASS (code x)  [box 11111111/100B inbox 22222222/100B content %s | xlsx ok]\n" % (i,h))
    fh.write("RESULT: 24 pass, 0 order-only (identical rows in another order), 0 fail, 9 skipped of 33\n")
print(open(rep).read())
PY
  cat > "$R/fut/server_runner.py" <<'PY'
import os, sys
if "--selftest" in sys.argv: print("selftest: %s failure(s)" % os.environ.get("REH_ST","0")); sys.exit(0)
if "--dry-run" in sys.argv:
    off = os.environ.get("FUT_OFF",""); root = os.environ.get("FUT_ROOT","")
    if off and os.path.exists(off): print("OFF (%s) -- nothing done" % off); sys.exit(0)
    assert os.path.exists(os.path.join(root, "processor.py")), "no processor.py in the copy"
    assert not os.path.exists(os.path.join(root, "venv")), "the copy carried the venv"
    print("DRY: intake 3 new, 0 already there; waiting -- nothing new to run"); sys.exit(0)
PY
  cat > "$R/fut/venv/bin/python3" <<EOF
#!/bin/bash
# stub venv python: the version question answered with the PC's versions; everything else the real python3
if [ "\${1:-}" = "-c" ] && echo "\$2" | grep -q importlib.metadata; then echo "3.11.9: numpy 2.2.6, pandas 2.3.3, openpyxl 3.1.5"; exit 0; fi
NPY_SELF="$R/fut/venv/bin/python3" exec python3 "\$@"
EOF
  chmod +x "$R/fut/venv/bin/python3"
  { for i in $(seq 1 22); do echo "$i 1 * * * /bin/true # filler $i"; done
    echo "*/5 * * * * [ -e /root/finance/_off/ALL_OFF ] || [ -e $R/fut/OFF ] || TZ=Asia/Kolkata flock -n /tmp/x.lock /root/wa/venv/bin/python3 -B $R/fut/server_runner.py >> $R/fut/logs/runner.log 2>&1 # S895_TRACKER runner"
    echo "0 8 * * * [ -e /root/finance/_off/ALL_OFF ] || [ -e $R/fut/OFF ] || (cd $R/fut && TZ=Asia/Kolkata /root/wa/venv/bin/python3 -B $R/fut/push_patient_mirror.py --push >> $R/fut/logs/mirror.log 2>&1) # S895_TRACKER mirror"
  } > "$R/crontab.txt"
  cat > "$R/crontab" <<EOF
#!/bin/bash
if [ "\${1:-}" = "-l" ]; then cat "$R/crontab.txt"; else cat "\$1" > "$R/crontab.txt"; fi
EOF
  chmod +x "$R/crontab"; printf '2026-11-20 21:05:00 pc followup_logs_x.csv 1234\n' > "$R/wa/followup-inbox/.uploads.log"
}
run() { FUT="$R/fut" WA="$R/wa" CRONTAB="$R/crontab" NPY="$R/fut/venv/bin/python3" PUSH_UNIT=nonesuch.service bash "$KDIR/install_S910_TRACKER_RUNNER_VENV311.sh" "$@" 2>&1; }
m8() { md5sum "$1" | cut -c1-8; }
croncount() { grep -F "# S895_TRACKER" "$R/crontab.txt" | grep -c "$1"; }

echo "A  green install"; mk; out="$(run)"; echo "$out" | sed 's/^/     /' | tail -12
ok "A says DONE"                 'echo "$out" | grep -q "S910_TRACKER_RUNNER_VENV311: DONE"'
ok "A engine = the PC bytes 6929fc15"   '[ "$(m8 "$R/fut/processor.py")" = 6929fc15 ]'
ok "A replay copy c1f7b50f"      '[ "$(m8 "$R/fut/replay/processor.py.bak_S777_0e7c129f")" = c1f7b50f ]'
ok "A backups beside"            '[ -f "$R/fut/processor.py.bak_S910_b5b01d87" ] && [ -f "$R/fut/replay/processor.py.bak_S777_0e7c129f.bak_S910_8d56e084" ]'
ok "A cron lines on the new venv (2)" '[ "$(croncount $R/fut/venv/bin/python3)" = 2 ] && [ "$(croncount /root/wa/venv)" = 0 ]'
ok "A crontab still 24 lines"    '[ "$(grep -c . "$R/crontab.txt")" = 24 ]'
ok "A OFF still present"         '[ -e "$R/fut/OFF" ]'
ok "A 24 of 24 hashes equal"     'echo "$out" | grep -q "24 of 24 content hashes EQUAL"'
ok "A dry pass on the copy ran"  'echo "$out" | grep -q "DRY: intake 3 new"'
ok "A S908 report kept"          '[ -f "$R/fut/logs/REPLAY2_REPORT_before_S910.txt" ]'
ok "A watch: 1 pc upload"        'echo "$out" | grep -q "uploads today by origin: 1 pc, 0 server"'
echo "B  install again"; out="$(run)"; ok "B already installed, nothing done" 'echo "$out" | grep -q "already installed"'
echo "C  undo"; out="$(run --undo)"; echo "$out" | tail -2 | sed 's/^/     /'
ok "C engine back b5b01d87"      '[ "$(m8 "$R/fut/processor.py")" = b5b01d87 ]'
ok "C replay copy back 8d56e084" '[ "$(m8 "$R/fut/replay/processor.py.bak_S777_0e7c129f")" = 8d56e084 ]'
ok "C cron back on the old venv" '[ "$(croncount /root/wa/venv)" = 2 ]'
ok "C no .bak_S910 left"         '[ -z "$(ls "$R/fut"/*.bak_S910_* "$R/fut/replay"/*.bak_S910_* 2>/dev/null)" ]'
echo "D  hashes differ -> put back"; mk; out="$(REH_DIFF=1 run)"; echo "$out" | grep -E '^!!|put back' | sed 's/^/     /'
ok "D stops at [5/6]"            'echo "$out" | grep -q "\[5/6\] the content hashes differ"'
ok "D engine put back"           '[ "$(m8 "$R/fut/processor.py")" = b5b01d87 ] && [ "$(m8 "$R/fut/replay/processor.py.bak_S777_0e7c129f")" = 8d56e084 ]'
ok "D cron untouched"            '[ "$(croncount /root/wa/venv)" = 2 ]'
ok "D nothing says DONE"         '! echo "$out" | grep -q ": DONE"'
echo "E  wrong engine -> STOP"; mk; echo "# not the engine" >> "$R/fut/processor.py"; h="$(m8 "$R/fut/processor.py")"; out="$(run)"
ok "E stops at [2/6]"            'echo "$out" | grep -q "\[2/6\].*neither S908"'
ok "E file untouched"            '[ "$(m8 "$R/fut/processor.py")" = "$h" ] && [ "$(croncount /root/wa/venv)" = 2 ]'
echo "F  tampered kit"; mk; cp -r "$KDIR" "$R/kit2"; echo "# x" >> "$R/kit2/future_out_s910.py"; out="$(FUT="$R/fut" WA="$R/wa" CRONTAB="$R/crontab" NPY="$R/fut/venv/bin/python3" bash "$R/kit2/install_S910_TRACKER_RUNNER_VENV311.sh" 2>&1)"
ok "F refused by SUMS"           'echo "$out" | grep -q "SUMS.md5 gate failed"'
echo "G  selftest fails -> put back"; mk; out="$(REH_ST=1 run)"
ok "G stops at [4/6]"            'echo "$out" | grep -q "\[4/6\] server_runner --selftest"'
ok "G engine put back"           '[ "$(m8 "$R/fut/processor.py")" = b5b01d87 ]'
echo "H  hashes differ, then run again (the live report must still be S908's; no false pass)"; mk; h0="$(m8 "$R/fut/logs/REPLAY2_REPORT.txt")"; out1="$(REH_DIFF=1 run)"; out2="$(REH_DIFF=1 run)"
ok "H live report untouched by both failing runs" '[ "$(m8 "$R/fut/logs/REPLAY2_REPORT.txt")" = "$h0" ] && [ ! -f "$R/fut/logs/REPLAY2_REPORT_before_S910.txt" ]'
ok "H the second run fails too (no false pass)" 'echo "$out2" | grep -q "\[5/6\] the content hashes differ" && ! echo "$out2" | grep -q ": DONE"'
ok "H engine still b5b01d87, cron old"        '[ "$(m8 "$R/fut/processor.py")" = b5b01d87 ] && [ "$(croncount /root/wa/venv)" = 2 ]'
echo "I  after a green install, cron put back by hand, a failing re-run must not use the stale backup"; mk; out="$(run)"; sed -i "s#$R/fut/venv/bin/python3#/root/wa/venv/bin/python3#g" "$R/crontab.txt"; out="$(REH_ST=1 run)"
ok "I stops at [4/6]"                         'echo "$out" | grep -q "\[4/6\] server_runner --selftest"'
ok "I engine stays the PC bytes (stale .bak_S910 not used)" '[ "$(m8 "$R/fut/processor.py")" = 6929fc15 ] && [ -f "$R/fut/processor.py.bak_S910_b5b01d87" ]'
ok "I cron untouched"                         '[ "$(croncount /root/wa/venv)" = 2 ]'
echo "J  undo with an unreadable crontab touches no file"; mk; out="$(run)"; : > "$R/crontab.txt"; out="$(run --undo)"
ok "J undo stops, engine still the PC bytes"  'echo "$out" | grep -q "could not be" && [ "$(m8 "$R/fut/processor.py")" = 6929fc15 ]'
echo "REHEARSAL: $((n-f)) of $n ok, $f failed"; [ "$f" = 0 ]
