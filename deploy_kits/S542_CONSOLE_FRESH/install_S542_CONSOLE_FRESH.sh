#!/bin/bash
# =============================================================================
#  install_S542_CONSOLE_FRESH.sh · kit S542 (session 313, 13-Oct-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S542_CONSOLE_FRESH/install_S542_CONSOLE_FRESH.sh
#
#  THE OWNER, 07:26 IST 13-Oct: "check why my command console does not show the amounts. Although the 12th October amounts are
#  showing in the relevant page of doctor's revenue ... whenever I update something through the command console, and then I
#  come back to command console and even refresh it, then also those stale messages are not cleared."
#   /root/finance/owner_console.py c09321e2 and owner_console.html e6d35d88, built HERE from the live bytes by make_s542.py
#   (2 + 2 counted edits):
#   1  the clinic's day on the console and on the Today tile reads Docterz's own day total while the counter sheet is not yet
#      filled (it read Rs 0: the morning match stops early and carries no totals); with the sheet in and Docterz not yet, the
#      sheet's total.
#   2  the console asks for a fresh reading when it is opened or reloaded and when he comes back to it -- not one up to five
#      minutes old.
#  Restarts clinic-finance. No other file. No data step.
#  ORDER: gates -> pins (ALREADY first) -> compile -> rebuild from the live bytes -> walk (the console's own builder on a copy
#  of the database, the counter sheet taken out on the walk's copy; the old files red) -> DRY stops -> backups -> place ->
#  restart -> health -> undo line.
# =============================================================================
set -u
KIT="S542_CONSOLE_FRESH"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
NAMES="owner_console.py owner_console.html"
declare -A FROM TO
FROM[owner_console.py]=c09321e2356f6b1bc441bb1f75118cbc;   TO[owner_console.py]=2b985708b1dc3239fafbb7f41e969e55
FROM[owner_console.html]=e6d35d88b87890911124b9778a43c5d2; TO[owner_console.html]=e0d7d62fe2c8e6184748052e3896905c
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s542_inst_$STAMP"
HAVE_LOCK=0; PLACED=0

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$FIN/$1.bak_S542_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting both files back"
  for n in $NAMES; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$FIN/$n"; done
  systemctl restart "$SVC" || true; sleep 3
  for n in $NAMES; do say "   $FIN/$n $(m5 "$FIN/$n") (expected ${FROM[$n]})"; done
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date systemctl curl timeout grep tail sleep; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$APY" ] || { say "!! preflight: $APY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$n")" = "${TO[$n]}" ] || { say "!! [1/8] the kit's $n is not its predicted md5 - nothing installed"; exit 1; }; done
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

ALL_TO=1
for n in $NAMES; do [ -f "$FIN/$n" ] || { say "!! [2/8] $FIN/$n is not there - nothing installed"; exit 1; }; [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
if [ "$ALL_TO" = 1 ]; then say "-- ALREADY INSTALLED: both files are the kit's. Nothing written."; exit 0; fi
for n in $NAMES; do C="$(m5 "$FIN/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/8] $FIN/$n is $C, expected ${FROM[$n]} - nothing installed"; exit 1; }; done
[ -f "$DB" ] || { say "!! [2/8] $DB is not there - nothing installed"; exit 1; }
say "[2/8] two live pins exact (owner_console.py c09321e2, owner_console.html e6d35d88)"

mkdir -p "$SCR/old" "$SCR/new" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"; export PYTHONDONTWRITEBYTECODE=1
"$APY" -m py_compile owner_console.py walk_s542.py make_s542.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
say "[3/8] py_compile green (3 files)"

"$APY" -B make_s542.py "$FIN/owner_console.py" "$SCR/new/owner_console.py" "$FIN/owner_console.html" "$SCR/new/owner_console.html" \
  >/dev/null || { say "!! [4/8] the builder refused a live file - nothing installed"; exit 1; }
for n in $NAMES; do
  [ "$(m5 "$SCR/new/$n")" = "${TO[$n]}" ] || { say "!! [4/8] rebuilt from the live bytes, $n is not the kit's - nothing installed"; exit 1; }
  \cp -p "$FIN/$n" "$SCR/old/$n"
done
say "[4/8] rebuilt from the live bytes: byte for byte the kit's two files"

"$APY" - "$DB" "$SCR/copy.db" <<'PYEOF' || { say "!! [5/8] could not take a copy of the database - nothing installed"; exit 1; }
import sqlite3, sys
src = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close(); src.close()
PYEOF
WOUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s542.py" "$SCR/new" --fin "$FIN" --db "$SCR/copy.db" 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s542.py" "$SCR/old" --fin "$FIN" --db "$SCR/copy.db" --expect-red 2>&1 )"; RRC=$?
rm -f "$SCR/copy.db"
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [5/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -8; say "   nothing installed"; exit 1
fi
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK"; then
  say "!! [5/8] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; exit 1
fi
say "[5/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "      negative control: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c1-110)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for n in $NAMES; do
  \cp -p "$FIN/$n" "$(bak $n)" || { say "!! [6/8] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/8] the backup of $n is not the live file - nothing placed"; exit 1; }
done
for n in $NAMES; do
  \cp -p "$SCR/new/$n" "$FIN/.$n.s542" || { rm -f "$FIN"/.*.s542; say "!! [6/8] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $NAMES; do mv -f "$FIN/.$n.s542" "$FIN/$n" || restore "placing $n"; done
for n in $NAMES; do [ "$(m5 "$FIN/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
say "[6/8] backups beside both files; both files placed"

systemctl restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$c1" = 200 ] && break; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/console")
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/console/api/state")
systemctl is-active --quiet "$SVC" || restore "$SVC is not active"
ok2() { [ "$1" = 302 ] || [ "$1" = 401 ] || [ "$1" = 303 ] || [ "$1" = 403 ]; }
{ [ "$c1" = 200 ] && ok2 "$c2" && ok2 "$c3"; } || restore "finance health $c1 / console $c2 / its reading $c3"
MF="$(journalctl -u "$SVC" --since "-2 min" --no-pager 2>/dev/null | grep -E "owner_console NOT mounted" | head -1)"
[ -z "$MF" ] || restore "a module did not mount: $MF"
say "[7/8] $SVC active - health $c1 - the console $c2 and its reading $c3 without a login (refused, as it should be) - the console mounted"
PLACED=0
for n in $NAMES; do md5sum "$FIN/$n"; done
say "[8/8] $KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/console"
say "undo: \\cp -p $(bak owner_console.py) $FIN/owner_console.py && \\cp -p $(bak owner_console.html) $FIN/owner_console.html && systemctl restart $SVC"
