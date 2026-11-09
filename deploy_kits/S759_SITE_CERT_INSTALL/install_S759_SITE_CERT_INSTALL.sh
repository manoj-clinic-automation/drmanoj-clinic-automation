#!/bin/bash
# =============================================================================
#  install_S759_SITE_CERT_INSTALL.sh . kit S759 (09-Nov-2026, session S413, the parent) . the follow-up of S758 part 2
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s759kit && cp -rp /root/deploy/repo/deploy_kits/S759_SITE_CERT_INSTALL /tmp/s759kit && bash /tmp/s759kit/install_S759_SITE_CERT_INSTALL.sh
#  (DRY=1 before bash: the LOOK only; nothing changed.)
#
#  S758 (08:14 IST) mended acme.sh's webroot and acme.sh RENEWED drmanojagarwal.com -- but the website still serves the old
#  certificate (ends 08-Dec): the new one sits in /root/.acme.sh, and the website reads the files its own vhost names (vhssl
#  keyFile / certFile). This kit:
#    LOOK  the renewed certificate in acme.sh's folder (days left; its key matches it), the two files the vhost names, what the
#          site serves now;
#    ACT   only when all of that holds: the two files backed up (*.bak_S759), acme.sh --install-cert to exactly those two files
#          with the web server's restart as its reload command -- recorded in acme.sh's conf, so EVERY later renewal lands there
#          by itself -- and the certificate the site SERVES read back (more than 60 days). If it does not show: the two files and
#          acme.sh's conf put back, the web server restarted once, nothing else touched.
#  Undo:  bash /tmp/s759kit/install_S759_SITE_CERT_INSTALL.sh --undo
# =============================================================================
set -u
KIT="S759_SITE_CERT_INSTALL"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SITE="${SITE:-drmanojagarwal.com}"
ACME_HOME="${ACME_HOME:-/root/.acme.sh}"; ADIR="$ACME_HOME/${SITE}_ecc"; ACME_CONF="$ADIR/${SITE}.conf"
LSWS="${LSWS:-/usr/local/lsws}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"; HAVE_LOCK=0; ACTED=0
release() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; HAVE_LOCK=0; }
trap release EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing was changed.} Send a photo of this screen to Claude."; exit 1; }
served_pem() { if [ -n "${SERVED_PEM_CMD:-}" ]; then $SERVED_PEM_CMD; return; fi; echo | timeout 15 openssl s_client -servername "$SITE" -connect "${CERT_HOST:-127.0.0.1}:443" 2>/dev/null | openssl x509 2>/dev/null; }
served_end() { served_pem | openssl x509 -noout -enddate 2>/dev/null | sed 's/^notAfter=//'; }
served_fp() { served_pem | openssl x509 -noout -fingerprint -sha256 2>/dev/null | cut -d= -f2; }
fp() { openssl x509 -noout -fingerprint -sha256 -in "$1" 2>/dev/null | cut -d= -f2; }
days_of() { [ -n "$1" ] || { echo "?"; return; }; echo $(( ( $(date -d "$1" +%s) - $(date +%s) ) / 86400 )); }
file_end() { openssl x509 -noout -enddate -in "$1" 2>/dev/null | sed 's/^notAfter=//'; }
pub_cert() { openssl x509 -noout -pubkey -in "$1" 2>/dev/null | sha256sum | cut -c1-16; }
pub_key() { openssl pkey -pubout -in "$1" 2>/dev/null | sha256sum | cut -c1-16; }
restart_web() { if [ -x "$LSWS/bin/lswsctrl" ]; then "$LSWS/bin/lswsctrl" restart >/dev/null 2>&1; else "$SYSTEMCTL" restart lsws >/dev/null 2>&1; fi; }
RELOAD_CMD="${RELOAD_CMD:-$([ -x "$LSWS/bin/lswsctrl" ] && echo "$LSWS/bin/lswsctrl restart" || echo "systemctl restart lsws")}"
putback() {   # the two files by content (a symlinked path keeps its link), acme.sh's conf, one restart
  [ -f "$KEYF.bak_S759" ] && { cat "$KEYF.bak_S759" > "$KEYF" || echo "!!!! the key could NOT be put back -- copy $KEYF.bak_S759 to $KEYF by hand NOW"; }
  [ -f "$CERTF.bak_S759" ] && { cat "$CERTF.bak_S759" > "$CERTF" || echo "!!!! the certificate could NOT be put back -- copy $CERTF.bak_S759 to $CERTF by hand NOW"; }
  [ -f "$ACME_CONF.bak_S759" ] && \cp -p "$ACME_CONF.bak_S759" "$ACME_CONF"
  restart_web; sleep 6
}
on_signal() { trap '' INT TERM HUP; [ "$ACTED" = 1 ] && { putback; echo "!! interrupted -- the two files and acme.sh's conf put back"; }; exit 130; }
trap on_signal INT TERM HUP

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || stop "KIT_ID.txt names another kit"
VH="$LSWS/conf/vhosts/$SITE/vhost.conf"
[ -f "$VH" ] || stop "the website's vhost file is not at $VH"
VHR=$(awk -v n="$SITE" '$1=="virtualhost" && $2==n {f=1} f && $1=="vhRoot" {print $2; exit}' "$LSWS/conf/httpd_config.conf" 2>/dev/null); VHR="${VHR:-/home/$SITE}"; VHR="${VHR%/}"
sub() { sed "s#\$VH_ROOT#$VHR#; s#\$SERVER_ROOT#$LSWS#; s#\$VH_NAME#$SITE#"; }
KEYF=$(awk '/^[[:space:]]*vhssl[[:space:]]*\{/{f=1} f && $1=="keyFile"{print $2; exit} f && /^[[:space:]]*\}/{f=0}' "$VH" | sub)
CERTF=$(awk '/^[[:space:]]*vhssl[[:space:]]*\{/{f=1} f && $1=="certFile"{print $2; exit} f && /^[[:space:]]*\}/{f=0}' "$VH" | sub)
if [ "${1:-}" = "--undo" ]; then
  [ -n "$KEYF" ] && [ -f "$KEYF.bak_S759" ] || stop "no backups (*.bak_S759) -- nothing to undo"
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK)"; HAVE_LOCK=1
  putback; echo "UNDONE: the website's two certificate files and acme.sh's conf are back; the site now serves one ending $(served_end)"; exit 0
