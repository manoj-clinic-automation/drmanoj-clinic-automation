#!/bin/bash
# rehearse_s967.sh -- S967_STOCKCHECK_ONE_PAGE on a MADE-UP root in the device VM (never the box): dry . red@4 . red@5 . install . again .
# undo . install again . wrong FROM . a read pin moved . the lock . a corrupt kit.     bash rehearse_s967.sh KIT_DIR LIVE_ROOT_COPY DB_COPY
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; DBC="$3"; W="$(mktemp -d /tmp/reh_s967_XXXX)"; PASS=0; N=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root"; cp -rp "$F/finance" "$F/marg_ingest" "$W/root/"; mkdir -p "$W/root/shared"; cp -p "$F"/shared/*.py "$W/root/shared/" 2>/dev/null
  rm -f "$W/root/finance/"*.bak_S967_*; cp "$DBC" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho 302\n' > "$W/door"; printf '#!/bin/bash\necho "S930 stock_check mounted v1.6"\n' > "$W/log"; chmod +x "$W/hz" "$W/door" "$W/log"
run() { (export ROOT="$W/root" LOCK="$W/build.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" DOOR_CMD="$W/door" LOG_CMD="$W/log" NAP=0 APY=python3 VPY=python3 TMPW="$W"; "$@"); }
pin() { awk -v f="$1" '$2==f{print $1}' "$K/TO_PINS.md5"; }
NAMES="finance/stock_check.py finance/stock_check.html finance/item_ledger.py finance/voucher_judge.py"
at_to() { for n in $NAMES; do [ "$(m5 "$W/root/$n")" = "$(pin $n)" ] || return 1; done; }
at_from() { [ "$(m5 "$W/root/finance/stock_check.py")" = 83bbed0dc396573fa2d0a53d2e12ba93 ] && [ "$(m5 "$W/root/finance/stock_check.html")" = 69d1fabe4848d7f0fda5828eb12fb176 ] \
  && [ "$(m5 "$W/root/finance/item_ledger.py")" = fe31f2c3a5c41412ccbfc7746a255b89 ] && [ "$(m5 "$W/root/finance/voucher_judge.py")" = 81d04b411db72820932835c7a43024cf ]; }
dbsum() { m5 "$W/root/finance/finance.db"; }
INST="$K/install_S967_STOCKCHECK_ONE_PAGE.sh"
fresh; D0=$(dbsum); O=$(run env DRY=1 bash "$INST" 2>&1); echo "$O" | grep -E "LIVE-SHAPE|\[3/6\]" | cut -c1-220 | sed 's/^/      /'
echo "$O" | grep -q "DRY RUN: every gate" && at_from && [ "$(dbsum)" = "$D0" ]; ok $? "dry: every gate, the walk twice, the control red, S965's walk, the live-shape desk; nothing written"
fresh; O=$(run env REHEARSE_RED_AT=4 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[4/6\]" && at_from; ok $? "red at [4/6]: the four files back"
fresh; O=$(run env REHEARSE_RED_AT=5 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[5/6\]" && at_from; ok $? "red at [5/6]: the four files back"
fresh; printf '#!/bin/bash\necho "S930 stock_check mounted v1.5"\n' > "$W/log15"; chmod +x "$W/log15"; O=$(run env LOG_CMD="$W/log15" bash "$INST" 2>&1)
echo "$O" | grep -q "does not show 'S930 stock_check mounted v1.6'" && at_from; ok $? "the log shows the old mount only: put back at [4/6] (second look 9)"
fresh; D0=$(dbsum); O=$(run bash "$INST" 2>&1); echo "$O" | tail -6 | cut -c1-220 | sed 's/^/      /'
echo "$O" | grep -q "S967_STOCKCHECK_ONE_PAGE: DONE" && at_to && [ "$(dbsum)" = "$D0" ]; ok $? "install: four files at their TO pins; the database not touched"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED" && at_to; ok $? "again: ALREADY INSTALLED, nothing touched"
O=$(run bash "$K/undo_s967.sh" 2>&1); echo "$O" | grep -q "S967 UNDONE" && at_from; ok $? "undo: the four files back at FROM"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q ": DONE" && at_to; ok $? "install again after the undo"
fresh; echo "# drift" >> "$W/root/finance/item_ledger.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*item_ledger.py.*changed after this kit was built" && [ "$(m5 "$W/root/finance/stock_check.py")" = 83bbed0dc396573fa2d0a53d2e12ba93 ]; ok $? "wrong FROM (a live file changed): stopped at [2/6], nothing placed"
fresh; echo "# drift" >> "$W/root/finance/record_judges.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*record_judges.py is not at" && at_from; ok $? "a file the desk reads moved: stopped at [2/6], nothing placed"
fresh; mkdir "$W/build.lock"; O=$(run bash "$INST" 2>&1); RC=$?; rmdir "$W/build.lock"; [ "$RC" = 3 ] && at_from; ok $? "another build holds the lock: exit 3, nothing placed"
fresh; cp "$K/SUMS.md5" "$W/sums.bak"; sed -i '1s/^./0/' "$K/SUMS.md5"; O=$(run bash "$INST" 2>&1); cp "$W/sums.bak" "$K/SUMS.md5"
echo "$O" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "a corrupt kit: refused at [1/6]"
rm -rf "$W"
echo "REHEARSAL $PASS/$N"
