#!/bin/bash
# install_S434_PACKS_FIXES.sh -- session 286 (parent), 28-Sep-2026 -- the owner's walk of the August pack (F-653 ... F-658).
#   /root/finance/packs.py    c3eb9db0 -> 6a1cf6ce   (full file from the live S433 bytes; 25 anchored edits)
#   /root/finance/packs.html  2e06943b -> 4c46cd0e    (the page folded into sections; a summary card on top)
#   finance.db: packs.retired_slots cleared (the clinic's Yes Bank current row back); two new settings (INSERT OR IGNORE).
# Proven on a COPY of the live database first (walk_s434.py); RED after placing = the old files back. Restarts clinic-finance.
set -u -o pipefail
KIT="S434_PACKS_FIXES"; KDIR="$(cd "$(dirname "$0")" && pwd)"; FD="${FD:-/root/finance}"; SPY=/usr/bin/python3
FROM_PY=c3eb9db0; TO_PY=6a1cf6ce; FROM_HT=2e06943b; TO_HT=4c46cd0e
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/7] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 packs.py | cut -c1-8)" = "$TO_PY" ] && [ "$(m5 packs.html | cut -c1-8)" = "$TO_HT" ] || { say "!! [1/7] the kit's files are not the built ones"; exit 1; }
$SPY -B -c "import sys; [compile(open(f).read(), f, 'exec', dont_inherit=True) for f in sys.argv[1:]]" packs.py walk_s434.py || { say "!! [1/7] compile check failed"; exit 1; }
say "      green"
say "[2/7] the live files"
P0="$(m5 "$FD/packs.py")"; H0="$(m5 "$FD/packs.html")"
if [ "${P0:0:8}" = "$TO_PY" ] && [ "${H0:0:8}" = "$TO_HT" ]; then say "      already in; the data step still runs"; ALREADY=1
elif [ "${P0:0:8}" != "$FROM_PY" ] || [ "${H0:0:8}" != "$FROM_HT" ]; then say "!! [2/7] packs.py ${P0:0:8} / packs.html ${H0:0:8} -- not $FROM_PY / $FROM_HT. Nothing installed; the kit is rebuilt from the new bytes."; exit 1
else ALREADY=0; say "      packs.py ${P0:0:8} · packs.html ${H0:0:8} = the bytes this kit was built from"; fi
say "[3/7] the walk, on a copy of the live database"
W="/tmp/s434_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W"
$SPY -B -c "import sqlite3; s=sqlite3.connect('$FD/finance.db'); d=sqlite3.connect('$W/finance.db'); s.backup(d); d.close(); s.close()" || { say "!! [3/7] copy of the database failed"; rm -rf "$W"; exit 1; }
( cd /tmp && timeout 300 $SPY -B "$KDIR/walk_s434.py" "$KDIR" "$W" "$W/finance.db" "$FD" ) > "$W.log" 2>&1
WOUT="$(tail -1 "$W.log")"; sed -E 's/[0-9]{11,}/[num]/g' "$W.log" | sed 's/^/      /'
rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/7] walk red - nothing installed (the log: $W.log)"; exit 1; }
say "[4/7] backups"
STAMP="$(date +%Y%m%d_%H%M%S)"; BP="$FD/packs.py.bak_S434_${P0:0:8}"; BH="$FD/packs.html.bak_S434_${H0:0:8}"; BD="$FD/finance.db.bak_S434_$STAMP"
if [ "$ALREADY" = 0 ]; then \cp -p "$FD/packs.py" "$BP" && \cp -p "$FD/packs.html" "$BH" || { say "!! [4/7] backup failed"; exit 1; }; fi
$SPY -B -c "import sqlite3; s=sqlite3.connect('$FD/finance.db'); d=sqlite3.connect('$BD'); s.backup(d); d.close(); s.close()" || { say "!! [4/7] database backup failed"; exit 1; }
say "      $BP · $BH · $BD"
restore() { say "!! RED after placing ($1) - the old files back"; if [ "$ALREADY" = 0 ]; then \cp -p "$BP" "$FD/packs.py"; \cp -p "$BH" "$FD/packs.html"; fi
            systemctl restart clinic-finance || true; sleep 5; say "   packs.py $(m5 "$FD/packs.py") · packs.html $(m5 "$FD/packs.html") · database backup kept: $BD"; exit 1; }
say "[5/7] place + the data step"
if [ "$ALREADY" = 0 ]; then \cp -p "$KDIR/packs.py" "$FD/packs.py" && \cp -p "$KDIR/packs.html" "$FD/packs.html" || restore "copy"; fi
( cd "$FD" && $SPY -B -c "import sys; [compile(open(f).read(), f, 'exec', dont_inherit=True) for f in sys.argv[1:]]" packs.py ) || restore "compile check on the box"
( cd "$FD" && FINANCE_DB="$FD/finance.db" $SPY -B - <<'PY' ) 2>&1 | sed 's/^/      /' || restore "data step"
import sys; sys.path.insert(0, ".")
import packs
con = packs._con(); packs.ensure(con)
n = con.execute("UPDATE setting SET value='' WHERE key='packs.retired_slots' AND value='yes_cur_clinic'").rowcount
for k in ("packs.electricity_expected", "packs.digest_drop_words"):
    con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (k, packs.SETTINGS[k][0], packs.SETTINGS[k][1]))
con.commit()
print("the clinic's Yes Bank current row: %s; two settings in place" % ("back" if n else "already back"))
PY
say "[6/7] restart clinic-finance, then the probes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart"; sleep 6; systemctl is-active --quiet clinic-finance || restore "not active"
FP="$(grep -o '127.0.0.1:[0-9]*' /etc/systemd/system/clinic-finance.service | head -1 | cut -d: -f2)"; FP="${FP:-8106}"
HZ="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:$FP/finance/healthz)"
PK="$(curl -s -o /dev/null -m 10 -w '%{http_code}' http://127.0.0.1:$FP/finance/packs)"
say "      healthz $HZ (200 expected) · packs page without login $PK (302 or 401 expected, F-621)"
[ "$HZ" = 200 ] || restore "healthz"; { [ "$PK" = 302 ] || [ "$PK" = 401 ]; } || restore "packs page gate"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -i 'Traceback\|SyntaxError\|NameError\|ImportError' | grep -ci 'packs\|Traceback')"
[ "$JR" = 0 ] || { journalctl -u clinic-finance --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error' | head -30; restore "journal: $JR error line(s)"; }
say "      journal since restart: clean"
say "[7/7] August on the live page"
( cd "$FD" && FINANCE_DB="$FD/finance.db" $SPY -B - <<'PY' ) 2>&1 | sed -E 's/[0-9]{11,}/[num]/g' | sed 's/^/      /'
import sys; sys.path.insert(0, ".")
import packs
con = packs._con()
rows, att = packs.pack_rows(con, "2026-08", light=True)
print("accountant pack: %d of %d rows ready" % (sum(1 for r in rows if r["status"] == "ready"), len(rows)))
for r in rows:
    if r["status"] != "ready":
        print("  open: %s -- %s" % (r["title"], (r["why"] or "")[:90]))
k, d, t = packs.digest_rows(con, "2026-08")
print("digest: %d payments kept, %d mails set aside, total Rs %.2f" % (len(k), len(d), t))
PY
say "      all green -- $KIT: DONE"
md5sum "$FD/packs.py" "$FD/packs.html"
