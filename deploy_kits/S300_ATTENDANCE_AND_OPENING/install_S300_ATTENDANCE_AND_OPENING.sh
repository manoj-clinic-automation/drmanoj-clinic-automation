#!/bin/bash
# =============================================================================
#  install_S300_ATTENDANCE_AND_OPENING.sh · kit S300_ATTENDANCE_AND_OPENING (session 267, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S300_ATTENDANCE_AND_OPENING/install_S300_ATTENDANCE_AND_OPENING.sh
#
#  THE OWNER, 17-Sep-2026 evening (D540, as he then amended it -- "past days show absents and leaves
#  only: not needed"; "also need to add opening balance of bhati, in his cash and loan sections"):
#   A  /root/staff_register/staff_register.py  13a26205 -> 439d6790
#      the staff self page in Hinglish and tap-only: the Mark-me-present reason is tapped (five
#      choices, typed words refused); "Mark my exit" becomes "Mark overtime" = two buttons,
#      Told Dr Bhawna / Told Dr Manoj; the My month link removed; review card "Overtime requests".
#   B  /root/finance/petty_book.py             53f7e65d -> 88f28571
#      Manoj Bhati's opening cash and opening loan: a doctor sets or corrects each on the English
#      page (audited); both add into his in-hand and loan figures; Bhati sees them, cannot change them.
#  DATA: none. The new table petty_opening is created on first request (IF NOT EXISTS).
#
#  Gates: kit SUMS + KIT_ID -> both live pins exact (or ALREADY INSTALLED) -> compile -> the staff
#  register's own selftest -> THE PETTY WALK on this box (live finance app files + the kit's
#  petty_book over a scratch copy of the live finance.db) -> THE SELF-PAGE WALK on this box (the
#  kit's staff_register over a scratch copy of the live staff_register.db, every mapped staff login)
#  -> backups -> place -> restart staff-register + clinic-finance -> health. Any red after placing:
#  both files restored byte-identically, both services restarted.
#  No portal.py, no stock_* file, no cron line, no scheduled job, nothing on manojz or the medical PC.
# =============================================================================
set -u
KIT="S300_ATTENDANCE_AND_OPENING"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"          # staff-register runs on the venv
SPY="${SPY:-/usr/bin/python3}"                    # clinic-finance runs on the system python
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; SRD="$ROOT/staff_register"
DBF="$FIN/finance.db"; SRDB="$SRD/staff_register.db"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s300_walk_$STAMP"

declare -A FROM=( [staff_register.py]=13a262059c9108f9f67b653c28998c10
                  [petty_book.py]=53f7e65df20e139cd7e5b09a4ecd9738 )
declare -A TO=(   [staff_register.py]=439d679003d13fb9b0eabf6ba72b0523
                  [petty_book.py]=88f2857193938a493f20c9c31f672d1e )
declare -A DEST=( [staff_register.py]="$SRD/staff_register.py"
                  [petty_book.py]="$FIN/petty_book.py" )
ORDER=(staff_register.py petty_book.py)

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$VPY" ] && [ -x "$SPY" ] || { say "!! preflight: python not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/9] kit gates green"

# ---- [2] live pins ------------------------------------------------------------------------------
ALL_TO=1
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || ALL_TO=0; done
[ "$ALL_TO" = 1 ] && { say "-- ALREADY INSTALLED: both files carry this kit."; exit 0; }
for f in "${ORDER[@]}"; do
  have="$(m5 "${DEST[$f]}")"
  [ "$have" = "${FROM[$f]}" ] || { say "!! [2/9] ${DEST[$f]} is ${have:-missing}, expected ${FROM[$f]} - nothing installed"; exit 1; }
  [ "$(m5 "$f")" = "${TO[$f]}" ] || { say "!! [2/9] kit file $f is not its predicted md5 - nothing installed"; exit 1; }
done
say "[2/9] both live pins exact; kit files at their predicted md5"

