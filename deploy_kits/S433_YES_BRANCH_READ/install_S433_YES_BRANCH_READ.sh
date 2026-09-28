#!/bin/bash
# install_S433_YES_BRANCH_READ.sh -- session 286 (parent), 28-Sep-2026 -- F-652: the statement shelf reads the Yes Bank BRANCH statements.
#   /root/finance/packs.py      938aa68f -> c3eb9db0   (full file, built from the live bytes of the 28-Sep 01:35 bundle; 14 anchored edits)
#   /root/finance/yes_branch.py NEW                    (the branch layout, read and proved; finance_yesbank.py is NOT touched)
#   finance.db  three settings (the owner's rulings of 28-Sep, INSERT OR IGNORE): packs.off_shelf_tails=0460 · packs.retired_slots=
#               yes_cur_clinic · packs.hide_locked=1; the period-less branch files get a fresh look; one identification pass.
# Proven on a COPY of the live database with the live inbox first (walk_s433.py); RED after placing = the old packs.py back.
# Restarts clinic-finance. Touches no Sanjeevni file.
set -u -o pipefail
KIT="S433_YES_BRANCH_READ"; KDIR="$(cd "$(dirname "$0")" && pwd)"; FD="${FD:-/root/finance}"; SPY=/usr/bin/python3
FROM=938aa68f; TO=c3eb9db0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/7] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 packs.py | cut -c1-8)" = "$TO" ] || { say "!! [1/7] the kit's packs.py is not $TO"; exit 1; }
$SPY -B -c "import ast,sys; [compile(open(f).read(), f, 'exec', dont_inherit=True) for f in sys.argv[1:]]" packs.py yes_branch.py walk_s433.py || { say "!! [1/7] compile check failed"; exit 1; }
say "      green"
say "[2/7] the live file"
P0="$(m5 "$FD/packs.py")"
ALREADY=0
if [ "${P0:0:8}" = "$TO" ]; then say "      packs.py is already $TO (the code is in); the data step still runs"; ALREADY=1
elif [ "${P0:0:8}" != "$FROM" ]; then say "!! [2/7] packs.py is ${P0:0:8}, not $FROM -- it moved since the 28-Sep bundle. Nothing installed; the kit is rebuilt from the new bytes."; exit 1
else say "      packs.py ${P0:0:8} = the bytes this kit was built from"; fi
say "[3/7] the walk, on a copy of the live database (the inbox is only read)"
W="/tmp/s433_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W"
$SPY -B -c "import sqlite3,sys; s=sqlite3.connect('$FD/finance.db'); d=sqlite3.connect('$W/finance.db'); s.backup(d); d.close(); s.close()" || { say "!! [3/7] copy of the database failed"; rm -rf "$W"; exit 1; }
( cd /tmp && timeout 300 $SPY -B "$KDIR/walk_s433.py" "$KDIR" "$W" "$W/finance.db" "$FD" ) > "$W.log" 2>&1
WOUT="$(tail -1 "$W.log")"; sed -E 's/[0-9]{11,}/[num]/g' "$W.log" | sed 's/^/      /'
rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/7] walk red - nothing installed (the log: $W.log)"; exit 1; }
say "[4/7] backups"
STAMP="$(date +%Y%m%d_%H%M%S)"
BP="$FD/packs.py.bak_S433_${P0:0:8}"; BD="$FD/finance.db.bak_S433_$STAMP"
[ "$ALREADY" = 1 ] || \cp -p "$FD/packs.py" "$BP" || { say "!! [4/7] backup of packs.py failed"; exit 1; }
$SPY -B -c "import sqlite3; s=sqlite3.connect('$FD/finance.db'); d=sqlite3.connect('$BD'); s.backup(d); d.close(); s.close()" || { say "!! [4/7] database backup failed"; exit 1; }
say "      $BP · $BD"
restore() { say "!! RED after placing ($1) - the old packs.py back"; [ "$ALREADY" = 1 ] || \cp -p "$BP" "$FD/packs.py"
            systemctl restart clinic-finance || true; sleep 5; say "   packs.py $(m5 "$FD/packs.py") (was $P0) · database backup kept: $BD"; exit 1; }
say "[5/7] place + the data step + one identification pass"
if [ "$ALREADY" = 0 ]; then \cp -p "$KDIR/packs.py" "$FD/packs.py" || restore "copy packs.py"; fi
\cp -p "$KDIR/yes_branch.py" "$FD/yes_branch.py" || restore "copy yes_branch.py"
( cd "$FD" && $SPY -B -c "import sys; [compile(open(f).read(), f, 'exec', dont_inherit=True) for f in sys.argv[1:]]" packs.py yes_branch.py ) || restore "compile check on the box"
( cd "$FD" && FINANCE_DB="$FD/finance.db" $SPY -B - <<'PY' ) 2>&1 | sed 's/^/      /' || restore "data step"
import sys; sys.path.insert(0, ".")
import packs
con = packs._con(); packs.ensure(con)
for k, v in (("packs.off_shelf_tails", "0460"), ("packs.retired_slots", "yes_cur_clinic"), ("packs.hide_locked", "1")):
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, packs.SETTINGS[k][1]))
n = con.execute("UPDATE stmt_file SET read_status=NULL, note=NULL WHERE folder='bank' AND COALESCE(locked,0)=0 AND period_to IS NULL "
                "AND LOWER(COALESCE(local_path,'')) LIKE '%.pdf'").rowcount
con.commit()
print("settings in place; %d period-less statement file(s) given a fresh look" % n)
print("identification: %s" % packs.process_inbox(con))
PY
say "[6/7] restart clinic-finance, then the probes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart"; sleep 6; systemctl is-active --quiet clinic-finance || restore "not active"
FP="$(grep -o '127.0.0.1:[0-9]*' /etc/systemd/system/clinic-finance.service | head -1 | cut -d: -f2)"; FP="${FP:-8106}"
HZ="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:$FP/finance/healthz)"
PK="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:$FP/finance/packs)"
say "      healthz $HZ (200 expected) · packs page without login $PK (302 or 401 expected, F-621)"
[ "$HZ" = 200 ] || restore "healthz"; { [ "$PK" = 302 ] || [ "$PK" = 401 ]; } || restore "packs page gate"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -i 'Traceback\|SyntaxError\|NameError\|ImportError' | grep -ci 'packs\|yes_branch\|Traceback')"
[ "$JR" = 0 ] || { journalctl -u clinic-finance --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "journal: $JR error line(s)"; }
say "      journal since restart: clean"
say "[7/7] August on the live shelf"
( cd "$FD" && FINANCE_DB="$FD/finance.db" $SPY -B - <<'PY' ) 2>&1 | sed 's/^/      /'
import sys; sys.path.insert(0, ".")
import packs
con = packs._con()
for c in packs.cells(con, "2026-08"):
    if c["kind"] != "card":
        f = c["file"] or {}
        print("%-44s %-8s %s" % (c["label"], c["state"], (f.get("matched_status") or "")[:70]))
print("Amir's pack ready: %s" % packs.amir_pack(con, "2026-08")["ready"])
rows, _ = packs.pack_rows(con, "2026-08", light=True)
print("accountant pack: %d of %d rows ready" % (sum(1 for r in rows if r["status"] == "ready"), len(rows)))
PY
say "      all green -- $KIT: DONE"
md5sum "$FD/packs.py" "$FD/yes_branch.py"
