#!/bin/bash
# =============================================================================
#  install_h1c.sh · kit S187_H1c — the Hub under Clinic Design Language v1.
#
#  PAGE-ONLY KIT: one HTML file. Zero server change, zero schema change, no
#  service restart needed (the page is read from disk per request). Every
#  element id and API path is byte-preserved from H1a — presentation only.
#
#  Syntax-checked whole (bash -n) before shipping — the F-126 rule, learned
#  when H1a's goodbye message aborted after a string-surgery quote slip.
#
#  Rehearsal: H1B_FIN=/tmp/x/finance H1B_DEPLOY=/tmp/x/deploy bash install_h1c.sh
# =============================================================================
set -u
KIT_NAME="S187_H1c"
FIN="${H1B_FIN:-/root/finance}"
DEP="${H1B_DEPLOY:-/root/deploy}"
PY=/usr/bin/python3

OLD_PAGE_A="e7ae6208860ca671ed4ce1f0b11dc548"
OLD_PAGE_B="29eb6326a8c6a6d8b1a8b7620479fbf6"
NEW_PAGE="028255054662924713e03362c3976b05"

KIT_DIR="$(cd "$(dirname "$0")" && pwd)"; cd "$KIT_DIR" || exit 1
cur() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }

md5sum -c SUMS.md5 \
&& [ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT_NAME" ] \
&& [ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum SUMS.md5 | awk '{print $1}')" ] \
&& echo "-- kit integrity OK" \
&& [ "$(cur finance_approvals.html)" = "$NEW_PAGE" ] \
&& echo "-- payload hash matches the Register v5.21 pin" \
|| { echo "RED - kit gate failed. Nothing changed."; exit 1; }

P="$(cur "$FIN/finance_ui/finance_approvals.html")"
if [ "$P" = "$NEW_PAGE" ]; then
  echo "-- page already at H1b (idempotent re-run)"
elif [ "$P" = "$OLD_PAGE_A" ] || [ "$P" = "$OLD_PAGE_B" ]; then
  echo "-- currency gate OK: the page is a recorded prior build ($P)"
else
  echo "!! CURRENCY GATE RED: the page is '$P' - neither H1a nor H1b."
  echo "   NOTHING was changed (D321(d))."
  exit 1
fi

cp -f "$FIN/finance_ui/finance_approvals.html" "$FIN/finance_ui/finance_approvals.html.bak_$KIT_NAME" \
&& cp -f finance_approvals.html "$FIN/finance_ui/finance_approvals.html" \
&& echo "-- page placed (backup finance_approvals.html.bak_$KIT_NAME)" \
|| { echo "RED - could not place the page."; exit 1; }

[ -f "$DEP/live_pins.txt" ] && cp -f "$DEP/live_pins.txt" "$DEP/live_pins.txt.bak_$KIT_NAME"
cp -f live_pins_H1c.txt "$DEP/live_pins.txt" \
&& echo "-- pin list updated (previous kept as live_pins.txt.bak_$KIT_NAME)"

if [ -f "$DEP/verify_live_pins.py" ]; then
  echo ""
  "$PY" "$DEP/verify_live_pins.py" --pins "$DEP/live_pins.txt"
fi
echo ""
echo ">> Refresh /finance/approvals - the redesigned Hub is live immediately"
echo ">> (no service restart needed for a page). Expect pins 43/0/0 AMBER."
exit 0
