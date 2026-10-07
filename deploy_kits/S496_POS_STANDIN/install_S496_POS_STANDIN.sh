#!/bin/bash
# =============================================================================
# install_S496_POS_STANDIN.sh -- session 300 (parent), 07-Oct-2026 -- the POS machine's UPI total, when the bank's statement has not come
#  THE OWNER, 07-Oct 12:17 IST: "when the bank's daily statement (MPR) has not come, the staff give the POS machine's UPI total
#  on the SAME screen they already use, and it counts only after my confirmation."  No new screen for anyone.
#  NEW:    /root/finance/bank_standin.py     ONE table (bank_standin) and ONE function every unit reads; the owner's lines; the settings.
#  WHOLE-FILE REPLACEMENTS, each gated on the md5 of the file it replaces (the 07-Oct 01:35 bundle's bytes):
#          /root/finance/bank_mpr_status.py                 a0e740ce -> the stale 11:15 / 12:20 become the setting bank_mpr.expect_hhmm (default 10:00)
#          /root/finance/clinic_money.py                    c56d3331 -> the match's bank part; the one field on the counter sheet and the
#                                                                      morning-match card; his line, his own typing and the settings on Clinic money
#          /root/finance/darpan_kal.py                      c45bb343 -> compute_day reads a confirmed figure (still provisional); the day is decided
#                                                                      again on his confirmation; three small routes; his lines on the owner card
#          /root/finance/darpan_kal.html                    ec8b64ae -> the one optional field in Darpan's form (Devanagari); the owner's badge
#          /root/finance/finance_ui/finance_approvals.html  8edc44c5 -> Confirm / Reject on the Kal ka hisaab card; his own typing; the settings
#  (the last three are the Sanjeevni chat's files; it agreed in its prompt of 07-Oct, and the PLANNED line is on the board.)
#  NOT TOUCHED: finance_app.py, clinic_register.py, any money row. The table is created on first use, inside a request (F-303).
#  UNTIL A FIGURE IS TYPED AND THE BANK IS IN, EVERY PAGE IS BYTE FOR BYTE TODAY'S PAGE -- the walk proves it on this box first.
# Walked first, on this box (walk_s496.py): the live code and the kit render the same pages on a copy of finance.db and are compared;
# then the whole life of a typed figure is walked on that copy for the clinic and for Sanjeevni, and every money table is fingerprinted.
# Restarts clinic-finance only (about 10 seconds); red after placing -> all six files are put back as they were.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S496_POS_STANDIN"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
DB="${FINANCE_DB:-$FIN/finance.db}"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
# kit file | destination under $FIN | md5 it replaces | md5 it becomes
TABLE="bank_mpr_status.py|bank_mpr_status.py|a0e740ce745230bcd7cada69e0428648|e1a72305cca72b90afcaa6b61bda626d
clinic_money.py|clinic_money.py|c56d33311fbd3c364ede650059563e80|683f75112920adb17c0a077602f4f9ec
darpan_kal.py|darpan_kal.py|c45bb343ac867f322f031da94882413d|fd799a56cf212625cfaadce768d3431d
darpan_kal.html|darpan_kal.html|ec8b64ae8f15c232d390b5ea0b8b266d|f5e279eb26e7f24827f29b79f95b2769
finance_approvals.html|finance_ui/finance_approvals.html|8edc44c51b46e7d7643840b485715c85|b32da7ffe605ce2440414febb8cf7bce"
NEWPIN=a35d04f1badcb840d52ee0ea5afcf250            # bank_standin.py
SCR=""; PLACED=0; HAVE_LOCK=0; HAD_NEW=0; T0=""; RED=""
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
rows() { echo "$TABLE"; }
clean() {
  [ -n "$SCR" ] && rm -rf "$SCR"
  rows | while IFS='|' read -r k d f t; do rm -f "$FIN/$(dirname "$d")/.$(basename "$d").s496"; done
  rm -f "$FIN/.bank_standin.py.s496"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - restoring"
  PLACED=0
  while IFS='|' read -r k d f t; do
    b="$FIN/$d.bak_S496_$(echo "$f" | cut -c1-8)"
    \cp -p "$b" "$FIN/$d"
    if [ "$(m5 "$FIN/$d")" = "$f" ]; then say "   $d back at its old bytes"; else say "   !! $d is NOT its old bytes - put $b back by hand"; fi
  done <<EOF
$TABLE
EOF
  [ "$HAD_NEW" = 0 ] && rm -f "$FIN/bank_standin.py" && say "   bank_standin.py removed"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 9
  say "   finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
on_signal() {
  trap '' INT TERM HUP
  say ""; say "!! interrupted"
  if [ "$PLACED" = 1 ]; then restore "the run was interrupted after placing"; fi
  clean; exit 130
}
trap on_exit EXIT
trap on_signal INT TERM HUP
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 bank_standin.py)" = "$NEWPIN" ] || { say "!! [1/7] the kit's bank_standin.py is not the one this installer names - nothing installed"; exit 1; }
while IFS='|' read -r k d f t; do
  [ "$(m5 "$KDIR/$k")" = "$t" ] || { say "!! [1/7] the kit's $k is not the file this installer names - nothing installed"; exit 1; }
