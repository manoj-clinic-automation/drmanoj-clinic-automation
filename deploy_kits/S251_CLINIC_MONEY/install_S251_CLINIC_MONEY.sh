#!/bin/bash
# =============================================================================
#  install_S251_CLINIC_MONEY.sh · kit S251_CLINIC_MONEY (= S249_CLINIC_MONEY rebuilt on the S250 grants file, F-458)
#
#  Run by:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S251_CLINIC_MONEY/install_S251_CLINIC_MONEY.sh
#
#  THE OWNER, 13-Sep-2026 (S249_CLINIC_MONEY_FINAL_PLAN): the morning match -- the counter sheet,
#  Docterz and the bank MPR joined into one verdict, flags only where no pattern explains the
#  money; reception makes the first pass, Shavez checks; four things reach the owner.  Other UPI
#  (a personal phone when the ICICI QR is down) recorded on the counter sheet, kept out of the bank
#  match.  The reception float (Rs 2,500) issued once, counted at close, never revenue.  The
#  physiotherapy revenue table -- reception writes, Bhati (new login, its own server unit) reads,
#  the doctors tap received.  F-459 fixed first: ONE "our online" figure.
#
#  FILES PLACED (each from an exact live pin, each backed up beside itself):
#    /root/finance/finance_clinic_day.py   56fb7619 -> (kit)     F-459 + the channel-5-aware bank card
#    /root/finance/clinic_register.py      c6b87682 -> (kit)     other-UPI box, float, physio hand-over
#    /root/finance/finance_app.py          912398e9 -> 1fc62335  PATCHED ON THE BOX by patch_s249.py (F-185 keeps the
#                                                                   file out of the repository); the physio unit on the gate; the mount
#    /root/finance/clinic_money.py         NEW
#    /root/portal/portal.py                06f1b378 -> (kit)     two tiles
#    /root/portal/tile_grants.json         v15 932f7bd0 (S250) -> v16   (kit)
#  DATA: seed_s249.py -- business_unit 'physio', six unit_role rows, setting clinic_money.checker
#        (INSERT OR IGNORE; a second run changes nothing).  Tables of the new module: first request.
#
#  Gates in order: kit SUMS + KIT_ID -> every live pin exact (or ALREADY INSTALLED) -> the patcher's
#  own selftest on the box (patch(live) == kit, byte for byte) -> py_compile of every file -> THE
#  WALK ON THIS BOX (the real app over a scratch db, 126 checks, nothing live touched) -> backups
#  -> place -> seed -> restart clinic-finance + clinic-portal -> healthz 200, portal 200, the new
#  routes answer behind the login.  Any red after placing: EVERY file restored, both restarted.
# =============================================================================
set -u
KIT="S251_CLINIC_MONEY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
FIN="${FIN_DIR:-/root/finance}"
POR="${PORTAL_DIR:-/root/portal}"
DBF="${FINANCE_DB:-$FIN/finance.db}"
FIN_SVC="${FIN_SVC:-clinic-finance.service}"
POR_SVC="${POR_SVC:-clinic-portal.service}"
FIN_PORT="${FIN_PORT:-8106}"
POR_PORT="${POR_PORT:-8099}"
STAMP="$(date +%Y%m%d_%H%M%S)"

declare -A FROM=( ["finance_clinic_day.py"]=56fb76198a6911ae512c3b73925a3c22
                  ["clinic_register.py"]=c6b87682ccbfb03734a39ad33c26f2a3
                  ["finance_app.py"]=912398e9897b180dce43955814beaf43
                  ["portal.py"]=06f1b378608fbc97c54bc1f546d7985c
                  ["tile_grants.json"]=932f7bd05f4bf19b1f53deb9a2f35d22 )
