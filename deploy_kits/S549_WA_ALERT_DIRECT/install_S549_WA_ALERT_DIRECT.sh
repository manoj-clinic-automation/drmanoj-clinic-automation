#!/bin/bash
# =============================================================================
#  install_S549_WA_ALERT_DIRECT.sh · kit S549 (session 313, 13-Oct-2026) · URGENT
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S549_WA_ALERT_DIRECT/install_S549_WA_ALERT_DIRECT.sh
#
#  THE OWNER, 13-Oct: "ntfy whatsapp alert have stopped from 7th October, system ones are still coming" (18:23) ·
#  "why not move to server from Google sheets, if it's more reliable?" (18:29) · "It's urgent" (18:47).
#  The alert stopped at 14:37 IST 7-Oct: notifier_wa.py hung on a Google Sheets read while its service stayed "active".
#   /root/wa/wa_receiver.py 9f46279e -> RX_TO (3 counted edits): each inbound WhatsApp is handed to the alert FIRST, before
#      Google is touched; the sheet is written exactly as before.
#   /root/wa/wa_alert.py NEW: a queue with retries (5 s, 30 s, 2 min, 10 min) and one warning to the system topic when it
#      cannot send; patient names refreshed in the background (a slow Google costs a name, never an alert).
#   /root/wa/clinic_watchdog.py 35e40626 and clinic_health_report.py beb33190: wa-notifier no longer listed.
#   wa-notifier.service stopped and disabled (its file stays; the undo line brings it back).
#  Restarts wa-receiver only. Then ONE test alert to the WhatsApp topic: "WhatsApp alerts are working again".
# =============================================================================
set -u
KIT="S549_WA_ALERT_DIRECT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
APY="${APY:-/root/wa/venv/bin/python}"
WA="${WA:-/root/wa}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
RX_PORT="${RX_PORT:-8095}"
NAMES="wa_receiver.py clinic_watchdog.py clinic_health_report.py"
declare -A FROM TO
FROM[wa_receiver.py]=9f46279ebc080262102ab13ad200d6a9;          TO[wa_receiver.py]=793f01820709653587fbee366ea46f17
FROM[clinic_watchdog.py]=35e406261f27b2b0845911ee6382bb3d;      TO[clinic_watchdog.py]=d7844f8e7f13d0bd871a2064517a7711
FROM[clinic_health_report.py]=beb331903e227f7c2661f05aeaf12f8b; TO[clinic_health_report.py]=27cbc9e4cb00b9c62ed85832bcc843ec
AL_TO=e7d0b766090b718a81f9f63f05fb4c6a
STAMP="$(date +%Y%m%d_%H%M%S)"
SCR="/tmp/s549_inst_$STAMP"
HAVE_LOCK=0; PLACED=0; NOTIF_WAS=""

m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
bak() { echo "$WA/$1.bak_S549_${FROM[$1]:0:8}"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; rm -rf "$SCR"; }
restore() {
  trap '' INT TERM HUP
  say "!! RED after placing ($1) - putting everything back"
  for n in $NAMES; do [ -f "$(bak $n)" ] && \cp -p "$(bak $n)" "$WA/$n"; done
  rm -f "$WA/wa_alert.py"
  systemctl restart wa-receiver || true
  if [ "$NOTIF_WAS" = enabled ]; then systemctl enable --now wa-notifier >/dev/null 2>&1 || true; fi
  sleep 3
  for n in $NAMES; do say "   $WA/$n $(m5 "$WA/$n") (expected ${FROM[$n]})"; done
  say "   wa-receiver $(systemctl is-active wa-receiver) · wa-notifier $(systemctl is-active wa-notifier)"
  exit 1
}
on_signal() { trap '' INT TERM HUP; if [ "$PLACED" = 1 ]; then restore "the run was interrupted"; fi; exit 130; }
trap on_exit EXIT
trap on_signal INT TERM HUP

cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
for c in md5sum awk cp mv date systemctl curl timeout grep tail sleep journalctl; do
  command -v "$c" >/dev/null 2>&1 || { say "!! preflight: '$c' missing - nothing installed"; exit 1; }
