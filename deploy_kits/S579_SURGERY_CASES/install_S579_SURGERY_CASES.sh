#!/bin/bash
# =============================================================================
#  install_S579_SURGERY_CASES.sh · kit S579 (session S325, 18-Oct-2026) · D735
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s579kit && cp -rp /root/deploy/repo/deploy_kits/S579_SURGERY_CASES /tmp/s579kit && bash /tmp/s579kit/install_S579_SURGERY_CASES.sh
#  (DRY=1 before bash: every gate, the walks and the probe, nothing written.)
#
#  THE OWNER, 18-Oct 10:51-11:39 IST: one record per surgery on the server -- the papers scanned or uploaded (pre-approval to
#  discharge, X-rays, scans, MLC, police memo), the implants vendor-wise and patient-wise, the vendors' ledgers (private to him),
#  the hospital's monthly payments entered against each patient; cash / credit (cashless, Ayushman, Deendayal); from the Case Pack.
#   /root/finance/finance_app.py          87cc4266 -> FA_TO   one guarded mount block + the unit for /finance/surgery (2 counted edits)
#   /root/finance/surgery_cases.py        NEW
#   /root/portal/portal.py                f8b059f6 -> PO_TO   the tile 'Surgery cases' + its section (2 counted edits)
#   /root/wa/casepack/casepack_page.html  08807cdf -> CP_TO   'Continue to surgery case' beside the chosen patient (1 counted edit)
#   /root/portal/tile_grants.json         merged: 'Surgery cases' added to shavez's extra and to bhawna's mask; version + 1
#   /root/wa/casepack/surgery_papers/     NEW folder (700), inside the Case Pack's tree the nightly encrypted backup carries
#  Data step (seed_s579.py, idempotent): nine surg_* tables; unit 'surgery'; shavez maker, manoj checker (only if the unit has none).
#  Restarts clinic-finance and clinic-portal. Housekeeping: /tmp/s578kit, /tmp/s573kit, /tmp/s576kit if present.
#  Red after placing: every file put back byte-identically, surgery_cases.py taken out, the grants file back, both restarted.
# =============================================================================
set -u
KIT="S579_SURGERY_CASES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"                      # the finance service's python
VPY="${VPY:-/root/wa/venv/bin/python3}"             # the portal's and the jobs' python
FIN="${FIN:-/root/finance}"; POR="${POR:-/root/portal}"; CPD="${CPD:-/root/wa/casepack}"
DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; POR_PORT="${POR_PORT:-8099}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
HOUSEKEEP="${HOUSEKEEP:-/tmp/s578kit /tmp/s573kit /tmp/s576kit}"
FA_FROM=87cc4266f9cd05f3633f23e1f36488a0; FA_TO=f2e86ca7919abc9e660b1bd5e811eebf
PO_FROM=f8b059f61fa8b885f024f4f4ce73e4f2; PO_TO=963911cc41eac1ef98677b54e1a17291
CP_FROM=08807cdfbfd595f6425f5cc277a38dbb; CP_TO=2dfe4221e5261216d5fbe7964cfc1520
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s579_inst_$STAMP"
HAVE_LOCK=0; PLACED=0
DBBAK="$FIN/finance.db.bak_S579_$STAMP"
B_FA="$FIN/finance_app.py.bak_S579_${FA_FROM:0:8}"; B_PO="$POR/portal.py.bak_S579_${PO_FROM:0:8}"
B_CP="$CPD/casepack_page.html.bak_S579_${CP_FROM:0:8}"; B_TG="$POR/tile_grants.json.bak_S579_$STAMP"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"); [ "$h" = "$2" ] && break; done; echo "$h"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting every file back"
  [ -f "$B_FA" ] && \cp -p "$B_FA" "$FIN/finance_app.py"
  [ -f "$B_PO" ] && \cp -p "$B_PO" "$POR/portal.py"
  [ -f "$B_CP" ] && \cp -p "$B_CP" "$CPD/casepack_page.html"
  [ -f "$B_TG" ] && \cp -p "$B_TG" "$POR/tile_grants.json"
  rm -f "$FIN/surgery_cases.py" "$FIN"/.*.s579 "$POR"/.*.s579 "$CPD"/.*.s579
  "$SYSTEMCTL" restart clinic-finance || true; "$SYSTEMCTL" restart clinic-portal || true
  say "   finance $(m5 "$FIN/finance_app.py") (expected $FA_FROM) · portal $(m5 "$POR/portal.py") (expected $PO_FROM) · case pack page $(m5 "$CPD/casepack_page.html") (expected $CP_FROM)"
  say "   health: finance $(health "http://127.0.0.1:$FIN_PORT/finance/healthz" 200) · portal $(health "http://127.0.0.1:$POR_PORT/portal/login" 200)"
  say "   the database backup stays: $DBBAK (the surg_* tables and the 'surgery' rows, if made, are additive and unused without the module)"
  say "   Send a photo of this screen to Claude."
  exit 1
}

