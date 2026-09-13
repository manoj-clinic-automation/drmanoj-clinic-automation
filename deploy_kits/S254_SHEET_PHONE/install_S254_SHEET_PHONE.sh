#!/bin/bash
# =============================================================================
#  install_S254_SHEET_PHONE.sh · kit S254_SHEET_PHONE
#
#  Run by (AFTER S253_MATCH_PLAIN is installed -- this kit is built on its clinic_money.py):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S254_SHEET_PHONE/install_S254_SHEET_PHONE.sh
#
#  THE OWNER, 13-Sep-2026, on his phone: "The entry boxes appear so small that the typed amount is
#  not visible in total ... a long scroll including all the optional sections. Make extra sections
#  collapsible so that on a regular day it is less scroll and easy submit."
#
#  TWO FILES, both patched from exact live pins (patch_s254.py, every anchor once):
#    /root/finance/clinic_register.py  92136a97 (S251) -> kit   each head on its own row, three equal
#                                      boxes beneath; hand-over count and three-records table folded
#    /root/finance/clinic_money.py     da9122e0 (S253) -> kit   other-UPI and float boxes folded, their
#                                      lines carrying what matters; open only when there is something
#  No data change, no portal, no grants.
#  Gates: SUMS + KIT_ID -> both live pins exact (or ALREADY INSTALLED) -> patch(live)==kit on the box
#  -> py_compile -> THE WALK ON THIS BOX (152 checks, scratch db) -> backups -> place -> restart
#  clinic-finance -> healthz 200, the four addresses 302, journal free of NOT mounted.  Any red:
#  both files restored, restarted.
# =============================================================================
set -u
KIT="S254_SHEET_PHONE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
FIN="${FIN_DIR:-/root/finance}"
POR="${PORTAL_DIR:-/root/portal}"
FIN_SVC="${FIN_SVC:-clinic-finance.service}"
FIN_PORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"
declare -A FROM=( ["clinic_register.py"]=92136a97929d86b8458e62e1a9c8878f ["clinic_money.py"]=da9122e0f8b48a1a0aa3d86d02adc109 )
FILES=(clinic_register.py clinic_money.py)
m5() { md5sum "$1" | awk '{print $1}'; }
cd "$KDIR" || { echo "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing"; exit 1; }; done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [1/7] SUMS.md5 gate failed — kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { echo "!! [1/7] KIT_ID names another kit"; exit 1; }
echo "[1/7] kit gates green"
ALL=1
for f in "${FILES[@]}"; do [ -f "$FIN/$f" ] && [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || ALL=0; done
if [ "$ALL" = 1 ]; then echo "-- ALREADY INSTALLED: both files are this kit's. Nothing changed."; exit 0; fi
for f in "${FILES[@]}"; do
  [ -f "$FIN/$f" ] || { echo "!! [2/7] $FIN/$f not found — nothing installed"; exit 1; }
  got="$(m5 "$FIN/$f")"
  [ "$got" = "$(m5 "$f")" ] && { echo "   $f already this kit's"; continue; }
  [ "$got" = "${FROM[$f]}" ] || { echo "!! [2/7] LIVE CODE CURRENCY GATE — $FIN/$f is $got, this kit was built against ${FROM[$f]} ($([ "$f" = clinic_money.py ] && echo 'install S253_MATCH_PLAIN first' || echo 'S251')). Nothing installed."; exit 1; }
done
echo "[2/7] both live files are the pins this kit was built on"
SRC=/tmp/s254_src_$STAMP; rm -rf "$SRC"; mkdir -p "$SRC" && chmod 700 "$SRC"
for f in "${FILES[@]}"; do if [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ]; then cp -f "$FIN/$f" "$SRC/$f"; else cp -f "$f" "$SRC/$f"; fi; done
OUT="$("$PY" -B patch_s254.py --selftest "$SRC" "$KDIR" 2>&1)"; rm -rf "$SRC"
echo "$OUT" | grep -q "selftest GREEN" || { echo "!! [3/7] patch(live) != kit — nothing installed"; echo "$OUT"; exit 1; }
for f in "${FILES[@]}"; do "$PY" -B -m py_compile "$f" 2>/dev/null || { echo "!! [3/7] $f does not compile under $PY"; exit 1; }; done
echo "[3/7] patch(live bytes) == kit, byte for byte; both compile"
OUT_W="$(KIT="$KDIR" FIN_MODS="$FIN" PORTAL_DIR="$POR" "$PY" -B walk_s254.py 2>&1)"
echo "$OUT_W" | grep -q "WALK GREEN" || { echo "!! [4/7] the kit's own walk failed ON THIS BOX — nothing installed"; echo "$OUT_W" | grep -E "FAIL|==" | tail -12; exit 1; }
echo "[4/7] $(echo "$OUT_W" | grep -E '^== [0-9]+ checks' | tail -1)"
declare -A BAK
for f in "${FILES[@]}"; do BAK[$f]="$FIN/$f.bak_${KIT}_${STAMP}"; cp -f "$FIN/$f" "${BAK[$f]}" || { echo "!! [5/7] backup failed"; exit 1; }; done
echo "[5/7] backups: ${BAK[*]}"
restore() { echo "   restoring both"; for f in "${FILES[@]}"; do cp -f "${BAK[$f]}" "$FIN/$f"; done; systemctl restart "$FIN_SVC"; sleep 2; exit 1; }
rm -rf "$FIN/__pycache__" 2>/dev/null || true
for f in "${FILES[@]}"; do cp -f "$f" "$FIN/$f" || { echo "!! [6/7] copy failed"; restore; }; [ "$(m5 "$FIN/$f")" = "$(m5 "$f")" ] || { echo "!! [6/7] bytes differ"; restore; }; done
echo "[6/7] placed: $(for f in "${FILES[@]}"; do printf '%s=%s ' "$f" "$(m5 "$FIN/$f" | cut -c1-8)"; done)"
systemctl restart "$FIN_SVC" || { echo "!! [7/7] restart failed"; restore; }
sleep 3
systemctl is-active --quiet "$FIN_SVC" || { echo "!! [7/7] $FIN_SVC not active"; restore; }
[ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz")" = "200" ] || { echo "!! [7/7] healthz not 200"; restore; }
for u in /finance/clinic/match /finance/clinic/money /finance/physio /finance/clinic/register; do
  C2="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$u")"; [ "$C2" = "302" ] || { echo "!! [7/7] $u answered $C2"; restore; }
done
journalctl -u "$FIN_SVC" --since "-1 min" --no-pager 2>/dev/null | grep -q "NOT mounted" && { echo "!! [7/7] a module did NOT mount"; restore; }
echo "[7/7] GREEN"
echo
echo "=============================================================="
echo "  GREEN — the counter sheet fits a phone; the extras are folded. Nothing else changed."
echo "    https://followup.dr-manoj.in/finance/clinic/register"
echo "  PINS:"; for f in "${FILES[@]}"; do printf '    %-36s %s\n' "$FIN/$f" "$(m5 "$FIN/$f")"; done
echo "  Reverse:"; for f in "${FILES[@]}"; do echo "    \\cp -f ${BAK[$f]} $FIN/$f"; done; echo "    systemctl restart $FIN_SVC"
echo "=============================================================="
