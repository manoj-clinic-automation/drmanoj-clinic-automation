#!/bin/bash
# rehearse_s773.sh LIVE_DIR -- the installer on a MADE-UP root (never /root): dry / a changed file / install / again / a red at [6/6].
# LIVE_DIR holds copies of purchase_app.py and purchase_schema.sql. Last line: 'REHEARSAL S773 5/5' when all five behave.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"
PY="${PY:-$(command -v python3)}"
R=/tmp/r773; OK=0
mk() { rm -rf "$R"; mkdir -p "$R/root/finance" "$R/root/shared" "$R/tmp"; \cp -p "$LIVE/purchase_app.py" "$LIVE/purchase_schema.sql" "$R/root/finance/";
       "$PY" - "$R/root/finance" <<'P'
import sqlite3, sys
d = sys.argv[1]
c = sqlite3.connect(d + "/finance.db")
c.executescript(open(d + "/purchase_schema.sql").read())
c.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows) VALUES ('b1','BILLWISE','x','2026-10-01','2026-10-31','20261101-090000','x',1)")
c.execute("INSERT INTO purchase_export (md5,type,file,period_from,period_to,export_stamp,received_at,n_rows) VALUES ('i1','ITEMWISE','x','2026-10-01','2026-10-31','20261101-090100','x',1)")
c.execute("INSERT INTO purchase_bill (supplier_norm,supplier,bill_no,bill_date,month,amount_p,bw_md5) VALUES ('YUVIKA SURGICALS','YUVIKA SURGICALS','YS0706202627','2026-10-07','2026-10',57400,'b1')")
c.execute("INSERT INTO purchase_line (supplier_norm,bill_no,bill_date,month,item,qty,direction,source_md5,line_type) VALUES ('YUVIKA SURGICALS',NULL,NULL,NULL,'06202627CAST SHOE M TYNOR',1,'PURCHASE','i1','ITEMWISE')")
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
          REHEARSE_PROOF=skip "$@" bash "$KDIR/install_S773_UNSPILL_BILLS.sh" 2>&1; }
pins() { printf '%s %s ' "$(md5sum "$R/root/finance/purchase_app.py" 2>/dev/null | cut -c1-8)" "$( [ -e "$R/root/finance/purchase_unspill.py" ] && md5sum "$R/root/finance/purchase_unspill.py" | cut -c1-8 || echo none)"; }
joined() { "$PY" -c "import sqlite3; print(sqlite3.connect('$R/root/finance/finance.db').execute(\"SELECT COUNT(*) FROM purchase_line WHERE bill_no='YS0706202627' AND item='CAST SHOE M TYNOR'\").fetchone()[0])"; }

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "8424e05b none " ] && [ "$(joined)" = 0 ] && { echo "GREEN 1 dry: green, nothing written"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -5; echo "pins: $P"; }

mk; echo "# a change" >> "$R/root/finance/purchase_app.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ ! -e "$R/root/finance/purchase_unspill.py" ] && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
TOP=$(awk '{printf "%s ", substr($1,1,8)}' "$KDIR/TO_PINS.md5")
echo "$O" | grep -q "S773_UNSPILL_BILLS: DONE" && [ "$P" = "$TOP" ] && ls "$R/root/finance/"purchase_app.py.bak_S773_* >/dev/null 2>&1 && [ ! -d "$R/lock" ] && [ "$(joined)" = 1 ] \
  && { echo "GREEN 3 install: both files at TO, the backup, the stored line joined to its bill, lock released"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -8; echo "pins $P / $TOP"; }

O=$(run); echo "$O" | grep -q "ALREADY INSTALLED" && { echo "GREEN 4 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -3; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "8424e05b none " ] && [ "$(joined)" = 0 ] && [ ! -d "$R/lock" ] && { echo "GREEN 5 a red at [6/6]: the file put back, the new one removed, the line as it came, lock released"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O" | tail -6; echo "pins: $P"; }
rm -rf "$R" "$R.sysctl" "$R.health"
echo "REHEARSAL S773 $OK/5"
