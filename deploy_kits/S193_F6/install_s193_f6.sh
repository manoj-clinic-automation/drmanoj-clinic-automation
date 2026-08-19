#!/bin/bash
# =====================================================================
#  S193_F6 · the Staff-Ledger bridge (F-148) + the contra against_month
#            fix (F-153).  ONE kit, two payloads, one install run.
#
#  F6 / F-148  (finance_app.py) — APPROVAL posts a salary advance to the
#    Staff Ledger. When the doctor approves a Sanjeevni day that carries a
#    salary-advance expense, the advance is written to the Staff Ledger as
#    an ADVANCE_ISSUE (against that day's month), THROUGH the ledger's own
#    writer. Approval is the post; entry is not. Order: ledger first, then
#    the finance stamp — so a crash leaves a visible ledger row, never a
#    finance record claiming a post that never happened. IDEMPOTENT
#    (ledger_posted is the guard). FAIL-LOUD: any ledger error REFUSES the
#    approval; the day stays submitted and nothing is committed.
#
#  F-153  (staff_ledger.py) — make_contra now carries the original's
#    against_month, so a reversal nets that month's quota instead of
#    leaking to the contra's own entry month.
#
#  Verified offline with the F-87 seeded-store remedy (differential, zero
#  failures added). D317 chain, self-gating, rolls BOTH back on any red.
#  Projections, written before measuring:
#     ledger  selftest 287 -> 289  (+2)
#     finance smoke    550 -> 555  (+5)
# =====================================================================
set -u
cd "$(dirname "$0")"
LEDGER_WANT=44e39d6abf34db5e11acc2223ac908d3     # SL7, current live
FIN_WANT=17e6b84ce90ca7d7a0a9ba0c668ab15f        # F5,  current live
LIVE_LEDGER=/root/staff_ledger.py
LIVE_FIN=/root/finance/finance_app.py
LPY=/root/wa/venv/bin/python3                     # the ledger runs under the venv
SVC_L=staff-ledger.service
SVC_F=clinic-finance.service

echo "==============================================================="
echo " S193_F6 · Staff-Ledger bridge (F-148) + contra fix (F-153)"
echo "==============================================================="
echo "[1/9] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "      KIT_ID : $(cat KIT_ID.txt)"

echo "[2/9] ledger currency gate (expect SL7)"
HL=$(md5sum $LIVE_LEDGER | cut -d' ' -f1); echo "      live ledger : $HL"
[ "$HL" = "$LEDGER_WANT" ] || { echo '*** RED: ledger is not the SL7 build. STOP.'; exit 1; }

echo "[3/9] finance currency gate (expect F5)"
HF=$(md5sum $LIVE_FIN | cut -d' ' -f1); echo "      live finance: $HF"
[ "$HF" = "$FIN_WANT" ] || { echo '*** RED: finance is not the F5 build. STOP.'; exit 1; }

echo "[4/9] ledger projection 287 -> 289 (+2, F-153)"
CL=$($LPY $LIVE_LEDGER --selftest 2>&1 | tail -1); echo "      cur : $CL"
echo "$CL" | grep -q "PASSED — 287 " || { echo '*** RED. STOP.'; exit 1; }
NL=$($LPY ./staff_ledger_S193.py --selftest 2>&1 | tail -1); echo "      new : $NL"
echo "$NL" | grep -q "PASSED — 289 " || { echo '*** RED. STOP.'; exit 1; }

echo "[5/9] finance projection 550 -> 555 (+5, F6) — dry run on a staged copy"
CF=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
echo "      cur : $CF"; echo "$CF" | grep -q "SMOKE 550/550" || { echo '*** RED. STOP.'; exit 1; }
STAGE=$(mktemp -d); mkdir -p "$STAGE/finance_ui"
cp /root/finance/*.py "$STAGE/" 2>/dev/null
cp /root/finance/finance_ui/*.html "$STAGE/finance_ui/" 2>/dev/null
cp finance_app_S193.py "$STAGE/finance_app.py"
cp /root/finance/finance.db "$STAGE/finance.db"
NF=$(cd "$STAGE" && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE ")
rm -rf "$STAGE"
echo "      new : $NF"; echo "$NF" | grep -q "SMOKE 555/555" || { echo '*** RED. STOP.'; exit 1; }

echo "[6/9] ledger-user mapping preflight (who may post salary advances)"
python3 - <<'PYEOF'
import json, sqlite3
lu = {}
try:
    lu = json.load(open('/root/staff_ledger/users.json'))
except Exception as e:
    print("      (could not read ledger users.json:", e, ")")
con = sqlite3.connect('/root/finance/finance.db'); con.row_factory = sqlite3.Row
fin = [r['username'] for r in con.execute(
    "SELECT DISTINCT username FROM unit_role WHERE unit='medical' AND role='checker' AND active=1")]
any_ok = False
for u in fin:
    ok = (u in lu and lu[u].get('role') == 'checker'); any_ok = any_ok or ok
    print("      medical checker '%s' -> ledger checker: %s"
          % (u, "YES" if ok else "NO -- his salary-advance approvals will be REFUSED"))
if fin and not any_ok:
    print("      *** WARNING: no medical checker is a ledger checker. Salary-advance")
    print("          approvals will fail-loud (refuse) until a ledger user is added.")
    print("          Nothing is corrupted; the day simply will not approve.")
PYEOF

TS=$(date +%Y%m%d_%H%M%S)
echo "[7/9] backup"
BL=/root/staff_ledger.py.bak_S193_$TS; cp -p $LIVE_LEDGER "$BL"; echo "      ledger  -> $BL"
BF=/root/finance/_backup_S193_$TS; mkdir -p "$BF"; cp -p $LIVE_FIN "$BF/"; echo "      finance -> $BF/finance_app.py"

rollback(){ echo "*** RED -- ROLLING BACK BOTH."; cp -p "$BL" $LIVE_LEDGER; cp -p "$BF/finance_app.py" $LIVE_FIN; systemctl restart $SVC_L $SVC_F; exit 1; }

echo "[8/9] swap + live verify"
cp staff_ledger_S193.py $LIVE_LEDGER
PL=$($LPY $LIVE_LEDGER --selftest 2>&1 | tail -1); echo "      ledger  : $PL"; echo "$PL" | grep -q "PASSED — 289 " || rollback
cp finance_app_S193.py $LIVE_FIN
PF=$(cd /root/finance && python3 finance_app.py --selftest 2>&1 | grep -m1 "SMOKE "); echo "      finance : $PF"; echo "$PF" | grep -q "SMOKE 555/555" || rollback

echo "[9/9] restart services"
systemctl restart $SVC_L; sleep 2; systemctl is-active --quiet $SVC_L || rollback
systemctl restart $SVC_F; sleep 2; systemctl is-active --quiet $SVC_F || rollback

echo "==============================================================="
echo " GREEN.  S193_F6 is live."
echo "   staff_ledger.py  $(md5sum $LIVE_LEDGER | cut -d' ' -f1)   (287 -> 289, F-153)"
echo "   finance_app.py   $(md5sum $LIVE_FIN | cut -d' ' -f1)   (550 -> 555, F6/F-148)"
echo " NOW LOOK: approve a Sanjeevni day that carries a salary advance on"
echo " /finance/review, then open that staff member's ledger statement and"
echo " confirm the ADVANCE_ISSUE appears, attributed to the day's month."
echo " Then pin BOTH md5s into the KB Register (D321(d))."
echo "==============================================================="
