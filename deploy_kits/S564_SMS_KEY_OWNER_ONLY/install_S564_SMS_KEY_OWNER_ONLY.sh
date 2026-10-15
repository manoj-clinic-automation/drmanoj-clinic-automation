#!/bin/bash
# =============================================================================
#  install_S564_SMS_KEY_OWNER_ONLY.sh · kit S564 (15-Oct-2026) · brief claude_code_briefs/S564_SMS_KEY_OWNER_ONLY.md
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S564_SMS_KEY_OWNER_ONLY):
#    rm -rf /tmp/s564kit && cp -rp <kit> /tmp/s564kit && bash /tmp/s564kit/install_S564_SMS_KEY_OWNER_ONLY.sh
#  (DRY=1 before bash: every gate and the walks, nothing written.)
#
#  The phone's door key on /finance/bank-sms ("Phone setup — MacroDroid") is drawn for the owner's login only; every other login
#  that can open the page no longer sees the fold at all. Step 4 of the fold says what the phone sends today.
#   /root/finance/bank_sms.py      053d4ccb -> aa527840   4 counted edits
#  Read only, at its pin: bank_standin.py fd635862 (is_owner).  No data step.  The key file is not read by this installer except
#  to look (yes/no) that the placed page shows it to manoj, and to check the scratch folders it removes hold no copy of it.
#  ORDER: gates -> pins (ALREADY first) -> compile (both pythons) -> rebuild from the live bytes (in memory, counted anchors) -> the
#  walk on scratch copies (new green; the old file red) -> DRY stops -> backups (db by the backup API, .bak_S564_053d4ccb) -> place ->
#  md5 read-back -> ONE restart of clinic-finance -> healthz 200, the page 302 (login gate, expected) -> journal clean -> the page read
#  as manoj / shavez / bhawna on copies -> housekeeping of S562's /tmp scratch.
#  Red after placing: the file put back byte-identically, restart, healthz; the database backup stays.
# =============================================================================
set -u
KIT="S564_SMS_KEY_OWNER_ONLY"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
KEYF="${KEYF:-$FIN/bank_sms.key}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
HOUSEKEEP="${HOUSEKEEP:-/tmp/s562kit /tmp/s562probe}"
DMAP="$REPO/claude_code_briefs/DUTY_MAP.json"
N="bank_sms.py"
FROM=053d4ccb85d64403daf9918a0ba6f46c; TO=aa5278403ec85c898d808486e4c3cde3
RONAME="bank_standin.py"; RO=fd635862c75e1ab44f770a6ffd79511a
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s564_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S564_$STAMP"
BAK="$FIN/$N.bak_S564_${FROM:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the file back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$FIN/$N"
  rm -f "$FIN/.$N.s564"
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  say "   $FIN/$N $(m5 "$FIN/$N") (expected $FROM)"
  say "   after the restore: finance healthz $h"
  say "   the database backup stays: $DBBAK (no data was changed by this kit)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date curl timeout grep tail sleep find sed tr wc; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
command -v "$SYSTEMCTL" >/dev/null 2>&1 || { say "!! preflight: $SYSTEMCTL missing - nothing installed"; exit 1; }
[ -x "$APY" ] && [ -x "$VPY" ] || { say "!! preflight: $APY or $VPY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/10] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/10] KIT_ID.txt names another kit - nothing installed"; exit 1; }
if [ "${LOCK_HELD:-0}" = 1 ]; then
  grep -q "$KIT" "$LOCK/owner" 2>/dev/null || { say "!! [1/10] LOCK_HELD=1 but $LOCK/owner does not name $KIT - nothing installed"; exit 3; }
else
  mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
  if [ "$HAVE_LOCK" != 1 ]; then
    say "!! [1/10] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again when it is free."
    exit 3
  fi
  echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
fi
say "[1/10] kit gates green (SUMS, KIT_ID); the build lock is ours"

