#!/bin/bash
# =============================================================================
#  install_S253_MATCH_PLAIN.sh · kit S253_MATCH_PLAIN · clinic_money.py 1.1 -> 1.2
#
#  Run by:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S253_MATCH_PLAIN/install_S253_MATCH_PLAIN.sh
#
#  THE OWNER, 13-Sep-2026: "Your match page data is very taxing and cumbersome for me also, not
#  only staff, to understand your mathematics. If you can simplify it, then it is much better."
#  And: "50 rupees was a blood sugar payment" -- Docterz books it under X-ray, the counter under
#  procedures; a head difference, never money.
#
#  WHAT CHANGES -- ONE FILE, /root/finance/clinic_money.py (live 9cc6bb7a, the S252 install):
#    the card    the answer first: one plain sentence ("Saturday 12-Sep: the counter sheet has
#                Rs 650 more than Docterz. Everything else matches or is explained."), then only
#                what needs a person, in words with the likely cause ("Rs 600 paid by card was
#                written as cash; one consultation more"), then the buttons.  Everything else --
#                Explained (n), Waiting for the bank (n), Show the numbers -- is folded and opens
#                only if tapped.  No minus-sign arithmetic outside the folds.
#    the pattern the Rs 50 blood sugar head move is explained by name and netted out before any
#                difference is judged (HEAD_MOVES -- one line per such fact).
#  No data change, no portal, no grants.
#  Gates: kit SUMS + KIT_ID -> live pin exact (or ALREADY INSTALLED) -> py_compile -> THE WALK ON
#  THIS BOX (143 checks, scratch db) -> backup -> place -> restart clinic-finance -> healthz 200,
#  the four addresses 302, journal free of NOT mounted.  Any red: restored and restarted.
# =============================================================================
set -u
KIT="S253_MATCH_PLAIN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
FIN="${FIN_DIR:-/root/finance}"
POR="${PORTAL_DIR:-/root/portal}"
LIVE="$FIN/clinic_money.py"
FROM=9cc6bb7ab5a9eacaf9ecfaee20e44763
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
OUT_W="$(KIT="$KDIR" FIN_MODS="$FIN" PORTAL_DIR="$POR" "$PY" -B walk_s253.py 2>&1)"
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
echo "  GREEN — the plain morning-match card is live. Nothing else changed."
echo "    https://followup.dr-manoj.in/finance/clinic/match/2026-09-12   (Saturday, the plain card)"
echo "    https://followup.dr-manoj.in/finance/clinic/money             (your line)"
echo "  PIN:  $LIVE  $(m5 "$LIVE")"
echo "  Reverse:  \\cp -f $BAK $LIVE && systemctl restart $FIN_SVC"
echo "=============================================================="
