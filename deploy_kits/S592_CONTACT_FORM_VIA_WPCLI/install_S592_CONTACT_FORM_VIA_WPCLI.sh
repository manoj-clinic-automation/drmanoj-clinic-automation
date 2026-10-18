#!/bin/bash
# =============================================================================
#  install_S592_CONTACT_FORM_VIA_WPCLI.sh · kit S592 (session S329, 18-Oct-2026) · D742
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S592_CONTACT_FORM_VIA_WPCLI/install_S592_CONTACT_FORM_VIA_WPCLI.sh
#  (DRY=1 before bash: finds and says what would change; nothing changed.)
#
#  THE OWNER, 18:41 IST 18-Oct (D742): "remove" -- the outside marketing firm's address comes out of the website contact form's
#  e-mail fields, so patient enquiries go to the clinic Gmail only. S591 stopped at the database login (F-938); S592 is the same
#  change reaching the database the way S589 proved (WordPress's own connection through wp-cli), with two fall-backs.
#  All the work is fix_s592.py (its header says exactly what it changes and keeps). No program is restarted.
#  Housekeeping (S326 close, item B8): the two leftover folders /tmp/s578kit and /tmp/s581kit are removed.
# =============================================================================
set -u
KIT="S592_CONTACT_FORM_VIA_WPCLI"
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
PYTHONPYCACHEPREFIX=/tmp/s592_pyc "$PY" -m py_compile fix_s592.py || stop "fix_s592.py does not compile"
rm -rf /tmp/s592_pyc
for d in /tmp/s578kit /tmp/s581kit; do [ -d "$d" ] && rm -rf "$d" && echo "  housekeeping: removed $d"; done
DRY="${DRY:-0}" "$PY" -B fix_s592.py "$@"