[ -f "$FIN/$N" ] || { say "!! [2/10] $FIN/$N is not there - nothing installed"; exit 1; }
if [ "$(m5 "$FIN/$N")" = "$TO" ]; then say "-- ALREADY INSTALLED: $N is the kit's ($TO). Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null)"; exit 0; fi
C="$(m5 "$FIN/$N")"; [ "$C" = "$FROM" ] || { say "!! [2/10] $FIN/$N is $C, expected $FROM - it changed after this kit was built: STOP, nothing installed"; exit 1; }
C="$(m5 "$FIN/$RONAME")"; [ "$C" = "$RO" ] || { say "!! [2/10] $FIN/$RONAME is $C, not $RO - this kit was built reading that file: STOP, nothing installed"; exit 1; }
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$DMAP" ] || { say "!! [2/10] the database, the assets database or the duty map is missing - nothing installed"; exit 1; }
say "[2/10] live pins exact (bank_sms 053d4ccb; bank_standin fd635862 read only)"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
chmod 700 "$SCR"
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s564.py walk_s564.py || { say "!! [3/10] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s564.py --fin "$FIN" --out "$SCR/built" >/dev/null || { say "!! [4/10] the builder refused the live file - nothing installed"; exit 1; }
[ "$(m5 "$SCR/built/$N")" = "$TO" ] || { say "!! [4/10] rebuilt, $N is $(m5 "$SCR/built/$N"), not $TO - nothing installed"; exit 1; }
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/$N" || { say "!! [3/10] the built $N does not compile on $py - nothing installed"; exit 1; }
done
say "[3/10] the kit's python files and the built file compile on $APY and $VPY"
say "[4/10] rebuilt here from this box's live bytes (4 counted edits): at its TO pin $TO"

mkside() {   # $1 = side: a copy of the live finance code, the marg reader, the two databases (backup API)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do [ -f "$MARG/$f" ] && cp -p "$MARG/$f" "$d/marg_ingest/"; done
  copydb "$DB" "$d/f.db" && copydb "$ADB" "$d/a.db"
}
for side in new old; do mkside "$side" || { say "!! [5/10] no scratch side '$side' - nothing installed"; exit 1; }; done
cp -p "$SCR/built/$N" "$SCR/new/finance/"
WOUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s564.py" --fin "$SCR/new/finance" --oldfin "$SCR/old/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --map "$DMAP" 2>&1 )"; WRC=$?
for side in new old; do mkside "${side}2" || { say "!! [5/10] no scratch side '${side}2' - nothing installed"; exit 1; }; done
cp -p "$SCR/built/$N" "$SCR/new2/finance/"
ROUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s564.py" --fin "$SCR/old2/finance" --oldfin "$SCR/new2/finance" --db "$SCR/old2/f.db" --adb "$SCR/old2/a.db" --marg "$SCR/old2/marg_ingest" --map "$DMAP" --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S564"; then say "!! [5/10] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | grep -E "^  RED on the old file:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/10] the negative control did not go red on the old file - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -12; exit 1; fi
[ "$(m5 "$FIN/$N")" = "$FROM" ] || { say "!! [5/10] $FIN/$N changed during the walk - nothing installed"; exit 1; }
say "[5/10] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old file: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
rm -rf "$SCR/new" "$SCR/old" "$SCR/new2" "$SCR/old2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [6/10] database backup failed - nothing placed"; exit 1; }
\cp -p "$FIN/$N" "$BAK" || { say "!! [6/10] backup of $N failed - nothing placed"; exit 1; }
[ "$(m5 "$BAK")" = "$FROM" ] || { say "!! [6/10] the backup of $N is not the live file - nothing placed"; exit 1; }
say "[6/10] backups: $(basename "$DBBAK") (sqlite backup API); $(basename "$BAK")"

