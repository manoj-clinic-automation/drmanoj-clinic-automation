#!/bin/bash
# =============================================================================
#  install_m2a.sh · kit S183_M2a — turn ON the Marg pharmacy feed (code + config)
#
#  WHAT THIS INSTALLS  (three things; NO patient data — F-31/D320)
#    1. /root/finance/marg_report.py     — REPLACED: now reads .xlsx as well as
#                                          .xls (staff save exports through Excel).
#                                          The .xls path is byte-for-byte unchanged.
#    2. /root/finance/marg_backfill.py   — REPLACED (v1 -> v2): writes BOTH
#                                          sale_item AND sale_line_item per day.
#    3. finance.db                        — migration S183_marg_map: 7-field column
#                                          map + source activated. Additive,
#                                          reversible, moves NO money.
#
#  WHAT IT DOES NOT DO
#    No service is restarted — nothing on the box imports marg_report (only the
#    standalone backfill driver uses it), so the running finance app is untouched.
#    It does NOT run the backfill. That is a separate, owner-driven step once the
#    export files are on the box (they are PHI and never travel through git).
#
#  Shape per D317: preflight -> SUMS -> KIT_ID -> live-file currency gate ->
#  smoke BEFORE any swap -> backup db -> swap files -> apply migration -> verify
#  -> honest red that restores what it touched.
# =============================================================================
set -u

KIT_NAME="S183_M2a"
FIN=/root/finance
PY=/usr/bin/python3
EXPECT_LIVE_MD5="28b47d447cfd966411742055717a5c56"   # marg_report.py pinned live (S180)

for c in md5sum awk cp mv; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing before touching anything"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
[ -f "$FIN/marg_report.py" ] || { echo "!! preflight: $FIN/marg_report.py not found — refusing"; exit 1; }
[ -f "$FIN/finance.db" ]     || { echo "!! preflight: $FIN/finance.db not found — refusing"; exit 1; }
# the new parser needs openpyxl to read .xlsx; finance_upi already uses it, so it
# should be present — check rather than assume.
"$PY" -c "import openpyxl, xlrd, sqlite3" 2>/dev/null \
  || { echo "!! preflight: python3 cannot import openpyxl/xlrd — refusing."; \
       echo "   install with: $PY -m pip install openpyxl xlrd"; exit 1; }

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KIT_DIR" || exit 1

LIVE_NOW="$(md5sum "$FIN/marg_report.py" | awk '{print $1}')"

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum marg_report.py | awk '{print $1}')" ] \
&& { [ "$LIVE_NOW" = "$EXPECT_LIVE_MD5" ] || {
       echo ""
       echo "!! REFUSING — the live marg_report.py is NOT the file this kit was built against."
       echo "     live now : $LIVE_NOW"
       echo "     expected : $EXPECT_LIVE_MD5"
       echo "   Nothing has been touched. Send the current $FIN/marg_report.py back"
       echo "   and the kit will be rebuilt on top of it (F-97 discipline)."
       exit 1; }; } \
&& echo "-- integrity + currency OK (live marg_report.py = $LIVE_NOW)" \
&& echo "" \
&& echo "-- SMOKE (before touching anything): compile + parser selftest on the NEW files" \
&& "$PY" -m py_compile marg_report.py marg_backfill.py \
&& "$PY" -c "import sys; sys.path.insert(0,'.'); import marg_report as M; sys.exit(0 if M.selftest('.') else 1)" \
&& echo "-- smoke green" \
&& STAMP="$(date +%Y%m%d_%H%M%S)" \
&& cp -p "$FIN/finance.db" "$FIN/finance.db.bak_S183M2_$STAMP" \
&& echo "-- finance.db backed up: finance.db.bak_S183M2_$STAMP" \
&& cp -p "$FIN/marg_report.py"   "$FIN/marg_report.py.bak_S183M2" \
&& { [ -f "$FIN/marg_backfill.py" ] && cp -p "$FIN/marg_backfill.py" "$FIN/marg_backfill.py.bak_S183M2" || true; } \
&& touch "$FIN/.S183M2_touched" \
&& cp marg_report.py   "$FIN/marg_report.py" \
&& cp marg_backfill.py "$FIN/marg_backfill.py" \
&& echo "-- files swapped; applying the migration (additive, atomic, reversible)" \
&& "$PY" -c "import sqlite3;c=sqlite3.connect('$FIN/finance.db');c.executescript(open('finance_migration_S183_marg_map.sql').read());c.commit();c.close()" \
&& VERIFY="$("$PY" - <<PYEOF
import sqlite3
c=sqlite3.connect('$FIN/finance.db')
mark=c.execute("select value from setting where key='migration.S183_marg_map'").fetchone()
src=c.execute("select active from ingest_source where unit='medical' and adapter='marg_export'").fetchone()
n=c.execute("select count(*) from ingest_column_map m join ingest_source s on s.id=m.source_id where s.unit='medical' and s.adapter='marg_export'").fetchone()[0]
ok = (mark and mark[0]=='applied') and (src and src[0]==1) and n==7
print('OK' if ok else 'BAD marker=%s active=%s rows=%s'%(mark,src,n))
PYEOF
)" \
&& [ "$VERIFY" = "OK" ] \
&& "$PY" -c "import sys; sys.path.insert(0,'$FIN'); import marg_report; print('-- new marg_report imports from the box OK')" \
&& rm -f "$FIN/.S183M2_touched" \
&& echo "" \
&& echo "=============================================================" \
&& echo " $KIT_NAME INSTALLED" \
&& echo "   marg_report.py  -> reads .xls AND .xlsx (xls path unchanged)" \
&& echo "   marg_backfill.py -> v2 (bills + drug lines)" \
&& echo "   migration S183_marg_map -> column map + source active, verified" \
&& echo "   backups: marg_report.py.bak_S183M2 · finance.db.bak_S183M2_$STAMP" \
&& echo "   NO service restarted (nothing imports marg_report)." \
&& echo "=============================================================" \
&& echo "" \
&& echo " NEXT (owner-driven, not done here): put the Marg export files on the box" \
&& echo " and run the backfill — DRY RUN first, then --apply:" \
&& echo "     $PY $FIN/marg_backfill.py <export.xls|.xlsx>" \
&& echo "     $PY $FIN/marg_backfill.py <export.xls|.xlsx> --apply" \
&& echo " The files are PHI — keep them off git (F-31/D320); delete after." \
&& echo "" \
|| { echo ""; \
     echo "RED — install did not complete."; \
     if [ -f "$FIN/.S183M2_touched" ]; then \
        echo "   live files WERE touched — restoring from .bak_S183M2:"; \
        cp -f "$FIN/marg_report.py.bak_S183M2" "$FIN/marg_report.py" && echo "   marg_report.py restored"; \
        [ -f "$FIN/marg_backfill.py.bak_S183M2" ] && cp -f "$FIN/marg_backfill.py.bak_S183M2" "$FIN/marg_backfill.py" && echo "   marg_backfill.py restored"; \
        echo "   NOTE: if the migration had already applied it is additive, idempotent"; \
        echo "   and reversible (rollback block at the foot of the .sql); finance.db"; \
        echo "   backup is finance.db.bak_S183M2_* regardless."; \
        rm -f "$FIN/.S183M2_touched"; \
     else \
        echo "   the gate fired BEFORE anything live was touched — nothing to restore."; \
     fi; \
     exit 1; }
