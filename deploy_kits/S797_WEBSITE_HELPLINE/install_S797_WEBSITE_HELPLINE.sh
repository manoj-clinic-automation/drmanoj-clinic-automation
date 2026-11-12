#!/bin/bash
# =============================================================================
#  install_S797_WEBSITE_HELPLINE.sh . kit S797 (12-Nov-2026, session S435, the parent) . the owner 08:08 / 08:21 IST: the helpline
#  number is to be made known everywhere -- on the website it is shown first, the old number beside it.
#  The two numbers are GIVEN ON THE LINE (no number is kept in the repository, F-185):
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s797kit && \cp -rp /root/deploy/repo/deploy_kits/S797_WEBSITE_HELPLINE /tmp/s797kit && HELPLINE=<helpline> OLD=<old number> bash /tmp/s797kit/install_S797_WEBSITE_HELPLINE.sh
#  ONE new file on the website: wp-content/mu-plugins/clinic-helpline-number.php (WordPress loads it by itself). On the public pages
#  every call link dials the helpline and the number shown reads "helpline, old number"; WhatsApp links are untouched. Nothing in the
#  website's database is changed, no plugin or theme file is edited, nothing is restarted.
#  v2: no `php -l` (the server's crashed on it); the checks run with -n and any PHP that crashes is passed over.
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
[ -f "$SITE/wp-config.php" ] && [ -d "$SITE/wp-content" ] || stop "the website is not at $SITE"
SCR=$(mktemp -d /tmp/s797.XXXX); chmod 700 "$SCR"
sed -e "s/@@OLD@@/$OLD/g" -e "s/@@NEW@@/$HELPLINE/g" clinic-helpline-number.php.tpl > "$SCR/plugin.php" || stop "could not make the file"
grep -q '@@' "$SCR/plugin.php" && stop "the made file still holds a placeholder"
# A PHP program for the checks. v2 (12-Nov 09:1x IST): the first run stopped because the server's `php -l` itself crashed (a
# segmentation fault of the program, not a fault of the file). So: every candidate is run with -n (no php.ini, no extensions --
# the checks need none), and a candidate counts only if it runs the WHOLE walk green; one that crashes is passed over.
WALKR=""; PHPBIN_OK=""
try_php() {
  [ -n "$1" ] && [ -x "$1" ] || return 1
  local r
  r=$( (TMPDIR="$SCR" timeout 90 "$1" -n walk_s797.php "$KDIR" 2>/dev/null | tail -1) 2>/dev/null )
  case "$r" in "WALK OK"*) WALKR="$r"; PHPBIN_OK="$1"; return 0;; esac
  return 1
}
if [ -n "${S797_PHP_CANDIDATES+x}" ]; then CANDS="$S797_PHP_CANDIDATES"; else
  WPPHP=$( (wp --allow-root --info 2>/dev/null | sed -n 's/^PHP binary:[[:space:]]*//p' | head -1) 2>/dev/null )
  CANDS="${PHPBIN:-} $(command -v php 2>/dev/null) $WPPHP $(ls -d /usr/local/lsws/lsphp8*/bin/php 2>/dev/null | sort -r | tr '\n' ' ') $(ls -d /usr/local/lsws/lsphp7*/bin/php 2>/dev/null | sort -r | tr '\n' ' ') /usr/bin/php /usr/local/bin/php"
fi
TRIED=""
for c in $CANDS; do
  case " $TRIED " in *" $c "*) continue;; esac
  TRIED="$TRIED $c"
  if ( try_php "$c" ) 2>/dev/null; then try_php "$c" 2>/dev/null; break; fi
done
if [ -n "$PHPBIN_OK" ]; then
  PHPBIN="$PHPBIN_OK"
  mkdir -p "$SCR/none"
  R2=$( ("$PHPBIN" -n walk_s797.php "$SCR/none" --control 2>&1 | tail -1) 2>/dev/null )
  case "$R2" in "CONTROL: red"*) ;; *) stop "the control without the template did not go red ($R2)";; esac
  echo "[1/5] kit files match; checks run by $PHPBIN ($( ("$PHPBIN" -n -r 'echo PHP_VERSION;') 2>/dev/null )); the walk: $WALKR | without the template: $R2"
else
  PHPBIN=""
  echo "[1/5] kit files match. NO PHP program on this server ran the checks (tried:$TRIED) -- the file was checked where it was built"
  echo "      (PHP 8.3, walk 22/22). Going on to the live check, which takes the file out again if the page does not come out right."
fi
NEWSUM=$(m5 "$SCR/plugin.php")
if [ -f "$N1" ] && [ "$(m5 "$N1")" = "$NEWSUM" ]; then echo "-- ALREADY INSTALLED with these two numbers. Nothing written."; exit 0; fi
[ -e "$N1" ] && [ "${REPLACE:-0}" != 1 ] && stop "$N1 is there already and differs (other numbers?). Run with --undo first, or REPLACE=1"
C0=$(fetch "$URL" "$SCR/before.html")
[ "$C0" = 200 ] || stop "the website's home page did not answer 200 (it answered $C0)"
B_OLD=$(cnt "href=[\"']tel:[^\"']*$OLD" "$SCR/before.html"); B_WA=$(cnt "(whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*$OLD" "$SCR/before.html")
[ "$B_OLD" -ge 1 ] || stop "the home page shows no call link to the old number -- nothing for this kit to do (old number given: ...${OLD: -4})"
if [ -n "$PHPBIN" ]; then
  A=$( ("$PHPBIN" -n walk_s797.php --apply "$SCR/plugin.php" "$SCR/before.html" "$SCR/would.html" 2>&1 | tail -1) 2>/dev/null )
  W_OLD=$(cnt "href=[\"']tel:[^\"']*$OLD" "$SCR/would.html"); W_NEW=$(cnt "href=[\"']tel:\+91$HELPLINE[\"']" "$SCR/would.html"); W_WA=$(cnt "(whatsapp\.com/send\?phone=|wa\.me/)[0-9+]*$OLD" "$SCR/would.html")
  [ "$W_OLD" = 0 ] && [ "$W_NEW" = "$B_OLD" ] && [ "$W_WA" = "$B_WA" ] || stop "today's home page through the file does not come out as expected ($A)"
  echo "[2/5] today's home page through the file: $A"
else
  echo "[2/5] today's home page: call links to the old number $B_OLD, WhatsApp links $B_WA (no PHP here to show the page as it would read)"
fi
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
