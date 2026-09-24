#!/bin/bash
# =============================================================================
#  install_S393_PETTY_FOLD.sh · kit S393_PETTY_FOLD (session 279, 24-Sep-2026)
#
#  The owner 24-Sep: Bhati's book did not match his paper book -- one 9,000 Shavez top-up had been saved three
#  times (22-Sep 21:29:26 / :38 / :55) and Dr Bhawna's 20,000 twice. Those were cancelled and the opening cash 440
#  set on his word (in hand 14,420 = the paper book). Cause: the save had no guard against a repeated tap.
#  And: "maximum sections visible on a single screen without scrolling, as a collapsible expandable system."
#
#  S393: /root/finance/petty_book.py 88f28571 -> S393 (pin below)
#   * the same entry (kind, person, name, amount) by the same person within 10 minutes is refused with a Hindi
#     message ("abhi-abhi save ho chuki"); another amount, another person, or after 10 minutes is allowed;
#   * the doctors' page and Bhati's page become folds: a strip with today / in hand / loan always on top, each
#     section one line with its figure, one open at a time -- still no JavaScript. Both fit one phone screen.
#  Restarts clinic-finance only.
#
#  Run by (one line on the VPS):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S393_PETTY_FOLD/install_S393_PETTY_FOLD.sh
# =============================================================================
set -u
KIT="S393_PETTY_FOLD"; KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"; SPY="${SPY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"; DBF="${FINANCE_DB:-$FIN/finance.db}"; FPORT="${FIN_PORT:-8106}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s393_walk_$STAMP"
S_FROM=88f2857193938a493f20c9c31f672d1e; S_TO=3bf8d2304c5ee8108875a606e6db03f1
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
code() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ "$(m5 petty_book.py)" = "$S_TO" ] || { say "!! [1/6] kit petty_book.py not at its pin - nothing installed"; exit 1; }
say "[1/6] kit gates green"
[ "$(m5 "$FIN/petty_book.py")" = "$S_TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
[ "$(m5 "$FIN/petty_book.py")" = "$S_FROM" ] || { say "!! [2/6] petty_book.py is $(m5 "$FIN/petty_book.py"), not the pinned S300 - nothing installed"; exit 1; }
say "[2/6] live pin exact (petty_book S300 88f28571)"
mkdir -p "$WALK/fin" && \cp -p petty_book.py "$WALK/fin/" || exit 1
"$VPY" -B -m py_compile "$WALK/fin/petty_book.py" walk_s393.py || { say "!! [3/6] compile failed - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[3/6] py_compile green"
"$SPY" -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro'%sys.argv[1],uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$DBF" "$WALK/scratch.db" \
  || { say "!! [4/6] no scratch copy of the database - nothing installed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && FINANCE_DB="$WALK/scratch.db" timeout 180 "$VPY" -B "$KDIR/walk_s393.py" "$WALK/fin" "$FIN/petty_book.py" 2>&1 | tail -1 )"
rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [4/6] walk red: $WOUT - nothing installed"; exit 1; }
say "[4/6] $WOUT (scratch copy of the live database; the live petty_book.py is the negative control)"
BS="$FIN/petty_book.py.bak_S393_88f28571"
\cp -p "$FIN/petty_book.py" "$BS" || { say "!! [5/6] backup failed - nothing placed"; exit 1; }
restore() {
  say "!! RED after placing (${1:-a check failed}) - restoring byte-identically"
  \cp -p "$BS" "$FIN/petty_book.py"; systemctl restart clinic-finance || true; sleep 5
  say "   petty_book $(m5 "$FIN/petty_book.py") · finance $(code "http://127.0.0.1:$FPORT/finance/healthz")"; exit 1
}
\cp -p petty_book.py "$FIN/petty_book.py" && [ "$(m5 "$FIN/petty_book.py")" = "$S_TO" ] || restore "petty_book.py did not read back"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "clinic-finance would not restart"
sleep 5; systemctl is-active --quiet clinic-finance || restore "clinic-finance not active after restart"
H=$(code "http://127.0.0.1:$FPORT/finance/healthz"); PC=$(code "http://127.0.0.1:$FPORT/finance/petty")
[ "$H" = 200 ] || restore "finance healthz answered $H"
{ [ "$PC" = 302 ] || [ "$PC" = 401 ] || [ "$PC" = 403 ]; } || restore "the petty book without login answered $PC"
J="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null)"
echo "$J" | grep -q "petty_book NOT mounted" && restore "$(echo "$J" | grep -m1 "petty_book NOT mounted" | cut -c1-200)"
echo "$J" | grep -q 'petty_book.py", line' && restore "a fault inside petty_book.py: $(echo "$J" | grep -m1 -A1 'petty_book.py", line' | tail -1 | cut -c1-160)"
say "[5/6] placed; finance healthz $H · petty book without login $PC (locked) · backup beside the file"
md5sum "$FIN/petty_book.py"
say "[6/6] $KIT: DONE -- read next: https://followup.dr-manoj.in/finance/petty"
