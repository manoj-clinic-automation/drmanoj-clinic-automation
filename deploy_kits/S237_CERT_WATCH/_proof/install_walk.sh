#!/bin/bash
# LIVE-SHAPE WALK for install_cert_watch.sh.
# Runs the real installer three times against a real filesystem, with a stub
# `systemctl` on PATH so nothing systemd-side actually happens. Asserts the
# green path installs and does NOT enable the timer, and that BOTH red paths
# leave a pre-existing /root/wa/cert_watch.py completely untouched.
set -u
KIT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p /tmp/stub && printf '#!/bin/bash\necho "[stub systemctl] $*"\nexit 0\n' > /tmp/stub/systemctl && chmod +x /tmp/stub/systemctl
export PATH=/tmp/stub:$PATH
F=0; ck(){ if [ "$2" = "1" ]; then echo "  PASS $1"; else echo "  FAIL $1"; F=$((F+1)); fi; }

echo "== 1 · GREEN PATH (no previous file) =="
rm -f /root/wa/cert_watch.py /etc/systemd/system/clinic-certwatch.*
( cd "$KIT" && bash install_cert_watch.sh ) > /tmp/w1.log 2>&1; rc=$?
ck "exits 0" "$([ $rc -eq 0 ] && echo 1 || echo 0)"
ck "cert_watch.py placed" "$([ -f /root/wa/cert_watch.py ] && echo 1 || echo 0)"
ck "placed copy matches the kit" "$([ "$(md5sum /root/wa/cert_watch.py|awk '{print $1}')" = "$(md5sum "$KIT/cert_watch.py"|awk '{print $1}')" ] && echo 1 || echo 0)"
ck "both units placed" "$([ -f /etc/systemd/system/clinic-certwatch.timer ] && [ -f /etc/systemd/system/clinic-certwatch.service ] && echo 1 || echo 0)"
ck "selftest ran clean" "$(grep -q '0 failures' /tmp/w1.log && echo 1 || echo 0)"
ck "timer was NOT enabled by the installer" "$(grep -qE '^\[stub systemctl\] enable' /tmp/w1.log && echo 0 || echo 1)"
ck "the enable line is printed for the owner" "$(grep -q 'enable --now clinic-certwatch.timer' /tmp/w1.log && echo 1 || echo 0)"

echo "== 2 · RED PATH, identity gate (a previous file MUST survive) =="
echo "# PREVIOUS VERSION MARKER" > /root/wa/cert_watch.py
PREV=$(md5sum /root/wa/cert_watch.py | awk '{print $1}')
rm -rf /tmp/redkit && cp -r "$KIT" /tmp/redkit
sed -i 's/^S237_CERT_WATCH .*/S237_CERT_WATCH deadbeefdeadbeefdeadbeefdeadbeef/' /tmp/redkit/KIT_ID.txt
python3 - <<'PY'
import hashlib
p='/tmp/redkit/SUMS.md5'
rows=[l.split('  ',1)[1].strip() for l in open(p)]
open(p,'w').writelines('%s  %s\n'%(hashlib.md5(open('/tmp/redkit/'+n,'rb').read()).hexdigest(),n) for n in rows)
PY
( cd /tmp/redkit && bash install_cert_watch.sh ) > /tmp/w2.log 2>&1; rc=$?
ck "exits 1" "$([ $rc -eq 1 ] && echo 1 || echo 0)"
ck "names the F-88 identity gate" "$(grep -q 'F-88' /tmp/w2.log && echo 1 || echo 0)"
ck "THE PREVIOUS FILE SURVIVED UNTOUCHED" "$([ -f /root/wa/cert_watch.py ] && [ "$(md5sum /root/wa/cert_watch.py|awk '{print $1}')" = "$PREV" ] && echo 1 || echo 0)"
ck "says the target was not touched" "$(grep -q 'was NOT touched by this run' /tmp/w2.log && echo 1 || echo 0)"
ck "did not remove units it never placed" "$(grep -q 'removed the systemd units' /tmp/w2.log && echo 0 || echo 1)"

echo "== 3 · RED PATH, hash gate (a previous file MUST survive) =="
rm -rf /tmp/redkit2 && cp -r "$KIT" /tmp/redkit2 && echo "# tampered" >> /tmp/redkit2/cert_watch.py
( cd /tmp/redkit2 && bash install_cert_watch.sh ) > /tmp/w3.log 2>&1; rc=$?
ck "exits 1" "$([ $rc -eq 1 ] && echo 1 || echo 0)"
ck "names the SUMS.md5 gate" "$(grep -q 'SUMS.md5 gate failed' /tmp/w3.log && echo 1 || echo 0)"
ck "THE PREVIOUS FILE SURVIVED UNTOUCHED" "$([ -f /root/wa/cert_watch.py ] && [ "$(md5sum /root/wa/cert_watch.py|awk '{print $1}')" = "$PREV" ] && echo 1 || echo 0)"

echo "== 4 · GREEN PATH OVER an existing file (must back it up) =="
( cd "$KIT" && bash install_cert_watch.sh ) > /tmp/w4.log 2>&1; rc=$?
ck "exits 0" "$([ $rc -eq 0 ] && echo 1 || echo 0)"
ck "the previous file was backed up" "$(ls /root/wa/cert_watch.py.bak_S237_* >/dev/null 2>&1 && echo 1 || echo 0)"
ck "the backup still holds the OLD bytes" "$([ "$(md5sum $(ls -t /root/wa/cert_watch.py.bak_S237_*|head -1)|awk '{print $1}')" = "$PREV" ] && echo 1 || echo 0)"
ck "the new file is now in place" "$([ "$(md5sum /root/wa/cert_watch.py|awk '{print $1}')" = "$(md5sum "$KIT/cert_watch.py"|awk '{print $1}')" ] && echo 1 || echo 0)"

rm -f /root/wa/cert_watch.py /root/wa/cert_watch.py.bak_S237_* /etc/systemd/system/clinic-certwatch.*
rm -rf /tmp/redkit /tmp/redkit2
echo ""
echo "INSTALLER WALK: $F failure(s)"
exit $([ $F -eq 0 ] && echo 0 || echo 1)
