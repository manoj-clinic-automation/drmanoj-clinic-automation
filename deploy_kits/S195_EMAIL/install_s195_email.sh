#!/bin/bash
# =====================================================================
#  S195_EMAIL · ⭐5 hardening — the ping-pong Gmail query agent
#
#  Updates email_agent.py in place (systemd units unchanged). The two
#  fixes the owner asked for after S194:
#    (a) "answered" is tracked with a Gmail LABEL (clinic-agent-done),
#        not the read/unread flag — a Q: you OPEN before the 3-min poll
#        is still answered (the old UNSEEN filter skipped read mail).
#    (b) ALWAYS reply, even when the command errors or the query raises.
#
#  Still safe by construction: only the dr_query allowlist runs, and
#  dr_query opens the DB mode=ro (physically cannot write).
#
#  Your existing /root/deploy/email_agent.json is KEPT untouched. The new
#  done_label defaults automatically, so no config edit is required; add
#  "done_label" to the JSON only if you want a different label name.
# =====================================================================
set -u; cd "$(dirname "$0")"
DEPLOY=/root/deploy
echo "==============================================================="
echo " S195_EMAIL · Gmail query agent (label-tracked, always-reply)"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] dr_query present + read-only?"
[ -f "$DEPLOY/dr_query.py" ] || { echo "*** RED: $DEPLOY/dr_query.py missing (install S193_TOOLS first)."; exit 1; }
python3 "$DEPLOY/dr_query.py" selftest 2>&1 | tail -1 | grep -q "SELFTEST OK" || { echo '*** RED: dr_query selftest failed.'; exit 1; }
echo "      OK"
echo "[3/6] back up + install email_agent.py -> $DEPLOY/"
[ -f "$DEPLOY/email_agent.py" ] && cp "$DEPLOY/email_agent.py" "$DEPLOY/email_agent.py.bak_s195" && echo "      previous kept as email_agent.py.bak_s195"
cp email_agent.py "$DEPLOY/email_agent.py"; chmod 700 "$DEPLOY/email_agent.py"
python3 -c "import py_compile;py_compile.compile('$DEPLOY/email_agent.py',doraise=True)" || { echo '*** RED compile.'; exit 1; }
echo "[4/6] config template refreshed (your real email_agent.json is left untouched)"
cp email_agent.example.json "$DEPLOY/email_agent.example.json"
if [ -f "$DEPLOY/email_agent.json" ]; then echo "      existing email_agent.json kept (done_label defaults automatically)."; else echo "      no email_agent.json yet — create it from the example (step below)."; fi
echo "[5/6] systemd units (unchanged; refreshed for safety)"
cp email-agent.service email-agent.timer /etc/systemd/system/
systemctl daemon-reload
echo "      done"
echo "[6/6] smoke: selftest + --help"
python3 "$DEPLOY/email_agent.py" --help >/dev/null 2>&1 && echo "      --help OK" || { echo '*** RED: agent will not run.'; exit 1; }
if [ -f "$DEPLOY/email_agent.json" ]; then
  python3 "$DEPLOY/email_agent.py" --selftest 2>&1 | tail -1
fi
echo "==============================================================="
echo " GREEN.  If the timer is already enabled from S194, the next poll"
echo " (<=3 min) runs the hardened agent — nothing else to do."
echo
echo " To verify by hand:"
echo "   python3 $DEPLOY/email_agent.py --selftest      # expect SELFTEST OK"
echo "   python3 $DEPLOY/email_agent.py --once          # one live poll"
echo "   systemctl list-timers | grep email-agent       # confirm 3-min timer"
echo
echo " If you ever need to re-answer a Q: the agent already handled,"
echo " remove the 'clinic-agent-done' label from that mail in Gmail and"
echo " it will be picked up on the next poll."
echo "==============================================================="
