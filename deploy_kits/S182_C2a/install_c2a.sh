#!/bin/bash
# =============================================================================
#  install_c2a.sh · kit S182_C2a — clinic redesign (C2): English UI, four
#  tenders (cash/UPI/card/razorpay), expenses, two-stage approval
#  (verify -> final), tracker-day panel + feed endpoint.
#  Proven pattern: preflight -> stage from kit dir -> backup -> swap ->
#  python3 migration (marker migration.S182_c2) -> smoke gate -> restart
#  on green -> HONEST red path (restores only what was touched).
#  NOTE: gas/VPS_Push_TrackerDay.gs is NOT installed here — it goes into the
#  clinic Gmail Apps Script by hand, like VPS_Push_UPI.gs did.
# =============================================================================
set -u
for c in python3 systemctl curl md5sum awk; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing before touching anything"; exit 1; }
done
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIVE=/root/finance
cd "$KIT_DIR" \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S182_C2a" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_app.py.new | awk '{print $1}')" ] \
&& cp finance_app.py.new "$LIVE/finance_app.py.new" \
&& cp finance_ui/finance_entry_clinic.html.new "$LIVE/finance_ui/finance_entry_clinic.html.new" \
&& cp finance_migration_S182_c2.sql "$LIVE/" \
&& cd "$LIVE" \
&& systemctl stop clinic-finance \
&& cp finance_app.py finance_app.py.bak_S182C2 \
&& cp finance_ui/finance_entry_clinic.html finance_ui/finance_entry_clinic.html.bak_S182C2 \
&& cp finance.db finance.db.bak_S182C2 \
&& touch .S182C2_touched \
&& mv finance_app.py.new finance_app.py \
&& mv finance_ui/finance_entry_clinic.html.new finance_ui/finance_entry_clinic.html \
&& python3 -m py_compile finance_app.py \
&& python3 - <<'PYEOF'
import sqlite3, sys
con = sqlite3.connect("finance.db")
done = con.execute("SELECT value FROM setting WHERE key='migration.S182_c2'").fetchone()
if done:
    print("migration already applied — skipping (marker present)")
else:
    con.executescript(open("finance_migration_S182_c2.sql").read()); con.commit()
    print("migration applied")
sys.exit(0 if con.execute("SELECT value FROM setting WHERE key='migration.S182_c2'").fetchone() else 1)
PYEOF
[ $? -eq 0 ] \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz \
&& rm -f .S182C2_touched \
&& echo "" && echo "S182_C2a INSTALLED — smoke green, migration in, service restarted" \
|| { echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S182C2_touched" ]; then \
        echo "   live files WERE touched — restoring from the S182C2 backups:"; \
        cp -f "$LIVE/finance_app.py.bak_S182C2" "$LIVE/finance_app.py" && echo "   finance_app.py restored"; \
        cp -f "$LIVE/finance_ui/finance_entry_clinic.html.bak_S182C2" "$LIVE/finance_ui/finance_entry_clinic.html" && echo "   entry UI restored"; \
        cp -f "$LIVE/finance.db.bak_S182C2" "$LIVE/finance.db" && echo "   finance.db restored"; \
        rm -f "$LIVE/.S182C2_touched"; \
     else \
        echo "   the gate fired BEFORE anything live was touched — nothing to restore."; \
     fi; \
     systemctl start clinic-finance; \
     echo "   the C2 redesign is NOT installed"; exit 1; }
