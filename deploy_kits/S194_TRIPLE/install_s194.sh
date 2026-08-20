#!/bin/bash
# =====================================================================
#  S194  ·  three medical-finance features, ONE install run
#
#   ⭐1  Daily Sale v2 page  — a NEW two-stage page at /finance/daily
#        (enter+save -> submit -> reconcile+transfer -> final submit,
#        plus a transfer-only path). /finance/entry stays as fallback.
#   ⭐2  Home-medicine bills  — sales Marg bills out to "Home Medicine /
#        Home Medisun" are auto-tagged from the export (no scan) and
#        shown on the Hub + a /finance/api/home-medicine endpoint.
#   ⭐3  Cash/UPI reclassification log — a re-import that flips a bill's
#        payment mode (cash<->upi) is logged to mode_change_log and
#        shown on the Hub + a /finance/api/reclassifications endpoint.
#
#  Payloads: finance_app.py (swap) · finance_ingest.py (swap) ·
#            finance_ui/finance_daily.html (NEW) ·
#            finance_ui/finance_approvals.html (swap, +2 Hub cards).
#  Live DB: sale_item gains home_med; new table mode_change_log
#           (idempotent migration in step 5).
#
#  Self-gating (3 currency hashes), ALL-GREEN smoke required, and the
#  new checks must have RUN (smoke total grows). Rolls ALL files back on
#  any red and restarts the service.
# =====================================================================
set -u
cd "$(dirname "$0")"

LIVE_FIN=/root/finance/finance_app.py
LIVE_INGEST=/root/finance/finance_ingest.py
LIVE_HTML=/root/finance/finance_ui/finance_approvals.html
LIVE_DAILY=/root/finance/finance_ui/finance_daily.html
LIVE_DB=/root/finance/finance.db
SVC_F=clinic-finance.service

FIN_WANT=4c0a2d19734e3860ed3d172191b2e7ff       # current live (S193 close)
INGEST_WANT=a4e9663f9be1c138293d6dd8311577d0    # current live (S193 DISC)
HTML_WANT=8ce3fabd3f712d99456d60ddbf6f4e1c      # current live Hub (S193 CASHPOS4)

echo "==============================================================="
echo " S194 · Daily Sale v2 · home-medicine · cash/UPI reclass"
echo "==============================================================="

echo "[1/11] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "       KIT_ID : $(cat KIT_ID.txt)"

echo "[2/11] currency gates (3 live files)"
gate(){ local h; h=$(md5sum "$1" | cut -d' ' -f1); echo "       $2 : $h";
        [ "$h" = "$3" ] || { echo "*** RED: $2 is not the expected build. STOP."; exit 1; }; }
gate "$LIVE_FIN"    "finance_app   " "$FIN_WANT"
gate "$LIVE_INGEST" "finance_ingest" "$INGEST_WANT"
gate "$LIVE_HTML"   "approvals html" "$HTML_WANT"

