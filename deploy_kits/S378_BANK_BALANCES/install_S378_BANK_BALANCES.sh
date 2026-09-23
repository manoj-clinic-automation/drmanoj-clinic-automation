#!/bin/bash
# =============================================================================
#  install_S378_BANK_BALANCES.sh · kit S378_BANK_BALANCES (session 281, Sanjeevni, 23-Sep-2026)
#  The owner, after S377: "better if it could also show the updated balances of both the accounts boldly and
#  clearly in the banks section." Bank now opens with two bold figures -- ICICI Sanjeevni (S377's count from
#  the bank's own balance) and Yes Bank Sanjeevni (the balance its own statement closes on, plus every
#  recorded movement that statement does not show, never counting a confirmed one twice).
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S378_BANK_BALANCES/install_S378_BANK_BALANCES.sh
#
#    /root/finance/sanjeevni_approvals.py            f52ff847 (S377) -> TO  (v1.3)
#    /root/finance/finance_ui/finance_approvals.html 87157a85 (S377) -> TO -- THE PARENT'S FILE, DECLARED
#    finance.db is NOT touched: both figures are read, nothing is stored.
#    clinic-finance RESTARTED -- DECLARED.
# =============================================================================
set -u
KIT="S378_BANK_BALANCES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s378_walk_$STAMP"
declare -A FROM=( [sanjeevni_approvals.py]=f52ff84779df0c5a6abdb718ab19323a [finance_ui/finance_approvals.html]=87157a85833c84b917a6df7c49db2324 )
declare -A TO=( [sanjeevni_approvals.py]=7ab5fec63db83af3e11c6ac08599be93 [finance_ui/finance_approvals.html]=750f89e008a89a372af25cf7898a7d17 )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/sanjeevni_approvals.py")" = "${TO[sanjeevni_approvals.py]}" ] && [ "$(m5 "$FIN/finance_ui/finance_approvals.html")" = "${TO[finance_ui/finance_approvals.html]}" ]; then
  say "-- ALREADY INSTALLED"; exit 0; fi
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
say "[2/7] live files at their pins (S377)"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s378.py walk_s378.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s378.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$WALK/app/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the patch does not produce the predicted $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
( cd "$WALK/app" && "$SPY" -m py_compile sanjeevni_approvals.py && "$VPY" -m py_compile sanjeevni_approvals.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s378.py --app "$WALK/app" --db "$WALK/scratch.db" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S378 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above); the live database was never written to"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do [ -f "$FIN/$f.bak_S378_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S378_${FROM[$f]:0:8}" "$FIN/$f"; done
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   sanjeevni_approvals.py $(m5 "$FIN/sanjeevni_approvals.py") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  exit 1
}
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do \cp -p "$FIN/$f" "$FIN/$f.bak_S378_${FROM[$f]:0:8}" || restore; done
( cd "$KDIR" && "$SPY" -B apply_s378.py --dir "$FIN" ) | sed 's/^/   /'
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[5/7] .bak_S378_<from8> beside each file; placed; every md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_approvals; print('imports', sanjeevni_approvals.VERSION)" 2>&1 )"
echo "$IMP" | grep -q "imports 1.3" || restore
say "[6/7] clinic-finance up, healthz $HC, the bank door is v1.3"
( cd "$FIN" && "$SPY" -B -c "
import finance_app as fa, sanjeevni_approvals as sa
with fa.app.app_context():
    con = fa.db(); i = sa.icici_position(con); y = sa.yesbank_position(con)
    print('   ICICI Sanjeevni    %s' % sa.rs(max(i['holds_p'], 0)))
    print('   Yes Bank Sanjeevni %s  (statement of %s closes at %s)' % (sa.rs(max(y['holds_p'], 0)), y['as_on'], sa.rs(y['base_p'])))
    con.commit()" 2>&1 | grep -v Warning )
md5sum "$FIN/sanjeevni_approvals.py" "$FIN/finance_ui/finance_approvals.html"
say "[7/7] $KIT: DONE -- Bank opens with both balances, bold."
