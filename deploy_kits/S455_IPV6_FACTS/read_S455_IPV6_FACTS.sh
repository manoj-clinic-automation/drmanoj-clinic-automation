#!/bin/bash
# =============================================================================
# read_S455_IPV6_FACTS.sh -- session 291, 03-Oct-2026 -- the parent. READ-ONLY.
# It places nothing, edits nothing and restarts nothing on this server. Two readings:
#   [1/2] the Reception PC kit that the Clinic PCs page serves (deploy_kits/PC_KITS/reception) is WHOLE after this pull:
#         kit.zip and the bundled Python are exactly what KIT_INFO.txt names, and exactly what was rehearsed on that PC.
#         (03-Oct: secure_setup.cmd joined the kit, so the firewall rules come back after a Windows reinstall.)
#   [2/2] what this server has for IPv6 (F-692) -> /root/finance/ipv6_facts_s455.json, mode 600, which the 01:35 code
#         bundle carries to the owner's PC. The change itself is a later kit, built from this file, never from a guess.
# It takes the server-wide build lock (CLAUDE.md; F-694) and releases it on every exit.
# =============================================================================
set -u
KIT="S455_IPV6_FACTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
KITS="${KITS:-$(cd "$KDIR/.." && pwd)/PC_KITS}"
OUT="${OUT:-/root/finance/ipv6_facts_s455.json}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
PCKITS_LIVE="${PCKITS_LIVE:-/root/finance/pc_kits.py}"
KITZIP=994871f3a3cb821235db9131e561f33e; PYZIP=30a7b6ab01fbaa598844f4b3d8220a68
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
say ""
say "S455 -- READ ONLY. Nothing on this server is changed by this line."
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! SUMS.md5 gate failed - nothing read"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! KIT_ID.txt names another kit - nothing read"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing read."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT

RED=0
GK="$(m5 "$KITS/reception/kit.zip")"; GP="$(m5 "$KITS/_shared/pyportable_3.11.9.zip")"
if [ "$GK" = "$KITZIP" ] && [ "$GP" = "$PYZIP" ] && grep -q "^kit_md5=$KITZIP$" "$KITS/reception/KIT_INFO.txt" && grep -q "^python_md5=$PYZIP$" "$KITS/reception/KIT_INFO.txt"; then
  say "   [1/2] the Reception PC kit on this server : WHOLE - the one rehearsed on that PC on 03-Oct (with the firewall step)"
else
  RED=1
  say "!! [1/2] the Reception PC kit on this server is NOT the rehearsed one (kit.zip ${GK:-missing}, python ${GP:-missing})."
  say "         The Clinic PCs page will show no button for it until this is put right. Tell Claude what this window says."
fi
[ -f "$PCKITS_LIVE" ] && say "         (the page's own code is untouched: $(m5 "$PCKITS_LIVE" | cut -c1-8))"

say "   [2/2] IPv6 on this server:"
if "$SPY" -B "$KDIR/ipv6_facts.py" "$OUT"; then
  say "         written: $OUT ($(wc -c < "$OUT") bytes) - the assistant reads it from tonight's backup"
else
  RED=1
  say "!! [2/2] the IPv6 reading did not finish - nothing was changed. Tell Claude what this window says."
fi
say ""
if [ "$RED" = 0 ]; then say "DONE. Nothing was changed, and there is nothing for you to read or do here."; else say "FINISHED WITH A RED LINE ABOVE. Nothing was changed."; fi
exit "$RED"
