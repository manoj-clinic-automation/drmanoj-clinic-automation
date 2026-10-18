#!/bin/bash
# =============================================================================
#  install_S590_WEBSITE_MAIL_RELAY.sh · kit S590 (session S326, 18-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S590_WEBSITE_MAIL_RELAY/install_S590_WEBSITE_MAIL_RELAY.sh
#  (DRY=1 before bash: every check, including the Gmail sign-in, nothing changed.)
#
#  THE OWNER, 18:27 IST 18-Oct: "Why not do this now, if possible?" -- the website's mail (S588: WordPress hands it to this box's
#  postfix, which sends it direct; Gmail refuses it as unauthenticated, 550-5.7.26) is sent through smtp.gmail.com:587, signed in
#  as the clinic Gmail -- the account and app password the daily health mail already uses (/root/wa/.env). The password goes into
#  postfix's own map, root-only (600); WordPress never sees it.
#   1. Checks: postfix active; no relay set today (any -> stop and ask); the env file's login signs in to Gmail (nothing sent).
#   2. /etc/postfix/main.cf kept in /root/s590_backup/ (and the settings before, as postconf -n).
#   3. The relay: the sasl map (600) + postmap; relayhost [smtp.gmail.com]:587, SASL on, TLS required; postfix check; reload.
#   4. Two tests to the clinic inbox: sendmail as root, and PHP's own mail() as the website's user (the road WordPress takes) --
#      each must show "status=sent ... relay=smtp.gmail.com" in the mail log within 90 s. Red -> main.cf put back, map removed,
#      postfix reloaded.
#  Nothing else on the box changes; no clinic program is restarted.
# =============================================================================
set -u
KIT="S590_WEBSITE_MAIL_RELAY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
ENVF="${ENVF:-/root/wa/.env}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s590_backup}"
MAINCF="${MAINCF:-/etc/postfix/main.cf}"
SASL="${SASL:-/etc/postfix/sasl/sasl_passwd}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
SITE="${SITE:-drmanojagarwal.com}"
SITEDIR="${SITEDIR:-/home/$SITE/public_html}"
MAILLOG="${MAILLOG:-/var/log/mail.log}"
SENDMAIL="${SENDMAIL:-/usr/sbin/sendmail}"
RUNUSER="${RUNUSER:-runuser}"
STAMP="$(date +%Y%m%d_%H%M%S)"
HAVE_LOCK=0; PLACED=0
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the mail settings back"
  [ -f "$BK/main.cf" ] && \cp -p "$BK/main.cf" "$MAINCF"
  rm -f "$SASL" "$SASL.db" "$SASL.lmdb"
  postfix check >/dev/null 2>&1 && "$SYSTEMCTL" reload postfix
  say "   relay now: '$(postconf -h relayhost 2>/dev/null)' (expected empty) · postfix $("$SYSTEMCTL" is-active postfix)"
  say "   Send a photo of this screen to Claude."
  exit 1
}
mlog() { { cat "$MAILLOG" /var/log/maillog 2>/dev/null; journalctl -u postfix --since "-15 min" --no-pager -q 2>/dev/null; }; }
qid_for() { mlog | grep -F "message-id=<$1>" | sed -n 's/.*\]: \([0-9A-Za-z]\{6,\}\): .*/\1/p' | tail -1; }
wait_sent() {   # $1 = message id; prints the status line once it has one
  local q="" line="" i
  for i in $(seq 1 30); do
    sleep 3
    [ -z "$q" ] && q="$(qid_for "$1")"
    [ -n "$q" ] && line="$(mlog | grep -F "$q: " | grep -E 'status=(sent|deferred|bounced)' | tail -1)"
    [ -n "$line" ] && break
  done
  echo "${line:-no status line for <$1> within 90 s}" | sed -E 's/to=<[^>]*>/to=<clinic inbox>/; s/\[[0-9.]+\]/[ip]/g' | cut -c1-200
}

say "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
say "[1/5] kit files match SUMS.md5"

"$SYSTEMCTL" is-active --quiet postfix || stop "postfix is not running"
RH="$(postconf -h relayhost 2>/dev/null)"
if [ "$RH" = "[smtp.gmail.com]:587" ] && { [ -f "$SASL.db" ] || [ -f "$SASL.lmdb" ]; }; then
  say "ALREADY INSTALLED (relay $RH)."; INST=0
