#!/bin/bash
# =============================================================================
#  install_S366_RING_POPUP.sh · kit S366_RING_POPUP (session 279, 22-Sep-2026)
#  D590 step 1 -- the caller's name on the staff phone as it rings. Owner GO: 21-Sep-2026 evening.
#
#  WHAT THIS PUTS ON THE BOX (all under /root/portal; the live call-hook is NOT touched)
#    NEW  ring_hook.py · ring_common.py · portal_push.py · portal_sw.js · ring_agents_build.py · ring_setup.py
#    NEW  ring-hook.service (gunicorn, 127.0.0.1:<RING_HOOK_PORT>, default 8110)  +  OLS context /ring-hook
#    NEW  0600 config: ring_hook.env · vapid_private.pem · ring_agents.json (built from MyOperator's user list)
#    portal.py  62b223cd (S364) -> 7bddc17c  (full file; make_s366.py = four anchored edits): the service worker,
#               the push routes, the "suchna chalu karein" card that only a ringing phone's login sees
#    /root/wa/venv gains pywebpush 1.14.1 (+ py-vapid, http-ece); if http-ece will not build, the kit's own copy
#               of http_ece.py (MIT, 1.2.1) is placed beside the portal instead.
#  CHECKED, NOT CHANGED: tracker_pass.py 97ac975a · clinic_sso.py 2bc6ba15 · clinic_users.py 2e85a7c8 ·
#               /root/finance/finance_patient_match.py 0700768a (the fingerprint the lookup uses)
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S366_RING_POPUP/install_S366_RING_POPUP.sh
#  S279 re-issue 2: the first VPS run went red inside its own walk -- PYTHONPATH=/root/portal let the scratch portal import the
#  REAL portal_config.py, so the walk signed its test cookie with the wrong secret. The walk now names that fault; PYTHONPATH gone.
#  Re-running is safe: every step is idempotent; an already-installed box prints what it finds and stops.
# =============================================================================
set -u
KIT="S366_RING_POPUP"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"
FIN="${FIN:-/root/finance}"
PORTAL_PORT="${PORTAL_PORT:-8099}"
VH="${VH:-/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf}"
LSWSCTRL="${LSWSCTRL:-/usr/local/lsws/bin/lswsctrl}"
UNIT="/etc/systemd/system/ring-hook.service"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s366_walk_$STAMP"
P_FROM=62b223cd4086d673f550e5eccf3380e0
P_TO=7bddc17cd7e65c75303b0046a86a08db
TP=97ac975ad842247b5bcdce2f5b1432f2
SSO=2bc6ba15e52512d3f866536e758079ed
CU=2e85a7c85d047d400b0417e7aca9f3b7
FPM=0700768afc475d43da5f24deb6e8fc38
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
probe() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 portal.py)" = "$P_TO" ] || { say "!! [1/9] kit portal.py is not its pin - nothing installed"; exit 1; }
say "[1/9] kit gates green"
if [ "$(m5 "$PD/portal.py")" = "$P_TO" ] && [ -f "$PD/ring_hook.py" ] && systemctl is-active --quiet ring-hook; then
  say "-- ALREADY INSTALLED (portal.py $P_TO, ring-hook active). Status:"
  curl -s -m 5 "http://127.0.0.1:$(grep ^RING_HOOK_PORT= "$PD/ring_hook.env" | cut -d= -f2)/ring-hook/health"; echo
  "$VPY" "$PD/ring_agents_build.py" --show
  exit 0
fi
[ "$(m5 "$PD/portal.py")" = "$P_FROM" ] || { say "!! [2/9] portal.py is $(m5 "$PD/portal.py"), not 62b223cd (S364) - nothing installed"; exit 1; }
[ "$(m5 "$PD/tracker_pass.py")" = "$TP" ] && [ "$(m5 "$PD/clinic_sso.py")" = "$SSO" ] && [ "$(m5 "$PD/clinic_users.py")" = "$CU" ] \
  || { say "!! [2/9] a portal helper is not at its pin - nothing installed"; exit 1; }
