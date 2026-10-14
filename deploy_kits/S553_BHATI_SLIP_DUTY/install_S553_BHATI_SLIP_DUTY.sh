#!/bin/bash
# =============================================================================
#  install_S553_BHATI_SLIP_DUTY.sh · kit S553 (14-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S553_BHATI_SLIP_DUTY/install_S553_BHATI_SLIP_DUTY.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  THE OWNER, 14-Oct 05:43 IST: "his daily slip entry goes on his staff duty list." Bhati's 'Aaj ka kaam' gets one line: the
#  physiotherapy slips of a day (from 14-Oct, before today) are not in his register, or do not agree with reception's cash / UPI.
#   /root/finance/aaj_duties.json  2d6d30eb -> TO   one 'extra' duty bhati.physio_register (kind sql; make_s553.py, 1 counted edit)
#   /root/finance/aaj_seed.py      156ded1e -> TO   its door (/finance/physio/book?day={since}) and Bhati's panel line, on (2 edits)
#  Data step (cfg_s553.py, idempotent): only if the owner has SAVED a panel for bhati -- the line appended to it, switched on.
#  NEVER: clinic_physio_day or any physio table written; another person's list changed; a line switched off.
#  Read, not edited (pinned): aaj_kaam.py, physio_book.py. Restarts clinic-finance only (aaj_kaam imports aaj_seed there).
#  ORDER: gates -> pins (ALREADY first) -> compile (both pythons) -> rebuild from the live bytes -> walk on scratch copies (new green;
#  the old files red) -> DRY stops -> backups (db + .bak_S553_<from8>) -> place -> md5 read-back -> data step -> restart -> health
#  200, /finance/aaj 302 -> as manoj on a copy: /finance/aaj?as=bhati shows the line or not, and why -> undo line.
#  Red after placing: both files put back byte-identically, restart, health; the db backup stays.
# =============================================================================
set -u
KIT="S553_BHATI_SLIP_DUTY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                      # the service's python
VPY="${VPY:-/root/wa/venv/bin/python3}"             # the jobs' python: every file must compile on both
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
EDITED="aaj_duties.json aaj_seed.py"
declare -A FROM TO SRC READ
FROM[aaj_duties.json]=2d6d30ebe73ff721d5591743c86eebb1; TO[aaj_duties.json]=cb8ac36aa60768216b82c918874a65af; SRC[aaj_duties.json]=aaj_duties.json.kit
FROM[aaj_seed.py]=156ded1ee17b852b4a30e94be453ca61;     TO[aaj_seed.py]=a97cd07bfc7270184c62c16dff4dff48;       SRC[aaj_seed.py]=aaj_seed.py
READ[aaj_kaam.py]=cd232b1c987417aa07d341d498c5effc;     READ[physio_book.py]=745130164014ec8d6f90cda839f5521b
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s553_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S553_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S553_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN"/.*.s553
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (a line the data step may have added to a saved panel is unknown to the old seed and is dropped by aaj_kaam -- harmless)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "${SRC[$n]}")" = "${TO[$n]}" ] || { say "!! [1/9] the kit's ${SRC[$n]} is not the file this installer names - nothing installed"; exit 1; }; done
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/9] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/9] kit gates green (SUMS, KIT_ID, each file's own md5); the build lock is ours"

for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [2/9] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: aaj_duties.json and aaj_seed.py are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null)"; exit 0; fi
for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/9] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; exit 1; }; done
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/9] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading that file: STOP, nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [2/9] $DB is not there - nothing installed"; exit 1; }
[ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] || { say "!! [2/9] $POR/portal.py or tile_grants.json missing (the staff-eye walk reads them) - nothing installed"; exit 1; }
say "[2/9] live pins exact (aaj_duties 2d6d30eb, aaj_seed 156ded1e); read beside them: aaj_kaam cd232b1c, physio_book 74513016"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile aaj_seed.py make_s553.py cfg_s553.py walk_s553.py probe_s553.py \
    || { say "!! [3/9] compile failed on $py - nothing installed"; exit 1; }
  "$py" -c "import json,sys; json.load(open(sys.argv[1], encoding='utf-8'))" aaj_duties.json.kit || { say "!! [3/9] aaj_duties.json.kit does not read as JSON on $py - nothing installed"; exit 1; }
done
say "[3/9] the kit's python files compile on $APY and $VPY; the duties file reads as JSON on both"