done <<EOF
$TABLE
EOF
"$SPY" -c "import flask, sqlite3" 2>/dev/null || { say "!! [1/7] $SPY lacks flask (the walk needs it) - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
SCR="$(mktemp -d "/tmp/s496_scratch_XXXXXXXX")" || { say "!! [1/7] no scratch folder - nothing installed"; exit 1; }
chmod 700 "$SCR"
say "[1/7] kit gates green (SUMS, KIT_ID, every file's own md5, flask); the build lock is taken"

[ -f "$FIN/bank_standin.py" ] && HAD_NEW=1
AT_TO=1; AT_FROM=1
while IFS='|' read -r k d f t; do
  h="$(m5 "$FIN/$d")"
  [ "$h" = "$t" ] || AT_TO=0
  [ "$h" = "$f" ] || AT_FROM=0
done <<EOF
$TABLE
EOF
if [ "$AT_TO" = 1 ] && [ "$(m5 "$FIN/bank_standin.py")" = "$NEWPIN" ]; then say "-- ALREADY INSTALLED: the six files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; clean; exit 0; fi
if [ "$AT_FROM" != 1 ]; then
  while IFS='|' read -r k d f t; do
    h="$(m5 "$FIN/$d")"; [ "$h" = "$f" ] || say "!! [2/7] $FIN/$d is $h, not $f - another kit changed it after this one was built."
  done <<EOF
$TABLE
EOF
  say "   Nothing installed; tell the assistant, the kit is rebuilt on the new file."; clean; exit 1
fi
if [ "$HAD_NEW" = 1 ] && [ "$(m5 "$FIN/bank_standin.py")" != "$NEWPIN" ]; then say "!! [2/7] $FIN/bank_standin.py is already there and is not this kit's file - nothing installed; tell the assistant."; clean; exit 1; fi
say "[2/7] the five files at the pins this kit was built on; no other bank_standin.py in the way"

mkdir -p "$SCR/c" && \cp -p "$KDIR"/bank_standin.py "$KDIR"/bank_mpr_status.py "$KDIR"/clinic_money.py "$KDIR"/darpan_kal.py "$KDIR"/walk_s496.py "$SCR/c/" \
  || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile "$SCR/c/bank_standin.py" "$SCR/c/bank_mpr_status.py" "$SCR/c/clinic_money.py" "$SCR/c/darpan_kal.py" "$SCR/c/walk_s496.py" 2>"$SCR/compile.err" \
  || { say "!! [3/7] compile failed: $(tail -1 "$SCR/compile.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
rm -rf "$SCR/c"
say "[3/7] the four programs and the walk compile under $SPY"

unchanged() {
  while IFS='|' read -r k d f t; do [ "$(m5 "$FIN/$d")" = "$f" ] || return 1; done <<EOF
$TABLE
EOF
  return 0
}
WOUT="$( cd /tmp && TMPDIR="$SCR" timeout 900 "$SPY" -B "$KDIR/walk_s496.py" --kit "$KDIR" --code "$FIN" --code "$ROOT/marg_ingest" --db "$DB" ${WALK_EXTRA:-} 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^  note|^WALK_S496' | cut -c1-500 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S496 GREEN" || { say "!! [4/7] walk red - nothing installed. Tell the assistant with this output."; echo "$WOUT" | tail -25 | cut -c1-500; clean; exit 1; }
unchanged || { say "!! [4/7] a file changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: with no figure typed and the bank in, the kit's pages are the live pages; then a typed figure's whole life on a copy of the real database -- nothing changes until his confirm, the bank replaces it by itself, no money row moved"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

while IFS='|' read -r k d f t; do
  b="$FIN/$d.bak_S496_$(echo "$f" | cut -c1-8)"
  \cp -p "$FIN/$d" "$b" && [ "$(m5 "$b")" = "$f" ] || { say "!! [5/7] the backup of $d failed - nothing placed"; clean; exit 1; }
done <<EOF
$TABLE
EOF
say "[5/7] backups made beside each file (.bak_S496_<its old md5>)"
while IFS='|' read -r k d f t; do
  s="$FIN/$(dirname "$d")/.$(basename "$d").s496"
  \cp -p "$FIN/$d" "$s" && cat "$KDIR/$k" > "$s" && [ "$(m5 "$s")" = "$t" ] || { say "!! [6/7] could not stage $d - nothing placed"; clean; exit 1; }
done <<EOF
$TABLE
EOF
\cp -p "$FIN/clinic_money.py" "$FIN/.bank_standin.py.s496" && cat "$KDIR/bank_standin.py" > "$FIN/.bank_standin.py.s496" && [ "$(m5 "$FIN/.bank_standin.py.s496")" = "$NEWPIN" ] \
  || { say "!! [6/7] could not stage bank_standin.py - nothing placed"; clean; exit 1; }
PLACED=1
mv -f "$FIN/.bank_standin.py.s496" "$FIN/bank_standin.py" || restore "placing bank_standin.py"
while IFS='|' read -r k d f t; do
  mv -f "$FIN/$(dirname "$d")/.$(basename "$d").s496" "$FIN/$d" || restore "placing $d"
done <<EOF
$TABLE
EOF
while IFS='|' read -r k d f t; do [ "$(m5 "$FIN/$d")" = "$t" ] || restore "md5 read-back of $d"; done <<EOF
$TABLE
EOF
[ "$(m5 "$FIN/bank_standin.py")" = "$NEWPIN" ] || restore "md5 read-back of bank_standin.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
for _w in 1 2 3 4 5 6 7 8 9 10 11 12; do sleep 3; [ "$(health "$FINURL/finance/healthz")" = 200 ] && break; done
sleep 3
post_checks() {
  RED=""
  systemctl is-active --quiet clinic-finance || { RED="clinic-finance not active"; return 1; }
  c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || { RED="finance healthz $c1"; return 1; }
  for u in /finance/clinic/match /finance/clinic/money /finance/clinic/register /finance/clinic/bank/mpr /finance/darpan/kal /finance/approvals /finance/console; do
    c=$(health "$FINURL$u"); case "$c" in 302|401) ;; *) RED="$u answered $c without a login (it must be behind the login gate)"; return 1;; esac
  done
  c=$(curl -s -o /dev/null -m 10 -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data-binary '{}' "$FINURL/finance/darpan/kal/api/pos-total")
  case "$c" in 302|401) ;; *) RED="the new POS-total address answered $c to a caller with no login (it must turn him away)"; return 1;; esac
  if journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted\|bank_standin not beside"; then RED="a part of the finance app did NOT mount"; return 1; fi
  JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError\|ImportError')"
  [ "${JR:-0}" = 0 ] || { RED="clinic-finance journal: $JR error line(s)"; return 1; }
  ( cd "$FIN" && "$SPY" -B -c "
import sqlite3, datetime as dt
import bank_standin as b, bank_mpr_status as m, clinic_money as c, darpan_kal as k
assert b.VERSION == 'S496 1.0' and hasattr(c, 'post_pos_total') and hasattr(c, '_pos_block') and hasattr(k, 'api_s496_pos_total') and hasattr(m, 'expect_hhmm')
con = sqlite3.connect('file:$DB?mode=ro', uri=True, timeout=5); con.row_factory = sqlite3.Row
y = (dt.date.today() - dt.timedelta(days=1)).isoformat()
print('   on this box: units of the statement store: %s · bank expected by %s · tolerance Rs %s' % (', '.join(b.units(con)), m.expect_hhmm(con), b.rupees(b.tolerance_p(con))))
print('   by the statement rows alone, %s reads: %s' % (y, ' · '.join('%s %s' % (b.unit_label(con, u), b.bank_state(con, u, y).replace('_', ' ').upper()) for u in b.units(con))))
" ) || { RED="the placed programs do not load under $SPY"; return 1; }
  return 0
}
post_checks || restore "$RED"
PLACED=0
say "[6/7] placed, md5 read back = the kit's pins · clinic-finance active · healthz 200 · the pages behind the login gate as before · a caller with no login is turned away from the new address · every part mounted · journal clean"
say "[7/7] from now: a day whose bank statement is missing after its time offers ONE optional figure to Darpan and to reception; it counts only after Dr Manoj's Confirm (Clinic money · Approvals > Kal ka hisaab); the bank's own statement replaces it by itself"
clean
say "all green -- $KIT: DONE."
( cd "$FIN" && md5sum bank_standin.py bank_mpr_status.py clinic_money.py darpan_kal.py darpan_kal.html finance_ui/finance_approvals.html )
exit 0
