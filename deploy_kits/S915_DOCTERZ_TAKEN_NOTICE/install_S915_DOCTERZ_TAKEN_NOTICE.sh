#!/bin/bash
# =============================================================================
#  install_S915_DOCTERZ_TAKEN_NOTICE.sh · kit S915 (the parent, S496, 21-Nov-2026)
#  1. NEW /root/portal/docterz_taken_notice.py + cron every 5 min (2,7,12.. past -- just after the pickup's quarter hours):
#     one message to the owner when the server takes a Docterz report -- consultation, follow-up log, clinical data -- naming
#     the day, the rows, the PC it came from (reception PC / your PC (manojz) / the Docterz reports page), the call days of a
#     follow-up log, the period of a clinical report, and how far the clinical data reaches
#  2. /root/portal/docterz_missing_alert.py 5476038d -> TO: its words say "from reception or your PC (manojz)" (wording only)
#  No service restart (both run from cron). The first run notes the newest row and sends nothing.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s915kit && cp -rp /root/deploy/repo/deploy_kits/S915_DOCTERZ_TAKEN_NOTICE /tmp/s915kit && bash /tmp/s915kit/install_S915_DOCTERZ_TAKEN_NOTICE.sh
#  DRY=1 before bash: every gate, the walks and the probe; nothing changed. --undo: the alert's words back, the cron line out.
# =============================================================================
set -u
KIT="S915_DOCTERZ_TAKEN_NOTICE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
PD="${PD:-/root/portal}"; FIN="${FIN:-/root/finance}"; DB="${DB:-/root/finance/finance.db}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
CRONTAB="${CRONTAB:-crontab}"
TAG="# S915_DOCTERZ_TAKEN_NOTICE"
CRONLINE="2-59/5 * * * * [ -e /root/finance/_off/ALL_OFF ] || flock -n /tmp/docterz_taken_notice.lock $VPY -B $PD/docterz_taken_notice.py >> $PD/docterz_taken_notice.log 2>&1 $TAG"
A="docterz_missing_alert.py"; N="docterz_taken_notice.py"
AFROM="5476038db4d0197b75e5570e166acd39"
to_of() { awk -v f="portal/$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
SCR="${TMPW:-/tmp}/s915_inst_$(date +%Y%m%d_%H%M%S)"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
BAK="$PD/$A.bak_S915_${AFROM:0:8}"
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$PD/.$A.s915" "$PD/.$N.s915"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
cron_has() { $CRONTAB -l 2>/dev/null | grep -qF "$TAG"; }
cron_out() { $CRONTAB -l 2>/dev/null | grep -vF "$TAG" | $CRONTAB -; }
restore() { say "!! RED after placing ($1) - putting things back"
  \cp -p "$BAK" "$PD/$A"; cron_has && cron_out; [ -f "$PD/$N" ] && mv -f "$PD/$N" "$PD/$N.undone_S915"
  say "   $A $(m5 "$PD/$A" | cut -c1-8) (expected ${AFROM:0:8}); cron line out; the new script moved aside. Send a photo of this screen to Claude."
  release_lock; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  [ -f "$BAK" ] && [ "$(m5 "$BAK")" = "$AFROM" ] || { say "!! no good backup $BAK - nothing undone"; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo" > "$LOCK/owner"
  [ "$(m5 "$PD/$A")" = "$(to_of $A)" ] && \cp -p "$BAK" "$PD/$A"
  cron_has && cron_out
  [ -f "$PD/$N" ] && mv -f "$PD/$N" "$PD/$N.undone_S915"
  release_lock
  say "   $A $(m5 "$PD/$A" | cut -c1-8) (expected ${AFROM:0:8}); cron line $(cron_has && echo STILL THERE || echo out); $N moved aside"
  say "$KIT: UNDONE."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $A $N; do [ "$(m5 "$KDIR/$n")" = "$(to_of $n)" ] || { say "!! [1/5] the kit's $n is not as built - nothing installed"; exit 1; }; done
[ -f "$DB" ] && [ -f "$PD/$A" ] && [ -f "$FIN/patient_sync_on_arrival.sh" ] || { say "!! [1/5] $DB, $PD/$A or $FIN/patient_sync_on_arrival.sh missing - nothing installed"; exit 1; }
if [ "$(m5 "$PD/$A")" = "$(to_of $A)" ] && [ "$(m5 "$PD/$N")" = "$(to_of $N)" ] && cron_has; then say "-- $KIT is ALREADY INSTALLED - nothing to do."; exit 0; fi
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$PD/$A")" = "$AFROM" ] || stop "!! [2/5] $PD/$A is $(m5 "$PD/$A" | cut -c1-8), expected ${AFROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
[ -e "$PD/$N" ] && [ "$(m5 "$PD/$N")" != "$(to_of $N)" ] && stop "!! [2/5] $PD/$N exists and is not this kit's - nothing installed. Tell Claude."
for n in $A $N; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -W ignore -m py_compile "$KDIR/$n" || stop "!! [2/5] $n does not compile on $VPY - nothing installed"; done
say "[2/5] the live pin exact; both files compile"
py() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" timeout 300 "$VPY" -W ignore -B "$@" 2>&1); }
R1=$(py "$KDIR/walk_s915.py" "$KDIR" "$SCR/w915" | tail -1)
case "$R1" in "WALK 19/19") ;; *) stop "!! [3/5] walk_s915 (made-up) on the new files: $R1 - nothing installed";; esac
R1c=$(py "$KDIR/walk_s915.py" "$KDIR" "$SCR/w915c" --control | tail -1)
case "$R1c" in "WALK 19/19") stop "!! [3/5] walk_s915's control did not go red - nothing installed";; esac
{ mkdir -p "$SCR/k811n/finance" "$SCR/k811n/portal" "$SCR/k811o/finance" "$SCR/k811o/portal" && cp -p "$FIN/patient_sync_on_arrival.sh" "$SCR/k811n/finance/" \
  && cp -p "$FIN/patient_sync_on_arrival.sh" "$SCR/k811o/finance/" && cp -p "$KDIR/$A" "$SCR/k811n/portal/" && cp -p "$PD/$A" "$SCR/k811o/portal/"; } || stop "!! [3/5] could not lay out S811's walk - nothing installed"
