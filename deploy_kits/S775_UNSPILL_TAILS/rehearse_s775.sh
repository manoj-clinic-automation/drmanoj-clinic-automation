#!/bin/bash
# rehearse_s775.sh LIVE_DIR -- the installer on a MADE-UP root (never /root): dry / a changed file / install / again / a red at [6/6].
# LIVE_DIR holds copies of purchase_app.py (S773), purchase_unspill.py (v1.0) and purchase_schema.sql. Last line: 'REHEARSAL S775 5/5'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"
PY="${PY:-$(command -v python3)}"
R=/tmp/r775; OK=0
mk() { rm -rf "$R"; mkdir -p "$R/root/finance" "$R/root/shared" "$R/tmp"; \cp -p "$LIVE/purchase_app.py" "$LIVE/purchase_unspill.py" "$LIVE/purchase_schema.sql" "$R/root/finance/";
       "$PY" - "$R/root/finance" <<'P'
import sqlite3, sys
d = sys.argv[1]
c = sqlite3.connect(d + "/finance.db")
c.executescript(open(d + "/purchase_schema.sql").read())
c.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows) VALUES ('b1','BILLWISE','x','2026-10-01','2026-10-31','20261101-090000','x',1)")
c.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows) VALUES ('i1','ITEMWISE','x','2026-10-01','2026-10-31','20261101-090100','x',1)")
c.execute("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,month,amount_p,bw_md5) VALUES ('GUNINA PHARMACEUTICALS PVT LTD','GUNINA PHARMACEUTICALS PVT LTD','GPPL2678591','2026-10-05','2026-10',251300,'b1')")
c.execute("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,qty,direction,source_md5,line_type) VALUES ('GUNINA PHARMACEUTICALS PVT LTD','L2678591',NULL,NULL,'LEFUMED 20MG TAB',1,'PURCHASE','i1','ITEMWISE')")
c.execute("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,qty,direction,source_md5,line_type) VALUES ('YUVIKA SURGICALS','YS0706202627','2026-10-07','2026-10','CAST SHOE M TYNOR',1,'PURCHASE','i1','ITEMWISE')")
c.execute("CREATE TABLE purchase_unspill_log (line_id INTEGER PRIMARY KEY, old_item TEXT NOT NULL, old_bill_no TEXT, old_bill_date TEXT, old_month TEXT, new_item TEXT NOT NULL, bill_id INTEGER NOT NULL, at TEXT NOT NULL, by_who TEXT)")
c.execute("INSERT INTO purchase_unspill_log VALUES (2,'06202627CAST SHOE M TYNOR',NULL,NULL,NULL,'CAST SHOE M TYNOR',9,'2026-11-10T00:00:01','S773 install')")
c.commit()
P
}
cat > "$R.sysctl" <<'E'
#!/bin/bash
exit 0
E
chmod +x "$R.sysctl"
cat > "$R.health" <<'E'
#!/bin/bash
[ "${2:-}" = route ] && { echo 401; exit 0; }; echo 200
E
chmod +x "$R.health"
run() { env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL=/nonexistent HEALTH_CMD="$R.health" \
          REHEARSE_PROOF=skip "$@" bash "$KDIR/install_S775_UNSPILL_TAILS.sh" 2>&1; }
pins() { printf '%s ' "$(md5sum "$R/root/finance/purchase_unspill.py" 2>/dev/null | cut -c1-8)"; }
joined() { "$PY" -c "import sqlite3; c=sqlite3.connect('$R/root/finance/finance.db'); print(c.execute(\"SELECT COUNT(*) FROM purchase_line WHERE bill_no='GPPL2678591' AND bill_date='2026-10-05'\").fetchone()[0], c.execute(\"SELECT COUNT(*) FROM purchase_line WHERE bill_no='YS0706202627'\").fetchone()[0])"; }

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "3c12a4cc " ] && [ "$(joined)" = "0 1" ] && { echo "GREEN 1 dry: green, nothing written"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -5; echo "pins: $P"; }

mk; echo "# a change" >> "$R/root/finance/purchase_unspill.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
TOP=$(awk '{printf "%s ", substr($1,1,8)}' "$KDIR/TO_PINS.md5")
echo "$O" | grep -q "S775_UNSPILL_TAILS: DONE" && [ "$P" = "$TOP" ] && ls "$R/root/finance/"purchase_unspill.py.bak_S775_* >/dev/null 2>&1 && [ ! -d "$R/lock" ] && [ "$(joined)" = "1 1" ] \
  && { echo "GREEN 3 install: the module at TO, the backup, the tail line joined, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; echo "pins $P / $TOP"; }

O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "3c12a4cc " ] && [ "$(joined)" = "0 1" ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [6/6]: v1.0 put back, only what this install joined undone (S773's join kept), lock released"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -6; echo "pins: $P"; }
rm -rf "$R" "$R.sysctl" "$R.health"
echo "REHEARSAL S775 $OK/5"
