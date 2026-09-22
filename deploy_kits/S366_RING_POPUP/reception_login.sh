#!/bin/bash
# reception_login.sh · kit S366_RING_POPUP · the owner's ruling 22-Sep-2026: "Reception Mobile ... is a backup mobile
# with callback tracker, stays at reception, needs to be a part of our system."
# Gives that phone its own Clinic-app login `reception` (staff), shows it the Call Tracker tile, and links the phone
# MyOperator rings to that login -- the number comes from MyOperator's record, nobody types it.
# The password is typed once, here, by the owner (his credential). Re-running is safe.
#   bash /root/deploy/repo/deploy_kits/S366_RING_POPUP/reception_login.sh
set -u
VPY="${VPY:-/root/wa/venv/bin/python3}"; PD="${PD:-/root/portal}"
say() { echo "$@"; }
if "$VPY" "$PD/clinic_users.py" listusers 2>/dev/null | grep -qiE '(^|[^a-z])reception([^a-z]|$)'; then
  say "[1/3] login 'reception' already exists"
else
  say "[1/3] creating the login 'reception' (staff) -- type its password twice when asked:"
  "$VPY" "$PD/clinic_users.py" adduser reception staff || { say "!! adduser failed - nothing else changed"; exit 1; }
fi
"$VPY" - "$PD/tile_grants.json" <<'PY' || { say "!! tile_grants.json edit failed"; exit 1; }
import json, os, shutil, sys, time
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
u = d.setdefault("users", {}).setdefault("reception", {})
extra = u.setdefault("extra", [])
if "Call Tracker" in extra:
    print("[2/3] reception already sees the Call Tracker tile")
else:
    shutil.copy2(p, p + ".bak_S366_reception_" + time.strftime("%Y%m%d_%H%M%S"))
    extra.append("Call Tracker")
    tmp = p + ".tmp"
    json.dump(d, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    os.replace(tmp, p)
    print("[2/3] reception now sees the Call Tracker tile (backup kept beside the file)")
PY
"$VPY" "$PD/ring_agents_build.py" --link "Reception Mobile" reception || { say "!! link failed"; exit 1; }
say "[3/3] done -- on the reception phone: open the Clinic app, sign in as reception, tap the card, Allow."
"$VPY" "$PD/ring_agents_build.py" --show
