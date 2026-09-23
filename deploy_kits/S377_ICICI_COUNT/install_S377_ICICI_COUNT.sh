#!/bin/bash
# =============================================================================
#  install_S377_ICICI_COUNT.sh · kit S377_ICICI_COUNT (session 281, Sanjeevni, 23-Sep-2026) · F-615
#  S375 counted what ICICI holds from ZERO at the 17-Aug cash anchor, so it could not see the money the account
#  already held -- and its over-balance rule refused the owner's real 20-Sep ICICI -> Yes Bank transfer of
#  40,000. Now the count starts at the balance the BANK printed on its own statement (new table bank_anchor,
#  seeded from his August ICICI statement: 1,50,263.42 as on 31-Aug), a statement that stops on an entry's own
#  date no longer calls it missing, and a count that is short records the transfer and says so.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S377_ICICI_COUNT/install_S377_ICICI_COUNT.sh
#
#    /root/finance/sanjeevni_approvals.py            4f98cb37 (S375) -> TO  (v1.2)
#    /root/finance/finance_ui/finance_approvals.html 19c877e5 (S375) -> TO -- THE PARENT'S FILE, DECLARED
#    finance.db: ONE NEW TABLE bank_anchor + ONE row (the ICICI closing balance from his own statement).
#    clinic-finance RESTARTED -- DECLARED.
# =============================================================================
set -u
KIT="S377_ICICI_COUNT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s377_walk_$STAMP"
declare -A FROM=( [sanjeevni_approvals.py]=4f98cb378a9beee6771c3df11cc3d606 [finance_ui/finance_approvals.html]=19c877e57a65e54740af86690fedc90a )
declare -A TO=( [sanjeevni_approvals.py]=f52ff84779df0c5a6abdb718ab19323a [finance_ui/finance_approvals.html]=87157a85833c84b917a6df7c49db2324 )
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$FIN/sanjeevni_approvals.py")" = "${TO[sanjeevni_approvals.py]}" ] && [ "$(m5 "$FIN/finance_ui/finance_approvals.html")" = "${TO[finance_ui/finance_approvals.html]}" ]; then
  say "-- files ALREADY INSTALLED; the anchor:"; ( cd "$FIN" && FINANCE_APP_DIR="$FIN" "$VPY" -B "$KDIR/seed_icici_anchor.py" ); exit 0; fi
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/7] $FIN/$f is not its pin ${FROM[$f]:0:8} - nothing installed"; exit 1; }; done
say "[2/7] live files at their pins (S375)"
mkdir -p "$WALK/app/finance_ui" "$WALK/kit" || exit 1
cp -p apply_s377.py walk_s377.py seed_icici_anchor.py "$WALK/kit/" || exit 1
for p in "$FIN"/*.py "$FIN"/*.json "$FIN"/*.sql "$FIN"/*.html "$FIN"/*.txt; do [ -f "$p" ] && cp -p "$p" "$WALK/app/"; done
cp -p "$FIN"/finance_ui/* "$WALK/app/finance_ui/" 2>/dev/null
( cd "$WALK/kit" && "$SPY" -B apply_s377.py --dir "$FIN" --out "$WALK/app" ) | sed 's/^/   /'
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do
  [ "$(m5 "$WALK/app/$f")" = "${TO[$f]}" ] || { say "!! [3/7] the patch does not produce the predicted $f - nothing installed"; rm -rf "$WALK"; exit 1; }; done
( cd "$WALK/app" && "$SPY" -m py_compile sanjeevni_approvals.py && "$VPY" -m py_compile sanjeevni_approvals.py ) || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the patch produces exactly the predicted bytes; compiles on both pythons"
"$SPY" - "$FIN/finance.db" "$WALK/scratch.db" <<'PYEOF' || { say "!! [4/7] could not copy the database - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
WOUT="$( cd "$WALK/kit" && timeout 600 "$SPY" -B walk_s377.py --app "$WALK/app" --db "$WALK/scratch.db" --seed "$WALK/kit/seed_icici_anchor.py" 2>&1 )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S377 GREEN" || { say "!! [4/7] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[4/7] walk green on a scratch copy of the live database (above) -- his own 20-Sep transfers, both of them"
restore() {
  say "!! RED after placing - restoring byte-identically"
  for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do [ -f "$FIN/$f.bak_S377_${FROM[$f]:0:8}" ] && \cp -p "$FIN/$f.bak_S377_${FROM[$f]:0:8}" "$FIN/$f"; done
  systemctl restart clinic-finance 2>/dev/null; sleep 3
  say "   sanjeevni_approvals.py $(m5 "$FIN/sanjeevni_approvals.py") · healthz $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)"
  say "   the database backup of this run: $FIN/finance.db.bak_S377_$STAMP"
  exit 1
}
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S377_$STAMP" <<'PYEOF' || { say "!! [5/7] database backup failed - nothing installed"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do \cp -p "$FIN/$f" "$FIN/$f.bak_S377_${FROM[$f]:0:8}" || restore; done
( cd "$KDIR" && "$SPY" -B apply_s377.py --dir "$FIN" ) | sed 's/^/   /'
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
for f in sanjeevni_approvals.py finance_ui/finance_approvals.html; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore; done
say "[5/7] database backed up (finance.db.bak_S377_$STAMP); .bak_S377_<from8> beside each file; placed; every md5 read back = the kit"
systemctl restart clinic-finance || restore
sleep 3
systemctl is-active --quiet clinic-finance || restore
HC=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
[ "$HC" = "200" ] || restore
IMP="$( cd "$FIN" && "$SPY" -B -c "import sanjeevni_approvals; print('imports', sanjeevni_approvals.VERSION)" 2>&1 )"
echo "$IMP" | grep -q "imports 1.2" || restore
say "[6/7] clinic-finance up, healthz $HC, the bank door is v1.2"
( cd "$FIN" && FINANCE_APP_DIR="$FIN" "$VPY" -B "$KDIR/seed_icici_anchor.py" ) | sed 's/^/   /'
md5sum "$FIN/sanjeevni_approvals.py" "$FIN/finance_ui/finance_approvals.html"
say "[7/7] $KIT: DONE -- record the 40,000 of 20-Sep on the Bank section; ICICI now counts from the bank's own balance."