fi
echo "[1/4] kit files: all match SUMS.md5"
SNOW=$(served_end); SD=$(days_of "$SNOW")
NEWC="$ADIR/fullchain.cer"; NEWK="$ADIR/$SITE.key"
NE=$(file_end "$NEWC"); ND=$(days_of "$NE")
echo "[2/4] LOOK"
echo "      the site serves now: ends ${SNOW:-?} -- $SD days"
echo "      the renewed certificate in acme.sh's folder: ends ${NE:-?} -- $ND days"
echo "      the website's own files (vhost vhssl): keyFile ${KEYF:-?} . certFile ${CERTF:-?}"
[ -n "$CERTF" ] && [ -f "$CERTF" ] && echo "      what certFile holds now: ends $(file_end "$CERTF") -- $(days_of "$(file_end "$CERTF")") days$([ -L "$CERTF" ] && echo " (a link to $(readlink -f "$CERTF"))")"
echo "      acme.sh's install setting now: key ${Le_K:-$(sed -n "s/^Le_RealKeyPath='\(.*\)'$/\1/p" "$ACME_CONF" 2>/dev/null)} . fullchain $(sed -n "s/^Le_RealFullChainPath='\(.*\)'$/\1/p" "$ACME_CONF" 2>/dev/null)"
[ -n "$KEYF" ] && [ -n "$CERTF" ] || stop "the vhost names no keyFile / certFile in its vhssl block"
[ -f "$KEYF" ] && [ -f "$CERTF" ] || stop "the vhost's keyFile / certFile do not exist"
[ "$ND" -gt 60 ] 2>/dev/null || stop "the renewed certificate in $ADIR is not fresh ($ND days) -- not installing it"
[ "$(pub_cert "$NEWC")" = "$(pub_key "$NEWK")" ] || stop "the renewed certificate and its key in $ADIR do not belong together -- not installing them"
if [ "$SD" -gt 60 ] 2>/dev/null; then echo "-- the site already serves $SD days: nothing to install"; exit 0; fi
SFP=$(served_fp)
[ -n "$SFP" ] || stop "the certificate the site serves could not be read -- not touching anything"
[ "$(pub_cert "$CERTF")" = "$(pub_key "$KEYF")" ] || stop "the website's two files on disk are not a matching pair -- not touching anything (they would be the fallback)"
[ "$SFP" = "$(fp "$CERTF")" ] || stop "the site serves a different certificate than its certFile holds -- not touching anything"
echo "      the website's two files are a matching pair and are exactly what it serves (the safe fallback)"
echo "      => install the renewed certificate into the website's own two files, with '$RELOAD_CMD' kept for every later renewal"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: the LOOK only; nothing changed."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"; HAVE_LOCK=1
cp -pL "$KEYF" "$KEYF.bak_S759" || stop "could not back up $KEYF"            # always this run's: the pair just proven served
cp -pL "$CERTF" "$CERTF.bak_S759" || stop "could not back up $CERTF"
\cp -p "$ACME_CONF" "$ACME_CONF.bak_S759" || stop "could not back up $ACME_CONF"
chmod 600 "$KEYF.bak_S759"
echo "[3/4] backed up: $KEYF.bak_S759, $CERTF.bak_S759, $ACME_CONF.bak_S759"
ACTED=1
timeout 120 "$ACME_HOME/acme.sh" --install-cert -d "$SITE" --ecc --home "$ACME_HOME" --key-file "$KEYF" --fullchain-file "$CERTF" --reloadcmd "$RELOAD_CMD" > /tmp/s759_acme.out 2>&1; RC=$?
sleep 8
NFP=$(fp "$NEWC")
if [ "$(served_fp)" != "$NFP" ] && [ "$RC" = 0 ] && [ "$(pub_cert "$CERTF")" = "$(pub_key "$KEYF")" ] && [ "$(fp "$CERTF")" = "$NFP" ]; then
  restart_web; sleep 8                                   # the files are the new matching pair; the server may not have re-read them
