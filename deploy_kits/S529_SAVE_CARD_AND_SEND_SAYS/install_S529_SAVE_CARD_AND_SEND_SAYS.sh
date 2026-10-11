#!/bin/bash
# =============================================================================
#  install_S529_SAVE_CARD_AND_SEND_SAYS.sh · kit S529 (session 305, 11-Oct-2026) · F-855
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S529_SAVE_CARD_AND_SEND_SAYS/install_S529_SAVE_CARD_AND_SEND_SAYS.sh
#
#  THE OWNER, 11:23 IST 11-Oct: the save link "showing multiple prompts and not opening the contacts directly in my fold
#  ... do whatever is required"; the accountant pack "no confirmation message on that page ... check it".
#   1  NEW https://drmanojagarwal.com/save/ -- the clinic's "save contact" page: one tap opens the phone's own new-contact
#      form, filled in (Android), or the contact card itself (iPhone). Its card, clinic.vcf, is fetched HERE on the box
#      from the card the clinic's contact page already uses -- no number is in the repository or this kit.
#   2  /root/finance/packs.html 633ddba8 -> d25452a5: the Send button says Sending..., then Sent at HH:MM / NOT sent right
#      under itself, cannot be pressed twice in flight, and reads "Send again" once a month is sent.
#   3  /root/finance/setup_notes.py 63477bc0 -> d32423d1: the Websites card's save line.
#  Restarts clinic-finance. The GoDaddy forward for save is pointed at the new page afterwards (Claude, in the browser).
#  ORDER: gates -> pins (ALREADY first) -> compile + php -l -> walk -> DRY stops -> fetch and check the card -> backups ->
#  place -> restart -> health + the page read over https on this box -> undo line. Red after placing: all three put back.
# =============================================================================
set -u
KIT="S529_SAVE_CARD_AND_SEND_SAYS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DOCROOT="${DOCROOT:-/home/drmanojagarwal.com/public_html}"
SITE="${SITE:-drmanojagarwal.com}"
CARD_URL="${CARD_URL:-https://candid-trifle-127363.netlify.app/DrManojAgarwalClinic.vcf}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
PK="$FIN/packs.html"; SN="$FIN/setup_notes.py"; SAVE="$DOCROOT/save"
FROM_PK=633ddba801a80e2aaaf1102d8ef7d1a2; TO_PK=d25452a51f2f5fdd5c1e2b39b54bd9ff
FROM_SN=63477bc0781f6554b57a7868ea6161dc; TO_SN=d32423d1472081416b140fc5437523ab
TO_PH=f6496578168fc565cfd20e935d9f0510
UA_ANDROID="Mozilla/5.0 (Linux; Android 14; SM-F956B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36"
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s529_inst_$STAMP"
HAVE_LOCK=0; PLACED=0; SAVE_PLACED=0
BAK_PK="$PK.bak_S529_${FROM_PK:0:8}"; BAK_SN="$SN.bak_S529_${FROM_SN:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting everything back"
  [ -f "$BAK_PK" ] && \cp -p "$BAK_PK" "$PK"
  [ -f "$BAK_SN" ] && \cp -p "$BAK_SN" "$SN"
  [ "$SAVE_PLACED" = 1 ] && [ -d "$SAVE" ] && mv "$SAVE" "$SAVE.removed_S529_$STAMP"
  systemctl restart "$SVC" || true; sleep 3
  say "   $PK $(m5 "$PK") (expected $FROM_PK) · $SN $(m5 "$SN") (expected $FROM_SN) · save page $( [ -d "$SAVE" ] && echo PRESENT || echo 'taken off')"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date systemctl curl timeout grep tail sleep chown chmod stat; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$APY" ] || { say "!! preflight: $APY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 packs.html)" = "$TO_PK" ] && [ "$(m5 setup_notes.py)" = "$TO_SN" ] && [ "$(m5 save/index.php)" = "$TO_PH" ] \
  || { say "!! [1/8] the kit's files are not their predicted md5 - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

for f in "$PK" "$SN"; do [ -f "$f" ] || { say "!! [2/8] $f is not there - nothing installed"; exit 1; }; done
[ -d "$DOCROOT" ] && { [ -f "$DOCROOT/wp-config.php" ] || [ -f "$DOCROOT/../wp-config.php" ]; } \
  || { say "!! [2/8] $DOCROOT is not the website's WordPress folder - nothing installed"; exit 1; }
CPK="$(m5 "$PK")"; CSN="$(m5 "$SN")"
if [ "$CPK" = "$TO_PK" ] && [ "$CSN" = "$TO_SN" ] && [ "$(m5 "$SAVE/index.php")" = "$TO_PH" ] && grep -q "BEGIN:VCARD" "$SAVE/clinic.vcf" 2>/dev/null; then
  say "-- ALREADY INSTALLED: both files are the kit's and the save page is in place. Nothing written."; exit 0
fi
[ ! -e "$SAVE" ] || { say "!! [2/8] $SAVE already exists and is not this kit's - nothing installed"; exit 1; }
[ "$CPK" = "$FROM_PK" ] || { say "!! [2/8] $PK is $CPK, expected $FROM_PK - nothing installed"; exit 1; }
[ "$CSN" = "$FROM_SN" ] || { say "!! [2/8] $SN is $CSN, expected $FROM_SN - nothing installed"; exit 1; }
say "[2/8] two live pins exact; the website's folder found; no save folder there yet"

