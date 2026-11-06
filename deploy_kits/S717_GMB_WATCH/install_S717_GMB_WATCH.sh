#!/bin/bash
# =============================================================================
#  install_S717_GMB_WATCH.sh . kit S717 (06-Nov-2026, session S389, the parent) . "What patients say -- for our clinic"
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s717kit && cp -rp /root/deploy/repo/deploy_kits/S717_GMB_WATCH /tmp/s717kit && bash /tmp/s717kit/install_S717_GMB_WATCH.sh
#  (DRY=1 before bash: every gate; nothing written.)
#
#  D832 Part C, the owner's "build" 11:05 IST 06-Nov on the mock-up he narrowed (percent of reviewers; only what is useful
#  for our clinic): a section under the drafts -- our complaints with the trend, complaints to stay ahead of, words patients
#  use elsewhere -- read from readings kept in the S713 store; the owner can add a listing to read.
#    /root/portal/portal_gmb.py  a4606e4c -> 5bd5318f   two tables (snapshot, watch) and three doors; S713's doors unchanged
#    /root/portal/gmb.html       964f0288 -> 47d38f4f   the new section after the Staff SOP; the S707 engine untouched
#    the store: the 5-Nov reading and the five listings put in once (seed_s717.txt), only when no reading is there yet
#  Restarts clinic-portal. Red after placing: both files back byte-identically, restart (a seeded reading stays; it is
#  harmless data the old module never reads).
#  Undo:  \cp -p /root/portal/portal_gmb.py.bak_S717 /root/portal/portal_gmb.py && \cp -p /root/portal/gmb.html.bak_S717 /root/portal/gmb.html && systemctl restart clinic-portal
# =============================================================================
set -u
KIT="S717_GMB_WATCH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PD="${PD:-/root/portal}"
PY="${PY:-/root/wa/venv/bin/python3}"
SVC="${SVC:-clinic-portal}"; PPORT="${PPORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
PUB="${PUB:-https://followup.dr-manoj.in}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
LM="$PD/portal_gmb.py"; FM=a4606e4c2bad723bd98b09500d093b26; TM=5bd5318fdcc80261c18cab280e5e17ad
LG="$PD/gmb.html";      FG=964f0288a24ec558544de68a465e414a; TG=47d38f4f9a13f4867f33a1a6652f6e34
WALK_OK="18 of 18 green"; CONTROL="18 S717 check(s) red . 0 green"
HAVE_LOCK=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting the two files back"
  \cp -p "$LM.bak_S717" "$LM"; \cp -p "$LG.bak_S717" "$LG"
  "$SYSTEMCTL" restart "$SVC"; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(phz); [ "$h2" = 200 ] && break; done
  [ "$(m5 "$LM")" = "$FM" ] && [ "$(m5 "$LG")" = "$FG" ] && echo "   portal_gmb.py and gmb.html are back byte-identically" \
    || echo "   !! copy $LM.bak_S717 and $LG.bak_S717 back by hand"
  echo "   after the restore: portal health $h2. Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/portal_gmb.py")" = "$TM" ] && [ "$(m5 "$KDIR/gmb.html")" = "$TG" ] || stop "the kit's two files are not the built ones"
echo "1. kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
CFGP=$(grep -h -E '^\s*GMB_HTML_PATH\s*=' "$PD/portal_config.py" 2>/dev/null | tail -1 | sed -E "s/^[^=]*=\s*['\"]?([^'\"]*)['\"]?.*/\1/")
[ -z "$CFGP" ] || [ "$CFGP" = "$LG" ] || stop "portal_config.py points GMB_HTML_PATH at $CFGP, not $LG"
CFGS=$(grep -h -E '^\s*GMB_STORE_DB\s*=' "$PD/portal_config.py" 2>/dev/null | tail -1 | sed -E "s/^[^=]*=\s*['\"]?([^'\"]*)['\"]?.*/\1/")
SP="${CFGS:-$PD/gmb_store.db}"
grep -q '^    import portal_gmb$' "$PD/portal.py" 2>/dev/null || stop "portal.py does not mount portal_gmb (S713 is not installed)"
L1=$(m5 "$LM"); L2=$(m5 "$LG")
if [ "$L1" = "$TM" ] && [ "$L2" = "$TG" ]; then
  R=$(cd /tmp && "$PY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import portal_gmb as G; print(G.seed(sys.argv[2], sys.argv[3]))" "$PD" "$SP" "$KDIR/seed_s717.txt" 2>&1)
  case "$R" in seeded|already) ;; *) echo "!! the files are the kit's, but the first reading could not be put in ($R). Send a photo of this screen to Claude."; exit 1;; esac
  echo "-- ALREADY INSTALLED: portal_gmb.py and gmb.html are the kit's. The first reading: $R. portal health $(phz)"; exit 0
