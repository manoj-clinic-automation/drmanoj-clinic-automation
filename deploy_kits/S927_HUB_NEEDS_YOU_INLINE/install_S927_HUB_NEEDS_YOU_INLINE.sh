#!/bin/bash
# =============================================================================
#  install_S927_HUB_NEEDS_YOU_INLINE.sh · kit S927 (22-Nov-2026, Sanjeevni session 502) · the owner's word 12:08 IST on mock-up v1
#   NEW /root/finance/hub_panels.py : every Needs-you line opens INLINE on his Sanjeevni Hub with the thing itself and its own buttons --
#        the purchase flow's S926 section; an arrival counted and not in Marg (the order line, the scan with its read lines, Marg's purchases from
#        that dealer since, the stock; Ask Amir to enter it · It is this Marg line · Never came); goods tapped with no bill (read); a count voucher
#        Marg never moved (Ask Amir again); the expiry list; Seen on an information line (30 days). Mounted by sanjeevni_day.init beside hub_cash.
#   /root/finance/sanjeevni_day.py       69c2921e -> TO : the mount (one try block).
#   /root/finance/sanjeevni_approvals.py a1a09d24 -> TO : the lines decorated before S761 groups them (panel, ref, since/age; Seen out; the
#        'Orthotic shortages' line retired while the purchase-flow line stands).
#   /root/finance/stock_watch.py         1a8c98c6 -> TO : the arrival line carries its order line id and its moment.
#   /root/finance/finance_ui/finance_approvals.html f00db25d -> TO : '▾ open here' on each line, the panel loader, three tiers, the age chip,
#        the arrived group drawn one line per item.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s927kit && cp -rp /root/deploy/repo/deploy_kits/S927_HUB_NEEDS_YOU_INLINE /tmp/s927kit && bash /tmp/s927kit/install_S927_HUB_NEEDS_YOU_INLINE.sh
#  (DRY=1 before bash: every gate and the walk; NOTHING written.)
# =============================================================================
set -u
KIT="S927_HUB_NEEDS_YOU_INLINE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
REPO_KITS="${REPO_KITS:-/root/deploy/repo/deploy_kits}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
LIVE_DB="${LIVE_DB:-$ROOT/finance/finance.db}"
NAMES=("finance/hub_panels.py" "finance/sanjeevni_day.py" "finance/sanjeevni_approvals.py" "finance/stock_watch.py" "finance/finance_ui/finance_approvals.html")
FROMS=("absent" "69c2921e69996f5524237e23d289d648" "a1a09d243b483bb5ec299460c67a23bd" "1a8c98c6c11f5d33d415b3c485bdc918" "f00db25df9315b427cf0eb7c1b2b9283")   # read from the live bytes, never typed from a prefix (F-1480)
KF=("hub_panels.py" "sanjeevni_day.py" "sanjeevni_approvals.py" "stock_watch.py" "finance_approvals.html")
N=5; IDX="0 1 2 3 4"
TOS=(); for k in $IDX; do TOS[$k]="$(awk -v f="${NAMES[$k]}" '$2==f{print $1}' "$KDIR/TO_PINS.md5")"; done
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s927_inst_$STAMP"; TOOK_LOCK=0; PLACING=0
# the earlier kits' own proofs run on the new files too (the S837 rule: the install stops only on a check WORSE than the live files);
# these checks changed BY DESIGN with S926 (the team row is a shortage, not a tap; two texts) and are allowed to differ:
# ALLOWED_DIFF (unused here)="team = the open 'Ab nahi milta' rows|Wait — order next week|wait_pass: on the day it becomes keep ordering|the waited medicine is back on the list|Substitute aaya on the team list|its out-of-stock count is the team list's"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
cur() { [ -f "$ROOT/${NAMES[$1]}" ] && m5 "$ROOT/${NAMES[$1]}" || echo absent; }
say() { echo "$@"; }
bak() { echo "$ROOT/${NAMES[$1]}.bak_S927_${FROMS[$1]:0:8}"; }
stg() { local n="${NAMES[$1]}"; echo "$(dirname "$ROOT/$n")/.$(basename "$n").s927"; }
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
door() { if [ -n "${DOOR_CMD:-}" ]; then $DOOR_CMD "$1"; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT$1"; fi; }
# the service's own log since the restart proves the module loaded (F-1554): every door of the flow is login-gated, a page cannot prove it
flog() { if [ -n "${LOG_CMD:-}" ]; then $LOG_CMD; else journalctl -u "$FSVC" --since "@$T0" --no-pager 2>/dev/null; fi; }
wait200() { local h=000; for _t in $(seq 1 20); do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { for k in $IDX; do rm -f "$(stg $k)"; done; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
restore() { PLACING=0; trap '' HUP INT TERM; say "!! RED after placing ($1) - putting everything back"
  for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then rm -f "$ROOT/${NAMES[$k]}"; else [ -f "$(bak $k)" ] && \cp -p "$(bak $k)" "$ROOT/${NAMES[$k]}"; fi; done
  "$SYSTEMCTL" restart "$FSVC" || true
  for k in $IDX; do say "   ${NAMES[$k]} $(cur $k | cut -c1-8) (expected ${FROMS[$k]:0:8})"; done
  say "   $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
on_sig() { if [ "$PLACING" = 1 ]; then restore "the session was interrupted while placing"; fi; say "!! interrupted - nothing placed"; release_lock; exit 1; }
trap on_sig HUP INT TERM
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 900 "$VPY" -u -W ignore -B "$@" 2>&1); }
fails() { echo "$1" | grep '^FAIL' | sed 's/^FAIL //' | cut -d'(' -f1 | sed 's/ *$//' | sort -u; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for k in $IDX; do [ -n "${TOS[$k]}" ] && [ "$(m5 "$KDIR/${KF[$k]}")" = "${TOS[$k]}" ] || { say "!! [1/6] the kit's ${KF[$k]} is not at its TO pin - nothing installed"; exit 1; }; done
ALL=1; for k in $IDX; do [ "$(cur $k)" = "${TOS[$k]}" ] || ALL=0; done
if [ "$ALL" = 1 ]; then say "$KIT: ALREADY INSTALLED - the files are at the new version."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/6] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/6] kit gates green; the build lock taken by $KIT"
else say "!! [1/6] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for k in $IDX; do [ "$(cur $k)" = "${FROMS[$k]}" ] || { [ "${FROMS[$k]}" = absent ] && [ "$(cur $k)" = "${TOS[$k]}" ]; } || stop "!! [2/6] $ROOT/${NAMES[$k]} is $(cur $k | cut -c1-8), expected ${FROMS[$k]:0:8} - STOP, nothing installed. Tell Claude."; done   # a NEW file left by an undo at its TO is fine
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/hub_panels.py" "$KDIR/sanjeevni_day.py" "$KDIR/sanjeevni_approvals.py" "$KDIR/stock_watch.py" "$KDIR/walk_s927.py" || stop "!! [2/6] a file does not compile on $p - nothing installed"; done
say "[2/6] the live files at their FROM pins; the kit's python compiles on both pythons"
mkdir -p "$SCR/new" "$SCR/old" && \cp -p "$ROOT"/finance/*.py "$ROOT"/finance/*.html "$ROOT"/finance/*.sql "$ROOT"/finance/*.json "$SCR/new/" 2>/dev/null; \cp -p "$ROOT"/shared/*.py "$SCR/new/" 2>/dev/null
\cp -rp "$SCR/new/." "$SCR/old/"
mkdir -p "$SCR/new/finance_ui" && \cp -p "$ROOT"/finance/finance_ui/* "$SCR/new/finance_ui/" 2>/dev/null; \cp -p "$ROOT"/finance/finance_ui/finance_approvals.html "$SCR/old/" 2>/dev/null
for k in $IDX; do \cp -p "$KDIR/${KF[$k]}" "$SCR/new/" || stop "!! [3/6] could not lay out the walk - nothing installed"; done
\cp -p "$KDIR/finance_approvals.html" "$SCR/new/finance_ui/finance_approvals.html"
copydb() { py -c "import sqlite3,sys; s=sqlite3.connect('file:%s?mode=ro' % sys.argv[1], uri=True); d=sqlite3.connect(sys.argv[2]); s.backup(d); d.close(); s.close()" "$LIVE_DB" "$1" >/dev/null && [ -s "$1" ]; }
copydb "$SCR/copy.db" || stop "!! [3/6] could not take a copy of the database for the walk - nothing installed"
W1=$(py "$KDIR/walk_s927.py" "$SCR/new" "$SCR/copy.db"); R1=$(echo "$W1" | tail -1)
echo "$W1" | grep "^INFO" | cut -c1-200
[ "$R1" = "RESULT: ALL PASS" ] || { echo "$W1" | grep "^RED" | cut -c1-160; stop "!! [3/6] the walk on a copy of the live database: $R1 - nothing installed"; }
W0=$(py "$KDIR/walk_s927.py" "$SCR/old" "$SCR/copy.db" --control); R0=$(echo "$W0" | tail -1)
case "$R0" in "RESULT: "*FAIL) ;; *) stop "!! [3/6] the control did not go red ($R0) - nothing installed";; esac
say "[3/6] S927's walk on a copy of the live database: $(echo "$W1" | grep -c '^ok') checks pass; the control goes red as it must"
rm -f "$SCR/copy.db"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walks green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/6] finance healthz $f0 before the install - nothing installed"
for k in $IDX; do if [ "${FROMS[$k]}" = absent ]; then [ ! -e "$ROOT/${NAMES[$k]}" ] || [ "$(cur $k)" = "${TOS[$k]}" ] || stop "!! [4/6] $ROOT/${NAMES[$k]} already exists with other bytes - nothing placed"; continue; fi
  { \cp -p "$ROOT/${NAMES[$k]}" "$(bak $k)" && [ "$(m5 "$(bak $k)")" = "${FROMS[$k]}" ]; } || stop "!! [4/6] could not write the backup of ${NAMES[$k]} - nothing placed"; done
for k in $IDX; do s="$(stg $k)"; ref="$ROOT/${NAMES[$k]}"; [ -e "$ref" ] || ref="$ROOT/finance/sanjeevni_day.py"
  { cat "$KDIR/${KF[$k]}" > "$s" && chmod --reference="$ref" "$s" 2>/dev/null; chown --reference="$ref" "$s" 2>/dev/null; [ "$(m5 "$s")" = "${TOS[$k]}" ]; } || stop "!! [4/6] could not stage ${KF[$k]} - nothing placed"; done
PLACING=1
for k in $IDX; do mv -f "$(stg $k)" "$ROOT/${NAMES[$k]}" || restore "the rename of ${KF[$k]}"; [ "$(cur $k)" = "${TOS[$k]}" ] || restore "read back of ${KF[$k]}"; done
T0=$(date +%s); "$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/6]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
d1=$(door /finance/sanjeevni/api/needs-you/healthz); [ "$d1" = 200 ] || restore "hub_panels healthz answers $d1 (not mounted)"
d2=$(door /finance/sanjeevni/api/needs-you); case "$d2" in 404|000|5*) restore "the Needs-you door answers $d2";; esac
d3=$(door /finance/sanjeevni/approvals); case "$d3" in 404|000|5*) restore "his Hub page answers $d3";; esac
sleep "${NAP:-3}"; bad=$(flog | grep -E "hub_panels not mounted|hub_cash not mounted|S927 .* failed|Traceback" | head -3)
[ -z "$bad" ] || restore "the service log after the restart: $(echo "$bad" | head -1 | cut -c1-120)"
PLACING=0
say "[4/6] the five files placed and read back; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1, hub_panels healthz $d1, the Needs-you door $d2 and his Hub $d3 (login-gated), the service log clean since the restart"
release_lock
say "[5/6] what changes now: his Sanjeevni Hub's Needs-you -- three tiers, every line with 'open here' (the thing itself and its buttons), the age on old lines, the arrivals one per item."
say "[6/6] undo (one line): bash /root/deploy/repo/deploy_kits/$KIT/undo_s927.sh  (the four patched files back, hub_panels.py left in place unmounted, $FSVC restarted; hub_seen and Amir's jobs stay, harmless)"
say ""
say "$KIT: DONE."
exit 0
