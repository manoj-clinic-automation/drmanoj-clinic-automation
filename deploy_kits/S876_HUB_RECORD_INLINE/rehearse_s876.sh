#!/bin/bash
# rehearse_s876.sh <kit dir> <S874's files dir: finance_ui/finance_approvals.html + sanjeevni_day.py at their FROM pins> <a db copy> <deploy_kits dir>
# Runs the installer and the undo on a MADE-UP root in the build machine (stubs for systemctl and the health answers).
set -u
K="$1"; SRC="$2"; DBC="$3"; OK_="$4"; W="$(mktemp -d /tmp/s876rh.XXXX)"; P=0; F=0
res() { if [ "$1" = 0 ]; then P=$((P+1)); echo "  ok   $2"; else F=$((F+1)); echo "  FAIL $2"; fi; }
mkroot() { rm -rf "$W/root"; mkdir -p "$W/root/finance/finance_ui"; cp "$SRC/sanjeevni_day.py" "$W/root/finance/"; cp "$SRC/finance_ui/finance_approvals.html" "$W/root/finance/finance_ui/"; cp "$DBC" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\ncase "$1" in *patient-events*) echo "${DOOR:-302}";; *) echo 200;; esac\n' > "$W/hz2"; chmod +x "$W/hz" "$W/hz2"
printf '#!/bin/bash\necho "${JLINE:-started}"\n' > "$W/jr"; chmod +x "$W/jr"
export JOURNAL_CMD="$W/jr" ROOT="$W/root" SYSTEMCTL=true NAP=0 LOCK="$W/lock" APY=python3 VPY=python3 OLDK="$OK_" TMPW="$W" HEALTH_CMD="$W/hz2"
I="bash $K/install_S876_HUB_RECORD_INLINE.sh"; U="bash $K/undo_s876.sh"
pin() { md5sum "$W/root/finance/$1" 2>/dev/null | cut -c1-8; }
mkroot
O=$(DRY=1 $I 2>&1); echo "$O" | grep -q "DRY RUN: every gate" && [ ! -e "$W/root/finance/patient_events.py" ] && [ "$(pin sanjeevni_day.py)" = db30da9f ]; res $? "A1 dry run: proofs green, nothing written"
O=$(REHEARSE_RED_AT=4 $I 2>&1); echo "$O" | grep -q "RED after placing" && [ "$(pin sanjeevni_day.py)" = db30da9f ] && [ "$(pin finance_ui/finance_approvals.html)" = 254c0bbf ] && [ ! -e "$W/root/finance/patient_events.py" ] && [ ! -d "$W/lock" ]; res $? "A2 a red after placing puts both files back, takes the new one out, frees the lock"
O=$(DOOR=404 $I 2>&1); echo "$O" | grep -q "not mounted" && [ "$(pin sanjeevni_day.py)" = db30da9f ] && [ ! -e "$W/root/finance/patient_events.py" ]; res $? "A3 the door not mounted (404) rolls back (F-1439)"
O=$(JLINE="patient_events not mounted: boom" $I 2>&1); echo "$O" | grep -q "the service log says" && [ ! -e "$W/root/finance/patient_events.py" ] && [ "$(pin sanjeevni_day.py)" = db30da9f ]; res $? "A3b the service log saying 'not mounted' rolls back"
O=$($I 2>&1); echo "$O" | grep -q "S876_HUB_RECORD_INLINE: DONE" && [ "$(pin patient_events.py)" = "$(awk '$2=="finance/patient_events.py"{print substr($1,1,8)}' $K/TO_PINS.md5)" ]; res $? "A4 install: DONE, the new file at its pin (door 302 = mounted)"
echo "$O" | grep -E "^\[3/5\]" | sed 's/^/      /'
O=$($I 2>&1); echo "$O" | grep -q "ALREADY INSTALLED"; res $? "A5 again: already installed"
O=$($U 2>&1); echo "$O" | grep -q "S876 UNDONE" && [ "$(pin sanjeevni_day.py)" = db30da9f ] && [ "$(pin finance_ui/finance_approvals.html)" = 254c0bbf ] && [ ! -e "$W/root/finance/patient_events.py" ]; res $? "A6 undo: the FROM pins back, the new file out"
O=$($U 2>&1); echo "$O" | grep -q "NOT installed"; res $? "A7 undo again: nothing to undo"
echo "// tamper" >> "$W/root/finance/sanjeevni_day.py"; O=$($I 2>&1); echo "$O" | grep -q "changed after this kit was built" && [ ! -e "$W/root/finance/patient_events.py" ]; res $? "A8 a live file off its FROM pin: STOP"
mkroot; touch "$W/root/finance/patient_events.py"; O=$($I 2>&1); echo "$O" | grep -q "already exists and is not this kit's"; res $? "A9 a stray patient_events.py: STOP"
mkroot; mkdir "$W/lock"; O=$($I 2>&1); [ $? = 3 ] && echo "$O" | grep -q "another build holds the lock"; res $? "A10 the lock held: exit 3, nothing written"; rmdir "$W/lock"
cp -rp "$K" "$W/kc"; echo x >> "$W/kc/patient_events.py"; O=$(bash "$W/kc/install_S876_HUB_RECORD_INLINE.sh" 2>&1); echo "$O" | grep -q "SUMS.md5 gate failed"; res $? "A11 a corrupt kit: SUMS gate stops it"
rm -rf "$W"; echo "rehearse S876: $P ok, $F failed"; [ "$F" = 0 ]
