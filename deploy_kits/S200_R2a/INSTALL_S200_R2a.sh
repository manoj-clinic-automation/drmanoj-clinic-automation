#!/usr/bin/env bash
# S200_R2a — bring the Staff Register/Salary flow under the portal PWA origin.
# Appends ONE proxy block to the LIVE followup vhost. Backup + graceful restart
# + probe (/register AND /portal AND /finance) + auto-rollback on any failure.
# Nothing is removed; attendance.dr-manoj.in/register keeps working too.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
VH="/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf"
LSWSCTRL="/usr/local/lsws/bin/lswsctrl"
BLOCK="$KIT/register_proxy.block"
BLOCK_MD5="24738a34c86b8ef054ec01997e47a32c"
md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
probe(){ curl -s -k -o /dev/null -m 6 -w '%{http_code}' -H "Host: followup.dr-manoj.in" "https://127.0.0.1$1" 2>/dev/null || echo 000; }
bad(){ case "$1" in 000|502|503) return 0;; *) return 1;; esac; }

# 0) sanity gates
[ -f "$VH" ]  || { echo "REFUSE: live vhost not found at $VH"; exit 1; }
[ -f "$BLOCK" ] || { echo "REFUSE: block file missing from kit"; exit 1; }
[ "$(md5of "$BLOCK")" = "$BLOCK_MD5" ] || { echo "REFUSE: block bytes unexpected ($(md5of "$BLOCK"))"; exit 1; }
[ -x "$LSWSCTRL" ] || { echo "REFUSE: lswsctrl not executable at $LSWSCTRL"; exit 1; }

# 1) idempotency
if grep -qE '^[[:space:]]*context[[:space:]]+/register\b' "$VH"; then
  echo "/register already present in $VH — nothing to do."; exit 0
fi

# 2) don't wire a dead backend
bcode="$(curl -s -o /dev/null -m 5 -w '%{http_code}' http://127.0.0.1:8044/register/health 2>/dev/null || echo 000)"
[ "$bcode" = "200" ] || { echo "REFUSE: register backend 127.0.0.1:8044 not healthy (got $bcode) — start staff-register first."; exit 1; }

# 3) baseline: existing paths must answer BEFORE we touch anything
pre_por="$(probe /portal)"; pre_fin="$(probe /finance)"
echo "pre:  /portal=$pre_por  /finance=$pre_fin"
if bad "$pre_por" || bad "$pre_fin"; then
  echo "REFUSE: an existing path is already not answering — fix that first, not now."; exit 1
fi

# 4) backup + append
TS="$(date +%Y%m%d_%H%M%S)"; BAK="$VH.bak_S200_R2a_$TS"
cp -p "$VH" "$BAK"; echo "backup: $BAK"
printf '\n' >> "$VH"; cat "$BLOCK" >> "$VH"

# 5) graceful restart
"$LSWSCTRL" restart >/tmp/s200_r2a_lsws.log 2>&1 || true
sleep 3

# 6) probe all three
new="$(probe /register/health)"; por="$(probe /portal)"; fin="$(probe /finance)"
echo "post: /register/health=$new  /portal=$por  /finance=$fin"

new_ok=0; case "$new" in 200|301|302) new_ok=1;; esac
if [ "$new_ok" = 1 ] && ! bad "$por" && ! bad "$fin"; then
  echo "== DONE. https://followup.dr-manoj.in/register is live; /portal and /finance still answer. =="
  echo "   attendance.dr-manoj.in/register is untouched and still works."
  echo "   backup kept: $BAK"
else
  echo "PROBE FAILED (new=$new por=$por fin=$fin) — ROLLING BACK."
  cp -p "$BAK" "$VH"
  "$LSWSCTRL" restart >>/tmp/s200_r2a_lsws.log 2>&1 || true
  sleep 3
  r_por="$(probe /portal)"; r_fin="$(probe /finance)"
  echo "rolled back. recheck: /portal=$r_por /finance=$r_fin  (log: /tmp/s200_r2a_lsws.log)"
  exit 1
fi
