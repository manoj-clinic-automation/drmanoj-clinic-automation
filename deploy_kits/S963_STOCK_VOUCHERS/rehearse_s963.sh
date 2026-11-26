#!/bin/bash
# rehearse_s963.sh -- S963_STOCK_VOUCHERS on a MADE-UP root (never the box): dry . red@4 . red@5 . install . again . undo . wrong FROM . lock.
#    bash rehearse_s963.sh KIT_DIR FROM_MARG_INGEST_DIR      (the second: the live /root/marg_ingest files, e.g. from the nightly bundle)
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; W="$(mktemp -d /tmp/reh_s963_XXXX)"; PASS=0; N=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root/marg_ingest/lib" "$W/root/finance"; cp -p "$F"/*.py "$F"/*.json "$W/root/marg_ingest/" 2>/dev/null
  rm -f "$W/root/marg_ingest/marg_vouchers.py"; cp -p "$F"/lib/*.py "$W/root/marg_ingest/lib/" 2>/dev/null
  [ ! -d "$F/xlrd" ] || cp -rp "$F/xlrd" "$W/root/marg_ingest/xlrd"
  python3 -c "import sqlite3,sys;sqlite3.connect(sys.argv[1]).execute('CREATE TABLE IF NOT EXISTS x(a)')" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; chmod +x "$W/hz"
run() { (export ROOT="$W/root" DB="$W/root/finance/finance.db" LOCK="$W/build.lock" MLOCK="$W/mi.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" NAP=0 \
  APY=python3 VPY="${VPY:-python3}" TMPW="$W"; "$@"); }
at_from() { for n in signatures.json marg_take.py marg_ingest.py; do [ "$(m5 "$W/root/marg_ingest/$n")" = "$(awk -v f="marg_ingest/$n" '$2==f{print $1}' "$K/FROM_PINS.md5")" ] || return 1; done; [ ! -e "$W/root/marg_ingest/marg_vouchers.py" ]; }
at_to() { for n in signatures.json marg_take.py marg_ingest.py marg_vouchers.py; do [ "$(m5 "$W/root/marg_ingest/$n")" = "$(awk -v f="marg_ingest/$n" '$2==f{print $1}' "$K/TO_PINS.md5")" ] || return 1; done; }
INST="$K/install_S963_STOCK_VOUCHERS.sh"

fresh; O=$(run env DRY=1 bash "$INST" 2>&1); echo "$O" | tail -2 | sed 's/^/      /'
echo "$O" | grep -q "DRY RUN: every gate" && at_from; ok $? "dry: every gate, the walk and the control green; nothing written"
fresh; O=$(run env REHEARSE_RED_AT=4 bash "$INST" 2>&1); echo "$O" | grep -q "RED after placing (rehearsal: a forced red at \[4/6\])" && at_from; ok $? "red at [4/6]: the three files back, the new reader gone"
fresh; O=$(run env REHEARSE_RED_AT=5 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[5/6\]" && at_from; ok $? "red at [5/6]: the same"
fresh; O=$(run bash "$INST" 2>&1); echo "$O" | tail -3 | sed 's/^/      /'
echo "$O" | grep -q "S963_STOCK_VOUCHERS: DONE" && at_to && python3 -c "import sqlite3,sys;n=[r[0] for r in sqlite3.connect(sys.argv[1]).execute(\"SELECT name FROM sqlite_master WHERE name LIKE 'mi_voucher%'\")];sys.exit(0 if len(n)==5 else 1)" "$W/root/finance/finance.db"
ok $? "install: four files at their TO pins, the tables and views made"
for n in signatures.json marg_take.py marg_ingest.py; do [ -f "$W/root/marg_ingest/$n.bak_S963_$(awk -v f="marg_ingest/$n" '$2==f{print substr($1,1,8)}' "$K/FROM_PINS.md5")" ] || false; done; ok $? "install: the three backups kept at their FROM names"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED" && at_to; ok $? "again: ALREADY INSTALLED, nothing touched"
O=$(run bash "$K/undo_s963.sh" 2>&1); echo "$O" | grep -q "S963 UNDONE" && at_from; ok $? "undo: the three files back at FROM, the new reader gone"
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "DONE" && at_to; ok $? "install again after the undo"
fresh; echo "# drift" >> "$W/root/marg_ingest/marg_take.py"; B=$(m5 "$W/root/marg_ingest/marg_take.py")
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ "$(m5 "$W/root/marg_ingest/marg_take.py")" = "$B" ] && [ ! -e "$W/root/marg_ingest/marg_vouchers.py" ]
ok $? "wrong FROM (a live file changed): stopped at [2/6], nothing placed"
fresh; mkdir "$W/build.lock"; O=$(run bash "$INST" 2>&1); RC=$?; rmdir "$W/build.lock"; [ "$RC" = 3 ] && at_from; ok $? "another build holds the lock: exit 3, nothing placed"
fresh; O=$(run bash "$INST" 2>&1); echo "# a later kit" >> "$W/root/marg_ingest/marg_take.py"; B=$(m5 "$W/root/marg_ingest/marg_take.py")
O=$(run bash "$K/undo_s963.sh" 2>&1); echo "$O" | grep -q "a later change; nothing undone" && [ "$(m5 "$W/root/marg_ingest/marg_take.py")" = "$B" ] && [ -e "$W/root/marg_ingest/marg_vouchers.py" ]
ok $? "undo after a later change to a file: refused, nothing undone (cold review S5)"
fresh; cp "$K/SUMS.md5" "$W/sums.bak"; sed -i '1s/^./0/' "$K/SUMS.md5"; O=$(run bash "$INST" 2>&1); cp "$W/sums.bak" "$K/SUMS.md5"
echo "$O" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "a corrupt kit: refused at [1/6]"
rm -rf "$W"
echo "REHEARSAL $PASS/$N"
