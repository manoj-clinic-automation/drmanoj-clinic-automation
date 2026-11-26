#!/bin/bash
# rehearse_s964.sh -- S964 on a MADE-UP root: dry . red@4 . install (the refused record cleared, another kept) . again . undo . wrong FROM
#    bash rehearse_s964.sh KIT_DIR LIVE_MARG_INGEST_DIR S963_KIT_DIR
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; S3="$(cd "$3" && pwd)"; W="$(mktemp -d /tmp/reh_s964_XXXX)"; PASS=0; N=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root/marg_ingest/lib" "$W/root/finance"; cp -p "$F"/*.py "$F"/*.json "$W/root/marg_ingest/" 2>/dev/null
  cp -p "$F"/lib/*.py "$W/root/marg_ingest/lib/" 2>/dev/null; [ ! -d "$F/xlrd" ] || cp -rp "$F/xlrd" "$W/root/marg_ingest/xlrd"
  python3 - "$W/root/finance/finance.db" <<'P'
import sqlite3,sys
c=sqlite3.connect(sys.argv[1])
c.execute("CREATE TABLE mi_file (md5 TEXT PRIMARY KEY, type TEXT, verdict TEXT, kept INT)")
c.execute("CREATE TABLE mi_voucher_file (md5 TEXT PRIMARY KEY, ok INT, note TEXT)")
for m,t,k,o,n in (("a"*32,"STOCK_VOUCHERS",0,0,"not read: row 38: a cell not of its column's shape (item, packing, batch, unit or expiry)"),
                  ("b"*32,"STOCK_VOUCHERS",0,0,"not read: row 9: the party cell is not 'cash' or 'party' -- a name may have come through; nothing kept"),
                  ("c"*32,"STOCK_VOUCHERS",1,1,"")):
    c.execute("INSERT INTO mi_file VALUES (?,?,?,?)",(m,t,"VERIFIED",k)); c.execute("INSERT INTO mi_voucher_file VALUES (?,?,?)",(m,o,n))
c.commit()
P
}
printf '#!/bin/bash\necho 200\n' > "$W/hz"; chmod +x "$W/hz"
run() { (export ROOT="$W/root" DB="$W/root/finance/finance.db" LOCK="$W/build.lock" MLOCK="$W/mi.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" NAP=0 \
  APY=python3 VPY="${VPY:-python3}" TMPW="$W" S963K="$S3"; "$@"); }
FROM=7bc3df848ff4a8fdb5ba6d978d4496c0; TO=$(awk '{print $1}' "$K/TO_PINS.md5"); L="$W/root/marg_ingest/marg_vouchers.py"; I="$K/install_S964_VOUCHER_NAME_SHAPE.sh"
rows() { python3 -c "import sqlite3,sys;print(sqlite3.connect(sys.argv[1]).execute('SELECT COUNT(*) FROM mi_voucher_file').fetchone()[0])" "$W/root/finance/finance.db"; }
fresh; O=$(run env DRY=1 bash "$I" 2>&1); echo "$O" | tail -2 | sed 's/^/      /'; echo "$O" | grep -q "DRY RUN: every gate" && [ "$(m5 "$L")" = "$FROM" ] && [ "$(rows)" = 3 ]; ok $? "dry: green, nothing written"
fresh; O=$(run env REHEARSE_RED_AT=4 bash "$I" 2>&1); echo "$O" | grep -q "forced red at \[4/5\]" && [ "$(m5 "$L")" = "$FROM" ] && [ "$(rows)" = 3 ]; ok $? "red at [4/5]: the S963 reader back, no record touched"
fresh; O=$(run bash "$I" 2>&1); echo "$O" | tail -3 | sed 's/^/      /'; echo "$O" | grep -q "cleared 1 refused" && [ "$(m5 "$L")" = "$TO" ] && [ "$(rows)" = 2 ]; ok $? "install: the new reader; exactly the shape-refused record cleared, the name-refused and the sound kept"
O=$(run bash "$I" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED"; ok $? "again: ALREADY INSTALLED"
O=$(run bash "$K/undo_s964.sh" 2>&1); echo "$O" | grep -q "S964 UNDONE" && [ "$(m5 "$L")" = "$FROM" ]; ok $? "undo: the S963 reader back"
fresh; echo "# drift" >> "$L"; O=$(run bash "$I" 2>&1); echo "$O" | grep -q "\[2/5\].*changed after this kit was built" && [ "$(rows)" = 3 ]; ok $? "wrong FROM: stopped at [2/5], nothing touched"
rm -rf "$W"; echo "REHEARSAL $PASS/$N"
