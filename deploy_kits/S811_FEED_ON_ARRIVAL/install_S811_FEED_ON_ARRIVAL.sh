#!/bin/bash
# =============================================================================
#  install_S811_FEED_ON_ARRIVAL.sh . kit S811 (13-Nov-2026, session S443, the parent)
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s811kit && cp -rp /root/deploy/repo/deploy_kits/S811_FEED_ON_ARRIVAL /tmp/s811kit && bash /tmp/s811kit/install_S811_FEED_ON_ARRIVAL.sh
#  (DRY=1 before bash: every gate; nothing written.)   Undo: bash /tmp/s811kit/install_S811_FEED_ON_ARRIVAL.sh --undo
#
#  THE GAP (12-Nov): the PC's two join workbooks landed at 21:20:58, after the day's last patient sync (cron 20 8-21), so the
#  visits waited until 08:20 and the WhatsApp lists were a day behind. And when reception's Docterz export does not come, the
#  owner is not told.
#  A. NEW /root/finance/patient_sync_on_arrival.sh + ONE cron line (every 5 minutes): a new workbook in the inbox starts the
#     SAME finance_patient_sync.py at once. That file is not changed; its hourly line stays.
#  B. NEW /root/portal/docterz_missing_alert.py + TWO cron lines (21:45 Mon-Sat; 08:15 Mon-Sat about the last working day):
#     one notification to the owner when the consultation report or the follow-up log of a working day has not reached
#     the server.
#  No live file is changed, no service restarted. The crontab is edited only from a good read of it, byte-wise (LC_ALL=C,
#  grep -a: a line holding a byte that is not text is a line like any other), never written if a line that is not this
#  kit's would be lost, and read back; if anything is red after placing, the files come out and the crontab goes back
#  byte for byte.
# =============================================================================
set -u
KIT="S811_FEED_ON_ARRIVAL"
TAG_A="# S811_PATIENT_SYNC_ON_ARRIVAL"
TAG_B="# S811_DOCTERZ_MISSING_ALERT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"
CRONTAB="${CRONTAB:-crontab}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-$ROOT/s811_backup}"
TLOCK="${PSOA_LOCK:-/tmp/patient_sync_on_arrival.lock}"
FDB="${FINANCE_DB:-$ROOT/finance/finance.db}"
N1="$ROOT/finance/patient_sync_on_arrival.sh"; PIN1=9b41c26fdb2945b627513cbe3024db7c
N2="$ROOT/portal/docterz_missing_alert.py"; PIN2=9cc227e12cbe88d1a6784a0da46a9915
WALK_OK="WALK OK 67/67"
SYNC="$ROOT/finance/finance_patient_sync.py"
INBOX="$ROOT/wa/followup-inbox"
LOG_A="$ROOT/finance/patient_sync_on_arrival.log"
LOG_B="$ROOT/portal/docterz_missing_alert.log"
STAMP="$ROOT/finance/.patient_sync_on_arrival.stamp"
# the hourly line exactly as it stands in root's crontab (read from the nightly code bundle of 13-Nov, line 39)
HOURLY="20 8-21 * * * $VPY -B $SYNC >>$ROOT/finance/patient_sync.log 2>&1"
LINE_A="*/5 * * * * /bin/bash $N1 >> $LOG_A 2>&1 $TAG_A"
LINE_B1="45 21 * * 1-6 $VPY -B $N2 --slot evening >> $LOG_B 2>&1 $TAG_B"
LINE_B2="15 8 * * 1-6 $VPY -B $N2 --slot morning >> $LOG_B 2>&1 $TAG_B"
# everything this kit may leave on the box besides its two files (taken out again by --undo and by a red install)
OWN="$STAMP $STAMP.next $ROOT/finance/.patient_sync_on_arrival.fail $LOG_A $LOG_A.cut $LOG_B $ROOT/portal/docterz_missing_alert_state.json $ROOT/portal/docterz_missing_alert_state.json.tmp $ROOT/portal/docterz_missing_alert_state.json.unreadable $ROOT/portal/docterz_missing_alert_state.json.lock"
SCR=""; HAVE_LOCK=0; PLACED1=0; PLACED2=0; CRON_CHANGED=0; ORIG=""; KEEP=""; HAD_TLOCK=0; BACK_OK=0; DEV="?"; NTFY="no"
m5() { md5sum "$1" 2>/dev/null | cut -c1-32; }
on_exit() { [ -n "$SCR" ] && rm -rf "$SCR"; [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   ${2:-Nothing live was changed.} Send a photo of this screen to Claude."; exit 1; }
# a GOOD read of root's crontab into a file: the command answered 0, the file is not empty and ends with a newline
read_cron() { "$CRONTAB" -l > "$1" 2>/dev/null || return 1; [ -s "$1" ] || return 1; [ -z "$(tail -c1 "$1")" ] || return 1; return 0; }
# every look at the crontab is byte-wise: under a UTF-8 locale GNU grep would call a file with one non-text byte "binary"
# and print nothing for it -- and a filter built on that would drop other products' lines.
G() { LC_ALL=C grep -a "$@"; }
OURS_RE="(${TAG_A}|${TAG_B})[[:space:]]*\$"                                    # this kit's tags, only at the END of a line
n_tag() { G -c -E -- "$2[[:space:]]*\$" "$1"; }
n_ours() { G -c -E -- "$OURS_RE" "$1"; }
n_lines() { G -c '' "$1"; }
strip_ours() { G -v -E -- "$OURS_RE" "$1"; }
# $1 = the crontab as read, $2 = the crontab to write, $3 = lines this kit adds: nothing that is not this kit's may be lost
keeps_all() { [ "$(n_lines "$2")" = "$(( $(n_lines "$1") - $(n_ours "$1") + $3 ))" ] && [ "$(strip_ours "$1" | md5sum)" = "$(strip_ours "$2" | md5sum)" ]; }
probe_b() { FINANCE_DB="$FDB" RING_PORTAL_DIR="$ROOT/portal" DMA_NTFY_CONF="$ROOT/finance/freshness.conf" timeout 60 "$VPY" -B "$1" --probe --date "$LWD" 2>&1 | tail -1; }
wait_tick() { ( flock -w 300 9 || true ) 9>>"$TLOCK" 2>/dev/null; }            # let a tick that is running finish
dry_b() { FINANCE_DB="$FDB" FINANCE_OFF_DIR="$ROOT/finance/_off" RING_PORTAL_DIR="$ROOT/portal" DMA_STATE="$ROOT/portal/docterz_missing_alert_state.json" timeout 60 "$VPY" -B "$1" --dry --slot evening --date "$LWD" 2>&1 | tail -1; }
back() {   # after placing: the crontab back byte for byte, the kit's files and whatever its one run left taken out again
  local ok=1
  if [ "$CRON_CHANGED" = 1 ]; then
    "$CRONTAB" - < "$BK/crontab.before_S811" 2>/dev/null
    if read_cron "$SCR/ct.back" && [ "$(m5 "$SCR/ct.back")" = "$ORIG" ]; then echo "   the crontab is back as it was, byte for byte (md5 ${ORIG:0:8})"
    else ok=0; echo "   !! THE CRONTAB DID NOT GO BACK -- its copy from before is kept at $BK/crontab.before_S811"; fi
  fi
  wait_tick
  [ "$PLACED1" = 1 ] && rm -f "$N1" "$N1.s811new"
  [ "$PLACED2" = 1 ] && rm -f "$N2" "$N2.s811new"
  for f in $OWN; do case " $KEEP " in *" $f "*) ;; *) rm -f "$f";; esac; done
  [ "$HAD_TLOCK" = 1 ] || rm -f "$TLOCK"
  { [ -e "$N1" ] && [ "$PLACED1" = 1 ]; } && ok=0
  { [ -e "$N2" ] && [ "$PLACED2" = 1 ]; } && ok=0
  if [ "$ok" = 1 ]; then rm -f "$BK/crontab.before_S811"; rmdir "$BK" 2>/dev/null; echo "   the two new files and what the one run left were taken out again"; fi
  BACK_OK=$ok
  return 0
}
red() {
  echo "!! RED after placing: $1"; back; echo "!! STOPPED: $1"
  if [ "$BACK_OK" = 1 ]; then echo "   Everything this kit placed was taken out again; the box is as it was before. Send a photo of this screen to Claude."
  else echo "   NOT EVERYTHING WENT BACK -- read the !! line above. Send a photo of this screen to Claude."; fi
  exit 1
}

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
[ "$(head -1 KIT_ID.txt | tr -d '\r')" = "$KIT" ] || stop "KIT_ID.txt names another kit"
[ "$(m5 finance/patient_sync_on_arrival.sh)" = "$PIN1" ] || stop "the kit's patient_sync_on_arrival.sh is not the built one"
[ "$(m5 portal/docterz_missing_alert.py)" = "$PIN2" ] || stop "the kit's docterz_missing_alert.py is not the built one"
SCR=$(mktemp -d /tmp/s811.XXXX) || stop "no scratch folder could be made in /tmp"
[ -n "$SCR" ] && [ -d "$SCR" ] || stop "no scratch folder could be made in /tmp"
chmod 700 "$SCR"

