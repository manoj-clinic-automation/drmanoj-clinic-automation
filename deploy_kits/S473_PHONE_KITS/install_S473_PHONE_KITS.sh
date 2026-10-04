#!/bin/bash
# =============================================================================
# install_S473_PHONE_KITS.sh -- session 293, 04-Oct-2026 -- the two phones' MacroDroid setups on the Clinic PCs page
#  THE OWNER, 04-Oct: "a full setup of that MacroDroid part for the reception mobile and for my mobile should also be there
#  in case it is required again".
#  EDIT, by apply_s473.py (exact anchors on the real bytes; every anchor found exactly once):
#   /root/finance/pc_kits.py   83f318d7 (S460) -> c172efb0   two phone cards on the page (now 'Clinic PCs & phones'); a button
#                               each -> MacroDroid_<phone>_<date>.mdr made at that moment from the repository's template with
#                               the LIVE key put in (the bank-SMS door's key on this box; the reception phone's token from
#                               the settings); the same owner gate and cross-site check as a PC button; the press logged
#  FILES THE PULL BRINGS: deploy_kits/PC_KITS/macrodroid/<phone>/macros.template.mdr + KIT_INFO.txt -- the owner's own exports
#   of 04-Oct with every key a placeholder and the geofence / cell-tower data blanked. No secret in the repository.
#  NOT TOUCHED: the three PC kits and their buttons, every door, the database, the keys themselves.
# Walked first, on this box, hermetically (F-709): the edited file in /tmp, a throwaway app, a scratch kits root, a made-up
# key and token made at run time. Restarts clinic-finance only (about 8 seconds); red after placing -> the file is put back.
# DRY=1 places nothing. NEEDS the build lock free (F-694).
# =============================================================================
set -u
KIT="S473_PHONE_KITS"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
REPO="${REPO:-/root/deploy/repo}"; PHONES="$REPO/deploy_kits/PC_KITS/macrodroid"
FINURL="${FINURL:-http://127.0.0.1:8106}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FROM=83f318d70abbaa2058aca97c0cbc2784; TO=708fd2030cdf7b13aa7232ba00ef4b7a
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="/tmp/s473_scratch_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
health() { curl -s -o /dev/null -m 10 -w '%{http_code}' "$@"; }
clean() { find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; rm -rf "$SCR" "$FIN/.pc_kits.py.s473"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }

md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
"$SPY" -c "import flask, werkzeug" 2>/dev/null || { say "!! [1/7] $SPY lacks flask - nothing installed"; exit 1; }
if ! mkdir "$LOCK" 2>/dev/null; then
  say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed."
  say "   Paste the same line again in a few minutes."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
trap 'rm -rf "$LOCK"' EXIT
say "[1/7] kit gates green (SUMS, KIT_ID, flask); the build lock is taken"

for ph in foldphone receptionmobile; do
  d="$PHONES/$ph"
  [ -f "$d/macros.template.mdr" ] && [ -f "$d/KIT_INFO.txt" ] || { say "!! [2/7] $d is not whole (the pull did not bring the template) - nothing installed"; exit 1; }
  want="$(sed -n 's/^template_md5=//p' "$d/KIT_INFO.txt" | tr -d '\r')"
  [ "$(m5 "$d/macros.template.mdr")" = "$want" ] || { say "!! [2/7] $d/macros.template.mdr is not what its KIT_INFO says - nothing installed"; exit 1; }
  grep -q '{{BANK_SMS_KEY}}\|{{PHONE_TOKEN}}' "$d/macros.template.mdr" || { say "!! [2/7] $d template carries no placeholder - nothing installed"; exit 1; }
done
HAVE="$(m5 "$FIN/pc_kits.py")"
if [ "$HAVE" = "$TO" ]; then say "-- ALREADY INSTALLED: pc_kits.py is at the kit's pin; the two templates whole; clinic-finance $(systemctl is-active clinic-finance 2>/dev/null)"; exit 0; fi
[ "$HAVE" = "$FROM" ] || { say "!! [2/7] $FIN/pc_kits.py is $HAVE, not $FROM (S460) - another kit changed it after this one was built. Nothing installed; tell the assistant, the kit is rebuilt on the new file."; exit 1; }
[ -f "$FIN/bank_sms.key" ] || say "   note: $FIN/bank_sms.key is not there -- the fold phone's button will answer 'Not made' until it is (the reception button is unaffected)"
say "[2/7] pc_kits.py at its S460 pin; both templates whole, placeholders in, nothing secret"

