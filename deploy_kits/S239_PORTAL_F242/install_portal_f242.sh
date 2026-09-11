#!/usr/bin/env bash
# install_portal_f242.sh · kit S239_PORTAL_F242    Run by:  bash /root/deploy/vps_deploy.sh S239_PORTAL_F242
# ONE file: /root/portal/portal.py  7bc59115 -> ed558b36. Ends the login loop (F-242) and closes AF-12:
# the login page never bounces a half-signed-in browser, old device cookies are cleared, a new
# /portal/logout exists, and only the doctor can sign everyone out. Red path restores and restarts.
set -u
KIT="S239_PORTAL_F242"
KDIR="$(cd "$(dirname "$0")" && pwd)"
P=/root/portal/portal.py; B1=7bc591151553344e80d1e034a8f176d6; N1=ed558b3663c3dd100a24f58aafc32363
PY=/root/wa/venv/bin/python3
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
cd "$KDIR" || exit 1
c="$(md5of "$P")"
[ "$c" = "$N1" ] && { echo "already installed -- nothing to do."; exit 0; }
[ "$c" = "$B1" ] || { echo "!! [1/5] CURRENCY GATE -- $P is $c, expected $B1. Nothing installed."; exit 1; }
"$PY" -B patch_portal_f242_s239.py "$P" "$B1" --dry-run | grep -q "new md5 $N1" \
  || { echo "!! [2/5] dry run did not predict $N1 -- nothing installed"; exit 1; }
echo "[2/5] dry run predicts $N1"
out="$("$PY" -B patch_portal_f242_s239.py "$P" "$B1")" || { echo "!! [3/5] patch refused: $out"; exit 1; }
echo "[3/5] $out"
BAK="$(ls -t "$P".bak_S239_F242_* | head -1)"
rollback(){ echo "!! RED -- restoring"; \cp -p "$BAK" "$P"; systemctl restart clinic-portal; sleep 2; echo "   now: $(md5of "$P")"; exit 1; }
[ "$(md5of "$P")" = "$N1" ] || rollback
systemctl restart clinic-portal || rollback
sleep 3; systemctl is-active --quiet clinic-portal || rollback
h=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8099/portal/health)
l=$(curl -s -o /dev/null -m 6 -w '%{http_code}' -H 'Cookie: clinic_portal_device=stale' http://127.0.0.1:8099/portal/login)
o=$(curl -s -o /dev/null -m 6 -w '%{http_code}' http://127.0.0.1:8099/portal/logout)
echo "[4/5] health $h · login page with an old cookie $l (must be 200, not a redirect) · logout $o (302)"
[ "$h" = "200" ] && [ "$l" = "200" ] && [ "$o" = "302" ] || rollback
echo "[5/5] GREEN -- $(md5of "$P")"
echo "  Reverse:  \\cp -p $BAK $P && systemctl restart clinic-portal"