if [ "${1:-}" = "--undo" ]; then
  [ "${DRY:-0}" = 1 ] && stop "DRY=1 and --undo were given together -- nothing done. Run --undo without DRY=1 to take the kit out"
  read_cron "$SCR/ct" || stop "root's crontab could not be read (crontab -l) -- nothing undone"
  for pair in "$N1|$PIN1" "$N2|$PIN2"; do
    f="${pair%%|*}"; p="${pair##*|}"
    [ -e "$f" ] && [ "$(m5 "$f")" != "$p" ] && stop "$f has been changed since this kit (a later kit is on top) -- not undone"
  done
  mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
  HAVE_LOCK=1; echo "$KIT undo $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  strip_ours "$SCR/ct" > "$SCR/ct.want"
  if [ "$(m5 "$SCR/ct.want")" != "$(m5 "$SCR/ct")" ]; then
    [ -s "$SCR/ct.want" ] || stop "taking the three lines out would leave an empty crontab -- not undone"
    keeps_all "$SCR/ct" "$SCR/ct.want" 0 || stop "the new crontab would lose a line that is not this kit's -- not written, not undone"
    "$CRONTAB" - < "$SCR/ct.want" || stop "the crontab could not be written -- not undone" "The crontab is as it was."
    read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || stop "the crontab did not read back as written -- send a photo" "Look at the crontab before anything else."
  fi
  wait_tick
  rm -f "$N1" "$N2" "$N1.s811new" "$N2.s811new" $OWN "$TLOCK" "$BK/crontab.before_S811"; rmdir "$BK" 2>/dev/null
  { [ -e "$N1" ] || [ -e "$N2" ]; } && { echo "!! a file is still there -- send a photo"; exit 1; }
  echo "UNDONE: the three S811 cron lines and the two S811 files are out (crontab md5 $(m5 "$SCR/ct.want" | cut -c1-8)). The hourly patient sync runs as before; visits already folded stay."
  exit 0
