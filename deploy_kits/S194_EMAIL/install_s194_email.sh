#!/bin/bash
# =====================================================================
#  S194_EMAIL · ⭐5 — the ping-pong Gmail query agent
#
#  Installs email_agent.py + a systemd timer (poll every 3 min). The
#  agent reads the clinic Gmail for command emails FROM a trusted sender
#  (subject "Q: cash 30" etc.), runs the READ-ONLY dr_query tool, and
#  replies in-thread. It NEVER runs anything but the dr_query allowlist,
#  and dr_query opens the DB mode=ro (physically cannot write).
#
#  This installer STAGES the agent but does NOT start it — it needs the
#  Gmail app password, which must be placed on the box (never in chat).
#  Steps to go live are printed at the end.
# =====================================================================
set -u; cd "$(dirname "$0")"
DEPLOY=/root/deploy
echo "==============================================================="
echo " S194_EMAIL · ping-pong Gmail query agent (staged, not started)"
echo "==============================================================="
echo "[1/6] kit bytes"; md5sum -c SUMS.md5 || { echo '*** RED. STOP.'; exit 1; }
echo "[2/6] dr_query present + read-only?"
[ -f "$DEPLOY/dr_query.py" ] || { echo "*** RED: $DEPLOY/dr_query.py missing (install S193_TOOLS first)."; exit 1; }
python3 "$DEPLOY/dr_query.py" selftest 2>&1 | tail -1 | grep -q "SELFTEST OK" || { echo '*** RED: dr_query selftest failed.'; exit 1; }
echo "      OK"
echo "[3/6] install email_agent.py -> $DEPLOY/"
cp email_agent.py "$DEPLOY/email_agent.py"; chmod 700 "$DEPLOY/email_agent.py"
python3 -c "import py_compile;py_compile.compile('$DEPLOY/email_agent.py',doraise=True)" || { echo '*** RED compile.'; exit 1; }
echo "[4/6] config template (real config is left untouched if it exists)"
cp email_agent.example.json "$DEPLOY/email_agent.example.json"
if [ -f "$DEPLOY/email_agent.json" ]; then echo "      existing email_agent.json kept."; else echo "      no email_agent.json yet — create it from the example (step below)."; fi
echo "[5/6] systemd units"
cp email-agent.service email-agent.timer /etc/systemd/system/
systemctl daemon-reload
echo "      installed (timer NOT enabled yet)"
echo "[6/6] --help smoke"
python3 "$DEPLOY/email_agent.py" --help >/dev/null 2>&1 && echo "      OK" || { echo '*** RED: agent will not run.'; exit 1; }
echo "==============================================================="
echo " GREEN (staged).  To go LIVE:"
echo "  1) Create the config with your app password (keep it private):"
echo "       cp $DEPLOY/email_agent.example.json $DEPLOY/email_agent.json"
echo "       nano $DEPLOY/email_agent.json      # paste the 16-char app password"
echo "       chmod 600 $DEPLOY/email_agent.json"
echo "  2) Test it (offline check, no mail sent):"
echo "       python3 $DEPLOY/email_agent.py --selftest      # expect SELFTEST OK"
echo "  3) One live poll (send yourself a test first — see below):"
echo "       python3 $DEPLOY/email_agent.py --once"
echo "  4) Turn on the 3-min timer:"
echo "       systemctl enable --now email-agent.timer"
echo "       systemctl list-timers | grep email-agent"
echo "---------------------------------------------------------------"
echo " USE IT: email drmka.ortho@gmail.com from a trusted address with"
echo " subject like:   Q: cash 30     Q: custody     Q: day 2026-08-19"
echo "                 Q: sql SELECT COUNT(*) FROM day_entry"
echo " You'll get the answer back in the same thread within ~3 minutes."
echo "==============================================================="
