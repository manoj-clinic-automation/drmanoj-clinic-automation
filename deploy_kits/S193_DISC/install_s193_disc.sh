#!/bin/bash
# =====================================================================
#  S193_DISC · the per-bill DISCOUNT feature (Hub Fix 5).
#
#  Today the Marg bill drill shows only the NET; a discounted bill
#  reconciles invisibly against a day's gap. After this, every bill
#  shows  Gross | Disc | Net, going forward AND for all history.
#
#  FIVE payloads, ONE install run:
#   1. finance_schema.sql  — sale_item gains gross_p, disc_p (fresh-DB
#      reference; the live DB is migrated in step [5] by ALTER).
#   2. marg_report.py      — the bill-level CSV now carries gross, disc.
#   3. finance_ingest.py   — (in-place patch) the Marg adapter reads
#      gross/disc from the row and stores gross_p/disc_p. It reads them
#      DIRECTLY (not via column-map), so no column-map change is needed
#      and the schema's our_field CHECK is never touched.
#   4. finance_app.py      — the bill drill returns gross/disc per bill.
#   5. finance_approvals.html — (in-place patch) Gross | Disc | Net cols.
#
#  Historical fill is a SEPARATE, explicit second command (see the end)
#  so you see the code working before any history is written. It only
#  ever writes gross_p/disc_p — never the booked net.
#
#  Self-gating (5 currency hashes), measured ZERO-delta smoke, rolls ALL
#  files back on any red. tax_p is always 0 in your data, and Marg rounds
#  the net, so gross is STORED (not computed) to stay exact.
# =====================================================================
set -u
cd "$(dirname "$0")"

LIVE_FIN=/root/finance/finance_app.py
LIVE_MARG=/root/finance/marg_report.py
LIVE_INGEST=/root/finance/finance_ingest.py
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
LIVE_DB=/root/finance/finance.db
SVC_F=clinic-finance.service

FIN_WANT=d455e1aad1e6a91dce0b3b4d3f0e440f       # F-155, current live
MARG_WANT=829f4344df6e086510bb0fb6112ecb77      # live parser (xls+xlsx)
INGEST_WANT=1f730bcdf3c7044841cedc06833bc228    # current live ingest
HTML_WANT=fbf1655fd5137c5853581d44142f7874      # current live Hub template

echo "==============================================================="
echo " S193_DISC · per-bill discount (Gross | Disc | Net)"
echo "==============================================================="

echo "[1/11] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "       KIT_ID : $(cat KIT_ID.txt)"

echo "[2/11] currency gates (5 live files)"
gate(){ local h; h=$(md5sum "$1" | cut -d' ' -f1); echo "       $2 : $h";
        [ "$h" = "$3" ] || { echo "*** RED: $2 is not the expected build. STOP."; exit 1; }; }
gate "$LIVE_FIN"    "finance_app   " "$FIN_WANT"
gate "$LIVE_MARG"   "marg_report   " "$MARG_WANT"
gate "$LIVE_INGEST" "finance_ingest" "$INGEST_WANT"
gate "$LIVE_HTML"   "approvals html" "$HTML_WANT"

echo "[3/11] measure CURRENT smoke (baseline, before any change)"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "       $CUR"
CUR_N=$(echo "$CUR" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
echo "$CUR" | grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline smoke not all-green. STOP.'; exit 1; }

TS=$(date +%Y%m%d_%H%M%S)
echo "[4/11] backup (files + DB)"
BK=/root/finance/_backup_S193_DISC_$TS; mkdir -p "$BK"
cp -p "$LIVE_FIN" "$LIVE_MARG" "$LIVE_INGEST" "$BK/"
mkdir -p "$BK/finance_ui"; cp -p "$LIVE_HTML" "$BK/finance_ui/"
cp -p "$LIVE_DB" "$BK/finance.db"
echo "       -> $BK"

rollback(){
  echo "*** RED -- ROLLING BACK ALL FILES.";
  cp -p "$BK/finance_app.py"     "$LIVE_FIN";
  cp -p "$BK/marg_report.py"     "$LIVE_MARG";
  cp -p "$BK/finance_ingest.py"  "$LIVE_INGEST";
  cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML";
  systemctl restart $SVC_F;
  echo "    (the new gross_p/disc_p columns are harmless and were left in place;";
  echo "     no history was written — the backfill is a separate command.)";
  exit 1;
}

echo "[5/11] migrate live DB — add sale_item.gross_p, disc_p (idempotent)"
python3 - "$LIVE_DB" <<'PY' || rollback
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
cols = {r[1] for r in con.execute("PRAGMA table_info(sale_item)")}
added = []
for c in ("gross_p", "disc_p"):
    if c not in cols:
        con.execute("ALTER TABLE sale_item ADD COLUMN %s INTEGER" % c); added.append(c)
con.commit()
print("       migration:", ("added " + ", ".join(added)) if added else "already present")
PY

echo "[6/11] swap marg_report.py + finance_app.py"
cp marg_report_S193.py "$LIVE_MARG" || rollback
cp finance_app_S193.py "$LIVE_FIN"  || rollback

echo "[7/11] in-place patch finance_ingest.py"
python3 patch_disc_ingest.py || rollback

echo "[8/11] in-place patch finance_approvals.html"
python3 patch_disc_hub.py || rollback

echo "[9/11] py_compile the swapped/patched python"
python3 -c "import py_compile as p; [p.compile(f,doraise=True) for f in ['$LIVE_FIN','$LIVE_MARG','$LIVE_INGEST']]; print('       compile OK')" || rollback

echo "[10/11] measure NEW smoke — require GREEN and ZERO delta vs baseline"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "       $NEW"
echo "$NEW" | grep -Eq "SMOKE ([0-9]+)/\1 " || rollback
NEW_N=$(echo "$NEW" | sed -n 's/.*SMOKE \([0-9]*\/[0-9]*\).*/\1/p')
[ "$NEW_N" = "$CUR_N" ] || { echo "*** RED: smoke count changed ($CUR_N -> $NEW_N)."; rollback; }

echo "[11/11] restart service + verify"
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  S193_DISC code is live."
echo "   finance_app.py   $(md5sum $LIVE_FIN    | cut -d' ' -f1)"
echo "   marg_report.py   $(md5sum $LIVE_MARG   | cut -d' ' -f1)"
echo "   finance_ingest.py$(md5sum $LIVE_INGEST | cut -d' ' -f1)"
echo "   approvals html   $(md5sum $LIVE_HTML   | cut -d' ' -f1)"
echo "   smoke unchanged  : $NEW_N"
echo "---------------------------------------------------------------"
echo " NEW Marg pushes now store & show gross/disc automatically."
echo
echo " NOW FILL HISTORY (3,162 bills, Apr 1 - Aug 15). First a dry-run:"
echo
echo "   python3 $(pwd)/apply_historical_discount.py --dry"
echo
echo " review the 'matched / would set' numbers, then commit it with:"
echo
echo "   python3 $(pwd)/apply_historical_discount.py --apply"
echo
echo " (it writes ONLY gross_p/disc_p, never the booked net; re-runnable.)"
echo " Then pin the new md5s into the KB Register (D321(d))."
echo "==============================================================="