fi

echo "[1/6] kit files: all match SUMS.md5; the two scripts are the built ones (${PIN1:0:8}, ${PIN2:0:8})"
read_cron "$SCR/ct" || stop "root's crontab could not be read (crontab -l gave nothing usable) -- it is never edited from a bad read"
ORIG=$(m5 "$SCR/ct")
if [ "$(m5 "$N1")" = "$PIN1" ] && [ "$(m5 "$N2")" = "$PIN2" ] && [ "$(n_tag "$SCR/ct" "$TAG_A")" = 1 ] && [ "$(n_tag "$SCR/ct" "$TAG_B")" = 2 ]; then
  echo "-- ALREADY INSTALLED (both files in place, the three cron lines there). Nothing written."; exit 0
fi
for t in flock pgrep timeout stat md5sum; do command -v "$t" >/dev/null 2>&1 || stop "the box has no '$t' -- the on-arrival script needs it"; done
"$VPY" -c "import sqlite3, json" 2>/dev/null || stop "$VPY does not run"
[ -f "$SYNC" ] || stop "$SYNC is not on the box -- there is nothing to start on arrival"
[ "$(G -cFx -- "$HOURLY" "$SCR/ct")" = 1 ] || stop "the hourly patient-sync line is not in the crontab exactly as this kit read it (20 8-21, $VPY -B) -- the kit was built on that line"
[ -d "$INBOX" ] || stop "the inbox folder $INBOX is not on the box"
[ -d "$ROOT/portal" ] || stop "$ROOT/portal is not on the box"
[ -e "$N1" ] && [ "$(m5 "$N1")" != "$PIN1" ] && stop "$N1 is there and is not this kit's"
[ -e "$N2" ] && [ "$(m5 "$N2")" != "$PIN2" ] && stop "$N2 is there and is not this kit's"
bash -n "$KDIR/finance/patient_sync_on_arrival.sh" 2>/dev/null || stop "patient_sync_on_arrival.sh does not pass bash -n on this box"
"$VPY" -B -c "import sys; compile(open(sys.argv[1], encoding='utf-8').read(), sys.argv[1], 'exec')" "$KDIR/portal/docterz_missing_alert.py" 2>/dev/null || stop "docterz_missing_alert.py does not compile with $VPY"
( cd "$SCR" && RING_PORTAL_DIR="$ROOT/portal" "$VPY" -B -c "import sys; sys.path.insert(0, sys.argv[1]); import ring_common as rc; assert callable(rc.push_user)" "$ROOT/portal" 2>/dev/null ) || stop "the portal's own push (ring_common.push_user) could not be loaded with $VPY"
LWD=$(date -d "yesterday" +%F); [ "$(date -d "$LWD" +%u)" = 7 ] && LWD=$(date -d "$LWD -1 day" +%F)
D=$(dry_b "$KDIR/portal/docterz_missing_alert.py")
case "$D" in *"could not be read"*) stop "the alert could not read docterz_export in $FDB ($D)";; "DRY "*) ;; *) stop "the alert's dry read did not answer as expected ($D)";; esac
# the alert's own three reads, run against the live store; the owner's devices; the ntfy topic (read-only, nothing sent)
P=$(probe_b "$KDIR/portal/docterz_missing_alert.py")
case "$P" in "PROBE "*) ;; *) stop "the alert's probe did not answer as expected (${P:0:160})";; esac
case "$P" in *" exports=ok"*) ;; *) stop "the alert's own read of docterz_export in $FDB did not go through ($P)";; esac
case "$P" in *" slips=ok"*) ;; *) stop "the clinic-open sign cannot be read: the alert's own question to the slip table of $FDB did not go through ($P) -- without it a closed day cannot be told from a missed export";; esac
DEV=$(printf '%s\n' "$P" | sed -n 's/.* devices=\([0-9]*\).*/\1/p'); DEV=${DEV:-?}
case "$P" in *" ntfy=yes"*) NTFY=yes;; *) NTFY=no;; esac
case "$DEV" in
  "?") PHONES="the phones registered for your login could not be counted here";;
  0) PHONES="NO phone is registered for your login (0 devices)";;
  1) PHONES="1 phone is registered for your login";;
  *) PHONES="$DEV phones are registered for your login";;