fi
S2=$(served_end); D2=$(days_of "$S2")
W=$(curl -s -o /dev/null -m 12 -w '%{http_code}' --resolve "$SITE:443:${CERT_HOST:-127.0.0.1}" "${SITE_CHECK:-https://$SITE/}" 2>/dev/null)
if [ "$(served_fp)" = "$NFP" ] && [ "$D2" -gt 60 ] 2>/dev/null && [ "$W" != 000 ]; then
  ACTED=0
  echo "[4/4] the website now SERVES a certificate ending $S2 -- $D2 days; the site answers $W (acme.sh exit $RC)"
  if grep -q "^Le_RealKeyPath='$KEYF'" "$ACME_CONF" 2>/dev/null; then
    echo "      acme.sh keeps: key -> $KEYF . fullchain -> $CERTF . reload -> '$RELOAD_CMD' (every renewal from now lands there by itself)"
  else echo "      !! the site is fixed, but acme.sh's conf does not show the saved key path -- send a photo to Claude (the next renewal may not land)"; fi
  rm -f /tmp/s759_acme.out
  echo ""; echo "$KIT: DONE."
else
  putback; ACTED=0
  echo "[4/4] !! the site still serves ${S2:-?} ($D2 days; answers $W; acme.sh exit $RC: $(tail -2 /tmp/s759_acme.out 2>/dev/null | tr '\n' ' ' | cut -c1-240))"
  echo "      the two files and acme.sh's conf put back; the web server restarted once; it now serves $(served_end). Send a photo of this screen to Claude."
  exit 1
fi
