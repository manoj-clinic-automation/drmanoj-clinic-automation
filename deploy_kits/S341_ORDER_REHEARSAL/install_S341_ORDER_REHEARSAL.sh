#!/bin/bash
# =============================================================================
#  install_S341_ORDER_REHEARSAL.sh · kit S341_ORDER_REHEARSAL (session 274, Sanjeevni, 20-Sep-2026)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S341_ORDER_REHEARSAL/install_S341_ORDER_REHEARSAL.sh
#
#  D567 item 5: ordering prepared offline against the spine, rehearsed every night, NOT switched.
#    /root/finance/spine/order_rehearsal.py   NEW (TO below)  -- reads spine.db read-only, writes orders/ beside it
#    /root/finance/spine/order_rules.json     written by the first run (the four lists, internal_use seeded, S235)
#    CRONTAB: one root line, 23:58 daily, tagged # S341_ORDER_REHEARSAL -- DECLARED TO THE PARENT
#  No screen, no table, no restart, nothing in finance.db, no existing file changed.
# =============================================================================
set -u
KIT="S341_ORDER_REHEARSAL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
SP="$ROOT/finance/spine"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s341_walk_$STAMP"
OR_TO=02582fbea29f51606a6ba8bb8694d3fc
CRON_LINE='58 23 * * * cd /root/finance/spine && /root/wa/venv/bin/python3 -B order_rehearsal.py >> /root/finance/spine/order_rehearsal.log 2>&1 # S341_ORDER_REHEARSAL'
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 order_rehearsal.py)" = "$OR_TO" ] || { say "!! [1/7] kit order_rehearsal.py is not its pin - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$SP/order_rehearsal.py")" = "$OR_TO" ]; then say "-- ALREADY INSTALLED"; crontab -l 2>/dev/null | grep -q "# S341_ORDER_REHEARSAL" && say "   cron line present" || say "   !! cron line ABSENT"; exit 0; fi
[ -e "$SP/order_rehearsal.py" ] && { say "!! [2/7] $SP/order_rehearsal.py exists and is not this kit's - nothing installed"; exit 1; }
[ -s "$SP/spine.db" ] && [ -f "$SP/spine_build.py" ] || { say "!! [2/7] no spine at $SP (S331 not live?) - nothing installed"; exit 1; }
say "[2/7] the spine is there ($(m5 "$SP/spine.db" | cut -c1-8)); no earlier copy of this file"
mkdir -p "$WALK/compile" || exit 1
cp -p order_rehearsal.py selftest_s341.py "$WALK/compile/" && ( cd "$WALK/compile" && "$SPY" -m py_compile order_rehearsal.py selftest_s341.py && "$VPY" -m py_compile order_rehearsal.py selftest_s341.py ) \
  || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] py_compile green on both pythons (on copies)"
SOUT="$( cd "$WALK/compile" && "$VPY" -B "$KDIR/selftest_s341.py" --spine-dir "$SP" 2>&1 )"
echo "$SOUT" | grep -E '^  (ok|FAIL)|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^selftest: 15/15" || { say "!! [4/7] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/7] selftest 15/15 on a scratch spine built with the live SCHEMA"
# a dry rehearsal against the LIVE spine into scratch first -- the real file is written only by the placed copy
DOUT="$( cd "$WALK/compile" && "$VPY" -B order_rehearsal.py --spine "$SP/spine.db" --out "$WALK/orders" --rules "$WALK/order_rules.json" 2>&1 | tail -3 )"
echo "$DOUT" | sed 's/^/   /'
echo "$DOUT" | grep -q "^lines " || { say "!! [5/7] the rehearsal did not run against the live spine - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/7] rehearsal runs against the live spine (read-only)"
CBAK="$SP/crontab.bak_S341_$STAMP"
crontab -l > "$CBAK" 2>/dev/null || : > "$CBAK"
restore() {
  say "!! RED after placing - restoring"
  rm -f "$SP/order_rehearsal.py"; crontab "$CBAK" 2>/dev/null || true
  say "   order_rehearsal.py removed · crontab restored from $CBAK (orders/ and order_rules.json left as written, harmless)"
  exit 1
}
\cp -p order_rehearsal.py "$SP/order_rehearsal.py" && [ "$(m5 "$SP/order_rehearsal.py")" = "$OR_TO" ] || restore
if ! crontab -l 2>/dev/null | grep -q "# S341_ORDER_REHEARSAL"; then { crontab -l 2>/dev/null; echo "$CRON_LINE"; } | crontab - || restore; fi
crontab -l 2>/dev/null | grep -q "# S341_ORDER_REHEARSAL" || restore
say "[6/7] placed $OR_TO; cron 23:58 (# S341_ORDER_REHEARSAL); crontab backup $CBAK"
ROUT="$( cd "$SP" && "$VPY" -B order_rehearsal.py 2>&1 | tail -3 )"
echo "$ROUT" | sed 's/^/   /'
echo "$ROUT" | grep -q "^lines " && [ -s "$SP/orders/order_rehearsal_latest.txt" ] && [ -s "$SP/order_rules.json" ] || restore
say "[7/7] tonight's file is written: $SP/orders/order_rehearsal_latest.txt (read it; nothing acts on it)"
md5sum "$SP/order_rehearsal.py" "$SP/order_rules.json"
say "$KIT: DONE -- NOT switched: no screen, no send, no finance.db change. The owner's sitting edits $SP/order_rules.json."
