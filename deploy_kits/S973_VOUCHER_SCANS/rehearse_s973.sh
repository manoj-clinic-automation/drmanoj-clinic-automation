#!/bin/bash
# rehearse_s973.sh -- S973_VOUCHER_SCANS on a MADE-UP root in the device VM (never the box): dry . red@5 . red@6 . a 'NOT mounted' in the scan
# app's log . install . again . undo . install again . wrong FROM . a read pin moved . a new file already there . the lock . a corrupt kit.
#     bash rehearse_s973.sh KIT_DIR LIVE_ROOT_COPY FINANCE_DB_COPY REPO_COPY
#  LIVE_ROOT_COPY holds finance/ marg_ingest/ shared/ assetapp/ as live; REPO_COPY holds deploy_kits/S841_*/ and S754_*/ walks.
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; DBC="$3"; RP="$(cd "$4" && pwd)"; W="$(mktemp -d /tmp/reh_s973_XXXX)"; PASS=0; N=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root"; cp -rp "$F/finance" "$F/marg_ingest" "$F/shared" "$F/assetapp" "$W/root/"
  rm -f "$W/root/finance/"*.bak_S973_* "$W/root/assetapp/"*.bak_S973_* "$W/root/shared/"*.bak_S973_*; cp "$DBC" "$W/root/finance/finance.db"
  python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('CREATE TABLE IF NOT EXISTS bills (id INTEGER PRIMARY KEY, kind TEXT, stamp_no TEXT, bill_no TEXT, bill_date TEXT, submitted_at TEXT, created_at TEXT, status TEXT, dup_of INTEGER)'); c.execute('CREATE TABLE IF NOT EXISTS bill_items (id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, quantity REAL, batch TEXT)'); c.commit()" "$W/root/assetapp/assets.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho 302\n' > "$W/door"; printf '#!/bin/bash\necho "S930 stock_check mounted v1.8"\n' > "$W/log"; chmod +x "$W/hz" "$W/door" "$W/log"
run() { (export ROOT="$W/root" REPO="$RP" LOCK="$W/build.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" DOOR_CMD="$W/door" LOG_CMD="$W/log" NAP=0 APY=python3 VPY=python3 TMPW="$W" \
  ADB="$W/root/assetapp/assets.db"; "$@"); }
pin() { awk -v f="$1" '$2==f{print $1}' "$K/TO_PINS.md5"; }
NAMES="finance/voucher_inquiry.py finance/voucher_judge.py finance/amir_day.py finance/porders_s454.py finance/voucher_scan.py assetapp/asset_register.py assetapp/claude_reader.py shared/scan_quality.py"
at_to() { for n in $NAMES; do [ "$(m5 "$W/root/$n")" = "$(pin $n)" ] || return 1; done; }
at_from() { [ "$(m5 "$W/root/finance/voucher_inquiry.py")" = ac76b9d339de6b58b7835cab7e46e08d ] && [ "$(m5 "$W/root/finance/voucher_judge.py")" = 6c7259418481cd9f37099f93a9ca7b17 ] \
  && [ "$(m5 "$W/root/finance/amir_day.py")" = 27a2a128f8e6fbdbf0c015727db70538 ] && [ "$(m5 "$W/root/finance/porders_s454.py")" = 3f52d1f390ff704d152fd3b96bba5afc ] \
  && [ "$(m5 "$W/root/assetapp/asset_register.py")" = a325d0f400923e1989ff4cd2a4df408d ] && [ "$(m5 "$W/root/assetapp/claude_reader.py")" = 5b27b2269f4f358a36cd62aef6b0eb7a ] \
  && [ ! -e "$W/root/finance/voucher_scan.py" ]; }
