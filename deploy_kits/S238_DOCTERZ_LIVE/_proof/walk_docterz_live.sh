#!/usr/bin/env bash
# walk_docterz_live.sh -- the installer offline: the REAL pinned reader file (so the pin gate
# is real), a fake python that pretends to be the reader when asked to run it (real python3 for
# everything else), a fake crontab. Paths: green, re-run (no duplicate line), reader failure
# (nothing scheduled), wrong reader file (refused), tampered kit.
set -u
K="$(cd "$(dirname "$0")/.." && pwd)"; READER="$1"
T=$(mktemp -d); mkdir -p $T/bin $T/fin
cat > $T/bin/fakepy <<'S'
#!/bin/bash
if [ "$1" = "-B" ] && [[ "$2" == *docterz_ingest.py ]]; then
  echo "Drive: 160 day files in the folder"; echo "  Staff_Action_Today_2026-09-05.xlsx -> 2026-09-04  Rs 41200  38 lines"
  echo "read 6, skipped 154 unchanged, failed 0; clinic_day_revenue now holds 74 days and 2400 lines"
  [ -n "${FAKE_JUNE:-}" ] && echo "  FAILED  Staff_Action_Today_2026-06-11.xlsx     no 'Day Revenue' sheet (sheets: Call Sheet, Vacation Notice List)"
  [ -n "${FAKE_OTHER:-}" ] && echo "  FAILED  Staff_Action_Today_2026-09-12.xlsx     bad banner"
  exit ${FAKE_RC:-0}
fi
exec python3 "$@"
S
cat > $T/bin/crontab <<'S'
#!/bin/bash
F="$CRON_FILE"
if [ "$1" = "-l" ]; then [ -f "$F" ] && cat "$F" || exit 1; elif [ "$1" = "-" ]; then cat > "$F"; else cp "$1" "$F"; fi
S
chmod +x $T/bin/*; export PATH="$T/bin:$PATH" CRON_FILE=$T/cron FIN_DIR=$T/fin PY=$T/bin/fakepy
fresh(){ rm -rf $T/fin; mkdir -p $T/fin; cp "$READER" $T/fin/docterz_ingest.py
  python3 -c "import sqlite3;c=sqlite3.connect('$T/fin/finance.db');c.execute('create table clinic_day_revenue(business_date text, taken_at text)');c.execute(\"insert into clinic_day_revenue values('2026-09-03','x')\");c.commit()"
  printf '5 8 * * * /root/wa/venv/bin/python3 freshness.py --shout\n' > $T/cron; }
p=0; f=0; chk(){ if eval "$2"; then p=$((p+1)); echo "  ok   $1"; else f=$((f+1)); echo "  FAIL $1"; fi; }
echo "== green"; fresh; bash "$K/install_docterz_live.sh" > $T/o1 2>&1; rc=$?
chk "exit 0" "[ $rc = 0 ]"; chk "GREEN" "grep -q GREEN $T/o1"
chk "one docterz line added" "[ \$(grep -c docterz_ingest.py $T/cron) = 1 ]"
chk "old cron line kept" "grep -q freshness.py $T/cron"
chk "db backup made" "ls $T/fin/finance.db.bak_S238_DOCTERZ_LIVE_* >/dev/null 2>&1"
chk "before/after printed" "grep -q 'before: 1 days, newest 2026-09-03' $T/o1"
chk "log written" "grep -q 'catch-up by S238_DOCTERZ_LIVE' $T/fin/logs/docterz_ingest.log"
echo "== re-run"; bash "$K/install_docterz_live.sh" > $T/o2 2>&1; rc=$?
chk "re-run exit 0" "[ $rc = 0 ]"; chk "still one line" "[ \$(grep -c docterz_ingest.py $T/cron) = 1 ]"; chk "says already" "grep -q 'already in the crontab' $T/o2"
echo "== reader failure"; fresh; FAKE_RC=1 bash "$K/install_docterz_live.sh" > $T/o3 2>&1; rc=$?
chk "exit 1" "[ $rc = 1 ]"; chk "nothing scheduled" "! grep -q docterz_ingest.py $T/cron"; chk "backup kept" "ls $T/fin/finance.db.bak_* >/dev/null 2>&1"
echo "== June workbooks only (accepted)"; fresh; FAKE_RC=1 FAKE_JUNE=1 bash "$K/install_docterz_live.sh" > $T/o6 2>&1; rc=$?
chk "june-only accepted" "[ $rc = 0 ] && grep -q 'skipped, as expected' $T/o6 && [ \$(grep -c docterz_ingest.py $T/cron) = 1 ]"
echo "== June + another failure (refused)"; fresh; FAKE_RC=1 FAKE_JUNE=1 FAKE_OTHER=1 bash "$K/install_docterz_live.sh" > $T/o7 2>&1; rc=$?
chk "other failure refused" "[ $rc = 1 ] && ! grep -q docterz_ingest.py $T/cron"
echo "== wrong reader file"; fresh; echo "#x" >> $T/fin/docterz_ingest.py; bash "$K/install_docterz_live.sh" > $T/o4 2>&1; rc=$?
chk "refused" "[ $rc = 1 ] && grep -q 'not the S223_SPLIT_LEGS reader' $T/o4 && ! grep -q docterz_ingest.py $T/cron && ! ls $T/fin/finance.db.bak_* >/dev/null 2>&1"
echo "== tampered kit"; fresh; cp -r "$K" $T/k2; echo x >> $T/k2/install_docterz_live.sh; bash $T/k2/install_docterz_live.sh > $T/o5 2>&1; rc=$?
chk "tampered refused" "[ $rc = 1 ] && grep -q 'SUMS.md5 gate failed' $T/o5"
echo; sed 's/^/  | /' $T/o1; echo "walk: $p passed, $f failed"; rm -rf $T; [ $f = 0 ]
