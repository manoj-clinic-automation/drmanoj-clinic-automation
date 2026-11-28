#!/bin/bash
# rehearse_s975.sh -- S975_STOCKCHECK_V10 on a MADE-UP root in the device VM (never the box): dry . red@4 . red@5 . the old mount in the log .
# install . again . undo . install again . wrong FROM . a read pin moved . the lock . a corrupt kit.
#     bash rehearse_s975.sh KIT_DIR LIVE_ROOT_COPY DB_COPY [STEP]
# STEP (1-12) runs that one step only, with its scratch in $REH_W kept between calls (the device shell stops what outlives a call);
# steps 5-8 share one root (install . again . undo . install again) and run in that order. No STEP: all twelve.
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; DBC="$3"; W="${REH_W:-$(mktemp -d /tmp/reh_s975_XXXX)}"; mkdir -p "$W"; PASS=0; N=0; ONLY="${4:-}"; I=0
want() { I=$((I+1)); [ -z "$ONLY" ] || [ "$ONLY" = "$I" ]; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root"; cp -rp "$F/finance" "$F/marg_ingest" "$W/root/"; mkdir -p "$W/root/shared"; cp -p "$F"/shared/*.py "$W/root/shared/" 2>/dev/null
  rm -f "$W/root/finance/"*.bak_S975_*; cp "$DBC" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho 302\n' > "$W/door"; printf '#!/bin/bash\necho "S930 stock_check mounted v1.9"\n' > "$W/log"; chmod +x "$W/hz" "$W/door" "$W/log"
run() { (export ROOT="$W/root" LOCK="$W/build.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" DOOR_CMD="$W/door" LOG_CMD="$W/log" NAP=0 APY=python3 VPY=python3 TMPW="$W"; "$@"); }
pin() { awk -v f="$1" '$2==f{print $1}' "$K/TO_PINS.md5"; }
NAMES="finance/stock_check.py finance/stock_check.html finance/voucher_judge.py finance/item_ledger.py"
at_to() { for n in $NAMES; do [ "$(m5 "$W/root/$n")" = "$(pin $n)" ] || return 1; done; }
at_from() { [ "$(m5 "$W/root/finance/stock_check.py")" = 623c10528fead13397ac7e7067eb9935 ] && [ "$(m5 "$W/root/finance/stock_check.html")" = 225af840770e22779bd5b670f15fb22a ] \
  && [ "$(m5 "$W/root/finance/voucher_judge.py")" = 0a066f960fba1a110084121a82d4ede3 ] && [ "$(m5 "$W/root/finance/item_ledger.py")" = 6735167f3b56793ae6edbfd504f5584e ]; }
dbsum() { m5 "$W/root/finance/finance.db"; }
INST="$K/install_S975_STOCKCHECK_V10.sh"
if want; then
fresh; D0=$(dbsum); O=$(run env DRY=1 bash "$INST" 2>&1); echo "$O" | grep -E "LIVE-SHAPE|\[3/6\]|^!!" | cut -c1-240 | sed 's/^/      /'
echo "$O" | grep -q "DRY RUN: every gate" && at_from && [ "$(dbsum)" = "$D0" ]; ok $? "dry: every gate, the walk twice, the control red, the five earlier walks, the bands on a copy; nothing written"
fi
if want; then
fresh; O=$(run env REHEARSE_RED_AT=4 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[4/6\]" && at_from; ok $? "red at [4/6]: the four files back"
fi
if want; then
fresh; O=$(run env REHEARSE_RED_AT=5 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[5/6\]" && at_from; ok $? "red at [5/6]: the four files back"
fi
if want; then
fresh; printf '#!/bin/bash\necho "S930 stock_check mounted v1.8"\n' > "$W/log18"; chmod +x "$W/log18"; O=$(run env LOG_CMD="$W/log18" bash "$INST" 2>&1)
echo "$O" | grep -q "does not show 'S930 stock_check mounted v1.9'" && at_from; ok $? "the log shows the old mount only: put back at [4/6]"
fi
if want; then
fresh; D0=$(dbsum); O=$(run bash "$INST" 2>&1); echo "$O" | tail -6 | cut -c1-240 | sed 's/^/      /'
echo "$O" | grep -q "S975_STOCKCHECK_V10: DONE" && at_to && [ "$(dbsum)" = "$D0" ]; ok $? "install: four files at their TO pins; the database untouched"
fi
if want; then
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED" && at_to; ok $? "again: ALREADY INSTALLED, nothing touched"
fi
if want; then
O=$(run bash "$K/undo_s975.sh" 2>&1); echo "$O" | grep -q "S975 UNDONE" && at_from; ok $? "undo: the four files back at FROM"
fi
if want; then
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q ": DONE" && at_to; ok $? "install again after the undo"
fi
if want; then
fresh; echo "# drift" >> "$W/root/finance/item_ledger.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*item_ledger.py.*changed after this kit was built" && [ "$(m5 "$W/root/finance/stock_check.py")" = 623c10528fead13397ac7e7067eb9935 ]; ok $? "wrong FROM (a live file changed): stopped at [2/6], nothing placed"
fi
if want; then
fresh; echo "# drift" >> "$W/root/finance/voucher_inquiry.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*voucher_inquiry.py is not at" && at_from; ok $? "a file the kit reads moved: stopped at [2/6], nothing placed"
fi
if want; then
fresh; mkdir "$W/build.lock"; O=$(run bash "$INST" 2>&1); RC=$?; rmdir "$W/build.lock"; [ "$RC" = 3 ] && at_from; ok $? "another build holds the lock: exit 3, nothing placed"
fi
if want; then
fresh; cp "$K/SUMS.md5" "$W/sums.bak"; sed -i '1s/^./0/' "$K/SUMS.md5"; O=$(run bash "$INST" 2>&1); cp "$W/sums.bak" "$K/SUMS.md5"
echo "$O" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "a corrupt kit: refused at [1/6]"
fi
[ -n "${REH_W:-}" ] || rm -rf "$W"
echo "REHEARSAL $PASS/$N"
