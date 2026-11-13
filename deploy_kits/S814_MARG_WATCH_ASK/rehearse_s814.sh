#!/bin/bash
# rehearse_s814.sh -- kit S814's installer on a STAND-IN root (never /root): dry, a changed live file, the lock held, install, again, the undo
# line, a red after placing (at 4 and at 5), a kit file altered. Needs STAND=<a folder holding finance/ (the live bytes of the three files, every
# other finance file, finance.db, spine/spine.db), shared/>. VPY = a python with flask.
set -u
K="$(cd "$(dirname "$0")" && pwd)"; STAND="${STAND:?}"; PASSN=0; TOTAL=0
m5() { md5sum "$1" | awk '{print $1}'; }
fresh() { rm -rf /tmp/s814r && mkdir -p /tmp/s814r && cp -rp "$STAND"/. /tmp/s814r/ && rm -rf /tmp/s814k && cp -rp "$K" /tmp/s814k; }
run() { (export ROOT=/tmp/s814r LOCK=/tmp/s814r/.lock SYSTEMCTL=true HEALTH_CMD="$K/hz.sh" NAP=0 TMPW=/tmp VPY="${VPY:-python3}" APY="${APY:-python3}"; bash /tmp/s814k/install_S814_MARG_WATCH_ASK.sh) 2>&1; }
t() { TOTAL=$((TOTAL+1)); if [ "$2" = 1 ]; then PASSN=$((PASSN+1)); echo "ok   $1"; else echo "RED  $1"; fi; }
same3() { [ "$(m5 /tmp/s814r/finance/amir_day.py)" = "$A0" ] && [ "$(m5 /tmp/s814r/finance/marg_billwatch.py)" = "$W0" ] && [ "$(m5 /tmp/s814r/finance/owner_notice.py)" = "$N0" ]; }
A0=$(m5 "$STAND/finance/amir_day.py"); W0=$(m5 "$STAND/finance/marg_billwatch.py"); N0=$(m5 "$STAND/finance/owner_notice.py")
fresh; O=$(DRY=1 run); t "dry: every gate green, nothing written" $(same3 && echo "$O" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
echo "$O" | grep -E "^\[3/7\]|^!!|^      " | sed 's/^/      /'
fresh; echo "# x" >> /tmp/s814r/finance/owner_notice.py; O=$(run); t "a live file not the pinned one -> stopped, nothing placed" $(echo "$O" | grep -q "changed after this kit was built" && [ "$(m5 /tmp/s814r/finance/amir_day.py)" = "$A0" ] && echo 1 || echo 0)
fresh; mkdir /tmp/s814r/.lock; O=$(run); t "another build holds the lock -> nothing installed" $(echo "$O" | grep -q "another build holds the lock" && same3 && echo 1 || echo 0)
fresh; O=$(run); t "install: DONE, all three at their TO pins" $(echo "$O" | grep -q "S814_MARG_WATCH_ASK: DONE" && [ "$(m5 /tmp/s814r/finance/amir_day.py)" = "$(awk '$2=="finance/amir_day.py"{print $1}' $K/TO_PINS.md5)" ] && [ "$(m5 /tmp/s814r/finance/marg_billwatch.py)" = "$(awk '$2=="finance/marg_billwatch.py"{print $1}' $K/TO_PINS.md5)" ] && [ "$(m5 /tmp/s814r/finance/owner_notice.py)" = "$(awk '$2=="finance/owner_notice.py"{print $1}' $K/TO_PINS.md5)" ] && echo 1 || echo 0)
echo "$O" | grep -E "^\[|tables" | sed 's/^/      /'
t "the lock is released after a DONE" $([ ! -d /tmp/s814r/.lock ] && echo 1 || echo 0)
O2=$(run); t "again: ALREADY INSTALLED" $(echo "$O2" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
"${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('/tmp/s814r/finance/finance.db');c.execute(\"INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES ('mwask:rehearse','ask','q','q','fixed,right,unknown','2026-11-13 10:00:00','manoj','2026-11-13 10:00:00')\");c.commit()"
U=$(echo "$O" | grep "undo (one line)" | sed 's/.*(one line): //'); eval "$(echo "$U" | sed 's/ && true restart.*//; s/ && true$//')"
t "the undo line puts all three back byte-identical" $(same3 && echo 1 || echo 0)
t "... and closes an open question on Amir's card as withdrawn" $("${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('/tmp/s814r/finance/finance.db');print(c.execute(\"SELECT COUNT(*) FROM amir_job WHERE kind='ask' AND done_at IS NULL\").fetchone()[0])" | grep -qx 0 && echo 1 || echo 0)
fresh; O=$(REHEARSE_RED_AT=4 run); t "a red after placing (at 4) -> all three back" $(echo "$O" | grep -q "RED after placing" && same3 && echo 1 || echo 0)
fresh; O=$(REHEARSE_RED_AT=5 run); t "a red after the tables (at 5) -> all three back" $(echo "$O" | grep -q "RED after placing" && same3 && echo 1 || echo 0)
fresh; echo "#" >> /tmp/s814k/seg_bw_ask.py; O=$( (export ROOT=/tmp/s814r LOCK=/tmp/s814r/.lock SYSTEMCTL=true HEALTH_CMD="$K/hz.sh" NAP=0; bash /tmp/s814k/install_S814_MARG_WATCH_ASK.sh) 2>&1); t "a kit file altered -> stopped" $(echo "$O" | grep -q "SUMS.md5 gate failed" && same3 && echo 1 || echo 0)
rm -rf /tmp/s814r /tmp/s814k
echo "REHEARSAL $PASSN/$TOTAL"