done
[ -x "$APY" ] || { say "!! preflight: $APY not executable - nothing installed"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/9] SUMS.md5 gate failed - kit corrupt, nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/9] KIT_ID.txt names another kit - nothing installed"; exit 1; }
for n in $NAMES; do [ "$(m5 "$n")" = "${TO[$n]}" ] || { say "!! [1/9] the kit's $n is not its predicted md5 - nothing installed"; exit 1; }; done
[ "$(m5 wa_alert.py)" = "$AL_TO" ] || { say "!! [1/9] the kit's wa_alert.py is not its predicted md5 - nothing installed"; exit 1; }
mkdir "$LOCK" 2>/dev/null && HAVE_LOCK=1
if [ "$HAVE_LOCK" != 1 ]; then
  say "!! [1/9] another build holds the lock $LOCK (owner: $(cat "$LOCK/owner" 2>/dev/null || echo unknown)) - nothing installed. Paste the line again when it is free."
  exit 3
fi
echo "$KIT $(date '+%Y-%m-%d %H:%M:%S')" > "$LOCK/owner"
say "[1/9] kit gates green; the build lock is ours"

ALL_TO=1
for n in $NAMES; do [ -f "$WA/$n" ] || { say "!! [2/9] $WA/$n is not there - nothing installed"; exit 1; }; [ "$(m5 "$WA/$n")" = "${TO[$n]}" ] || ALL_TO=0; done
[ "$(m5 "$WA/wa_alert.py")" = "$AL_TO" ] || ALL_TO=0
if [ "$ALL_TO" = 1 ] && ! systemctl is-enabled --quiet wa-notifier 2>/dev/null; then
  say "-- ALREADY INSTALLED: the four files are the kit's and wa-notifier is retired. Nothing written."; exit 0
fi
for n in $NAMES; do C="$(m5 "$WA/$n")"; [ "$C" = "${FROM[$n]}" ] || { say "!! [2/9] $WA/$n is $C, expected ${FROM[$n]} - nothing installed"; exit 1; }; done
[ -e "$WA/wa_alert.py" ] && { say "!! [2/9] $WA/wa_alert.py already exists and is not the kit's - nothing installed"; exit 1; }
say "[2/9] three live pins exact (wa_receiver 9f46279e, clinic_watchdog 35e40626, clinic_health_report beb33190); no wa_alert.py yet"

mkdir -p "$SCR/old" "$SCR/new" || { say "!! cannot make $SCR - nothing installed"; exit 1; }
export PYTHONPYCACHEPREFIX="$SCR/pyc"; export PYTHONDONTWRITEBYTECODE=1
"$APY" -m py_compile wa_receiver.py wa_alert.py clinic_watchdog.py clinic_health_report.py walk_s549.py make_s549.py \
  || { say "!! [3/9] compile failed - nothing installed"; exit 1; }
say "[3/9] py_compile green (6 files, with the receiver's own python)"

"$APY" -B make_s549.py "$WA/wa_receiver.py" "$SCR/new/wa_receiver.py" "$WA/clinic_watchdog.py" "$SCR/new/clinic_watchdog.py" \
  "$WA/clinic_health_report.py" "$SCR/new/clinic_health_report.py" >/dev/null || { say "!! [4/9] the builder refused a live file - nothing installed"; exit 1; }
for n in $NAMES; do
  [ "$(m5 "$SCR/new/$n")" = "${TO[$n]}" ] || { say "!! [4/9] rebuilt from the live bytes, $n is not the kit's - nothing installed"; exit 1; }
  \cp -p "$WA/$n" "$SCR/old/$n"
done
\cp -p wa_alert.py "$SCR/new/wa_alert.py"
say "[4/9] rebuilt from the live bytes: byte for byte the kit's three files"

WOUT="$( cd /tmp && env -u NTFY_TOPIC -u WATCHDOG_NTFY_URL timeout 180 "$APY" -B "$KDIR/walk_s549.py" "$SCR/new" 2>&1 )"; WRC=$?
ROUT="$( cd /tmp && env -u NTFY_TOPIC -u WATCHDOG_NTFY_URL timeout 180 "$APY" -B "$KDIR/walk_s549.py" "$SCR/old" --expect-red 2>&1 )"; RRC=$?
if [ "$WRC" != 0 ] || ! echo "$WOUT" | grep -q "^WALK OK"; then
  say "!! [5/9] the walk is RED on this box (exit $WRC):"; echo "$WOUT" | tail -8; say "   nothing installed"; exit 1