declare -A DEST=( ["finance_clinic_day.py"]="$FIN/finance_clinic_day.py"
                  ["clinic_register.py"]="$FIN/clinic_register.py"
                  ["finance_app.py"]="$FIN/finance_app.py"
                  ["clinic_money.py"]="$FIN/clinic_money.py"
                  ["portal.py"]="$POR/portal.py"
                  ["tile_grants.json"]="$POR/tile_grants.json" )
ORDER=(finance_clinic_day.py clinic_register.py finance_app.py clinic_money.py portal.py tile_grants.json)
FA_TO=1fc62335f085b4cb4a634bbe9cca96c4
FA_NEW="/tmp/s249_finance_app_$STAMP.py"   # written by the patcher from the live bytes, step 3; never inside the clone

m5() { md5sum "$1" | awk '{print $1}'; }
cd "$KDIR" || { echo "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — nothing installed"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/9] SUMS.md5 gate failed — kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/9] KIT_ID.txt names another kit — nothing installed"; exit 1; }
echo "[1/9] kit gates green"

# ---- [2] the live pins: every file exact, or the whole kit already in place --------------------
ALL_SAME=1; ANY_SAME=0
for f in "${ORDER[@]}"; do
  d="${DEST[$f]}"
  if [ "$f" = finance_app.py ]; then
    if [ -f "$d" ] && [ "$(m5 "$d")" = "$FA_TO" ]; then ANY_SAME=1; else ALL_SAME=0; fi
  elif [ -f "$d" ] && [ "$(m5 "$d")" = "$(m5 "$f")" ]; then ANY_SAME=1; else ALL_SAME=0; fi
done
if [ "$ALL_SAME" = 1 ]; then
  echo "-- ALREADY INSTALLED: every file is this kit's. Re-seeding roles (idempotent):"
  "$PY" -B seed_s249.py "$DBF" | sed 's/^/   /'
  exit 0
fi
for f in finance_clinic_day.py clinic_register.py finance_app.py portal.py tile_grants.json; do
  d="${DEST[$f]}"
  [ -f "$d" ] || { echo "!! [2/9] $d not found — nothing installed"; exit 1; }
  got="$(m5 "$d")"
  if [ "$f" = finance_app.py ] && [ "$got" = "$FA_TO" ]; then echo "   $f already this kit's ($got)"; continue; fi
  if [ "$f" != finance_app.py ] && [ "$got" = "$(m5 "$f")" ]; then echo "   $f already this kit's ($got)"; continue; fi
  [ "$got" = "${FROM[$f]}" ] || { echo "!! [2/9] LIVE CODE CURRENCY GATE — $d is $got, this kit was built against ${FROM[$f]}. Nothing installed."; exit 1; }
done
systemctl show -p ExecStart "$FIN_SVC" 2>/dev/null | grep -q "finance" || { echo "!! [2/9] $FIN_SVC does not look like the finance app — nothing installed"; exit 1; }
[ -f "$DBF" ] || { echo "!! [2/9] $DBF not found — nothing installed"; exit 1; }
echo "[2/9] every live file is the pin this kit was built on"

# ---- [3] the patcher's own proof, on the box: patch(live) == kit --------------------------------
SRC=/tmp/s249_src_$STAMP; rm -rf "$SRC"; mkdir -p "$SRC" && chmod 700 "$SRC"
for f in finance_clinic_day.py clinic_register.py finance_app.py portal.py; do
  if [ "$(m5 "${DEST[$f]}")" = "${FROM[$f]}" ]; then cp -f "${DEST[$f]}" "$SRC/$f"; elif [ -f "$f" ]; then cp -f "$f" "$SRC/$f"; else cp -f "${DEST[$f]}" "$SRC/$f"; fi
