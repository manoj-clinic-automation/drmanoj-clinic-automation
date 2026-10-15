#!/bin/bash
# =============================================================================
#  install_S565_DARPAN_SMS_AND_CLAUDE_BILLS.sh · kit S565 (15-Oct-2026) · brief claude_code_briefs/S565_DARPAN_SMS_AND_CLAUDE_BILLS.md
#
#  Run from a copy of the kit folder (or from /root/deploy/repo/deploy_kits/S565_DARPAN_SMS_AND_CLAUDE_BILLS):
#    rm -rf /tmp/s565kit && cp -rp <kit> /tmp/s565kit && bash /tmp/s565kit/install_S565_DARPAN_SMS_AND_CLAUDE_BILLS.sh
#  (DRY=1 before bash: every gate and the walks, nothing written.)
#
#  PART A only (part B, claude_vs_sarvam_s565.py, is a read-only run of its own and is never run by this installer).
#  Darpan's "Kal ka hisaab" draws the bank's SMS when it stands in for the MPR, and a posted day is worked again when the SMS stands.
#   /root/finance/darpan_kal.html  f5e279eb -> 75d5a5b5   4 counted edits
#   /root/finance/darpan_kal.py    a8e11c31 -> 8128598f   1 counted edit
#  Read only, at their pins: bank_standin.py fd635862, bank_sms.py aa527840 (S564's TO; the brief's 053d4ccb was moved by S564 at 16:45).
#  No data step.
#  ORDER: gates -> pins (ALREADY first) -> compile (both pythons) -> rebuild from the live bytes (in memory, counted anchors) -> the walk on
#  scratch copies (new green; the old files red) -> DRY stops -> backups (db by the backup API, .bak_S565_<from8>) -> place -> md5 read-back
#  -> ONE restart of clinic-finance -> healthz 200, the page 302 (login gate, expected) -> journal clean -> the page read as darpan / manoj
#  on a copy of the placed files and the live database.
#  Red after placing: both files put back byte-identically, restart, healthz; the database backup stays.
# =============================================================================
set -u
KIT="S565_DARPAN_SMS_AND_CLAUDE_BILLS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"
MARG="${MARG:-/root/marg_ingest}"
ADB="${ADB:-/root/assetapp/assets.db}"
POR="${POR:-/root/portal}"
REPO="${REPO:-/root/deploy/repo}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
DMAP="${DMAP:-$REPO/claude_code_briefs/DUTY_MAP.json}"
NAMES="darpan_kal.html darpan_kal.py"
declare -A FROM=( [darpan_kal.html]=f5e279eb26e7f24827f29b79f95b2769 [darpan_kal.py]=a8e11c31b9c80c1b01e63e948418d4a4 )
declare -A TO=( [darpan_kal.html]=75d5a5b51b017abd5ad3aa408609a1ff [darpan_kal.py]=8128598f745fca48a08472905f47da97 )
declare -A RO=( [bank_standin.py]=fd635862c75e1ab44f770a6ffd79511a [bank_sms.py]=aa5278403ec85c898d808486e4c3cde3 )
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s565_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S565_$STAMP"
bak() { echo "$FIN/$1.bak_S565_${FROM[$1]:0:8}"; }

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  for n in $NAMES; do [ -f "$(bak "$n")" ] && \cp -p "$(bak "$n")" "$FIN/$n"; rm -f "$FIN/.$n.s565"; done
  "$SYSTEMCTL" restart "$SVC" || true
  local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health /finance/healthz); [ "$h" = 200 ] && break; done
  for n in $NAMES; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
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
command -v "${JJS:-jjs}" >/dev/null 2>&1 || { say "!! preflight: jjs (the box's JS engine, the walk draws the page with it) missing - nothing installed"; exit 1; }
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
say "[1/10] kit gates green (SUMS, KIT_ID, jjs); the build lock is ours"

for n in $NAMES; do [ -f "$FIN/$n" ] || { say "!! [2/10] $FIN/$n is not there - nothing installed"; exit 1; }; done
if [ "$(m5 "$FIN/darpan_kal.html")" = "${TO[darpan_kal.html]}" ] && [ "$(m5 "$FIN/darpan_kal.py")" = "${TO[darpan_kal.py]}" ]; then
  say "-- ALREADY INSTALLED: both files are the kit's (${TO[darpan_kal.html]:0:8}, ${TO[darpan_kal.py]:0:8}). Nothing written. $SVC $("$SYSTEMCTL" is-active "$SVC" 2>/dev/null)"; exit 0