{ \cp -p "$FIN/$N" "$FIN/.$N.s564" && cat "$SCR/built/$N" > "$FIN/.$N.s564" && [ "$(m5 "$FIN/.$N.s564")" = "$TO" ]; } || { rm -f "$FIN/.$N.s564"; say "!! [7/10] could not stage $N - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.$N.s564" "$FIN/$N" || restore "placing $N"
[ "$(m5 "$FIN/$N")" = "$TO" ] || restore "$N did not land at its pin"
say "[7/10] placed; md5 read back: $N $(m5 "$FIN/$N") (= the kit's)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/bank-sms)
case "$c2" in 302|401) ;; *) restore "/finance/bank-sms answered $c2 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|NOT mounted')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[8/10] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/bank-sms $c2 without a login (302 = the login gate, expected) - journal clean"

mkdir -p "$SCR/placed/finance/spine" "$SCR/placed/marg_ingest/archive"; cp -p "$FIN"/*.py "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/finance/" 2>/dev/null
cp -rp "$FIN/finance_ui" "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$SCR/placed/finance/spine/" 2>/dev/null
for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do [ -f "$MARG/$f" ] && cp -p "$MARG/$f" "$SCR/placed/marg_ingest/"; done
copydb "$DB" "$SCR/placed/f.db" && copydb "$ADB" "$SCR/placed/a.db" || restore "no copy of the database for the page look"
POUT="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s564.py" --page --fin "$SCR/placed/finance" --db "$SCR/placed/f.db" --adb "$SCR/placed/a.db" --marg "$SCR/placed/marg_ingest" --map "$DMAP" --keyfile "$KEYF" 2>&1 )"; PRC=$?
echo "$POUT" | grep -E "^   /finance|^PAGE" | sed 's/^/ /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PAGE OK" || restore "the page on a copy of the placed file is red"
say "[9/10] the placed file (copied) on a copy of the live database, the walk's own session: the fold and the key for manoj only"
rm -rf "$SCR/placed"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0

# housekeeping (the brief): S562's scratch in /tmp -- counted, checked for a secret, a copy of the key or a number, then removed
HK=""
KPAT="$SCR/k.pat"; ( umask 077; tr -d '\r\n' < "$KEYF" > "$KPAT" 2>/dev/null ); [ -s "$KPAT" ] || KPAT=""
for d in $HOUSEKEEP; do
  if [ ! -e "$d" ]; then HK="$HK $(basename "$d"): not there;"; continue; fi
  NF="$(find "$d" -type f 2>/dev/null | wc -l)"
  NS="$(find "$d" -type f \( -name '*.key' -o -name '*.env' -o -name '.env' -o -name '*token*' -o -name '*secret*' -o -name '*.db' -o -name '*.db-*' \) 2>/dev/null | wc -l)"
  NN="$(grep -rIlE '(^|[^0-9])(\+?91[ -]?)?[6-9][0-9]{9}([^0-9]|$)' "$d" 2>/dev/null | wc -l)"
  NK=0; [ -n "$KPAT" ] && NK="$(grep -rlF -f "$KPAT" "$d" 2>/dev/null | wc -l)"
  if [ "$NS" = 0 ] && [ "$NN" = 0 ] && [ "$NK" = 0 ]; then
    rm -rf "$d" 2>/dev/null && [ ! -e "$d" ] && HK="$HK $(basename "$d"): $NF file(s), no secret, no key, no number - removed;" || HK="$HK $(basename "$d"): $NF file(s) - the delete was refused, left;"
  else
    HK="$HK $(basename "$d"): $NF file(s), $NS secret-shaped, $NK holding the key, $NN with a phone-shaped number - LEFT for a person;"
  fi
done
rm -f "$SCR/k.pat"
say "[10/10] housekeeping:$HK"
say "md5 read back:"
md5sum "$FIN/$N"
say "$KIT: DONE - the phone's key on https://followup.dr-manoj.in/finance/bank-sms is drawn for the owner's login only."
say "undo: \\cp -p $BAK $FIN/$N && $SYSTEMCTL restart $SVC"
exit 0
