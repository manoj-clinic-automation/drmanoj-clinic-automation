#!/bin/bash
# =============================================================================
#  install_S347_SPINE_BACKUP.sh · kit S347_SPINE_BACKUP (session 276 parent, 20-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S347_SPINE_BACKUP/install_S347_SPINE_BACKUP.sh
#
#  THE PHARMACY SPINE (S331, live 20-Sep 07:19) INTO THE TWO NIGHTLY STORES.
#  Named to the parent by the Sanjeevni chat at its S274 close; this is that line.
#
#  CODE CHANGE, TWO FILES, BOTH RUN BY CRON ONLY -- NO SERVICE IS RESTARTED:
#    /root/state_backup/code_bundle.py          598e55a4 -> v1.7  carries /root/finance/spine
#                                               (*.py *.json *.txt, non-recursive) at 01:35
#    /root/state_backup/clinic_state_backup.py  fba57985 -> v4    carries spine.db (sqlite
#                                               backup api) + readings/ at 01:50, encrypted
#
#  Gates: kit SUMS + KIT_ID + the spine actually on the box -> the selftest on COPIES
#  of both live files against a fake root (49 checks, 4 negative controls) -> a
#  read-only --check of each -> --apply each (backup .bak_S347_* beside it, py_compile
#  before replacing) -> read-back -> the live proof, READ-ONLY: what tonight's code
#  bundle will carry from the spine, and the state backup's own `preflight` (every
#  source present, spine.db integrity, Drive reachable, NOTHING shipped).
#  ALL-OR-NOTHING: if the second file refuses, the first is put back from its backup.
#
#  --restore : put both files back from their newest .bak_S347_* (nothing else).
# =============================================================================
set -u
KIT="S347_SPINE_BACKUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
CB="${CB:-/root/state_backup/code_bundle.py}"
SB="${SB:-/root/state_backup/clinic_state_backup.py}"
SPINE="${SPINE:-/root/finance/spine}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s347_$STAMP"
say() { echo "$@"; }

restore_one() {  # $1 = live file
  local b; b="$(ls -1t "$1".bak_S347_* 2>/dev/null | head -1)"
  if [ -n "$b" ]; then \cp -p "$b" "$1" && say "    restored $1 from $(basename "$b") (md5 $(md5sum "$1" | cut -c1-8))"
  else say "    no .bak_S347_* beside $1 -- nothing to restore"; fi
}
if [ "${1:-}" = "--restore" ]; then
  say "$KIT --restore:"; restore_one "$CB"; restore_one "$SB"; exit 0
fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
[ -f "$CB" ] || { say "!! preflight: $CB is not there - nothing changed"; exit 1; }
[ -f "$SB" ] || { say "!! preflight: $SB is not there - nothing changed"; exit 1; }
grep -q "S318, the gap" "$CB" || { say "!! preflight: $CB does not carry S318 yet - install S318 first, nothing changed"; exit 1; }
grep -q '"/root/state_backup/sheets",' "$SB" || { say "!! preflight: $SB is not the S233 v3 source list - nothing changed"; exit 1; }
[ -f "$SPINE/spine.db" ] || { say "!! preflight: $SPINE/spine.db is not on this box - S331 is not live here, nothing changed"; exit 1; }
[ -d "$SPINE/readings" ] || { say "!! preflight: $SPINE/readings is not on this box - S331 is not live here, nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/7] kit gates green; the spine is on this box ($(ls "$SPINE/readings" | grep -c '\.json$') readings, spine.db $(du -k "$SPINE/spine.db" | cut -f1) KB)"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
SOUT="$( cd /tmp && timeout 600 "$VPY" -B "$KDIR/selftest_s347.py" "--code-bundle=$CB" "--state-backup=$SB" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$SOUT" in
  *"SELFTEST OK"*) say "[2/7] $(echo "$SOUT" | grep -o 'SELFTEST OK -- [0-9]* checks') on copies of both live files" ;;
  *) say "!! [2/7] selftest red against copies of the live files:"; say "    $SOUT"; rm -rf "$T"; exit 1 ;;
esac

say "[3/7] as they stand now (read-only):"
"$VPY" -B patch_code_bundle_s347.py --check "--file=$CB" | sed 's/^/    /'
"$VPY" -B patch_state_backup_s347.py --check "--file=$SB" | sed 's/^/    /'

