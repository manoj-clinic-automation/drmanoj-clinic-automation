#!/bin/bash
# =============================================================================
#  install_S581_SURGERY_FIXES.sh · kit S581 (session S325, 18-Oct-2026) · D735
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s581kit && cp -rp /root/deploy/repo/deploy_kits/S581_SURGERY_FIXES /tmp/s581kit && bash /tmp/s581kit/install_S581_SURGERY_FIXES.sh
#  (DRY=1 before bash: every gate, the walks and the probe, nothing written.)
#
#  The fixes from the live dummy-case test of S579 (18-Oct 12:18-12:27 IST, at the owner's word 12:17):
#   /root/finance/surgery_cases.py   e56e3f52 -> KSC   (the only file; whole-file replacement of the parent's own S579 module)
#   - a removed case's / payment's papers stop opening · "Still due after this payment" · Indian grouping (1,50,000)
#   - '— choose —' first in every removal list · the UTR shown · the quantity column · a vendor with no entries can be taken off
#     the lists (marked; the same name written again brings it back) · the vendor page's wording · the scanner page's one title
#  Data: one column added on the first request (surg_vendor.hidden, default ''). Restarts clinic-finance only.
#  Red after placing: the S579 file put back, restart, health.
# =============================================================================
set -u
KIT="S581_SURGERY_FIXES"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
FIN="${FIN:-/root/finance}"; DB="${DB:-$FIN/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"; JOURNALCTL="${JOURNALCTL:-journalctl}"
FROM=e56e3f52da0336a83199c8e51c5f8c74
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="${TMPW:-/tmp}/s581_inst_$STAMP"
HAVE_LOCK=0
BAK="$FIN/surgery_cases.py.bak_S581_${FROM:0:8}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
copydb() { "$APY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$1" "$2"; }
health() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"); [ "$h" = "$2" ] && break; done; echo "$h"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting the S579 file back"
  [ -f "$BAK" ] && \cp -p "$BAK" "$FIN/surgery_cases.py"
  "$SYSTEMCTL" restart clinic-finance || true
  say "   surgery_cases.py $(m5 "$FIN/surgery_cases.py") (expected $FROM) · health $(health "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)"
  say "   (the added column surg_vendor.hidden is harmless to the S579 module.) Send a photo of this screen to Claude."
  exit 1
}
allgreen() { local g t; g=$(echo "$1" | sed -n 's/^walk_s581: \([0-9]*\) of \([0-9]*\) green$/\1/p'); t=$(echo "$1" | sed -n 's/^walk_s581: \([0-9]*\) of \([0-9]*\) green$/\2/p')
            [ -n "$g" ] && [ "$g" = "$t" ] && [ "$g" -ge 65 ]; }      # 67, or 65 where the database has no bank-statement table

say "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
say "[1/7] kit files: all match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
mkdir -p "$SCR/new" || stop "no scratch folder"
KSC=$(m5 "$KDIR/surgery_cases.py")
if [ "$(m5 "$FIN/surgery_cases.py")" = "$KSC" ]; then say "ALREADY INSTALLED (surgery_cases ${KSC:0:8})."; exit 0; fi
[ "$(m5 "$FIN/surgery_cases.py")" = "$FROM" ] || stop "$FIN/surgery_cases.py is $(m5 "$FIN/surgery_cases.py"), not the pinned $FROM (S579)"
grep -q "S579_SURGERY_CASES begin" "$FIN/finance_app.py" || stop "the finance app does not carry the S579 mount"
say "[2/7] pin: surgery_cases.py ${FROM:0:8} (S579), the mount present"
for py in "$APY" "$VPY"; do
  PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -m py_compile surgery_cases.py walk_s581.py probe_s581.py || stop "the kit's python does not compile on $py"
