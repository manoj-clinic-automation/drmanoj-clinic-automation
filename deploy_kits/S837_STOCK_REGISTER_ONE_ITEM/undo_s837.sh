#!/bin/bash
# undo_s837.sh -- takes kit S837_STOCK_REGISTER_ONE_ITEM back out (the installer's line [6/7]):
#   the six live files from their .bak_S837_ backups (each checked against its FROM pin first -- nothing changes if one is missing or wrong),
#   the new reader /root/marg_ingest/marg_register.py removed, every OPEN Stock Register ask closed ('S837 undone' -- the older Marg watch
#   has no kind filter and would show them on Shavez's sale card), clinic-finance restarted. The added tables and column stay (unread).
set -u
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
PAIRS="finance/marg_billwatch.py:960b5309e78570ef6fac605e34594f1f finance/reports_tile.py:163a869aee0547f891d47023a45873c4
finance/sanjeevni_approvals.py:ae29e2bc5bf2da9819e1f095e8aee7a5 finance/finance_ui/finance_approvals.html:82f459efc902085a6b4f9285efe9c1ef
marg_ingest/marg_take.py:5cad2d24d63344146f562fd5d441dbdf marg_ingest/marg_ingest.py:828c4dad6b159207b034d8129aed3ab7"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
for p in $PAIRS; do n=${p%%:*}; f=${p##*:}; b="$ROOT/$n.bak_S837_${f:0:8}"
  [ "$(m5 "$b")" = "$f" ] || { echo "!! no good backup of $n ($b) - NOTHING changed. Tell Claude."; exit 1; }; done
for p in $PAIRS; do n=${p%%:*}; f=${p##*:}; \cp -p "$ROOT/$n.bak_S837_${f:0:8}" "$ROOT/$n" || { echo "!! could not put back $n - tell Claude"; exit 1; }; done
rm -f "$ROOT/marg_ingest/marg_register.py"
C=$("$VPY" - "$DB" <<'PY' 2>&1 | tail -1
import datetime, sqlite3, sys
c = sqlite3.connect(sys.argv[1], timeout=30)
have = {r[1] for r in c.execute("PRAGMA table_info(marg_watch_report)")}
n = 0
if "kind" in have:
    n = c.execute("UPDATE marg_watch_report SET closed_at=?, closed_how='S837 undone' WHERE kind='REGISTER' AND closed_at IS NULL",
                  (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),)).rowcount
    c.commit()
print("asks closed %d" % n)
PY
)
"$SYSTEMCTL" restart "$FSVC" || echo "!! the restart of $FSVC failed - tell Claude"
for p in $PAIRS; do n=${p%%:*}; f=${p##*:}; echo "   $n $(m5 "$ROOT/$n" | cut -c1-8) (expected ${f:0:8})"; done
echo "   marg_register.py present: $([ -e "$ROOT/marg_ingest/marg_register.py" ] && echo yes || echo no) (expected no); $C"
echo "S837 UNDONE."
