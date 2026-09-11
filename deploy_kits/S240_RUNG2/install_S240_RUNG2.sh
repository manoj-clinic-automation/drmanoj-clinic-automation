#!/bin/bash
# =============================================================================
#  install_S240_RUNG2.sh · kit S240_RUNG2 · T1 installed, then Rung 2 (the attribution)
#
#  Run by:  bash /root/deploy/vps_deploy.sh S240_RUNG2
#
#  1  T1 -- the owner's 93 discount rulings (kit S236_DISCOUNT, published 09-Sep, never installed):
#     its own gate, its own backup, its own 43 selftests, then the seed. Skipped if already in.
#  2  Rung 2 -- sale_attribution.py: every bill's discount put on the line it belongs to, by the
#     rulings. Three NEW tables, rebuilt in full each run. NOTHING reads them yet -- no screen,
#     no figure changes (that is Rung 3, on the owner's word).
#     cron: every 30 min 09-23 if anything moved, and 23:55 always.
#  No service restart. No live file replaced. finance_app.py, purchase_app.py untouched.
# =============================================================================
set -u
KIT="S240_RUNG2"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="/usr/bin/python3"
FIN="${FINANCE_DIR:-/root/finance}"
DB="$FIN/finance.db"
KITS="${REPO_KITS:-$(dirname "$KDIR")}"
STAMP="$(date +%Y%m%d-%H%M%S)"
SPINE_EXPECT="b5956f59464671f23dc376391f9e8bae"
red() { echo "!! RED -- $*"; echo "   no screen or figure was changed by this kit"; exit 1; }

cd "$KDIR" || red "cannot enter the kit folder"
md5sum -c SUMS.md5 >/dev/null 2>&1 || red "SUMS.md5 gate failed"
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || red "KIT_ID names a different kit"
[ "$(awk 'NR==1{print $2}' KIT_ID.txt)" = "$(md5sum sale_attribution.py | awk '{print $1}')" ] || red "KIT_ID does not match sale_attribution.py (F-88)"
echo "-- gates green: SUMS.md5 and KIT_ID.txt"

[ "$(md5sum $FIN/marg_spine.py 2>/dev/null | awk '{print $1}')" = "$SPINE_EXPECT" ] || red "$FIN/marg_spine.py is not the S240 copy $SPINE_EXPECT"
$PY - "$DB" <<'PYEOF' || red "Rung 1 is not in: sale_bill is missing or empty"
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
n = c.execute("SELECT COUNT(*), COUNT(DISTINCT business_date) FROM sale_bill").fetchone()
assert n[0] > 0
print("-- Rung 1 present: sale_bill %d bills over %d days" % n)
PYEOF

# ---- 1. T1
HAS_T1="$($PY -c "import sqlite3,sys;c=sqlite3.connect('file:$DB?mode=ro',uri=True);print(c.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE name='marg_item_discount'\").fetchone()[0])")"
if [ "$HAS_T1" = "1" ]; then
  echo "-- T1 already installed -- left alone"
else
  T1="$KITS/S236_DISCOUNT"
  ( cd "$T1" && md5sum -c KIT_MANIFEST.md5 >/dev/null 2>&1 ) || red "the S236_DISCOUNT kit gate failed (checked from inside its folder)"
  [ "$(md5sum "$KITS/S229_ITEM_SPINE/marg_spine.py" | awk '{print $1}')" = "$SPINE_EXPECT" ] || red "the spine beside T1 is not $SPINE_EXPECT"
  echo "-- T1 kit gate green (from inside its folder); installing the 93 rulings"
  OUT="$(cd "$T1" && $PY -B marg_discount.py --db "$DB" --install 2>&1)"; RC=$?
  echo "$OUT" | tail -24 | sed 's/^/   /'
  [ $RC -eq 0 ] || red "T1 install returned $RC"
fi