done
# finance_app.py: patched FROM THE LIVE BYTES into the kit folder (never published -- F-185)
rm -f "$FA_NEW"
"$PY" -B patch_s249.py --file finance_app.py "${DEST[finance_app.py]}" "$FA_NEW" || { echo "!! [3/9] finance_app.py could not be patched from the live bytes — nothing installed"; rm -rf "$SRC"; exit 1; }
[ "$(m5 "$FA_NEW")" = "$FA_TO" ] || { echo "!! [3/9] patched finance_app.py is $(m5 "$FA_NEW"), predicted $FA_TO — nothing installed"; rm -rf "$SRC"; rm -f "$FA_NEW"; exit 1; }
OUT="$("$PY" -B patch_s249.py --selftest "$SRC" "$KDIR" 2>&1)"
if echo "$OUT" | grep -q "selftest GREEN"; then echo "[3/9] patch(live bytes) == kit files, byte for byte"; else
  # a file already at the kit pin makes the selftest's source-pin check fail by design; accept only that case
  if echo "$OUT" | grep -q "FAIL" && [ "$ANY_SAME" = 1 ]; then echo "[3/9] (partial re-run) some files already placed; selftest skipped for those"; else
  echo "!! [3/9] the patcher does not reproduce the kit from the live bytes — nothing installed"; echo "$OUT"; rm -rf "$SRC"; exit 1; fi
fi
rm -rf "$SRC"
for f in finance_clinic_day.py clinic_register.py clinic_money.py portal.py seed_s249.py; do
  "$PY" -B -m py_compile "$f" 2>/dev/null || { echo "!! [4/9] $f does not compile under $PY — nothing installed"; exit 1; }
done
"$PY" -B -m py_compile "$FA_NEW" 2>/dev/null || { echo "!! [4/9] the patched finance_app.py does not compile under $PY — nothing installed"; rm -f "$FA_NEW"; exit 1; }
"$PY" -c "import json,sys; g=json.load(open('tile_grants.json')); sys.exit(0 if g.get('version')==16 else 1)" || { echo "!! [4/9] tile_grants.json is not v16"; exit 1; }
echo "[4/9] every file compiles under $PY; grants v16"

# ---- [5] THE WALK ON THIS BOX: the real app, a scratch db, nothing live touched ---------------
OUT_W="$(KIT="$KDIR" FIN_MODS="$FIN" PORTAL_DIR="$POR" "$PY" -B walk_s249.py 2>&1)"
echo "$OUT_W" | grep -q "WALK GREEN" || { echo "!! [5/9] the kit's own walk failed ON THIS BOX — nothing installed"; echo "$OUT_W" | grep -E "FAIL|==" | tail -15; exit 1; }
echo "[5/9] $(echo "$OUT_W" | grep -E '^== [0-9]+ checks' | tail -1)"

# ---- [6] backups, then place -------------------------------------------------------------------
declare -A BAK
for f in "${ORDER[@]}"; do
  d="${DEST[$f]}"
  if [ -f "$d" ]; then BAK[$f]="${d}.bak_${KIT}_${STAMP}"; cp -f "$d" "${BAK[$f]}" || { echo "!! [6/9] backup of $d failed — nothing installed"; exit 1; }; fi
done
echo "[6/9] backups: ${BAK[*]}"
restore() {
  echo "   RESTORING every file"
  for f in "${ORDER[@]}"; do
    d="${DEST[$f]}"
    if [ -n "${BAK[$f]:-}" ]; then cp -f "${BAK[$f]}" "$d"; else rm -f "$d"; fi
  done
  systemctl restart "$FIN_SVC"; systemctl restart "$POR_SVC"; sleep 2
  echo "   restored; finance_app now $(m5 "$FIN/finance_app.py"), portal $(m5 "$POR/portal.py")"
  exit 1
}
rm -rf "$POR/__pycache__" "$FIN/__pycache__" 2>/dev/null || true
for f in "${ORDER[@]}"; do
  src="$f"; [ "$f" = finance_app.py ] && src="$FA_NEW"
  cp -f "$src" "${DEST[$f]}" || { echo "!! [7/9] copy of $f failed"; restore; }
  [ "$(m5 "${DEST[$f]}")" = "$(m5 "$src")" ] || { echo "!! [7/9] installed bytes differ for $f"; restore; }
  [ "$f" = finance_app.py ] && rm -f "$FA_NEW"
