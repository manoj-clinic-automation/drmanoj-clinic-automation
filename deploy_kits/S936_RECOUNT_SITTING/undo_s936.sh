#!/bin/bash
# undo_s936.sh -- kit S936_RECOUNT_SITTING: the four files back from the install's backups, clinic-finance restarted, and TRAMATEE's four rows
# (point 388, loss line 7, trace 35, the 23-11 count) put back as they were from the repair's own record of them. The new columns stay (harmless).
# A count held for a recount after the install stays in the table with status 'recount'; the old files read it as an ordinary count again.
set -u
ROOT="${ROOT:-/root}"; FSVC="${FSVC:-clinic-finance}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"; BEFORE_JSON="${BEFORE_JSON:-$ROOT/finance/.s936_repair_before.json}"
NAMES=("finance/stock_watch.py" "finance/stock_figure.py" "finance/stockmatch.py" "finance/stockmatch.html")
FROMS=("048b51df91a5dc8babbbc6bca983d5de" "d7fac10cec56b0db170da3d40326a0c6" "e459af2a05a0451d81e6c6fc0c62082f" "2a985d94217b05cdb9b5e657db3b1290")
for k in 0 1 2 3; do b="$ROOT/${NAMES[$k]}.bak_S936_${FROMS[$k]:0:8}"
  [ -f "$b" ] && [ "$(md5sum "$b" | awk '{print $1}')" = "${FROMS[$k]}" ] || { echo "!! no good backup $b - nothing undone. Tell Claude."; exit 1; }; done
for k in 0 1 2 3; do \cp -p "$ROOT/${NAMES[$k]}.bak_S936_${FROMS[$k]:0:8}" "$ROOT/${NAMES[$k]}"; echo "   ${NAMES[$k]} back to ${FROMS[$k]:0:8}"; done
if [ -f "$BEFORE_JSON" ]; then
  "$VPY" -B - "$LIVE_DB" "$BEFORE_JSON" <<'EOF'
import json, sqlite3, sys
con = sqlite3.connect(sys.argv[1], timeout=60)
b = json.load(open(sys.argv[2]))
con.execute("UPDATE stock_point SET status=?, note=? WHERE id=388", (b["point_388"]["status"], b["point_388"]["note"]))
con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why=? WHERE id=7", (b["loss_line_7"]["void_at"], b["loss_line_7"]["void_why"]))
con.execute("UPDATE stock_trace SET status=?, seen_by=?, seen_at=? WHERE id=35", (b["trace_35"]["status"], b["trace_35"]["seen_by"], b["trace_35"]["seen_at"]))
t = b["point_today"]
con.execute("UPDATE stock_point SET note=?, expected_units=?, gap_units=?, basis=? WHERE id=?", (t["note"], t["expected_units"], t["gap_units"], t["basis"], t["id"]))
con.commit()
print("   TRAMATEE's four rows put back as they were before the repair")
EOF
else echo "   (no repair record at $BEFORE_JSON - TRAMATEE's rows were not touched by the install)"; fi
# the review (S506, finding 5): the old files would take a count still HELD as the shelf -- set aside as superseded; the open recounts withdrawn
"$VPY" -B - "$LIVE_DB" <<'EOF'
import datetime, sqlite3, sys
con = sqlite3.connect(sys.argv[1], timeout=60)
now = datetime.datetime.now().replace(microsecond=0).isoformat()
cols = {r[1] for r in con.execute("PRAGMA table_info(stock_watch_ask)")}
n = con.execute("UPDATE stock_point SET status='superseded', note=COALESCE(note,'') || ' · S936 undone: a count held for a recount, set aside' WHERE status IN ('recount','recounted')").rowcount
m = con.execute("UPDATE stock_watch_ask SET done_at=?, closed_how='withdrawn' WHERE recount_of IS NOT NULL AND done_at IS NULL", (now,)).rowcount if "recount_of" in cols else 0
try:
    con.execute("INSERT INTO setting (key, value, note) VALUES ('count._s936_held_at', ?, 'S936 undo: the record rebuilds') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (now,))
except sqlite3.Error:
    pass
con.commit()
print("   %d held count(s) set aside; %d open recount(s) withdrawn" % (n, m))
EOF
systemctl restart "$FSVC" && echo "   $FSVC restarted" && echo "S936 undone."
