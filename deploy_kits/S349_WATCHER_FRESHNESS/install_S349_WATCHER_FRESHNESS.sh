#!/bin/bash
# =============================================================================
#  install_S349_WATCHER_FRESHNESS.sh · kit S349_WATCHER_FRESHNESS (session 276 parent, 20-Sep-2026)
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S349_WATCHER_FRESHNESS/install_S349_WATCHER_FRESHNESS.sh
#
#  TWO THINGS THE OWNER TICKED ON 20-Sep-2026:
#    1 · D554 / F-547 -- the health card's 'watcher' row goes RED when the medical PC's
#        heartbeat is stale DURING THE CLINIC DAY (pipeline.clinic_hour_from/_to, IST;
#        Sunday out unless pipeline.clinic_sunday = 1); info outside it, as before.
#    2 · F-540 -- /finance/freshness serves the collector's own freshness.html, read-only,
#        behind the health page's gate; one link to it in the health page's help box.
#
#  CODE CHANGE: /root/finance/finance_app.py 7866b1ee -> read back at install (three anchored
#  edits) + NEW /root/finance/freshness_page.py. clinic-finance is restarted.
#
#  Gates: kit SUMS + KIT_ID -> the walk on a COPY of the live file with the SERVICE'S python
#  (28 checks, 1 negative control, a real Flask mount) -> read-only --check -> --apply (backup
#  .bak_S349_* beside it, py_compile before replacing) -> place the module -> py_compile with both
#  pythons -> restart -> healthz 200 · /finance/health · /finance/freshness (302/401/403 = the
#  login gate, accepted -- F-525) -> the freshness file's own age, read-only. Any red restores
#  finance_app.py from this run's backup, removes the module, restarts again.
# =============================================================================
set -u
KIT="S349_WATCHER_FRESHNESS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
TARGET="$FIN/finance_app.py"
MODULE="$FIN/freshness_page.py"
SVC="${SVC:-clinic-finance}"
PORT="${PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"
T="/tmp/s349_$STAMP"
say() { echo "$@"; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
[ -x "$SPY" ] || { say "!! preflight: $SPY not executable - nothing changed"; exit 1; }
[ -f "$TARGET" ] || { say "!! preflight: $TARGET is not there - nothing changed"; exit 1; }
grep -q "S332_RECORDS end" "$TARGET" || { say "!! preflight: $TARGET does not carry S332 - nothing changed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - kit corrupt, nothing changed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing changed"; exit 1; }
if [ -f "$MODULE" ] && [ "$(m5 "$MODULE")" != "$(m5 "$KDIR/freshness_page.py")" ]; then
  say "!! [1/8] $MODULE already exists with OTHER bytes ($(m5 "$MODULE")) - not overwriting, nothing changed"; exit 1
fi
say "[1/8] kit gates green (live finance_app.py $(m5 "$TARGET"))"

export PYTHONPYCACHEPREFIX="$T/pyc"
mkdir -p "$T" || exit 1
\cp -p "$TARGET" "$T/live_copy.py"
WOUT="$( cd /tmp && timeout 300 "$SPY" -B "$KDIR/walk_s349.py" "--file=$T/live_copy.py" 2>&1 | tail -3 | tr '\n' ' ' )"
case "$WOUT" in
  *"WALK OK"*) say "[2/8] $(echo "$WOUT" | grep -o 'WALK OK -- [0-9]* checks') on a copy of the live file, with the service's python" ;;
  *) say "!! [2/8] the walk is red against a copy of the live file:"; say "    $WOUT"; rm -rf "$T"; exit 1 ;;
esac

say "[3/8] as it stands now (read-only):"
"$SPY" -B patch_finance_app_s349.py --check "--file=$TARGET" | sed 's/^/    /'

BAK="$T/finance_app.before"
\cp -p "$TARGET" "$BAK"
PLACED_MODULE=0
restore() { say "!! restoring $TARGET from this run's backup"; \cp -p "$BAK" "$TARGET";
            if [ "$PLACED_MODULE" = "1" ]; then rm -f "$MODULE"; say "!! removed $MODULE"; fi
            systemctl restart "$SVC" >/dev/null 2>&1 || true; sleep 4;
            say "!! restored: finance_app $(m5 "$TARGET") · $SVC $(systemctl is-active "$SVC")"; rm -rf "$T"; exit 1; }

say "[4/8] applying to finance_app.py:"
AOUT="$("$SPY" -B patch_finance_app_s349.py --apply "--file=$TARGET" 2>&1)"
echo "$AOUT" | sed 's/^/    /'
case "$AOUT" in
  *"RESULT APPLIED"*|*"RESULT ALREADY"*) : ;;
  *) say "!! [4/8] refused for the reason above - nothing changed"; rm -rf "$T"; exit 1 ;;
esac
"$SPY" -B patch_finance_app_s349.py --check "--file=$TARGET" | grep -q "RESULT ALREADY" || restore

if [ -f "$MODULE" ]; then
  say "[5/8] $MODULE already in place with these bytes"
else
  \cp "$KDIR/freshness_page.py" "$MODULE" && chmod 644 "$MODULE" && PLACED_MODULE=1
  say "[5/8] placed $MODULE ($(m5 "$MODULE"))"
fi
"$SPY" -m py_compile "$TARGET" || restore
"$VPY" -m py_compile "$TARGET" || restore
"$SPY" -m py_compile "$MODULE" || restore
say "[6/8] py_compile green with both pythons"

systemctl restart "$SVC" || restore
sleep 4
systemctl is-active --quiet "$SVC" || restore
C1=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz")
C2=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/health")
C3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/freshness")
say "[7/8] $SVC restarted · healthz $C1 · /finance/health $C2 · /finance/freshness $C3 (302/401/403 = the login gate, expected)"
[ "$C1" = "200" ] || restore
case "$C3" in 200|302|401|403) : ;; *) say "!! /finance/freshness answered $C3 -- the mount did not take"; restore ;; esac
if journalctl -u "$SVC" --since "-2 min" --no-pager 2>/dev/null | grep -q "freshness_page NOT mounted"; then
  say "!! the service log says the module did not mount:"; journalctl -u "$SVC" --since "-2 min" --no-pager | grep "NOT mounted" | sed 's/^/    /'; restore
fi

say "[8/8] the collector's file, read-only:"
FH="$FIN/freshness.html"
if [ -f "$FH" ]; then
  say "    $FH written $(date -r "$FH" '+%d-%b-%Y %H:%M') ($(( ( $(date +%s) - $(date -r "$FH" +%s) ) / 60 )) min ago) -- that is what the page serves, with that line on top"
else
  say "    $FH is not there yet -- the page says so (503) until the 08:05 collector writes it"
fi
say "    finance_app.py now $(m5 "$TARGET") (backup $(ls "$TARGET".bak_S349_* 2>/dev/null | tail -1)) · freshness_page.py $(m5 "$MODULE")"
rm -rf "$T"
say "$KIT: DONE -- the watcher row goes red in clinic hours when the medical PC falls silent; the freshness table is at:"
say "https://followup.dr-manoj.in/finance/freshness"
