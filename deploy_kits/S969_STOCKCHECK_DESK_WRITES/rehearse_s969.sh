#!/bin/bash
# rehearse_s969.sh -- S969_STOCKCHECK_DESK_WRITES on a MADE-UP root in the device VM (never the box): dry . red@4 . red@5 . the old mount in the
# log . install . again . undo . install again . wrong FROM . a read pin moved . the lock . a corrupt kit.
#     bash rehearse_s969.sh KIT_DIR LIVE_ROOT_COPY DB_COPY
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; DBC="$3"; W="$(mktemp -d /tmp/reh_s969_XXXX)"; PASS=0; N=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root"; cp -rp "$F/finance" "$F/marg_ingest" "$W/root/"; mkdir -p "$W/root/shared"; cp -p "$F"/shared/*.py "$W/root/shared/" 2>/dev/null
  rm -f "$W/root/finance/"*.bak_S969_*; cp "$DBC" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho 302\n' > "$W/door"; printf '#!/bin/bash\necho "S930 stock_check mounted v1.7"\n' > "$W/log"; chmod +x "$W/hz" "$W/door" "$W/log"
run() { (export ROOT="$W/root" LOCK="$W/build.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" DOOR_CMD="$W/door" LOG_CMD="$W/log" NAP=0 APY=python3 VPY=python3 TMPW="$W"; "$@"); }
pin() { awk -v f="$1" '$2==f{print $1}' "$K/TO_PINS.md5"; }
NAMES="finance/stock_check.py finance/stock_check.html finance/stock_watch.py finance/voucher_judge.py finance/amir_day.py"
at_to() { for n in $NAMES; do [ "$(m5 "$W/root/$n")" = "$(pin $n)" ] || return 1; done; }
at_from() { [ "$(m5 "$W/root/finance/stock_check.py")" = 5f1b239e6af3c931cc15adb17fd2edb2 ] && [ "$(m5 "$W/root/finance/stock_check.html")" = a9f7b6827e590cd63a3e2cc053334d0c ] \
  && [ "$(m5 "$W/root/finance/stock_watch.py")" = e205f889b456f4c6c61b07389073943e ] && [ "$(m5 "$W/root/finance/voucher_judge.py")" = aea436338fc138b1ff1e27b552b328bc ] \
  && [ "$(m5 "$W/root/finance/amir_day.py")" = 1cf0f13f70cb7bafb4c34359c7b54285 ]; }
dbsum() { m5 "$W/root/finance/finance.db"; }
INST="$K/install_S969_STOCKCHECK_DESK_WRITES.sh"
fresh; D0=$(dbsum); O=$(run env DRY=1 bash "$INST" 2>&1); echo "$O" | grep -E "LIVE-SHAPE|\[3/6\]" | cut -c1-240 | sed 's/^/      /'
echo "$O" | grep -q "DRY RUN: every gate" && at_from && [ "$(dbsum)" = "$D0" ]; ok $? "dry: every gate, the walk twice, the control red, S967's and S965's walks, the live-shape desk + a write-off on a copy; nothing written"
fresh; O=$(run env REHEARSE_RED_AT=4 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[4/6\]" && at_from; ok $? "red at [4/6]: the five files back"
fresh; O=$(run env REHEARSE_RED_AT=5 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[5/6\]" && at_from; ok $? "red at [5/6]: the five files back"
fresh; printf '#!/bin/bash\necho "S930 stock_check mounted v1.6"\n' > "$W/log16"; chmod +x "$W/log16"; O=$(run env LOG_CMD="$W/log16" bash "$INST" 2>&1)
echo "$O" | grep -q "does not show 'S930 stock_check mounted v1.7'" && at_from; ok $? "the log shows the old mount only: put back at [4/6]"
fresh; O=$(run bash "$INST" 2>&1); echo "$O" | tail -6 | cut -c1-240 | sed 's/^/      /'
TB=$(python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='stock_desk_action'\").fetchone()[0], c.execute(\"SELECT COUNT(*) FROM amir_job WHERE key LIKE 'S969:%'\").fetchone()[0])" "$W/root/finance/finance.db")
echo "$O" | grep -q "S969_STOCKCHECK_DESK_WRITES: DONE" && at_to && [ "$TB" = "1 0" ]; ok $? "install: five files at their TO pins; the database gets only the empty table, no card line ($TB)"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED" && at_to; ok $? "again: ALREADY INSTALLED, nothing touched"
O=$(run bash "$K/undo_s969.sh" 2>&1); echo "$O" | grep -q "S969 UNDONE" && at_from; ok $? "undo: the five files back at FROM"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q ": DONE" && at_to; ok $? "install again after the undo"
fresh; echo "# drift" >> "$W/root/finance/amir_day.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*amir_day.py.*changed after this kit was built" && [ "$(m5 "$W/root/finance/stock_check.py")" = 5f1b239e6af3c931cc15adb17fd2edb2 ]; ok $? "wrong FROM (a live file changed): stopped at [2/6], nothing placed"
fresh; echo "# drift" >> "$W/root/finance/qty_words.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*qty_words.py is not at" && at_from; ok $? "a file the writes read moved: stopped at [2/6], nothing placed"
fresh; mkdir "$W/build.lock"; O=$(run bash "$INST" 2>&1); RC=$?; rmdir "$W/build.lock"; [ "$RC" = 3 ] && at_from; ok $? "another build holds the lock: exit 3, nothing placed"
fresh; cp "$K/SUMS.md5" "$W/sums.bak"; sed -i '1s/^./0/' "$K/SUMS.md5"; O=$(run bash "$INST" 2>&1); cp "$W/sums.bak" "$K/SUMS.md5"
echo "$O" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "a corrupt kit: refused at [1/6]"
rm -rf "$W"
echo "REHEARSAL $PASS/$N"
