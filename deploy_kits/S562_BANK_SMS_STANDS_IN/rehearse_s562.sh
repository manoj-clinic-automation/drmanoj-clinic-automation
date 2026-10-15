#!/bin/bash
# rehearse_s562.sh -- kit S562_BANK_SMS_STANDS_IN: the installer on a MADE-UP root under /tmp (never /root/finance, never the live service):
#   1. a forced red after placing (a stub journal with a Traceback) -> all four files put back byte-identically, exit 1
#   2. a green run -> placed at the TO pins, the setting row '0', the page look PAGE OK, housekeeping on made-up folders
#      (a clean one removed; one holding a phone-shaped number LEFT)
#   3. a second run -> ALREADY INSTALLED
# systemctl and journalctl are stubs; healthz and the 302 probes read the live service read-only (GET, no login).
#   bash rehearse_s562.sh            (from a copy of the kit, on the server)
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
R=/tmp/s562reh
rm -rf "$R"; mkdir -p "$R/finance/spine" "$R/finance/finance_ui" "$R/bin" "$R/hk_clean/sub" "$R/hk_number"
cp -p /root/finance/*.py "$R/finance/"; cp -p /root/finance/*.html /root/finance/*.json /root/finance/*.sql "$R/finance/" 2>/dev/null
cp -rp /root/finance/finance_ui/. "$R/finance/finance_ui/" 2>/dev/null; cp -p /root/finance/spine/*.py /root/finance/spine/*.json "$R/finance/spine/" 2>/dev/null
/usr/bin/python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" /root/finance/finance.db "$R/finance/finance.db"
printf '#!/bin/bash\necho "stub systemctl $*" >> %s/stub.log\nexit 0\n' "$R" > "$R/bin/systemctl"
printf '#!/bin/bash\necho "Traceback (most recent call last): stub"\n' > "$R/bin/journal_red"
printf '#!/bin/bash\nexit 0\n' > "$R/bin/journal_ok"
chmod +x "$R/bin/"*
echo "a made-up scratch note" > "$R/hk_clean/sub/note.txt"
printf 'call %s\n' "$(printf '9%09d' 0)" > "$R/hk_number/x.txt"          # a phone-SHAPED number, made at run time (none in this file)
md5() { md5sum "$1" | awk '{print $1}'; }
FILES="bank_standin.py bank_sms.py clinic_money.py darpan_kal.py"
before() { for f in $FILES; do printf '%s ' "$(md5 "$R/finance/$f" | cut -c1-8)"; done; }
B="$(before)"
ENVV="FIN=$R/finance DB=$R/finance/finance.db LOCK=$R/lock SYSTEMCTL=$R/bin/systemctl TMPW=$R"
echo "== 1. forced red after placing"
env $ENVV HOUSEKEEP="$R/hk_clean $R/hk_number" JOURNALCTL="$R/bin/journal_red" bash "$KDIR/install_S562_BANK_SMS_STANDS_IN.sh" > "$R/run1.txt" 2>&1; RC1=$?
grep -E "^\[|^!!|^   /tmp" "$R/run1.txt" | grep -v "^\[5/11\] WALK" | tail -9
A1="$(before)"
[ "$RC1" = 1 ] && [ "$A1" = "$B" ] && grep -q "RED after placing" "$R/run1.txt" && [ -d "$R/hk_clean" ] && R1=ok || R1=FAIL
echo "   exit $RC1; the four files now $A1(were $B) -> $R1"
echo "== 2. green"
env $ENVV HOUSEKEEP="$R/hk_clean $R/hk_number $R/hk_absent" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S562_BANK_SMS_STANDS_IN.sh" > "$R/run2.txt" 2>&1; RC2=$?
grep -E "^\[|^!!|^ +/finance|^ PAGE|DONE" "$R/run2.txt" | grep -v "^\[5/11\]   " | tail -14
SET="$(/usr/bin/python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); r=c.execute(\"SELECT value FROM setting WHERE key='bank_sms.standin_on'\").fetchone(); print(r[0] if r else 'none')" "$R/finance/finance.db")"
[ "$RC2" = 0 ] && grep -q "^ PAGE OK" "$R/run2.txt" && [ "$SET" = 0 ] && [ ! -e "$R/hk_clean" ] && [ -e "$R/hk_number" ] && R2=ok || R2=FAIL
echo "   exit $RC2; setting bank_sms.standin_on = $SET; hk_clean removed: $([ ! -e "$R/hk_clean" ] && echo yes || echo no); hk_number left: $([ -e "$R/hk_number" ] && echo yes || echo no) -> $R2"
echo "== 3. second run"
env $ENVV HOUSEKEEP="$R/hk_absent" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S562_BANK_SMS_STANDS_IN.sh" > "$R/run3.txt" 2>&1; RC3=$?
grep -E "ALREADY" "$R/run3.txt"
[ "$RC3" = 0 ] && grep -q "ALREADY INSTALLED" "$R/run3.txt" && R3=ok || R3=FAIL
echo "   exit $RC3 -> $R3"
echo "stub systemctl calls: $(tr '\n' ';' < "$R/stub.log")"
echo "live files untouched: $(md5sum /root/finance/bank_standin.py /root/finance/bank_sms.py /root/finance/clinic_money.py /root/finance/darpan_kal.py | awk '{printf "%s ", substr($1,1,8)}')"
if [ "$R1$R2$R3" = okokok ]; then echo "REHEARSAL OK S562"; rm -rf "$R"; exit 0; fi
echo "REHEARSAL RED S562 (logs in $R)"; exit 1
