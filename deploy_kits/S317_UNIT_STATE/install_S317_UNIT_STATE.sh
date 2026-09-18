#!/bin/bash
# =============================================================================
#  install_S317_UNIT_STATE.sh · kit S317_UNIT_STATE (session 269 parent, 18-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S317_UNIT_STATE/install_S317_UNIT_STATE.sh
#
#  F-496: the nightly code bundle has always said WHAT each scheduled job is and
#  never WHETHER IT IS SWITCHED ON. This adds one generated member to the
#  bundle, unit_state.txt, beside crontab.txt: the *.wants enable symlinks read
#  from disk (gather() skips symlinks, so no bundle has ever carried one) and
#  systemctl's own is-enabled / is-active for every unit the bundle carries.
#
#  CODE CHANGE, ONE FILE: /root/state_backup/code_bundle.py, a70bf6e2 -> the pin
#  printed below. No service is restarted -- the file is run by the 01:35 timer
#  and by nothing else, so the change takes effect at the next run, tonight.
#
#  Gates: kit SUMS + KIT_ID -> the selftest, which patches a COPY of the LIVE
#  file, builds two whole bundles against a fake root and compares them member
#  by member (26 checks, 2 negative controls) -> a read-only --check -> --apply,
#  which backs the file up, py_compiles the result before it replaces anything,
#  and refuses on any anchor that is not found exactly once -> a read-back ->
#  the live table, printed once, read-only.
# =============================================================================
set -u
KIT="S317_UNIT_STATE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
TARGET="${TARGET:-/root/state_backup/code_bundle.py}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s317_$STAMP"
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
[ -f "$TARGET" ] || { say "!! preflight: $TARGET is not there - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/6] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
SOUT="$( cd /tmp && timeout 300 "$VPY" -B "$KDIR/selftest_s317.py" "--file=$TARGET" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$SOUT" in
  *"SELFTEST OK"*) say "[2/6] $(echo "$SOUT" | grep -o 'SELFTEST OK -- [0-9]* checks')" ;;
  *) say "!! [2/6] selftest red against a copy of the live file:"; say "    $SOUT"; rm -rf "$T"; exit 1 ;;
esac
say "    target: $TARGET"

say "[3/6] as it stands now (read-only):"
"$VPY" -B patch_code_bundle_s317.py --check "--file=$TARGET" | sed 's/^/    /'

say "[4/6] applying:"
AOUT="$("$VPY" -B patch_code_bundle_s317.py --apply "--file=$TARGET" 2>&1)"
echo "$AOUT" | sed 's/^/    /'
case "$AOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [4/6] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1 ;;
esac
"$VPY" -B patch_code_bundle_s317.py --check "--file=$TARGET" | grep -q "RESULT ALREADY" \
  || { say "!! [4/6] the read-back does not carry the change -- the .bak_S317_* beside the file holds the original"; rm -rf "$T"; exit 1; }
"$VPY" -B -c "import py_compile,sys; py_compile.compile('$TARGET', cfile='$T/t.pyc', doraise=True)" \
  || { say "!! [4/6] the live file does not compile -- restore the .bak_S317_* beside it"; rm -rf "$T"; exit 1; }
say "[4/6] applied and it compiles; nothing was restarted (the 01:35 timer runs this file)"

say "[5/6] the live answer, read-only -- what is switched on right now:"
"$VPY" -B show_unit_state_s317.py "--file=$TARGET" 2>/dev/null | sed 's/^/    /'
rm -rf "$T"

say "[6/6] tonight's 01:35 bundle will carry unit_state.txt; the PC nightly copies it"
say "    with the rest, and its manifest row is checked like every other member."
say "$KIT: DONE"
say "read next (on the PC, tomorrow): D:\\Downloads\\_kbtools\\vps_code\\code_nightly.tar.gz -> unit_state.txt"
