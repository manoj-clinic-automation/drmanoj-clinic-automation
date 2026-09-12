#!/bin/bash
# =============================================================================
#  install_S240_NET_ROUND10.sh · kit S240_NET_ROUND10
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_NET_ROUND10
#
#  THE OWNER, 12-Sep-2026: "ROUND OFF NET PAYABLE TO LAST 10 RUPEES."
#
#  Money is handed over in notes, so the paise and the last digit are not paid. The cut is made at
#  the ONE place the net is computed, so sheet 3, sheet 4, the own sheets, the slip, the totals and
#  whatever the lock stores all show the same rounded rupee, and the sheet still adds up.
#
#  DIRECTION: always towards zero. 8,651.33 is paid 8,650. A month ending at -1,949.07 carries
#  1,940 forward, not 1,950. The rounding never runs against the person.
#
#  No column is added to sheets 3 or 4. Sheet 3's footnote gains one sentence; the own sheets and
#  the slip gain a "Round off" line so their working still adds up to the rupee paid.
#
#  HOW IT PROVES ITSELF, on the real August data, before it keeps anything:
#    renders the sheets BEFORE, applies the edit, renders AFTER, and refuses unless
#      * SHEET 3 keeps every name in order and every column except the net to the paisa;
#      * every net is its old value cut TOWARDS ZERO to the last Rs.10 -- never up, never by
#        Rs.10 or more, and an already-round net does not move;
#      * the TOTAL net equals the sum of the rounded nets;
#      * SHEET 4 pays the same rounded rupee as SHEET 3 for every person;
#      * the own sheets show that rounded rupee on both pages with a round-off line.
#    Anything short of that puts the file back and restarts the service.
# =============================================================================
set -u
KIT="S240_NET_ROUND10"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${SAL_PY:-/root/wa/venv/bin/python3}"
YM="${SAL_YM:-2026-08}"
PIN_FROM="21b9cd0054c74cde8fe3b72251ef23d6"
PIN_DONE="92aecbe37d4272523c1cf6a4d8c8aced"
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
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum patch_net_round10_S240.py | awk '{print $1}')" ] \
  || red "KIT_ID does not match the patch script (F-88)"
[ -x "$PY" ] || red "$PY not found"

SP="/root/staff_register/salary_policy.py"
[ -f "$SP" ] || SP="$(find /root -maxdepth 4 -name salary_policy.py -not -path '*/deploy/*' | head -1)"
[ -n "$SP" ] && [ -f "$SP" ] || red "salary_policy.py not found under /root"
SDIR="$(dirname "$SP")"
LIVE="$(md5sum "$SP" | awk '{print $1}')"
echo "-- salary_policy.py: $SP  (${LIVE:0:8})   ·  month: $YM"
if [ "$LIVE" = "$PIN_DONE" ]; then echo "-- already done; nothing to do"; exit 0; fi
[ "$LIVE" = "$PIN_FROM" ] || red "the live file is ${LIVE:0:8}, not the ${PIN_FROM:0:8} this kit was built against (install S240_DARPAN_SHEETS first). Nothing was changed."

SVC="$(basename "$(grep -rl staff_register /etc/systemd/system/*.service 2>/dev/null | head -1)" 2>/dev/null)"
[ -n "$SVC" ] && echo "-- service: $SVC" || echo "-- NOTE: no systemd unit mentions staff_register; nothing will be restarted"

W="$(mktemp -d)"
echo "-- rendering $YM as it stands today..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$SDIR" "$YM" "$W/before.html" ) || red "could not render before the edit -- nothing was changed"

OUT="$(SP_PATH="$SP" "$PY" -B "$KDIR/patch_net_round10_S240.py" 2>&1)" || { echo "$OUT"; red "the edit refused -- nothing was changed"; }
echo "$OUT" | sed 's/^/   /'
BAK="$(echo "$OUT" | awk -F': *' '/backup *:/{print $2}')"
"$PY" -m py_compile "$SP" || restore "salary_policy.py does not compile after the edit"

echo "-- rendering $YM again, and comparing..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$SDIR" "$YM" "$W/after.html" ) || restore "could not render after the edit"
"$PY" -B "$KDIR/compare_round10_S240.py" "$W/before.html" "$W/after.html" \
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
echo "$KIT GREEN -- every NET PAYABLE is now cut to the last Rs.10, towards zero, everywhere the"
echo "net appears. No other figure on any sheet moved by a paisa."
