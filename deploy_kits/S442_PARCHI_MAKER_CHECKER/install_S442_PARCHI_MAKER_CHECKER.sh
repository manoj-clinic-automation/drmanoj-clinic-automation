#!/bin/bash
# =============================================================================
#  install_S442_PARCHI_MAKER_CHECKER.sh · kit S442_PARCHI_MAKER_CHECKER (session 287, 01-Oct-2026, D644 · F-663 · F-664 · F-668) · PARENT
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S442_PARCHI_MAKER_CHECKER/install_S442_PARCHI_MAKER_CHECKER.sh
#  (DRY=1 runs every gate and the walk on a scratch copy, shows the 17 parchis it would move, and places nothing.)
#
#  THE OWNER, 30-Sep / 01-Oct: "reception enters, Shavez or me approve".
#   * Chhoot Rs ___ or Free on any X-ray or procedure line, with a reason from a pick (staff/family · poor patient ·
#     repeat/redo · doctor's instruction · other). Shavez, the owner or Dr Bhawna approve; nobody approves their own.
#     The patient never waits; a rejected one goes to the night report.
#   * The night check: Docterz below the rate with no chhoot written -> "discount not written", to the person who logged it.
#   * Radd after billing (Docterz cannot cancel): the clinic ID + money returned / never taken, approved like a discount;
#     the Docterz line then leaves the expected cash / UPI (clinic_money) and shows under "Cancelled after billing".
#   * The late parchi: the screen proposes its day (the ID in the last Docterz day, or a number below today's first).
#   * The owner's page: /finance/slips/discounts -- the month's discounts and free lines, who asked, who approved.
#  FILES:  /root/finance/slip_log.py      fa2d21bf -> caef39f6   PARENT
#          /root/finance/clinic_money.py  a92fc4c6 -> c56d3331   PARENT (the read side only: the radd line out of the expected money)
#          /root/finance/slip_adjust.py   NEW      -> 41c55a99
#  DATA:   finance.db (backed up first): the table slip_adjust (made on first request); setting slips.approvers seeded;
#          F-663 -- OPD parchis 19493-19509 (17, entered 29-Sep 08:47-09:02 under "Aaj") moved to 28-Sep, each audited,
#          ONLY if exactly those 17 are still on 29-Sep; otherwise nothing is moved and the count is said.
#  Restarts clinic-finance.
# =============================================================================
set -u
KIT="S442_PARCHI_MAKER_CHECKER"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"
FIN="$ROOT/finance"; POR="$ROOT/portal"
DBF="${FINANCE_DB:-$FIN/finance.db}"
STAMP="$(date +%Y%m%d_%H%M%S)"
WALK="/tmp/s442_walk_$STAMP"
declare -A FROM=( [slip_log.py]=fa2d21bfbf5fae297857e7da58a1ceae [clinic_money.py]=a92fc4c6236fda9ec3a7c0ed7bac68f5 [slip_adjust.py]=NEW )
ORDER=(slip_adjust.py slip_log.py clinic_money.py)
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
copydb() { "$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
clean() { find "$KDIR" "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$VPY" -c "import flask" 2>/dev/null || { say "!! [1/8] the venv python lacks flask; nothing installed"; exit 1; }
[ -f "$DBF" ] || { say "!! [1/8] $DBF is not there; nothing installed"; exit 1; }
say "[1/8] kit gates green (SUMS, KIT_ID, the venv's flask, finance.db)"
declare -A TO
while read -r h f; do TO[$(basename "$f")]="$h"; done < <(grep ' built/' SUMS.md5)
ALL=1; for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "-- ALREADY INSTALLED: the three files are at the kit's pins; clinic-finance $(systemctl is-active clinic-finance)"; exit 0; fi
for f in "${ORDER[@]}"; do
  if [ "${FROM[$f]}" = NEW ]; then [ ! -e "$FIN/$f" ] || { say "!! [2/8] $FIN/$f already exists - nothing installed"; exit 1; }
  else [ "$(m5 "$FIN/$f")" = "${FROM[$f]}" ] || { say "!! [2/8] $FIN/$f is $(m5 "$FIN/$f"), not its FROM pin ${FROM[$f]} - someone changed it since the build; nothing installed"; exit 1; }; fi
done
say "[2/8] slip_log.py and clinic_money.py at their FROM pins; slip_adjust.py not there yet"
( "$SPY" -m py_compile built/*.py walk_s442.py && "$VPY" -m py_compile built/*.py walk_s442.py ) 2>/dev/null || { say "!! [3/8] compile failed - nothing installed"; clean; exit 1; }
clean
say "[3/8] compiles on /usr/bin/python3 and the venv python"
for side in new old; do
  mkdir -p "$WALK/$side/finance_ui" || exit 1
  cp -p "$FIN"/*.py "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$WALK/$side/" 2>/dev/null; cp -rp "$FIN/finance_ui/." "$WALK/$side/finance_ui/"
  [ -d "$FIN/spine" ] && { mkdir -p "$WALK/$side/spine"; cp -p "$FIN"/spine/*.py "$FIN"/spine/*.json "$WALK/$side/spine/" 2>/dev/null; }
done
cp -p built/*.py "$WALK/new/"
copydb "$DBF" "$WALK/scratch_fin.db" || { say "!! [4/8] no scratch copy - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd "$WALK" && W_PORTAL="$POR" timeout 1500 "$VPY" -B "$KDIR/walk_s442.py" --new "$WALK/new" --old "$WALK/old" --db "$WALK/scratch_fin.db" 2>&1 )"
echo "$WOUT" | grep -v '^-- ' | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S442 GREEN" || { say "!! [4/8] walk red - nothing installed"; echo "$WOUT" | grep '^-- ' | cut -c1-800; clean; rm -rf "$WALK"; exit 1; }
clean
say "[4/8] walk_s442 green on a scratch copy of finance.db, its negative control red on the box as it is (above)"
MOVE='
import sqlite3, sys, json, datetime
db = sys.argv[1]; apply_ = sys.argv[2] == "1"; app = sys.argv[3]
sys.path.insert(0, app)
c = sqlite3.connect(db, timeout=30); c.row_factory = sqlite3.Row
rows = c.execute("SELECT id, slip_no, clinic_id, is_new FROM slip WHERE series=\"opd\" AND slip_no BETWEEN 19493 AND 19509 AND day=\"2026-09-29\" AND state=\"ok\" ORDER BY slip_no").fetchall()
moved = c.execute("SELECT COUNT(*) FROM slip WHERE series=\"opd\" AND slip_no BETWEEN 19493 AND 19509 AND day=\"2026-09-28\" AND state=\"ok\"").fetchone()[0]
print("   F-663: OPD 19493-19509 on 29-Sep: %d (expected 17) · already on 28-Sep: %d" % (len(rows), moved))
if len(rows) != 17:
    print("   F-663: NOT moved -- the 17 are not all still on 29-Sep exactly; nothing changed"); sys.exit(0)
import slip_log
now = datetime.datetime.now().replace(microsecond=0).isoformat()
for r in rows:
    new = 1 if (r["clinic_id"] and slip_log.is_new_id(c, r["clinic_id"], "2026-09-28")) else 0
    print("   %s %d  29-Sep -> 28-Sep%s" % ("move" if apply_ else "would move", r["slip_no"], " (new patient on 28-Sep)" if new != r["is_new"] and new else ""))
    if apply_:
        c.execute("UPDATE slip SET day=\"2026-09-28\", is_new=?, updated_by=\"S442 (F-663)\", updated_at=? WHERE id=?", (new, now.replace("T", " "), r["id"]))
        c.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, by_whom, at) VALUES (?,?,?,?,?,?,?)",
                  ("slip", r["id"], "slip_day_moved", json.dumps({"day": "2026-09-29", "is_new": r["is_new"]}),
                   json.dumps({"day": "2026-09-28", "is_new": new, "why": "F-663: entered 29-Sep 08:47-09:02 under Aaj; 28-Sep had 21 Docterz consult patients and 5 slips"}),
                   "S442 install", now))
if apply_:
    c.commit(); print("   F-663: 17 parchis moved to 28-Sep, each in audit_log (slip_day_moved)")
'
if [ "${DRY:-0}" = 1 ]; then
  copydb "$DBF" "$WALK/fig.db" && ( cd "$FIN" && "$SPY" -B -c "$MOVE" "$WALK/fig.db" 0 "$WALK/new" 2>&1 )
  say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted, nothing moved"; clean; rm -rf "$WALK"; exit 0
fi
copydb "$DBF" "$FIN/finance.db.bak_S442_$STAMP" || { say "!! [5/8] finance.db backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
declare -A BAK
for f in "${ORDER[@]}"; do
  [ "${FROM[$f]}" = NEW ] && { BAK[$f]=""; continue; }
  BAK[$f]="$FIN/$f.bak_S442_$(m5 "$FIN/$f" | cut -c1-8)"; \cp -p "$FIN/$f" "${BAK[$f]}" || { say "!! [5/8] backup failed - nothing placed"; rm -rf "$WALK"; exit 1; }
done
say "[5/8] finance.db.bak_S442_$STAMP made (backup API); .bak_S442_<from8> beside the two files"
restore() {
  say "!! RED after placing ($1) - restoring the files byte-identically"
  for f in "${ORDER[@]}"; do if [ -n "${BAK[$f]}" ]; then \cp -p "${BAK[$f]}" "$FIN/$f"; else rm -f "$FIN/$f"; fi; done
  systemctl restart clinic-finance || true; sleep 6
  for f in "${ORDER[@]}"; do say "   $FIN/$f $(m5 "$FIN/$f")"; done
  say "   finance healthz $(health http://127.0.0.1:8106/finance/healthz) · the database backup stays: $FIN/finance.db.bak_S442_$STAMP"
  clean; rm -rf "$WALK"; exit 1
}
for f in "${ORDER[@]}"; do \cp -p "built/$f" "$FIN/$f" || restore "copy"; done
for f in "${ORDER[@]}"; do [ "$(m5 "$FIN/$f")" = "${TO[$f]}" ] || restore "md5 read-back"; done
say "[6/8] placed; all three md5s read back = the kit's pins"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 7
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health http://127.0.0.1:8106/finance/healthz); c2=$(health http://127.0.0.1:8106/finance/slips); c3=$(health http://127.0.0.1:8106/finance/slips/discounts)
say "health : finance healthz $c1 · /finance/slips $c2 · /finance/slips/discounts $c3 (200 'not permitted' page or a 302/401 login gate)"
[ "$c1" = 200 ] || restore "finance health"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a finance module NOT mounted"
say "[7/8] clinic-finance active; healthz 200; nothing 'NOT mounted'"
( cd "$FIN" && "$SPY" -B -c "
import sqlite3; c=sqlite3.connect('$DBF', timeout=30)
c.execute(\"CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)\")
c.execute(\"INSERT OR IGNORE INTO setting (key, value, note) VALUES ('slips.approvers','shavez,manoj,bhawna','S442 D644: who approves a chhoot / free / radd (nobody their own)')\")
c.commit(); print('   slips.approvers =', c.execute(\"SELECT value FROM setting WHERE key='slips.approvers'\").fetchone()[0])
" && "$SPY" -B -c "$MOVE" "$DBF" 1 "$FIN" ) 2>&1 || restore "the data step"
say "[8/8] the approvers seeded; F-663 handled (above)"
clean; rm -rf "$WALK"
for f in "${ORDER[@]}"; do md5sum "$FIN/$f"; done
say "$KIT: DONE -- https://followup.dr-manoj.in/finance/slips · https://followup.dr-manoj.in/finance/slips/discounts"