fi
if [ "$RRC" != 0 ] || ! echo "$ROUT" | grep -q "^WALK OK"; then
  say "!! [5/9] the negative control did not go red on the old files - the walk proves nothing; nothing installed"; exit 1
fi
say "[5/9] $(echo "$WOUT" | grep "^WALK OK" | tail -1 | cut -c1-60) (nothing sent: the walk records, never posts)"
say "      negative control: $(echo "$ROUT" | grep "^WALK OK" | tail -1 | cut -c1-100)"
if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every gate and the walk green; NOTHING written, nothing placed, nothing restarted"; exit 0; fi

for n in $NAMES; do
  \cp -p "$WA/$n" "$(bak $n)" || { say "!! [6/9] backup of $n failed - nothing placed"; exit 1; }
  [ "$(m5 "$(bak $n)")" = "${FROM[$n]}" ] || { say "!! [6/9] the backup of $n is not the live file - nothing placed"; exit 1; }
done
NOTIF_WAS="$(systemctl is-enabled wa-notifier 2>/dev/null || echo unknown)"
for n in $NAMES wa_alert.py; do
  \cp -p "$SCR/new/$n" "$WA/.$n.s549" || { rm -f "$WA"/.*.s549; say "!! [6/9] could not stage $n - nothing placed"; exit 1; }
done
PLACED=1
for n in $NAMES wa_alert.py; do mv -f "$WA/.$n.s549" "$WA/$n" || restore "placing $n"; done
chmod 644 "$WA/wa_alert.py"
for n in $NAMES; do [ "$(m5 "$WA/$n")" = "${TO[$n]}" ] || restore "$n did not land at its pin"; done
[ "$(m5 "$WA/wa_alert.py")" = "$AL_TO" ] || restore "wa_alert.py did not land at its pin"
say "[6/9] backups beside the three files; four files placed (wa_alert.py new)"

T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart wa-receiver || restore "restart wa-receiver"
c1=""; for _try in 1 2 3 4 5 6 7 8 9 10; do sleep 2; c1="$(curl -s -m 5 "http://127.0.0.1:$RX_PORT/")"; [ "$c1" = "wa_receiver alive" ] && break; done
systemctl is-active --quiet wa-receiver || restore "wa-receiver is not active"
[ "$c1" = "wa_receiver alive" ] || restore "wa-receiver does not answer on $RX_PORT"
journalctl -u wa-receiver --since "$T0" --no-pager 2>/dev/null | grep -q "wa_alert NOT loaded" && restore "wa_alert did not load inside the receiver"
say "[7/9] wa-receiver active and answering; the alert module loaded inside it"

systemctl disable --now wa-notifier >/dev/null 2>&1 || true
say "[8/9] wa-notifier stopped and disabled (was: $NOTIF_WAS; now: $(systemctl is-active wa-notifier 2>/dev/null))"
PLACED=0

TEST="$( cd "$WA" && WA_DIR="$WA" timeout 30 "$APY" -B - <<'PYEOF' 2>&1
import os, sys
WA_DIR = os.environ["WA_DIR"]
sys.path.insert(0, WA_DIR)
for line in open(os.path.join(WA_DIR, ".env"), encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
import wa_alert
url = wa_alert._topic_url()
if not url:
    print("TEST NO-TOPIC")
else:
    print("TEST OK" if wa_alert._post(url, "WhatsApp alerts are working again",
          "WhatsApp alerts now come straight from the server, the moment a message arrives. No action needed.") else "TEST FAILED")
PYEOF
)"
case "$TEST" in
  *"TEST OK"*) say "[9/9] one test alert sent to the WhatsApp topic: \"WhatsApp alerts are working again\"";;
  *) say "!! [9/9] the test alert did NOT go ($(echo "$TEST" | tail -1 | cut -c1-80)) - the receiver is installed; tell Claude";;
esac
for n in $NAMES wa_alert.py; do md5sum "$WA/$n"; done
say "$KIT: DONE"
say "undo: \\cp -p $(bak wa_receiver.py) $WA/wa_receiver.py && \\cp -p $(bak clinic_watchdog.py) $WA/clinic_watchdog.py && \\cp -p $(bak clinic_health_report.py) $WA/clinic_health_report.py && rm -f $WA/wa_alert.py && systemctl restart wa-receiver && systemctl enable --now wa-notifier"
