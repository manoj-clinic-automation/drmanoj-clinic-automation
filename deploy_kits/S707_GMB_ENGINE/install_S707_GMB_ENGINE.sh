#!/bin/bash
# =============================================================================
#  install_S707_GMB_ENGINE.sh . kit S707 (05-Nov-2026, session S385, the parent) . the GMB Review Assist wording engine
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s707kit && cp -rp /root/deploy/repo/deploy_kits/S707_GMB_ENGINE /tmp/s707kit && bash /tmp/s707kit/install_S707_GMB_ENGINE.sh
#  (DRY=1 before bash: every gate; nothing written.)
#
#  /root/portal/gmb.html  e33aa612 -> d9aad642   the whole file replaced (a static page the portal reads from disk on
#      every request -- no restart): the wording engine behind the Generate button rebuilt to the owner's final plan
#      (claude/S385_GMB_PLAN.md, his OK 14:58 IST 05-Nov); a fourth language button (हिंदी + English); the size hints.
#      Nothing else on the page changes: the tick lists, the relation and language buttons' behaviour, Copy, WhatsApp,
#      Restore -- byte-identical to the live page.
#  Red after placing: gmb.html back byte-identically.
#  Undo:  \cp -p /root/portal/gmb.html.bak_S707 /root/portal/gmb.html
# =============================================================================
set -u
KIT="S707_GMB_ENGINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PD="${PD:-/root/portal}"
PPORT="${PPORT:-8099}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
LP="${GMB:-$PD/gmb.html}"
FROM=e33aa6125a5914063da138c585d85861; TO=d9aad64299c2ef3260ae6186ef0dc8b1
HAVE_LOCK=0; PLACED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
hcode() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
phz() { hcode "http://127.0.0.1:$PPORT/portal/health"; }
release() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
restore() {
  trap '' INT TERM HUP
  echo "!! RED after placing ($1) -- putting gmb.html back"
  \cp -p "$LP.bak_S707" "$LP"
  [ "$(m5 "$LP")" = "$FROM" ] && echo "   gmb.html is back byte-identically (${FROM:0:8})" || echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S707 back by hand"
  echo "   Send a photo of this screen to Claude."; exit 1
}
on_signal() { trap '' INT TERM HUP; [ "$PLACED" = 1 ] && restore "the run was interrupted"; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 "$KDIR/gmb.html")" = "$TO" ] || stop "the kit's gmb.html is not the built one"
echo "[1/5] kit files: all match SUMS.md5"
H=$(TZ=Asia/Kolkata date +%H%M)
if [ "${DRY:-0}" != 1 ] && { [ "$H" -lt 0400 ] || [ "$H" -gt 2330 ]; }; then stop "outside the install window (04:00-23:30 IST; now $(TZ=Asia/Kolkata date +%H:%M))"; fi
# the portal may be pointed elsewhere by its config -- the page must be the one it serves
CFGP=$(grep -h -E '^\s*GMB_HTML_PATH\s*=' "$PD/portal_config.py" 2>/dev/null | tail -1 | sed -E "s/^[^=]*=\s*['\"]?([^'\"]*)['\"]?.*/\1/")
[ -z "$CFGP" ] || [ "$CFGP" = "$LP" ] || stop "portal_config.py points GMB_HTML_PATH at $CFGP, not $LP"
L=$(m5 "$LP")
if [ "$L" = "$TO" ]; then echo "-- ALREADY INSTALLED: gmb.html is the kit's (${TO:0:8}). Nothing written. portal health $(phz)"; exit 0; fi
[ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
grep -q 'function mkOne(size)' "$KDIR/gmb.html" && grep -q "data-l=\"Mixed\"" "$KDIR/gmb.html" || stop "the kit's gmb.html lacks the new engine or the fourth language button"
[ "$(grep -c '<script>' "$KDIR/gmb.html")" = 1 ] || stop "the kit's gmb.html does not carry exactly one script"
echo "[2/5] the live gmb.html is the page the S385 research read (${FROM:0:8}); the kit's carries the new engine and the fourth language"
[ "$(phz)" = 200 ] || stop "the portal is not healthy before the install"
g0=$(hcode "http://127.0.0.1:$PPORT/portal/gmb"); case "$g0" in 302|401|403|303) ;; *) stop "/portal/gmb answered $g0 without a login before the install";; esac
echo "[3/5] portal health 200; /portal/gmb behind the login ($g0)"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
\cp -p "$LP" "$LP.bak_S707" || stop "could not keep a backup of $LP"
PLACED=1
\cp "$KDIR/gmb.html" "$LP.s707new" && chmod --reference="$LP.bak_S707" "$LP.s707new" && chown --reference="$LP.bak_S707" "$LP.s707new" && mv -f "$LP.s707new" "$LP" || restore "the file could not be placed"
[ "$(m5 "$LP")" = "$TO" ] || restore "read-back did not match"
echo "[4/5] placed gmb.html (${TO:0:8}), read back; backup gmb.html.bak_S707 (no restart: the portal reads the page per request)"
p1=$(phz); [ "$p1" = 200 ] || restore "portal health $p1"
g1=$(hcode "http://127.0.0.1:$PPORT/portal/gmb"); case "$g1" in 302|401|403|303) ;; *) restore "/portal/gmb answered $g1 without a login";; esac
PLACED=0
echo "[5/5] portal health $p1; /portal/gmb still behind the login ($g1)"
echo ""
echo "$KIT: DONE. Open the GMB Review Assist page and press Generate -- the drafts are the new ones."