esac
WB="both workbooks are in the inbox"; { [ -f "$INBOX/Visit_Ledger_Join.xlsx" ] && [ -f "$INBOX/Patient_Master_Join.xlsx" ]; } || WB="NOTE: the two join workbooks are not both in the inbox yet"
echo "[2/6] the box: finance_patient_sync.py there; its hourly cron line exactly as read; the inbox folder there ($WB); the portal's push loads; docterz_export and the slips read"
echo "      $PHONES; the ntfy topic for a fallback is set: $NTFY"
echo "      the last working day, read dry: ${D#DRY }"
R=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s811.py" "$KDIR" 2>&1 | tail -1)
[ "$R" = "$WALK_OK" ] || { (cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s811.py" "$KDIR" 2>&1 | grep -E '^BAD|Error' | cut -c1-300 | head -6); stop "the walk is not green on this box ($R)"; }
R2=$(cd "$SCR" && TMPDIR="$SCR" timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s811.py" "$KDIR" --control 2>&1 | tail -1)
case "$R2" in "CONTROL: red"*) ;; *) stop "the control (two broken copies) did not go red ($R2)";; esac
echo "[3/6] the walk on this box (a made-up root): $R | $R2"
[ "${DRY:-0}" = 1 ] || [ "${1:-}" = "--dry" ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }

mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1; echo "$KIT $$ $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
read_cron "$SCR/ct2" && [ "$(m5 "$SCR/ct2")" = "$ORIG" ] || stop "the crontab changed (or could not be read) while this kit was checking -- run the line again"
for f in $OWN; do [ -e "$f" ] && KEEP="$KEEP $f"; done
[ -e "$TLOCK" ] && HAD_TLOCK=1
mkdir -p "$BK" && chmod 700 "$BK" && \cp -f "$SCR/ct" "$BK/crontab.before_S811" && [ "$(m5 "$BK/crontab.before_S811")" = "$ORIG" ] || { rm -f "$BK/crontab.before_S811"; rmdir "$BK" 2>/dev/null; stop "could not keep a copy of the crontab in $BK"; }
chmod 600 "$BK/crontab.before_S811"
[ -e "$N1" ] || PLACED1=1
\cp -f "$KDIR/finance/patient_sync_on_arrival.sh" "$N1.s811new" && mv -f "$N1.s811new" "$N1" && [ "$(m5 "$N1")" = "$PIN1" ] || red "patient_sync_on_arrival.sh did not land byte-exact"
chmod 755 "$N1"
[ -e "$N2" ] || PLACED2=1
\cp -f "$KDIR/portal/docterz_missing_alert.py" "$N2.s811new" && mv -f "$N2.s811new" "$N2" && [ "$(m5 "$N2")" = "$PIN2" ] || red "docterz_missing_alert.py did not land byte-exact"
chmod 644 "$N2"
echo "[4/6] placed $N1 (${PIN1:0:8}) and $N2 (${PIN2:0:8}); the crontab as it was is kept in $BK/crontab.before_S811 (md5 ${ORIG:0:8})"

{ strip_ours "$SCR/ct"; echo "$LINE_A"; echo "$LINE_B1"; echo "$LINE_B2"; } > "$SCR/ct.want"
keeps_all "$SCR/ct" "$SCR/ct.want" 3 || red "the new crontab would lose a line that is not this kit's -- not written"
[ "$(G -cFx -- "$HOURLY" "$SCR/ct.want")" = 1 ] || red "the new crontab would not carry the hourly line -- not written"
CRON_CHANGED=1
"$CRONTAB" - < "$SCR/ct.want" || red "the crontab could not be written"
read_cron "$SCR/ct.now" && [ "$(m5 "$SCR/ct.now")" = "$(m5 "$SCR/ct.want")" ] || red "the crontab did not read back as written"
[ "$(n_tag "$SCR/ct.now" "$TAG_A")" = 1 ] && [ "$(n_tag "$SCR/ct.now" "$TAG_B")" = 2 ] && [ "$(G -cFx -- "$HOURLY" "$SCR/ct.now")" = 1 ] || red "the cron lines are not there exactly once each"
echo "[5/6] three cron lines added, each once, read back; every other line kept, the hourly line untouched ($(n_lines "$SCR/ct") lines before, $(n_lines "$SCR/ct.now") now)"

D=$(dry_b "$N2")
case "$D" in *"could not be read"*) red "the placed alert could not read docterz_export ($D)";; "DRY "*) ;; *) red "the placed alert's dry read did not answer as expected ($D)";; esac
L0=$(G -c '' "$LOG_A" 2>/dev/null); L0=${L0:-0}
PSOA_ROOT="$ROOT" PSOA_PY="$VPY" /bin/bash "$N1" > "$SCR/a.out" 2>&1
RA=$?
[ "$RA" = 0 ] || red "the on-arrival script ended with exit $RA"
[ -s "$SCR/a.out" ] && red "the on-arrival script printed something (cron would mail it): $(head -c 200 "$SCR/a.out")"
NEWL=$(tail -n +$((L0 + 1)) "$LOG_A" 2>/dev/null | tail -1)
case "$NEWL" in
  *"FAILED"*|*"the last sync failed"*) red "the patient sync did not end well when started on arrival: ${NEWL:0:200} (see $ROOT/finance/patient_sync.log)";;
  *"sync ran, exit 0"*) [ -f "$STAMP" ] || red "the sync ran but no stamp was made"; A_SAID="the waiting workbooks were folded now (sync exit 0)";;
  *"skipped: "*) A_SAID="not run this minute -- ${NEWL#*skipped: } -- the next tick does it";;
  "") if [ -e "$ROOT/finance/_off/ALL_OFF" ] || [ -e "$ROOT/finance/_off/PATIENT_SYNC_ON_ARRIVAL_OFF" ]; then A_SAID="the off switch is on: it does nothing until that is lifted"
      elif [ -f "$STAMP" ]; then A_SAID="nothing new was waiting (a tick had already folded the workbooks)"
      elif [ "$WB" != "both workbooks are in the inbox" ]; then A_SAID="nothing to fold yet: the two workbooks are not both in the inbox"
      else red "the on-arrival script said nothing although workbooks are waiting"; fi;;
  *) red "the on-arrival script's log line is not one this kit knows: ${NEWL:0:200}";;
