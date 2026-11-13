#!/bin/bash
# =============================================================================
#  install_S814_MARG_WATCH_ASK.sh · kit S814 (13-Nov-2026, Sanjeevni sessions 445-446) · the owner's "Ok" of 09:24 IST on the Ask mock-up (D956)
#  The Marg watch, Ask (plan v4 section 8):
#  1. /root/finance/marg_billwatch.py e6b4e534 -> TO : an Ask box on every open row of A and B -- whom (Amir on his card; Darpan or Shavez by
#     copy / WhatsApp), the message as it will go (it starts at the matter, D927), the answer back on the row, amber at two days; the answer
#     notice switch (OFF). New tables marg_watch_ask, marg_watch_ask_row (made by the page itself).
#  2. /root/finance/amir_day.py       49e1eba1 -> TO : one new kind on his one-time jobs card, first: "Doctor sahab ka sawaal", one tap per answer.
#  3. /root/finance/owner_notice.py   bf3da532 -> TO : one line to his phone when a staff answer comes back -- OFF until he turns it on.
#  All three REBUILT HERE from the live bytes (make_s814a/b/c.py), checked against the TO pins. clinic-finance is restarted.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s814kit && cp -rp /root/deploy/repo/deploy_kits/S814_MARG_WATCH_ASK /tmp/s814kit && bash /tmp/s814kit/install_S814_MARG_WATCH_ASK.sh
#  (DRY=1 before bash: every gate, the walks and the control; NOTHING written.)
# =============================================================================
set -u
KIT="S814_MARG_WATCH_ASK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; DB="${DB:-$ROOT/finance/finance.db}"; SPDB="${SPDB:-$ROOT/finance/spine/spine.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
FIN_PORT="${FIN_PORT:-8106}"; FSVC="${FSVC:-clinic-finance}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"
FA="finance/amir_day.py"; FW="finance/marg_billwatch.py"; FN="finance/owner_notice.py"
FROM_A="49e1eba1ac3190ee2afc03b192df13c0"; FROM_W="e6b4e53490416c6e62ae9299e6891bc6"; FROM_N="bf3da53250c02ca83bd11a2d0ba8daa3"
pin() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
TO_A="$(pin "$FA")"; TO_W="$(pin "$FW")"; TO_N="$(pin "$FN")"
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s814_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK_A="$ROOT/$FA.bak_S814_${FROM_A:0:8}"; BAK_W="$ROOT/$FW.bak_S814_${FROM_W:0:8}"; BAK_N="$ROOT/$FN.bak_S814_${FROM_N:0:8}"
fhz() { if [ -n "${HEALTH_CMD:-}" ]; then $HEALTH_CMD /finance/healthz; else curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$FIN_PORT/finance/healthz"; fi; }
wait200() { local h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep "${NAP:-3}"; h=$(fhz); [ "$h" = 200 ] && break; done; echo "$h"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$ROOT/finance/.amir_day.py.s814" "$ROOT/finance/.marg_billwatch.py.s814" "$ROOT/finance/.owner_notice.py.s814"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
# the old card does not know kind 'ask': on any way back, an open question is closed as withdrawn (the owner's row keeps the ask)
WD_PY="import sqlite3,sys,datetime;c=sqlite3.connect(sys.argv[1],timeout=30);t={r[0] for r in c.execute('SELECT name FROM sqlite_master WHERE type=\'table\'')};n=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S');c.execute('UPDATE amir_job SET done_at=?, done_how=\'withdrawn_S814\' WHERE kind=\'ask\' AND done_at IS NULL',(n,)) if 'amir_job' in t else None;c.commit()"
restore() { say "!! RED after placing ($1) - putting the three files back (the two ask tables stay; the old files never read them)"
  \cp -p "$BAK_A" "$ROOT/$FA"; \cp -p "$BAK_W" "$ROOT/$FW"; \cp -p "$BAK_N" "$ROOT/$FN"
  "$VPY" -c "$WD_PY" "$DB" 2>/dev/null || true; "$SYSTEMCTL" restart "$FSVC" || true
  say "   amir_day.py $(m5 "$ROOT/$FA" | cut -c1-8) (expected ${FROM_A:0:8}) · marg_billwatch.py $(m5 "$ROOT/$FW" | cut -c1-8) (expected ${FROM_W:0:8}) · owner_notice.py $(m5 "$ROOT/$FN" | cut -c1-8) (expected ${FROM_N:0:8}); $FSVC restarted, finance healthz $(wait200). Send a photo of this screen to Claude."
  release_lock; exit 1; }
mkfin() { rm -rf "$SCR/fin_$1"; mkdir -p "$SCR/fin_$1/spine" && \cp -p "$ROOT"/finance/*.py "$SCR/fin_$1/" && \cp -p "$ROOT"/finance/spine/*.py "$ROOT"/finance/spine/*.json "$SCR/fin_$1/spine/" 2>/dev/null; }
walk() { (cd /tmp && TMPDIR="$SCR" PYTHONPATH="$ROOT/shared${PYTHONPATH:+:$PYTHONPATH}" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 600 "$VPY" -W ignore -B "$KDIR/$1" "$2" "$SCR/spine.db" "$SCR/finance.db" 2>&1); }
w803() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s803.py" "$1" "$ROOT/shared" "$ROOT/finance" "$DB" 2>&1); }
full() { case "$1" in "WALK "*) local a=${1#WALK }; [ "${a%/*}" = "${a#*/}" ];; *) return 1;; esac; }

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/7] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/7] KIT_ID.txt names another kit - nothing installed"; exit 1; }
[ -n "$TO_A" ] && [ -n "$TO_W" ] && [ -n "$TO_N" ] && [ -f "$ROOT/$FA" ] && [ -f "$ROOT/$FW" ] && [ -f "$ROOT/$FN" ] && [ -f "$DB" ] && [ -f "$SPDB" ] || { say "!! [1/7] a TO pin, a live file, $DB or $SPDB missing - nothing installed"; exit 1; }
if [ "$(m5 "$ROOT/$FA")" = "$TO_A" ] && [ "$(m5 "$ROOT/$FW")" = "$TO_W" ] && [ "$(m5 "$ROOT/$FN")" = "$TO_N" ]; then say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
mkdir -p "$SCR/built" "$SCR/w803" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/7] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/7] kit gates green; the build lock taken by $KIT"
else say "!! [1/7] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
for p in "A:$FA:$FROM_A" "W:$FW:$FROM_W" "N:$FN:$FROM_N"; do f=$(echo "$p" | cut -d: -f2); fr=$(echo "$p" | cut -d: -f3)
  [ "$(m5 "$ROOT/$f")" = "$fr" ] || stop "!! [2/7] $ROOT/$f is $(m5 "$ROOT/$f" | cut -c1-8), expected ${fr:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."; done
