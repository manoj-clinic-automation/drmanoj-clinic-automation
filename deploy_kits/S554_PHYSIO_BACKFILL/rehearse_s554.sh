#!/bin/bash
# =============================================================================
#  rehearse_s554.sh · kit S554_PHYSIO_BACKFILL -- the installer's order rehearsed on a MADE-UP ROOT in /tmp (BUILD_NORM_v1 §3).
#    bash rehearse_s554.sh            (on the VPS, from the kit folder; touches nothing live)
#  The made-up root: a copy of /root/finance's code, a backup-API copy of finance.db, a copy of /root/portal's code and grants
#  file (never portal_config.py, never the user store), its own lock path, and a stand-in 'systemctl' that runs the REAL
#  finance app from the made-up root on port 18554 (its stderr is the stand-in journal). Three runs:
#    1 red after placing  -- the stand-in refuses the first restart: both files must come back byte-identical, health 200 again,
#                            the database backup left beside it, the lock released
#    2 green              -- DONE, the md5s read back, the setting physio_book.from = 2026-10-01
#    3 again              -- ALREADY INSTALLED, nothing written
#  Prints 'REHEARSAL OK' or 'REHEARSAL RED'.
# =============================================================================
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
LIVE_FIN=/root/finance; LIVE_POR=/root/portal
R="/tmp/s554_reh_$(date +%Y%m%d_%H%M%S)"
PORT="${REH_PORT:-18554}"
FAIL=0
ok() { echo "  ok   $1"; }
bad() { echo "  FAIL $1"; FAIL=1; }
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cleanup() {   # stop the stand-in app: by its pid file, and any listener on the port whose folder is this made-up root
  [ -f "$R/app.pid" ] && kill "$(cat "$R/app.pid")" 2>/dev/null
  for p in $(ss -ltnp 2>/dev/null | grep ":$PORT " | grep -o 'pid=[0-9]*' | cut -d= -f2 | sort -u); do
    case "$(readlink "/proc/$p/cwd")" in "$R"/*) kill "$p" 2>/dev/null;; esac
  done
  sleep 1; rm -rf "$R"
  find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
}
trap cleanup EXIT
if curl -s -o /dev/null -m 3 "http://127.0.0.1:$PORT/"; then echo "REHEARSAL RED: port $PORT is in use"; exit 1; fi
mkdir -p "$R/root/finance/finance_ui" "$R/root/finance/spine" "$R/root/portal" "$R/bin" "$R/deploy"
cp -p "$LIVE_FIN"/*.py "$R/root/finance/" 2>/dev/null; cp -p "$LIVE_FIN"/*.html "$LIVE_FIN"/*.json "$LIVE_FIN"/*.sql "$R/root/finance/" 2>/dev/null
cp -rp "$LIVE_FIN/finance_ui/." "$R/root/finance/finance_ui/" 2>/dev/null; cp -p "$LIVE_FIN"/spine/*.py "$LIVE_FIN"/spine/*.json "$R/root/finance/spine/" 2>/dev/null
rm -f "$R/root/finance"/*.bak_S554_*
/usr/bin/python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True,timeout=60); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" \
  "$LIVE_FIN/finance.db" "$R/root/finance/finance.db" || { echo "REHEARSAL RED: no copy of the database"; exit 1; }
for f in "$LIVE_POR"/*.py; do [ "$(basename "$f")" = portal_config.py ] || cp -p "$f" "$R/root/portal/"; done
cp -p "$LIVE_POR/tile_grants.json" "$R/root/portal/"
cat > "$R/bin/systemctl" <<EOF
#!/bin/bash
# stand-in systemctl for the rehearsal: the REAL finance app from the made-up root on port $PORT
case "\$1" in
  restart)
    [ -f "$R/app.pid" ] && kill "\$(cat "$R/app.pid")" 2>/dev/null
    for _i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null -m 2 "http://127.0.0.1:$PORT/finance/healthz" || break; sleep 1; done
    if [ -f "$R/RED_ONCE" ]; then rm -f "$R/RED_ONCE"; exit 1; fi
    cd "$R/root/finance" && FINANCE_DB="$R/root/finance/finance.db" FINANCE_PORT=$PORT PYTHONDONTWRITEBYTECODE=1 setsid nohup /usr/bin/python3 -B finance_app.py >>"$R/app.log" 2>&1 < /dev/null &
    echo \$! > "$R/app.pid"
    exit 0 ;;
  is-active) [ "\$(curl -s -o /dev/null -m 5 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz")" = 200 ]; exit \$? ;;
  *) exit 0 ;;
esac
EOF
cat > "$R/bin/journalctl" <<EOF
#!/bin/bash
cat "$R/app.log" 2>/dev/null | grep -v -E 'GET /finance/|POST /finance/'
EOF
chmod +x "$R/bin/systemctl" "$R/bin/journalctl"
"$R/bin/systemctl" restart reh
ENV=(FIN="$R/root/finance" POR="$R/root/portal" DB="$R/root/finance/finance.db" LOCK="$R/deploy/.lock" FIN_PORT=$PORT SVC=reh
     SYSTEMCTL="$R/bin/systemctl" JOURNALCTL="$R/bin/journalctl" TMPW="$R")
P0="$(m5 "$R/root/finance/physio_book.py")"; D0="$(m5 "$R/root/finance/aaj_duties.json")"

echo "-- run 1: red after placing (the stand-in refuses the first restart)"
touch "$R/RED_ONCE"
O1="$(env "${ENV[@]}" bash "$KDIR/install_S554_PHYSIO_BACKFILL.sh" 2>&1)"; X1=$?
echo "$O1" | grep -E "^\[|^!!|^   (/|after|the database)" | sed 's/^/   | /'
[ "$X1" = 1 ] && echo "$O1" | grep -q "RED after placing" && ok "run 1 went red after placing and said so" || bad "run 1 did not go red after placing (exit $X1)"
[ "$(m5 "$R/root/finance/physio_book.py")" = "$P0" ] && [ "$(m5 "$R/root/finance/aaj_duties.json")" = "$D0" ] && ok "run 1: physio_book.py and aaj_duties.json back byte-identical ($P0 / $D0)" || bad "run 1: a file was not put back"
echo "$O1" | grep -q "finance healthz 200" && ok "run 1: health 200 after the restore" || bad "run 1: health not 200 after the restore"
ls "$R/root/finance"/finance.db.bak_S554_* >/dev/null 2>&1 && ok "run 1: the database backup stays" || bad "run 1: no database backup"
[ ! -d "$R/deploy/.lock" ] && ok "run 1: the lock released" || bad "run 1: the lock left behind"

echo "-- run 2: green"
O2="$(env "${ENV[@]}" bash "$KDIR/install_S554_PHYSIO_BACKFILL.sh" 2>&1)"; X2=$?
echo "$O2" | grep -E "^\[|^!!|^S554|PROBE|SHOWN|^undo|^   (as manoj|the )" | sed 's/^/   | /'
[ "$X2" = 0 ] && echo "$O2" | grep -q "S554_PHYSIO_BACKFILL: DONE" && ok "run 2 green: DONE" || { bad "run 2 not green (exit $X2)"; echo "$O2" | tail -15; echo "-- the stand-in app's log:"; tail -15 "$R/app.log"; }
[ "$(m5 "$R/root/finance/physio_book.py")" = "$(m5 "$KDIR/physio_book.py")" ] && [ "$(m5 "$R/root/finance/aaj_duties.json")" = "$(m5 "$KDIR/aaj_duties.json.kit")" ] \
  && ok "run 2: both files at the kit's md5s" || bad "run 2: md5s wrong"
FV="$(/usr/bin/python3 -c "import sqlite3,sys; print(sqlite3.connect(sys.argv[1]).execute(\"SELECT value FROM setting WHERE key='physio_book.from'\").fetchone()[0])" "$R/root/finance/finance.db" 2>&1)"
[ "$FV" = "2026-10-01" ] && ok "run 2: the setting physio_book.from = 2026-10-01" || bad "run 2: the setting reads '$FV'"
[ ! -d "$R/deploy/.lock" ] && ok "run 2: the lock released" || bad "run 2: the lock left behind"

echo "-- run 3: again"
O3="$(env "${ENV[@]}" bash "$KDIR/install_S554_PHYSIO_BACKFILL.sh" 2>&1)"; X3=$?
[ "$X3" = 0 ] && echo "$O3" | grep -q "ALREADY INSTALLED" && ok "run 3: ALREADY INSTALLED, nothing written" || bad "run 3 did not say ALREADY INSTALLED (exit $X3)"
if [ "$FAIL" = 0 ]; then echo "REHEARSAL OK: red-after-placing restores, green installs, a second run says ALREADY INSTALLED"; exit 0; fi
echo "REHEARSAL RED"; exit 1
