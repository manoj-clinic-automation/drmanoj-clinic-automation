#!/bin/bash
# =============================================================================
#  install_S322_PROC_SIDE.sh · kit S322_PROC_SIDE (session 269, 19-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S322_PROC_SIDE/install_S322_PROC_SIDE.sh
#
#  His instruction of 19-Sep: the word FIBRE in every cast and slab · every
#  plaster variant to exist BOTH as cast and as slab, because the charges differ ·
#  right / left asked on the ILI lines, and on the X-rays where it applies.
#
#  Side is a marker on the line, not two more lines: the two sides are one line at
#  one charge, and which side it was belongs to the visit. He can flip it on any
#  row from the page.
#
#  Needs S321 in place. Page: /root/finance/owner_sheets.py a4e8694e -> 70963a91.
#  Data: ten plaster lines renamed to their fibre cast (U slab to its fibre slab),
#  their twins added with the same consumables, side asked on the cast/slab and
#  ILI lines and on the limb X-rays. Procedure prices are left EMPTY -- he has not
#  stated them. Nothing is deleted; a line he has edited himself is never touched.
#
#  Gates: kit SUMS + KIT_ID -> the walk (30 checks, 4 negative controls; it renders
#  the page and POSTs its own buttons the way a browser resolves them) -> read-only
#  --check -> the page patched, py_compiled with both pythons, service restarted,
#  probed -> the table dumped to a .sql beside the database -> the list rebuilt,
#  read back -> printed section by section. Any red after the page is placed
#  restores the backup and restarts.
# =============================================================================
set -u
KIT="S322_PROC_SIDE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
TARGET="$FIN/owner_sheets.py"
DB="${DB:-$FIN/finance.db}"
SVC="${SVC:-clinic-finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s322_$STAMP"
say() { echo "$@"; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$VPY" ] || { say "!! preflight: $VPY not executable - nothing changed"; exit 1; }
[ -f "$TARGET" ] || { say "!! preflight: $TARGET is not there - nothing changed"; exit 1; }
[ -f "$DB" ] || { say "!! preflight: $DB is not there - nothing changed"; exit 1; }
grep -q "S321" "$TARGET" || { say "!! preflight: the page does not carry S321 yet - install S321 first, nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/7] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
WOUT="$( cd /tmp && timeout 240 "$VPY" -B "$KDIR/walk_s322.py" "--file=$TARGET" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$WOUT" in
  *"WALK OK"*) say "[2/7] $(echo "$WOUT" | grep -o 'WALK OK -- [0-9]* checks') (rendered, clicked, on a copy)" ;;
  *) say "!! [2/7] the walk is red against a copy of the live page:"; say "    $WOUT"; rm -rf "$T"; exit 1 ;;
esac

say "[3/7] the page as it stands now (read-only):"
"$VPY" -B patch_owner_sheets_s322.py --check "--file=$TARGET" | sed 's/^/    /'

BAK="$T/owner_sheets.before"
\cp -p "$TARGET" "$BAK"
restore() { say "!! restoring $TARGET"; \cp -p "$BAK" "$TARGET";
            systemctl restart "$SVC" >/dev/null 2>&1 || true; sleep 4;
            say "!! restored: owner_sheets $(m5 "$TARGET") · $SVC $(systemctl is-active "$SVC")"; exit 1; }

say "[4/7] patching the page:"
AOUT="$("$VPY" -B patch_owner_sheets_s322.py --apply "--file=$TARGET" 2>&1)"
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
C2=$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:8106/finance/clinic/sheets)
say "[5/7] $SVC restarted · healthz $C1 · the page $C2 (302 = the login redirect a curl gets)"
[ "$C1" = "200" ] || restore

SQLBAK="$FIN/owner_service_before_S322_$STAMP.sql"
"$VPY" -B - "$DB" "$SQLBAK" <<'PY'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1])
with open(sys.argv[2], "w", encoding="utf-8") as fh:
    for line in con.iterdump():
        if "owner_service" in line:
            fh.write(line + "\n")
print("    table backup: %s" % sys.argv[2])
PY
say "[6/7] the procedures, read-only first:"
"$VPY" -B update_proc_s322.py --db "$DB" | sed 's/^/    /'
say "[6/7] applying:"
UOUT="$("$VPY" -B update_proc_s322.py --db "$DB" --apply 2>&1)"
echo "$UOUT" | sed 's/^/    /'
case "$UOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [6/7] the list was NOT changed (the page change above stays). Backup: $SQLBAK"; rm -rf "$T"; exit 1 ;;
esac

say "[7/7] his procedure list, section by section:"
"$VPY" -B - "$DB" <<'PY' | sed 's/^/    /'
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); con.row_factory = sqlite3.Row
last = None
for r in con.execute("SELECT grp, name, price_p, side, status FROM owner_service "
                     "WHERE kind='proc' ORDER BY grp, name"):
    if r["grp"] != last:
        last = r["grp"]
        print("  -- %s" % (last or "(no section)"))
    print("     %-34s %6s  %-11s %s"
          % (r["name"], ("%.0f" % (r["price_p"] / 100.0)) if r["price_p"] else "-",
             "asks R / L" if r["side"] == "ask" else "", r["status"]))
n = con.execute("SELECT COUNT(*) c FROM owner_service WHERE kind='xray' AND side='ask'").fetchone()["c"]
print("  X-rays that now ask a side: %d" % n)
PY
rm -rf "$T"
say "$KIT: DONE"
say "open: https://followup.dr-manoj.in/finance/clinic/sheets"
