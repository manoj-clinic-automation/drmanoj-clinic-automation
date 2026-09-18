#!/bin/bash
# =============================================================================
#  install_S318_UNIT_GAP.sh · kit S318_UNIT_GAP (session 269 parent, 18-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S318_UNIT_GAP/install_S318_UNIT_GAP.sh
#
#  Needs S317 in place (it patches v1.5). Two parts: seven more unit files in the
#  bundle -- both call-* timers, staff-register, staff-ledger, assetapp,
#  attlistener, attendance-dashboard -- and a section in unit_state.txt that
#  NAMES every enabled unit of ours the bundle does not carry, so this gap can
#  never hide again.
#
#  CODE CHANGE, ONE FILE: /root/state_backup/code_bundle.py, c7f33e55 -> 598e55a4.
#  No service is restarted: that file is run by the 01:35 timer and nothing else.
#
#  Gates: kit SUMS + KIT_ID -> the selftest on a COPY of the live file against a
#  fake root shaped like this box (28 checks, 3 negative controls) -> a read-only
#  --check -> --apply, which backs the file up and py_compiles before replacing
#  anything -> read-back -> the live table printed once, read-only, from S317.
# =============================================================================
set -u
KIT="S318_UNIT_GAP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
TARGET="${TARGET:-/root/state_backup/code_bundle.py}"
SHOW="${SHOW:-$KDIR/../S317_UNIT_STATE/show_unit_state_s317.py}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s318_$STAMP"
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
[ -f "$TARGET" ] || { say "!! preflight: $TARGET is not there - nothing changed"; exit 1; }
grep -q "S317, F-496" "$TARGET" || { say "!! preflight: $TARGET does not carry S317 yet - install S317 first, nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/6] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
SOUT="$( cd /tmp && timeout 300 "$VPY" -B "$KDIR/selftest_s318.py" "--file=$TARGET" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$SOUT" in
  *"SELFTEST OK"*) say "[2/6] $(echo "$SOUT" | grep -o 'SELFTEST OK -- [0-9]* checks')" ;;
  *) say "!! [2/6] selftest red against a copy of the live file:"; say "    $SOUT"; rm -rf "$T"; exit 1 ;;
esac
say "    target: $TARGET"

say "[3/6] as it stands now (read-only):"
"$VPY" -B patch_code_bundle_s318.py --check "--file=$TARGET" | sed 's/^/    /'

say "[4/6] applying:"
AOUT="$("$VPY" -B patch_code_bundle_s318.py --apply "--file=$TARGET" 2>&1)"
echo "$AOUT" | sed 's/^/    /'
case "$AOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [4/6] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1 ;;
esac
"$VPY" -B patch_code_bundle_s318.py --check "--file=$TARGET" | grep -q "RESULT ALREADY" \
  || { say "!! [4/6] the read-back does not carry the change -- the .bak_S318_* beside the file holds the original"; rm -rf "$T"; exit 1; }
"$VPY" -B -c "import py_compile; py_compile.compile('$TARGET', cfile='$T/t.pyc', doraise=True)" \
  || { say "!! [4/6] the live file does not compile -- restore the .bak_S318_* beside it"; rm -rf "$T"; exit 1; }
say "[4/6] applied and it compiles; nothing was restarted (the 01:35 timer runs this file)"

if [ -f "$SHOW" ]; then
  say "[5/6] the live answer, read-only -- the gap as it stands now:"
  "$VPY" -B "$SHOW" "--file=$TARGET" 2>/dev/null \
    | sed -n '/enabled, ours, and NOT carried/,/units carried by this bundle/p' | sed 's/^/    /'
else
  say "[5/6] S317's read-only viewer is not beside this kit; tonight's bundle carries the same table"
fi
rm -rf "$T"

say "[6/6] tonight's 01:35 bundle carries seven more unit files and the gap section."
say "$KIT: DONE"
say "read next (on the PC, tomorrow): D:\\Downloads\\_kbtools\\vps_code\\code_nightly.tar.gz -> unit_state.txt"
