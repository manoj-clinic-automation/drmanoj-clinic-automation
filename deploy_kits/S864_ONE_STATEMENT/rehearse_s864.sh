#!/bin/bash
# rehearse_s864.sh <live finance dir (FROM files)> <shared dir> <finance.db COPY> <deploy_kits holding the walks> -- the installer and the undo,
# rehearsed on a made-up /root (never the server): dry · a forced red at [4/5] · install · again · a page answering 500 · undo · undo again ·
# a tampered kit · a drifted live file · a held lock. Last line: 'REHEARSE S864: n PASS, m FAIL'.
set -u
LIVE="$1"; SHARED="$2"; DBC="$3"; KDS="$4"
KDIR="$(cd "$(dirname "$0")" && pwd)"
T="$(mktemp -d /tmp/reh864_XXXX)"; P=0; F=0
ok() { if [ "$1" = 0 ]; then P=$((P+1)); echo "PASS $2"; else F=$((F+1)); echo "FAIL $2"; fi; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to() { awk -v f="finance/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
cat > "$T/hz.sh" <<'EOF'
#!/bin/bash
case "$1" in /finance/healthz) echo 200;; *) cat "$(dirname "$0")/page_code" 2>/dev/null || echo 302;; esac
EOF
chmod +x "$T/hz.sh"; echo 302 > "$T/page_code"
printf '#!/bin/bash\nexit 0\n' > "$T/sysctl.sh"; chmod +x "$T/sysctl.sh"
setup() { rm -rf "$T/root" "$T/kit"; mkdir -p "$T/root/finance/finance_ui" "$T/root/assetapp" "$T/root/deploy" "$T/root/finance/_off"
  cp -p "$LIVE"/*.py "$T/root/finance/"; cp -p "$LIVE"/*.sql "$LIVE"/*.json "$T/root/finance/" 2>/dev/null; cp -p "$LIVE"/finance_ui/*.html "$T/root/finance/finance_ui/" 2>/dev/null
  cp -r "$SHARED" "$T/root/shared"; cp "$DBC" "$T/root/finance/finance.db"
  python3 - "$T/root/assetapp/assets.db" "$DBC" <<'EOF'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.execute("CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT, vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL, stamp_no TEXT, status TEXT, lane TEXT, bill_month TEXT, created_at TEXT)")
c.execute("CREATE TABLE bill_items(id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, pack_size TEXT, quantity REAL, rate REAL, amount REAL, make TEXT, model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT, asset_id INTEGER)")
import json                                     # made-up readings for the copy's October scans (the real ones live only on the server)
f = sqlite3.connect(sys.argv[2])
for sid, d in f.execute("SELECT asset_bill_id, detail FROM purchase_sarvam_check WHERE month='2026-10'"):
    c.execute("INSERT OR IGNORE INTO bills(id,kind,vendor,bill_no,bill_date,total_amount) VALUES (?,?,?,?,?,?)", (sid, "Pharmacy", "MADE UP", "1", "2026-10-01", 1.0))
    for it in (json.loads(d or "{}").get("items") or []):
        c.execute("INSERT INTO bill_items(bill_id,item_name,quantity,rate,batch,expiry) VALUES (?,?,?,?,?,?)", (sid, it.get("scan_item"), 1, 1.0, "RB1", "1/29"))
c.commit()
EOF
  cp -rp "$KDIR" "$T/kit"; }
run() { (cd /tmp && ROOT="$T/root" KD="$KDS" LOCK="$T/root/deploy/lock" SYSTEMCTL="$T/sysctl.sh" HEALTH_CMD="$T/hz.sh" JOURNAL_CMD=true NAP=0 \
  APY="${APY:-python3}" VPY="${VPY:-python3}" TMPW="$T" "$@" bash "$T/kit/install_S864_ONE_STATEMENT.sh" 2>&1); }
und() { (ROOT="$T/root" LOCK="$T/root/deploy/lock" SYSTEMCTL="$T/sysctl.sh" HEALTH_CMD="$T/hz.sh" NAP=0 bash "$T/kit/undo_s864.sh" 2>&1); }
at_from() { for f in purchase_app.py month_asks.py amir_day.py export_watch.py; do [ "$(m5 "$T/root/finance/$f")" = "$(m5 "$LIVE/$f")" ] || return 1; done; }
at_to() { for f in purchase_app.py month_asks.py amir_day.py export_watch.py; do [ "$(m5 "$T/root/finance/$f")" = "$(to "$f")" ] || return 1; done; }
FROM="${REH_FROM:-1}"            # REH_FROM=7: start at R7 (the device VM reaps a background run past ~5 min; the server runs it whole)
setup
[ "$FROM" -le 6 ] && {
o=$(run env DRY=1);echo "$o" | tail -2 | sed 's/^/   /'
echo "$o" | grep -q "DRY RUN: every gate and walk green; NOTHING written" && at_from; ok $? "R1 dry: every gate and walk green, nothing written"
o=$(run env REHEARSE_RED_AT=4); echo "$o" | grep -q "RED after placing" && at_from; ok $? "R2 a forced red at [4/5]: every file back at FROM"
true
o=$(run env); echo "$o" | tail -1 | sed 's/^/   /'; echo "$o" | grep -q "S864_ONE_STATEMENT: DONE" && at_to; ok $? "R3 install: DONE, four files at TO; the one-off ran on the made-up root ($(echo "$o" | grep -o "S864 ONE-OFF: [^;]*"))"
o=$(run env); echo "$o" | grep -q "ALREADY INSTALLED"; ok $? "R4 again: ALREADY INSTALLED, nothing done"
o=$(und); echo "$o" | grep -q "S864 UNDONE" && at_from; ok $? "R5 undo: back at FROM"
o=$(und); echo "$o" | grep -q "nothing undone"; ok $? "R6 undo again: refused, nothing undone"
}
true "$T"/root/finance/*.bak_S864_*
echo 500 > "$T/page_code"; o=$(run env); echo "$o" | grep -q "the purchase check answered 500" && at_from; ok $? "R7 the page answering 500 after the restart: rolled back"
echo 302 > "$T/page_code"; true "$T"/root/finance/*.bak_S864_*
echo "#" >> "$T/kit/export_watch.py"; o=$(run env); echo "$o" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "R8 a tampered kit: refused at [1/5]"
setup; echo "# drift" >> "$T/root/finance/export_watch.py"; o=$(run env); echo "$o" | grep -q "expected f6845ec5 - STOP" ; ok $? "R9 a live file changed since: STOP at [2/5]"
setup; mkdir "$T/root/deploy/lock"; o=$(run env); [ "$(echo "$o" | grep -c 'another build holds the lock')" = 1 ] && at_from; ok $? "R10 a held lock: nothing installed"
rm -rf "$T"
echo "REHEARSE S864: $P PASS, $F FAIL"
