#!/bin/bash
# =============================================================================
#  install_S591_CONTACT_FORM_ONE_RECIPIENT.sh · kit S591 (session S326, 18-Oct-2026) · D742
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S591_CONTACT_FORM_ONE_RECIPIENT/install_S591_CONTACT_FORM_ONE_RECIPIENT.sh
#  (DRY=1 before bash: finds and says what would change; nothing changed.)
#
#  THE OWNER, 18:41 IST 18-Oct (D742): "remove" -- the outside marketing firm's address comes out of the website contact form's
#  e-mail fields, so patient enquiries go to the clinic Gmail only. All the work is fix_s591.py (its header says exactly what it
#  changes and keeps). No program is restarted; the website reads the new form settings at the next enquiry.
# =============================================================================
set -u
KIT="S591_CONTACT_FORM_ONE_RECIPIENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
HAVE_LOCK=0
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
PYTHONPYCACHEPREFIX=/tmp/s591_pyc "$PY" -m py_compile fix_s591.py || stop "fix_s591.py does not compile"
rm -rf /tmp/s591_pyc
DRY="${DRY:-0}" "$PY" -B fix_s591.py
