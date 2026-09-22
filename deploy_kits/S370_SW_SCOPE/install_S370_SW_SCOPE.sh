#!/bin/bash
# install_S370_SW_SCOPE.sh · kit S370_SW_SCOPE (session 279, 22-Sep-2026) -- the service worker's scope.
# Shivani's phone reported (S369): permission granted, then sw-ready-timeout. Cause: the worker was registered for /portal/
# while the page lives at /portal, so navigator.serviceWorker.ready never resolved. Now: scope /portal, the page waits on
# its own registration, the old /portal/ registration is retired. Nothing else moves.
#   portal.py       f24abe2d (S369) -> 5876225db99894d74270be1829761661   (make_s370.py: the card script swapped whole)
#   portal_push.py  52bd4348 (S369) -> 576ae269e7136261f47c1de2314f67b7
# Run: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S370_SW_SCOPE/install_S370_SW_SCOPE.sh
set -u
KIT="S370_SW_SCOPE"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; PD="${PD:-/root/portal}"; PORTAL_PORT="${PORTAL_PORT:-8099}"
P_FROM=f24abe2d61bd95062741ab577c59c5a1; P_TO=5876225db99894d74270be1829761661; PP_FROM=52bd4348100a47beaf03d1b264d3cb70; PP_TO=576ae269e7136261f47c1de2314f67b7; STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s370_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 portal.py)" = "$P_TO" ] && [ "$(m5 portal_push.py)" = "$PP_TO" ] || { say "!! [1/5] kit files not at their pins"; exit 1; }
say "[1/5] kit gates green"
if [ "$(m5 "$PD/portal.py")" = "$P_TO" ] && [ "$(m5 "$PD/portal_push.py")" = "$PP_TO" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
[ "$(m5 "$PD/portal.py")" = "$P_FROM" ] && [ "$(m5 "$PD/portal_push.py")" = "$PP_FROM" ] || { say "!! [2/5] live portal.py/portal_push.py are not the S369 pins - nothing installed"; exit 1; }
say "[2/5] live pins exact"
mkdir -p "$WALK/app" && \cp -p portal.py portal_push.py "$WALK/app/" && \cp -p "$PD/ring_common.py" "$PD/portal_sw.js" "$PD/clinic_sso.py" "$PD/clinic_users.py" "$PD/tracker_pass.py" "$WALK/app/" || { say "!! [3/5] scratch copy failed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile "$WALK/app/portal.py" "$WALK/app/portal_push.py" || { say "!! [3/5] compile failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s370.py" "$WALK/app" "$PD/tile_grants.json" "$PD/portal.py" 2>&1 | tail -1 )"; rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/5] walk red: $WOUT - nothing installed"; exit 1; }
say "[3/5] $WOUT"
BAK="$PD/portal.py.bak_S370_f24abe2d"; \cp -p "$PD/portal.py" "$BAK" && \cp -p "$PD/portal_push.py" "$PD/portal_push.py.bak_S370_52bd4348" || { say "!! [4/5] backup failed"; exit 1; }
restore() { say "!! RED after placing - restoring"; \cp -p "$BAK" "$PD/portal.py"; \cp -p "$PD/portal_push.py.bak_S370_52bd4348" "$PD/portal_push.py"; systemctl restart clinic-portal || true; sleep 3; say "   portal.py $(m5 "$PD/portal.py")"; exit 1; }
\cp -p portal.py "$PD/portal.py" && \cp -p portal_push.py "$PD/portal_push.py" && [ "$(m5 "$PD/portal.py")" = "$P_TO" ] || restore
systemctl restart clinic-portal || restore; sleep 4; systemctl is-active --quiet clinic-portal || restore
PH=$(curl -s -m 8 "http://127.0.0.1:$PORTAL_PORT/portal/health"); SW=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/sw.js"); DG=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORTAL_PORT/portal/push/diag")
say "      health $PH · sw.js $SW · diag without login $DG (302 expected)"
echo "$PH" | grep -q '"status": *"ok"' && [ "$SW" = 200 ] && [ "$DG" = 302 ] || restore
say "[4/5] placed; backup $BAK"; say "[5/5] all green -- $KIT: DONE"; md5sum "$PD/portal.py" "$PD/portal_push.py"
