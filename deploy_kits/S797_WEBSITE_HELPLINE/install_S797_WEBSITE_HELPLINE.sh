#!/bin/bash
# =============================================================================
#  install_S797_WEBSITE_HELPLINE.sh . kit S797 (12-Nov-2026, session S435, the parent) . the owner 08:08 / 08:21 IST: the helpline
#  number is to be made known everywhere -- on the website it is shown first, the old number beside it.
#  The two numbers are GIVEN ON THE LINE (no number is kept in the repository, F-185):
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s797kit && \cp -rp /root/deploy/repo/deploy_kits/S797_WEBSITE_HELPLINE /tmp/s797kit && HELPLINE=<helpline> OLD=<old number> bash /tmp/s797kit/install_S797_WEBSITE_HELPLINE.sh
#  ONE new file on the website: wp-content/mu-plugins/clinic-helpline-number.php (WordPress loads it by itself). On the public pages
#  every call link dials the helpline and the number shown reads "helpline, old number"; WhatsApp links are untouched. Nothing in the
#  website's database is changed, no plugin or theme file is edited, nothing is restarted.
#  DRY=1 before bash: every check, and the home page as it WOULD read -- nothing placed.
#  Undo:  bash /tmp/s797kit/install_S797_WEBSITE_HELPLINE.sh --undo
# =============================================================================
set -u
KIT="S797_WEBSITE_HELPLINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SITE="${SITE:-/home/drmanojagarwal.com/public_html}"
URL="${URL:-https://drmanojagarwal.com/}"
MU="$SITE/wp-content/mu-plugins"
N1="$MU/clinic-helpline-number.php"
HELPLINE="${HELPLINE:-}"; OLD="${OLD:-}"
SCR=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
trap '[ -n "$SCR" ] && rm -rf "$SCR"' EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing on the website was changed.} Send a photo of this screen to Claude."; exit 1; }
# fetch <url> <file> -> prints the HTTP status
fetch() {
  if [ -n "${S797_FAKE_FETCH:-}" ]; then
    if [ -f "$N1" ] && [ -n "${S797_FAKE_FETCH_AFTER:-}" ]; then \cp "$S797_FAKE_FETCH_AFTER" "$2"; else \cp "$S797_FAKE_FETCH" "$2"; fi; echo 200
  else curl -sS -m 40 -L -A "Mozilla/5.0 (S797 check)" -o "$2" -w '%{http_code}' "$1" 2>/dev/null; fi
}
cnt() { grep -o -i -E "$1" "$2" 2>/dev/null | wc -l | tr -d ' '; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
if [ "${1:-}" = "--undo" ]; then
  if [ -f "$N1" ]; then mv -f "$N1" "/root/s797_undone_$(date +%Y%m%d_%H%M%S).txt" && echo "UNDONE: the website shows the old number as before (the file was moved out to /root/s797_undone_*.txt)"; else echo "Nothing to undo: $N1 is not there."; fi
  exit 0
fi
case "$HELPLINE" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) stop "give the helpline number on the line: HELPLINE=<10 digits> OLD=<10 digits> bash ...";; esac
case "$OLD" in [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;; *) stop "give the old number on the line: HELPLINE=<10 digits> OLD=<10 digits> bash ...";; esac
[ "$HELPLINE" != "$OLD" ] || stop "the two numbers are the same"
PHPBIN="${PHPBIN:-}"
if [ -z "$PHPBIN" ]; then for c in "$(command -v php 2>/dev/null)" /usr/local/lsws/lsphp8*/bin/php /usr/local/lsws/lsphp7*/bin/php /usr/bin/php; do [ -n "$c" ] && [ -x "$c" ] && { PHPBIN="$c"; break; }; done; fi
[ -n "$PHPBIN" ] && [ -x "$PHPBIN" ] || stop "no PHP program found to check the file with"
[ -f "$SITE/wp-config.php" ] && [ -d "$SITE/wp-content" ] || stop "the website is not at $SITE"
SCR=$(mktemp -d /tmp/s797.XXXX); chmod 700 "$SCR"
sed -e "s/@@OLD@@/$OLD/g" -e "s/@@NEW@@/$HELPLINE/g" clinic-helpline-number.php.tpl > "$SCR/plugin.php" || stop "could not make the file"
grep -q '@@' "$SCR/plugin.php" && stop "the made file still holds a placeholder"
"$PHPBIN" -l "$SCR/plugin.php" >/dev/null 2>&1 || stop "the made file does not pass PHP's own check"
R=$(TMPDIR="$SCR" "$PHPBIN" walk_s797.php "$KDIR" 2>&1 | tail -1)
case "$R" in "WALK OK"*) ;; *) (TMPDIR="$SCR" "$PHPBIN" walk_s797.php "$KDIR" 2>&1 | grep -E '^BAD|rror' | head -6); stop "the walk is not green ($R)";; esac
mkdir -p "$SCR/none"
R2=$("$PHPBIN" walk_s797.php "$SCR/none" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control without the template did not go red ($R2)";; esac
echo "[1/5] kit files match; PHP $("$PHPBIN" -r 'echo PHP_VERSION;' 2>/dev/null); the walk: $R | without the template: $R2"
NEWSUM=$(m5 "$SCR/plugin.php")
if [ -f "$N1" ] && [ "$(m5 "$N1")" = "$NEWSUM" ]; then echo "-- ALREADY INSTALLED with these two numbers. Nothing written."; exit 0; fi
[ -e "$N1" ] && [ "${REPLACE:-0}" != 1 ] && stop "$N1 is there already and differs (other numbers?). Run with --undo first, or REPLACE=1"
C0=$(fetch "$URL" "$SCR/before.html")
[ "$C0" = 200 ] || stop "the website's home page did not answer 200 (it answered $C0)"
B_OLD=$(cnt "href=[\"']tel:[^\"']*$OLD" "$SCR/before.html"); B_WA=$(cnt "(whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*$OLD" "$SCR/before.html")
[ "$B_OLD" -ge 1 ] || stop "the home page shows no call link to the old number -- nothing for this kit to do (old number given: ...${OLD: -4})"
A=$("$PHPBIN" walk_s797.php --apply "$SCR/plugin.php" "$SCR/before.html" "$SCR/would.html" 2>&1 | tail -1)
W_OLD=$(cnt "href=[\"']tel:[^\"']*$OLD" "$SCR/would.html"); W_NEW=$(cnt "href=[\"']tel:\+91$HELPLINE[\"']" "$SCR/would.html"); W_WA=$(cnt "(whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*$OLD" "$SCR/would.html")
[ "$W_OLD" = 0 ] && [ "$W_NEW" = "$B_OLD" ] && [ "$W_WA" = "$B_WA" ] || stop "today's home page through the file does not come out as expected ($A)"
echo "[2/5] today's home page through the file: $A"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing placed."; exit 0; }
mkdir -p "$MU" || stop "could not make $MU"
chown --reference="$SITE/wp-content" "$MU" 2>/dev/null
\cp "$SCR/plugin.php" "$N1.s797new" && chown --reference="$SITE/wp-content" "$N1.s797new" 2>/dev/null; chmod 644 "$N1.s797new" && mv -f "$N1.s797new" "$N1" || stop "could not place $N1"
[ "$(m5 "$N1")" = "$NEWSUM" ] || { rm -f "$N1"; stop "the read-back did not match (removed again)"; }
echo "[3/5] placed $N1 (${NEWSUM:0:8})"
sleep "${S797_WAIT:-2}"
C1=$(fetch "${URL}?s797=$(date +%s)" "$SCR/after.html")
L_OLD=$(cnt "href=[\"']tel:[^\"']*$OLD" "$SCR/after.html"); L_NEW=$(cnt "href=[\"']tel:\+91$HELPLINE[\"']" "$SCR/after.html"); L_WA=$(cnt "(whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*$OLD" "$SCR/after.html")
S0=$(wc -c < "$SCR/before.html"); S1=$(wc -c < "$SCR/after.html")
if [ "$C1" != 200 ] || [ "$L_OLD" != 0 ] || [ "$L_NEW" -lt 1 ] || [ "$L_WA" != "$B_WA" ] || [ "$S1" -lt $((S0 * 9 / 10)) ]; then
  mv -f "$N1" "/root/s797_undone_$(date +%Y%m%d_%H%M%S).txt"
  C2=$(fetch "${URL}?s797b=$(date +%s)" "$SCR/back.html")
  stop "the live page after placing was not as expected (status $C1; call links old $L_OLD, helpline $L_NEW; WhatsApp links $L_WA of $B_WA; bytes $S0 -> $S1)" "The file was taken out again; the home page now answers $C2."
fi
echo "[4/5] the live home page now: status $C1; call links to the helpline $L_NEW, to the old number $L_OLD; WhatsApp links $L_WA (as before); bytes $S0 -> $S1"
echo "[5/5] $KIT: DONE. Every call link on the website dials the helpline; the number shown reads helpline first, the old number beside it."