fi
[ "$L1" = "$FM" ] || stop "the live $LM changed since this kit was built (live ${L1:0:8}, kit expects ${FM:0:8} -- S713's)"
[ "$L2" = "$FG" ] || stop "the live $LG changed since this kit was built (live ${L2:0:8}, kit expects ${FG:0:8} -- S713's)"
[ -f "$SP" ] || stop "the store $SP is not there (S713 makes it)"
echo "2. the live portal_gmb.py and gmb.html are S713's; the store is there"
"$PY" -B -m py_compile "$KDIR/portal_gmb.py" 2>/dev/null || stop "portal_gmb.py does not compile with $PY"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s717.py" "$KDIR" "$KDIR/seed_s717.txt" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd /tmp && "$PY" -B "$KDIR/walk_s717.py" "$KDIR" "$KDIR/seed_s717.txt" 2>&1 | grep -E 'RED|Error' | head); stop "the walk is not green ($R)"; }
echo "3. the walk on a made-up store: $R"
R=$(cd /tmp && "$PY" -B "$KDIR/walk_s717.py" "$PD" "$KDIR/seed_s717.txt" 2>&1 | tail -1)
[ "$R" = "$CONTROL" ] || stop "the control on the live module is not as expected ($R)"
echo "   control on the live module: $R"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
echo "4. portal health 200"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
[ "$(m5 "$LM")" = "$FM" ] && [ "$(m5 "$LG")" = "$FG" ] || stop "a live file changed while this kit was checking -- run the line again"
\cp -p "$LM" "$LM.bak_S717" && \cp -p "$LG" "$LG.bak_S717" || stop "could not keep backups"
"$PY" -B -c "import sqlite3,sys; s=sqlite3.connect(sys.argv[1]); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$SP" "$SP.bak_S717" || stop "could not back up the store"
echo "5. backups: portal_gmb.py.bak_S717, gmb.html.bak_S717, the store's copy ${SP##*/}.bak_S717"
PLACED=1
for P in "$LM:portal_gmb.py" "$LG:gmb.html"; do
  L=${P%%:*}; K=${P##*:}
  \cp "$KDIR/$K" "$L.s717new" && chmod --reference="$L.bak_S717" "$L.s717new" && chown --reference="$L.bak_S717" "$L.s717new" && mv -f "$L.s717new" "$L" || restore "$K could not be placed"
done
[ "$(m5 "$LM")" = "$TM" ] && [ "$(m5 "$LG")" = "$TG" ] || restore "read-back did not match"
echo "6. placed portal_gmb.py (${TM:0:8}) and gmb.html (${TG:0:8}); read back by md5"
R=$(cd /tmp && "$PY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import portal_gmb as G; print(G.seed(sys.argv[2], sys.argv[3]))" "$PD" "$SP" "$KDIR/seed_s717.txt" 2>&1)
case "$R" in seeded|already) ;; *) restore "the first reading could not be put in ($R)";; esac
echo "   the first reading (5 Nov) and the five listings: $R"
"$SYSTEMCTL" restart "$SVC"
p1=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; p1=$(phz); [ "$p1" = 200 ] && break; done
[ "$p1" = 200 ] || restore "portal health $p1"
g1=$(hcode "http://127.0.0.1:$PPORT/portal/gmb"); case "$g1" in 302|401|403|303) ;; *) restore "/portal/gmb answered $g1 without a login";; esac
a1=$(hcode "http://127.0.0.1:$PPORT/portal/gmb/api/watch"); case "$a1" in 302|401|403|303) ;; *) restore "the new door answered $a1 without a login (404 = the module did not load)";; esac
a2=$(hcode "http://127.0.0.1:$PPORT/portal/gmb/api/health"); case "$a2" in 302|401|403|303) ;; *) restore "S713's door answered $a2 without a login";; esac
a3=$(curl -s -o /dev/null -m 12 -w '%{http_code}' "$PUB/portal/gmb/api/watch")
case "$a3" in 302|401|403|303) A3="through the public address too ($a3)";; 000) A3="(the public address could not be reached from the server -- not this kit's fault)";; *) restore "the public address answered $a3 for the new door";; esac
PLACED=0
echo "7. $SVC restarted: health $p1; /portal/gmb behind the login ($g1); the doors refuse a signed-out call ($a1, $a2) $A3"
echo ""
echo "$KIT: DONE. Open the GMB Review Assist page and scroll below the drafts -- 'What patients say -- for our clinic'."