say "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
say "[1/9] kit files: all match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
mkdir -p "$SCR/built" "$SCR/new" "$SCR/old" || stop "no scratch folder"

KSC=$(m5 "$KDIR/surgery_cases.py")
if [ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$FIN/surgery_cases.py")" = "$KSC" ] && [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] \
   && [ "$(m5 "$CPD/casepack_page.html")" = "$CP_TO" ] && grep -q '"Surgery cases"' "$POR/tile_grants.json"; then
  say "ALREADY INSTALLED (finance_app ${FA_TO:0:8}, surgery_cases ${KSC:0:8}, portal ${PO_TO:0:8}, case pack page ${CP_TO:0:8}, the grant)."
  exit 0
fi
[ "$(m5 "$FIN/finance_app.py")" = "$FA_FROM" ] || stop "$FIN/finance_app.py is $(m5 "$FIN/finance_app.py"), not the pinned $FA_FROM"
[ "$(m5 "$POR/portal.py")" = "$PO_FROM" ] || stop "$POR/portal.py is $(m5 "$POR/portal.py"), not the pinned $PO_FROM"
[ "$(m5 "$CPD/casepack_page.html")" = "$CP_FROM" ] || stop "$CPD/casepack_page.html is $(m5 "$CPD/casepack_page.html"), not the pinned $CP_FROM"
[ -e "$FIN/surgery_cases.py" ] && stop "$FIN/surgery_cases.py already exists and is not this kit's"
"$VPY" -c "import json,sys; d=json.load(open(sys.argv[1])); assert isinstance(d.get('users'),dict)" "$POR/tile_grants.json" 2>/dev/null \
  || stop "$POR/tile_grants.json does not read as the grants file"
say "[2/9] pins: finance_app ${FA_FROM:0:8} · portal ${PO_FROM:0:8} · case pack page ${CP_FROM:0:8} · grants file readable"

for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile surgery_cases.py walk_s579.py make_s579.py seed_s579.py probe_s579.py \
    || stop "the kit's python does not compile on $py"
done
"$APY" -B make_s579.py "$FIN/finance_app.py" "$POR/portal.py" "$CPD/casepack_page.html" "$SCR/built" >/dev/null || stop "the builder refused a live file"
[ "$(m5 "$SCR/built/finance_app.py")" = "$FA_TO" ] || stop "rebuilt finance_app.py is $(m5 "$SCR/built/finance_app.py"), not $FA_TO"
[ "$(m5 "$SCR/built/portal.py")" = "$PO_TO" ] || stop "rebuilt portal.py is $(m5 "$SCR/built/portal.py"), not $PO_TO"
[ "$(m5 "$SCR/built/casepack_page.html")" = "$CP_TO" ] || stop "rebuilt casepack_page.html is $(m5 "$SCR/built/casepack_page.html"), not $CP_TO"
PYTHONPYCACHEPREFIX="$SCR/pyc" "$APY" -m py_compile "$SCR/built/finance_app.py" || stop "rebuilt finance_app.py does not compile on $APY"
PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -m py_compile "$SCR/built/portal.py" 2>/dev/null || stop "rebuilt portal.py does not compile on $VPY"
say "[3/9] compiled on both pythons; rebuilt from the live bytes (2 + 2 + 1 counted edits) to finance_app ${FA_TO:0:8}, portal ${PO_TO:0:8}, page ${CP_TO:0:8}"

