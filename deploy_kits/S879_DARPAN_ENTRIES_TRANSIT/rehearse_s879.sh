#!/bin/bash
# rehearse_s879.sh <kit dir> <a finance dir at the live pins (all modules)> <a db copy> <deploy_kits dir>
# The installer and the undo on a MADE-UP root in the build machine (stubs for systemctl and the health answers).
set -u
K="$1"; SRC="$2"; DBC="$3"; OK_="$4"; W="$(mktemp -d /tmp/s879rh.XXXX)"; P=0; F=0
res() { if [ "$1" = 0 ]; then P=$((P+1)); echo "  ok   $2"; else F=$((F+1)); echo "  FAIL $2"; fi; }
mkroot() { rm -rf "$W/root"; mkdir -p "$W/root"; cp -rp "$SRC" "$W/root/finance"; cp "$DBC" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\ncase "$1" in *darpan*) echo "${DOOR:-302}";; *) echo 200;; esac\n' > "$W/hz"; chmod +x "$W/hz"
export ROOT="$W/root" SYSTEMCTL=true NAP=0 LOCK="$W/lock" APY=python3 VPY=python3 OLDK="$OK_" TMPW="$W" HEALTH_CMD="$W/hz"
I="bash $K/install_S879_DARPAN_ENTRIES_TRANSIT.sh"; U="bash $K/undo_s879.sh"
pin() { md5sum "$W/root/finance/$1" 2>/dev/null | cut -c1-8; }
atfrom() { [ "$(pin darpan_kal.py)" = d27ed062 ] && [ "$(pin darpan_kal.html)" = b7d2d61e ] && [ "$(pin purchase_app.py)" = c15bc1c5 ]; }
mkroot
O=$(DRY=1 $I 2>&1); echo "$O" | grep -q "DRY RUN: every gate" && atfrom; res $? "A1 dry run: proofs green, nothing written"
echo "$O" | grep -E "^\[3/5\]|FAIL|!!" | sed 's/^/      /'
O=$(REHEARSE_RED_AT=4 $I 2>&1); echo "$O" | grep -q "RED after placing" && atfrom && [ ! -d "$W/lock" ]; res $? "A2 a red after placing puts all three back, frees the lock"
O=$(DOOR=404 $I 2>&1); echo "$O" | grep -q "door answers 404" && atfrom; res $? "A3 Darpan's door not answering rolls back"
O=$($I 2>&1); echo "$O" | grep -q "S879_DARPAN_ENTRIES_TRANSIT: DONE" && [ "$(pin darpan_kal.py)" = "$(awk '$2=="finance/darpan_kal.py"{print substr($1,1,8)}' $K/TO_PINS.md5)" ]; res $? "A4 install: DONE at the TO pins"
O=$($I 2>&1); echo "$O" | grep -q "ALREADY INSTALLED"; res $? "A5 again: already installed"
O=$($U 2>&1); echo "$O" | grep -q "S879 UNDONE" && atfrom; res $? "A6 undo: the FROM pins back"
O=$($U 2>&1); echo "$O" | grep -q "NOT installed"; res $? "A7 undo again: nothing to undo"
echo "// tamper" >> "$W/root/finance/darpan_kal.py"; O=$($I 2>&1); echo "$O" | grep -q "changed after this kit was built"; res $? "A8 a live file off its FROM pin: STOP"
mkroot; mkdir "$W/lock"; O=$($I 2>&1); [ $? = 3 ] && echo "$O" | grep -q "another build holds the lock" && atfrom; res $? "A9 the lock held: exit 3, nothing written"; rmdir "$W/lock"
cp -rp "$K" "$W/kc"; echo x >> "$W/kc/make_s879.py"; O=$(bash "$W/kc/install_S879_DARPAN_ENTRIES_TRANSIT.sh" 2>&1); echo "$O" | grep -q "SUMS.md5 gate failed"; res $? "A10 a corrupt kit: SUMS gate stops it"
rm -rf "$W"; echo "rehearse S879: $P ok, $F failed"; [ "$F" = 0 ]
