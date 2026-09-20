#!/bin/bash
# =============================================================================
#  install_S357_DAY_TRUTH_3.sh · kit S357_DAY_TRUTH_3 (session 275, Sanjeevni, 20-Sep-2026) -- on S356 (LIVE 22:17)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S357_DAY_TRUTH_3/install_S357_DAY_TRUTH_3.sh
#
#  THE OWNER'S RULING (20-Sep, 22:2x): a credit note on a home / procedure medicine bill is bookkeeping --
#  goods came back to the shop, no cash moved -- so the day's cash must NOT read low by it.
#    /root/finance/day_resync.py   S356 cfe61ee6 -> TO below: a label credit note becomes ONE cash_adjustment
#                                  row of +amount (the ledger's own +/- column), once; the 11-Sep CN00208 +2300
#    /root/finance/darpan_kal.py   28e23b15 -> patched (anchored, apply_kal_s357.py): Darpan's expected cash
#    /root/finance/darpan_kal.html e62746d8 -> patched: one row, shown only when an adjustment exists
#    clinic-finance RESTARTED (the kal blueprint is loaded by the app) -- DECLARED TO THE PARENT
#    cron: unchanged (# S356_DAY_TRUTH_2 runs the same file every 30 min 07-23)
#  No parent file changed.  finance.db backed up first (sqlite backup API).
# =============================================================================
set -u
KIT="S357_DAY_TRUTH_3"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="$FIN/finance.db"
SVC="${SVC:-clinic-finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s357_walk_$STAMP"
DR_FROM=cfe61ee6fec44b9406b9f91d3c9f2e13
DR_TO=a4e53adc201904bc48a15b592ddd9ebe
KAL_PY_FROM=28e23b15daae7f92d4ea668fb5a06b77
KAL_PY_TO=04bb158650393e1cff2ce9bd3b38bceb
KAL_HTML_FROM=e62746d86e349a143179b320f9d6a87f
KAL_HTML_TO=31f737f26bab765ae35aaa12f9c74232
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 day_resync.py)" = "$DR_TO" ] || { say "!! [1/8] kit day_resync.py is not its pin - nothing installed"; exit 1; }
say "[1/8] kit gates green"
if [ "$(m5 "$FIN/day_resync.py")" = "$DR_TO" ] && [ "$(m5 "$FIN/darpan_kal.py")" = "$KAL_PY_TO" ] && [ "$(m5 "$FIN/darpan_kal.html")" = "$KAL_HTML_TO" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
[ "$(m5 "$FIN/day_resync.py")" = "$DR_FROM" ] || { say "!! [2/8] $FIN/day_resync.py is not S356's $DR_FROM (is S356 live?) - nothing installed"; exit 1; }
[ "$(m5 "$FIN/darpan_kal.py")" = "$KAL_PY_FROM" ] || { say "!! [2/8] $FIN/darpan_kal.py is not its pin $KAL_PY_FROM - nothing installed"; exit 1; }
[ "$(m5 "$FIN/darpan_kal.html")" = "$KAL_HTML_FROM" ] || { say "!! [2/8] $FIN/darpan_kal.html is not its pin $KAL_HTML_FROM - nothing installed"; exit 1; }
[ -s "$DB" ] && [ -f "$FIN/finance_upi.py" ] || { say "!! [2/8] no finance.db or finance_upi.py at $FIN - nothing installed"; exit 1; }
say "[2/8] S356 live ($DR_FROM); darpan_kal.py $KAL_PY_FROM and its page at their pins"
mkdir -p "$WALK/compile" "$WALK/kal" || exit 1
cp -p day_resync.py selftest_s357.py apply_kal_s357.py "$WALK/compile/" && ( cd "$WALK/compile" && "$SPY" -m py_compile day_resync.py selftest_s357.py apply_kal_s357.py && "$VPY" -m py_compile day_resync.py selftest_s357.py apply_kal_s357.py ) \
  || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green on both pythons (on copies)"
SOUT="$( cd "$WALK/compile" && "$VPY" -B selftest_s357.py --finance-dir "$FIN" --python "$VPY" 2>&1 )"
echo "$SOUT" | grep -E '^  FAIL|selftest:' | sed 's/^/   /'
echo "$SOUT" | grep -q "^selftest: 30/30" || { say "!! [4/8] selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
# the kal patch rehearsed into scratch from the LIVE files: the predicted hashes must come out
KOUT="$( cd "$WALK/compile" && "$VPY" -B apply_kal_s357.py --dir "$FIN" --out "$WALK/kal" 2>&1 )"
echo "$KOUT" | sed 's/^/   /'
[ "$(m5 "$WALK/kal/darpan_kal.py")" = "$KAL_PY_TO" ] && [ "$(m5 "$WALK/kal/darpan_kal.html")" = "$KAL_HTML_TO" ] && ( cd "$WALK/kal" && "$VPY" -m py_compile darpan_kal.py ) \
  || { say "!! [4/8] the kal patch does not produce the predicted files - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest 30/30 with this box's finance_upi; the kal patch rehearsed into scratch = the predicted bytes"
DOUT="$( cd "$WALK/compile" && "$VPY" -B day_resync.py --db "$DB" --dry-run --no-reconcile 2>&1 )"
echo "$DOUT" | grep -vE "^  (SAME|NONE|PRESENT) " | sed 's/^/   /'
echo "$DOUT" | grep -q "^summary2:" || { say "!! [5/8] the dry run did not read the live database - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/8] dry run against the live database read (nothing written)"
BAK="$FIN/finance.db.bak_S357_$STAMP"
"$VPY" - "$DB" "$BAK" <<'EOF' || { say "!! [6/8] database backup failed - nothing installed"; exit 1; }
import sqlite3, sys
src = sqlite3.connect(sys.argv[1]); dst = sqlite3.connect(sys.argv[2])
src.backup(dst); dst.close(); src.close()
EOF
[ -s "$BAK" ] || { say "!! [6/8] backup empty - nothing installed"; exit 1; }
say "[6/8] finance.db backed up (sqlite backup API): $BAK"
restore() {
  say "!! RED after placing - restoring byte-identically"
  [ -f "$FIN/day_resync.py.bak_S357_${DR_FROM:0:8}" ] && \cp -p "$FIN/day_resync.py.bak_S357_${DR_FROM:0:8}" "$FIN/day_resync.py"
  [ -f "$FIN/darpan_kal.py.bak_S357_${KAL_PY_FROM:0:8}" ] && \cp -p "$FIN/darpan_kal.py.bak_S357_${KAL_PY_FROM:0:8}" "$FIN/darpan_kal.py"
  [ -f "$FIN/darpan_kal.html.bak_S357_${KAL_HTML_FROM:0:8}" ] && \cp -p "$FIN/darpan_kal.html.bak_S357_${KAL_HTML_FROM:0:8}" "$FIN/darpan_kal.html"
  systemctl restart "$SVC" 2>/dev/null; sleep 3
  say "   day_resync.py $(m5 "$FIN/day_resync.py") · darpan_kal.py $(m5 "$FIN/darpan_kal.py") · darpan_kal.html $(m5 "$FIN/darpan_kal.html") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz) · database backup $BAK"
  exit 1
}
\cp -p "$FIN/day_resync.py" "$FIN/day_resync.py.bak_S357_${DR_FROM:0:8}" || exit 1
\cp -p day_resync.py "$FIN/day_resync.py" && [ "$(m5 "$FIN/day_resync.py")" = "$DR_TO" ] || restore
"$VPY" -B apply_kal_s357.py --dir "$FIN" | sed 's/^/   /' || restore
[ "$(m5 "$FIN/darpan_kal.py")" = "$KAL_PY_TO" ] && [ "$(m5 "$FIN/darpan_kal.html")" = "$KAL_HTML_TO" ] || restore
say "[7/8] placed day_resync.py $DR_TO · darpan_kal.py $KAL_PY_TO · darpan_kal.html $KAL_HTML_TO (backups .bak_S357_<from8> beside each)"
systemctl restart "$SVC" || restore
sleep 3
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$VPY" -B -c "import darpan_kal as k; print(k.compute_day.__doc__.split(chr(10))[0])" 2>&1 )"
echo "$IMP" | grep -q "Expected cash" || restore
ROUT="$( cd "$FIN" && flock -w 60 /tmp/day_resync.lock "$VPY" -B day_resync.py 2>&1 )"
echo "$ROUT" | grep -vE "^  (SAME|NONE|PRESENT) " | sed 's/^/   /'
echo "$ROUT" | grep -q "^summary2:" || restore
say "[8/8] $SVC restarted, healthz $HC, the patched kal module imports; the resync ran once (above)"
md5sum "$FIN/day_resync.py" "$FIN/darpan_kal.py" "$FIN/darpan_kal.html"
say "$KIT: DONE -- a home / procedure credit note no longer reads as missing cash; the approval section and Darpan's page agree."