"$APY" -B make_s553.py "$FIN" "$SCR/built" >/dev/null || { say "!! [4/9] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do
  [ "$(m5 "$SCR/built/${SRC[$n]}")" = "${TO[$n]}" ] || { say "!! [4/9] rebuilt from the live bytes, $n is $(m5 "$SCR/built/${SRC[$n]}"), not ${TO[$n]} - nothing installed"; exit 1; }
done
say "[4/9] rebuilt here from this box's live bytes (1 + 2 counted edits): each is the kit's file, byte for byte"

mkscratch() {   # $1 = side folder: a copy of the live finance code (never the database, never a backup)
  mkdir -p "$1/finance_ui" "$1/spine"
  cp -p "$FIN"/*.py "$1/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$1/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$1/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$1/spine/" 2>/dev/null
  return 0
}
for side in new old; do mkscratch "$SCR/$side"; copydb "$DB" "$SCR/$side.db" || { say "!! [5/9] no scratch copy of the database - nothing installed"; exit 1; }; done
cp -p aaj_seed.py "$SCR/new/aaj_seed.py"; cp -p aaj_duties.json.kit "$SCR/new/aaj_duties.json"
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
WOUT="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s553.py" --fin "$SCR/new" --db "$SCR/new.db" --portal "$SCR/por" --kit "$KDIR" 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 900 "$APY" -B "$KDIR/walk_s553.py" --fin "$SCR/old" --db "$SCR/old.db" --portal "$SCR/por" --kit "$KDIR" --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S553"; then say "!! [5/9] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/9] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -8; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [5/9] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[5/9] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "      negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
echo "$ROUT" | grep -E "^  FAIL LINE:" | cut -c1-150 | sed 's/^/      /'
rm -rf "$SCR/old" "$SCR"/*.db
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [6/9] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [6/9] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/9] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[6/9] backups: $(basename "$DBBAK") (sqlite backup API); $(basename "$(bak aaj_duties.json)"), $(basename "$(bak aaj_seed.py)")"

for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s553" && cat "${SRC[$n]}" > "$FIN/.$n.s553" && [ "$(m5 "$FIN/.$n.s553")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s553; say "!! [7/9] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $EDITED; do mv -f "$FIN/.$n.s553" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[7/9] placed; md5 read back: aaj_duties.json $(m5 "$FIN/aaj_duties.json") . aaj_seed.py $(m5 "$FIN/aaj_seed.py") (= the kit's)"

SOUT="$("$APY" -B cfg_s553.py "$DB" 2>&1)" || { echo "$SOUT"; restore "the data step"; }
say "[8/9] $SOUT"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
c2=$(health /finance/aaj); c3=$(health /finance/aaj/api/list); c4=$(health /finance/physio/book)
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
for c in "$c2" "$c3" "$c4"; do case "$c" in 302|401) ;; *) restore "a page answered $c without a login (302 = the login gate expected): aaj $c2 / list $c3 / register $c4";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
( cd "$FIN" && "$APY" -B -c "import json, aaj_seed; assert 'bhati.physio_register' in aaj_seed.ENGINE and any(l['id']=='bhati.physio_register' and l['on'] for p in aaj_seed.PEOPLE if p['key']=='bhati' for l in p['lines']); d=json.load(open('aaj_duties.json', encoding='utf-8')); assert [x for x in d['extra'] if x['id']=='bhati.physio_register']" ) 2>/dev/null \
  || restore "the placed files do not load under $APY"
mkscratch "$SCR/placed"; copydb "$DB" "$SCR/placed.db" || restore "no copy of the database for the look as manoj"
POUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s553.py" --fin "$SCR/placed" --db "$SCR/placed.db" 2>&1 )"; PRC=$?
echo "$POUT" | grep -v -E '^\s*$' | tail -8 | sed 's/^/   /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PROBE OK" || restore "the look as manoj on a copy is red"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[9/9] $SVC restarted (nothing else) and active - healthz $c1 - /finance/aaj $c2, /finance/aaj/api/list $c3, /finance/physio/book $c4 without a login (302 = the login gate, expected) - journal clean"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE - Bhati's list carries the physio slips line (shown only while a day from 14-Oct disagrees with reception)"
say "undo: \\cp -p $(bak aaj_duties.json) $FIN/aaj_duties.json && \\cp -p $(bak aaj_seed.py) $FIN/aaj_seed.py && $SYSTEMCTL restart $SVC"
exit 0
