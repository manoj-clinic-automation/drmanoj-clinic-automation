#!/bin/bash
# =============================================================================
#  install_S416_BUNDLE_ALLOWLIST.sh · kit S416_BUNDLE_ALLOWLIST (session 282, 26-Sep-2026) · F-631
#
#  The S279 close found five live files in NO nightly code bundle. code_bundle.py v1.7 -> v1.8 adds four
#  source entries (root/portal *.js · ring-*.service · root/wa/casepack *.html *.py · root/wa *.sh) as NEW
#  lines after the old ones, so nothing carried today stops being carried. Proved here on a mock root with
#  the kit's own bytes of the five before anything is placed; then the real 'build' (no network) runs on the
#  box and must list the files that exist. The next 01:35 'run' ships them to Drive.
#  FILE:  /root/state_backup/code_bundle.py  v1.7 8200dcca -> v1.8 37a5a132.  No service restart.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S416_BUNDLE_ALLOWLIST/install_S416_BUNDLE_ALLOWLIST.sh
# =============================================================================
set -u
KIT="S416_BUNDLE_ALLOWLIST"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SB="${SB:-/root/state_backup}"; F="$SB/code_bundle.py"
S_FROM=8200dcca2256a843ccabcdbd8250ec55; S_TO=37a5a1326a8e90c364e3e50c6083f4f3
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 code_bundle.py)" = "$S_TO" ] || { say "!! [1/6] kit code_bundle.py not at its pin - nothing installed"; exit 1; }
say "[1/6] kit gates green"
[ "$(m5 "$F")" = "$S_TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
[ "$(m5 "$F")" = "$S_FROM" ] || { say "!! [2/6] code_bundle.py is $(m5 "$F"), not v1.7 - nothing installed"; exit 1; }
say "[2/6] live pin exact (code_bundle v1.7)"
"$VPY" -B -c "import sys, hashlib; sys.argv = sys.argv[1:]; exec(open(sys.argv[0]).read().split('open(sys.argv[2]')[0]); assert hashlib.md5(s.encode()).hexdigest() == sys.argv[2]" \
  apply_s416.py "$F" "$S_TO" 2>/dev/null || { say "!! [3/6] the kit file is not the live file plus S416 - nothing installed"; exit 1; }
"$VPY" -B -m py_compile code_bundle.py walk_s416.py || { say "!! [3/6] compile failed - nothing installed"; exit 1; }
say "[3/6] rebuilt from the live bytes = the kit file; py_compile green"
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s416.py" "$KDIR/code_bundle.py" "$F" "$KDIR/five" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/6] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/6] $WOUT (mock root; nothing on the box touched)"
for p in /root/portal/portal_sw.js /root/portal/http_ece.py /etc/systemd/system/ring-hook.service /root/wa/casepack/casepack_page.html /root/wa/fu_push_on_arrival.sh; do
  if [ -f "$p" ]; then say "      on the box: $p  $(m5 "$p" | cut -c1-8)"; else say "      NOT ON THE BOX: $p  (F-631 pinned it; the pin needs correcting at the close)"; fi
done
BS="$F.bak_S416_8200dcca"
\cp -p "$F" "$BS" || { say "!! [5/6] backup failed - nothing placed"; exit 1; }
\cp -p code_bundle.py "$F" && [ "$(m5 "$F")" = "$S_TO" ] || { \cp -p "$BS" "$F"; say "!! [5/6] did not read back - restored"; exit 1; }
say "[5/6] placed; backup beside the file"
BOUT="$( "$VPY" -B "$F" build 2>&1 | tail -3 )"
echo "$BOUT" | grep -q "SUMMARY files=" || { \cp -p "$BS" "$F"; say "!! [6/6] the real build failed - restored v1.7: $BOUT"; exit 1; }
say "[6/6] real build (no network) green: $(echo "$BOUT" | grep SUMMARY | cut -c1-120)"
MF="$(tar -tzf "$SB/code_nightly.tar.gz" 2>/dev/null | grep -cE 'portal_sw\.js|ring-hook\.service|casepack_page\.html|fu_push_on_arrival\.sh|http_ece\.py')"
say "      of the five, now in the local bundle: $MF   (the 01:35 run ships it to Drive)"
md5sum "$F"
say "[6/6] $KIT: DONE"