R2=$(py "$KDIR/walk_s811.py" "$SCR/k811n" | tail -1)
case "$R2" in "WALK OK 67/67") ;; *) stop "!! [3/5] S811's walk (its words updated) on the new alert: $R2 - nothing installed";; esac
R2c=$(py "$KDIR/walk_s811.py" "$SCR/k811o" | tail -1)
case "$R2c" in "WALK OK"*) stop "!! [3/5] S811's walk with the new words did not go red on the live alert - nothing installed";; esac
PR=$(cd /tmp && FINANCE_DB="$DB" DTN_STATE="$SCR/probe_state.json" "$VPY" -B "$KDIR/$N" --probe 2>&1 | tail -1)
case "$PR" in "PROBE OK"*) ;; *) stop "!! [3/5] the probe on the live store: $PR - nothing installed";; esac
say "[3/5] walk_s915 $R1 (control red: $R1c); S811's walk $R2 (live alert red: $R2c); $PR"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate, the walks and the probe green; nothing live changed"; exit 0; fi
{ \cp -p "$PD/$A" "$BAK" && [ "$(m5 "$BAK")" = "$AFROM" ]; } || stop "!! [4/5] could not write the backup - nothing placed"
for n in $A $N; do { cat "$KDIR/$n" > "$PD/.$n.s915" && chmod --reference="$PD/$A" "$PD/.$n.s915" && chown --reference="$PD/$A" "$PD/.$n.s915" && [ "$(m5 "$PD/.$n.s915")" = "$(to_of $n)" ]; } || stop "!! [4/5] could not stage $n - nothing placed"; done
for n in $A $N; do mv -f "$PD/.$n.s915" "$PD/$n" || restore "the rename of $n"; done
for n in $A $N; do [ "$(m5 "$PD/$n")" = "$(to_of $n)" ] || restore "read back of $n"; done
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
F1=$(cd /tmp && FINANCE_DB="$DB" "$VPY" -B "$PD/$N" 2>&1 | tail -1)
case "$F1" in *"first run"*|"") ;; *) restore "the first run said: $F1";; esac
$CRONTAB -l > "$SCR/cron_before.txt" 2>/dev/null || true
{ grep -vF "$TAG" "$SCR/cron_before.txt"; echo "$CRONLINE"; } | $CRONTAB - || restore "the cron line"
cron_has || restore "the cron line did not read back"
release_lock
say "[4/5] placed and read back: $N $(m5 "$PD/$N" | cut -c1-8) (NEW), $A $(m5 "$PD/$A" | cut -c1-8); the first run: ${F1:-nothing to say}; cron line in (every 5 minutes)"
say "[5/5] undo (one line): bash $KDIR/install_$KIT.sh --undo"
say ""
say "$KIT: DONE."
exit 0
