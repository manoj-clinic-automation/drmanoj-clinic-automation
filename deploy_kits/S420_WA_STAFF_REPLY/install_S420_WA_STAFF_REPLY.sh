#!/bin/bash
# install_S420_WA_STAFF_REPLY.sh -- session 284, 27-Sep-2026 -- D630 item 2, the VPS half:
#   notifier_wa.py  08219ae8 -> b0376d6e  the sender's NUMBER in the ntfy WhatsApp alert (D587); a failed push is
#                                          retried on the next cycles (up to 5), never silently dropped (AF-20).
#   wa_send_api.py  a3ed3708 -> e86d8f16  the outbound row carries 'sent by' when the tracker sends it.
#   WA_Inbox tab: the header 'sent by' added ONCE as the next free column (header-driven writers, receiver unaffected).
# The Apps Script half (Reply for every staff member, 'we -> <name>' in the thread) is placed separately in the
# owner's browser (D577) and recorded in GAS_CURRENT (D583).
set -u
KIT="S420_WA_STAFF_REPLY"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; WD="${WD:-/root/wa}"
NW_FROM=08219ae8fe995a8c85cc93f9a67ab16f; NW_TO=b0376d6ed09cb2e9a437476d63d9ca45; SA_FROM=a3ed37080aaec940226c98bf0d2c7e04; SA_TO=e86d8f16e3168126b3e87fd303620cb7
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/6] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 notifier_wa.py)" = "$NW_TO" ] && [ "$(m5 wa_send_api.py)" = "$SA_TO" ] || { say "!! [1/6] kit files not at their pins"; exit 1; }
say "      green"
if [ "$(m5 "$WD/notifier_wa.py")" = "$NW_TO" ] && [ "$(m5 "$WD/wa_send_api.py")" = "$SA_TO" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
say "[2/6] live pins (from the 27-Sep bundle; repo copies identical)"
[ "$(m5 "$WD/notifier_wa.py")" = "$NW_FROM" ] || { say "!! [2/6] live notifier_wa.py is $(m5 "$WD/notifier_wa.py") - nothing installed"; exit 1; }
[ "$(m5 "$WD/wa_send_api.py")" = "$SA_FROM" ] || { say "!! [2/6] live wa_send_api.py is $(m5 "$WD/wa_send_api.py") - nothing installed"; exit 1; }
say "      exact"
say "[3/6] scratch: py_compile + walk (no network)"
WALK="/tmp/s420_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$WALK/app" && \cp -p notifier_wa.py wa_send_api.py "$WALK/app/" || { say "!! [3/6] scratch copy failed"; exit 1; }
"$VPY" -B -m py_compile "$WALK/app/notifier_wa.py" "$WALK/app/wa_send_api.py" || { say "!! [3/6] py_compile failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s420.py" "$WALK/app" 2>&1 | tail -1 )"; rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT"
say "[4/6] the WA_Inbox header: 'sent by' added once (read-write on ONE header cell, nothing else; nothing printed)"
HOUT="$( cd "$WD" && "$VPY" -B - <<'PY' 2>&1
import os, re, sys
env = {}
for line in open("/root/wa/.env", encoding="utf-8"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
sid, key, tab = env.get("WA_SHEET_ID", ""), env.get("WA_SA_KEY", ""), env.get("WA_TAB", "WA_Inbox") or "WA_Inbox"
if not (sid and key and os.path.exists(key)):
    print("HEADER RED: receiver env incomplete"); sys.exit(1)
import gspread
from google.oauth2.service_account import Credentials
gc = gspread.authorize(Credentials.from_service_account_file(key, scopes=["https://www.googleapis.com/auth/spreadsheets"]))
ws = gc.open_by_key(sid).worksheet(tab)
head = ws.row_values(1)
low = [h.strip().lower() for h in head]
if "sent by" in low:
    print("header: 'sent by' already at column", low.index("sent by") + 1, "of", len(head)); print("HEADER OK"); sys.exit(0)
ws.update_cell(1, len(head) + 1, "sent by")
head2 = ws.row_values(1)
print("header: was", len(head), "columns; 'sent by' added at column", len(head2), "->", [h.strip().lower() for h in head2][-1] == "sent by")
print("HEADER OK" if [h.strip().lower() for h in head2][-1] == "sent by" else "HEADER RED")
PY
)"
echo "$HOUT" | sed 's/^/      /'; echo "$HOUT" | grep -q "^HEADER OK" || { say "!! [4/6] header step red - nothing installed"; exit 1; }
say "[5/6] backup + place + restart wa-notifier, wa-send-api"
B1="$WD/notifier_wa.py.bak_S420_08219ae8"; B2="$WD/wa_send_api.py.bak_S420_a3ed3708"
\cp -p "$WD/notifier_wa.py" "$B1" && \cp -p "$WD/wa_send_api.py" "$B2" || { say "!! [5/6] backup failed"; exit 1; }
restore() { say "!! RED after placing ($1) - restoring"; \cp -p "$B1" "$WD/notifier_wa.py"; \cp -p "$B2" "$WD/wa_send_api.py"; systemctl restart wa-notifier wa-send-api || true; sleep 3; say "   notifier_wa.py $(m5 "$WD/notifier_wa.py") wa_send_api.py $(m5 "$WD/wa_send_api.py")"; exit 1; }
\cp -p notifier_wa.py "$WD/notifier_wa.py" && \cp -p wa_send_api.py "$WD/wa_send_api.py" || restore "copy"
[ "$(m5 "$WD/notifier_wa.py")" = "$NW_TO" ] && [ "$(m5 "$WD/wa_send_api.py")" = "$SA_TO" ] || restore "placed bytes"
T0="$(date '+%Y-%m-%d %H:%M:%S')"
systemctl restart wa-send-api || restore "wa-send-api restart"; systemctl restart wa-notifier || restore "wa-notifier restart"
sleep 12; systemctl is-active --quiet wa-send-api || restore "wa-send-api not active"; systemctl is-active --quiet wa-notifier || restore "wa-notifier not active"
NK="$(curl -s -o /dev/null -m 8 -w '%{http_code}' -X POST "http://127.0.0.1:8096/wa-send" -H 'Content-Type: application/json' -d '{}')"
say "      wa-send without key: $NK (403 expected)"; [ "$NK" = 403 ] || restore "relay gate"
BL="$(journalctl -u wa-notifier --since "$T0" --no-pager 2>/dev/null | grep -c 'baseline rows=')"
say "      notifier baseline line since restart: $BL (1 expected)"; [ "$BL" -ge 1 ] || restore "notifier did not reach its baseline"
JR="$(journalctl -u wa-notifier -u wa-send-api --since "$T0" --no-pager 2>/dev/null | grep -c -i 'Traceback\|ModuleNotFoundError\|ImportError\|MISSING config')"
[ "$JR" = "0" ] || { journalctl -u wa-notifier -u wa-send-api --since "$T0" --no-pager | grep -i -A6 'Traceback\|Error\|MISSING' | head -30; restore "journal: $JR error line(s)"; }
say "      journal since restart: clean"
say "[6/6] all green -- $KIT: DONE"; say "      backups: $B1 · $B2"
md5sum "$WD/notifier_wa.py" "$WD/wa_send_api.py"
