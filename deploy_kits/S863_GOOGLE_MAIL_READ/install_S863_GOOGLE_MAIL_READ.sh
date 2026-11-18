#!/bin/bash
# =============================================================================
#  install_S863_GOOGLE_MAIL_READ.sh · kit S863 (the parent, S480, 18-Nov-2026) · his "go" 07:59
#  Google's monthly figures on his Patients page read by the server by itself, from Google's own monthly mail.
#   1. NEW /root/finance/google_mail_read.py            (read-only Gmail; writes patients_google_mail.json + its state)
#   2. /root/finance/freshness_legs.json FROM 3588a4bb -> TO   (one leg: "Google monthly mail")
#   3. cron: 23 10 * * * ... google_mail_read.py run   # S863_GOOGLE_MAIL_READ
#   4. THE ONE-TIME ALLOW (at the end, when this runs in a terminal): a Google link to open, Allow, paste the address back.
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s863kit && cp -rp /root/deploy/repo/deploy_kits/S863_GOOGLE_MAIL_READ /tmp/s863kit && bash /tmp/s863kit/install_S863_GOOGLE_MAIL_READ.sh
#  DRY=1 before bash: every gate and the walk; nothing live changes.   NO_CONNECT=1: install without the Allow step.
#  --undo: the reader and its cron line out, the leg out; the months file set aside. His Gmail permission file is kept.
# =============================================================================
set -u
KIT="S863_GOOGLE_MAIL_READ"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"
ROOT="${ROOT:-/root}"; FIN="$ROOT/finance"
CRONTAB="${CRONTAB:-crontab}"; MARK="# S863_GOOGLE_MAIL_READ"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
READER="$FIN/google_mail_read.py"; LEGS="$FIN/freshness_legs.json"; MAILJ="$FIN/patients_google_mail.json"
LEGS_FROM=3588a4bbac92e6fd3b3ed6db4022cb93
CRONLINE="23 10 * * * $VPY -B $READER run >> $FIN/google_mail_read.log 2>&1 $MARK"
to_of() { awk -v f="$1" '$2==f{print $1}' "$KDIR/TO_PINS.md5"; }
STAMP="$(date +%Y%m%d_%H%M%S)"; SCR="${TMPW:-/tmp}/s863_inst_$STAMP"; TOOK_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
LBAK="$LEGS.bak_S863_${LEGS_FROM:0:8}"
release_lock() { [ "$TOOK_LOCK" = 1 ] || return 0; rm -f "${LOCK:?}/owner"; rmdir "$LOCK" 2>/dev/null; TOOK_LOCK=0; }
on_exit() { rm -f "$FIN/.google_mail_read.py.s863" "$FIN/.freshness_legs.json.s863"; release_lock; rm -rf "${SCR:?}"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { say "$1"; release_lock; exit 1; }
MIN_CRON="${MIN_CRON:-20}"     # the live crontab holds ~100 lines: a read shorter than this is a failed read, never written back
cron_has() { "$CRONTAB" -l 2>/dev/null | grep -qF "$MARK"; }
cron_read() { "$CRONTAB" -l > "$SCR/cron.cur" 2>/dev/null && [ "$(grep -c . "$SCR/cron.cur")" -ge "$MIN_CRON" ]; }
cron_drop() { cron_read || { say "!! the crontab could not be read whole - left as it is"; return 1; }
  grep -vF "$MARK" "$SCR/cron.cur" > "$SCR/cron.new"; [ "$(grep -c . "$SCR/cron.new")" -ge "$MIN_CRON" ] && "$CRONTAB" "$SCR/cron.new"; }
restore() { say "!! RED after placing ($1) - putting everything back"
  mkdir -p "$SCR"
  for _t in 1 2 3; do if cron_read; then grep -qF "$MARK" "$SCR/cron.cur" && cron_drop; break; fi; sleep "${NAP:-2}"; done
  if cron_read; then grep -qF "$MARK" "$SCR/cron.cur" && CR="the cron line is STILL THERE" || CR="no cron line"; else CR="the crontab could not be read, so the cron line may still be there"; fi
  [ -f "$LBAK" ] && \cp -p "$LBAK" "$LEGS"
  [ -f "$READER" ] && mv -f "$READER" "$READER.undone_S863"
  say "   freshness_legs.json $(m5 "$LEGS" | cut -c1-8) (expected ${LEGS_FROM:0:8}); the reader set aside (its cron line, if left, finds no reader and does nothing); $CR. Send a photo of this screen to Claude."
  release_lock; exit 1; }

if [ "${1:-}" = "--undo" ]; then
  mkdir -p "$SCR"
  [ ! -e "$READER" ] && ! cron_has && [ "$(m5 "$LEGS")" = "$LEGS_FROM" ] && { say "-- $KIT is not installed - nothing to undo."; exit 0; }
  [ "$(m5 "$LEGS")" = "$(to_of finance/freshness_legs.json)" ] || [ "$(m5 "$LEGS")" = "$LEGS_FROM" ] || { say "!! $LEGS is $(m5 "$LEGS" | cut -c1-8), not this kit's - a later change is on it: nothing undone. Tell Claude."; exit 1; }
  [ "$(m5 "$LEGS")" = "$LEGS_FROM" ] || { [ -f "$LBAK" ] && [ "$(m5 "$LBAK")" = "$LEGS_FROM" ]; } || { say "!! no good backup $LBAK - nothing undone"; exit 1; }
  mkdir "$LOCK" 2>/dev/null || { say "!! another build holds the lock $LOCK - nothing undone. Run it again in five minutes."; exit 3; }
  TOOK_LOCK=1; echo "$KIT undo $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
  cron_has && { cron_drop || { say "!! the cron line could not be removed (the crontab did not read whole) - nothing undone. Run it again in a minute."; release_lock; exit 1; }; }
  [ "$(m5 "$LEGS")" = "$LEGS_FROM" ] || \cp -p "$LBAK" "$LEGS"
  [ -f "$READER" ] && mv -f "$READER" "$READER.undone_S863"
  [ -f "$MAILJ" ] && mv -f "$MAILJ" "$MAILJ.undone_S863"
  release_lock
  say "$KIT: UNDONE (no cron line, the leg out: freshness_legs.json $(m5 "$LEGS" | cut -c1-8); the reader and the months file set aside as *.undone_S863; your Gmail permission file kept)."; exit 0; fi

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $1}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for f in google_mail_read.py freshness_legs.json; do [ "$(m5 "$KDIR/$f")" = "$(to_of "finance/$f")" ] || { say "!! [1/5] the kit's $f is not as built - nothing installed"; exit 1; }; done
mkdir -p "$SCR" && chmod 700 "$SCR" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
if [ "$(m5 "$READER")" = "$(to_of finance/google_mail_read.py)" ] && [ "$(m5 "$LEGS")" = "$(to_of finance/freshness_legs.json)" ] && cron_has; then
  say "-- $KIT is ALREADY INSTALLED."
  if [ "${NO_CONNECT:-0}" != 1 ] && [ -t 0 ] && { [ ! -f "$ROOT/wa/recordings-archive/gmail_token.json" ] || [ -n "${RECONNECT:-}" ]; }; then
    "$VPY" -B "$READER" connect; exit 0; fi                            # review 10: no exec -- the exit trap still cleans up
  "$VPY" -B "$READER" status; exit 0; fi