esac
echo "[6/6] live: the alert read dry from its place: ${D#DRY }"
echo "      the on-arrival script, run once for real: $A_SAID"
echo ""
A_DONE="Visits now reach the server's records within about 5 minutes of your PC sending them, at any hour except 01:25-02:15 at night."
B_WHEN="If reception's consultation report or follow-up log has not come by 9:45 pm"
B_MORN="and one more at 8:15 on the next working morning (Monday for Saturday) if it is still missing"
if [ "$DEV" = 0 ] && [ "$NTFY" = yes ]; then
  echo "$KIT: DONE. $A_DONE $B_WHEN a message is made for you, $B_MORN. No phone is registered for your login yet, so the message would come by ntfy only -- open the portal on your phone and allow notifications. Nothing was sent to anyone now."
elif [ "$DEV" = 0 ]; then
  echo "$KIT: DONE. $A_DONE $B_WHEN a message is made for you, $B_MORN. No phone is registered for your login yet, so the message would reach only the log -- open the portal on your phone and allow notifications. Nothing was sent to anyone now."
else
  [ "$DEV" = "?" ] && echo "NOTE: the phones registered for your login could not be counted here; if no message comes when one should, open the portal on your phone and allow notifications."
  echo "$KIT: DONE. $A_DONE $B_WHEN you get one message on your phone, $B_MORN. Nothing was sent to anyone now."
fi