W1="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s579.py" "$KDIR/surgery_cases.py" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk.db" || stop "no scratch copy of the database for the walk"
W2="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s579.py" "$KDIR/surgery_cases.py" --db "$SCR/walk.db" 2>&1 | tail -1 )"
rm -f "$SCR/walk.db"
allgreen() { local g t; g=$(echo "$1" | sed -n 's/^walk_s579: \([0-9]*\) of \([0-9]*\) green$/\1/p'); t=$(echo "$1" | sed -n 's/^walk_s579: \([0-9]*\) of \([0-9]*\) green$/\2/p')
            [ -n "$g" ] && [ "$g" = "$t" ] && [ "$g" -ge 51 ]; }      # 53, or 51 where the database has no bank-statement table (2 bank checks skipped)
allgreen "$W1" || stop "the walk on a made-up database is not all green ($W1)"
allgreen "$W2" || stop "the walk on a copy of the live database is not all green ($W2)"
say "[4/9] the walk: made-up database $W1 · a copy of the live database $W2"

mk() { cp -p "$FIN"/*.py "$1/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$1/" 2>/dev/null
       for d in finance_ui spine vendor; do [ -d "$FIN/$d" ] && mkdir -p "$1/$d" && cp -rp "$FIN/$d/." "$1/$d/" 2>/dev/null; done; return 0; }
mk "$SCR/new"; mk "$SCR/old"
cp -p "$SCR/built/finance_app.py" "$KDIR/surgery_cases.py" "$SCR/new/"
copydb "$DB" "$SCR/new.db" && copydb "$DB" "$SCR/old.db" || stop "no scratch copy of the database for the probe"
"$APY" -B seed_s579.py "$SCR/new.db" "$KDIR/surgery_cases.py" >/dev/null || stop "the data step failed on a copy"
P1="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s579.py" --fin "$SCR/new" --db "$SCR/new.db" 2>&1 )"
P0="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s579.py" --fin "$SCR/old" --db "$SCR/old.db" --expect-red 2>&1 )"
echo "$P1" | grep -E "^  (ok|RED)" | sed 's/^/   /'
echo "$P1" | grep -q "^PROBE OK" || stop "the look as manoj and shavez through the real finance app is red on copies"
echo "$P0" | grep -q "^PROBE OK negative control" || stop "the negative control did not go red on the old files"
say "[5/9] the real finance app on copies: $(echo "$P1" | grep '^PROBE OK') · the old files: $(echo "$P0" | grep '^PROBE OK' | cut -c10-)"
rm -rf "$SCR/old" "$SCR"/*.db
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the probe green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

copydb "$DB" "$DBBAK" || stop "database backup failed"
\cp -p "$FIN/finance_app.py" "$B_FA" && \cp -p "$POR/portal.py" "$B_PO" && \cp -p "$CPD/casepack_page.html" "$B_CP" && \cp -p "$POR/tile_grants.json" "$B_TG" \
  || stop "a file backup failed"
[ "$(m5 "$B_FA")" = "$FA_FROM" ] && [ "$(m5 "$B_PO")" = "$PO_FROM" ] && [ "$(m5 "$B_CP")" = "$CP_FROM" ] || stop "a backup is not the live file"
say "[6/9] backups: $(basename "$DBBAK") (sqlite backup API); $(basename "$B_FA"), $(basename "$B_PO"), $(basename "$B_CP"), $(basename "$B_TG")"

PLACED=1
\cp -p "$KDIR/surgery_cases.py" "$FIN/.surgery_cases.py.s579" && mv -f "$FIN/.surgery_cases.py.s579" "$FIN/surgery_cases.py" && chmod 644 "$FIN/surgery_cases.py" || restore "placing surgery_cases.py"
\cp -p "$SCR/built/finance_app.py" "$FIN/.finance_app.py.s579" && mv -f "$FIN/.finance_app.py.s579" "$FIN/finance_app.py" || restore "placing finance_app.py"
\cp -p "$SCR/built/portal.py" "$POR/.portal.py.s579" && mv -f "$POR/.portal.py.s579" "$POR/portal.py" || restore "placing portal.py"
\cp -p "$SCR/built/casepack_page.html" "$CPD/.casepack_page.html.s579" && mv -f "$CPD/.casepack_page.html.s579" "$CPD/casepack_page.html" || restore "placing casepack_page.html"
[ "$(m5 "$FIN/finance_app.py")" = "$FA_TO" ] && [ "$(m5 "$POR/portal.py")" = "$PO_TO" ] && [ "$(m5 "$CPD/casepack_page.html")" = "$CP_TO" ] \
  && [ "$(m5 "$FIN/surgery_cases.py")" = "$KSC" ] || restore "a file did not land at its md5"
mkdir -p "$CPD/surgery_papers" && chmod 700 "$CPD/surgery_papers" || restore "the papers folder"
TG="$("$VPY" - "$POR/tile_grants.json" <<'PYEOF'
import json, os, sys
p = sys.argv[1]
d = json.load(open(p, encoding="utf-8"))
u = d.setdefault("users", {})
did = []
s = u.setdefault("shavez", {}); ex = s.setdefault("extra", [])
if "Surgery cases" not in ex:
    ex.append("Surgery cases"); did.append("shavez extra")
b = u.get("bhawna")
if isinstance(b, dict):
    mk = b.setdefault("mask", [])
    if "Surgery cases" not in mk:
        mk.append("Surgery cases"); did.append("bhawna mask")
if did:
    d["version"] = int(d.get("version") or 0) + 1
    tmp = p + ".s579tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(d, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    os.chmod(tmp, os.stat(p).st_mode & 0o777)
    os.replace(tmp, p)
json.load(open(p, encoding="utf-8"))
print("grants: %s; version %s" % (", ".join(did) or "already there", d.get("version")))
PYEOF
)" || restore "the grants file"
say "[7/9] placed; md5 read back: finance_app $(m5 "$FIN/finance_app.py") · surgery_cases $(m5 "$FIN/surgery_cases.py") · portal $(m5 "$POR/portal.py") · page $(m5 "$CPD/casepack_page.html") · $TG"

SOUT="$("$APY" -B seed_s579.py "$DB" "$FIN/surgery_cases.py" 2>&1)" || { echo "$SOUT"; restore "the data step"; }
say "[8/9] $SOUT"

"$SYSTEMCTL" restart clinic-finance || restore "restart clinic-finance"
"$SYSTEMCTL" restart clinic-portal || restore "restart clinic-portal"
c1=$(health "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
c2=$(health "http://127.0.0.1:$POR_PORT/portal/login" 200)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/surgery")
"$SYSTEMCTL" is-active --quiet clinic-finance && "$SYSTEMCTL" is-active --quiet clinic-portal || restore "a service is not active"
{ [ "$c1" = 200 ] && [ "$c2" = 200 ] && [ "$c3" = 302 ]; } || restore "health finance $c1 / portal $c2 / surgery page $c3 (302 expected without a login)"
MF=""
command -v "$JOURNALCTL" >/dev/null 2>&1 && MF="$("$JOURNALCTL" -u clinic-finance --since "-3 min" --no-pager 2>/dev/null | grep -E "surgery_cases NOT mounted" | head -1)"
[ -z "$MF" ] || restore "the module did not mount: $MF"
mkdir -p "$SCR/placed"; mk "$SCR/placed"; copydb "$DB" "$SCR/placed.db" || restore "no copy of the database for the look as manoj"
P2="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s579.py" --fin "$SCR/placed" --db "$SCR/placed.db" 2>&1 )"
echo "$P2" | grep -q "^PROBE OK" || { echo "$P2" | tail -12; restore "the look as manoj on the placed files is red"; }
PLACED=0
for d in $HOUSEKEEP; do [ -d "$d" ] && rm -rf "$d" && say "   housekeeping: removed $d"; done
say "[9/9] clinic-finance and clinic-portal restarted and active - health $c1 / $c2 - /finance/surgery $c3 without a login (the login gate) - $(echo "$P2" | grep '^PROBE OK')"
say ""
say "INSTALLED. Your portal now has the tile 'Surgery cases' (Clinic section); Shavez has it too, without the money pages."
say "In the Case Pack, after choosing a patient: 'Continue to surgery case'."
say "undo: see the README (every file has its .bak_S579 copy beside it)"
