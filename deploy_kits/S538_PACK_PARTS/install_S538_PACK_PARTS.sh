#!/bin/bash
# =============================================================================
#  install_S538_PACK_PARTS.sh · kit S538 (session 311, 12-Oct-2026) · D714 · F-867, F-868, F-869
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S538_PACK_PARTS/install_S538_PACK_PARTS.sh
#
#  THE OWNER, 06:11-06:29 IST 12-Oct, on September's pack: the split column "is confusing and does not clarify us";
#  "any other wallet payment not coming through the email data is not a wallet payment ... only for the Consultation fees".
#  and, 07:53 IST: the days that differ are NOT raised to reception -- "keep it aside and populate it in one place where I can see".
#   /root/finance/packs.py 368aa68c -> 382081fa and packs.html d25452a5 -> 49906969, both built HERE from the live bytes by
#   make_s538.py (10 + 1 counted edits):
#   1  the income sheet counts every split by its real parts; the Razorpay booking (a consultation line with pay_...) apart,
#      the consultation fee only; any other 'Wallet' an entry error, decided against the bank
#   2  the bank check (Docterz online + card against the card machine's next-day settlement, with the month's totals) on the
#      owner's packs page ONLY -- never in the accountants' workbook or mail, never on Shavez's checklist
#   3  the payment digest one row per charge (a renewal / confirmation and its receipt), labelled payment papers
#  Restarts clinic-finance. clinic_money.py, finance_clinic_day.py, clinic_register.py, clinic_day_pdf.py are not touched.
#  ORDER: gates -> pin (ALREADY first) -> compile -> rebuild from the live bytes -> walk (made-up + the old file red +
#  September on a copy of the database) -> DRY stops -> backup -> place -> restart -> health -> undo line.
# =============================================================================
set -u
KIT="S538_PACK_PARTS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; SVC="${SVC:-clinic-finance}"
PK="$FIN/packs.py"; PH="$FIN/packs.html"
FROM_PK=368aa68cfd03176dce99816043390ea1; TO_PK=382081fa886000065e648d63dc793ece
FROM_PH=d25452a51f2f5fdd5c1e2b39b54bd9ff; TO_PH=499069693a21de84fbad09d427a5fb0c
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s538_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
BAK_PK="$PK.bak_S538_${FROM_PK:0:8}"; BAK_PH="$PH.bak_S538_${FROM_PH:0:8}"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting packs.py and packs.html back"
  [ -f "$BAK_PK" ] && \cp -p "$BAK_PK" "$PK"
  [ -f "$BAK_PH" ] && \cp -p "$BAK_PH" "$PH"
  systemctl restart "$SVC" || true; sleep 3
  say "   $PK $(m5 "$PK") (expected $FROM_PK) · $PH $(m5 "$PH") (expected $FROM_PH)"
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
[ "$(m5 packs.py)" = "$TO_PK" ] && [ "$(m5 packs.html)" = "$TO_PH" ] || { say "!! [1/8] the kit's files are not their predicted md5 - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/8] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/8] kit gates green; the build lock is ours"

for f in "$PK" "$PH"; do [ -f "$f" ] || { say "!! [2/8] $f is not there - nothing installed"; exit 1; }; done
CPK="$(m5 "$PK")"; CPH="$(m5 "$PH")"
if [ "$CPK" = "$TO_PK" ] && [ "$CPH" = "$TO_PH" ]; then say "-- ALREADY INSTALLED: both files are the kit's. Nothing written."; exit 0; fi
[ "$CPK" = "$FROM_PK" ] || { say "!! [2/8] $PK is $CPK, expected $FROM_PK - nothing installed"; exit 1; }
[ "$CPH" = "$FROM_PH" ] || { say "!! [2/8] $PH is $CPH, expected $FROM_PH - nothing installed"; exit 1; }
[ -f "$DB" ] || { say "!! [2/8] $DB is not there - nothing installed"; exit 1; }
say "[2/8] two live pins exact (packs.py ${FROM_PK:0:8}, packs.html ${FROM_PH:0:8})"

mkdir -p "$SCR/old" "$SCR/new" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"; export PYTHONDONTWRITEBYTECODE=1
"$APY" -m py_compile packs.py walk_s538.py make_s538.py || { say "!! [3/8] compile failed - nothing installed"; exit 1; }
say "[3/8] py_compile green (3 files)"

"$APY" -B make_s538.py "$PK" "$SCR/new/packs.py" "$PH" "$SCR/new/packs.html" >/dev/null || { say "!! [4/8] the builder refused a live file - nothing installed"; exit 1; }
[ "$(m5 "$SCR/new/packs.py")" = "$TO_PK" ] && [ "$(m5 "$SCR/new/packs.html")" = "$TO_PH" ] \
  || { say "!! [4/8] rebuilt from the live bytes they are not the kit's files - nothing installed"; exit 1; }
\cp -p "$PK" "$SCR/old/packs.py"; \cp -p "$PH" "$SCR/old/packs.html"
say "[4/8] rebuilt from the live bytes: byte for byte the kit's packs.py and packs.html"

"$APY" - "$DB" "$SCR/copy.db" <<'PYEOF' || { say "!! [5/8] could not take a copy of the database - nothing installed"; exit 1; }
import sqlite3, sys
src = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
dst = sqlite3.connect(sys.argv[2])
src.backup(dst)
dst.close(); src.close()
PYEOF
WOUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s538.py" "$SCR/new" --db "$SCR/copy.db" --month 2026-09 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/walk_s538.py" "$SCR/old" --expect-red 2>&1 )"; RRC=$?
rm -f "$SCR/copy.db"
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [5/8] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -8; say "   nothing installed"; exit 1
fi
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK"; then
  say "!! [5/8] the negative control did not go red on the old file - the walk proves nothing; nothing installed"; exit 1