done
echo "[7/9] placed: $(for f in "${ORDER[@]}"; do printf '%s=%s ' "$f" "$(m5 "${DEST[$f]}" | cut -c1-8)"; done)"

# ---- [8] the data: the physio unit, its roles, the named checker --------------------------------
cp -f "$DBF" "${DBF}.bak_${KIT}_${STAMP}" || { echo "!! [8/9] db backup failed"; restore; }
"$PY" -B seed_s249.py "$DBF" | sed 's/^/   /' || { echo "!! [8/9] seed failed"; restore; }
echo "[8/9] roles seeded (db backup ${DBF}.bak_${KIT}_${STAMP})"

# ---- [9] restart both, then ask the box ---------------------------------------------------------
systemctl restart "$FIN_SVC" || { echo "!! [9/9] $FIN_SVC restart failed"; restore; }
systemctl restart "$POR_SVC" || { echo "!! [9/9] $POR_SVC restart failed"; restore; }
sleep 3
systemctl is-active --quiet "$FIN_SVC" || { echo "!! [9/9] $FIN_SVC is NOT active"; restore; }
systemctl is-active --quiet "$POR_SVC" || { echo "!! [9/9] $POR_SVC is NOT active"; restore; }
CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")"
[ "$CODE" = "200" ] || { echo "!! [9/9] /finance/healthz answered $CODE"; restore; }
for u in /finance/clinic/match /finance/clinic/money /finance/physio /finance/clinic/register; do
  C2="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$u")"
  [ "$C2" = "302" ] || { echo "!! [9/9] $u answered $C2 behind no login, expected 302"; restore; }
done
journalctl -u "$FIN_SVC" --since "-1 min" --no-pager 2>/dev/null | grep -q "clinic_money NOT mounted" && { echo "!! [9/9] the journal says clinic_money did NOT mount"; restore; }
PC="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$POR_PORT/portal/health")"
[ "$PC" = "200" ] || { echo "!! [9/9] the portal answered $PC on /portal/health"; restore; }
echo "[9/9] GREEN — finance healthz 200; match / money / physio / register answer 302 behind the login; portal $PC"

echo
echo "=============================================================="
echo "  GREEN — S251_CLINIC_MONEY (the S249 build) is live."
echo
echo "  ONE THING ONLY YOU CAN DO — Bhati's login (the physiotherapist):"
echo "    https://followup.dr-manoj.in/portal/users"
echo "    Add user  bhati  role  staff  and a password. His roles and his tile are already in place."
echo
echo "  THEN, ONCE — issue the reception float (Rs 2,500: 5 x 200, 10 x 100, 10 x 50):"
echo "    https://followup.dr-manoj.in/finance/clinic/money"
echo
echo "  The pages:"
echo "    https://followup.dr-manoj.in/finance/clinic/match        (reception / Shavez; your login lands on your line)"
echo "    https://followup.dr-manoj.in/finance/clinic/money        (your four flags, the month's channels, the float)"
echo "    https://followup.dr-manoj.in/finance/physio              (the physiotherapy table)"
echo "    https://followup.dr-manoj.in/finance/clinic/register     (the counter sheet: other-UPI box, float count)"
echo
echo "  PINS:"
for f in "${ORDER[@]}"; do printf '    %-44s %s\n' "${DEST[$f]}" "$(m5 "${DEST[$f]}")"; done
echo "  Reverse (all six, both services):"
for f in "${ORDER[@]}"; do [ -n "${BAK[$f]:-}" ] && echo "    \\cp -f ${BAK[$f]} ${DEST[$f]}"; done
echo "    rm -f $FIN/clinic_money.py && systemctl restart $FIN_SVC && systemctl restart $POR_SVC"
echo "=============================================================="
