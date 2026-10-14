#!/bin/bash
# rehearse_s558.sh -- the S558 installer rehearsed on a made-up root under /tmp/s558dev/root (BUILD_NORM_v1 s3).
# Copies of the portal's files, of call_api.py, and of both stores (SQLite's backup API) are put there; every setting of the
# installer points there; systemctl and journalctl are stand-ins that only answer; the HTTP answers come from a stand-in
# (a small python3 server on a free port: the health routes 200 with "status": "ok", the list and its doors 302 -- the login
# gate, as the live portal answers a plain request). Nothing live is placed or restarted; nothing under /root is written.
# Outcomes: 1 green (table and OFF keys made on the made-up copy); 2 ALREADY INSTALLED; 3 a forced red after placing restores;
# 4 the list answering 200 (a login gate open) restores; 5 a forced red after the look as manoj restores.
# Run as root on the VPS: bash rehearse_s558.sh        (the made-up root is removed at the end; KEEP=1 keeps it)
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT=/tmp/s558dev/root
LP=/root/portal
S497="${S497DIR:-/root/deploy/repo/deploy_kits/S497_RING_LIST}"
md5(){ md5sum "$1" | cut -c1-32; }
fail(){ echo "REHEARSAL RED: $*"; [ -n "${HPID:-}" ] && kill "$HPID" 2>/dev/null; exit 1; }
pin(){ grep -m1 "^$1=" "$HERE/install_S558_RING_LIST_LINK_CALL.sh" | cut -d= -f2 | cut -d';' -f1; }
RO_FROM=$(pin RO_FROM); RC_FROM=$(pin RC_FROM)
RO_TO=$(grep -m1 -o 'RO_TO=[0-9a-f]*' "$HERE/install_S558_RING_LIST_LINK_CALL.sh" | cut -d= -f2)
RC_TO=$(grep -m1 -o 'RC_TO=[0-9a-f]*' "$HERE/install_S558_RING_LIST_LINK_CALL.sh" | cut -d= -f2)
at_from(){ [ "$(md5 "$ROOT/portal/ring_outcome.py")" = "$RO_FROM" ] && [ "$(md5 "$ROOT/portal/ring_common.py")" = "$RC_FROM" ]; }
at_to(){ [ "$(md5 "$ROOT/portal/ring_outcome.py")" = "$RO_TO" ] && [ "$(md5 "$ROOT/portal/ring_common.py")" = "$RC_TO" ]; }
reset_root(){ cp "$ROOT/orig/ring_outcome.py" "$ROOT/orig/ring_common.py" "$ROOT/portal/"; rm -f "$ROOT/portal/"*.bak_S558_* "$ROOT/finance/"*.bak_S558_*; }
copydb(){ python3 -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
store(){ python3 -c "
import sqlite3,sys; c=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True)
t={r[0] for r in c.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}
kv=dict(c.execute(\"SELECT k,v FROM kv WHERE k IN ('link_on','call_on')\").fetchall()) if 'kv' in t else {}
print('appt_link' in t, kv.get('link_on'), kv.get('call_on'))" "$1"; }

rm -rf "$ROOT"; mkdir -p "$ROOT/portal" "$ROOT/finance" "$ROOT/wa" "$ROOT/orig" "$ROOT/web" "$ROOT/bin" "$ROOT/tmp" || fail "no made-up root"
for f in ring_outcome.py ring_common.py portal.py portal_push.py clinic_sso.py clinic_users.py tracker_pass.py portal_sw.js tile_grants.json ring_agents.json \
         ring_outcome.py.bak_S497_495b0ada portal.py.bak_S497_63df9d49 tile_grants.json.bak_S497_f9441311; do
  cp "$LP/$f" "$ROOT/portal/" || fail "copy $f"
done
chmod 600 "$ROOT/portal/ring_agents.json"
cp "$ROOT/portal/ring_outcome.py" "$ROOT/portal/ring_common.py" "$ROOT/orig/"
cp /root/wa/call_api.py "$ROOT/wa/"
copydb "$LP/ring_outcomes.db" "$ROOT/portal/ring_outcomes.db" || fail "ring store copy"
copydb /root/finance/finance.db "$ROOT/finance/finance.db" || fail "finance copy"
at_from || fail "the live files are not at the kit's FROM pins -- nothing to rehearse"
echo "  the made-up store before: $(store "$ROOT/portal/ring_outcomes.db")  (appt_link? link_on call_on)"
cat > "$ROOT/bin/systemctl" <<'EOF'
#!/bin/bash
# stand-in: answers, starts and stops nothing
case "$1" in restart) echo "restart $*" >> /tmp/s558dev/root/web/restarts; exit 0;; is-active) [ "$2" = "--quiet" ] && exit 0; echo active; exit 0;; esac
exit 0
EOF
printf '#!/bin/bash\nexit 0\n' > "$ROOT/bin/journalctl"
chmod +x "$ROOT/bin/systemctl" "$ROOT/bin/journalctl"
cat > "$ROOT/web/standin.py" <<'PYEOF'
import http.server, os, sys
WEB = os.path.dirname(os.path.abspath(__file__))
class H(http.server.BaseHTTPRequestHandler):
    def ans(self):
        p = self.path.split("?")[0]
        mode = open(os.path.join(WEB, "list_mode")).read().strip()
        if p in ("/portal/health", "/ring-hook/health"):
            code, body = 200, b'{"status": "ok"}'
        elif p == "/finance/healthz":
            code, body = 200, b"ok"
        elif p.startswith("/portal/ring/list") or p == "/portal":
            code, body = int(mode), b""
        else:
            code, body = 404, b""
        self.send_response(code)
        if code == 302:
            self.send_header("Location", "/portal/login")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    do_GET = ans
    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        self.rfile.read(n)
        self.ans()
    def log_message(self, *a):
        pass
http.server.HTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
PYEOF
echo 302 > "$ROOT/web/list_mode"
PORT="$(python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1',0)); print(s.getsockname()[1]); s.close()")"
python3 -B "$ROOT/web/standin.py" "$PORT" >/dev/null 2>&1 & HPID=$!
sleep 1
export PD="$ROOT/portal" FINDB="$ROOT/finance/finance.db" FINDIR="$ROOT/finance" WADIR="$ROOT/wa" LOCK="$ROOT/lock" TMPBASE="$ROOT/tmp"
export PORURL="http://127.0.0.1:$PORT" RINGURL="http://127.0.0.1:$PORT" FINURL="http://127.0.0.1:$PORT"
export SYSTEMCTL="$ROOT/bin/systemctl" JOURNALCTL="$ROOT/bin/journalctl" WAIT=0 S497DIR="$S497"
for v in PD FINDB FINDIR WADIR LOCK TMPBASE; do p="$(readlink -m "${!v}")"; case "$p" in /root/*) fail "$v resolves to $p";; esac; done
[ "$(curl -s -o /dev/null -w '%{http_code}' "$PORURL/portal/health")" = 200 ] || fail "the stand-in is not up"
[ "$(curl -s -o /dev/null -w '%{http_code}' "$PORURL/portal/ring/list")" = 302 ] || fail "the stand-in list does not answer 302"
echo "made-up root $ROOT; stand-in on port $PORT; systemctl/journalctl stand-ins; lock $LOCK"
I="$HERE/install_S558_RING_LIST_LINK_CALL.sh"

echo "=== outcome 1: a fresh install (green) ==="
bash "$I" > "$ROOT/run1.txt" 2>&1; R1=$?
grep -E '^\[|DONE|REFUSED|NOT INSTALLED|under |as manoj|UNDO|read back|restarted' "$ROOT/run1.txt" | cut -c1-260 | sed 's/^/  /'
[ "$R1" = 0 ] && grep -q "S558_RING_LIST_LINK_CALL: DONE." "$ROOT/run1.txt" || { tail -30 "$ROOT/run1.txt"; fail "outcome 1 was not green (exit $R1)"; }
at_to || fail "outcome 1: the placed files are not at the TO pins"
ls "$ROOT/portal/" | grep -q "^ring_outcome.py.bak_S558_7cb60aad$" && ls "$ROOT/portal/" | grep -q "^ring_common.py.bak_S558_4344b592$" || fail "outcome 1: no file backups"
ls "$ROOT/portal/" | grep -q "ring_outcomes.db.bak_S558_" && ls "$ROOT/finance/" | grep -q "finance.db.bak_S558_" || fail "outcome 1: no database backups"
[ "$(store "$ROOT/portal/ring_outcomes.db")" = "True 0 0" ] || fail "outcome 1: the table / OFF keys were not made: $(store "$ROOT/portal/ring_outcomes.db")"
grep -q "restart ring-hook" "$ROOT/web/restarts" && grep -q "restart clinic-portal" "$ROOT/web/restarts" && [ "$(grep -vc 'ring-hook\|clinic-portal' "$ROOT/web/restarts")" = 0 ] || fail "outcome 1: restarted something else"
[ ! -e "$ROOT/lock" ] || fail "outcome 1: the lock was left behind"
[ -z "$(find "$HERE" -name __pycache__)" ] || fail "outcome 1: a __pycache__ was left in the kit"
echo "  after outcome 1: both files at the TO pins; backups beside them; appt_link made; link_on=0 call_on=0; only ring-hook and clinic-portal restarted; lock gone"

echo "=== outcome 2: the same line again (ALREADY INSTALLED) ==="
bash "$I" > "$ROOT/run2.txt" 2>&1; R2=$?
tail -2 "$ROOT/run2.txt" | cut -c1-200 | sed 's/^/  /'
[ "$R2" = 0 ] && grep -q "ALREADY INSTALLED" "$ROOT/run2.txt" || fail "outcome 2 did not say ALREADY INSTALLED"

echo "=== outcome 3: a forced red after placing (restores) ==="
reset_root
FORCE_RED=1 bash "$I" > "$ROOT/run3.txt" 2>&1; R3=$?
grep -E 'RED after|back at|after the restore|NOT INSTALLED' "$ROOT/run3.txt" | cut -c1-200 | sed 's/^/  /'
[ "$R3" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run3.txt" || fail "outcome 3 did not restore (exit $R3)"
at_from || fail "outcome 3: the files are not back at the FROM pins"

echo "=== outcome 4: the list answering 200 to a stranger (a login gate open) -> restores ==="
reset_root
echo 200 > "$ROOT/web/list_mode"
bash "$I" > "$ROOT/run4.txt" 2>&1; R4=$?
grep -E 'answered 200|RED after|NOT INSTALLED' "$ROOT/run4.txt" | cut -c1-200 | sed 's/^/  /'
[ "$R4" = 1 ] && grep -q "answered 200 without a login" "$ROOT/run4.txt" && grep -q "NOT INSTALLED (restored" "$ROOT/run4.txt" || fail "outcome 4 did not restore (exit $R4)"
at_from || fail "outcome 4: the files are not back at the FROM pins"
echo 302 > "$ROOT/web/list_mode"

echo "=== outcome 5: a forced red after the look as manoj (restores) ==="
reset_root
FORCE_RED_LATE=1 bash "$I" > "$ROOT/run5.txt" 2>&1; R5=$?
grep -E 'RED after|NOT INSTALLED' "$ROOT/run5.txt" | cut -c1-200 | sed 's/^/  /'
[ "$R5" = 1 ] && grep -q "NOT INSTALLED (restored" "$ROOT/run5.txt" || fail "outcome 5 did not restore (exit $R5)"
at_from || fail "outcome 5: the files are not back at the FROM pins"

kill "$HPID" 2>/dev/null
[ -z "$(find "$HERE" -name __pycache__)" ] || fail "a __pycache__ was left in the kit"
echo "REHEARSAL GREEN: fresh install green; ALREADY INSTALLED; forced red restored; list 200 restored (302 only); red after the look restored. Nothing live was placed or restarted."
[ -n "${KEEP:-}" ] || rm -rf "$ROOT"
exit 0
