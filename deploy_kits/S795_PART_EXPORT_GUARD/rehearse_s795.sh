#!/bin/bash
# rehearse_s795.sh LIVE_purchase_app.py -- the installer on a MADE-UP root and a MADE-UP database (never /root). Last line: 'REHEARSAL S795 6/6'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; PY="${PY:-$(command -v python3)}"; R=/tmp/r795; OK=0
mkdb() { "$PY" - "$1" <<'P'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
c.executescript("CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT, file TEXT, period_from TEXT, period_to TEXT, export_stamp TEXT, received_at TEXT, n_rows INTEGER, grand_amount_p INTEGER, superseded_by TEXT);"
                "CREATE TABLE purchase_bill (id INTEGER PRIMARY KEY, month TEXT, bw_md5 TEXT, sw_md5 TEXT);CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);")
c.execute("INSERT INTO purchase_export VALUES ('full29','BILLWISE','','2026-11-01','2026-11-11','20261111-110400','',29,0,'part4')")
c.execute("INSERT INTO purchase_export VALUES ('part4','BILLWISE','','2026-11-01','2026-11-11','20261111-110415','',4,0,NULL)")
c.executemany("INSERT INTO purchase_bill (month,bw_md5) VALUES ('2026-11',?)", [("full29",)] * 25 + [("part4",)] * 4)
c.execute("INSERT INTO setting VALUES ('purchase.rematch_seen','x','')"); c.commit()
P
}
mk() { rm -rf "${R:?}"; mkdir -p "$R/root/finance" "$R/tmp"; \cp -p "$LIVE" "$R/root/finance/purchase_app.py"; mkdb "$R/root/finance/finance.db"; }
eff() { "$PY" -c "import sqlite3,sys;print(sqlite3.connect(sys.argv[1]).execute(\"SELECT COUNT(*) FROM purchase_bill b WHERE EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL AND e.md5=b.bw_md5)\").fetchone()[0])" "$R/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$R.health"; printf '#!/bin/bash\necho "$@" >> /tmp/r795.sysctl\n' > "$R.sys"; chmod +x "$R.health" "$R.sys"
run() { env ROOT="$R/root" LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" NAP=0 HEALTH_CMD="$R.health" SYSTEMCTL="$R.sys" "$@" bash "$KDIR/install_S795_PART_EXPORT_GUARD.sh" 2>&1; }
pin() { md5sum "$R/root/finance/purchase_app.py" | cut -c1-8; }
TOP="$(awk '{print substr($1,1,8)}' "$KDIR/TO_PINS.md5")"
mk; O=$(run DRY=1); echo "$O" | grep -q "DRY RUN: every gate" && [ "$(pin)" = 54d27cd3 ] && [ "$(eff)" = 4 ] && { echo "GREEN 1 dry: nothing written"; OK=$((OK+1)); } || { echo "RED 1"; echo "$O" | tail -4; }
mk; echo "# a change" >> "$R/root/finance/purchase_app.py"; O=$(run); echo "$O" | grep -q "\[2/5\].*changed after this kit" && [ ! -d "$R/lock" ] && [ "$(eff)" = 4 ] && { echo "GREEN 2 a changed file: stop, nothing installed"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }
mk; rm -f /tmp/r795.sysctl; O=$(run); echo "$O" | grep -q "S795_PART_EXPORT_GUARD: DONE" && [ "$(pin)" = "$TOP" ] && [ -f "$R/root/finance/purchase_app.py.bak_S795_54d27cd3" ] && [ ! -d "$R/lock" ] && [ "$(eff)" = 29 ] && grep -q "restart clinic-finance" /tmp/r795.sysctl && ls "$R"/root/finance/s795_repair_before_*.json >/dev/null 2>&1 && { echo "GREEN 3 the install: placed, restarted, 29 effective, before-state saved"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -6; }
O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && echo "$O" | grep -q "nothing to put right" && [ "$(eff)" = 29 ] && { echo "GREEN 4 again: nothing more"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -4; }
mk; O=$(run REHEARSE_RED_AT=4); echo "$O" | grep -q "RED after placing" && [ "$(pin)" = 54d27cd3 ] && [ ! -d "$R/lock" ] && [ "$(eff)" = 4 ] && { echo "GREEN 5 a red at [4/5]: the file put back, the database untouched"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -4; }
mk; mkdir -p "$R/lock"; echo "another" > "$R/lock/owner"; O=$(run); echo "$O" | grep -q "another build holds the lock" && [ "$(pin)" = 54d27cd3 ] && [ -f "$R/lock/owner" ] && { echo "GREEN 6 the lock held by another: nothing installed, their lock left"; OK=$((OK+1)); } || { echo "RED 6"; echo "$O" | tail -4; }
rm -rf "${R:?}" "$R.health" "$R.sys" /tmp/r795.sysctl
echo "REHEARSAL S795 $OK/6"
