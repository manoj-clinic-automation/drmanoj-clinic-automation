#!/bin/bash
# rehearse_s914.sh · kit S914: the installer and the undo on a MADE-UP root (stub systemctl, stub healthz and door; the live files'
# code copied in; no database).  bash rehearse_s914.sh <folder holding the two FROM files>     -> last line 'rehearse_s914: N/N'
set -u
KSRC="$(cd "$(dirname "$0")" && pwd)"; FROMD="$1"
T="$(mktemp -d /tmp/s914_reh_XXXX)"; R="$T/root"; K="$T/kit"; PASS=0; N=0
m5() { md5sum "$1" | awk '{print $1}'; }
fresh() { rm -rf "$R" "$K"; mkdir -p "$R/finance" "$T/lockdir"; cp -p "$FROMD/supplier_msg.py" "$FROMD/porders_s454.py" "$R/finance/"; cp -rp "$KSRC" "$K"; echo 200 > "$T/hz"; echo 302 > "$T/dz"; rmdir "$T/lockdir/l" 2>/dev/null; true; }
printf '#!/bin/bash\ncat %s/hz\n' "$T" > "$T/health.sh"; printf '#!/bin/bash\ncat %s/dz\n' "$T" > "$T/door.sh"; chmod +x "$T/health.sh" "$T/door.sh"
export ROOT="$R" SYSTEMCTL=true HEALTH_CMD="$T/health.sh" DOOR_CMD="$T/door.sh" NAP=0 LOCK="$T/lockdir/l" APY="${APY:-python3}" VPY="${VPY:-python3}" TMPW="$T"
F0=$(m5 "$FROMD/supplier_msg.py"); F1=$(m5 "$FROMD/porders_s454.py")
T0=$(awk '$2=="finance/supplier_msg.py"{print $1}' "$KSRC/TO_PINS.md5"); T1=$(awk '$2=="finance/porders_s454.py"{print $1}' "$KSRC/TO_PINS.md5")
at() { [ "$(m5 "$R/finance/supplier_msg.py")" = "$1" ] && [ "$(m5 "$R/finance/porders_s454.py")" = "$2" ]; }
chk() { N=$((N+1)); if eval "$2"; then PASS=$((PASS+1)); echo "ok   $1"; else echo "RED  $1"; echo "$OUT" | tail -4 | sed 's/^/     /'; fi; }
run() { OUT=$(bash "$K/install_S914_PHONE_SETUP_PAGE.sh" 2>&1); RC=$?; }
undo() { OUT=$(bash "$K/undo_s914.sh" 2>&1); RC=$?; }

fresh; OUT=$(DRY=1 bash "$K/install_S914_PHONE_SETUP_PAGE.sh" 2>&1); RC=$?
chk "A dry run: green, nothing written" '[ $RC = 0 ] && echo "$OUT" | grep -q "DRY RUN: every gate and the walk green" && at $F0 $F1'
run; chk "B install: DONE, both at TO, backups there" '[ $RC = 0 ] && echo "$OUT" | grep -q "S914_PHONE_SETUP_PAGE: DONE" && at $T0 $T1 && [ -f "$R/finance/supplier_msg.py.bak_S914_${F0:0:8}" ]'
run; chk "C again: ALREADY INSTALLED" '[ $RC = 0 ] && echo "$OUT" | grep -q "ALREADY INSTALLED" && at $T0 $T1'
undo; chk "D undo: both back at FROM" '[ $RC = 0 ] && at $F0 $F1 && echo "$OUT" | grep -q "back to"'
undo; chk "E undo again: already at FROM, nothing restarted" '[ $RC = 0 ] && at $F0 $F1 && ! echo "$OUT" | grep -q "restarted"'
fresh; OUT=$(REHEARSE_RED_AT=4 bash "$K/install_S914_PHONE_SETUP_PAGE.sh" 2>&1); RC=$?
chk "F forced red at [4/5]: everything put back" '[ $RC = 1 ] && echo "$OUT" | grep -q "putting everything back" && at $F0 $F1'
fresh; echo "# tamper" >> "$K/supplier_msg.py"; run
chk "G a changed kit file: SUMS gate, nothing installed" '[ $RC = 1 ] && echo "$OUT" | grep -q "SUMS.md5 gate failed" && at $F0 $F1'
fresh; echo "# someone else" >> "$R/finance/porders_s454.py"; run
chk "H a live file moved since the build: STOP at [2/5], untouched" '[ $RC = 1 ] && echo "$OUT" | grep -q "\[2/5\]" && [ "$(m5 "$R/finance/supplier_msg.py")" = $F0 ]'
fresh; mkdir -p "$LOCK"; run; rmdir "$LOCK"
chk "I the build lock held: nothing installed, exit 3" '[ $RC = 3 ] && at $F0 $F1'
fresh; echo 404 > "$T/dz"; run
chk "J the page not mounted (404): put back" '[ $RC = 1 ] && echo "$OUT" | grep -q "not mounted" && at $F0 $F1'
fresh; echo 302 > "$T/dz"; printf '#!/bin/bash\nif [ -f %s/root/finance/.placed ]; then echo 500; else cat %s/hz; fi\n' "$T" "$T" > "$T/health.sh"
printf '#!/bin/bash\ntouch %s/root/finance/.placed\n' "$T" > "$T/sysctl.sh"; chmod +x "$T/sysctl.sh"
OUT=$(SYSTEMCTL="$T/sysctl.sh" bash "$K/install_S914_PHONE_SETUP_PAGE.sh" 2>&1); RC=$?
chk "K healthz 500 after the restart: put back" '[ $RC = 1 ] && echo "$OUT" | grep -q "after the restart" && at $F0 $F1'
printf '#!/bin/bash\ncat %s/hz\n' "$T" > "$T/health.sh"; rm -f "$R/finance/.placed"
fresh; run; echo "# hand edit" >> "$R/finance/supplier_msg.py"; undo
chk "L undo on a hand-edited file: left as it is, said" 'echo "$OUT" | grep -q "neither the kit" && ! at $F0 $F1'
leak=$(ls "$T" | grep -c '^s914_inst_' || true)
chk "M no scratch left behind" '[ "$leak" = 0 ]'
rm -rf "$T"
echo "rehearse_s914: $PASS/$N"