done
say "[3/7] compiled on both pythons"
W1="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s581.py" "$KDIR/surgery_cases.py" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk.db" || stop "no scratch copy of the database for the walk"
W2="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s581.py" "$KDIR/surgery_cases.py" --db "$SCR/walk.db" 2>&1 | tail -1 )"
copydb "$DB" "$SCR/walk0.db"
W0="$( cd /tmp && timeout 600 "$APY" -B "$KDIR/walk_s581.py" "$FIN/surgery_cases.py" --db "$SCR/walk0.db" 2>&1 | tail -1 )"
rm -f "$SCR"/walk*.db
allgreen "$W1" || stop "the walk on a made-up database is not all green ($W1)"
allgreen "$W2" || stop "the walk on a copy of the live database is not all green ($W2)"
allgreen "$W0" && stop "the control did not go red: the walk passes the live S579 module too ($W0)"
say "[4/7] the walk: made-up $W1 · a copy of the live database $W2 · the live S579 module (control) $W0"
cp -p "$FIN"/*.py "$SCR/new/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/new/" 2>/dev/null
for d in finance_ui spine vendor; do [ -d "$FIN/$d" ] && mkdir -p "$SCR/new/$d" && cp -rp "$FIN/$d/." "$SCR/new/$d/" 2>/dev/null; done
cp -p "$KDIR/surgery_cases.py" "$SCR/new/"
copydb "$DB" "$SCR/new.db" || stop "no scratch copy of the database for the probe"
P1="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s581.py" --fin "$SCR/new" --db "$SCR/new.db" 2>&1 )"
echo "$P1" | grep -q "^PROBE OK" || { echo "$P1" | tail -12; stop "the look as manoj and shavez through the real finance app is red on copies"; }
say "[5/7] the real finance app on copies: $(echo "$P1" | grep '^PROBE OK')"
rm -rf "$SCR/new" "$SCR"/*.db
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the probe green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

\cp -p "$FIN/surgery_cases.py" "$BAK" && [ "$(m5 "$BAK")" = "$FROM" ] || stop "the backup of surgery_cases.py failed"
\cp -p "$KDIR/surgery_cases.py" "$FIN/.surgery_cases.py.s581" && mv -f "$FIN/.surgery_cases.py.s581" "$FIN/surgery_cases.py" && chmod 644 "$FIN/surgery_cases.py" || restore "placing"
[ "$(m5 "$FIN/surgery_cases.py")" = "$KSC" ] || restore "the file did not land at its md5"
say "[6/7] placed: surgery_cases.py $KSC (the S579 file kept as $(basename "$BAK"))"
"$SYSTEMCTL" restart clinic-finance || restore "restart clinic-finance"
c1=$(health "http://127.0.0.1:$FIN_PORT/finance/healthz" 200)
c3=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/surgery")
"$SYSTEMCTL" is-active --quiet clinic-finance || restore "clinic-finance is not active"
{ [ "$c1" = 200 ] && [ "$c3" = 302 ]; } || restore "health $c1 / surgery page $c3 (302 expected without a login)"
MF=""
command -v "$JOURNALCTL" >/dev/null 2>&1 && MF="$("$JOURNALCTL" -u clinic-finance --since "-3 min" --no-pager 2>/dev/null | grep -E "surgery_cases NOT mounted" | head -1)"
[ -z "$MF" ] || restore "the module did not mount: $MF"
mkdir -p "$SCR/placed"; cp -p "$FIN"/*.py "$SCR/placed/" 2>/dev/null; cp -p "$FIN"/*.html "$FIN"/*.json "$FIN"/*.sql "$SCR/placed/" 2>/dev/null
for d in finance_ui spine vendor; do [ -d "$FIN/$d" ] && mkdir -p "$SCR/placed/$d" && cp -rp "$FIN/$d/." "$SCR/placed/$d/" 2>/dev/null; done
copydb "$DB" "$SCR/placed.db" || restore "no copy of the database for the look as manoj"
P2="$( cd /tmp && timeout 300 "$APY" -B "$KDIR/probe_s581.py" --fin "$SCR/placed" --db "$SCR/placed.db" 2>&1 )"
echo "$P2" | grep -q "^PROBE OK" || { echo "$P2" | tail -12; restore "the look as manoj on the placed file is red"; }
[ -d /tmp/s579kit ] && rm -rf /tmp/s579kit && say "   housekeeping: removed /tmp/s579kit"
say "[7/7] clinic-finance restarted and active - health $c1 - /finance/surgery $c3 without a login (the login gate) - $(echo "$P2" | grep '^PROBE OK')"
say ""
say "INSTALLED. Surgery cases: amounts as 1,50,000; 'Still due after this payment'; removed records' papers closed; vendors with no"
say "entries can be taken off the lists; the UTR and the quantity shown."
say "undo: \\cp -p $BAK $FIN/surgery_cases.py && systemctl restart clinic-finance"