"$APY" -B make_s814a.py "$ROOT/$FA" "$SCR/built/amir_day.py" > "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused (amir_day) - nothing installed"; }
"$APY" -B make_s814b.py "$ROOT/$FW" "$KDIR/seg_bw_ask.py" "$SCR/built/marg_billwatch.py" >> "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused (marg_billwatch) - nothing installed"; }
"$APY" -B make_s814c.py "$ROOT/$FN" "$SCR/built/owner_notice.py" >> "$SCR/make.txt" 2>&1 || { cat "$SCR/make.txt"; stop "!! [2/7] the builder refused (owner_notice) - nothing installed"; }
[ "$(m5 "$SCR/built/amir_day.py")" = "$TO_A" ] && [ "$(m5 "$SCR/built/marg_billwatch.py")" = "$TO_W" ] && [ "$(m5 "$SCR/built/owner_notice.py")" = "$TO_N" ] || stop "!! [2/7] rebuilt, the files are not at their TO pins - nothing installed"
for py in "$APY" "$VPY"; do for f in amir_day.py marg_billwatch.py owner_notice.py; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$py" -W ignore -m py_compile "$SCR/built/$f" || stop "!! [2/7] $f does not compile on $py - nothing installed"; done; done
say "[2/7] live pins exact (${FROM_A:0:8}, ${FROM_W:0:8}, ${FROM_N:0:8}); rebuilt here at their TO pins (${TO_A:0:8}, ${TO_W:0:8}, ${TO_N:0:8}); all compile on both pythons"
"$VPY" -B copy_dbs.py "$DB" "$SCR/finance.db" >/dev/null && "$VPY" -B copy_dbs.py "$SPDB" "$SCR/spine.db" >/dev/null || stop "!! [3/7] could not copy the databases for the walk - nothing installed"
mkfin new && \cp -p "$SCR/built/amir_day.py" "$SCR/built/marg_billwatch.py" "$SCR/built/owner_notice.py" "$SCR/fin_new/" || stop "!! [3/7] could not lay out the walk - nothing installed"
O=$(walk walk_s814.py "$SCR/fin_new"); R=$(printf '%s\n' "$O" | tail -1)
printf '%s\n' "$O" | grep -E "^FAIL|Error" | head -8 | sed 's/^/      /'
full "$R" || stop "!! [3/7] walk_s814: $R - nothing installed"
O2=$(walk walk_s812.py "$SCR/fin_new"); R2=$(printf '%s\n' "$O2" | tail -1); full "$R2" || stop "!! [3/7] the section A walk (S812) on the rebuilt files: $R2 - nothing installed"
mkfin old; R0=$(walk walk_s814.py "$SCR/fin_old" | tail -1); full "$R0" && stop "!! [3/7] the control on the live files did not go red ($R0) - nothing installed"
\cp -p "$SCR/built/marg_billwatch.py" "$SCR/built/owner_notice.py" "$SCR/w803/"; \cp -p "$ROOT/finance/sanjeevni_approvals.py" "$ROOT/finance/finance_ui/finance_approvals.html" "$SCR/w803/"
O3=$(w803 "$SCR/w803"); R3=$(printf '%s\n' "$O3" | tail -1); [ "$R3" = "WALK S803 GREEN" ] || { printf '%s\n' "$O3" | grep -E "RED|Error" | head -6 | sed 's/^/      /'; stop "!! [3/7] the Marg watch's own walk (S803) on the rebuilt page: $R3 - nothing installed"; }
say "[3/7] walk_s814 on copies of the live databases: $R; section A's walk: $R2; the Marg watch's own walk: $R3; the control on the live files: red"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the control green; NOTHING written"; exit 0; fi
f0=$(fhz); [ "$f0" = 200 ] || stop "!! [4/7] finance healthz $f0 before the install - nothing installed"
{ \cp -p "$ROOT/$FA" "$BAK_A" && [ "$(m5 "$BAK_A")" = "$FROM_A" ] && \cp -p "$ROOT/$FW" "$BAK_W" && [ "$(m5 "$BAK_W")" = "$FROM_W" ] && \cp -p "$ROOT/$FN" "$BAK_N" && [ "$(m5 "$BAK_N")" = "$FROM_N" ]; } || stop "!! [4/7] could not write the backups - nothing placed"
for x in amir_day marg_billwatch owner_notice; do st="$ROOT/finance/.$x.py.s814"
  { cat "$SCR/built/$x.py" > "$st" && chmod --reference="$ROOT/finance/$x.py" "$st" 2>/dev/null; chown --reference="$ROOT/finance/$x.py" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(m5 "$SCR/built/$x.py")" ]; } || stop "!! [4/7] could not stage $x.py - nothing placed"; done
mv -f "$ROOT/finance/.owner_notice.py.s814" "$ROOT/$FN" || restore "the rename of owner_notice.py"
mv -f "$ROOT/finance/.marg_billwatch.py.s814" "$ROOT/$FW" || restore "the rename of marg_billwatch.py"
mv -f "$ROOT/finance/.amir_day.py.s814" "$ROOT/$FA" || restore "the rename of amir_day.py"
[ "$(m5 "$ROOT/$FA")" = "$TO_A" ] && [ "$(m5 "$ROOT/$FW")" = "$TO_W" ] && [ "$(m5 "$ROOT/$FN")" = "$TO_N" ] || restore "read back"
"$SYSTEMCTL" restart "$FSVC" || restore "restart $FSVC"
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/7]"
c1=$(wait200); [ "$c1" = 200 ] || restore "finance healthz $c1 after the restart"
say "[4/7] placed and read back: amir_day.py ${TO_A:0:8}, marg_billwatch.py ${TO_W:0:8}, owner_notice.py ${TO_N:0:8}; $FSVC restarted $(TZ=Asia/Kolkata date '+%H:%M IST'), finance healthz $c1"
TB=$(cd "$ROOT/finance" && PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 120 "$VPY" -W ignore -B -c "import sqlite3,sys;sys.path.insert(0,'.');import marg_billwatch as BW;c=sqlite3.connect('$DB',timeout=30);BW.ensure(c);c.commit();print('tables', BW._ask_tables(c), 'notice', BW.setting(c,'ask.notice','off'))" 2>&1 | tail -1)
say "      $TB"
printf '%s\n' "$TB" | grep -q "^tables True notice off" || restore "the ask tables: $TB"
[ "${REHEARSE_RED_AT:-}" = 5 ] && restore "rehearsal: a forced red at [5/7]"
release_lock
say "[5/7] the two ask tables made; the answer notice OFF"
say "[6/7] undo (one line): \\cp -p $BAK_A $ROOT/$FA && \\cp -p $BAK_W $ROOT/$FW && \\cp -p $BAK_N $ROOT/$FN && $VPY -c \"$WD_PY\" $DB && $SYSTEMCTL restart $FSVC"
say "[7/7] nothing goes to anyone until you press Ask on a row; your phone hears nothing until you turn the answer line on, on the page."
say ""
say "$KIT: DONE. Every open row on the Marg watch has an Ask box; a question to Amir lands first on his card, and his one-tap answer comes back to the row."
exit 0
