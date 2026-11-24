#!/bin/bash
# rehearse_s945.sh -- kit S945 on a MADE-UP root (ROOT=<tmp>): the FROM code_bundle.py live, a made-up recordings-archive with the
# three leftovers (made-up numbers built at run time), a made-up followup_tracker with data folders, a made-up finance_app.py.
# The real `code_bundle.py build` runs against that root (local tar only). The VM's python3 as the venv. No live file, no network.
# Scenes: A dry . B install . C again . D undo . E forced red at [4/5] -> everything back . F tampered kit . G wrong live pin . H lock held
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; R="$(mktemp -d /tmp/s945_reh.XXXXXX)"; trap 'rm -rf "$R"' EXIT
CBFROM="${CBFROM:?code_bundle.py aa8f985f}"
n=0; f=0; ok() { n=$((n+1)); if eval "$2"; then echo "  ok   $1"; else echo "  FAIL $1"; f=$((f+1)); fi; }
m8() { md5sum "$1" | cut -c1-8; }
TO8="$(awk '/code_bundle/{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
mk() { rm -rf "$R/root"; mkdir -p "$R/root/root/state_backup" "$R/root/root/wa/recordings-archive" "$R/root/root/finance" "$R/root/root/followup_tracker/data" "$R/root/root/followup_tracker/venv/bin" "$R/root/root/deploy"
  cp "$CBFROM" "$R/root/root/state_backup/code_bundle.py"; echo "app = 1" > "$R/root/root/finance/finance_app.py"
  echo "r = 1" > "$R/root/root/followup_tracker/server_runner.py"; echo "d = 1" > "$R/root/root/followup_tracker/data/helper.py"; echo "v" > "$R/root/root/followup_tracker/venv/bin/python3"
  python3 - "$R/root/root/wa/recordings-archive" <<'PY'
import sys, os
ra = sys.argv[1]; G = 10 ** 9
open(os.path.join(ra, "make_force_keys.py"), "w").write('TRIPLES = [\n    ("%d", "2026-07-01", "10:00"),\n]\n' % (9 * G + 1234))
open(os.path.join(ra, "force_keys.txt"), "w").write("%d_x\n" % (9 * G + 1234))
open(os.path.join(ra, "call_verdict_BACKUP_S123_pre_join_redesign.py"), "w").write("y = 2\n")
open(os.path.join(ra, "call_verdict.py"), "w").write("z = 3\n")
PY
}
run() { ROOT="$R/root" LOCK="$R/root/root/deploy/.lock" APY="$(command -v python3)" bash "$KDIR/install_S945_PHI_OUT_TRACKER_BUNDLED.sh" "$@" 2>&1; }
CB="$R/root/root/state_backup/code_bundle.py"; RA="$R/root/root/wa/recordings-archive"; RET="$R/root/root/_retired/S510"; TAR="$R/root/root/state_backup/code_nightly.tar.gz"
echo "A  dry"; mk; out="$(DRY=1 run)"; echo "$out" | tail -2 | sed 's/^/     /'
ok "A dry: nothing changed" 'echo "$out" | grep -q "nothing live changed" && [ "$(m8 "$CB")" = aa8f985f ] && [ -f "$RA/make_force_keys.py" ] && [ ! -d "$RET" ]'
echo "B  install"; out="$(run)"; echo "$out" | tail -4 | sed 's/^/     /'
ok "B DONE" 'echo "$out" | grep -q "S945_PHI_OUT_TRACKER_BUNDLED: DONE"'
ok "B code_bundle.py at TO, bak beside" '[ "$(m8 "$CB")" = "$TO8" ] && [ "$(m8 "$CB.bak_S945_aa8f985f")" = aa8f985f ]'
ok "B the three retired, the live folder clean, the retired list empty" '[ ! -f "$RA/make_force_keys.py" ] && [ ! -f "$RA/force_keys.txt" ] && [ -f "$RET/make_force_keys.py" ] && grep -q "TRIPLES = \[\]" "$RET/make_force_keys.py" && ! grep -qE "[6-9][0-9]{9}" "$RET/make_force_keys.py"'
ok "B the built bundle lists the tracker's .py, not data/, not make_force_keys" 'tar -xzOf "$TAR" MANIFEST.md5 | grep -q followup_tracker/server_runner.py && ! tar -xzOf "$TAR" MANIFEST.md5 | grep -q "followup_tracker/data/" && ! tar -xzOf "$TAR" MANIFEST.md5 | grep -q make_force_keys'
ok "B lock released" '[ ! -d "$R/root/root/deploy/.lock" ]'
echo "C  again"; out="$(run)"; ok "C already installed" 'echo "$out" | grep -q "already installed"'
echo "D  undo"; out="$(run --undo)"; ok "D UNDONE: code_bundle back, the three back (no numbers)" 'echo "$out" | grep -q UNDONE && [ "$(m8 "$CB")" = aa8f985f ] && [ -f "$RA/make_force_keys.py" ] && [ -f "$RA/force_keys.txt" ] && ! grep -qE "[6-9][0-9]{9}" "$RA/make_force_keys.py"'
echo "E  forced red at 4"; mk; out="$(REHEARSE_RED_AT=4 run)"; ok "E everything back" 'echo "$out" | grep -q RED && [ "$(m8 "$CB")" = aa8f985f ] && [ -f "$RA/make_force_keys.py" ] && [ ! -f "$RET/make_force_keys.py" ] && [ ! -d "$R/root/root/deploy/.lock" ]'
echo "F  tampered kit"; mk; rm -rf "$R/kitT"; cp -rp "$KDIR" "$R/kitT"; echo "# x" >> "$R/kitT/retire_s945.py"
out="$(ROOT="$R/root" LOCK="$R/root/root/deploy/.lock" APY="$(command -v python3)" bash "$R/kitT/install_S945_PHI_OUT_TRACKER_BUNDLED.sh" 2>&1)"; ok "F SUMS gate" 'echo "$out" | grep -q "SUMS.md5 gate failed"'
echo "G  wrong live pin"; mk; echo "# drift" >> "$CB"; out="$(run)"; ok "G stop, nothing moved" 'echo "$out" | grep -q "changed after this kit was built" && [ -f "$RA/make_force_keys.py" ]'
echo "H  lock held"; mk; mkdir -p "$R/root/root/deploy/.lock"; out="$(run)"; ok "H refused" 'echo "$out" | grep -q "another build holds" && [ -f "$RA/make_force_keys.py" ]'
echo "I  half state: force_keys.txt already retired -> STOP, nothing moved, everything back"; mk; mkdir -p "$RET"; echo x > "$RET/force_keys.txt"; out="$(run)"
ok "I restored" 'echo "$out" | grep -q "already in the retired folder" && [ -f "$RA/make_force_keys.py" ] && grep -qE "[6-9][0-9]{9}" "$RA/make_force_keys.py" && [ "$(m8 "$CB")" = aa8f985f ] && [ ! -d "$R/root/root/deploy/.lock" ]'
echo "REHEARSAL $((n-f))/$n"; [ "$f" = 0 ]
