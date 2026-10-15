#!/bin/bash
# =============================================================================
#  install_S562_BANK_SMS_STANDS_IN.sh · kit S562 (15-Oct-2026, D729) · brief claude_code_briefs/S562_BANK_SMS_STANDS_IN.md
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S562_BANK_SMS_STANDS_IN):
#    rm -rf /tmp/s562kit && cp -rp <kit> /tmp/s562kit && bash /tmp/s562kit/install_S562_BANK_SMS_STANDS_IN.sh
#  (DRY=1 before bash: every gate and the walks, nothing written.)
#
#  The bank's morning UPI settlement SMS stands in for the bank's figure on the clinic's and Sanjeevni's day pages, marked with its
#  time, until the MPR mail comes and takes over by itself; the pages then show both figures, both times and the difference (a
#  difference for the owner only). Installed OFF behind bank_sms.standin_on (his switch on /finance/bank-sms).
#   /root/finance/bank_standin.py  a35d04f1 -> fd635862   bank_day(), the SMS in standing()/day()/owner_items(), the hooks, the switch
#   /root/finance/bank_sms.py      7cdd0ac9 -> 053d4ccb   the ledger per unit, his ON/OFF box (audited), the door tells bank_standin
#   /root/finance/clinic_money.py  0a2085ca -> 7152cd3a   the card's SMS lines; an SMS figure never called a POS total
#   /root/finance/darpan_kal.py    fd799a56 -> a8e11c31   (the Sanjeevni chat's) two counted edits: the source word and its label
#  Read only, at their pins: darpan_app, sanjeevni_approvals, bank_mpr_status, finance_upi, owner_console, finance_app.
#  Data step: ONE setting row, bank_sms.standin_on = '0' (INSERT OR IGNORE). No money row.
#  ORDER: gates -> pins (ALREADY first) + read-only pins -> compile (both pythons) -> rebuild from the live bytes (in memory, counted
#  anchors) -> the walk on scratch copies (new green; the old files red) -> DRY stops -> backups (db by the backup API, .bak_S562_<from8>)
#  -> place -> md5 read-back -> the setting row -> ONE restart of clinic-finance -> healthz 200, the pages 302 (login gate, expected)
#  -> journal clean -> the two pages read as manoj on copies, the switch OFF -> housekeeping of the earlier kits' /tmp scratch.
#  Red after placing: all four files put back byte-identically, restart, healthz; the database backup stays.
# =============================================================================
set -u
KIT="S562_BANK_SMS_STANDS_IN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
POR="${POR:-/root/portal}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
HOUSEKEEP="${HOUSEKEEP:-/tmp/s554kit /tmp/s554probe /tmp/s561kit}"
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
EDITED="bank_standin.py bank_sms.py clinic_money.py darpan_kal.py"
declare -A FROM TO READ
FROM[bank_standin.py]=a35d04f1badcb840d52ee0ea5afcf250; TO[bank_standin.py]=fd635862c75e1ab44f770a6ffd79511a
FROM[bank_sms.py]=7cdd0ac9ca64921507bd0c65ab6a0e99;     TO[bank_sms.py]=053d4ccb85d64403daf9918a0ba6f46c
FROM[clinic_money.py]=0a2085ca5392646521fc9796485ae5f0; TO[clinic_money.py]=7152cd3a7d3dcae6da2a9aee893064e7
FROM[darpan_kal.py]=fd799a56cf212625cfaadce768d3431d;   TO[darpan_kal.py]=a8e11c31b9c80c1b01e63e948418d4a4
READ[darpan_app.py]=a55ecbed4bbe1230b24565b4185b8755;   READ[sanjeevni_approvals.py]=792f4a9af1728c76e8d5a656f5662421
READ[bank_mpr_status.py]=e1a72305cca72b90afcaa6b61bda626d; READ[finance_upi.py]=21eb25560cbb4c5ac35adacf9d46f8d0
READ[owner_console.py]=2b985708b1dc3239fafbb7f41e969e55; READ[finance_app.py]=87cc4266f9cd05f3633f23e1f36488a0
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s562_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S562_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S562_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting all four files back"
  for n in $EDITED; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  rm -f "$FIN"/.*.s562
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $EDITED; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (the one setting row bank_sms.standin_on='0' may remain; with the old files it is read by nothing)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed sort; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/11] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/11] KIT_ID.txt names another kit - nothing installed"; exit 1; }
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/11] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/11] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/11] kit gates green (SUMS, KIT_ID); the build lock is ours"