[ "$(m5 "$FIN/finance_patient_match.py")" = "$FPM" ] || { say "!! [2/9] finance_patient_match.py is $(m5 "$FIN/finance_patient_match.py"), not 0700768a - nothing installed"; exit 1; }
[ -f "$FIN/patient_fp.env" ] || { say "!! [2/9] $FIN/patient_fp.env missing - the lookup would have no salt - nothing installed"; exit 1; }
[ -f "$VH" ] && [ -x "$LSWSCTRL" ] || { say "!! [2/9] vhost.conf or lswsctrl not where expected - nothing installed"; exit 1; }
say "[2/9] live pins exact · salt file present"
# --- the one library ---------------------------------------------------------------------------------------
if ! "$VPY" -c "import pywebpush, py_vapid, http_ece" 2>/dev/null; then
  say "[3/9] installing pywebpush 1.14.1 into the venv ..."
  "$VPY" -m pip install -q "pywebpush==1.14.1" >/tmp/s366_pip.log 2>&1 || true
  if ! "$VPY" -c "import pywebpush, py_vapid, http_ece" 2>/dev/null; then
    say "      http-ece would not build -- taking the kit's own http_ece.py (MIT) beside the portal"
    "$VPY" -m pip install -q --no-deps "pywebpush==1.14.1" py-vapid requests six cryptography >>/tmp/s366_pip.log 2>&1 || true
    \cp -p http_ece.py "$PD/http_ece.py"
    ( cd "$PD" && "$VPY" -c "import pywebpush, py_vapid, http_ece" ) 2>/dev/null || { say "!! [3/9] pywebpush still not importable (see /tmp/s366_pip.log) - nothing installed"; rm -f "$PD/http_ece.py"; exit 1; }
  fi
fi
say "[3/9] pywebpush importable"
# --- compile + selftests + walk in a scratch world -------------------------------------------------------------
mkdir -p "$WALK/app" || exit 1
\cp -p ring_hook.py ring_common.py portal_push.py portal_sw.js portal.py "$WALK/app/" && \cp -p "$PD/clinic_sso.py" "$PD/clinic_users.py" "$PD/tracker_pass.py" "$WALK/app/" || { say "!! [4/9] scratch copy failed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile "$WALK/app/ring_hook.py" "$WALK/app/ring_common.py" "$WALK/app/portal_push.py" "$WALK/app/portal.py" "$KDIR/ring_agents_build.py" "$KDIR/ring_setup.py" "$KDIR/walk_s366.py" \
  || { say "!! [4/9] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && timeout 180 "$VPY" -B "$KDIR/walk_s366.py" "$WALK/app" "$FIN" "$PD/tile_grants.json" "$PD/portal.py" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/9] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/9] $WOUT (scratch db + test salt; the LIVE portal.py is the negative control)"
# --- config (idempotent, 0600) + the agent map --------------------------------------------------------------
( cd "$PD" && "$VPY" "$KDIR/ring_setup.py" ) || { say "!! [5/9] ring_setup failed - nothing placed"; exit 1; }
PORT="$(grep ^RING_HOOK_PORT= "$PD/ring_hook.env" | cut -d= -f2)"
if ss -ltn 2>/dev/null | grep -q ":$PORT " && ! systemctl is-active --quiet ring-hook; then
  say "!! [5/9] port $PORT is taken by something that is not ring-hook - set RING_HOOK_PORT in $PD/ring_hook.env and re-run"; exit 1; fi