# ---- [3] compile --------------------------------------------------------------------------------
export PYTHONPYCACHEPREFIX="$WALK/pyc"            # compiled bytes go to /tmp, never into the deploy clone
"$VPY" -m py_compile staff_register.py walk_sr_s300.py && "$SPY" -m py_compile petty_book.py walk_s300.py seed_s289.py \
  || { say "!! [3/9] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/9] py_compile green"

# ---- [4] the staff register's own selftest (kit copy, throwaway store) ----------------------------
mkdir -p "$WALK/st" && cp -p staff_register.py "$WALK/st/"
( cd "$WALK/st" && "$VPY" -B staff_register.py --selftest 2>&1 | tail -1 | grep -q "SELFTEST OK" ) \
  || { say "!! [4/9] staff_register selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/9] staff register selftest OK (incl. S300: tap reasons, Mark overtime, My month gone)"

# ---- [5] the petty walk on this box --------------------------------------------------------------
mkdir -p "$WALK/app" "$WALK/uploads" "$WALK/scans" || exit 1
cp -p "$FIN"/*.py "$WALK/app/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/app/" 2>/dev/null
cp -p petty_book.py "$WALK/app/petty_book.py"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/walk.db" \
  || { say "!! [5/9] could not take the finance scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
"$SPY" -B seed_s289.py "$WALK/walk.db" >/dev/null || { say "!! [5/9] seed on the scratch copy failed - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK/app" && FINANCE_DB="$WALK/walk.db" FINANCE_ALLOW_HEADER_AUTH=1 PETTY_UPLOAD_DIR="$WALK/uploads" \
         PETTY_NOW="$(date +%Y-%m-%dT%H:%M:%S)" FINANCE_SCAN_DIR="$WALK/scans" FINANCE_SSO_DIR="$ROOT/portal" \
         timeout 170 "$SPY" -B "$KDIR/walk_s300.py" "$WALK/app" 2>&1 | tail -1 )"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [5/9] petty walk red: $WOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[5/9] $WOUT"

# ---- [6] the self-page walk on this box ------------------------------------------------------------
mkdir -p "$WALK/sr" && cp -p staff_register.py "$WALK/sr/"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$SRDB" "$WALK/sr_walk.db" \
  || { say "!! [6/9] could not take the register scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
SOUT="$( SR_DB_PATH="$WALK/sr_walk.db" timeout 170 "$VPY" -B "$KDIR/walk_sr_s300.py" "$WALK/sr" "$SRD" 2>&1 | tail -1 )"
echo "$SOUT" | grep -q "^WALK OK" || { say "!! [6/9] self-page walk red: $SOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[6/9] $SOUT"

# ---- [7] backups + place ------------------------------------------------------------------------------
declare -A BAK
for f in "${ORDER[@]}"; do
  BAK[$f]="${DEST[$f]}.bak_S300_${FROM[$f]:0:8}"
  \cp -p "${DEST[$f]}" "${BAK[$f]}" || { say "!! [7/9] backup of ${DEST[$f]} failed - nothing placed"; exit 1; }
done
restore() {
  say "!! RED after placing - restoring both files byte-identically"
  for f in "${ORDER[@]}"; do \cp -p "${BAK[$f]}" "${DEST[$f]}"; done
  systemctl restart staff-register clinic-finance || true
  sleep 3
  for f in "${ORDER[@]}"; do say "   ${DEST[$f]} $(m5 "${DEST[$f]}")"; done
  say "   (a petty_opening table, if created, stays; the old file never reads it)"
  exit 1
}
for f in "${ORDER[@]}"; do \cp -p "$f" "${DEST[$f]}" || restore; done
for f in "${ORDER[@]}"; do [ "$(m5 "${DEST[$f]}")" = "${TO[$f]}" ] || { say "!! [7/9] ${DEST[$f]} did not land at its pin"; restore; }; done
say "[7/9] placed, backups beside each file (.bak_S300_<from8>)"

# ---- [8] restart ------------------------------------------------------------------------------------------
systemctl restart staff-register || restore
systemctl restart clinic-finance || restore
sleep 4
for s in staff-register clinic-finance; do systemctl is-active --quiet "$s" || { say "!! $s not active"; restore; }; done
say "[8/9] staff-register and clinic-finance active"

# ---- [9] health ------------------------------------------------------------------------------------------
c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8044/register/health)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/petty)
c4=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8044/register/me)
say "health : register $c1 · finance $c2 · /finance/petty without a login $c3 (302 expected) · /register/me without a login $c4 (302 expected)"
[ "$c1" = 200 ] && [ "$c2" = 200 ] && { [ "$c3" = 302 ] || [ "$c3" = 401 ]; } && { [ "$c4" = 302 ] || [ "$c4" = 401 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -q "petty_book NOT mounted" && { say "!! petty_book did not mount"; restore; }
say "[9/9] all green"
say "md5 of the installed files:"
for f in "${ORDER[@]}"; do md5sum "${DEST[$f]}"; done
say "$KIT: DONE"
