#!/bin/bash
# =============================================================================
#  install_S321_XRAY_VIEWS.sh · kit S321_XRAY_VIEWS (session 269, 19-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S321_XRAY_VIEWS/install_S321_XRAY_VIEWS.sh
#
#  TWO THINGS, both from the owner's message of 19-Sep:
#
#  1. THE BUTTONS. He pressed Approve and got "page not accessible". Every form on
#     the page carries a relative action, and the page is served without a
#     trailing slash, so a browser posted to /finance/clinic/status -- a route
#     that does not exist. One <base> tag fixes all of them at once, and any form
#     added later as well.
#  2. THE NAMES AND THE PRICES. Every X-ray gains its views ("Knee AP & Lateral
#     view"), chest becomes TWO studies (AP and PA), and every row gets a price
#     from his own rule: 1 view 300 · 2 views 500 · on 11 x 14 400 and 600 ·
#     wrist three views 800 · PBH single on 11 x 14 400 · chest 300 each.
#     A row he has already edited himself is left alone, for ever.
#
#  Gates: kit SUMS + KIT_ID -> the walk, which renders the page through Flask and
#  POSTS to every button the way a BROWSER resolves it (23 checks, 3 negative
#  controls, one of them reproducing his own 404) -> read-only --check -> the
#  module patched, py_compiled with both pythons, service restarted, page probed
#  -> the table's own backup, then the rename/price pass, read back.
#  Any red after the module is placed: the backup is restored and the service
#  restarted.
# =============================================================================
set -u
KIT="S321_XRAY_VIEWS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
TARGET="$FIN/owner_sheets.py"
DB="${DB:-$FIN/finance.db}"
SVC="${SVC:-clinic-finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s321_$STAMP"
say() { echo "$@"; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
[ -f "$TARGET" ] || { say "!! preflight: $TARGET is not there - nothing changed"; exit 1; }
[ -f "$DB" ] || { say "!! preflight: $DB is not there - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/7] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
WOUT="$( cd /tmp && timeout 240 "$VPY" -B "$KDIR/walk_s321.py" "--file=$TARGET" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$WOUT" in
  *"WALK OK"*) say "[2/7] $(echo "$WOUT" | grep -o 'WALK OK -- [0-9]* checks') (rendered and posted on a copy)" ;;
  *) say "!! [2/7] the walk is red against a copy of the live page:"; say "    $WOUT"; rm -rf "$T"; exit 1 ;;
esac

say "[3/7] the page module as it stands now (read-only):"
"$VPY" -B patch_owner_sheets_s321.py --check "--file=$TARGET" | sed 's/^/    /'

BAK="$T/owner_sheets.before"
\cp -p "$TARGET" "$BAK"
restore() { say "!! restoring $TARGET"; \cp -p "$BAK" "$TARGET";
            systemctl restart "$SVC" >/dev/null 2>&1 || true; sleep 4;
            say "!! restored: owner_sheets $(m5 "$TARGET") · $SVC $(systemctl is-active "$SVC")"; exit 1; }

say "[4/7] patching the page:"
AOUT="$("$VPY" -B patch_owner_sheets_s321.py --apply "--file=$TARGET" 2>&1)"
echo "$AOUT" | sed 's/^/    /'
case "$AOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [4/7] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1 ;;
esac
"$SPY" -m py_compile "$TARGET" || restore
"$VPY" -m py_compile "$TARGET" || restore

systemctl restart "$SVC" || restore
sleep 4
systemctl is-active --quiet "$SVC" || restore
C1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
C2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/clinic/sheets)
say "[5/7] $SVC restarted · healthz $C1 · the page $C2 (302 = the login redirect a curl gets)"
[ "$C1" = "200" ] || restore

say "[6/7] the X-ray list, read-only first:"
"$VPY" -B update_xray_s321.py --db "$DB" | sed 's/^/    /'
SQLBAK="$FIN/owner_service_before_S321_$STAMP.sql"
"$VPY" -B - "$DB" "$SQLBAK" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    for line in con.iterdump():
        if "owner_service" in line:
            fh.write(line + "\n")
print("    table backup: %s" % sys.argv[2])
PY
say "[6/7] applying:"
UOUT="$("$VPY" -B update_xray_s321.py --db "$DB" --apply 2>&1)"
echo "$UOUT" | sed 's/^/    /'
case "$UOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [6/7] the list was NOT changed (the page fix above stays). Backup: $SQLBAK"; rm -rf "$T"; exit 1 ;;
esac

say "[7/7] what he will see now:"
"$VPY" -B - "$DB" <<'PY' | sed 's/^/    /'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); con.row_factory = sqlite3.Row
rows = list(con.execute("SELECT name, price_p, status FROM owner_service "
                        "WHERE kind='xray' ORDER BY name"))
print("%d X-ray line(s):" % len(rows))
for r in rows:
    print("  %-46s %6.0f  %s" % (r["name"], r["price_p"] / 100.0, r["status"]))
PY
rm -rf "$T"
say "$KIT: DONE -- the buttons work and every X-ray has its views and a price"
say "open: https://followup.dr-manoj.in/finance/clinic/sheets"