echo "[3/11] measure CURRENT smoke (baseline, before any change)"
CUR=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "       $CUR"
echo "$CUR" | grep -Eq "SMOKE ([0-9]+)/\1 " || { echo '*** RED: baseline smoke not all-green. STOP.'; exit 1; }
CUR_T=$(echo "$CUR" | sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')

TS=$(date +%Y%m%d_%H%M%S)
echo "[4/11] backup (files + DB) -> /root/finance/_backup_S194_$TS"
BK=/root/finance/_backup_S194_$TS; mkdir -p "$BK/finance_ui"
cp -p "$LIVE_FIN" "$LIVE_INGEST" "$BK/"
cp -p "$LIVE_HTML" "$BK/finance_ui/"
cp -p "$LIVE_DB" "$BK/finance.db"

rollback(){
  echo "*** RED -- ROLLING BACK ALL FILES.";
  cp -p "$BK/finance_app.py"    "$LIVE_FIN";
  cp -p "$BK/finance_ingest.py" "$LIVE_INGEST";
  cp -p "$BK/finance_ui/finance_approvals.html" "$LIVE_HTML";
  rm -f "$LIVE_DAILY";
  systemctl restart $SVC_F;
  echo "    (the new home_med column and mode_change_log table are harmless";
  echo "     and were left in place; no sale/booking data was written.)";
  exit 1;
}

echo "[5/11] migrate live DB — sale_item.home_med + mode_change_log (idempotent)"
python3 - "$LIVE_DB" <<'PY' || rollback
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
cols = {r[1] for r in con.execute("PRAGMA table_info(sale_item)")}
if "home_med" not in cols:
    con.execute("ALTER TABLE sale_item ADD COLUMN home_med INTEGER DEFAULT 0")
    print("       migration: added sale_item.home_med")
else:
    print("       migration: sale_item.home_med already present")
con.execute("CREATE TABLE IF NOT EXISTS mode_change_log ("
            " id INTEGER PRIMARY KEY AUTOINCREMENT, unit TEXT NOT NULL,"
            " business_date TEXT NOT NULL, source_ref TEXT, patient_ref_id INTEGER,"
            " amount_p INTEGER, old_mode TEXT, new_mode TEXT, ingest_batch_id INTEGER,"
            " changed_at TEXT NOT NULL)")
con.execute("CREATE INDEX IF NOT EXISTS ix_modechg_day ON mode_change_log(unit, business_date)")
con.commit()
print("       migration: mode_change_log ready")
PY

echo "[6/11] install the NEW Daily Sale page"
cp finance_ui/finance_daily.html "$LIVE_DAILY" || rollback

echo "[7/11] swap finance_app.py + finance_ingest.py + Hub html"
cp finance_app_S194.py    "$LIVE_FIN"    || rollback
cp finance_ingest_S194.py "$LIVE_INGEST" || rollback
cp finance_ui/finance_approvals.html "$LIVE_HTML" || rollback

echo "[8/11] py_compile the swapped python"
python3 -c "import py_compile as p; [p.compile(f,doraise=True) for f in ['$LIVE_FIN','$LIVE_INGEST']]; print('       compile OK')" || rollback

echo "[9/11] measure NEW smoke — require ALL-GREEN and that the new checks ran"
NEW=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "       $NEW"
echo "$NEW" | grep -Eq "SMOKE ([0-9]+)/\1 " || rollback          # every check passed
NEW_T=$(echo "$NEW" | sed -n 's#.*SMOKE [0-9]*/\([0-9]*\).*#\1#p')
[ "$NEW_T" -gt "$CUR_T" ] || { echo "*** RED: the S194 checks did not run ($CUR_T -> $NEW_T)."; rollback; }
echo "       smoke grew $CUR_T -> $NEW_T (the S194 checks ran and passed)"

echo "[10/11] sanity — the new route + endpoints + Hub cards are present"
grep -q '/finance/daily' "$LIVE_FIN" \
  && grep -q 'api/home-medicine' "$LIVE_FIN" \
  && grep -q 'api/reclassifications' "$LIVE_FIN" \
  && grep -q 'homeMedCard' "$LIVE_HTML" \
  && grep -q 'reclassCard' "$LIVE_HTML" \
  && grep -q 'mode_change_log' "$LIVE_INGEST" || rollback
echo "       OK"

echo "[11/11] restart service + verify"
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  S194 is live."
echo "   finance_app.py    $(md5sum $LIVE_FIN    | cut -d' ' -f1)"
echo "   finance_ingest.py $(md5sum $LIVE_INGEST | cut -d' ' -f1)"
echo "   finance_daily.html$(md5sum $LIVE_DAILY  | cut -d' ' -f1)"
echo "   approvals html    $(md5sum $LIVE_HTML   | cut -d' ' -f1)"
echo "   smoke             : $NEW_T (was $CUR_T)"
echo "---------------------------------------------------------------"
echo " ⭐1  Darpan's new page:  https://<finance-host>/finance/daily"
echo "      (the old /finance/entry still works — switch over when happy)."
echo " ⭐2  Home-medicine + ⭐3 Reclassified: two new cards on the Hub"
echo "      (/finance/approvals). Hard-refresh once."
echo " Pin the 4 md5s above into the KB Register (D321(d))."
echo "==============================================================="
