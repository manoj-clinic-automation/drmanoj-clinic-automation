#!/bin/bash
# =============================================================================
#  install_S364_TRACKER_SSO.sh · kit S364_TRACKER_SSO (session 279, 21-Sep-2026)
#  The Callback Tracker opened from the Clinic app, already signed in.
#
#  THE OWNER'S ORDER (S278 close, D589; ruling at the S279 open): build ONLY the Callback Tracker's
#  single sign-in through the Clinic app, and take it live.
#
#  WHAT CHANGES ON THIS BOX
#    /root/portal/tracker_pass.py   NEW  -- the 120-second one-use pass (signed with a key derived
#                                           from the portal's existing CLINIC_SSO_SECRET; no new secret)
#    /root/portal/portal.py         d9a9dc40 -> 62b223cd (full file; make_s364.py = three anchored edits)
#        * the Call Tracker tile now opens /portal/go/call-tracker, which sends a signed-in person who is
#          shown that tile on to the Tracker with a pass; everyone else, and every failure, goes to the
#          plain Tracker address and its own key login, exactly as before
#        * /portal/sso/tracker-redeem (POST) -- the Tracker's server asks who a pass belongs to
#  CHECKED, NOT CHANGED: clinic_sso.py 2bc6ba15 · clinic_users.py 2e85a7c8 · tile_grants.json (read only)
#  THE TRACKER SIDE (Apps Script WebApp.gs + Dashboard.html) is placed by the assistant in the owner's
#  browser (D577); gas/ here is the record of it. Either side alone changes nothing a person sees.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S364_TRACKER_SSO/install_S364_TRACKER_SSO.sh
# =============================================================================
set -u
KIT="S364_TRACKER_SSO"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s364_walk_$STAMP"
P_FROM=d9a9dc409b203a4d8dcdd623aa54565f
P_TO=62b223cd4086d673f550e5eccf3380e0
TP=97ac975ad842247b5bcdce2f5b1432f2
SSO=2bc6ba15e52512d3f866536e758079ed
CU=2e85a7c85d047d400b0417e7aca9f3b7
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 portal.py)" = "$P_TO" ] && [ "$(m5 tracker_pass.py)" = "$TP" ] || { say "!! [1/7] kit files are not their pins - nothing installed"; exit 1; }
say "[1/7] kit gates green"
if [ "$(m5 "$PD/portal.py")" = "$P_TO" ] && [ "$(m5 "$PD/tracker_pass.py")" = "$TP" ]; then
  say "-- ALREADY INSTALLED (portal.py $P_TO, tracker_pass.py $TP). Nothing to do."; exit 0
fi
[ "$(m5 "$PD/portal.py")" = "$P_FROM" ] || { say "!! [2/7] portal.py is $(m5 "$PD/portal.py"), not d9a9dc40 - nothing installed"; exit 1; }
[ -e "$PD/tracker_pass.py" ] && { say "!! [2/7] $PD/tracker_pass.py already exists and is not the kit's - nothing installed"; exit 1; }
[ "$(m5 "$PD/clinic_sso.py")" = "$SSO" ] || { say "!! [2/7] clinic_sso.py is not 2bc6ba15 - nothing installed"; exit 1; }
[ "$(m5 "$PD/clinic_users.py")" = "$CU" ] || { say "!! [2/7] clinic_users.py is not 2e85a7c8 - nothing installed"; exit 1; }
say "[2/7] live pins exact"
mkdir -p "$WALK/app" || exit 1
\cp -p portal.py tracker_pass.py "$WALK/app/" && \cp -p "$PD/clinic_sso.py" "$PD/clinic_users.py" "$WALK/app/" || { say "!! [3/7] scratch copy failed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile "$WALK/app/portal.py" "$WALK/app/tracker_pass.py" "$KDIR/walk_s364.py" \
  || { say "!! [3/7] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
ST="$( cd "$WALK/app" && "$VPY" -B tracker_pass.py --selftest 2>&1 | tail -1 )"
echo "$ST" | grep -q "PASSED" || { say "!! [3/7] tracker_pass selftest red: $ST - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/7] py_compile green · $ST"
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s364.py" "$WALK/app" "$PD/tile_grants.json" "$PD/portal.py" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/7] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/7] $WOUT (scratch store, test secret; the LIVE portal.py is the negative control)"
BAK="$PD/portal.py.bak_S364_d9a9dc40"
\cp -p "$PD/portal.py" "$BAK" || { say "!! [5/7] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring byte-identically"
  \cp -p "$BAK" "$PD/portal.py"; mv -f "$PD/tracker_pass.py" "$PD/tracker_pass.py.removed_S364_$STAMP" 2>/dev/null
  systemctl restart clinic-portal || true; sleep 3
  say "   $PD/portal.py $(m5 "$PD/portal.py") · portal $(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8090/portal/health)"; exit 1
}
\cp -p tracker_pass.py "$PD/tracker_pass.py" && chmod 644 "$PD/tracker_pass.py" && [ "$(m5 "$PD/tracker_pass.py")" = "$TP" ] || restore
\cp -p portal.py "$PD/portal.py" && [ "$(m5 "$PD/portal.py")" = "$P_TO" ] || restore
say "[5/7] placed; backup $BAK"
systemctl restart clinic-portal || restore
sleep 4
systemctl is-active --quiet clinic-portal || restore
say "[6/7] clinic-portal active"
H=$(curl -s -m 8 http://127.0.0.1:8090/portal/health)
G=$(curl -s -o /dev/null -m 8 -w '%{http_code} %{redirect_url}' http://127.0.0.1:8090/portal/go/call-tracker)
R=$(curl -s -m 8 -X POST -d 'p=not.a-pass' http://127.0.0.1:8090/portal/sso/tracker-redeem | tr -d ' \n')
L=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8090/portal/login)
say "health : $H"
say "tile without a login : $G (302 to /portal/login expected)"
say "redeem with a bad pass : $R ({\"ok\":false} expected) · login page $L"
echo "$H" | grep -q '"mode": *"broker"' && echo "$H" | grep -q '"status": *"ok"' || restore
case "$G" in "302 "*"/portal/login"*) ;; *) restore;; esac
[ "$R" = '{"ok":false}' ] || restore
[ "$L" = 200 ] || restore
say "[7/7] all green -- the assistant now walks the real thing from the Clinic app (one tap on the Call Tracker tile)"
md5sum "$PD/portal.py" "$PD/tracker_pass.py" "$PD/clinic_sso.py" "$PD/clinic_users.py"
say "$KIT: DONE"