mkdir -p "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"; export PYTHONDONTWRITEBYTECODE=1
"$APY" -m py_compile setup_notes.py walk_s529.py make_s529.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
# php -l with the box's own PHP builds, newest first. A build that crashes (exit 128+, e.g. lsphp85's CLI on 11-Oct)
# says nothing about the page: the next one is tried. Only a build that SAYS "Parse error" stops the install.
PHPSAID=""
for PHPBIN in $(ls -d /usr/local/lsws/lsphp*/bin/php /usr/bin/php 2>/dev/null | sort -rV); do
  POUT="$("$PHPBIN" -l save/index.php 2>&1)"; PRC=$?
  if [ "$PRC" = 0 ]; then PHPSAID="passes php -l ($PHPBIN)"; break; fi
  if echo "$POUT" | grep -qi "parse error\|errors parsing"; then
    say "!! [3/8] the save page does not pass $PHPBIN -l: $(echo "$POUT" | head -2 | tr '\n' ' ') - nothing installed"; exit 1
  fi
  say "   ($PHPBIN could not check it -- exit $PRC -- trying the next PHP build)"
done
say "[3/8] py_compile green (3 files); the save page ${PHPSAID:-was not checked by any PHP build here -- it is proven by reading it over https after placing}"

WOUT="$( cd /tmp && timeout 120 "$APY" -B "$KDIR/walk_s529.py" "$KDIR" --fin "$FIN" 2>&1 )"; WRC=$?
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [4/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -6; say "   nothing installed"; exit 1
fi
say "[4/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

curl -fsS -m 30 -o "$SCR/clinic.vcf" "$CARD_URL" || { say "!! [5/8] could not fetch the clinic's card from $CARD_URL - nothing placed"; exit 1; }
CSZ=$(stat -c %s "$SCR/clinic.vcf")
head -c 200 "$SCR/clinic.vcf" | grep -q "BEGIN:VCARD" && grep -q "END:VCARD" "$SCR/clinic.vcf" && grep -qiE "^(item[0-9]+\.)?FN" "$SCR/clinic.vcf" \
  && grep -qiE "^(item[0-9]+\.)?TEL" "$SCR/clinic.vcf" && [ "$CSZ" -lt 3000000 ] \
  || { say "!! [5/8] what came back is not a clinic contact card - nothing placed"; exit 1; }
\cp -p "$PK" "$BAK_PK" && \cp -p "$SN" "$BAK_SN" || { say "!! [5/8] backup failed - nothing placed"; exit 1; }
[ "$(m5 "$BAK_PK")" = "$FROM_PK" ] && [ "$(m5 "$BAK_SN")" = "$FROM_SN" ] || { say "!! [5/8] a backup is not the live file - nothing placed"; exit 1; }
say "[5/8] the card fetched and checked ($CSZ bytes, a vCard with a name and numbers); backups beside both files"

\cp -p packs.html "$FIN/.packs.html.s529" && \cp -p setup_notes.py "$FIN/.setup_notes.py.s529" \
  || { rm -f "$FIN/.packs.html.s529" "$FIN/.setup_notes.py.s529"; say "!! [6/8] could not stage the files - nothing placed"; exit 1; }
mkdir "$SCR/save" && \cp save/index.php "$SCR/save/index.php" && \cp "$SCR/clinic.vcf" "$SCR/save/clinic.vcf" \
  && chown -R --reference="$DOCROOT" "$SCR/save" && chmod 755 "$SCR/save" && chmod 644 "$SCR/save/index.php" "$SCR/save/clinic.vcf" \
  || { rm -f "$FIN/.packs.html.s529" "$FIN/.setup_notes.py.s529"; say "!! [6/8] could not prepare the save page - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.packs.html.s529" "$PK" || restore "placing packs.html"
mv -f "$FIN/.setup_notes.py.s529" "$SN" || restore "placing setup_notes.py"
mv "$SCR/save" "$SAVE" && SAVE_PLACED=1 || restore "placing the save page"
[ "$(m5 "$PK")" = "$TO_PK" ] && [ "$(m5 "$SN")" = "$TO_SN" ] && [ "$(m5 "$SAVE/index.php")" = "$TO_PH" ] || restore "the files did not land at their pins"
say "[6/8] placed: packs.html, setup_notes.py, $SAVE (owner $(stat -c %U "$SAVE"))"

systemctl restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$c1" = 200 ] && break; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/packs")
systemctl is-active --quiet "$SVC" || restore "$SVC is not active"
{ [ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ] || [ "$c2" = 303 ]; }; } || restore "finance health $c1 / packs $c2"
say "[7/8] $SVC active - health $c1 - the packs page without a login $c2 (302 expected)"

P1="$(curl -s -m 20 -A "$UA_ANDROID" "https://$SITE/save/")"
H2="$(curl -s -m 20 -D - -o "$SCR/card.out" "https://$SITE/save/?card=1")"
echo "$P1" | grep -q "intent:#Intent;action=android.intent.action.INSERT" && echo "$P1" | grep -q "Save to my contacts" \
  || restore "the save page did not answer as itself over https (WordPress or the web server took the address)"
echo "$H2" | grep -qi "^content-type: text/vcard" && grep -q "BEGIN:VCARD" "$SCR/card.out" || restore "the card is not served as a contact card"
PLACED=0
say "[8/8] https://$SITE/save/ answers: Android gets the phone's own new-contact form, filled in; ?card=1 is served as a contact card"
md5sum "$PK" "$SN" "$SAVE/index.php"
say "$KIT: DONE"
say "read next: https://$SITE/save/"
say "undo: \\cp -p $BAK_PK $PK && \\cp -p $BAK_SN $SN && mv $SAVE $SAVE.removed_S529 && systemctl restart $SVC"
