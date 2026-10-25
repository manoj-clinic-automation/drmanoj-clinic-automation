#!/bin/bash
# =============================================================================
#  install_S650_ATTCORR.sh . kit S650 (25-Oct-2026, session S354, the parent) . D786 the month-end attendance corrections
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s650kit && cp -rp /root/deploy/repo/deploy_kits/S650_ATTCORR /tmp/s650kit && bash /tmp/s650kit/install_S650_ATTCORR.sh
#  (DRY=1 before bash: every gate and all four walks, nothing written.)
#
#  /root/staff_register/att_correction.py  NEW 448de63a        the flow: sheet, three screens, Approve & save, the lock's wait, the lines' door
#  /root/staff_register/staff_register.py  0a098cfa -> 7e92bc20  1 counted edit: the hook before __main__
#  /root/finance/aaj_duties.json           1c49af35 -> 90219853  1 counted edit: three 'fetch' lines (shipped as aaj_duties.json.kit)
#  /root/finance/aaj_seed.py               98f63364 -> 64d9a607  2 counted edits: reception's two lines, Shavez's one
#  /root/finance/owner_console.py          a6315bfd -> e414e7ad  1 counted edit: the console's 'Attendance correction' line
#  No data step (the staging tables appear on first use). Restarts staff-register, then clinic-finance.
#  Red after placing: every old file back byte-identically, the new file moved aside, both restarted.
#  Undo:  see README.md (four \cp lines and one mv).
# =============================================================================
set -u
KIT="S650_ATTCORR"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"          # the register's python (staff-register.service)
FPY="${FPY:-/usr/bin/python3}"                   # the finance app's python (clinic-finance.service)
REG="${REG:-/root/staff_register}"; FIN="${FIN:-/root/finance}"; ATT="${ATT:-/root}"
MAPF="${DUTY_MAP_JSON:-/root/deploy/repo/claude_code_briefs/DUTY_MAP.json}"; export DUTY_MAP_JSON="$MAPF"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
RSVC="${RSVC:-staff-register}"; RPORT="${RPORT:-8044}"
FSVC="${FSVC:-clinic-finance}"; FPORT="${FPORT:-8106}"
MAPMD5=78b5f07ef7cdd48b1a76d78db52107fc
NEWF=att_correction.py; NEWMD5=448de63aa625cc0a8fd4e01b48232a0f
# live path | kit file | from | to
ROWS="$REG/staff_register.py|staff_register.py|0a098cfa315628e3db270602a831edd9|7e92bc20458b8be182987820eed35233
$FIN/aaj_duties.json|aaj_duties.json.kit|1c49af3585c63beeeceef8803f112fca|90219853b4a25b051fa3f53f6c09d74d
$FIN/aaj_seed.py|aaj_seed.py|98f633640ada6e809ce60fa1f0b826a7|64d9a607fda40b34a96ed72fa688979b
$FIN/owner_console.py|owner_console.py|a6315bfdcc0f4811bf546f89dd96002f|e414e7ad9e683b5e7ecabff5e481c721"
HAVE_LOCK=0; WN=""; WO=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; [ -n "$WN" ] && rm -rf "$WN" "$WO"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
rhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$RPORT/register/health"; }
fhealth() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FPORT/finance/healthz"; }

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
[ "$(m5 "$KDIR/$NEWF")" = "$NEWMD5" ] || stop "the kit's $NEWF is not the built file"
ALL_TO=1
while IFS='|' read -r LP KF FROM TO; do
  [ "$(m5 "$KDIR/$KF")" = "$TO" ] || stop "the kit's $KF is not the built file"
  L=$(m5 "$LP"); [ "$L" = "$TO" ] || ALL_TO=0
done <<< "$ROWS"
if [ "$ALL_TO" = 1 ] && [ "$(m5 "$REG/$NEWF")" = "$NEWMD5" ]; then echo "ALREADY INSTALLED."; exit 0; fi
while IFS='|' read -r LP KF FROM TO; do
  L=$(m5 "$LP"); [ "$L" = "$FROM" ] || stop "the live $LP changed since this kit was built (live ${L:0:8}, kit expects ${FROM:0:8})"
