#!/bin/bash
# =============================================================================
#  install_S343_NEAR_EXPIRY.sh · kit S343_NEAR_EXPIRY (session 274, Sanjeevni, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S343_NEAR_EXPIRY/install_S343_NEAR_EXPIRY.sh
#
#  D567 item 6: near-expiry from the archived expiry exports (D409, three months on each batch's own expiry).
#    /root/finance/spine/near_expiry.py   NEW (TO below) -- reads the kept STOCK_EXPIRY exports and spine.db read-only,
#                                         writes expiry/ beside the spine
#    CRONTAB: one root line, 23:57 daily, tagged # S343_NEAR_EXPIRY -- DECLARED TO THE PARENT
#  No screen, no table, no restart, nothing in finance.db, no existing file changed.
# =============================================================================
set -u
KIT="S343_NEAR_EXPIRY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
SP="$ROOT/finance/spine"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s343_walk_$STAMP"
NE_TO=627a3915727fce3595c2fdfb11b8f01a
CRON_LINE='57 23 * * * cd /root/finance/spine && /root/wa/venv/bin/python3 -B near_expiry.py >> /root/finance/spine/near_expiry.log 2>&1 # S343_NEAR_EXPIRY'
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 near_expiry.py)" = "$NE_TO" ] || { say "!! [1/7] kit near_expiry.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$SP/near_expiry.py")" = "$NE_TO" ]; then say "-- ALREADY INSTALLED"; crontab -l 2>/dev/null | grep -q "# S343_NEAR_EXPIRY" && say "   cron line present" || say "   !! cron line ABSENT"; exit 0; fi
[ -e "$SP/near_expiry.py" ] && { say "!! [2/7] $SP/near_expiry.py exists and is not this kit's - nothing installed"; exit 1; }
[ -s "$SP/spine.db" ] && [ -f "$SP/spine_build.py" ] || { say "!! [2/7] no spine at $SP (S331 not live?) - nothing installed"; exit 1; }
say "[2/7] the spine is there ($(m5 "$SP/spine.db" | cut -c1-8)); no earlier copy of this file"
mkdir -p "$WALK/compile" || exit 1
cp -p near_expiry.py selftest_s343.py "$WALK/compile/" && ( cd "$WALK/compile" && "$SPY" -m py_compile near_expiry.py selftest_s343.py && "$VPY" -m py_compile near_expiry.py selftest_s343.py ) \
  || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] py_compile green on both pythons (on copies)"
SOUT="$( cd "$WALK/compile" && "$VPY" -B "$KDIR/selftest_s343.py" --spine-dir "$SP" --ingest "$ROOT/marg_ingest" --archive "$ROOT/marg_ingest/archive" 2>&1 )"
echo "$SOUT" | grep -E '^  (ok|FAIL)|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^selftest: 16/16" || { say "!! [4/7] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/7] selftest 16/16 on a scratch spine (live SCHEMA), synthetic exports, and the newest real export on this box"
# a dry rehearsal against the LIVE spine into scratch first -- the real file is written only by the placed copy
DOUT="$( cd "$WALK/compile" && "$VPY" -B near_expiry.py --spine "$SP/spine.db" --out "$WALK/expiry" --archive "$ROOT/marg_ingest/archive" 2>&1 | tail -3 )"
echo "$DOUT" | sed 's/^/   /'
echo "$DOUT" | grep -qE "^(export:|NO EXPIRY EXPORT)" || { say "!! [5/7] the rehearsal did not run against the live spine - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/7] near-expiry runs against the live spine and the kept exports (read-only)"
CBAK="$SP/crontab.bak_S343_$STAMP"
crontab -l > "$CBAK" 2>/dev/null || : > "$CBAK"
restore() {
  say "!! RED after placing - restoring"
  rm -f "$SP/near_expiry.py"; crontab "$CBAK" 2>/dev/null || true
  say "   near_expiry.py removed · crontab restored from $CBAK (expiry/ left as written, harmless)"
  exit 1
}
\cp -p near_expiry.py "$SP/near_expiry.py" && [ "$(m5 "$SP/near_expiry.py")" = "$NE_TO" ] || restore
if ! crontab -l 2>/dev/null | grep -q "# S343_NEAR_EXPIRY"; then { crontab -l 2>/dev/null; echo "$CRON_LINE"; } | crontab - || restore; fi
crontab -l 2>/dev/null | grep -q "# S343_NEAR_EXPIRY" || restore
say "[6/7] placed $NE_TO; cron 23:57 (# S343_NEAR_EXPIRY); crontab backup $CBAK"
ROUT="$( cd "$SP" && "$VPY" -B near_expiry.py 2>&1 | tail -3 )"
echo "$ROUT" | sed 's/^/   /'
echo "$ROUT" | grep -qE "^(export:|NO EXPIRY EXPORT)" && [ -s "$SP/expiry/near_expiry_latest.txt" ] || restore
say "[7/7] tonight's file is written: $SP/expiry/near_expiry_latest.txt (read it; every removal is a Marg voucher, R6)"
md5sum "$SP/near_expiry.py"
say "$KIT: DONE -- a file beside the spine, refreshed 23:57 nightly; no screen, no finance.db change."
