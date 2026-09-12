#!/bin/bash
# =============================================================================
#  install_S240_DARPAN_SHEETS.sh · kit S240_DARPAN_SHEETS
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_DARPAN_SHEETS
#
#  THE OWNER, 12-Sep-2026: Darpan is off the common sheet (D475, done). Now his two own sheets --
#  "one for myself and one for him. My one will include all his running advances, extra,
#  everything. And Darpan's includes what he actually needs, nothing historical, so that he
#  understands in one line what is his number of leaves, what is the deduction of the leaves,
#  what are the late minutes, what are the marks given, what are the deductions for late minutes."
#  And: "Darpan's own sheet show his advance deduction for the month YES."
#
#  THIS KIT ADDS TWO PRINTED PAGES at the end of the same salary document, per such person:
#    SHEET 5      the owner's page -- every deduction with its working, then the advance story
#                 for the month: opening, taken, recovered, interest, closing.
#    SALARY SLIP  his page, in his words -- salary, each deduction with its working, the advance
#                 cut this month, what he gets, and a signature line. No balances, no history.
#
#  NOTHING IS COMPUTED DIFFERENTLY. Every figure is the month's own; no money changes anywhere.
#
#  HOW IT PROVES ITSELF, on the real August data, before it keeps anything:
#    renders the sheets BEFORE, applies the edit, renders AFTER, and refuses unless
#      * every byte printed before the new pages is identical, and every byte after them is too --
#        so the ONLY difference in the whole document is one inserted block;
#      * that block is exactly two pages, his, carrying the advance deduction on both, the same
#        net on both, and his leaves / late minutes / marks on his own slip;
#      * SHEET 3 and SHEET 4 keep every row, in order, for the same rupee.
#    Anything short of that puts the file back and restarts the service.
# =============================================================================
set -u
KIT="S240_DARPAN_SHEETS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${SAL_PY:-/root/wa/venv/bin/python3}"
YM="${SAL_YM:-2026-08}"
WHO="${SAL_WHO:-Darpan}"
PIN_FROM="d42842e4028bafdfd1a539c1948afa67"
PIN_DONE="21b9cd0054c74cde8fe3b72251ef23d6"
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
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum patch_darpan_sheets_S240.py | awk '{print $1}')" ] \
  || red "KIT_ID does not match the patch script (F-88)"
[ -x "$PY" ] || red "$PY not found"

SP="/root/staff_register/salary_policy.py"
[ -f "$SP" ] || SP="$(find /root -maxdepth 4 -name salary_policy.py -not -path '*/deploy/*' | head -1)"
[ -n "$SP" ] && [ -f "$SP" ] || red "salary_policy.py not found under /root"
SDIR="$(dirname "$SP")"
LIVE="$(md5sum "$SP" | awk '{print $1}')"
echo "-- salary_policy.py: $SP  (${LIVE:0:8})   ·  person: $WHO   ·  month: $YM"
if [ "$LIVE" = "$PIN_DONE" ]; then echo "-- already done; nothing to do"; exit 0; fi
[ "$LIVE" = "$PIN_FROM" ] || red "the live file is ${LIVE:0:8}, not the ${PIN_FROM:0:8} this kit was built against (install S240_DARPAN_OWN_SHEET first). Nothing was changed."

SVC="$(basename "$(grep -rl staff_register /etc/systemd/system/*.service 2>/dev/null | head -1)" 2>/dev/null)"
[ -n "$SVC" ] && echo "-- service: $SVC" || echo "-- NOTE: no systemd unit mentions staff_register; nothing will be restarted"

W="$(mktemp -d)"
echo "-- rendering $YM as it stands today..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$SDIR" "$YM" "$W/before.html" ) || red "could not render before the edit -- nothing was changed"

OUT="$(SP_PATH="$SP" "$PY" -B "$KDIR/patch_darpan_sheets_S240.py" 2>&1)" || { echo "$OUT"; red "the edit refused -- nothing was changed"; }
echo "$OUT" | sed 's/^/   /'
BAK="$(echo "$OUT" | awk -F': *' '/backup *:/{print $2}')"
"$PY" -m py_compile "$SP" || restore "salary_policy.py does not compile after the edit"

echo "-- rendering $YM again, and comparing..."
( cd "$SDIR" && "$PY" -B "$KDIR/render_S240.py" "$SDIR" "$YM" "$W/after.html" ) || restore "could not render after the edit"
"$PY" -B "$KDIR/compare_sheets_S240.py" "$W/before.html" "$W/after.html" "$WHO" \
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
echo "$KIT GREEN -- $WHO now has two pages of his own at the end of the salary print: SHEET 5 for"
echo "you with the full advance story, and a SALARY SLIP for him with his month only and the"
echo "advance cut shown. Nothing else on the document moved by a single byte."