done <<< "$ROWS"
[ -e "$REG/$NEWF" ] && stop "$REG/$NEWF already exists and is not this kit's file"
[ "$(m5 "$MAPF")" = "$MAPMD5" ] || stop "the duty map $MAPF is not v20 (78b5f07e) -- it moved since this kit was built"
echo "2. the four live files and the duty map are the ones this kit was built from; $NEWF is new"
DB=$("$SYSTEMCTL" show -p Environment "$FSVC" 2>/dev/null | sed 's/^Environment=//' | tr ' ' '\n' | sed -n 's/^FINANCE_DB=//p' | head -1); [ -n "$DB" ] || DB="$FIN/finance.db"
[ -f "$DB" ] || stop "the finance database was not found ($DB)"
WN=$(mktemp -d /tmp/s650new.XXXX); WO=$(mktemp -d /tmp/s650old.XXXX)
for f in staff_register.py "$NEWF" aaj_seed.py owner_console.py; do \cp "$KDIR/$f" "$WN/$f"; done
\cp "$KDIR/aaj_duties.json.kit" "$WN/aaj_duties.json"
for f in salary_policy.py salary_engine.py; do \cp "$REG/$f" "$WN/$f"; \cp "$REG/$f" "$WO/$f"; done
\cp "$REG/staff_register.py" "$WO/"; for f in aaj_seed.py aaj_duties.json owner_console.py; do \cp "$FIN/$f" "$WO/$f"; done
for f in staff_register.py "$NEWF"; do "$VPY" -B -m py_compile "$WN/$f" || stop "$f does not compile with $VPY"; done
for f in aaj_seed.py owner_console.py; do "$FPY" -B -m py_compile "$WN/$f" || stop "$f does not compile with $FPY"; done
"$FPY" -c "import json,sys; json.load(open(sys.argv[1]))" "$WN/aaj_duties.json" || stop "aaj_duties.json is not valid JSON"
echo "3. every file compiles (register with $VPY, finance with $FPY); the duties file is valid JSON"
R=$("$VPY" -B walk_s650.py "$WN" "$ATT" 2>&1 | tail -1)
[ "$R" = "43 of 43 green" ] || { "$VPY" -B walk_s650.py "$WN" "$ATT" 2>&1 | grep -E 'RED|Error' | head -20; stop "the register walk is not green ($R)"; }
echo "4. the register walk on made-up staff: $R"
R=$("$VPY" -B walk_s650.py "$WO" "$ATT" --old 2>&1 | tail -1)
[ "$R" = "36 S650 check(s) red · 0 older red · 7 green" ] || { echo "$R"; stop "the control on the live register is not as expected ($R)"; }
echo "   control on the live register: $R"
R=$("$FPY" -B walk_s650_lists.py "$WN" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" 2>&1 | tail -1)
[ "$R" = "8 of 8 green" ] || { "$FPY" -B walk_s650_lists.py "$WN" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" 2>&1 | grep -E 'RED|Error' | head; stop "the lists walk on the live books is not green ($R)"; }
echo "5. the lists and console walk on the live books: $R"
R=$("$FPY" -B walk_s650_lists.py "$WO" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" --old 2>&1 | tail -1)
[ "$R" = "4 S650 check(s) red · 0 older red · 4 green" ] || { echo "$R"; stop "the control on the live lists is not as expected ($R)"; }
echo "   control on the live lists: $R"
[ "$(rhealth)" = 200 ] || stop "the staff register is not healthy before the install"
[ "$(fhealth)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1

restore() {
  while IFS='|' read -r LP KF FROM TO; do [ -f "$LP.bak_S650" ] && \cp -p "$LP.bak_S650" "$LP"; done <<< "$ROWS"
  [ -f "$REG/$NEWF" ] && mv -f "$REG/$NEWF" "$REG/$NEWF.removed_S650"
  "$SYSTEMCTL" restart "$RSVC"; "$SYSTEMCTL" restart "$FSVC"
  h1=000; h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h1=$(rhealth); h2=$(fhealth); [ "$h1" = 200 ] && [ "$h2" = 200 ] && break; done
  bad=0; while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$FROM" ] || { echo "   !! $LP is NOT ${FROM:0:8} -- copy $LP.bak_S650 back by hand"; bad=1; }; done <<< "$ROWS"
  [ "$bad" = 0 ] && echo "   every old file is back byte-identically; $NEWF moved aside"
  echo "   after the restore: register $h1, finance $h2. Send a photo of this screen to Claude."; exit 1
}
while IFS='|' read -r LP KF FROM TO; do \cp -p "$LP" "$LP.bak_S650" || stop "could not keep a backup of $LP"; done <<< "$ROWS"
\cp "$KDIR/$NEWF" "$REG/$NEWF" && chmod --reference="$REG/staff_register.py.bak_S650" "$REG/$NEWF" 2>/dev/null
while IFS='|' read -r LP KF FROM TO; do \cp "$KDIR/$KF" "$LP" && chmod --reference="$LP.bak_S650" "$LP" 2>/dev/null; done <<< "$ROWS"
ok=1; [ "$(m5 "$REG/$NEWF")" = "$NEWMD5" ] || ok=0
while IFS='|' read -r LP KF FROM TO; do [ "$(m5 "$LP")" = "$TO" ] || ok=0; done <<< "$ROWS"
[ "$ok" = 1 ] || { echo "!! read-back did not match"; restore; }
echo "6. placed five files (backups *.bak_S650), every one read back by md5"
"$SYSTEMCTL" restart "$RSVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(rhealth); [ "$h" = 200 ] && break; done
[ "$h" = 200 ] || { echo "!! RED: the register is not healthy after the restart ($h)"; restore; }
if journalctl -u "$RSVC" --since "-2 min" --no-pager 2>/dev/null | grep -q "att_correction not installed"; then
  journalctl -u "$RSVC" --since "-2 min" --no-pager | grep "att_correction not installed" | tail -1
  echo "!! RED: the register started without the new pages"; restore
fi
R=$("$VPY" -B liveread_s650.py "$REG" 2>&1 | tail -1)
case "$R" in "attcorr live: routes 8 · lock wrapped yes · punch feed read"*) echo "7. $RSVC restarted and healthy; the live read: $R";;
  *) echo "!! RED: the live read is not as expected: $R"; restore;; esac
"$SYSTEMCTL" restart "$FSVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(fhealth); [ "$h" = 200 ] && break; done
R=$("$FPY" -B walk_s650_lists.py "$FIN" "$FIN" --db "$DB" --map "$MAPF" --base "$WO" 2>&1 | tail -1)
if [ "$h" != 200 ] || [ "$R" != "8 of 8 green" ]; then echo "!! RED after placing (finance $h; lists walk on the placed files: $R)"; restore; fi
echo "8. $FSVC restarted and healthy; the lists walk on the placed files: $R"
echo ""
echo "INSTALLED. From 1-Nov reception's list asks for the attendance correction sheet; the owner approves at"
echo "   https://followup.dr-manoj.in/register/attcorr"
