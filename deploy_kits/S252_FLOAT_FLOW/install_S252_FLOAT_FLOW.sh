#!/bin/bash
# =============================================================================
#  install_S252_FLOAT_FLOW.sh · kit S252_FLOAT_FLOW · clinic_money.py 1.0 -> 1.1
#
#  Run by:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S252_FLOAT_FLOW/install_S252_FLOAT_FLOW.sh
#
#  THE OWNER, 13-Sep-2026, after issuing the float on the S251 pages: "I find the flow to be a
#  friction one. It should be very easy for everyone to monitor and to replenish."  He was right.
#
#  WHAT CHANGES -- ONE FILE, /root/finance/clinic_money.py (live 08c57466, the S251 install):
#    reception   ZERO taps on a normal day: the counter sheet states what to keep aside and what
#                to hand over; "poora rakha" is already the answer. "Nahi" opens three boxes
#                (200/100/50) and nothing else. Change requests are three buttons.
#    the owner / Dr Bhawna   ONE line at the top of the money page ("Float Rs 2,500 intact." or
#                "Rs 2,000 -- Rs 500 short since 13-Sep (alisha). Give reception: 10 x Rs 50.") and
#                ONE tap, Given, that records the top-up with the notes already worked out; Change
#                given likewise. The issue / take-back grid is folded away for the rare case.
#    plus        the morning-match checker (setting clinic_money.checker) is refused the owner's
#                page, whatever other clinic roles he holds (the S251 observation).
#  Data: one column added on first request (clinic_float_day.need_done). Nothing recorded today
#  is lost: the Rs 2,500 issue stands. No portal change, no grants change.
#  Gates: kit SUMS + KIT_ID -> live pin exact (or ALREADY INSTALLED) -> py_compile -> THE WALK ON
#  THIS BOX (137 checks, scratch db) -> backup -> place -> restart clinic-finance -> healthz 200,
#  the four addresses 302, journal free of NOT mounted.  Any red: restored and restarted.
# =============================================================================
set -u
KIT="S252_FLOAT_FLOW"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
FIN="${FIN_DIR:-/root/finance}"
POR="${PORTAL_DIR:-/root/portal}"
LIVE="$FIN/clinic_money.py"
FROM=08c57466b44e417d93fc1e6117724fda
FIN_SVC="${FIN_SVC:-clinic-finance.service}"
FIN_PORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"
m5() { md5sum "$1" | awk '{print $1}'; }
cd "$KDIR" || { echo "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing"; exit 1; }; done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed — kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/7] KIT_ID names another kit"; exit 1; }
NEW="$(m5 clinic_money.py)"
[ "$NEW" = "$(awk 'NR==1{print $2}' KIT_ID.txt)" ] || { echo "!! [1/7] KIT_ID does not match clinic_money.py (F-88)"; exit 1; }
echo "[1/7] kit gates green"
[ -f "$LIVE" ] || { echo "!! [2/7] $LIVE not found — S251_CLINIC_MONEY is not installed; nothing installed"; exit 1; }
GOT="$(m5 "$LIVE")"
if [ "$GOT" = "$NEW" ]; then echo "-- ALREADY INSTALLED: $LIVE is this kit's file ($NEW). Nothing changed."; exit 0; fi
[ "$GOT" = "$FROM" ] || { echo "!! [2/7] LIVE CODE CURRENCY GATE — $LIVE is $GOT, this kit was built against $FROM. Nothing installed."; exit 1; }
echo "[2/7] the live clinic_money.py is the pin this kit was built on"
"$PY" -B -m py_compile clinic_money.py 2>/dev/null || { echo "!! [3/7] clinic_money.py does not compile under $PY"; exit 1; }
echo "[3/7] compiles under $PY"
OUT_W="$(KIT="$KDIR" FIN_MODS="$FIN" PORTAL_DIR="$POR" "$PY" -B walk_s252.py 2>&1)"
echo "$OUT_W" | grep -q "WALK GREEN" || { echo "!! [4/7] the kit's own walk failed ON THIS BOX — nothing installed"; echo "$OUT_W" | grep -E "FAIL|==" | tail -12; exit 1; }
echo "[4/7] $(echo "$OUT_W" | grep -E '^== [0-9]+ checks' | tail -1)"
BAK="${LIVE}.bak_${KIT}_${STAMP}"
cp -f "$LIVE" "$BAK" || { echo "!! [5/7] backup failed"; exit 1; }
echo "[5/7] backup: $BAK"
restore() { echo "   restoring $BAK"; cp -f "$BAK" "$LIVE"; systemctl restart "$FIN_SVC"; sleep 2; echo "   now $(m5 "$LIVE") (expected $FROM)"; exit 1; }
rm -rf "$FIN/__pycache__" 2>/dev/null || true
cp -f clinic_money.py "$LIVE" || { echo "!! [6/7] copy failed"; restore; }
[ "$(m5 "$LIVE")" = "$NEW" ] || { echo "!! [6/7] installed bytes differ"; restore; }
echo "[6/7] placed $NEW"
systemctl restart "$FIN_SVC" || { echo "!! [7/7] restart failed"; restore; }
sleep 3
systemctl is-active --quiet "$FIN_SVC" || { echo "!! [7/7] $FIN_SVC not active"; restore; }
[ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")" = "200" ] || { echo "!! [7/7] healthz not 200"; restore; }
for u in /finance/clinic/match /finance/clinic/money /finance/physio /finance/clinic/register; do
  C2="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$u")"
  [ "$C2" = "302" ] || { echo "!! [7/7] $u answered $C2, expected 302"; restore; }
done
journalctl -u "$FIN_SVC" --since "-1 min" --no-pager 2>/dev/null | grep -q "clinic_money NOT mounted" && { echo "!! [7/7] clinic_money did NOT mount"; restore; }
echo "[7/7] GREEN"
echo
echo "=============================================================="
echo "  GREEN — the float flow is live. Nothing else changed."
echo "    https://followup.dr-manoj.in/finance/clinic/money       (your one line + Given)"
echo "    https://followup.dr-manoj.in/finance/clinic/register    (reception: keep aside / hand over, one line)"
echo "  PIN:  $LIVE  $(m5 "$LIVE")"
echo "  Reverse:  \\cp -f $BAK $LIVE && systemctl restart $FIN_SVC"
echo "=============================================================="
