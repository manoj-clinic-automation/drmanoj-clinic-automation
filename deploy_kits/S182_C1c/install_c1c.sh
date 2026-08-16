#!/bin/bash
# =============================================================================
#  install_c1c.sh · kit S182_C1c — clinic daily entry (C1 slice 1)
#  Supersedes C1b, whose installer called the `sqlite3` CLI — absent on the
#  VPS. The migration now runs through python3's built-in sqlite3 module
#  (the same interpreter the app runs on, F-53), and a PREFLIGHT verifies
#  every command this script uses before anything is touched.
# =============================================================================
set -u
for c in python3 systemctl curl md5sum awk; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' not found on this box — refusing before touching anything"; exit 1; }
done
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIVE=/root/finance
cd "$KIT_DIR" \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S182_C1c" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_app.py.new | awk '{print $1}')" ] \
&& cp finance_app.py.new "$LIVE/finance_app.py.new" \
&& mkdir -p "$LIVE/finance_ui" \
&& cp finance_ui/finance_entry_clinic.html.new "$LIVE/finance_ui/finance_entry_clinic.html.new" \
&& cp finance_migration_S182_clinic.sql "$LIVE/finance_migration_S182_clinic.sql" \
&& cd "$LIVE" \
&& systemctl stop clinic-finance \
&& cp finance_app.py finance_app.py.bak_S182 \
&& cp finance.db finance.db.bak_S182 \
&& touch .S182_touched \
&& mv finance_app.py.new finance_app.py \
&& mv finance_ui/finance_entry_clinic.html.new finance_ui/finance_entry_clinic.html \
&& python3 -m py_compile finance_app.py \
&& python3 - <<'PYEOF'
import sqlite3, sys
con = sqlite3.connect("finance.db")
done = con.execute("SELECT value FROM setting WHERE key='migration.S182_clinic'").fetchone()
if done:
    print("migration already applied — skipping (marker present)")
else:
    con.executescript(open("finance_migration_S182_clinic.sql").read())
    con.commit()
    print("migration applied")
chk = con.execute("SELECT value FROM setting WHERE key='migration.S182_clinic'").fetchone()
sys.exit(0 if chk else 1)
PYEOF
[ $? -eq 0 ] \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz \
&& rm -f .S182_touched \
&& echo "" && echo "S182_C1c INSTALLED — smoke green, migration in, service restarted" \
|| { echo "RED — install did not complete."; \
     if [ -f "$LIVE/.S182_touched" ]; then \
        echo "   live files WERE touched — restoring from the S182 backups:"; \
        cp -f "$LIVE/finance_app.py.bak_S182" "$LIVE/finance_app.py" && echo "   finance_app.py restored"; \
        cp -f "$LIVE/finance.db.bak_S182" "$LIVE/finance.db" && echo "   finance.db restored"; \
        rm -f "$LIVE/finance_ui/finance_entry_clinic.html" "$LIVE/.S182_touched"; \
     else \
        echo "   the gate fired BEFORE anything live was touched — nothing to restore."; \
     fi; \
     systemctl start clinic-finance; \
     echo "   the clinic slice is NOT installed"; exit 1; }
