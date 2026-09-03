#!/usr/bin/env bash
# S222 — bring the SCAN APP under the portal PWA origin, so a staff member scanning
# a bill is not thrown out of the app window.
#
# This is S200_R2a's installer, which has run on this exact vhost, with two changes:
#   * the backend port is DISCOVERED rather than hard-coded — by asking each candidate
#     for the /healthz the app patch just added. No port is guessed and none is asked of
#     the owner.
#   * the block carries a __PORT__ placeholder, so the md5 gate is on the template.
#
# Appends ONE proxy block to the LIVE followup vhost. Backup + graceful restart + probe
# (/scanapp AND /portal AND /finance AND /register) + AUTO-ROLLBACK on any failure.
# Nothing is removed; assets.dr-manoj.in keeps working exactly as it does today.
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
VH="/usr/local/lsws/conf/vhosts/followup.dr-manoj.in/vhost.conf"
LSWSCTRL="/usr/local/lsws/bin/lswsctrl"
TMPL="$KIT/scanapp_proxy.block.tmpl"
TMPL_MD5="c4de02827f9e669a695ee85839e881ac"
CANDIDATES="${ASSET_PORT:-} 8030 8031 8032 8033 8090 8098 8101 8102 5000 5010"

md5of(){ md5sum "$1" 2>/dev/null | cut -d' ' -f1; }
probe(){ curl -s -k -o /dev/null -m 6 -w '%{http_code}' -H "Host: followup.dr-manoj.in" "https://127.0.0.1$1" 2>/dev/null || echo 000; }
bad(){ case "$1" in 000|502|503) return 0;; *) return 1;; esac; }

# 0) sanity gates
[ -f "$VH" ]     || { echo "REFUSE: live vhost not found at $VH"; exit 1; }
[ -f "$TMPL" ]   || { echo "REFUSE: block template missing from kit"; exit 1; }
[ "$(md5of "$TMPL")" = "$TMPL_MD5" ] || { echo "REFUSE: template bytes unexpected ($(md5of "$TMPL"))"; exit 1; }
[ -x "$LSWSCTRL" ] || { echo "REFUSE: lswsctrl not executable at $LSWSCTRL"; exit 1; }

# 1) idempotency
if grep -qE '^[[:space:]]*context[[:space:]]+/scanapp\b' "$VH"; then
  echo "/scanapp already present in $VH — nothing to do."; exit 0
fi

# 2) FIND the backend by asking for the health route the app patch added.
#    If none answers, the app has not been patched or not restarted — refuse.
PORT=""
for p in $CANDIDATES; do
  [ -n "$p" ] || continue
  code="$(curl -s -o /dev/null -m 3 -w '%{http_code}' "http://127.0.0.1:$p/healthz" 2>/dev/null || echo 000)"
  if [ "$code" = "200" ]; then PORT="$p"; break; fi
done
if [ -z "$PORT" ]; then
  echo "REFUSE: no scan-app backend answered /healthz on: $CANDIDATES"
  echo "        Patch asset_register.py and 'systemctl restart assetapp.service' first,"
  echo "        or re-run with ASSET_PORT=<port> if it listens somewhere else."
  exit 1
fi
echo "backend: 127.0.0.1:$PORT answers /healthz"

# 3) and prove the PREFIX works on that backend before wiring anything to it
pcode="$(curl -s -o /dev/null -m 3 -w '%{http_code}' "http://127.0.0.1:$PORT/scanapp/healthz" 2>/dev/null || echo 000)"
[ "$pcode" = "200" ] || { echo "REFUSE: backend does not answer /scanapp/healthz (got $pcode) — the prefix patch is not live."; exit 1; }
echo "prefix : /scanapp/healthz answers on the backend"

# 4) baseline: everything already live must answer BEFORE we touch the vhost
pre_por="$(probe /portal)"; pre_fin="$(probe /finance)"; pre_reg="$(probe /register/health)"
echo "pre:  /portal=$pre_por  /finance=$pre_fin  /register/health=$pre_reg"
if bad "$pre_por" || bad "$pre_fin"; then
  echo "REFUSE: an existing path is already not answering — fix that first, not now."; exit 1
fi

# 5) backup + append
BLK="$(mktemp)"; sed "s/__PORT__/$PORT/" "$TMPL" > "$BLK"
TS="$(date +%Y%m%d_%H%M%S)"; BAK="$VH.bak_S222_scanapp_$TS"
cp -p "$VH" "$BAK"; echo "backup: $BAK"
printf '\n' >> "$VH"; cat "$BLK" >> "$VH"; rm -f "$BLK"

# 6) graceful restart
"$LSWSCTRL" restart >/tmp/s222_scanapp_lsws.log 2>&1 || true
sleep 3

# 7) probe the new path AND everything that was already working
new="$(probe /scanapp/healthz)"; por="$(probe /portal)"; fin="$(probe /finance)"; reg="$(probe /register/health)"
echo "post: /scanapp/healthz=$new  /portal=$por  /finance=$fin  /register/health=$reg"

new_ok=0; case "$new" in 200|301|302) new_ok=1;; esac
if [ "$new_ok" = 1 ] && ! bad "$por" && ! bad "$fin" && ! bad "$reg"; then
  echo "== DONE. https://followup.dr-manoj.in/scanapp is live; /portal, /finance and /register still answer. =="
  echo "   assets.dr-manoj.in is untouched and still works."
  echo "   backup kept: $BAK"
else
  echo "PROBE FAILED (new=$new por=$por fin=$fin reg=$reg) — ROLLING BACK."
  cp -p "$BAK" "$VH"
  "$LSWSCTRL" restart >>/tmp/s222_scanapp_lsws.log 2>&1 || true
  sleep 3
  r_por="$(probe /portal)"; r_fin="$(probe /finance)"; r_reg="$(probe /register/health)"
  echo "rolled back. recheck: /portal=$r_por /finance=$r_fin /register/health=$r_reg  (log: /tmp/s222_scanapp_lsws.log)"
  exit 1
fi
