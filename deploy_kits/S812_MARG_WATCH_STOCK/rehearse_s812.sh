#!/bin/bash
# rehearse_s812.sh -- kit S812's installer on a STAND-IN root (never /root): dry, a changed live file, install, again, the undo line, a red after
# placing, a kit file altered. Needs: STAND=<a folder holding finance/ (the live bytes of the two files, finance.db, spine/spine.db), shared/>.
set -u
K="$(cd "$(dirname "$0")" && pwd)"; STAND="${STAND:?}"; PASSN=0; TOTAL=0
m5() { md5sum "$1" | awk '{print $1}'; }
fresh() { rm -rf /tmp/s812r && mkdir -p /tmp/s812r && cp -rp "$STAND"/. /tmp/s812r/ && rm -rf /tmp/s812k && cp -rp "$K" /tmp/s812k; }
run() { (export ROOT=/tmp/s812r LOCK=/tmp/s812r/.lock SYSTEMCTL=true HEALTH_CMD="$K/hz.sh" NAP=0 TMPW=/tmp VPY="${VPY:-python3}" APY="${APY:-python3}"; bash /tmp/s812k/install_S812_MARG_WATCH_STOCK.sh) 2>&1; }
t() { TOTAL=$((TOTAL+1)); if [ "$2" = 1 ]; then PASSN=$((PASSN+1)); echo "ok   $1"; else echo "RED  $1"; fi; }
H0=$(m5 "$STAND/finance/marg_hand_change.py"); W0=$(m5 "$STAND/finance/marg_billwatch.py")
fresh; O=$(DRY=1 run); t "dry: every gate green, nothing written" $([ "$(m5 /tmp/s812r/finance/marg_hand_change.py)" = "$H0" ] && echo "$O" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
fresh; echo "# x" >> /tmp/s812r/finance/marg_billwatch.py; O=$(run); t "a live file not the pinned one -> stopped" $(echo "$O" | grep -q "changed after this kit was built" && echo 1 || echo 0)
fresh; O=$(run); t "install: DONE, both at their TO pins" $(echo "$O" | grep -q "S812_MARG_WATCH_STOCK: DONE" && [ "$(m5 /tmp/s812r/finance/marg_hand_change.py)" = "$(awk 'NR==1{print $1}' $K/TO_PINS.md5)" ] && echo 1 || echo 0)
echo "$O" | grep -E "^\[|counted|newer" | sed 's/^/      /'
O2=$(run); t "again: ALREADY INSTALLED" $(echo "$O2" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
U=$(echo "$O" | grep "undo (one line)" | sed 's/.*(one line): //'); eval "$(echo "$U" | sed 's/ && true restart.*//; s/ && true$//')"
t "the undo line puts both back byte-identical" $([ "$(m5 /tmp/s812r/finance/marg_hand_change.py)" = "$H0" ] && [ "$(m5 /tmp/s812r/finance/marg_billwatch.py)" = "$W0" ] && echo 1 || echo 0)
t "... and first marks every explained move as history (the old notice never tells it)" $(python3 -c "import sqlite3;c=sqlite3.connect('/tmp/s812r/finance/finance.db');print(c.execute('SELECT COUNT(*) FROM marg_hand_change WHERE rec_kind IS NOT NULL AND hist=0').fetchone()[0])" | grep -qx 0 && echo 1 || echo 0)
fresh; O=$(REHEARSE_RED_AT=4 run); t "a red after placing -> both files back" $(echo "$O" | grep -q "RED after placing" && [ "$(m5 /tmp/s812r/finance/marg_hand_change.py)" = "$H0" ] && [ "$(m5 /tmp/s812r/finance/marg_billwatch.py)" = "$W0" ] && echo 1 || echo 0)
fresh; echo "#" >> /tmp/s812k/seg_compute.py; O=$( (export ROOT=/tmp/s812r LOCK=/tmp/s812r/.lock SYSTEMCTL=true HEALTH_CMD="$K/hz.sh" NAP=0; bash /tmp/s812k/install_S812_MARG_WATCH_STOCK.sh) 2>&1); t "a kit file altered -> stopped" $(echo "$O" | grep -q "SUMS.md5 gate failed" && echo 1 || echo 0)
rm -rf /tmp/s812r /tmp/s812k
echo "REHEARSAL $PASSN/$TOTAL"
