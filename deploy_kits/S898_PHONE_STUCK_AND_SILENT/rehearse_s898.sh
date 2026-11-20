#!/bin/bash
# rehearse_s898.sh -- the installer on a MADE-UP root: dry, red at [4/5], door not mounted, install, again, undo, undo again, tamper.
#   bash rehearse_s898.sh <dir holding the FROM finance tree> <a copy of finance.db>
set -u; K="$(cd "$(dirname "$0")" && pwd)"; SRC="$1"; DBC="$2"; W=$(mktemp -d /tmp/s898reh.XXXX); P=0; F=0
ok() { echo "ok   $1"; P=$((P+1)); }; bad() { echo "RED  $1"; F=$((F+1)); }
mk() { rm -rf "$W/root" "$W/kit"; mkdir -p "$W/root/finance/finance_ui" "$W/root/finance/spine" "$W/root/shared"; cp -p "$SRC"/*.py "$W/root/finance/"; cp -p "$SRC"/spine/*.py "$W/root/finance/spine/" 2>/dev/null
  cp -p "$SRC/finance_ui/finance_approvals.html" "$W/root/finance/finance_ui/"; cp "$DBC" "$W/root/finance/finance.db"; cp -rp "$K" "$W/kit"; }
printf '#!/bin/bash\necho "$@" >> %s/sysctl.log\n' "$W" > "$W/sc"; printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho %s\n' "${DOOR:-401}" > "$W/door"; printf '#!/bin/bash\necho 404\n' > "$W/door404"; chmod +x "$W"/sc "$W"/hz "$W"/door "$W"/door404
run() { (export ROOT="$W/root" LOCK="$W/lock" SYSTEMCTL="$W/sc" HEALTH_CMD="$W/hz" DOOR_CMD="${DC:-$W/door}" VPY=python3 APY=python3 NAP=0 TMPW="$W"; "$@" bash "$W/kit/install_S898_PHONE_STUCK_AND_SILENT.sh" 2>&1); }
pins() { md5sum "$W/root/finance/supplier_msg.py" "$W/root/finance/porders_s454.py" "$W/root/finance/finance_ui/finance_approvals.html" | cut -c1-8 | tr '\n' ' '; }
FROM="bdfe4ce7 c992ba91 f045686d "; TO="$(awk '{print substr($1,1,8)}' "$K/TO_PINS.md5" | tr '\n' ' ')"
mk; o=$(run env DRY=1); echo "$o" | grep -q "DRY RUN: every gate" && [ "$(pins)" = "$FROM" ] && ok "A1 dry: walk green, nothing written" || { bad "A1 dry"; echo "$o" | tail -5; }
mk; o=$(run env REHEARSE_RED_AT=4); [ "$(pins)" = "$FROM" ] && echo "$o" | grep -q "RED after placing" && ok "A2 red at [4/5] puts all three back" || { bad "A2"; echo "$o" | tail -4; }
mk; o=$(DC="$W/door404" run env); [ "$(pins)" = "$FROM" ] && echo "$o" | grep -q "not mounted" && ok "A3 door 404 = not mounted, all three back" || { bad "A3"; echo "$o" | tail -4; }
mk; o=$(run env); [ "$(pins)" = "$TO" ] && echo "$o" | grep -q "S898_PHONE_STUCK_AND_SILENT: DONE" && ok "A4 install: three files at TO, lock released" || { bad "A4"; echo "$o" | tail -6; }
[ ! -d "$W/lock" ] && ls "$W"/root/finance/*.bak_S898_* "$W"/root/finance/finance_ui/*.bak_S898_* >/dev/null 2>&1 && ok "A5 backups beside each, lock gone" || bad "A5"
o=$(run env); echo "$o" | grep -q "ALREADY INSTALLED" && ok "A6 again: ALREADY INSTALLED" || bad "A6"
o=$( (export ROOT="$W/root" LOCK="$W/lock" SYSTEMCTL="$W/sc"; bash "$W/kit/undo_s898.sh") 2>&1); [ "$(pins)" = "$FROM" ] && echo "$o" | grep -q "UNDONE" && ok "A7 undo: three files back" || { bad "A7"; echo "$o"; }
o=$( (export ROOT="$W/root" LOCK="$W/lock" SYSTEMCTL="$W/sc"; bash "$W/kit/undo_s898.sh") 2>&1); echo "$o" | grep -c "already at its old" | grep -q 3 && ok "A8 undo again: nothing to do" || bad "A8"
mk; echo "#" >> "$W/kit/porders_s454.py"; o=$(run env); echo "$o" | grep -q "SUMS.md5 gate failed" && [ "$(pins)" = "$FROM" ] && ok "A9 tampered kit refused" || bad "A9"
mk; echo "#" >> "$W/root/finance/supplier_msg.py"; o=$(run env); echo "$o" | grep -q "STOP, nothing installed" && ok "A10 live drift refused" || bad "A10"
mk; mkdir "$W/lock"; o=$(run env); echo "$o" | grep -q "another build holds the lock" && ok "A11 lock held: refused" || bad "A11"; rmdir "$W/lock"
rm -rf "$W"; echo "rehearse_s898: $P ok, $F red"; [ "$F" = 0 ]
