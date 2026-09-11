#!/usr/bin/env bash
set -u
K="$(cd "$(dirname "$0")/.." && pwd)"; T=$(mktemp -d); mkdir -p $T/bin $T/fin
cat > $T/bin/crontab <<'S'
#!/bin/bash
F="$CRON_FILE"; [ -n "${CRON_FAIL:-}" ] && [ "$1" = "-" ] && exit 1
if [ "$1" = "-l" ]; then [ -f "$F" ] && cat "$F" || exit 1; elif [ "$1" = "-" ]; then cat > "$F"; else cp "$1" "$F"; fi
S
chmod +x $T/bin/*; export PATH="$T/bin:$PATH" CRON_FILE=$T/cron FIN_DIR=$T/fin TZ=Asia/Kolkata
fresh(){ touch $T/fin/docterz_ingest.py; printf '5 8 * * * python freshness.py --shout\n25 9 * * * /root/wa/venv/bin/python3 -B /root/finance/docterz_ingest.py >> /root/finance/logs/docterz_ingest.log 2>&1\n0 2 * * * backup.sh\n' > $T/cron; }
p=0; f=0; chk(){ if eval "$2"; then p=$((p+1)); echo "  ok   $1"; else f=$((f+1)); echo "  FAIL $1"; fi; }
fresh; bash "$K/install_docterz_schedule.sh" > $T/o1 2>&1; rc=$?
chk "green" "[ $rc = 0 ] && grep -q GREEN $T/o1"
chk "4 docterz lines" "[ \$(grep -c docterz_ingest.py $T/cron) = 4 ]"
chk "old 25 9 line gone" "! grep -q '^25 9 ' $T/cron"
chk "every-10-min from 09:30" "grep -q '^30-50/10 9 ' $T/cron && grep -q '^\*/10 10-11 ' $T/cron && ! grep -q ' 6-11 ' $T/cron"
chk "noon + 13:40/19:40" "grep -q '^0 12 ' $T/cron && grep -q '^40 13,19 ' $T/cron"
chk "other lines kept" "grep -q freshness.py $T/cron && grep -q backup.sh $T/cron"
bash "$K/install_docterz_schedule.sh" > $T/o2 2>&1; chk "re-run still 4 lines" "[ \$(grep -c docterz_ingest.py $T/cron) = 4 ]"
fresh; cp $T/cron $T/before; CRON_FAIL=1 bash "$K/install_docterz_schedule.sh" > $T/o3 2>&1; rc=$?
chk "write failure -> restored" "[ $rc = 1 ] && cmp -s $T/before $T/cron"
fresh; cp $T/cron $T/before; TZ=UTC bash "$K/install_docterz_schedule.sh" > $T/o4 2>&1; rc=$?
chk "non-IST clock refused" "[ $rc = 1 ] && cmp -s $T/before $T/cron"
echo; sed 's/^/  | /' $T/o1; echo "walk: $p passed, $f failed"; rm -rf $T; [ $f = 0 ]