for n in $EDITED; do [ -f "$FIN/$n" ] || { say "!! [2/11] $FIN/$n is not there - nothing installed"; exit 1; }; done
ALL_TO=1; for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: all four files are the kit's. Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null)"; exit 0; fi
for n in $EDITED; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/11] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; exit 1; }; done
for n in "${!READ[@]}"; do C="$(m5 "$FIN/$n")"; [ "$C" = "${READ[$n]}" ] || { say "!! [2/11] $FIN/$n is $C, not ${READ[$n]} - this kit was built reading that file: STOP, nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$DMAP" ] || { say "!! [2/11] the database, the assets database, the portal or the duty map is missing - nothing installed"; exit 1; }
say "[2/11] live pins exact (bank_standin a35d04f1, bank_sms 7cdd0ac9, clinic_money 0a2085ca, darpan_kal fd799a56); the six read-only files at their pins"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s562.py walk_s562.py || { say "!! [3/11] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s562.py --fin "$FIN" --out "$SCR/built" >/dev/null || { say "!! [4/11] the builder refused a live file - nothing installed"; exit 1; }
for n in $EDITED; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/11] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  for n in $EDITED; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$n" || { say "!! [3/11] the built $n does not compile on $py - nothing installed"; exit 1; }; done
done
say "[3/11] the kit's python files and the four built files compile on $APY and $VPY"
say "[4/11] rebuilt here from this box's live bytes (16 + 6 + 7 + 2 counted edits): each at its TO pin"

mkside() {   # $1 = side: a copy of the live finance code, the marg reader, the two databases (backup API)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do [ -f "$MARG/$f" ] && cp -p "$MARG/$f" "$d/marg_ingest/"; done
  [ -d "$MARG/archive/ORDER_PENDING" ] && cp -rp "$MARG/archive/ORDER_PENDING" "$d/marg_ingest/archive/"
  copydb "$DB" "$d/f.db" && copydb "$ADB" "$d/a.db"
}
for side in new old; do mkside "$side" || { say "!! [5/11] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $EDITED; do cp -p "$SCR/built/$n" "$SCR/new/finance/"; done
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
WOUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s562.py" --fin "$SCR/new/finance" --oldfin "$SCR/old/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --portal "$SCR/por" --map "$DMAP" 2>&1 )"; WRC=$?
for side in new old; do mkside "${side}2" || { say "!! [5/11] no scratch side '${side}2' - nothing installed"; exit 1; }; done
ROUT="$( cd /tmp && timeout 2400 "$APY" -B "$KDIR/walk_s562.py" --fin "$SCR/old2/finance" --oldfin "$SCR/new2/finance" --db "$SCR/old2/f.db" --adb "$SCR/old2/a.db" --marg "$SCR/old2/marg_ingest" --portal "$SCR/por" --map "$DMAP" --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S562"; then say "!! [5/11] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | grep -E "^  RED on the old files:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/11] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -12; exit 1; fi
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [5/11] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[5/11] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
rm -rf "$SCR/new" "$SCR/old" "$SCR/new2" "$SCR/old2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [6/11] database backup failed - nothing placed"; exit 1; }
for n in $EDITED; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [6/11] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/11] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[6/11] backups: $(basename "$DBBAK") (sqlite backup API); $(for n in $EDITED; do printf '%s ' "$(basename "$(bak $n)")"; done)"