fi
for n in $NAMES; do
  C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/10] $FIN/$n is $C, expected ${FROM[$n]} - it changed after this kit was built: STOP, nothing installed"; exit 1; }
done
for n in "${!RO[@]}"; do
  C="$(m5 "$FIN/$n")"; [ "$C" = "${RO[$n]}" ] || { say "!! [2/10] $FIN/$n is $C, not ${RO[$n]} - this kit was built reading that file: STOP, nothing installed"; exit 1; }
done
[ -f "$DB" ] && [ -f "$ADB" ] && [ -f "$POR/portal.py" ] && [ -f "$POR/tile_grants.json" ] && [ -f "$DMAP" ] || { say "!! [2/10] the database, the assets database, the portal or the duty map is missing - nothing installed"; exit 1; }
say "[2/10] live pins exact (darpan_kal.html f5e279eb, darpan_kal.py a8e11c31; read only: bank_standin fd635862, bank_sms aa527840)"

mkdir -p "$SCR/built" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
chmod 700 "$SCR"
export PYTHONDONTWRITEBYTECODE=1
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile make_s565.py walk_s565.py claude_vs_sarvam_s565.py || { say "!! [3/10] compile failed on $py - nothing installed"; exit 1; }
done
"$APY" -B make_s565.py --fin "$FIN" --out "$SCR/built" >/dev/null || { say "!! [4/10] the builder refused the live files - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$SCR/built/$n")" = "${TO[$n]}" ] || { say "!! [4/10] rebuilt, $n is $(m5 "$SCR/built/$n"), not ${TO[$n]} - nothing installed"; exit 1; }; done
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile "$SCR/built/darpan_kal.py" || { say "!! [3/10] the built darpan_kal.py does not compile on $py - nothing installed"; exit 1; }
done
say "[3/10] the kit's python files and the built darpan_kal.py compile on $APY and $VPY"
say "[4/10] rebuilt here from this box's live bytes (4 + 1 counted edits): darpan_kal.html ${TO[darpan_kal.html]}, darpan_kal.py ${TO[darpan_kal.py]}"

