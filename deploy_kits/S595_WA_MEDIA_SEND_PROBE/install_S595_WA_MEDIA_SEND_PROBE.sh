#!/bin/bash
# =============================================================================
#  install_S595_WA_MEDIA_SEND_PROBE.sh · kit S595 (session S329, 19-Oct-2026) · D744 -- the WhatsApp Inbox's first step
#
#  One line on the VPS (first send any message from your phone to the clinic WhatsApp number):
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S595_WA_MEDIA_SEND_PROBE/install_S595_WA_MEDIA_SEND_PROBE.sh
#  (DRY=1 before bash: every check, nothing sent.)
#
#  Sends ONE test photo, ONE test PDF and ONE test voice note to the owner's own number through MyOperator, to prove which media types
#  and message shape work before the inbox is built. Changes nothing live. All the work is probe_s595.py (its header says exactly what).
# =============================================================================
set -u
KIT="S595_WA_MEDIA_SEND_PROBE"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/root/wa/venv/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
HAVE_LOCK=0
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was sent. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s595_pyc "$PY" -m py_compile probe_s595.py || stop "probe_s595.py does not compile"
rm -rf /tmp/s595_pyc
DRY="${DRY:-0}" "$PY" -B probe_s595.py