for n in $EDITED; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s562" && cat "$SCR/built/$n" > "$FIN/.$n.s562" && [ "$(m5 "$FIN/.$n.s562")" = "${TO[$n]}" ]; } || { rm -f "$FIN"/.*.s562; say "!! [7/11] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $EDITED; do mv -f "$FIN/.$n.s562" "$FIN/$n" || restore "placing $n"; done
for n in $EDITED; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[7/11] placed; md5 read back: $(for n in $EDITED; do printf '%s %s . ' "$n" "$(m5 "$FIN/$n" | cut -c1-8)"; done)(= the kit's)"

SOUT="$("$APY" -B -c "
import sqlite3, sys
c = sqlite3.connect(sys.argv[1], timeout=60)
n = c.execute(\"INSERT OR IGNORE INTO setting (key, value, note) VALUES ('bank_sms.standin_on', '0', 'S562 (D729): 1 = the bank''s settlement SMS stands in for the MPR until the MPR comes; installed OFF')\").rowcount
c.commit()
v = c.execute(\"SELECT value FROM setting WHERE key='bank_sms.standin_on'\").fetchone()[0]
print('setting bank_sms.standin_on = %s (%s)' % (v, 'written now' if n else 'already there, left as it was'))
c.close()
" "$DB" 2>&1)" || restore "the setting row could not be written: $SOUT"
say "[8/11] $SOUT"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/bank-sms); c3=$(health /finance/clinic/money)
for c in "$c2" "$c3"; do case "$c" in 302|401) ;; *) restore "a page answered $c without a login (302 = the login gate, expected): bank-sms $c2 / clinic money $c3";; esac; done
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|NOT mounted')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[9/11] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/bank-sms $c2, /finance/clinic/money $c3 without a login (302 = the login gate, expected) - journal clean"

mkdir -p "$SCR/placed/finance/spine" "$SCR/placed/marg_ingest/archive"; cp -p "$FIN"/*.py "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/finance/" 2>/dev/null
cp -rp "$FIN/finance_ui" "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$SCR/placed/finance/spine/" 2>/dev/null
for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do [ -f "$MARG/$f" ] && cp -p "$MARG/$f" "$SCR/placed/marg_ingest/"; done
copydb "$DB" "$SCR/placed/f.db" && copydb "$ADB" "$SCR/placed/a.db" || restore "no copy of the database for the page look"
POUT="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s562.py" --page --fin "$SCR/placed/finance" --db "$SCR/placed/f.db" --adb "$SCR/placed/a.db" --marg "$SCR/placed/marg_ingest" --map "$DMAP" 2>&1 )"; PRC=$?
echo "$POUT" | grep -E "^   /finance|^PAGE" | sed 's/^/ /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PAGE OK" || restore "the two pages on a copy of the placed files are red"
say "[10/11] the placed files (copied) on a copy of the live database, the walk's own session, as manoj: the ledger and Clinic money read, the switch OFF"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0

# housekeeping (the parent's standing item): the earlier kits' scratch in /tmp -- counted, checked for a secret or a number, then removed
HK=""
for d in $HOUSEKEEP; do
  if [ ! -e "$d" ]; then HK="$HK $(basename "$d"): not there;"; continue; fi
  NF="$(find "$d" -type f 2>/dev/null | wc -l)"
  NS="$(find "$d" -type f \( -name '*.key' -o -name '*.env' -o -name '.env' -o -name '*token*' -o -name '*secret*' -o -name '*.db' -o -name '*.db-*' \) 2>/dev/null | wc -l)"
  NN="$(grep -rIlE '(^|[^0-9])(\+?91[ -]?)?[6-9][0-9]{9}([^0-9]|$)' "$d" 2>/dev/null | wc -l)"
  if [ "$NS" = 0 ] && [ "$NN" = 0 ]; then
    rm -rf "$d" 2>/dev/null && HK="$HK $(basename "$d"): $NF file(s), no secret, no number - removed;" || HK="$HK $(basename "$d"): $NF file(s) - the delete was refused, left;"
  else
    HK="$HK $(basename "$d"): $NF file(s), $NS secret-shaped, $NN with a phone-shaped number - LEFT for a person;"
  fi
done
say "[11/11] housekeeping:$HK"
say "md5 read back:"
for n in $EDITED; do md5sum "$FIN/$n"; done
say "$KIT: DONE - installed OFF. The owner switches it on at https://followup.dr-manoj.in/finance/bank-sms (his box)."
say "undo: $(for n in $EDITED; do printf '\\cp -p %s %s && ' "$(bak $n)" "$FIN/$n"; done)$SYSTEMCTL restart $SVC"
exit 0
