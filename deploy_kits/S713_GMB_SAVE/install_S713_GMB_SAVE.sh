#!/bin/bash
# =============================================================================
#  install_S713_GMB_SAVE.sh . kit S713 (06-Nov-2026, session S389, the parent) . the GMB Review Assist keeps every press
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s713kit && cp -rp /root/deploy/repo/deploy_kits/S713_GMB_SAVE /tmp/s713kit && bash /tmp/s713kit/install_S713_GMB_SAVE.sh
#  (DRY=1 before bash: every gate; nothing written.)
#
#  D832 Part B (the owner's OK 14:58 IST 05-Nov; his "Yes" 08:45 IST 06-Nov): every Generate / Fresh variation kept on
#  the server behind the doctor gate (the ticks, language, relation, the three drafts as generated); a "Shared" button
#  beside Copy; Copy, WhatsApp and Shared each keep the text as it was in the box. No phone number is kept.
#    /root/portal/portal_gmb.py  (new)      -> a4606e4c   the doors and the store (GMB_STORE_DB, default gmb_store.db)
#    /root/portal/portal.py      a93da673   -> 5cf80f82   the live file + ONE mount block (proved by the walk)
#    /root/portal/gmb.html       d9aad642   -> 964f0288   the Shared buttons and the keeping; the S707 engine untouched
#  Restarts clinic-portal. Red after placing: portal.py and gmb.html back byte-identically, portal_gmb.py taken away
#  (kept as portal_gmb.py.s713_removed), restart.
#  Undo:  \cp -p /root/portal/portal.py.bak_S713 /root/portal/portal.py && \cp -p /root/portal/gmb.html.bak_S713 /root/portal/gmb.html && mv /root/portal/portal_gmb.py /root/portal/portal_gmb.py.s713_removed && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S713_GMB_SAVE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PD="${PD:-/root/portal}"
PY="${PY:-/root/wa/venv/bin/python3}"
SVC="${SVC:-clinic-portal}"; PPORT="${PPORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
PUB="${PUB:-https://followup.dr-manoj.in}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
LP="$PD/portal.py";     FP=a93da673504dec090171f8b2cd744062; TP=5cf80f8259efac4cbc88dcdc12729554
LG="$PD/gmb.html";      FG=d9aad64299c2ef3260ae6186ef0dc8b1; TG=964f0288a24ec558544de68a465e414a
LM="$PD/portal_gmb.py";                                      TM=a4606e4c2bad723bd98b09500d093b26
WALK_OK="14 of 14 green"; CONTROL="14 S713 check(s) red . 0 green"
HAVE_LOCK=0; PLACED=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the portal back"
  \cp -p "$LP.bak_S713" "$LP"; \cp -p "$LG.bak_S713" "$LG"
  [ -f "$LM" ] && mv -f "$LM" "$LM.s713_removed"
  [ "$SP_NEW" = 1 ] && rm -f "$SP" "$SP-wal" "$SP-shm"
  "$SYSTEMCTL" restart "$SVC"; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(phz); [ "$h2" = 200 ] && break; done
  [ "$(m5 "$LP")" = "$FP" ] && [ "$(m5 "$LG")" = "$FG" ] && [ ! -f "$LM" ] && echo "   portal.py and gmb.html are back byte-identically; portal_gmb.py is set aside" \
    || echo "   !! copy $LP.bak_S713 and $LG.bak_S713 back by hand and move $LM away"
  echo "   after the restore: portal health $h2. Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/portal.py")" = "$TP" ] && [ "$(m5 "$KDIR/gmb.html")" = "$TG" ] && [ "$(m5 "$KDIR/portal_gmb.py")" = "$TM" ] || stop "the kit's three files are not the built ones"
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
CFGP=$(grep -h -E '^\s*GMB_HTML_PATH\s*=' "$PD/portal_config.py" 2>/dev/null | tail -1 | sed -E "s/^[^=]*=\s*['\"]?([^'\"]*)['\"]?.*/\1/")
[ -z "$CFGP" ] || [ "$CFGP" = "$LG" ] || stop "portal_config.py points GMB_HTML_PATH at $CFGP, not $LG"
CFGS=$(grep -h -E '^\s*GMB_STORE_DB\s*=' "$PD/portal_config.py" 2>/dev/null | tail -1 | sed -E "s/^[^=]*=\s*['\"]?([^'\"]*)['\"]?.*/\1/")
[ -z "$CFGS" ] || [ "${CFGS%.db}" != "$CFGS" ] || stop "portal_config.py sets GMB_STORE_DB to $CFGS -- the store must be a .db (kept out of the code bundle)"
SP="${CFGS:-$PD/gmb_store.db}"; SP_NEW=0; [ -e "$SP" ] || SP_NEW=1
L1=$(m5 "$LP"); L2=$(m5 "$LG")
if [ "$L1" = "$TP" ] && [ "$L2" = "$TG" ] && [ "$(m5 "$LM")" = "$TM" ]; then
  echo "-- ALREADY INSTALLED: portal.py, gmb.html and portal_gmb.py are the kit's. Nothing written. portal health $(phz)"; exit 0
