#!/bin/bash
# =============================================================================
#  install_S306_BUNDLE_MASK.sh · kit S306_BUNDLE_MASK (session 267, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S306_BUNDLE_MASK/install_S306_BUNDLE_MASK.sh
#
#  F-518: the nightly code bundle (01:35, to Google Drive and on to the owner's PC) carried the two machine
#  tokens in /etc/systemd/system/clinic-finance.service -- Environment= lines are unquoted, and the bundle's
#  content scan only catches quoted literals.
#   /root/state_backup/code_bundle.py  ed5b483f (v1.3) -> a70bf6e2 (v1.4)
#   unit files are MASKED (name kept, value replaced), the original md5 recorded in BUNDLE_INFO.txt, and a
#   closing guard refuses to ship a bundle that still carries a unit secret value (exit 23).
#  DATA: none. No service restarts: the file is run by cron at 01:35. The tokens themselves are NOT rotated
#  here -- that stays on the owner's key-rotation list (F-456): old copies already on Drive and the PC keep them.
#
#  Gates: kit SUMS + KIT_ID -> live pin exact (or ALREADY INSTALLED) -> compile -> test_s306 ON THIS BOX (builds
#  from the live tree into /tmp with the new file AND the live v1.3: no unit secret value anywhere in the new
#  bundle, only masked unit files differ, the guard refuses when masking is switched off) -> backup -> place ->
#  a local build (no network) from its real place must say MASKED and verify -> md5 read back.
#  Any red after placing: the file restored byte-identically.
# =============================================================================
set -u
KIT="S306_BUNDLE_MASK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
BROOT="${BROOT:-/}"                               # the tree a bundle is built from (the box)
DEST="${BROOT%/}/root/state_backup/code_bundle.py"
FROM=ed5b483f6eb09f0e3663091a01aaa251
TO=a70bf6e202a76fecc86306e39fdf9324
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s306_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/6] kit gates green"

[ "$(m5 "$DEST")" = "$TO" ] && { say "-- ALREADY INSTALLED: $DEST carries this kit."; exit 0; }
[ "$(m5 "$DEST")" = "$FROM" ] || { say "!! [2/6] $DEST is $(m5 "$DEST"), expected $FROM (v1.3) - nothing installed"; exit 1; }
[ "$(m5 code_bundle.py)" = "$TO" ] || { say "!! [2/6] kit code_bundle.py is not its predicted md5 - nothing installed"; exit 1; }
say "[2/6] live pin exact; kit file at its predicted md5"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T/new" "$T/old" && cp -p code_bundle.py "$T/new/" && cp -p "$DEST" "$T/old/code_bundle.py"
"$VPY" -m py_compile "$T/new/code_bundle.py" test_s306.py || { say "!! [3/6] compile failed - nothing installed"; rm -rf "$T"; exit 1; }
say "[3/6] py_compile green"

TOUT="$( cd /tmp && timeout 170 "$VPY" -B "$KDIR/test_s306.py" "$T/new" "$BROOT" "$T/old" 2>&1 | grep -E '^TEST OK|^FAIL|FATAL|Error' | tail -1 )"
echo "$TOUT" | grep -q "^TEST OK" || { say "!! [4/6] test red on this box: $TOUT - nothing installed"; rm -rf "$T"; exit 1; }
rm -rf "$T"
say "[4/6] $TOUT"

BAK="$DEST.bak_S306_${FROM:0:8}"
\cp -p "$DEST" "$BAK" || { say "!! [5/6] backup failed - nothing placed"; exit 1; }
restore() { say "!! RED after placing - restoring $DEST"; \cp -p "$BAK" "$DEST"; say "   $DEST $(m5 "$DEST")"; exit 1; }
\cp code_bundle.py "$DEST" || restore                # no -p: the live file keeps its owner and mode
[ "$(m5 "$DEST")" = "$TO" ] || { say "!! [5/6] $DEST did not land at its pin"; restore; }
say "[5/6] placed, backup $BAK"

BOUT="$( cd /tmp && ROOT="$BROOT" timeout 170 "$VPY" -B "$DEST" build 2>&1 )"
echo "$BOUT" | grep -q "SUMMARY files=" && echo "$BOUT" | grep -q "MASKED [1-9]" && ! echo "$BOUT" | grep -q "FATAL" \
  || { say "!! [6/6] the local build from the placed file did not mask or did not finish:"; echo "$BOUT" | grep -E 'FATAL|SUMMARY|MASKED' | tail -3; restore; }
say "[6/6] local build (no network) from the placed file:"
echo "$BOUT" | grep -E 'SUMMARY|MASKED' | sed 's/^/   /'
md5sum "$DEST"
say "$KIT: DONE -- tonight's 01:35 run ships the masked bundle to Drive; the PC copy follows at the 03:10 nightly."
