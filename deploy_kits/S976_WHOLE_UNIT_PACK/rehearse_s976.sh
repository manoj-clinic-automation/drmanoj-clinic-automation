#!/bin/bash
# rehearse_s976.sh -- S976_WHOLE_UNIT_PACK on a MADE-UP root in the device VM (never the box): dry . red@4 . red@5 . install . again . undo .
# install again . wrong FROM . a read pin moved . the lock . a corrupt kit.
#     bash rehearse_s976.sh KIT_DIR LIVE_ROOT_COPY DB_COPY [STEP]
# STEP (1-11) runs that one step only, with its scratch in $REH_W kept between calls (the device shell stops what outlives a call);
# steps 4-7 share one root (install . again . undo . install again) and run in that order. No STEP: all eleven.
set -u
K="$(cd "$1" && pwd)"; F="$(cd "$2" && pwd)"; DBC="$3"; W="${REH_W:-$(mktemp -d /tmp/reh_s976_XXXX)}"; mkdir -p "$W"; PASS=0; N=0; ONLY="${4:-}"; I=0
want() { I=$((I+1)); [ -z "$ONLY" ] || [ "$ONLY" = "$I" ]; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
ok() { N=$((N+1)); if [ "$1" = 0 ]; then PASS=$((PASS+1)); echo "PASS $2"; else echo "FAIL $2"; fi; }
fresh() { rm -rf "$W/root"; mkdir -p "$W/root"; cp -rp "$F/finance" "$F/marg_ingest" "$F/shared" "$W/root/"
  rm -f "$W/root/finance/"*.bak_S976_*; cp "$DBC" "$W/root/finance/finance.db"; }
printf '#!/bin/bash\necho 200\n' > "$W/hz"; printf '#!/bin/bash\necho 302\n' > "$W/door"; printf '#!/bin/bash\necho "S930 stock_check mounted v1.9"\n' > "$W/log"; chmod +x "$W/hz" "$W/door" "$W/log"
run() { (export ROOT="$W/root" LOCK="$W/build.lock" RLOCK="$W/rec.lock" SYSTEMCTL=true HEALTH_CMD="$W/hz" DOOR_CMD="$W/door" LOG_CMD="$W/log" NAP=0 APY=python3 VPY=python3 TMPW="$W"; "$@"); }
pin() { awk -v f="$1" '$2==f{print $1}' "$K/TO_PINS.md5"; }
NAMES="finance/stock_figure.py finance/stock_watch.py finance/stockmatch.py finance/voucher_judge.py finance/stock_check.py"
at_to() { for n in $NAMES; do [ "$(m5 "$W/root/$n")" = "$(pin $n)" ] || return 1; done; }
at_from() { [ "$(m5 "$W/root/finance/stock_figure.py")" = 0d8cab560d19783febf134058f447763 ] && [ "$(m5 "$W/root/finance/stock_watch.py")" = fe0a89cd0206b19ccf5439c9f364fb5e ] \
  && [ "$(m5 "$W/root/finance/stockmatch.py")" = 1f5a15bade4f6e002e61b883eadcaee0 ] && [ "$(m5 "$W/root/finance/voucher_judge.py")" = 59a68bb15c24261f533a48a33457fccb ] \
  && [ "$(m5 "$W/root/finance/stock_check.py")" = 6b8d077cd2e30b18dd02e42551a2d83f ]; }
q() { python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute(sys.argv[2]).fetchone())" "$W/root/finance/finance.db" "$1" 2>&1; }
ccm() { q "SELECT qty_units, (SELECT pack FROM stock_spot_roster r WHERE r.id=p.roster_id) FROM stock_point p WHERE item='CCM' AND source='spot' ORDER BY id DESC LIMIT 1"; }
rpk() { q "SELECT pack FROM stock_of_record WHERE item='CCM'"; }
INST="$K/install_S976_WHOLE_UNIT_PACK.sh"
if want; then
fresh; C0=$(ccm); O=$(run env DRY=1 bash "$INST" 2>&1); echo "$O" | grep -E "LIVE-SHAPE|DUMP|\[3/6\]|^!!" | cut -c1-300 | sed 's/^/      /'
echo "$O" | grep -q "DRY RUN: every gate" && at_from && [ "$(ccm)" = "$C0" ]; ok $? "dry: the gates, the walk twice, the control red, six earlier walks the same, the record on two copies; nothing written"
fi
if want; then
fresh; C0=$(ccm); O=$(run env REHEARSE_RED_AT=4 bash "$INST" 2>&1); echo "$O" | grep -q "forced red at \[4/6\]" && at_from && [ "$(ccm)" = "$C0" ]; ok $? "red at [4/6]: the five files back, the data untouched"
fi
if want; then
fresh; C0=$(ccm); O=$(run env REHEARSE_RED_AT=5 bash "$INST" 2>&1); echo "$O" | grep -E "the data:|the record:" | sed 's/^/      /'
echo "$O" | grep -q "forced red at \[5/6\]" && at_from && [ "$(ccm)" = "$C0" ] && [ "$(rpk)" = "(40,)" ]; ok $? "red at [5/6] (after the data fix): the five files back, the count back to $C0, the record rebuilt at pack 40"
fi
if want; then
fresh; O=$(run bash "$INST" 2>&1); echo "$O" | tail -7 | cut -c1-300 | sed 's/^/      /'
echo "$O" | grep -q "S976_WHOLE_UNIT_PACK: DONE" && at_to && [ "$(ccm)" = "(1.0, 1)" ] && [ "$(rpk)" = "(1,)" ]; ok $? "install: five files at TO; CCM's count 40 -> 1 bottle, its list row pack 1; the record's pack 1"
fi
if want; then
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q "ALREADY INSTALLED" && at_to && [ "$(ccm)" = "(1.0, 1)" ]; ok $? "again: ALREADY INSTALLED, nothing touched"
fi
if want; then
O=$(run bash "$K/undo_s976.sh" 2>&1); echo "$O" | grep -E "the data|the record" | sed 's/^/      /'
echo "$O" | grep -q "S976 UNDONE" && at_from && [ "$(ccm)" = "(40.0, 40)" ] && [ "$(rpk)" = "(40,)" ]; ok $? "undo: the five files at FROM, the count back to 40, the record at pack 40"
fi
if want; then
O=$(run bash "$INST" 2>&1); echo "$O" | grep -q ": DONE" && at_to && [ "$(ccm)" = "(1.0, 1)" ]; ok $? "install again after the undo: the same fix again"
fi
if want; then
fresh; echo "# drift" >> "$W/root/finance/stock_watch.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*stock_watch.py.*changed after this kit was built" && [ "$(m5 "$W/root/finance/stock_figure.py")" = 0d8cab560d19783febf134058f447763 ]; ok $? "wrong FROM (a live file changed): stopped at [2/6], nothing placed"
fi
if want; then
fresh; echo "# drift" >> "$W/root/finance/record_judges.py"; O=$(run bash "$INST" 2>&1)
echo "$O" | grep -q "\[2/6\].*record_judges.py is not at" && at_from; ok $? "a file the kit reads moved: stopped at [2/6], nothing placed"
fi
if want; then
fresh; mkdir "$W/build.lock"; O=$(run bash "$INST" 2>&1); RC=$?; rmdir "$W/build.lock"; [ "$RC" = 3 ] && at_from; ok $? "another build holds the lock: exit 3, nothing placed"
fi
if want; then
fresh; cp "$K/SUMS.md5" "$W/sums.bak"; sed -i '1s/^./0/' "$K/SUMS.md5"; O=$(run bash "$INST" 2>&1); cp "$W/sums.bak" "$K/SUMS.md5"
echo "$O" | grep -q "SUMS.md5 gate failed" && at_from; ok $? "a corrupt kit: refused at [1/6]"
fi
[ -n "${REH_W:-}" ] || rm -rf "$W"
echo "REHEARSAL $PASS/$N"