mkside() {   # $1 = side: a copy of the live finance code, the marg reader, the two databases (backup API)
  local d="$SCR/$1"; mkdir -p "$d/finance/spine" "$d/finance/finance_ui" "$d/marg_ingest/archive"
  cp -p "$FIN"/*.py "$d/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$d/finance/" 2>/dev/null
  cp -rp "$FIN/finance_ui/." "$d/finance/finance_ui/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$d/finance/spine/" 2>/dev/null
  for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do [ -f "$MARG/$f" ] && cp -p "$MARG/$f" "$d/marg_ingest/"; done
  copydb "$DB" "$d/f.db" && copydb "$ADB" "$d/a.db"
}
mkdir -p "$SCR/por"; for f in "$POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$SCR/por/"; done; cp -p "$POR/tile_grants.json" "$SCR/por/"
for side in new old; do mkside "$side" || { say "!! [5/10] no scratch side '$side' - nothing installed"; exit 1; }; done
for n in $NAMES; do cp -p "$SCR/built/$n" "$SCR/new/finance/"; done
WOUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s565.py" --fin "$SCR/new/finance" --oldfin "$SCR/old/finance" --db "$SCR/new/f.db" --adb "$SCR/new/a.db" --marg "$SCR/new/marg_ingest" --portal "$SCR/por" --map "$DMAP" ${DUMP:+--dump "$DUMP"} 2>&1 )"; WRC=$?
for side in new old; do mkside "${side}2" || { say "!! [5/10] no scratch side '${side}2' - nothing installed"; exit 1; }; done
for n in $NAMES; do cp -p "$SCR/built/$n" "$SCR/new2/finance/"; done
ROUT="$( cd /tmp && timeout 1800 "$APY" -B "$KDIR/walk_s565.py" --fin "$SCR/old2/finance" --oldfin "$SCR/new2/finance" --db "$SCR/old2/f.db" --adb "$SCR/old2/a.db" --marg "$SCR/old2/marg_ingest" --portal "$SCR/por" --map "$DMAP" --expect-red 2>&1 )"; RRC=$?
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
echo "$WOUT" | sed 's/^/   /'
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK S565"; then say "!! [5/10] the walk is RED on this box (exit $WRC) - nothing installed"; exit 1; fi
echo "$ROUT" | grep -E "^   drawn|^  RED on the old files:|^WALK OK negative|^NEGATIVE CONTROL" | sed 's/^/   /'
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK negative control"; then say "!! [5/10] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; echo "$ROUT" | tail -12; exit 1; fi
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "${FROM[$n]}" ] || { say "!! [5/10] $FIN/$n changed during the walk - nothing installed"; exit 1; }; done
say "[5/10] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "       negative control, the old files: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c27-)"
rm -rf "$SCR/new" "$SCR/old" "$SCR/new2" "$SCR/old2"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" && chmod 600 "$DBBAK" || { rm -f "$DBBAK"; say "!! [6/10] database backup failed - nothing placed"; exit 1; }
for n in $NAMES; do
  \cp -p "$FIN/$n" "$(bak "$n")" || { say "!! [6/10] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak "$n")")" = "${FROM[$n]}" ] || { say "!! [6/10] the backup of $n is not the live file - nothing placed"; exit 1; }
done
say "[6/10] backups: $(basename "$DBBAK") (sqlite backup API); $(basename "$(bak darpan_kal.html)"); $(basename "$(bak darpan_kal.py)")"

for n in $NAMES; do
  { \cp -p "$FIN/$n" "$FIN/.$n.s565" && cat "$SCR/built/$n" > "$FIN/.$n.s565" && [ "$(m5 "$FIN/.$n.s565")" = "${TO[$n]}" ]; } || { for x in $NAMES; do rm -f "$FIN/.$x.s565"; done; say "!! [7/10] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $NAMES; do mv -f "$FIN/.$n.s565" "$FIN/$n" || restore "placing $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[7/10] placed; md5 read back: darpan_kal.html $(m5 "$FIN/darpan_kal.html"), darpan_kal.py $(m5 "$FIN/darpan_kal.py") (= the kit's)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
"$SYSTEMCTL" restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(health /finance/healthz); [ "$c1" = 200 ] && break; done
"$SYSTEMCTL" is-active --quiet "$SVC" || restore "$SVC is not active"
[ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health /finance/darpan/kal)
case "$c2" in 302|401) ;; *) restore "/finance/darpan/kal answered $c2 without a login (302 = the login gate, expected)";; esac
if command -v "$JOURNALCTL" >/dev/null 2>&1; then
  JR="$("$JOURNALCTL" -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -c -i -E 'Traceback|SyntaxError|ImportError|ModuleNotFoundError|NameError|NOT mounted')"
  [ "${JR:-0}" = 0 ] || restore "journal: $JR error line(s) since the restart"
fi
say "[8/10] $SVC restarted at $T0 (nothing else) and active - healthz $c1 - /finance/darpan/kal $c2 without a login (302 = the login gate, expected) - journal clean"

mkdir -p "$SCR/placed/finance/spine" "$SCR/placed/marg_ingest/archive"; cp -p "$FIN"/*.py "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/finance/" 2>/dev/null
cp -rp "$FIN/finance_ui" "$SCR/placed/finance/" 2>/dev/null; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$SCR/placed/finance/spine/" 2>/dev/null
for f in marg_router.py xlsx_stdlib.py marg_take.py marg_ingest.py; do [ -f "$MARG/$f" ] && cp -p "$MARG/$f" "$SCR/placed/marg_ingest/"; done
copydb "$DB" "$SCR/placed/f.db" && copydb "$ADB" "$SCR/placed/a.db" || restore "no copy of the database for the page look"
POUT="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s565.py" --page --fin "$SCR/placed/finance" --db "$SCR/placed/f.db" --adb "$SCR/placed/a.db" --marg "$SCR/placed/marg_ingest" --map "$DMAP" 2>&1 )"; PRC=$?
echo "$POUT" | grep -E "^   /finance|^PAGE" | sed 's/^/ /'
[ "$PRC" = 0 ] && echo "$POUT" | grep -q "^PAGE OK" || restore "the page on a copy of the placed files is red"
say "[9/10] the placed files (copied) on a copy of the live database, the walk's own session: /finance/darpan/kal 200 as darpan, the owner's view as manoj"
rm -rf "$SCR/placed"
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
PLACED=0
say "[10/10] md5 read back:"
md5sum "$FIN/darpan_kal.html" "$FIN/darpan_kal.py"
say "$KIT (part A): DONE - Darpan's Kal ka hisaab draws the bank's SMS when it stands in; a posted day is worked again when the SMS stands."
say "undo: \\cp -p $(bak darpan_kal.html) $FIN/darpan_kal.html && \\cp -p $(bak darpan_kal.py) $FIN/darpan_kal.py && $SYSTEMCTL restart $SVC"
exit 0
