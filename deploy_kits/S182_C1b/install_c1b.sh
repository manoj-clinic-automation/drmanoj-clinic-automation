#!/bin/bash
# =============================================================================
#  install_c1b.sh · kit S182_C1b — clinic daily entry (C1 slice 1)
#  Supersedes S182_C1a, whose installer assumed the old WinSCP delivery
#  (`cd /root/finance` with kit files uploaded alongside) and therefore
#  refused — correctly, harmlessly — when run from the repo kit directory.
#
#  THIS installer runs FROM THE KIT DIRECTORY (wherever vps_deploy.sh cloned
#  it) and stages the payload into /root/finance itself. No upload step exists.
#
#  Green: SUMS gate → kit identity (F-88) → stage payload → stop service →
#         backup app AND db → marker → swap → py_compile → migration (skipped
#         if its marker setting exists) → smoke gate → service up → live probe.
#  Red  : if live files were touched, restore BOTH from the S182 backups and
#         say so; if the gate fired before anything was touched, SAY THAT
#         instead — this red branch reports what actually happened.
# =============================================================================
set -u
KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIVE=/root/finance
cd "$KIT_DIR" \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S182_C1b" ] \
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
&& { [ -n "$(sqlite3 finance.db "SELECT value FROM setting WHERE key='migration.S182_clinic'")" ] \
     || sqlite3 finance.db ".bail on" ".read finance_migration_S182_clinic.sql" ; } \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz \
&& rm -f .S182_touched \
&& echo "" && echo "S182_C1b INSTALLED — smoke green, migration in, service restarted" \
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
