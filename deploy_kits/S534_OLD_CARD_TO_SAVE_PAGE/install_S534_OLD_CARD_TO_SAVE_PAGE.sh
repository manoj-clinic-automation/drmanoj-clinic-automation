#!/bin/bash
# =============================================================================
#  install_S534_OLD_CARD_TO_SAVE_PAGE.sh · kit S534 (session 305, 12-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S534_OLD_CARD_TO_SAVE_PAGE/install_S534_OLD_CARD_TO_SAVE_PAGE.sh
#
#  WHY (the owner's screenshots, 04:53/04:55 IST 12-Oct): his Fold still downloads DrManojAgarwalClinic.vcf ("File can't be
#  downloaded securely"). Chrome remembered the old PERMANENT forward of save.dr-manoj.in to
#  http://drmanojagarwal.com/DrManojAgarwalClinic.vcf and never asks GoDaddy again, though GoDaddy now forwards to the new
#  page. THIS KIT: one marked block at the TOP of the website's .htaccess sends that old card address -- http or https --
#  to https://drmanojagarwal.com/save/ (a temporary 302, so nothing is remembered again). WordPress's own blocks are
#  untouched; the old file stays on disk.
#  ORDER: gates -> the file found (ALREADY first) -> the site answers before -> backup -> the block placed (same owner and
#  mode) -> the old address read: 302 to /save/ (a graceful web-server reload only if the rule is not yet read) -> the home
#  page, the save page and its card still answer -> undo line. Red after placing: the old .htaccess back byte for byte.
# =============================================================================
set -u
KIT="S534_OLD_CARD_TO_SAVE_PAGE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
DOCROOT="${DOCROOT:-/home/drmanojagarwal.com/public_html}"
SITE="${SITE:-drmanojagarwal.com}"
HT="$DOCROOT/.htaccess"
LSWSCTRL="${LSWSCTRL:-/usr/local/lsws/bin/lswsctrl}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
STAMP="$(date +%Y%m%d_%H%M%S)"
HAVE_LOCK=0; PLACED=0; RELOADED=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
code() { curl -s -o /dev/null -m 20 -w '%{http_code}' "$1"; }
loc() { curl -s -o /dev/null -m 20 -w '%{http_code} %{redirect_url}' "$1"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the old .htaccess back byte for byte"
  [ -f "$BAK" ] && \cp -p "$BAK" "$HT"
  [ "$RELOADED" = 1 ] && [ -x "$LSWSCTRL" ] && "$LSWSCTRL" restart >/dev/null 2>&1
  say "   $HT $(m5 "$HT") (expected $FROM)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
[ "$HAVE_LOCK" = 1 ] || { say "!! [1/6] another build holds the lock $LOCK - nothing installed. Paste the line again when it is free."; exit 3; }
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/6] kit gates green; the build lock is ours"

[ -f "$HT" ] && { [ -f "$DOCROOT/wp-config.php" ] || [ -f "$DOCROOT/../wp-config.php" ]; } || { say "!! [2/6] $HT is not the website's WordPress .htaccess - nothing installed"; exit 1; }
FROM="$(m5 "$HT")"; BAK="$HT.bak_S534_${FROM:0:8}"
if grep -q "^# BEGIN S534 " "$HT"; then
  L="$(loc "https://$SITE/DrManojAgarwalClinic.vcf")"
  say "-- ALREADY INSTALLED: the block is in $HT; the old card address answers: $L. Nothing written."; exit 0
fi
H0="$(code "https://$SITE/")"; S0="$(code "https://$SITE/save/")"; V0="$(loc "https://$SITE/DrManojAgarwalClinic.vcf")"
[ "$H0" = 200 ] && [ "$S0" = 200 ] || { say "!! [2/6] the site does not answer as expected before any change (home $H0, save page $S0) - nothing installed"; exit 1; }
say "[2/6] $HT found ($FROM); before: home $H0, save page $S0, the old card address $V0"

\cp -p "$HT" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [3/6] backup failed - nothing placed"; exit 1; }
say "[3/6] backup beside it: $(basename "$BAK")"

TMP="$DOCROOT/.htaccess.s534_new"
{ cat s534_block.txt; echo; cat "$HT"; } > "$TMP" && chown --reference="$HT" "$TMP" && chmod --reference="$HT" "$TMP" \
  || { rm -f "$TMP"; say "!! [4/6] could not prepare the new .htaccess - nothing placed"; exit 1; }
[ "$(tail -c +$(( $(wc -c < s534_block.txt) + 2 )) "$TMP" | md5sum | awk '{print $1}')" = "$FROM" ] \
  || { rm -f "$TMP"; say "!! [4/6] the prepared file is not the block + the old file unchanged - nothing placed"; exit 1; }
PLACED=1
mv -f "$TMP" "$HT" || restore "placing .htaccess"
say "[4/6] the block placed at the top; the rest of the file is the old file byte for byte"

V1="$(loc "https://$SITE/DrManojAgarwalClinic.vcf")"
if [ "${V1%% *}" != 302 ]; then
  [ -x "$LSWSCTRL" ] || restore "the rule is not read and $LSWSCTRL is not there"
  say "   the web server has not read the new rule yet ($V1) - a graceful reload"
  "$LSWSCTRL" restart >/dev/null 2>&1; RELOADED=1; sleep 4
  V1="$(loc "https://$SITE/DrManojAgarwalClinic.vcf")"
fi
[ "$V1" = "302 https://$SITE/save/" ] || restore "the old card address answers '$V1', not 302 to the save page"
V2="$(curl -s -o /dev/null -m 30 -L -w '%{http_code} %{url_effective}' "http://$SITE/DrManojAgarwalClinic.vcf")"
[ "$V2" = "200 https://$SITE/save/" ] || restore "over http the old card address ends at '$V2', not the save page"
say "[5/6] the old card address -> 302 -> https://$SITE/save/ (https), and over http it ends there too"

H1="$(code "https://$SITE/")"; S1="$(code "https://$SITE/save/")"
C1="$(curl -s -o /dev/null -m 20 -w '%{http_code} %{content_type}' "https://$SITE/save/?card=1")"
[ "$H1" = 200 ] && [ "$S1" = 200 ] && echo "$C1" | grep -q "^200 text/vcard" || restore "after the change: home $H1, save page $S1, card $C1"
PLACED=0
say "[6/6] the home page $H1, the save page $S1, the card $C1"
md5sum "$HT"
say "$KIT: DONE"
say "undo: \\cp -p $BAK $HT$( [ "$RELOADED" = 1 ] && echo " && $LSWSCTRL restart")"
