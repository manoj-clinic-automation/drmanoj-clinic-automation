#!/bin/bash
# install_staff_pwa_p1.sh -- S239: the staff app, phase 1 (tile_grants.json v8 -> v9).
# Gate: the live grants file must be v8 (07af4daa...). Backup first. The portal re-reads the file by
# mtime, so no restart. Nothing else on the box is touched. Undo: copy the .bak_S239 file back.
set -u
LIVE=/root/portal/tile_grants.json
FROM=07af4daa579776a357ea6d71ec6bd1f2
TO=$(md5sum tile_grants.json | cut -c1-32)
PY=/root/wa/venv/bin/python3
have=$(md5sum "$LIVE" 2>/dev/null | cut -c1-32)
if [ "$have" = "$TO" ]; then echo "== already installed ($TO) -- nothing to do"; else
  [ "$have" = "$FROM" ] || { echo "!! REFUSING: live $LIVE is ${have:-missing}, expected v8 $FROM. Nothing changed."; exit 1; }
  $PY -c "import json,sys; g=json.load(open('tile_grants.json')); assert g['version']==9; assert 'Call Tracker' in g['users']['shivani']['extra']" \
    || { echo "!! REFUSING: the new file does not validate. Nothing changed."; exit 1; }
  \cp -p "$LIVE" "$LIVE.bak_S239_v8" && \cp tile_grants.json "$LIVE.tmp_S239" && mv -f "$LIVE.tmp_S239" "$LIVE" \
    || { echo "!! copy failed -- restoring"; \cp -p "$LIVE.bak_S239_v8" "$LIVE"; exit 1; }
fi
echo "== tile_grants.json now: $(md5sum $LIVE | cut -c1-32)  (expect $TO)"
echo "== portal logins (name, role, active) -- no passwords printed:"
$PY - <<'PYEOF'
import json
s=json.load(open('/root/portal/clinic_users.json'))
g=json.load(open('/root/portal/tile_grants.json'))["users"]
for u,v in sorted(s.get("users",{}).items()):
    tag=""
    if v.get("role")=="staff" and "Attendance" not in (g.get(u,{}).get("mask") or []): tag="   <-- attendance NOT held for this login"
    print("   %-12s %-8s %s%s" % (u, v.get("role"), "active" if v.get("active") else "INACTIVE", tag))
PYEOF
echo "== STAFF PWA PHASE 1 INSTALLED"
