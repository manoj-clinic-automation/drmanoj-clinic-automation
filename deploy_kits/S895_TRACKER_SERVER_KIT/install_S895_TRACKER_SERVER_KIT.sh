#!/bin/bash
# install_S895_TRACKER_SERVER_KIT.sh -- S895 (the parent, S492, 20-Nov-2026): the Follow-up Tracker's engine on the server, OFF.
#
# WHAT ONE RUN DOES (gates first; nothing live changes until [4/6]):
#   [1/6] the kit's own SUMS.md5 gate
#   [2/6] the live files are the bytes this kit was built on (FROM pins); the box has what the tracker needs
#         (the venv, FU_UPLOAD_SECRET in /root/wa/.env, /root/finance/patient_fp.env, a Sheet key in /root/wa)
#   [3/6] the venv can run the engine (pandas/openpyxl/gspread; pandas installed into the venv ONLY if missing);
#         every kit file compiles; server_runner's own selftest on a made-up root says 0 failures
#   [4/6] /root/followup_tracker/ is made from the kit's tracker/ files, with its OFF file PRESENT; the three live
#         files are replaced (each kept as .bak_S895_<from>): docterz_ingest.py (the box's outputs first),
#         push_followups_vps.py (the Do_Not_Call filter back), followup_receiver.py (the origin mark)
#   [5/6] the receiver is restarted and answers /fu-ping; docterz_ingest runs once --dry-run in the venv
#   [6/6] two cron lines, both gated by the OFF file: the runner every 5 minutes, the 08:00 Patient_Master mirror
#   RED anywhere after [4/6]: everything this run placed goes back, the receiver restarted, nothing else touched.
#   The runner stays OFF until the switch evening (rm /root/followup_tracker/OFF). The seed comes with S895's session 2.
#
#   --undo : the three files back from their .bak, the cron lines out, the receiver restarted. /root/followup_tracker/
#            is removed only if it holds no data/*.csv (a seeded folder is never deleted by an undo).
set -u
KIT="S895_TRACKER_SERVER_KIT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
FIN="${FIN:-/root/finance}"; WA="${WA:-/root/wa}"; FUT="${FUT:-/root/followup_tracker}"
VENV="${VENV:-/root/wa/venv}"; APY="$VENV/bin/python3"
RSVC="${RSVC:-clinic-followup-receiver}"; SYSTEMCTL="${SYSTEMCTL:-systemctl}"; CRONTAB="${CRONTAB:-crontab}"
MARK="# S895_TRACKER"; MIN_CRON=20
LOCK="/tmp/s895_install.lock"; TOOK_LOCK=0; PLACED_FUT=0; PLACED_FILES=""
SCR="$(mktemp -d /tmp/s895_scr.XXXXXX)"

INGEST_FROM="d2102bb766a64d02c60473b556e4fdd2"
PUSH_FROM="b0fe0c377c26ff5d4d8ff15378887d63"
RECV_FROM="384e9ed8209a6645ff3776635197315d"

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
say() { echo "$@"; }
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -rf "$LOCK"; TOOK_LOCK=0; }
on_exit() { release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; exit 1; }
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
cron_drop() { cron_read || { say "!! the crontab could not be read whole - left as it is"; return 1; }
  grep -vF "$MARK" "$SCR/cron.cur" > "$SCR/cron.new"; "$CRONTAB" "$SCR/cron.new"; }