fi
say "[5/8] $(echo "$WOUT" | grep "^WALK OK" | tail -1)"
say "      negative control: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c1-110)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$PK" "$BAK_PK" && \cp -p "$PH" "$BAK_PH" || { say "!! [6/8] backup failed - nothing placed"; exit 1; }
[ "$(m5 "$BAK_PK")" = "$FROM_PK" ] && [ "$(m5 "$BAK_PH")" = "$FROM_PH" ] || { say "!! [6/8] a backup is not the live file - nothing placed"; exit 1; }
\cp -p "$SCR/new/packs.py" "$FIN/.packs.py.s538" && \cp -p "$SCR/new/packs.html" "$FIN/.packs.html.s538" \
  || { rm -f "$FIN/.packs.py.s538" "$FIN/.packs.html.s538"; say "!! [6/8] could not stage the files - nothing placed"; exit 1; }
PLACED=1
mv -f "$FIN/.packs.py.s538" "$PK" || restore "placing packs.py"
mv -f "$FIN/.packs.html.s538" "$PH" || restore "placing packs.html"
[ "$(m5 "$PK")" = "$TO_PK" ] && [ "$(m5 "$PH")" = "$TO_PH" ] || restore "the files did not land at their pins"
say "[6/8] backups beside both files; packs.py and packs.html placed"

systemctl restart "$SVC" || restore "restart $SVC"
c1=000
for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 3; c1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"); [ "$c1" = 200 ] && break; done
c2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/packs")
systemctl is-active --quiet "$SVC" || restore "$SVC is not active"
{ [ "$c1" = 200 ] && { [ "$c2" = 302 ] || [ "$c2" = 401 ] || [ "$c2" = 303 ]; }; } || restore "finance health $c1 / packs $c2"
say "[7/8] $SVC active - health $c1 - the packs page without a login $c2 (302 expected)"
PLACED=0
md5sum "$PK" "$PH"
say "[8/8] $KIT: DONE"
say "read next: https://followup.dr-manoj.in/finance/packs?month=2026-09"
say "undo: \\cp -p $BAK_PK $PK && \\cp -p $BAK_PH $PH && systemctl restart $SVC"
