#!/bin/bash
# install_S447_RATE_GROUPS.sh -- session 288, 02-Oct-2026 -- F-681, the owner: "cast slab is coming at three
# places". ONE anchored edit on exact bytes to /root/finance/owner_sheets.py (S441 6a04071d): the rate page builds
# ONE block per procedure group instead of one per run of neighbouring rows. No row, price or status changes; the
# database is only READ (the walk, read-only). Restarts clinic-finance; anything red after placing -> restored.
set -u
KIT="S447_RATE_GROUPS"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"
F="${F:-/root/finance/owner_sheets.py}"; DB="${DB:-/root/finance/finance.db}"; SVC="${SVC:-clinic-finance}"
BASEURL="${BASEURL:-http://127.0.0.1:8106}"
FROM=6a04071db4667a129dbd0446686bf749; TO=8b1aea31fc1d7dd231fbb45f87c2c6d2
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$1"; }
cd "$KDIR" || exit 1
say "[1/6] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
say "      green"
[ "$(m5 "$F")" = "$TO" ] && { say "-- ALREADY INSTALLED. Nothing to do. ($SVC $(systemctl is-active "$SVC" 2>/dev/null))"; exit 0; }
say "[2/6] live pin"
[ "$(m5 "$F")" = "$FROM" ] || { say "!! [2/6] live owner_sheets.py is $(m5 "$F"), not the S441 bytes $FROM - nothing installed"; exit 1; }
[ -f "$DB" ] || { say "!! [2/6] $DB not found - nothing installed"; exit 1; }
say "      exact (S441)"
say "[3/6] scratch: patch a copy + the walk (the 28 live lines, then the REAL database read-only)"
W="/tmp/s447_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W" && \cp -p "$F" "$W/orig.py" && \cp -p "$F" "$W/owner_sheets.py" || { say "!! [3/6] scratch copy failed"; exit 1; }
"$VPY" -B apply_s447.py "$W/owner_sheets.py" >/dev/null && [ "$(m5 "$W/owner_sheets.py")" = "$TO" ] || { say "!! [3/6] the patched copy is not the predicted bytes - nothing installed"; rm -rf "$W"; exit 1; }
"$VPY" -B -m py_compile "$W/owner_sheets.py" || { say "!! [3/6] py_compile failed"; rm -rf "$W"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s447.py" "$W/orig.py" "$W/owner_sheets.py" "$DB" 2>&1 | tail -1 )"
NEG="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s447.py" "$W/orig.py" "$W/orig.py" 2>&1 | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red: $WOUT - nothing installed"; exit 1; }
echo "$NEG" | grep -q "^WALK OK" && { say "!! [3/6] the walk passed the UNPATCHED file - it proves nothing; nothing installed"; exit 1; }
say "      $WOUT · unpatched file goes red, as it must"
say "[4/6] backup + place"
BAK="$F.bak_S447_6a04071d"; \cp -p "$F" "$BAK" || { say "!! [4/6] backup failed"; exit 1; }
restore() { \cp -p "$BAK" "$F"; systemctl restart "$SVC" 2>/dev/null; sleep 4; say "!! $1 - RESTORED the S441 file ($(m5 "$F")); $SVC $(systemctl is-active "$SVC" 2>/dev/null), healthz $(health "$BASEURL/finance/healthz")"; exit 1; }
"$VPY" -B apply_s447.py "$F" | sed 's/^/      /'
[ "$(m5 "$F")" = "$TO" ] || restore "[4/6] placed bytes wrong"
say "[5/6] restart + health"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart "$SVC" || restore "[5/6] restart failed"
sleep 6
systemctl is-active --quiet "$SVC" || restore "[5/6] $SVC not active"
c1=$(health "$BASEURL/finance/healthz"); c2=$(health "$BASEURL/finance/clinic/sheets")
[ "$c1" = 200 ] || restore "[5/6] healthz $c1"
case "$c2" in 302|401|200) ;; *) restore "[5/6] /finance/clinic/sheets answered $c2";; esac
journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "[5/6] a finance module NOT mounted"
JR="$(journalctl -u "$SVC" --since "$T0" --no-pager 2>/dev/null | grep -ci 'Traceback\|SyntaxError\|NameError')"
[ "${JR:-0}" = 0 ] || restore "[5/6] journal: $JR error line(s)"
say "      $SVC active · healthz $c1 · /finance/clinic/sheets $c2 (302/401 = the login gate) · journal clean"
say "[6/6] all green -- $KIT: DONE. Open the X-rays & procedures tile: Cast / slab is one block."
say "      backup: $BAK"
md5sum "$F"