say "[4/7] applying to the code bundle:"
AOUT="$("$VPY" -B patch_code_bundle_s347.py --apply "--file=$CB" 2>&1)"
echo "$AOUT" | sed 's/^/    /'
case "$AOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [4/7] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1 ;;
esac
"$VPY" -B patch_code_bundle_s347.py --check "--file=$CB" | grep -q "RESULT ALREADY" \
  || { say "!! [4/7] the read-back does not carry the change"; restore_one "$CB"; rm -rf "$T"; exit 1; }
"$VPY" -B -c "import py_compile; py_compile.compile('$CB', cfile='$T/cb.pyc', doraise=True)" \
  || { say "!! [4/7] the live file does not compile -- putting it back"; restore_one "$CB"; rm -rf "$T"; exit 1; }
say "[4/7] code bundle applied and it compiles (md5 $(md5sum "$CB" | cut -c1-32))"

say "[5/7] applying to the state backup:"
BOUT="$("$VPY" -B patch_state_backup_s347.py --apply "--file=$SB" 2>&1)"
echo "$BOUT" | sed 's/^/    /'
case "$BOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [5/7] refused for the reason above - putting the code bundle back too (all or nothing)"; restore_one "$CB"; rm -rf "$T"; exit 1 ;;
esac
"$VPY" -B patch_state_backup_s347.py --check "--file=$SB" | grep -q "RESULT ALREADY" \
  || { say "!! [5/7] the read-back does not carry the change -- putting both back"; restore_one "$SB"; restore_one "$CB"; rm -rf "$T"; exit 1; }
"$VPY" -B -c "import py_compile; py_compile.compile('$SB', cfile='$T/sb.pyc', doraise=True)" \
  || { say "!! [5/7] the live file does not compile -- putting both back"; restore_one "$SB"; restore_one "$CB"; rm -rf "$T"; exit 1; }
say "[5/7] state backup applied and it compiles (md5 $(md5sum "$SB" | cut -c1-32)); nothing restarted (both files run by cron only)"

say "[6/7] the live proof, read-only:"
say "    (a) what tonight's 01:35 code bundle will carry from $SPINE (a gather, no bundle written):"
ROOT="${PROOF_ROOT:-/}" "$VPY" -B - "$CB" <<'PY' 2>/dev/null | sed 's/^/        /'
import importlib.util, io, sys
from contextlib import redirect_stdout, redirect_stderr
spec = importlib.util.spec_from_file_location("cb", sys.argv[1]); m = importlib.util.module_from_spec(spec)
buf = io.StringIO()
with redirect_stdout(buf), redirect_stderr(buf):
    spec.loader.exec_module(m)
    files, skipped, hits = m.gather()
sp = sorted(r for r, _ in files if r.startswith("root/finance/spine/"))
print("%d file(s) under root/finance/spine/:" % len(sp))
for r in sp: print("  " + r)
print("readings/ orders/ expiry/ in the code bundle: %s (must be 0)" % sum(1 for r, _ in files if r.startswith(("root/finance/spine/readings/", "root/finance/spine/orders/", "root/finance/spine/expiry/"))))
PY
say "    (b) the state backup's own preflight -- every source present, spine.db integrity, Drive reachable, NOTHING shipped:"
POUT="$("$VPY" -B "$SB" preflight 2>&1)"
echo "$POUT" | grep -iv "key file\|openssl\|identity" | tail -12 | sed 's/^/        /'
case "$POUT" in
  *"PREFLIGHT OK"*|*"preflight ok"*|*"every precondition"*) say "    preflight: green" ;;
  *) say "    preflight: read the lines above -- if it names a FATAL, the 01:50 job will refuse tonight for that reason (the .bak_S347_* files are beside both targets; --restore puts them back)" ;;
esac
rm -rf "$T"

say "[7/7] tonight: 01:35 carries the spine's code and rule files; 01:50 carries spine.db + readings/ inside the encrypted state bundle."
say "$KIT: DONE"
say "read next (on the PC, tomorrow): D:\\Downloads\\_kbtools\\vps_code\\code_nightly.tar.gz -> root/finance/spine/ ; and /root/state_backup/clinic_state_backup.log"