fi
[ "$L1" = "$FP" ] || stop "the live $LP changed since this kit was built (live ${L1:0:8}, kit expects ${FP:0:8})"
[ "$L2" = "$FG" ] || stop "the live $LG changed since this kit was built (live ${L2:0:8}, kit expects ${FG:0:8})"
[ -e "$LM" ] && stop "$LM is already there (${LM##*/} $(m5 "$LM" | cut -c1-8)) -- not this kit's"
echo "2. the live portal.py and gmb.html are the ones this kit was built from; portal_gmb.py is new"
WN=$(mktemp -d /tmp/s713new.XXXX); WO=$(mktemp -d /tmp/s713old.XXXX)
\cp "$KDIR/portal.py" "$KDIR/portal_gmb.py" "$WN/"; \cp "$LP" "$WO/"
"$PY" -B -m py_compile "$WN/portal_gmb.py" 2>/dev/null || stop "portal_gmb.py does not compile with $PY"
"$PY" -B -W ignore -m py_compile "$WN/portal.py" 2>/dev/null || stop "portal.py does not compile with $PY"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s713.py" "$WN" "$LP" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd /tmp && "$PY" -B "$KDIR/walk_s713.py" "$WN" "$LP" 2>&1 | grep -E 'RED|Error' | head); stop "the walk is not green ($R)"; }
echo "3. the walk on a made-up store (and portal.py = the live file + the one block): $R"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s713.py" "$WO" "$LP" 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop "the control on the live files is not as expected ($R)"
echo "   control on the live files: $R"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
g0=$(hcode "http://127.0.0.1:$PPORT/portal/gmb"); case "$g0" in 302|401|403|303) ;; *) stop "/portal/gmb answered $g0 without a login before the install";; esac
echo "4. portal health 200; /portal/gmb behind the login ($g0)"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LP")" = "$FP" ] && [ "$(m5 "$LG")" = "$FG" ] && [ ! -e "$LM" ] || stop "a live portal file changed while this kit was checking -- run the line again"
\cp -p "$LP" "$LP.bak_S713" && \cp -p "$LG" "$LG.bak_S713" || stop "could not keep backups"
echo "5. backups: portal.py.bak_S713, gmb.html.bak_S713"
PLACED=1
\cp "$KDIR/portal_gmb.py" "$LM.s713new" && chmod --reference="$LP.bak_S713" "$LM.s713new" && chown --reference="$LP.bak_S713" "$LM.s713new" && mv -f "$LM.s713new" "$LM" || restore "portal_gmb.py could not be placed"
for P in "$LP:portal.py" "$LG:gmb.html"; do
  L=${P%%:*}; K=${P##*:}
  \cp "$KDIR/$K" "$L.s713new" && chmod --reference="$L.bak_S713" "$L.s713new" && chown --reference="$L.bak_S713" "$L.s713new" && mv -f "$L.s713new" "$L" || restore "$K could not be placed"
done
[ "$(m5 "$LP")" = "$TP" ] && [ "$(m5 "$LG")" = "$TG" ] && [ "$(m5 "$LM")" = "$TM" ] || restore "read-back did not match"
"$PY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import portal_gmb as G; c = G.connect(sys.argv[2]); c.execute('SELECT COUNT(*) FROM press'); c.close()" "$PD" "$SP" 2>/dev/null || restore "the store $SP could not be made"
echo "   the store: $SP ($( [ "$SP_NEW" = 1 ] && echo made now, empty || echo already there, kept as it is))"
echo "6. placed portal_gmb.py (${TM:0:8}), portal.py (${TP:0:8}), gmb.html (${TG:0:8}); read back by md5"
"$SYSTEMCTL" restart "$SVC"
p1=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; p1=$(phz); [ "$p1" = 200 ] && break; done
[ "$p1" = 200 ] || restore "portal health $p1"
g1=$(hcode "http://127.0.0.1:$PPORT/portal/gmb"); case "$g1" in 302|401|403|303) ;; *) restore "/portal/gmb answered $g1 without a login";; esac
a1=$(hcode "http://127.0.0.1:$PPORT/portal/gmb/api/health"); case "$a1" in 302|401|403|303) ;; *) restore "the new door answered $a1 without a login (404 = the module did not load)";; esac
a2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST -H 'Content-Type: application/json' -H 'X-Gmb: 1' -d '{}' "http://127.0.0.1:$PPORT/portal/gmb/api/press")
case "$a2" in 302|401|403|303) ;; *) restore "a signed-out save answered $a2, not a refusal";; esac
a3=$(curl -s -o /dev/null -m 12 -w '%{http_code}' "$PUB/portal/gmb/api/health")
case "$a3" in 302|401|403|303) A3="through the public address too ($a3)";; 000) A3="(the public address could not be reached from the server -- not this kit's fault; the page will say if a save fails)";; *) restore "the public address answered $a3 for the new door -- the web server does not route it";; esac
PLACED=0
echo "7. $SVC restarted: health $p1; /portal/gmb behind the login ($g1); the new doors refuse a signed-out call ($a1, $a2) $A3"
echo ""
echo "$KIT: DONE. Open the GMB Review Assist page and press Generate -- under the green tick it says 'Kept on the server.'"