else
  [ -z "$RH" ] || stop "a relay is already set ('$RH') -- not this kit's"
  [ -r "$ENVF" ] || stop "$ENVF is not readable"
  postfix check >/dev/null 2>&1 || stop "postfix check fails already, before any change"
  L="$("$PY" -B relay_s590.py check "$ENVF" 2>&1)" || stop "the Gmail sign-in failed ($L)"
  say "[2/5] checks: postfix active · no relay today · Gmail sign-in from the env file: $L"
  if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every check green; NOTHING changed"; exit 0; fi

  mkdir -p "$BK" && chmod 700 "$BK" || stop "no backup folder"
  \cp -p "$MAINCF" "$BK/main.cf" && postconf -n > "$BK/postconf_before.txt" 2>/dev/null || stop "the backup of main.cf failed"
  chmod 600 "$BK/postconf_before.txt"
  cmp -s "$MAINCF" "$BK/main.cf" || stop "the backup is not the live main.cf"
  say "[3/5] kept: $BK/main.cf · $BK/postconf_before.txt"

  PLACED=1
  W="$("$PY" -B relay_s590.py write "$ENVF" "$SASL" 2>&1)" || restore "writing the sign-in map ($W)"
  DBT="$(postconf -h default_database_type 2>/dev/null)"; DBT="${DBT:-hash}"
  chown root:root "$SASL" || restore "chown of the map"
  chmod 600 "$SASL" || restore "chmod of the map"
  postmap "$DBT:$SASL" || restore "postmap $DBT"
  chmod 600 "$SASL".* 2>/dev/null
  CA=/etc/ssl/certs/ca-certificates.crt; [ -f "$CA" ] || CA=""
  postconf -e "relayhost = [smtp.gmail.com]:587" "smtp_sasl_auth_enable = yes" \
    "smtp_sasl_password_maps = $DBT:$SASL" "smtp_sasl_security_options = noanonymous" \
    "smtp_sasl_tls_security_options = noanonymous" "smtp_tls_security_level = encrypt" ${CA:+"smtp_tls_CAfile = $CA"} \
    || restore "postconf"
  postfix check >/dev/null 2>&1 || restore "postfix check failed: $(postfix check 2>&1 | grep -iv warning | head -1)"
  "$SYSTEMCTL" reload postfix || restore "postfix reload"
  "$SYSTEMCTL" is-active --quiet postfix || restore "postfix not active after reload"
  say "[4/5] placed: $W · relay $(postconf -h relayhost) · SASL $(postconf -h smtp_sasl_auth_enable) · TLS $(postconf -h smtp_tls_security_level) · postfix reloaded"
  INST=1
fi

TO="$("$PY" -B relay_s590.py to "$ENVF" 2>/dev/null)"
[ -n "$TO" ] || { [ "$INST" = 1 ] && restore "no test address"; stop "no test address"; }
MID1="s590-root-$STAMP@$(hostname -f 2>/dev/null || hostname)"
printf 'From: "Clinic server test" <wordpress@%s>\nTo: %s\nSubject: S590 test 1 of 2 - server mail route %s\nMessage-ID: <%s>\n\nTest 1 of 2 from kit S590: the server mail now goes out through the clinic Gmail. Nothing to do; safe to delete.\n' \
  "$SITE" "$TO" "$STAMP" "$MID1" | "$SENDMAIL" -i -f "wordpress@$SITE" -t
R1="$(wait_sent "$MID1")"
SU="$(stat -c %U "$SITEDIR" 2>/dev/null)"
PHP="${PHP_BIN:-$(ls -1 /usr/local/lsws/lsphp*/bin/php 2>/dev/null | sort -V | tail -1)}"; [ -n "$PHP" ] || PHP="$(command -v php)"
MID2="s590-php-$STAMP@$SITE"
if [ -n "$SU" ] && [ -n "$PHP" ]; then
  "$RUNUSER" -u "$SU" -- "$PHP" -r '$h="From: \"Website test\" <wordpress@'"$SITE"'>\r\nMessage-ID: <'"$MID2"'>"; echo mail("'"$TO"'", "S590 test 2 of 2 - the website mail route '"$STAMP"'", "Test 2 of 2 from kit S590: sent by PHP mail() as the website user, the road WordPress takes. Nothing to do; safe to delete.", $h) ? "" : "php mail() returned false";' 2>&1 | head -2
  R2="$(wait_sent "$MID2")"
else
  R2="not run (website user '$SU' / php '$PHP' not found)"
fi
say "[5/5] test 1 (server): $R1"
say "      test 2 (website road, as $SU): $R2"
OK1=$(echo "$R1" | grep -c 'status=sent'); OK2=$(echo "$R2" | grep -c 'status=sent')
VIA1=$(echo "$R1" | grep -c 'relay=smtp.gmail.com'); VIA2=$(echo "$R2" | grep -c 'relay=smtp.gmail.com')
if [ "$INST" = 1 ] && { [ "$OK1" = 0 ] || [ "$VIA1" = 0 ]; }; then restore "test 1 did not go out through Gmail"; fi
say ""
if [ "$OK2" = 1 ] && [ "$VIA2" = 1 ]; then
  say "INSTALLED. The website's mail now goes out through the clinic Gmail. Two test mails are on their way to the clinic inbox."
else
  say "INSTALLED for the server (test 1 green); the website road (test 2) did not show 'sent' -- send a photo to Claude."
fi
say "undo: see the README (main.cf is kept in $BK)"
