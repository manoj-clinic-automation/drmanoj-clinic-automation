#!/bin/bash
# The owner's ONE line for both kits: S808 (the sending; his own mobile is this line's last word) and then S809 (the new
# post-visit wording). S809 runs only when S808 ended well. Both folders are copied to /tmp by the line itself.
KDIR="$(cd "$(dirname "$0")" && pwd)"
S808="${S808KIT:-/tmp/s808kit}/install_S808_WA_LADDER_SEND.sh"
[ -f "$S808" ] || { echo "!! STOPPED: kit S808 is not at $S808. Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
bash "$S808" "$@" || { echo "!! S808 did not finish -- S809 was NOT run. Send a photo of this screen to Claude."; exit 1; }
echo
bash "$KDIR/install_S809_WA_POST_VISIT_TEMPLATE.sh"
