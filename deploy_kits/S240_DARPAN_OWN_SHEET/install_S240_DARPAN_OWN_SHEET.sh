#!/bin/bash
# =============================================================================
#  install_S240_DARPAN_OWN_SHEET.sh · kit S240_DARPAN_OWN_SHEET
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_DARPAN_OWN_SHEET
#
#  THE OWNER, 12-Sep-2026: Darpan's advance history is long enough that one line on a shared sheet
#  cannot tell the truth about it. He comes OFF the common salary sheet and will be paid on two
#  sheets of his own -- one for the owner with the full advance history, one for Darpan with only
#  what he needs to understand his month. THIS KIT DOES THE FIRST HALF ONLY: his line no longer
#  appears on sheets 3 and 4. His own sheets are a separate build.
#
#  Nothing is computed differently. His pay, his advances and his ledger are untouched.
#
#  HOW IT PROVES ITSELF, on the real August data, before it keeps anything:
#    renders sheets 3 and 4 BEFORE, applies the edit, renders them AFTER, and refuses unless
#      * his name appears nowhere on the page afterwards;
#      * SHEET 4 keeps every other name, in the same order, for the same rupee;
#      * every SHEET 3 total drops by exactly his own figure -- no more, no less.
#    Anything short of that puts the file back and restarts the service.
# =============================================================================
set -u
KIT="S240_DARPAN_OWN_SHEET"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${SAL_PY:-/root/wa/venv/bin/python3}"
YM="${SAL_YM:-2026-08}"
WHO="${SAL_WHO:-Darpan}"
PIN_FROM="aabd90fbd8219817a73a39c43be4f474"
PIN_DONE="d42842e4028bafdfd1a539c1948afa67"
BAK=""
SVC=""
red() { echo "!! RED -- $*"; exit 1; }
restore() {
  [ -n "$BAK" ] && [ -f "$BAK" ] && \cp -f "$BAK" "$SP" && echo "   salary_policy.py put back as it was"
  [ -n "$SVC" ] && systemctl restart "$SVC" >/dev/null 2>&1
  red "$*"
}

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum patch_darpan_own_sheet_S240.py | awk '{print $1}')" ] \
  || red "KIT_ID does not match the patch script (F-88)"
[ -x "$PY" ] || red "$PY not found"

SP="/root/staff_register/salary_policy.py"
[ -f "$SP" ] || SP="$(find /root -maxdepth 4 -name salary_policy.py -not -path '*/deploy/*' | head -1)"
[ -n "$SP" ] && [ -f "$SP" ] || red "salary_policy.py not found under /root"
SDIR="$(dirname "$SP")"
LIVE="$(md5sum "$SP" | awk '{print $1}')"
echo "-- salary_policy.py: $SP  (${LIVE:0:8})   ·  person: $WHO"
if [ "$LIVE" = "$PIN_DONE" ]; then echo "-- already done; nothing to do"; exit 0; fi
[ "$LIVE" = "$PIN_FROM" ] || red "the live file is ${LIVE:0:8}, not the ${PIN_FROM:0:8} this kit was built against (install S240_SALARY_NOTE first). Nothing was changed."

SVC="$(basename "$(grep -rl staff_register /etc/systemd/system/*.service 2>/dev/null | head -1)" 2>/dev/null)"
[ -n "$SVC" ] && echo "-- service: $SVC" || echo "-- NOTE: no systemd unit mentions staff_register; nothing will be restarted"

W="$(mktemp -d)"
echo "-- rendering August as it stands today..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$SDIR" "$YM" "$W/before.html" ) || red "could not render before the edit -- nothing was changed"

OUT="$(SP_PATH="$SP" "$PY" -B "$KDIR/patch_darpan_own_sheet_S240.py" 2>&1)" || { echo "$OUT"; red "the edit refused -- nothing was changed"; }
echo "$OUT" | sed 's/^/   /'
BAK="$(echo "$OUT" | awk -F': *' '/backup *:/{print $2}')"
"$PY" -m py_compile "$SP" || restore "salary_policy.py does not compile after the edit"

echo "-- rendering August again, and comparing..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$SDIR" "$YM" "$W/after.html" ) || restore "could not render after the edit"
"$PY" -B "$KDIR/compare_darpan_S240.py" "$W/before.html" "$W/after.html" "$WHO" \
  || restore "the comparison did not prove the change was safe"

if [ -n "$SVC" ]; then
  systemctl restart "$SVC"; sleep 3
  systemctl is-active --quiet "$SVC" || restore "$SVC did not come back"
  echo "-- $SVC restarted and up"
fi
rm -rf "$W"
echo
echo "PINS  $SP  $(md5sum "$SP" | awk '{print $1}')"
echo "      backup $BAK"
echo
echo "$KIT GREEN -- $WHO is off the common salary sheet. Every other name, amount and total is"
echo "unchanged except by exactly his own figures. His two own sheets are the next build."
