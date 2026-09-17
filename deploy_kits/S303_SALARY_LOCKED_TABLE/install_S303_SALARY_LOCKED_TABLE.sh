#!/bin/bash
# =============================================================================
#  install_S303_SALARY_LOCKED_TABLE.sh · kit S303_SALARY_LOCKED_TABLE (session 267, 17-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S303_SALARY_LOCKED_TABLE/install_S303_SALARY_LOCKED_TABLE.sh
#
#  F-519: the August lock desk showed two totals -- the card (locked_run.total_payout, frozen at the
#  lock on 13-Sep) and a table TOTAL recomputed from today's data. The owner: "only one total".
#   /root/staff_register/staff_register.py  439d6790 (S300) -> 0a098cfa
#   A locked month's desk shows the FROZEN table read back from locked_run.report_html (its TOTAL is the
#   card's), a short per-staff "today's recompute differs" list naming what moved (information only),
#   and the frozen sheets read-only at /register/salary/locked. Unlocked months are unchanged.
#  DATA: none. salary_policy.py, the staff ledger and the hold ledger are not touched.
#
#  Gates: kit SUMS + KIT_ID -> live pin exact (or ALREADY INSTALLED) -> compile -> the register's own
#  selftest -> test_s303 (the real sheets34_html writes a frozen report, the desk reads it) -> THE WALK
#  ON THIS BOX (the kit's register over a scratch copy of the live DB, the live salary engine computing
#  read-only; August must read back and add up to the card; prints who differs and why) -> backup ->
#  place -> restart staff-register -> health. Any red after placing: the file restored, restarted.
#  No other file, no cron line, no scheduled job, nothing on manojz or the medical PC.
# =============================================================================
set -u
KIT="S303_SALARY_LOCKED_TABLE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
SRD="$ROOT/staff_register"; SRDB="$SRD/staff_register.db"
DEST="$SRD/staff_register.py"
FROM=439d679003d13fb9b0eabf6ba72b0523
TO=0a098cfa315628e3db270602a831edd9
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s303_walk_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp date systemctl curl; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
say "[1/8] kit gates green"

[ "$(m5 "$DEST")" = "$TO" ] && { say "-- ALREADY INSTALLED: $DEST carries this kit."; exit 0; }
[ "$(m5 "$DEST")" = "$FROM" ] || { say "!! [2/8] $DEST is $(m5 "$DEST"), expected $FROM (S300) - nothing installed"; exit 1; }
[ "$(m5 staff_register.py)" = "$TO" ] || { say "!! [2/8] kit staff_register.py is not its predicted md5 - nothing installed"; exit 1; }
say "[2/8] live pin exact; kit file at its predicted md5"

export PYTHONPYCACHEPREFIX="$WALK/pyc"            # compiled bytes go to /tmp, never into the deploy clone
"$VPY" -m py_compile staff_register.py test_s303.py walk_s303.py || { say "!! [3/8] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/8] py_compile green"

mkdir -p "$WALK/st" "$WALK/t" && cp -p staff_register.py "$WALK/st/" && cp -p staff_register.py "$WALK/t/"
( cd "$WALK/st" && "$VPY" -B staff_register.py --selftest 2>&1 | tail -1 | grep -q "SELFTEST OK" ) \
  || { say "!! [4/8] staff_register selftest red - nothing installed"; rm -rf "$WALK"; exit 1; }
TOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/test_s303.py" "$WALK/t" "$SRD" 2>&1 | tail -1 )"
echo "$TOUT" | grep -q "^TEST OK" || { say "!! [4/8] test_s303 red: $TOUT - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] selftest OK · $TOUT"

mkdir -p "$WALK/sr" && cp -p staff_register.py "$WALK/sr/"
"$VPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$SRDB" "$WALK/sr_walk.db" \
  || { say "!! [5/8] could not take the register scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( SR_DB_PATH="$WALK/sr_walk.db" timeout 170 "$VPY" -B "$KDIR/walk_s303.py" "$WALK/sr" "$SRD" 2>&1 )"
echo "$WOUT" | tail -1 | grep -q "^WALK OK" || { say "!! [5/8] walk red:"; echo "$WOUT" | tail -5; say "   nothing installed"; rm -rf "$WALK"; exit 1; }
rm -rf "$WALK"
say "[5/8] $(echo "$WOUT" | tail -1)"
echo "$WOUT" | grep '^   '

BAK="$DEST.bak_S303_${FROM:0:8}"
\cp -p "$DEST" "$BAK" || { say "!! [6/8] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing - restoring $DEST byte-identically"
  \cp -p "$BAK" "$DEST"; systemctl restart staff-register || true; sleep 3
  say "   $DEST $(m5 "$DEST")"; exit 1
}
\cp -p staff_register.py "$DEST" || restore
[ "$(m5 "$DEST")" = "$TO" ] || { say "!! [6/8] $DEST did not land at its pin"; restore; }
say "[6/8] placed, backup $BAK"

systemctl restart staff-register || restore
sleep 4
systemctl is-active --quiet staff-register || { say "!! staff-register not active"; restore; }
say "[7/8] staff-register active"

c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8044/register/health)
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:8044/register/salary/locked?ym=2026-08")
say "health : register $c1 · /register/salary/locked without a login $c2 (302 expected)"
[ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ]; } || restore
say "[8/8] all green"
md5sum "$DEST"
say "$KIT: DONE"
say "read next: https://attendance.dr-manoj.in/register/salary?ym=2026-08"
