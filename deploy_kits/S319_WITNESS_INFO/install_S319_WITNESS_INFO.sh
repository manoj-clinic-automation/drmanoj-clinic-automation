#!/bin/bash
# =============================================================================
#  install_S319_WITNESS_INFO.sh · kit S319_WITNESS_INFO (session 269 parent, 18-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S319_WITNESS_INFO/install_S319_WITNESS_INFO.sh
#
#  D525's first answer. The health page's never-fired witness names seven checks;
#  two of them -- flags and margqueue -- have NO red branch at all, by the S195
#  ruling. A list that is always the same is a list nobody reads, so they are
#  excluded BY NAME and the card says so in its own hint. After this it names
#  five, and every one of the five could have gone red and did not.
#
#  ONE FILE: /root/finance/finance_app.py. The two excluded rows are still
#  TRACKED -- the insert and the non-ok counter above the filter are untouched.
#  clinic-finance is restarted; any red restores the backup and restarts again.
#
#  Gates: kit SUMS + KIT_ID -> the walk, which lifts the witness's OWN list
#  comprehension out of the live file by text and runs it against a scratch
#  table (16 checks, 1 negative control) -> a read-only --check -> backup +
#  --apply, which py_compiles before replacing -> py_compile with both pythons ->
#  restart -> healthz + the page -> the live row counts, read-only.
# =============================================================================
set -u
KIT="S319_WITNESS_INFO"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
TARGET="$FIN/finance_app.py"
DB="${DB:-$FIN/finance.db}"
SVC="${SVC:-clinic-finance}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s319_$STAMP"
say() { echo "$@"; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$SPY" ] || { say "!! preflight: $SPY not executable - nothing changed"; exit 1; }
[ -f "$TARGET" ] || { say "!! preflight: $TARGET is not there - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing changed"; exit 1; }
say "[1/7] kit gates green"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
\cp -p "$TARGET" "$T/plain.py"
"$SPY" -B patch_finance_app_s319.py --apply "--file=$T/plain.py" >/dev/null 2>&1
\cp -p "$TARGET" "$T/asis.py"
WOUT="$( cd /tmp && timeout 180 "$SPY" -B "$KDIR/walk_s319.py" "--plain=$T/asis.py" "--patched=$T/plain.py" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$WOUT" in
  *"WALK OK"*) say "[2/7] $(echo "$WOUT" | grep -o 'WALK OK -- [0-9]* checks') (on a copy of the live file)" ;;
  *) say "!! [2/7] the walk is red against a copy of the live file:"; say "    $WOUT"; rm -rf "$T"; exit 1 ;;
esac

say "[3/7] as it stands now (read-only):"
"$SPY" -B patch_finance_app_s319.py --check "--file=$TARGET" | sed 's/^/    /'

BAK="$T/finance_app.before"
\cp -p "$TARGET" "$BAK"
restore() { say "!! restoring $TARGET from the backup taken this run"; \cp -p "$BAK" "$TARGET";
            systemctl restart "$SVC" >/dev/null 2>&1 || true; sleep 4;
            say "!! restored: finance_app $(m5 "$TARGET") · $SVC $(systemctl is-active "$SVC")"; exit 1; }

say "[4/7] applying:"
AOUT="$("$SPY" -B patch_finance_app_s319.py --apply "--file=$TARGET" 2>&1)"
echo "$AOUT" | sed 's/^/    /'
case "$AOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [4/7] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1 ;;
esac
"$SPY" -m py_compile "$TARGET" || restore
"$VPY" -m py_compile "$TARGET" || restore
say "[5/7] py_compile green with both pythons"

systemctl restart "$SVC" || restore
sleep 4
systemctl is-active --quiet "$SVC" || restore
C1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/healthz)
C2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' http://127.0.0.1:8106/finance/health)
say "[6/7] $SVC restarted · healthz $C1 · /finance/health $C2"
[ "$C1" = "200" ] || restore

say "[7/7] the witness's own rows, read-only from the live database:"
"$SPY" -B - "$DB" <<'PY' | sed 's/^/    /'
import sqlite3, sys, datetime as dt
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True)
con.row_factory = sqlite3.Row
now = dt.datetime.now()
rows = list(con.execute("SELECT key, first_seen, nonok_count FROM health_check_seen ORDER BY key"))
print("%d row(s) tracked; %d have never reported a problem"
      % (len(rows), sum(1 for r in rows if not r["nonok_count"])))
for r in rows:
    try:
        age = (now - dt.datetime.fromisoformat(str(r["first_seen"])[:19])).days
    except Exception:
        age = -1
    mark = "  <- informational by design, no longer counted" if r["key"] in ("flags", "margqueue") else ""
    print("  %-12s first seen %3d day(s) ago · non-ok %d%s" % (r["key"], age, r["nonok_count"], mark))
PY
rm -rf "$T"
say "$KIT: DONE -- the card reads five now, not seven; each of the five could have gone red and did not"