# ---- 2. Rung 2
OUT="$(cd "$KDIR" && PYTHONPATH="$FIN" $PY -B sale_attribution.py --selftest 2>&1)" || red "selftest failed
$OUT"
echo "-- $(echo "$OUT" | tail -1)"
$PY -m py_compile sale_attribution.py || red "py_compile"
mkdir -p "${BACKUP_DIR:-/root/backups/finance}"
$PY - "$DB" "${BACKUP_DIR:-/root/backups/finance}/finance_preS240R2_$STAMP.db" <<'PYEOF' || red "database backup failed"
import sqlite3, sys
s = sqlite3.connect(sys.argv[1]); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
print("-- database copied: " + sys.argv[2])
PYEOF
if [ -f "$FIN/sale_attribution.py" ] && ! cmp -s sale_attribution.py "$FIN/sale_attribution.py"; then \cp -f "$FIN/sale_attribution.py" "$FIN/sale_attribution.py.bak_S240_$STAMP"; fi
\cp -f sale_attribution.py "$FIN/sale_attribution.py"
[ "$(md5sum $FIN/sale_attribution.py | awk '{print $1}')" = "$(md5sum sale_attribution.py | awk '{print $1}')" ] || red "sale_attribution.py did not land"
echo ""
echo "================ RUNG 2 -- first run ================"
cd "$FIN" && $PY -B sale_attribution.py --db "$DB" --build 2>&1 || red "the first run failed"
echo "---------------- the fixture bills ----------------"
$PY - "$DB" <<'PYEOF'
import sqlite3, sys
c = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
for b in ("A003160", "A003250", "A003251", "A003181", "A003278", "A003136", "A003333", "A003495"):
    r = c.execute("SELECT gross_p, disc_p, attributed_p, residual_p, verdict FROM sale_bill_attrib WHERE bill_no=?", (b,)).fetchone()
    print("  %s  %s" % (b, "not in the window" if not r else
          "gross %.2f  discount %.2f  on its lines %.2f  left on the bill %.2f  (%s)" % (r[0]/100., r[1]/100., r[2]/100., r[3]/100., r[4])))
PYEOF
echo "===================================================="

# ---- cron + freshness
TMPC="$(mktemp)"; crontab -l 2>/dev/null | grep -v '# S240_RUNG2' > "$TMPC"
cat >> "$TMPC" <<'CRON'
*/30 9-23 * * * cd /root/finance && /usr/bin/python3 -B sale_attribution.py --db /root/finance/finance.db --build --if-changed >> /root/finance/sale_attribution.log 2>&1 # S240_RUNG2
55 23 * * * cd /root/finance && /usr/bin/python3 -B sale_attribution.py --db /root/finance/finance.db --build >> /root/finance/sale_attribution.log 2>&1 # S240_RUNG2
CRON
crontab "$TMPC" && rm -f "$TMPC"
echo "-- cron: $(crontab -l | grep -c '# S240_RUNG2') RUNG2 lines"
LEGS="$FIN/freshness_legs.json"
if [ -f "$LEGS" ]; then
  \cp -f "$LEGS" "$LEGS.bak_S240R2_$STAMP"
  $PY - "$LEGS" <<'PYEOF'
import json, sys
p = sys.argv[1]; d = json.load(open(p))
leg = {"name": "Sale discount attribution (S240)", "group": "Marg lane", "kind": "sqlite_max",
       "target": "/root/finance/finance.db", "table": "sale_attrib_run", "column": "finished_at",
       "max_age_h": 30, "note": "sale_attribution.py, 23:55 always"}
if leg["name"] not in {l.get("name") for l in d["legs"]}:
    d["legs"].append(leg); json.dump(d, open(p, "w"), indent=1, ensure_ascii=False)
print("-- freshness legs: now %d" % len(d["legs"]))
PYEOF
fi
echo ""
echo "PINS  sale_attribution.py $(md5sum $FIN/sale_attribution.py | awk '{print $1}')"
echo ""
echo "$KIT GREEN -- T1 and Rung 2 in. Nothing on any screen changed."
