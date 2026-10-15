#!/bin/bash
# rehearse_s565.sh -- kit S565_DARPAN_SMS_AND_CLAUDE_BILLS: the installer on a MADE-UP root under /tmp (never /root/finance, never the live service):
#   1. a forced red after placing (a stub journal with a Traceback) -> both files put back byte-identically, exit 1
#   2. a green run -> placed at the TO pins, the page look PAGE OK
#   3. a second run -> ALREADY INSTALLED
# systemctl and journalctl are stubs; healthz and the 302 probe read the live service read-only (GET, no login).
#   bash rehearse_s565.sh            (from a copy of the kit, on the server)
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
R=/tmp/s565reh
rm -rf "$R"; mkdir -p "$R/finance/spine" "$R/finance/finance_ui" "$R/bin"
cp -p /root/finance/*.py "$R/finance/"; cp -p /root/finance/*.html /root/finance/*.json /root/finance/*.sql "$R/finance/" 2>/dev/null
cp -rp /root/finance/finance_ui/. "$R/finance/finance_ui/" 2>/dev/null; cp -p /root/finance/spine/*.py /root/finance/spine/*.json "$R/finance/spine/" 2>/dev/null
/usr/bin/python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" /root/finance/finance.db "$R/finance/finance.db"
printf '#!/bin/bash\necho "stub systemctl $*" >> %s/stub.log\nexit 0\n' "$R" > "$R/bin/systemctl"
printf '#!/bin/bash\necho "Traceback (most recent call last): stub"\n' > "$R/bin/journal_red"
printf '#!/bin/bash\nexit 0\n' > "$R/bin/journal_ok"
chmod +x "$R/bin/"*
md5() { md5sum "$1" | awk '{print $1}'; }
BH="$(md5 "$R/finance/darpan_kal.html")"; BP="$(md5 "$R/finance/darpan_kal.py")"
ENVV="FIN=$R/finance DB=$R/finance/finance.db LOCK=$R/lock SYSTEMCTL=$R/bin/systemctl TMPW=$R"
echo "== 1. forced red after placing"
env $ENVV JOURNALCTL="$R/bin/journal_red" bash "$KDIR/install_S565_DARPAN_SMS_AND_CLAUDE_BILLS.sh" > "$R/run1.txt" 2>&1; RC1=$?
grep -E "^\[|^!!|^   /root|^   /tmp|^   after" "$R/run1.txt" | grep -v "^\[5/10\] WALK" | tail -10
A1H="$(md5 "$R/finance/darpan_kal.html")"; A1P="$(md5 "$R/finance/darpan_kal.py")"
[ "$RC1" = 1 ] && [ "$A1H" = "$BH" ] && [ "$A1P" = "$BP" ] && grep -q "RED after placing" "$R/run1.txt" && R1=ok || R1=FAIL
echo "   exit $RC1; darpan_kal.html now ${A1H:0:8} (was ${BH:0:8}), darpan_kal.py now ${A1P:0:8} (was ${BP:0:8}) -> $R1"
echo "== 2. green"
env $ENVV JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S565_DARPAN_SMS_AND_CLAUDE_BILLS.sh" > "$R/run2.txt" 2>&1; RC2=$?
grep -E "^\[|^!!|^ +/finance|^ PAGE|DONE" "$R/run2.txt" | grep -v "^\[5/10\]   " | tail -14
A2H="$(md5 "$R/finance/darpan_kal.html")"; A2P="$(md5 "$R/finance/darpan_kal.py")"
[ "$RC2" = 0 ] && grep -q "^ PAGE OK" "$R/run2.txt" && [ "$A2H" = 75d5a5b51b017abd5ad3aa408609a1ff ] && [ "$A2P" = 8128598f745fca48a08472905f47da97 ] && R2=ok || R2=FAIL
echo "   exit $RC2; darpan_kal.html ${A2H:0:8}, darpan_kal.py ${A2P:0:8} -> $R2"
echo "== 3. second run"
env $ENVV JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S565_DARPAN_SMS_AND_CLAUDE_BILLS.sh" > "$R/run3.txt" 2>&1; RC3=$?
grep -E "ALREADY" "$R/run3.txt"
[ "$RC3" = 0 ] && grep -q "ALREADY INSTALLED" "$R/run3.txt" && R3=ok || R3=FAIL
echo "   exit $RC3 -> $R3"
echo "stub systemctl calls: $(tr '\n' ';' < "$R/stub.log")"
echo "live files untouched: $(md5sum /root/finance/darpan_kal.html /root/finance/darpan_kal.py | awk '{printf "%s ", substr($1,1,8)}')"
if [ "$R1$R2$R3" = okokok ]; then echo "REHEARSAL OK S565"; rm -rf "$R"; exit 0; fi
echo "REHEARSAL RED S565 (logs in $R)"; exit 1
