#!/bin/bash
# rehearse_s564.sh -- kit S564_SMS_KEY_OWNER_ONLY: the installer on a MADE-UP root under /tmp (never /root/finance, never the live service),
# with a MADE-UP key file (never the phone's):
#   1. a forced red after placing (a stub journal with a Traceback) -> the file put back byte-identically, exit 1
#   2. a green run -> placed at the TO pin, the page look PAGE OK, housekeeping on made-up folders
#      (a clean one removed; one holding a phone-shaped number LEFT; one holding the made-up key LEFT)
#   3. a second run -> ALREADY INSTALLED
# systemctl and journalctl are stubs; healthz and the 302 probe read the live service read-only (GET, no login).
#   bash rehearse_s564.sh            (from a copy of the kit, on the server)
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
R=/tmp/s564reh
rm -rf "$R"; mkdir -p "$R/finance/spine" "$R/finance/finance_ui" "$R/bin" "$R/hk_clean/sub" "$R/hk_number" "$R/hk_key"
cp -p /root/finance/*.py "$R/finance/"; cp -p /root/finance/*.html /root/finance/*.json /root/finance/*.sql "$R/finance/" 2>/dev/null
cp -rp /root/finance/finance_ui/. "$R/finance/finance_ui/" 2>/dev/null; cp -p /root/finance/spine/*.py /root/finance/spine/*.json "$R/finance/spine/" 2>/dev/null
/usr/bin/python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" /root/finance/finance.db "$R/finance/finance.db"
echo "w564-rehearsal-made-up-key-$(date +%s)" > "$R/finance/bank_sms.key"; chmod 600 "$R/finance/bank_sms.key"
printf '#!/bin/bash\necho "stub systemctl $*" >> %s/stub.log\nexit 0\n' "$R" > "$R/bin/systemctl"
printf '#!/bin/bash\necho "Traceback (most recent call last): stub"\n' > "$R/bin/journal_red"
printf '#!/bin/bash\nexit 0\n' > "$R/bin/journal_ok"
chmod +x "$R/bin/"*
echo "a made-up scratch note" > "$R/hk_clean/sub/note.txt"
printf 'call %s\n' "$(printf '9%09d' 0)" > "$R/hk_number/x.txt"          # a phone-SHAPED number, made at run time (none in this file)
{ echo "a log line"; cat "$R/finance/bank_sms.key"; } > "$R/hk_key/log.txt"   # the MADE-UP key copied into a scratch log
md5() { md5sum "$1" | awk '{print $1}'; }
B="$(md5 "$R/finance/bank_sms.py")"
ENVV="FIN=$R/finance DB=$R/finance/finance.db LOCK=$R/lock SYSTEMCTL=$R/bin/systemctl TMPW=$R"
echo "== 1. forced red after placing"
env $ENVV HOUSEKEEP="$R/hk_clean $R/hk_number $R/hk_key" JOURNALCTL="$R/bin/journal_red" bash "$KDIR/install_S564_SMS_KEY_OWNER_ONLY.sh" > "$R/run1.txt" 2>&1; RC1=$?
grep -E "^\[|^!!|^   /tmp" "$R/run1.txt" | grep -v "^\[5/10\] WALK" | tail -9
A1="$(md5 "$R/finance/bank_sms.py")"
[ "$RC1" = 1 ] && [ "$A1" = "$B" ] && grep -q "RED after placing" "$R/run1.txt" && [ -d "$R/hk_clean" ] && R1=ok || R1=FAIL
echo "   exit $RC1; bank_sms.py now ${A1:0:8} (was ${B:0:8}) -> $R1"
echo "== 2. green"
env $ENVV HOUSEKEEP="$R/hk_clean $R/hk_number $R/hk_key $R/hk_absent" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S564_SMS_KEY_OWNER_ONLY.sh" > "$R/run2.txt" 2>&1; RC2=$?
grep -E "^\[|^!!|^ +/finance|^ PAGE|DONE" "$R/run2.txt" | grep -v "^\[5/10\]   " | tail -14
A2="$(md5 "$R/finance/bank_sms.py")"
[ "$RC2" = 0 ] && grep -q "^ PAGE OK" "$R/run2.txt" && [ "$A2" = aa5278403ec85c898d808486e4c3cde3 ] && [ ! -e "$R/hk_clean" ] && [ -e "$R/hk_number" ] && [ -e "$R/hk_key" ] \
  && grep -q "hk_key: 1 file(s), 0 secret-shaped, 1 holding the key" "$R/run2.txt" && R2=ok || R2=FAIL
echo "   exit $RC2; bank_sms.py ${A2:0:8}; hk_clean removed: $([ ! -e "$R/hk_clean" ] && echo yes || echo no); hk_number left: $([ -e "$R/hk_number" ] && echo yes || echo no); hk_key left: $([ -e "$R/hk_key" ] && echo yes || echo no) -> $R2"
echo "== 3. second run"
env $ENVV HOUSEKEEP="$R/hk_absent" JOURNALCTL="$R/bin/journal_ok" bash "$KDIR/install_S564_SMS_KEY_OWNER_ONLY.sh" > "$R/run3.txt" 2>&1; RC3=$?
grep -E "ALREADY" "$R/run3.txt"
[ "$RC3" = 0 ] && grep -q "ALREADY INSTALLED" "$R/run3.txt" && R3=ok || R3=FAIL
echo "   exit $RC3 -> $R3"
echo "stub systemctl calls: $(tr '\n' ';' < "$R/stub.log")"
echo "live files untouched: $(md5sum /root/finance/bank_sms.py /root/finance/bank_standin.py | awk '{printf "%s ", substr($1,1,8)}')"
if [ "$R1$R2$R3" = okokok ]; then echo "REHEARSAL OK S564"; rm -rf "$R"; exit 0; fi
echo "REHEARSAL RED S564 (logs in $R)"; exit 1