mkdir -p "$SCR" && \cp -p "$FIN/pc_kits.py" "$SCR/pc_kits.py" || { say "!! [3/7] no scratch copy - nothing installed"; clean; exit 1; }
"$SPY" -B apply_s473.py "$SCR/pc_kits.py" >/dev/null 2>"$SCR/apply.err" || { say "!! [3/7] the edits did not apply: $(tail -1 "$SCR/apply.err" | cut -c1-200) - nothing installed"; clean; exit 1; }
[ "$(m5 "$SCR/pc_kits.py")" = "$TO" ] || { say "!! [3/7] the edited scratch copy is not its predicted bytes - nothing installed"; clean; exit 1; }
"$SPY" -m py_compile apply_s473.py walk_s473.py "$SCR/pc_kits.py" 2>/dev/null || { say "!! [3/7] compile failed - nothing installed"; clean; exit 1; }
find "$KDIR" "$SCR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
say "[3/7] the five edits apply to a scratch copy and give the predicted bytes; compiles"

WOUT="$( cd /tmp && timeout 600 "$SPY" -B "$KDIR/walk_s473.py" --apply "$KDIR/apply_s473.py" --finance "$FIN" --kits "$REPO/deploy_kits/PC_KITS" 2>&1 )"
echo "$WOUT" | grep -E '^  FAIL|^WALK_S473' | cut -c1-400 | sed 's/^/   /'
echo "$WOUT" | tail -1 | grep -q "^WALK_S473 GREEN" || { say "!! [4/7] walk red - nothing installed"; echo "$WOUT" | tail -25 | cut -c1-400; clean; exit 1; }
[ "$(m5 "$FIN/pc_kits.py")" = "$FROM" ] || { say "!! [4/7] pc_kits.py changed during the walk - nothing installed"; clean; exit 1; }
say "[4/7] walk green on this box: the templates whole and secret-free; the page with both phone cards; a press makes the file with a made-up key in and no placeholder left; a cross-site press, an unknown phone and a box that cannot read the key are refused without a file"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING placed, nothing restarted"; clean; exit 0; fi

BA="$FIN/pc_kits.py.bak_S473_$(echo "$FROM" | cut -c1-8)"
\cp -p "$FIN/pc_kits.py" "$BA" && [ "$(m5 "$BA")" = "$FROM" ] || { say "!! [5/7] the backup failed - nothing placed"; clean; exit 1; }
say "[5/7] backup: $BA"
restore() {
  say "!! RED after placing ($1) - restoring"
  \cp -p "$BA" "$FIN/pc_kits.py"
  systemctl restart clinic-finance 2>/dev/null || true; sleep 7
  say "   pc_kits.py $(m5 "$FIN/pc_kits.py") · finance healthz $(health "$FINURL/finance/healthz")"
  clean; exit 1
}
\cp -p "$FIN/pc_kits.py" "$FIN/.pc_kits.py.s473" && cat "$SCR/pc_kits.py" > "$FIN/.pc_kits.py.s473" && [ "$(m5 "$FIN/.pc_kits.py.s473")" = "$TO" ] || { say "!! [6/7] could not stage the new file - nothing placed"; clean; exit 1; }
mv -f "$FIN/.pc_kits.py.s473" "$FIN/pc_kits.py" || restore "placing pc_kits.py"
[ "$(m5 "$FIN/pc_kits.py")" = "$TO" ] || restore "md5 read-back of pc_kits.py"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart clinic-finance || restore "restart clinic-finance"
sleep 8
systemctl is-active --quiet clinic-finance || restore "clinic-finance not active"
c1=$(health "$FINURL/finance/healthz"); [ "$c1" = 200 ] || restore "finance healthz $c1"
c2=$(health "$FINURL/finance/pcs"); case "$c2" in 302|401) ;; *) restore "/finance/pcs answered $c2 without a login";; esac
c3=$(health -X POST "$FINURL/finance/pcs/phone/foldphone"); case "$c3" in 302|401|403) ;; *) restore "/finance/pcs/phone answered $c3 without a login";; esac
D4="$(curl -s -m 10 "$FINURL/finance/api/pc-kit/fetch?part=kit")"
echo "$D4" | grep -q 'Clinic PCs page' || restore "the kit door (S450) no longer answers"
D1="$(curl -s -m 10 -X POST --data-binary '{}' "$FINURL/finance/api/reception/heartbeat")"
echo "$D1" | grep -q '"NOT_YOU"' || restore "the heartbeat door no longer refuses an unsigned heartbeat: $(echo "$D1" | cut -c1-160)"
journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -q "NOT mounted" && restore "a module NOT mounted"
JR="$(journalctl -u clinic-finance --since "$T0" --no-pager 2>/dev/null | grep -c 'Traceback\|SyntaxError\|NameError\|AssertionError')"
[ "${JR:-0}" = 0 ] || restore "clinic-finance journal: $JR error line(s)"
say "[6/7] placed, md5 read back = the kit's pin · clinic-finance active · healthz 200 · /finance/pcs $c2 and the phone button $c3 (the login gate) · the kit and heartbeat doors answer as before · every part mounted · journal clean"
say "[7/7] the two phone cards are on https://followup.dr-manoj.in/finance/pcs for the owner's login"
clean
say "all green -- $KIT: DONE."
md5sum "$FIN/pc_kits.py"
