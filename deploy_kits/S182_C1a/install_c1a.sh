#!/bin/bash
# =============================================================================
#  install_c1a.sh · kit S182_C1a — clinic daily entry (C1 slice 1) · S177 shape
#  ONE gate chain, no numbered steps. Run from /root/finance with the kit files
#  uploaded alongside (finance_app.py.new, finance_ui/finance_entry_clinic.html.new,
#  finance_migration_S182_clinic.sql, KIT_ID.txt, SUMS.md5).
#
#  Green path: md5 gate → kit identity (F-88) → stop service → backup app AND
#              db → swap in the new build → py_compile → migration (skipped if
#              its marker row already exists) → smoke gate (runs on a throwaway
#              copy; on the REAL store every check must be green) → service up
#              → live probe.
#  Red path  : anything fails → app AND db restored from the S182 .bak copies,
#              the old build restarted, non-zero exit. Nothing half-installed.
# =============================================================================
cd /root/finance \
&& md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "S182_C1a" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum finance_app.py.new | awk '{print $1}')" ] \
&& systemctl stop clinic-finance \
&& cp finance_app.py finance_app.py.bak_S182 \
&& cp finance.db finance.db.bak_S182 \
&& mv finance_app.py.new finance_app.py \
&& mv finance_ui/finance_entry_clinic.html.new finance_ui/finance_entry_clinic.html \
&& python3 -m py_compile finance_app.py \
&& { [ -n "$(sqlite3 finance.db "SELECT value FROM setting WHERE key='migration.S182_clinic'")" ] \
     || sqlite3 finance.db ".bail on" ".read finance_migration_S182_clinic.sql" ; } \
&& python3 finance_app.py --selftest \
&& systemctl start clinic-finance \
&& sleep 2 && curl -sf http://127.0.0.1:8106/finance/healthz \
&& echo "" && echo "S182_C1a INSTALLED — smoke green, migration in, service restarted" \
|| { echo "RED — restoring the pre-S182 build and database"; \
     cp -f finance_app.py.bak_S182 finance_app.py 2>/dev/null; \
     cp -f finance.db.bak_S182 finance.db 2>/dev/null; \
     rm -f finance_ui/finance_entry_clinic.html; \
     systemctl start clinic-finance; \
     echo "restored — the clinic slice is NOT installed"; exit 1; }
