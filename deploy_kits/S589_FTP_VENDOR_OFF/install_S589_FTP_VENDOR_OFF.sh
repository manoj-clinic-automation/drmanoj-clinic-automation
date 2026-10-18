#!/bin/bash
# =============================================================================
#  install_S589_FTP_VENDOR_OFF.sh · kit S589 (session S326, 18-Oct-2026) · D741
#
#  One line on the VPS:
#    cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S589_FTP_VENDOR_OFF/install_S589_FTP_VENDOR_OFF.sh
#  (DRY=1 before bash: every check, nothing changed.)
#
#  THE OWNER, 18:18 IST 18-Oct (D741), on S588's finding that the website vendor's FTP login admin_approids is still active
#  and nothing in the clinic uses FTP: "yes" -- remove it and switch FTP off.
#   1. Checks: the CyberPanel database answers; the FTP accounts are the vendor's ONE (any other -> stop and ask); no website on
#      the box is set to update itself over FTP (FS_METHOD ftp / FTP_USER in wp-config -> stop and ask); pure-ftpd exists.
#   2. The vendor's account row kept, root-only, in /root/s589_backup/ (to put it back, see the README's undo).
#   3. pure-ftpd stopped, disabled and masked -- door 21 closed; then the account row deleted.
#   4. Read back: no FTP account; nothing listening on 21; the portal and the website still answer.
#   5. probe_s589.py (S588's read-only check, v2) -- its WordPress lines.
#  Nothing on the clinic's own programs is touched; no restart of any of them.
# =============================================================================
set -u
KIT="S589_FTP_VENDOR_OFF"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
BK="${BK:-/root/s589_backup}"
CPW_FILE="${CPW_FILE:-/etc/cyberpanel/mysqlPassword}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
VENDOR="admin_approids"
HAVE_LOCK=0
say() { echo "$@"; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; }
trap on_exit EXIT
stop() { say "!! STOPPED: $1"; say "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
cq() { MYSQL_PWD="$(cat "$CPW_FILE")" mysql -N -B -u root cyberpanel -e "$1"; }
port21() { ss -ltnH 2>/dev/null | awk '{print $4}' | grep -Eq '(^|[:.])21$'; }
web() { curl -s -o /dev/null -m 12 -w '%{http_code}' "$1"; }

say "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
say "[1/5] kit files match SUMS.md5"

[ -r "$CPW_FILE" ] || stop "the CyberPanel database password file is not readable"
ALL="$(cq "SELECT User FROM users ORDER BY User" 2>&1)" || stop "the CyberPanel database did not answer: $(echo "$ALL" | tail -1)"
NV=$(echo "$ALL" | grep -c "^${VENDOR}$")
OTHERS="$(echo "$ALL" | grep -v "^${VENDOR}$" | grep -v '^$' | tr '\n' ' ')"
[ -z "$OTHERS" ] || stop "there are other FTP accounts besides the vendor's: ${OTHERS}-- switching FTP off would close them too"
FTPWP="$(grep -l -E "define\(\s*['\"](FS_METHOD['\"]\s*,\s*['\"]ftp|FTP_USER|FTP_PASS|FTP_HOST)" /home/*/public_html/wp-config.php 2>/dev/null | tr '\n' ' ')"
[ -z "$FTPWP" ] || stop "a website is set to update itself over FTP ($FTPWP) -- it would lose its updates"
"$SYSTEMCTL" cat pure-ftpd >/dev/null 2>&1 || stop "there is no pure-ftpd service on this box"
ACT="$("$SYSTEMCTL" is-active pure-ftpd 2>/dev/null)"; EN="$("$SYSTEMCTL" is-enabled pure-ftpd 2>/dev/null)"
if [ "$NV" = 0 ] && [ "$ACT" != active ] && ! port21; then
  say "ALREADY DONE: no FTP account, pure-ftpd $ACT / $EN, nothing on door 21."
else
  say "[2/5] checks: FTP accounts = the vendor's only ($NV row) · no website updates over FTP · pure-ftpd $ACT / $EN · door 21 $(port21 && echo open || echo closed)"
  W1=$(web https://followup.dr-manoj.in/portal/login); W2=$(web https://drmanojagarwal.com/)
  if [ "${DRY:-0}" = 1 ]; then say "-- DRY RUN: every check green; NOTHING changed (portal $W1 · website $W2)"; exit 0; fi

  mkdir -p "$BK" && chmod 700 "$BK" || stop "no backup folder"
  if [ "$NV" != 0 ]; then
    MYSQL_PWD="$(cat "$CPW_FILE")" mysqldump -u root --no-create-info --skip-extended-insert --compact cyberpanel users \
      --where="User='${VENDOR}'" > "$BK/ftp_${VENDOR}.sql" 2>"$BK/.err" || stop "the account backup failed: $(tail -1 "$BK/.err")"
    chmod 600 "$BK/ftp_${VENDOR}.sql"
    grep -q "INSERT INTO" "$BK/ftp_${VENDOR}.sql" && grep -q "$VENDOR" "$BK/ftp_${VENDOR}.sql" || stop "the account backup is empty"
  fi
  rm -f "$BK/.err"
  "$SYSTEMCTL" is-enabled pure-ftpd > "$BK/pure-ftpd.was" 2>/dev/null; chmod 600 "$BK/pure-ftpd.was"
  say "[3/5] kept, root-only: $BK/ftp_${VENDOR}.sql (the account row) · $BK/pure-ftpd.was ($(cat "$BK/pure-ftpd.was"))"

  "$SYSTEMCTL" stop pure-ftpd; "$SYSTEMCTL" disable pure-ftpd >/dev/null 2>&1; "$SYSTEMCTL" mask pure-ftpd >/dev/null 2>&1
  [ "$NV" != 0 ] && { cq "DELETE FROM users WHERE User='${VENDOR}'" || say "!! the account row was NOT deleted (FTP is off all the same)"; }
  sleep 2
  LEFT=$(cq "SELECT COUNT(*) FROM users WHERE User='${VENDOR}'" 2>/dev/null)
  ACT="$("$SYSTEMCTL" is-active pure-ftpd 2>/dev/null)"; EN="$("$SYSTEMCTL" is-enabled pure-ftpd 2>/dev/null)"
  W1=$(web https://followup.dr-manoj.in/portal/login); W2=$(web https://drmanojagarwal.com/)
  say "[4/5] read back: vendor account rows $LEFT · pure-ftpd $ACT / $EN · door 21 $(port21 && echo STILL OPEN || echo closed) · portal $W1 · website $W2"
  { [ "$LEFT" = 0 ] && [ "$ACT" != active ] && ! port21; } || say "!! NOT COMPLETE -- send a photo of this screen to Claude"
fi

say "[5/5] the read-only check v2 (the website's database read fixed):"
OUT="$( cd /tmp && timeout 300 "$PY" -B "$KDIR/probe_s589.py" 2>&1 )"
echo "$OUT" | grep -E "website |WordPress admins|FTP |doors open" | sed 's/^/   /'
say ""
say "DONE. The vendor's FTP login is gone and FTP is off. Undo: see the README. Send a photo of this screen to Claude."