if [ "${DRY:-0}" = 1 ]; then say "[1/5] DRY RUN: kit gates green; no lock"
elif mkdir "$LOCK" 2>/dev/null; then TOOK_LOCK=1; echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"; say "[1/5] kit gates green; the build lock taken by $KIT"
else say "!! [1/5] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Run it again in five minutes."; exit 3; fi
[ "$(m5 "$LEGS")" = "$LEGS_FROM" ] || stop "!! [2/5] $LEGS is $(m5 "$LEGS" | cut -c1-8), expected ${LEGS_FROM:0:8} - it changed after this kit was built: STOP, nothing installed. Tell Claude."
[ -e "$READER" ] && stop "!! [2/5] $READER already exists and is not this kit's - STOP, nothing installed. Tell Claude."
cron_has && stop "!! [2/5] the crontab already holds a $MARK line - STOP, nothing installed. Tell Claude."
for p in "$APY" "$VPY"; do PYTHONPYCACHEPREFIX="$SCR/pyc" "$p" -W ignore -m py_compile "$KDIR/google_mail_read.py" || stop "!! [2/5] google_mail_read.py does not compile on $p - nothing installed"; done
"$APY" -c "import json,sys;d=json.load(open(sys.argv[1]));assert len(d['legs'])==40 and d['legs'][-1]['name']=='Google monthly mail'" "$KDIR/freshness_legs.json" || stop "!! [2/5] the new legs file does not read - nothing installed"
(cd /tmp && PYTHONPYCACHEPREFIX="$SCR/pyc" "$VPY" -B -c "import sys;sys.path.insert(0,sys.argv[1]);import google_mail_read as g;g.client()" "$KDIR") >/dev/null 2>&1 || stop "!! [2/5] the server's Google client (client_id / client_secret in the drive_token.json the recordings already use) could not be read - nothing installed. Tell Claude."
say "[2/5] the live legs file at its FROM pin; no reader and no cron line yet; the reader compiles on both pythons; the new legs file reads (40 legs); the server's Google client is there"
R1=$(cd /tmp && TMPDIR="$SCR" PYTHONPYCACHEPREFIX="$SCR/pyc" TZ=Asia/Kolkata timeout 300 "$VPY" -W ignore -B "$KDIR/walk_s863.py" "$KDIR" "$SCR/w863" 2>&1 | tail -1)
case "$R1" in "WALK 27/27") ;; *) stop "!! [3/5] walk_s863 (a made-up Google) : $R1 - nothing installed";; esac
mkdir -p "$SCR/empty"; R1c=$(cd /tmp && TMPDIR="$SCR" TZ=Asia/Kolkata timeout 120 "$VPY" -W ignore -B "$KDIR/walk_s863.py" "$SCR/empty" "$SCR/w863c" 2>&1 | tail -1)
case "$R1c" in "WALK 27/27") stop "!! [3/5] walk_s863's control (no reader) did not go red - nothing installed";; esac
say "[3/5] walk_s863 $R1 (a made-up Google: token, Gmail, mails); control red (${R1c:0:40})"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; nothing live changed"; exit 0; fi
{ \cp -p "$LEGS" "$LBAK" && [ "$(m5 "$LBAK")" = "$LEGS_FROM" ]; } || stop "!! [4/5] could not write the backup of freshness_legs.json - nothing placed"
REF="$FIN/patients_page.py"; [ -f "$REF" ] || REF="$LEGS"
for f in google_mail_read.py freshness_legs.json; do st="$FIN/.$f.s863"
  { cat "$KDIR/$f" > "$st" && chmod --reference="$REF" "$st" 2>/dev/null; chown --reference="$REF" "$st" 2>/dev/null; [ "$(m5 "$st")" = "$(to_of "finance/$f")" ]; } || stop "!! [4/5] could not stage $f - nothing placed"; done
