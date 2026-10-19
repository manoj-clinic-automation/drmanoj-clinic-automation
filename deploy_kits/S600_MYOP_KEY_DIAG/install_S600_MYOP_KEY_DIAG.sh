#!/bin/bash
# install_S600_MYOP_KEY_DIAG.sh · kit S600 (session S329, 19-Oct-2026) -- READ-ONLY, SENDS NOTHING, CHANGES NOTHING LIVE.
#   cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S600_MYOP_KEY_DIAG/install_S600_MYOP_KEY_DIAG.sh
# Why: since ~08:50 IST 19-Oct MyOperator answers the clinic's WhatsApp key with HTTP 500. This gathers the evidence for the
# fix or for MyOperator support: the key's shape (never the key), four read-only calls, the sender's last 48 hours.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"
cd "$KDIR" || { echo "!! kit folder not found"; exit 1; }
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || { echo "!! STOPPED: the kit's files do not match SUMS.md5"; exit 1; }
echo "== S600_MYOP_KEY_DIAG (read-only) =="
/root/wa/venv/bin/python3 -B diag_s600.py
