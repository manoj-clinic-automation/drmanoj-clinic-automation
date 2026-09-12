#!/bin/bash
# =============================================================================
#  install_S240_SALARY_NOTE.sh · kit S240_SALARY_NOTE
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_SALARY_NOTE
#
#  TWO CORRECTIONS TO THE SALARY SHEET. NO AMOUNT CHANGES ANYWHERE.
#    1. The footnote said "salary / 30". The engine divides by 30.5 (D343) -- the line was built
#       with a whole-number format. Now it prints the divisor as it is.
#    2. Amir is flat pay (D459) and his row printed "31" in the Leaves column -- computed, then
#       thrown away, and it inflated the clinic's leave total by 31 days. Part-time rows now show
#       no leave working.
#
#  HOW IT PROVES ITSELF, on the real August data, before it keeps anything:
#    renders sheets 3 and 4 BEFORE the edit, applies the edit, renders them AFTER, and refuses
#    unless SHEET 4 -- every name and every amount -- is byte-identical, and at most two numbers
#    on the whole page changed. Anything short of that puts the file back.
#  No column is added or removed.
# =============================================================================
set -u
KIT="S240_SALARY_NOTE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${SAL_PY:-/root/wa/venv/bin/python3}"
YM="${SAL_YM:-2026-08}"
PIN_V116="c7577174f35b30d8ab7fd42e163d9e4e"
PIN_DONE="aabd90fbd8219817a73a39c43be4f474"
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
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum patch_salary_policy_S240.py | awk '{print $1}')" ] \
  || red "KIT_ID does not match the patch script (F-88)"
[ -x "$PY" ] || red "$PY not found"

SP="/root/staff_register/salary_policy.py"
[ -f "$SP" ] || SP="$(find /root -maxdepth 4 -name salary_policy.py -not -path '*/deploy/*' | head -1)"
[ -n "$SP" ] && [ -f "$SP" ] || red "salary_policy.py not found under /root"
SDIR="$(dirname "$SP")"
LIVE="$(md5sum "$SP" | awk '{print $1}')"
echo "-- salary_policy.py: $SP  (${LIVE:0:8})"
if [ "$LIVE" = "$PIN_DONE" ]; then echo "-- already corrected; nothing to do"; exit 0; fi
[ "$LIVE" = "$PIN_V116" ] || red "the live file is ${LIVE:0:8}, not the v1.16 this kit was built against (${PIN_V116:0:8}). Nothing was changed."

SVC="$(basename "$(grep -rl staff_register /etc/systemd/system/*.service 2>/dev/null | head -1)" 2>/dev/null)"
[ -n "$SVC" ] && echo "-- service: $SVC" || echo "-- NOTE: no systemd unit mentions staff_register; nothing will be restarted"

W="$(mktemp -d)"
echo "-- rendering August as it stands today..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$YM" "$W/before.html" ) || red "could not render before the edit -- nothing was changed"

OUT="$(SP_PATH="$SP" "$PY" -B "$KDIR/patch_salary_policy_S240.py" 2>&1)" || { echo "$OUT"; red "the edit refused -- nothing was changed"; }
echo "$OUT" | sed 's/^/   /'
BAK="$(echo "$OUT" | awk -F': *' '/backup *:/{print $2}')"
"$PY" -m py_compile "$SP" || restore "salary_policy.py does not compile after the edit"

echo "-- rendering August again, and comparing..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$YM" "$W/after.html" ) || restore "could not render after the edit"
"$PY" -B "$KDIR/compare_S240.py" "$W/before.html" "$W/after.html" || restore "the comparison did not prove the change was safe"

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
echo "$KIT GREEN -- the footnote now reads salary/30.5, Amir's row shows no working, and every"
echo "amount on sheets 3 and 4 is unchanged (proved by rendering August before and after)."