sq_from() { [ "$(m5 "$W/root/shared/scan_quality.py")" = 505a114f34452b5be994b04eca36e4b7 ]; }
sq_to() { [ "$(m5 "$W/root/shared/scan_quality.py")" = "$(pin shared/scan_quality.py)" ]; }
dbsum() { m5 "$W/root/finance/finance.db"; }
INST="$K/install_S973_VOUCHER_SCANS.sh"
fresh; D0=$(dbsum); O=$(run env DRY=1 bash "$INST" 2>&1); sq_from || echo "      (scan_quality not at FROM after dry)"; echo "$O" | grep -E "LIVE-SHAPE|\[3/7\]|\[4/7\]|^!!" | cut -c1-240 | sed 's/^/      /'
echo "$O" | grep -q "DRY RUN: every gate" && at_from && [ "$(dbsum)" = "$D0" ]; ok $? "dry: every gate, both walks twice / on the real app, both controls red, kit B/A2/A1/S965/S841/S754 walks, kit C on a copy; nothing written"
fresh; O=$(run env REHEARSE_RED_AT=5 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[5/7\]" && at_from && sq_to; ok $? "red at [5/7]: the six files back, voucher_scan.py moved aside, scan_quality kept"
fresh; O=$(run env REHEARSE_RED_AT=6 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[6/7\]" && echo "$O" | grep -q "S973 cards withdrawn:" && at_from; ok $? "red at [6/7]: the seven files back, voucher_scan.py moved aside, the database's S973 writes put back"
fresh; printf '#!/bin/bash\n[ "$1" = assetapp ] && echo "renewals_one NOT mounted: x" || echo "S930 stock_check mounted v1.8"\n' > "$W/logbad"; chmod +x "$W/logbad"; O=$(run env LOG_CMD="$W/logbad" bash "$INST" 2>&1)
echo "$O" | grep -q "the scan app's log after the restart" && at_from; ok $? "the scan app's log says a part is NOT mounted: put back at [5/7]"
fresh; O=$(run bash "$INST" 2>&1); echo "$O" | tail -7 | cut -c1-240 | sed 's/^/      /'
TB=$(python3 -c "import sqlite3,sys,datetime as dt; c=sqlite3.connect(sys.argv[1]); print(c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='stock_voucher_scanask'\").fetchone()[0], (c.execute(\"SELECT value FROM setting WHERE key='stock.scan_ask_from'\").fetchone() or [''])[0] == dt.datetime.now(dt.timezone(dt.timedelta(hours=5,minutes=30))).date().isoformat(), c.execute(\"SELECT COUNT(*) FROM amir_job WHERE key LIKE 'S973:%'\").fetchone()[0])" "$W/root/finance/finance.db")
echo "$O" | grep -q "S973_VOUCHER_SCANS: DONE" && at_to && [ "$TB" = "1 True 0" ]; ok $? "install: seven files at their TO pins; the table, the cut-name date = today, no card ($TB)"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED" && at_to; ok $? "again: ALREADY INSTALLED, nothing touched"
python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute(\"INSERT INTO amir_job (key,kind,subject,created_at,show_from) VALUES ('S973:prt:1:L000001','ask','X','2026-11-27','2026-11-27')\"); c.commit()" "$W/root/finance/finance.db"
O=$(run bash "$K/undo_s973.sh" 2>&1); WJ=$(python3 -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute(\"SELECT done_how FROM amir_job WHERE key='S973:prt:1:L000001'\").fetchone()[0])" "$W/root/finance/finance.db")
echo "$O" | grep -q "S973 UNDONE" && at_from && sq_to && [ "$WJ" = withdrawn ]; ok $? "undo: the six files back at FROM, voucher_scan.py moved aside, scan_quality kept at its new version, an open print card withdrawn"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q ": DONE" && at_to; ok $? "install again after the undo"
fresh; echo "# drift" >> "$W/root/finance/amir_day.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/7\].*amir_day.py.*changed after this kit was built" && [ "$(m5 "$W/root/assetapp/claude_reader.py")" = 5b27b2269f4f358a36cd62aef6b0eb7a ]; ok $? "wrong FROM (a live file changed): stopped at [2/7], nothing placed"
fresh; echo "# drift" >> "$W/root/assetapp/clinic_papers.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/7\].*clinic_papers.py is not at" && at_from; ok $? "a file the kit reads moved: stopped at [2/7], nothing placed"
fresh; echo "x" > "$W/root/finance/voucher_scan.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/7\].*voucher_scan.py already exists" && [ "$(m5 "$W/root/finance/amir_day.py")" = 27a2a128f8e6fbdbf0c015727db70538 ]; ok $? "a new file already there (not the kit's): stopped at [2/7], nothing placed"
fresh; mkdir "$W/build.lock"; O=$(run bash "$INST" 2>&1); RC=$?; rmdir "$W/build.lock"; [ "$RC" = 3 ] && at_from; ok $? "another build holds the lock: exit 3, nothing placed"
fresh; cp "$K/SUMS.md5" "$W/sums.bak"; sed -i '1s/^./0/' "$K/SUMS.md5"; O=$(run bash "$INST" 2>&1); cp "$W/sums.bak" "$K/SUMS.md5"
echo "$O" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "a corrupt kit: refused at [1/7]"
rm -rf "$W"
echo "REHEARSAL $PASS/$N"