say "[5/9] config ready · port $PORT"
say "      agent phones (from MyOperator's user list; names only):"
\cp -p ring_agents_build.py "$PD/ring_agents_build.py"
"$VPY" "$PD/ring_agents_build.py" | sed 's/^/      /'
# --- place --------------------------------------------------------------------------------------------------
BAK="$PD/portal.py.bak_S366_62b223cd"
\cp -p "$PD/portal.py" "$BAK" || { say "!! [6/9] backup failed - nothing placed"; exit 1; }
[ -f "$VH.bak_S366_$STAMP" ] || \cp -p "$VH" "$VH.bak_S366_$STAMP"
restore() {
  say "!! RED after placing - restoring"
  \cp -p "$BAK" "$PD/portal.py"; systemctl restart clinic-portal || true
  systemctl disable --now ring-hook >/dev/null 2>&1 || true; rm -f "$UNIT"; systemctl daemon-reload
  if ! cmp -s "$VH" "$VH.bak_S366_$STAMP"; then \cp -p "$VH.bak_S366_$STAMP" "$VH"; "$LSWSCTRL" restart >/dev/null 2>&1 || true; sleep 3; fi
  sleep 3; say "   portal.py $(m5 "$PD/portal.py") · /portal/health $(probe "http://127.0.0.1:$PORTAL_PORT/portal/health") · public /portal $(probe https://followup.dr-manoj.in/portal)"; exit 1
}
\cp -p ring_hook.py ring_common.py portal_push.py portal_sw.js ring_setup.py "$PD/" || restore
\cp -p ring-hook.service "$UNIT" || restore
systemctl daemon-reload && systemctl enable --now ring-hook >/dev/null 2>&1 || restore
systemctl restart ring-hook || restore
sleep 3
systemctl is-active --quiet ring-hook || restore
H=$(curl -s -m 8 "http://127.0.0.1:$PORT/ring-hook/health")
echo "$H" | grep -q '"service": *"ring-hook"' && echo "$H" | grep -q '"status": *"ok"' || restore
say "[6/9] ring-hook.service active on 127.0.0.1:$PORT"
# --- the public route ----------------------------------------------------------------------------------------
if grep -qE '^[[:space:]]*context[[:space:]]+/ring-hook\b' "$VH"; then
  say "[7/9] /ring-hook already in the vhost"
else
  pre_por="$(probe https://followup.dr-manoj.in/portal/health)"; pre_fin="$(probe https://followup.dr-manoj.in/finance/healthz)"
  { echo; sed "s/__PORT__/$PORT/" ringhook_proxy.block.tmpl; } >> "$VH"
  "$LSWSCTRL" restart >/tmp/s366_lsws.log 2>&1 || true
  sleep 4
  rh="$(probe https://followup.dr-manoj.in/ring-hook/health)"; por="$(probe https://followup.dr-manoj.in/portal/health)"; fin="$(probe https://followup.dr-manoj.in/finance/healthz)"
  say "      public: /ring-hook/health=$rh  /portal/health=$por (was $pre_por)  /finance/healthz=$fin (was $pre_fin)"
  [ "$rh" = 200 ] && [ "$por" = "$pre_por" ] && [ "$fin" = "$pre_fin" ] || restore
  say "[7/9] https://followup.dr-manoj.in/ring-hook answers; everything else unchanged"
fi
# --- the portal -----------------------------------------------------------------------------------------------
\cp -p portal.py "$PD/portal.py" && [ "$(m5 "$PD/portal.py")" = "$P_TO" ] || restore
systemctl restart clinic-portal || restore
sleep 4
systemctl is-active --quiet clinic-portal || restore
PH=$(curl -s -m 8 "http://127.0.0.1:$PORTAL_PORT/portal/health")
SW=$(probe "http://127.0.0.1:$PORTAL_PORT/portal/sw.js"); PK=$(curl -s -m 8 "http://127.0.0.1:$PORTAL_PORT/portal/push/key" | tr -d ' \n' | cut -c1-9)
GO=$(curl -s -o /dev/null -m 8 -w '%{http_code} %{redirect_url}' "http://127.0.0.1:$PORTAL_PORT/portal/go/call-tracker")
say "      portal: health $PH · sw.js $SW · push/key $PK... · tile without login: $GO"
echo "$PH" | grep -q '"status": *"ok"' && [ "$SW" = 200 ] && [ "$PK" = '{"key":"B' ] && case "$GO" in "302 "*"/portal/login"*) true;; *) false;; esac || restore
say "[8/9] portal.py $P_TO live; backup $BAK"
say "[9/9] all green -- $KIT: DONE"
md5sum "$PD/portal.py" "$PD/ring_hook.py" "$PD/ring_common.py" "$PD/portal_push.py" "$PD/portal_sw.js" "$PD/ring_agents_build.py" "$PD/ring_setup.py"
echo
say "=== THE ONE LINE FOR THE MYOPERATOR PANEL (APIs & Webhooks -> Webhooks v2 -> Add New Webhook; events: call.dial_begin, call.answered, call.end) ==="
( cd "$PD" && "$VPY" ring_setup.py --webhook-url )
say "==="
