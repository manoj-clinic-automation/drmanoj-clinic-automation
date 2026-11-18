#!/bin/bash
# rehearse_s874.sh -- S874 on a STAND (made-up root, copies): dry run; install; again (ALREADY); undo; undo again (refused);
# a forced red at [4/5] restores; tamper (a changed live file refused); corrupt (SUMS red); lock held (3). Nothing live touched.
set -u
KD="$(cd "$(dirname "$0")" && pwd)"; SRC="${1:?finance dir at the FROM pins}"; DBC="${2:?finance.db copy}"; OLDK="${3:?deploy_kits dir with S869}"
W=$(mktemp -d /tmp/s874reh_XXXX); P=0; F=0
ok(){ if [ "$1" = 0 ]; then P=$((P+1)); echo "PASS $2"; else F=$((F+1)); echo "FAIL $2"; fi; }
stand(){ rm -rf "$W/root"; mkdir -p "$W/root/finance/finance_ui" "$W/root/deploy"; cp -p "$SRC"/*.py "$SRC"/*.sql "$SRC"/*.json "$W/root/finance/" 2>/dev/null; cp -p "$SRC"/finance_ui/*.html "$W/root/finance/finance_ui/"; cp "$DBC" "$W/root/finance/finance.db"; }
cat > "$W/sysctl" <<'X'
#!/bin/bash
exit 0
X
cat > "$W/health" <<'X'
#!/bin/bash
echo 200
X
chmod +x "$W/sysctl" "$W/health"
E="ROOT=$W/root DB=$W/root/finance/finance.db LOCK=$W/root/deploy/.lock OLDK=$OLDK SYSTEMCTL=$W/sysctl HEALTH_CMD=$W/health NAP=0 TMPW=$W APY=python3 VPY=python3"
m5(){ md5sum "$1" | cut -c1-8; }
stand; O=$(env $E DRY=1 bash "$KD/install_S874_HUB_SHORT_MOBILE_CALL.sh" 2>&1); echo "$O" | grep -q "DRY RUN: every gate" && [ "$(m5 $W/root/finance/sanjeevni_day.py)" = 4359d048 ]; ok $? "A1 dry run green, nothing written"
O=$(env $E bash "$KD/install_S874_HUB_SHORT_MOBILE_CALL.sh" 2>&1); echo "$O" | grep -q "S874_HUB_SHORT_MOBILE_CALL: DONE" && [ "$(m5 $W/root/finance/sanjeevni_day.py)" = db30da9f ] && [ "$(m5 $W/root/finance/finance_ui/finance_approvals.html)" = 254c0bbf ] && [ ! -d "$W/root/deploy/.lock" ]; ok $? "A2 install DONE, both at TO, lock released"
O=$(env $E bash "$KD/install_S874_HUB_SHORT_MOBILE_CALL.sh" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED"; ok $? "A3 again: ALREADY INSTALLED"
O=$(env $E bash "$KD/undo_s874.sh" 2>&1); echo "$O" | grep -q "S874 UNDONE" && [ "$(m5 $W/root/finance/sanjeevni_day.py)" = 4359d048 ] && [ "$(m5 $W/root/finance/finance_ui/finance_approvals.html)" = 1f594b5f ]; ok $? "A4 undo: both back at FROM"
O=$(env $E bash "$KD/undo_s874.sh" 2>&1); echo "$O" | grep -q "not at S874's TO pin"; ok $? "A5 undo again: refused"
stand; O=$(env $E REHEARSE_RED_AT=4 bash "$KD/install_S874_HUB_SHORT_MOBILE_CALL.sh" 2>&1); echo "$O" | grep -q "RED after placing" && [ "$(m5 $W/root/finance/sanjeevni_day.py)" = 4359d048 ] && [ ! -d "$W/root/deploy/.lock" ]; ok $? "B1 a red at [4/5] restores both files, lock released"
stand; echo "# x" >> "$W/root/finance/sanjeevni_day.py"; O=$(env $E bash "$KD/install_S874_HUB_SHORT_MOBILE_CALL.sh" 2>&1); echo "$O" | grep -q "it changed after this kit was built"; ok $? "B2 a changed live file: refused"
stand; cp -r "$KD" "$W/kitc"; echo "#" >> "$W/kitc/make_s874.py"; O=$(env $E bash "$W/kitc/install_S874_HUB_SHORT_MOBILE_CALL.sh" 2>&1); echo "$O" | grep -q "SUMS.md5 gate failed"; ok $? "B3 corrupt kit: SUMS red"
stand; mkdir -p "$W/root/deploy/.lock"; echo other > "$W/root/deploy/.lock/owner"; env $E bash "$KD/install_S874_HUB_SHORT_MOBILE_CALL.sh" >/dev/null 2>&1; [ $? = 3 ]; ok $? "B4 lock held by another build: exit 3"
rm -rf "$W"; echo "REHEARSE S874: $P PASS, $F FAIL"