mv -f "$FIN/.google_mail_read.py.s863" "$READER" || restore "the rename of the reader"
mv -f "$FIN/.freshness_legs.json.s863" "$LEGS" || restore "the rename of the legs file"
cron_read || restore "the crontab could not be read whole (nothing written to it)"
{ cat "$SCR/cron.cur"; echo "$CRONLINE"; } > "$SCR/cron.new" && "$CRONTAB" "$SCR/cron.new" || restore "the cron line"
[ "$("$CRONTAB" -l 2>/dev/null | grep -c .)" -ge "$(( $(grep -c . "$SCR/cron.cur") + 1 ))" ] || restore "the crontab read back shorter than before"
[ "$("$CRONTAB" -l 2>/dev/null | grep -cF "$MARK")" = 1 ] || restore "the cron line read back"
for f in google_mail_read.py freshness_legs.json; do [ "$(m5 "$FIN/$f")" = "$(to_of "finance/$f")" ] || restore "read back of $f"; done
[ "${REHEARSE_RED_AT:-}" = 4 ] && restore "rehearsal: a forced red at [4/5]"
"$VPY" -B "$READER" run >/dev/null 2>&1; rc=$?
case "$rc" in 0|2|3|4) ;; *) restore "the reader's first run ended $rc";; esac
release_lock
say "[4/5] placed and read back: the reader, the legs file (40 legs), one cron line (10:23 daily); first run: $("$VPY" -B "$READER" status | head -1 | cut -c1-160)"
say "      undo (one line): bash $KDIR/install_$KIT.sh --undo"
if [ "${NO_CONNECT:-0}" = 1 ] || [ ! -t 0 ]; then
  say "[5/5] the one-time Allow is still owed. Run this line on the server when you have two minutes:"
  say "      $VPY -B $READER connect"
  say ""; say "$KIT: INSTALLED (the Allow owed)."; exit 0; fi
say "[5/5] THE ONE-TIME ALLOW -- read the three steps below."
"$VPY" -B "$READER" connect; rc=$?
say ""
if [ "$rc" = 0 ]; then
  if grep -q "def google_mail" "$FIN/patients_part2.py" 2>/dev/null; then say "$KIT: DONE. Your page: https://followup.dr-manoj.in/finance/console/patients"
  else say "$KIT: DONE (the page shows the mail's months once S862 is installed)."; fi
  exit 0; fi
[ "$rc" = 4 ] && { say "$KIT: CONNECTED -- Google's mail needs a look (the reason is on the line above). Tell Claude."; exit 0; }
say "$KIT: INSTALLED, the Allow not finished (exit $rc). Send a photo of this screen to Claude."; exit 0
