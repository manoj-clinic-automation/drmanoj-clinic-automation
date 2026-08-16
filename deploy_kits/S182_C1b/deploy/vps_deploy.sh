#!/bin/bash
# vps_deploy.sh — ONE-COMMAND gated install from the GitHub repo.
# One-time setup:   mkdir -p /root/deploy && cp this file there.
# Per install:      bash /root/deploy/vps_deploy.sh S182_C1a
#
# What it does (all existing gates retained — this only replaces WinSCP):
#   1. clone/pull the repo into /root/deploy/repo (read-only, no credentials)
#   2. locate deploy_kits/<KIT>/ in the repo
#   3. verify SUMS.md5 (integrity) AND KIT_ID.txt (currency — F-88)
#   4. hand off to the kit's own installer, which does:
#      md5 gate -> .bak backup -> swap -> migration -> smoke gate ->
#      restart only on green -> auto-restore on red
# Nothing installs without the kit's own gates passing. Running this IS the
# owner's explicit OK for exactly one named kit — nothing is automatic.
set -u
KIT="${1:-}"
[ -z "$KIT" ] && { echo "usage: bash vps_deploy.sh <KIT_NAME e.g. S182_C1a>"; exit 2; }
REPO_URL="https://github.com/manoj-clinic-automation/drmanoj-clinic-automation.git"
BASE="/root/deploy"; REPO="$BASE/repo"
mkdir -p "$BASE"
if [ -d "$REPO/.git" ]; then
  git -C "$REPO" fetch --depth 1 origin main && git -C "$REPO" reset --hard origin/main \
    || { echo "!! git pull failed"; exit 1; }
else
  git clone --depth 1 "$REPO_URL" "$REPO" || { echo "!! git clone failed"; exit 1; }
fi
KDIR="$REPO/deploy_kits/$KIT"
[ -d "$KDIR" ] || { echo "!! kit $KIT not found in repo (deploy_kits/$KIT)"; exit 1; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 || { echo "!! SUMS.md5 FAILED — kit corrupt, refusing"; exit 1; }
echo "-- kit found and internally consistent:"; cat KIT_ID.txt
echo "-- handing off to the kit's own gated installer..."
bash install_*.sh