pya() { (cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$APY" -W ignore -B "$@" 2>&1); }
ping_ok() { if [ -n "${PING_CMD:-}" ]; then $PING_CMD | grep -q '^ok'; else curl -s -m 8 "http://127.0.0.1:8100/fu-ping" 2>/dev/null | grep -q '^ok'; fi; }
ingest_dry() { if [ -n "${INGEST_DRY_CMD:-}" ]; then $INGEST_DRY_CMD 2>&1 | tail -1; else pya "$FIN/docterz_ingest.py" --dry-run 2>&1 | tail -1; fi; }

restore() {
  say "!! RED after placing ($1) - putting everything back"
  [ -f "$FIN/docterz_ingest.py.bak_S895_${INGEST_FROM:0:8}" ] && cp -fp "$FIN/docterz_ingest.py.bak_S895_${INGEST_FROM:0:8}" "$FIN/docterz_ingest.py"
  [ -f "$WA/push_followups_vps.py.bak_S895_${PUSH_FROM:0:8}" ] && cp -fp "$WA/push_followups_vps.py.bak_S895_${PUSH_FROM:0:8}" "$WA/push_followups_vps.py"
  [ -f "$WA/followup_receiver.py.bak_S895_${RECV_FROM:0:8}" ] && cp -fp "$WA/followup_receiver.py.bak_S895_${RECV_FROM:0:8}" "$WA/followup_receiver.py"
  [ "$PLACED_FUT" = 1 ] && rm -rf "${FUT:?}"
  cron_has && cron_drop >/dev/null 2>&1
  "$SYSTEMCTL" restart "$RSVC" 2>/dev/null; sleep 2
  if [ "$(m5 "$FIN/docterz_ingest.py")" = "$INGEST_FROM" ] && [ "$(m5 "$WA/push_followups_vps.py")" = "$PUSH_FROM" ] && [ "$(m5 "$WA/followup_receiver.py")" = "$RECV_FROM" ]; then
    say "   restored: the three files at their FROM pins; receiver $(ping_ok && echo answers || echo 'NOT answering - tell Claude')"
  else
    say "   !! restore incomplete - send a photo of this screen to Claude"
  fi
  exit 1
}

# ── undo ──────────────────────────────────────────────────────────────────────────────────────────
if [ "${1:-}" = "--undo" ]; then
  if [ "$(m5 "$FIN/docterz_ingest.py")" = "$INGEST_FROM" ] && ! cron_has && [ ! -d "$FUT" ]; then say "-- $KIT is not installed; nothing to undo"; exit 0; fi
  for spec in "$FIN/docterz_ingest.py|finance/docterz_ingest.py|$INGEST_FROM" "$WA/push_followups_vps.py|wa/push_followups_vps.py|$PUSH_FROM" "$WA/followup_receiver.py|wa/followup_receiver.py|$RECV_FROM"; do
    p="${spec%%|*}"; rest="${spec#*|}"; rel="${rest%%|*}"; from="${rest#*|}"
    [ "$(m5 "$p")" = "$from" ] || [ "$(m5 "$p")" = "$(to_of "$rel")" ] || stop "!! $p is $(m5 "$p" | cut -c1-8), neither this kit's nor its FROM - a later kit owns it; nothing undone. Tell Claude."
    [ "$(m5 "$p")" = "$from" ] || { [ -f "$p.bak_S895_${from:0:8}" ] && [ "$(m5 "$p.bak_S895_${from:0:8}")" = "$from" ]; } || stop "!! no good backup for $p - nothing undone"
  done
  mkdir "$LOCK" 2>/dev/null || stop "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."
  TOOK_LOCK=1
  cron_has && { cron_drop || stop "!! the cron lines could not be removed - nothing undone. Run it again in a minute."; }
  for spec in "$FIN/docterz_ingest.py|$INGEST_FROM" "$WA/push_followups_vps.py|$PUSH_FROM" "$WA/followup_receiver.py|$RECV_FROM"; do
    p="${spec%%|*}"; from="${spec#*|}"
    [ "$(m5 "$p")" = "$from" ] || cp -fp "$p.bak_S895_${from:0:8}" "$p"
  done
  if [ -d "$FUT" ]; then
    if ls "$FUT"/data/*.csv >/dev/null 2>&1; then say "   $FUT holds data - kept (an undo never deletes the seeded ledgers); its OFF file set"; touch "$FUT/OFF"; else rm -rf "${FUT:?}"; fi
  fi
  "$SYSTEMCTL" restart "$RSVC"; sleep 2
  ping_ok || { say "!! UNDONE but the receiver does not answer /fu-ping - send a photo of this screen to Claude."; exit 1; }
  say "$KIT: UNDONE (the three files back at their FROM pins, no cron lines, receiver answers)."
  exit 0
fi

# ── [1/6] the kit ─────────────────────────────────────────────────────────────────────────────────
cd "$KDIR" || stop "!! cannot enter $KDIR"
md5sum -c SUMS.md5 >/dev/null 2>&1 || stop "!! [1/6] SUMS.md5 gate failed - kit corrupt, nothing installed"
for f in server_runner.py docterz_ingest.py push_followups_vps.py followup_receiver.py; do [ -f "$KDIR/$f" ] || stop "!! [1/6] $f missing from the kit"; done
for f in processor.py revenue.py revenue_ingest.py concessions.py diagnosis_normalizer.py docterz_pickup.py push_to_vps.py push_patient_join.py push_patient_mirror.py seed_diagnosis.py; do
  [ -f "$KDIR/tracker/$f" ] || stop "!! [1/6] tracker/$f missing from the kit"; done
say "   [1/6] kit sums ok"

# ── [2/6] the box ─────────────────────────────────────────────────────────────────────────────────
[ -x "$APY" ] || stop "!! [2/6] $APY is not there - nothing installed"
[ "$(m5 "$FIN/docterz_ingest.py")" = "$INGEST_FROM" ] || stop "!! [2/6] $FIN/docterz_ingest.py is $(m5 "$FIN/docterz_ingest.py" | cut -c1-8), not ${INGEST_FROM:0:8} (the 20-Nov bundle) - STOP, nothing installed. Tell Claude."
[ "$(m5 "$WA/push_followups_vps.py")" = "$PUSH_FROM" ] || stop "!! [2/6] $WA/push_followups_vps.py is $(m5 "$WA/push_followups_vps.py" | cut -c1-8), not ${PUSH_FROM:0:8} - STOP, nothing installed. Tell Claude."
[ "$(m5 "$WA/followup_receiver.py")" = "$RECV_FROM" ] || stop "!! [2/6] $WA/followup_receiver.py is $(m5 "$WA/followup_receiver.py" | cut -c1-8), not ${RECV_FROM:0:8} - STOP, nothing installed. Tell Claude."
grep -q '^FU_UPLOAD_SECRET=' "$WA/.env" 2>/dev/null || stop "!! [2/6] $WA/.env has no FU_UPLOAD_SECRET line - STOP, nothing installed. Tell Claude."
[ -f "$FIN/patient_fp.env" ] || stop "!! [2/6] $FIN/patient_fp.env (the fingerprint salt) is not there - STOP, nothing installed. Tell Claude."
KEYJ="$(ls "$WA"/*.json 2>/dev/null | head -1)"; [ -n "$KEYJ" ] || stop "!! [2/6] no Sheet key (.json) in $WA - STOP, nothing installed. Tell Claude."
cron_has && stop "!! [2/6] the crontab already holds a $MARK line - STOP, nothing installed. Tell Claude."
[ -d "$FUT" ] && ls "$FUT"/*.py >/dev/null 2>&1 && stop "!! [2/6] $FUT already exists - STOP, nothing installed. Tell Claude."
mkdir "$LOCK" 2>/dev/null || stop "!! [2/6] another build holds the lock $LOCK - run it again in five minutes."
TOOK_LOCK=1
say "   [2/6] live files at their FROM pins; secret, salt and Sheet key present"

# ── [3/6] the engine runs here ────────────────────────────────────────────────────────────────────
if ! pya -c "import pandas" >/dev/null 2>&1; then
  say "   [3/6] pandas is not in the venv - installing it there (one time)"
  "$VENV/bin/pip" install -q pandas >/dev/null 2>&1 || stop "!! [3/6] pandas could not be installed into $VENV - nothing installed"
fi
pya -c "import pandas, numpy, openpyxl, gspread, requests, flask" >/dev/null 2>&1 || stop "!! [3/6] the venv lacks one of pandas/numpy/openpyxl/gspread/requests/flask - nothing installed"
for f in "$KDIR"/*.py "$KDIR"/tracker/*.py; do pya -m py_compile "$f" >/dev/null 2>&1 || stop "!! [3/6] $(basename "$f") does not compile in the venv - nothing installed"; done
st="$(FUT_ROOT="$KDIR" pya "$KDIR/server_runner.py" --selftest 2>&1 | tail -1)"
[ "$st" = "selftest: 0 failure(s)" ] || stop "!! [3/6] server_runner selftest: '$st' - nothing installed"
say "   [3/6] venv runs the engine; kit compiles; selftest 0 failures"

# ── [4/6] place ───────────────────────────────────────────────────────────────────────────────────
mkdir -p "$FUT" && chmod 700 "$FUT" && PLACED_FUT=1
for d in intake archive uploads outputs logs data; do mkdir -p "$FUT/$d" && chmod 700 "$FUT/$d"; done
for f in "$KDIR"/tracker/*.py; do cp -fp "$f" "$FUT/"; done
cp -fp "$KDIR/server_runner.py" "$FUT/server_runner.py"
touch "$FUT/OFF"
grep '^FU_UPLOAD_SECRET=' "$WA/.env" | head -1 > "$FUT/fu_upload.env" && chmod 600 "$FUT/fu_upload.env"
ln -sf "$FIN/patient_fp.env" "$FUT/patient_fp.env"
ln -sf "$KEYJ" "$FUT/$(basename "$KEYJ")"
for spec in "$FIN/docterz_ingest.py|finance/docterz_ingest.py|$INGEST_FROM|docterz_ingest.py" "$WA/push_followups_vps.py|wa/push_followups_vps.py|$PUSH_FROM|push_followups_vps.py" "$WA/followup_receiver.py|wa/followup_receiver.py|$RECV_FROM|followup_receiver.py"; do
  p="${spec%%|*}"; r="${spec#*|}"; rel="${r%%|*}"; r2="${r#*|}"; from="${r2%%|*}"; kf="${r2#*|}"
  cp -fp "$p" "$p.bak_S895_${from:0:8}"
  cp -fp "$KDIR/$kf" "$p"; PLACED_FILES="$PLACED_FILES $p"
  [ "$(m5 "$p")" = "$(to_of "$rel")" ] || restore "$p read back $(m5 "$p" | cut -c1-8), not its TO pin"
  pya -m py_compile "$p" >/dev/null 2>&1 || restore "$p does not compile"
done
say "   [4/6] $FUT placed (OFF present); the three files replaced, read back at their TO pins"

# ── [5/6] the services answer ─────────────────────────────────────────────────────────────────────
"$SYSTEMCTL" restart "$RSVC" || restore "the receiver would not restart"
sleep 3
ping_ok || restore "the receiver does not answer /fu-ping after the restart"
dry="$(ingest_dry)"
echo "$dry" | grep -q '^read ' || restore "docterz_ingest --dry-run did not finish: $dry"
FUT_OFF="$FUT/OFF" pya "$FUT/server_runner.py" 2>&1 | grep -q 'OFF' || restore "the runner did not honour its OFF file"
say "   [5/6] receiver answers; docterz_ingest dry run: $dry"
say "         runner honours OFF"

# ── [6/6] cron ────────────────────────────────────────────────────────────────────────────────────
cron_read || restore "the crontab could not be read whole (nothing written to it)"
{ cat "$SCR/cron.cur"
  echo "*/5 * * * * [ -e $FIN/_off/ALL_OFF ] || [ -e $FUT/OFF ] || TZ=Asia/Kolkata flock -n /tmp/followup_tracker.lock $APY -B $FUT/server_runner.py >> $FUT/logs/runner.log 2>&1 $MARK runner"
  echo "0 8 * * * [ -e $FIN/_off/ALL_OFF ] || [ -e $FUT/OFF ] || (cd $FUT && TZ=Asia/Kolkata $APY -B $FUT/push_patient_mirror.py --push >> $FUT/logs/mirror.log 2>&1) $MARK mirror"
} > "$SCR/cron.new"
"$CRONTAB" "$SCR/cron.new" || restore "the crontab would not take the two lines"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" -ge "$(( $(grep -c . "$SCR/cron.cur") + 2 ))" ] || restore "the crontab read back shorter than before"
say "   [6/6] two cron lines placed ($MARK), both gated by $FUT/OFF"
say ""
say "$KIT: DONE (OFF). Installed, nothing running yet:"
say "      $FIN/docterz_ingest.py $(m5 "$FIN/docterz_ingest.py" | cut -c1-8) (the box's outputs first) . $WA/push_followups_vps.py $(m5 "$WA/push_followups_vps.py" | cut -c1-8) (Do_Not_Call back) . $WA/followup_receiver.py $(m5 "$WA/followup_receiver.py" | cut -c1-8) (origin mark)"
say "      $FUT/ with OFF present; the seed and the switch are later sessions' work."
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
exit 0
