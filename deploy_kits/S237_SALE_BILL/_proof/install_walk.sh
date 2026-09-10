#!/bin/bash
# LIVE-SHAPE WALK for install_sale_bill.sh.
# Runs the real installer against a real filesystem, with a fake FINANCE_DIR and
# a real copy of a database, and asserts above all that IT WRITES NO ROW.
set -u
KIT="$(cd "$(dirname "$0")/.." && pwd)"
F=0; ck(){ if [ "$2" = "1" ]; then echo "  PASS $1"; else echo "  FAIL $1"; F=$((F+1)); fi; }
FIN=/tmp/fakefinance; rm -rf "$FIN"; mkdir -p "$FIN"
# a database that must come back untouched
python3 - <<'PY'
import sqlite3
c=sqlite3.connect("/tmp/fakefinance/finance.db")
c.execute("CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, bill_no TEXT)")
c.execute("INSERT INTO sale_line_item (bill_no) VALUES ('A1')")
c.commit()
PY
DBSUM=$(md5sum "$FIN/finance.db" | awk '{print $1}')

echo "== 1 · GREEN PATH (no previous file, no exports on this box) =="
( cd "$KIT" && FINANCE_DIR=$FIN bash install_sale_bill.sh ) > /tmp/sb1.log 2>&1; rc=$?
ck "exits 0" "$([ $rc -eq 0 ] && echo 1 || echo 0)"
ck "sale_bill.py placed" "$([ -f "$FIN/sale_bill.py" ] && echo 1 || echo 0)"
ck "placed copy matches the kit" "$([ "$(md5sum $FIN/sale_bill.py|awk '{print $1}')" = "$(md5sum $KIT/sale_bill.py|awk '{print $1}')" ] && echo 1 || echo 0)"
ck "selftest ran clean" "$(grep -q '0 failures' /tmp/sb1.log && echo 1 || echo 0)"
ck "⭐ THE DATABASE WAS NOT TOUCHED" "$([ "$(md5sum $FIN/finance.db|awk '{print $1}')" = "$DBSUM" ] && echo 1 || echo 0)"
ck "⭐ no sale_bill table was created" "$(python3 -c "
import sqlite3,sys
c=sqlite3.connect('$FIN/finance.db')
print(1 if not c.execute(\"select name from sqlite_master where name='sale_bill'\").fetchall() else 0)")"
ck "it says the database is untouched" "$(grep -q 'DATABASE UNTOUCHED' /tmp/sb1.log && echo 1 || echo 0)"
ck "it ran --locate for the owner" "$(grep -q 'WHERE ARE THE EXPORTS' /tmp/sb1.log && echo 1 || echo 0)"
ck "with no exports it says so plainly, not an error" "$(grep -q 'not under any of the folders it knows about' /tmp/sb1.log && echo 1 || echo 0)"

echo "== 2 · GREEN PATH with exports present (must print the numbers, still write nothing) =="
EXP=/mnt/user-data/uploads/Downloads/margsync/MargArchive/SALE_BILLWISE
if [ -d "$EXP" ]; then
  mkdir -p "$FIN/scans" && cp "$EXP"/2026-09/*20260909-221733*.XLS "$FIN/scans/" 2>/dev/null
  cp /mnt/user-data/uploads/dr-manoj-git/drmanoj-clinic-automation/finance/marg_report.py "$FIN/" 2>/dev/null
  ( cd "$KIT" && FINANCE_DIR=$FIN bash install_sale_bill.sh ) > /tmp/sb2.log 2>&1; rc=$?
  ck "exits 0" "$([ $rc -eq 0 ] && echo 1 || echo 0)"
  ck "it found the exports by itself" "$(grep -q 'use: --scan' /tmp/sb2.log && echo 1 || echo 0)"
  ck "it printed the discount it would keep" "$(grep -q 'DISCOUNT' /tmp/sb2.log && echo 1 || echo 0)"
  ck "⭐ STILL no row written" "$([ "$(md5sum $FIN/finance.db|awk '{print $1}')" = "$DBSUM" ] && echo 1 || echo 0)"
  ck "it printed the one line that WOULD write" "$(grep -q -- '--write' /tmp/sb2.log && echo 1 || echo 0)"
  ck "the previous copy was backed up" "$(ls $FIN/sale_bill.py.bak_S237_* >/dev/null 2>&1 && echo 1 || echo 0)"
else
  echo "  (skipped — archive not staged)"
fi

echo "== 3 · RED PATH, identity gate — a previous file MUST survive =="
echo "# PREVIOUS" > "$FIN/sale_bill.py"; PREV=$(md5sum "$FIN/sale_bill.py"|awk '{print $1}')
rm -rf /tmp/sbred && cp -r "$KIT" /tmp/sbred
sed -i 's/^S237_SALE_BILL .*/S237_SALE_BILL deadbeefdeadbeefdeadbeefdeadbeef/' /tmp/sbred/KIT_ID.txt
python3 - <<'PY'
import hashlib
p='/tmp/sbred/SUMS.md5'
rows=[l.split('  ',1)[1].strip() for l in open(p)]
open(p,'w').writelines('%s  %s\n'%(hashlib.md5(open('/tmp/sbred/'+n,'rb').read()).hexdigest(),n) for n in rows)
PY
( cd /tmp/sbred && FINANCE_DIR=$FIN bash install_sale_bill.sh ) > /tmp/sb3.log 2>&1; rc=$?
ck "exits 1" "$([ $rc -eq 1 ] && echo 1 || echo 0)"
ck "it is the IDENTITY gate that refuses, not the hash gate" "$(grep -q 'F-88' /tmp/sb3.log && ! grep -q 'SUMS.md5 gate failed' /tmp/sb3.log && echo 1 || echo 0)"
ck "⭐ THE PREVIOUS FILE SURVIVED" "$([ "$(md5sum $FIN/sale_bill.py|awk '{print $1}')" = "$PREV" ] && echo 1 || echo 0)"
ck "says no database row was written" "$(grep -q 'NO DATABASE ROW WAS WRITTEN' /tmp/sb3.log && echo 1 || echo 0)"
ck "⭐ database still untouched" "$([ "$(md5sum $FIN/finance.db|awk '{print $1}')" = "$DBSUM" ] && echo 1 || echo 0)"

echo "== 4 · RED PATH, wrong box (no finance dir) =="
( cd "$KIT" && FINANCE_DIR=/tmp/no_such_finance bash install_sale_bill.sh ) > /tmp/sb4.log 2>&1; rc=$?
ck "exits 1" "$([ $rc -eq 1 ] && echo 1 || echo 0)"
ck "says the finance folder is missing" "$(grep -q 'is this the finance box' /tmp/sb4.log && echo 1 || echo 0)"

rm -rf "$FIN" /tmp/sbred
echo ""
echo "INSTALLER WALK: $F failure(s)"
exit $([ $F -eq 0 ] && echo 0 || echo 1)
