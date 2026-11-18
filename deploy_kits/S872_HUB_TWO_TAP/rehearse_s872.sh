#!/bin/bash
# rehearse_s872.sh <finance dir holding S869's page (built/)> <python> -- the installer and undo on a stand; nothing of the server touched.
set -u
SRC="$1"; PY="$2"; KD="$(cd "$(dirname "$0")" && pwd)"; W="$(mktemp -d /tmp/reh872.XXXXXX)"; P=0; F=0
chk() { if eval "$2"; then P=$((P+1)); echo "PASS  $1"; else F=$((F+1)); echo "FAIL  $1"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
printf '#!/bin/bash\necho 200\n' > "$W/hz.sh"; chmod +x "$W/hz.sh"
stand() { rm -rf "$W/root" "$W/lock"; mkdir -p "$W/root/finance/finance_ui"; cp -p "$SRC/finance_ui/finance_approvals.html" "$W/root/finance/finance_ui/"; }
run() { (cd /tmp && env ROOT="$W/root" APY="$PY" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" TMPW="$W" "$@" bash "$KIT/install_S872_HUB_TWO_TAP.sh" 2>&1); }
undo() { (cd /tmp && env ROOT="$W/root" SYSTEMCTL=true NAP=0 HEALTH_CMD="$W/hz.sh" LOCK="$W/lock" bash "$KIT/undo_s872.sh" 2>&1); }
N="$W/root/finance/finance_ui/finance_approvals.html"; FR=7253dc9f9a8ec0cfd576808af4c9b6a7; TO=$(awk '{print $1}' "$KD/TO_PINS.md5")
KIT="$W/kit"; cp -rp "$KD" "$KIT"
stand; O=$(run DRY=1); chk "A1 dry run: green, nothing written" 'echo "$O" | grep -q "DRY RUN: every gate" && [ "$(m5 "$N")" = $FR ]'
O=$(run); chk "A2 install: DONE at the TO pin; backup at FROM; lock released" 'echo "$O" | grep -q "S872_HUB_TWO_TAP: DONE" && [ "$(m5 "$N")" = "$TO" ] && [ "$(m5 "$N.bak_S872_7253dc9f")" = $FR ] && [ ! -e "$W/lock" ]'
O=$(run); chk "A3 again: ALREADY INSTALLED" 'echo "$O" | grep -q "ALREADY INSTALLED"'
O=$(undo); chk "A4 undo: S869's page back" 'echo "$O" | grep -q "S872 UNDONE" && [ "$(m5 "$N")" = $FR ]'
stand; O=$(run REHEARSE_RED_AT=4); chk "B1 a red at [4/5]: restored, lock released" 'echo "$O" | grep -q "RED after placing" && [ "$(m5 "$N")" = $FR ] && [ ! -e "$W/lock" ]'
stand; echo "<!-- drift -->" >> "$N"; O=$(run); chk "B2 a live page changed since the build: STOP" 'echo "$O" | grep -q "changed after this kit was built"'
stand; echo x >> "$KIT/README.md"; O=$(run); chk "B3 a corrupt kit: refused at the SUMS gate" 'echo "$O" | grep -q "SUMS.md5 gate failed"'; rm -rf "$KIT"; cp -rp "$KD" "$KIT"
stand; mkdir -p "$W/lock"; echo other > "$W/lock/owner"; O=$(run); chk "B4 another build holds the lock: refused" 'echo "$O" | grep -q "another build holds the lock"'
echo "REHEARSE S872: $P PASS, $F FAIL"; rm -rf "$W"; exit $F
