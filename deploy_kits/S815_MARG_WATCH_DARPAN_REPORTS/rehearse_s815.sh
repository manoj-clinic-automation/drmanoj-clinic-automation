#!/bin/bash
# rehearse_s815.sh -- kit S815's installer on a STAND-IN root (never /root): no duty map, dry, a changed live file, the lock held, install, again,
# the undo line, a red after placing (at 4 and at 5), a kit file altered. STAND=<a folder holding finance/ (the live-as-now bytes of the five files,
# every other finance file, finance.db, spine/spine.db), shared/>; DMAP_NEW = the v24 map; VPY = a python with flask.
set -u
K="$(cd "$(dirname "$0")" && pwd)"; STAND="${STAND:?}"; DMAP_NEW="${DMAP_NEW:?}"; PASSN=0; TOTAL=0
NAMES="marg_billwatch.py darpan_kal.py darpan_kal.html reports_tile.py owner_notice.py"
m5() { md5sum "$1" | awk '{print $1}'; }
fresh() { rm -rf /tmp/s815r && mkdir -p /tmp/s815r && cp -rp "$STAND"/. /tmp/s815r/ && rm -rf /tmp/s815k && cp -rp "$K" /tmp/s815k; }
run() { (export ROOT=/tmp/s815r LOCK=/tmp/s815r/.lock SYSTEMCTL=true HEALTH_CMD="$K/hz.sh" NAP=0 TMPW=/tmp DMAP="${DMAPX:-$DMAP_NEW}" VPY="${VPY:-python3}" APY="${APY:-python3}"; bash /tmp/s815k/install_S815_MARG_WATCH_DARPAN_REPORTS.sh) 2>&1; }
t() { TOTAL=$((TOTAL+1)); if [ "$2" = 1 ]; then PASSN=$((PASSN+1)); echo "ok   $1"; else echo "RED  $1"; fi; }
declare -A F0; for n in $NAMES; do F0[$n]=$(m5 "$STAND/finance/$n"); done
same5() { for n in $NAMES; do [ "$(m5 /tmp/s815r/finance/$n)" = "${F0[$n]}" ] || return 1; done; }
to5() { for n in $NAMES; do [ "$(m5 /tmp/s815r/finance/$n)" = "$(awk -v f="finance/$n" '$2==f{print $1}' $K/TO_PINS.md5)" ] || return 1; done; }
fresh; O=$(DMAPX="$K/KIT_ID.txt" run); t "the duty map without the two duties -> publish first, nothing installed" $(echo "$O" | grep -q "publish first" && same5 && echo 1 || echo 0)
fresh; O=$(DRY=1 run); t "dry: every gate green, nothing written" $(same5 && echo "$O" | grep -q "DRY RUN: every gate" && echo 1 || echo 0)
echo "$O" | grep -E "^\[3/7\]|^!!|^      " | sed 's/^/      /'
fresh; echo "<!-- x -->" >> /tmp/s815r/finance/darpan_kal.html; O=$(run); t "a live file not the pinned one -> stopped, nothing placed" $(echo "$O" | grep -q "changed after this kit was built" && [ "$(m5 /tmp/s815r/finance/marg_billwatch.py)" = "${F0[marg_billwatch.py]}" ] && echo 1 || echo 0)
fresh; mkdir /tmp/s815r/.lock; O=$(run); t "another build holds the lock -> nothing installed" $(echo "$O" | grep -q "another build holds the lock" && same5 && echo 1 || echo 0)
fresh; O=$(run); t "install: DONE, all five at their TO pins" $(echo "$O" | grep -q "S815_MARG_WATCH_DARPAN_REPORTS: DONE" && to5 && echo 1 || echo 0)
echo "$O" | grep -E "^\[|report " | sed 's/^/      /'
t "the lock is released after a DONE" $([ ! -d /tmp/s815r/.lock ] && echo 1 || echo 0)
t "five backups beside the files" $([ "$(ls /tmp/s815r/finance/*.bak_S815_* | wc -l)" = 5 ] && echo 1 || echo 0)
O2=$(run); t "again: ALREADY INSTALLED" $(echo "$O2" | grep -q "ALREADY INSTALLED" && echo 1 || echo 0)
"${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('/tmp/s815r/finance/finance.db');c.execute(\"INSERT INTO marg_watch_ask (to_whom, staff_ref, text_hi, codes, asked_by, asked_at) VALUES ('darpan','darpan:card','q','fixed,right,unknown','manoj','2026-11-13 12:00:00')\");c.execute(\"INSERT INTO marg_watch_report (ref, kind, day_from, day_to, asked_at) VALUES ('rehearse','row','2026-11-10','2026-11-11','2026-11-13 12:00:00')\");c.commit()"
U=$(echo "$O" | grep "undo (one line)" | sed 's/.*(one line): //'); eval "$(echo "$U" | sed 's/ && true restart.*//; s/ && true$//')"
t "the undo line puts all five back byte-identical" $(same5 && echo 1 || echo 0)
t "... and withdraws an open question on Darpan's page and an open report ask" $("${VPY:-python3}" -c "import sqlite3;c=sqlite3.connect('/tmp/s815r/finance/finance.db');print(c.execute(\"SELECT COUNT(*) FROM marg_watch_ask WHERE staff_ref='darpan:card'\").fetchone()[0]+c.execute('SELECT COUNT(*) FROM marg_watch_report WHERE closed_at IS NULL').fetchone()[0])" | grep -qx 0 && echo 1 || echo 0)
fresh; O=$(REHEARSE_RED_AT=4 run); t "a red after placing (at 4) -> all five back" $(echo "$O" | grep -q "RED after placing" && same5 && echo 1 || echo 0)
fresh; O=$(REHEARSE_RED_AT=5 run); t "a red after the table (at 5) -> all five back" $(echo "$O" | grep -q "RED after placing" && same5 && echo 1 || echo 0)
fresh; echo "#" >> /tmp/s815k/seg_bw_s815.py; O=$(run); t "a kit file altered -> stopped" $(echo "$O" | grep -q "SUMS.md5 gate failed" && same5 && echo 1 || echo 0)
rm -rf /tmp/s815r /tmp/s815k
echo "REHEARSAL $PASSN/$TOTAL"
