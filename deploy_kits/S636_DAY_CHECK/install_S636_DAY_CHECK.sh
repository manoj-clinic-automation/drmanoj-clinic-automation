#!/bin/bash
# =============================================================================
#  install_S636_DAY_CHECK.sh · kit S636 (24-Oct-2026, session S347) · D776 stage 1 · F-1017, F-1018
#    cd /root/deploy/repo && git pull --ff-only && rm -rf /tmp/s636kit && cp -rp /root/deploy/repo/deploy_kits/S636_DAY_CHECK /tmp/s636kit && bash /tmp/s636kit/install_S636_DAY_CHECK.sh
#  (DRY=1 before bash: every gate and the walk, nothing written.)
#
#  /root/finance/day_check.py        NEW                  f223cbf6   the day's corrections (page + check + buttons)
#  /root/finance/clinic_register.py  38d0cb4f -> 321f659a  5 counted edits (make_s636.py): mounts day_check, the chip is a link
#                                                           naming the kinds, the Save says the check, the cards under the three records
#  /root/finance/owner_console.py    2b985708 -> 32780bcb  1 counted edit: his line, counts only, no patient
#  No data step (day_check_tick is made on first request). ONE restart of clinic-finance.
#  Red after placing: the old files back byte-identically, day_check.py set aside, restart, healthz.
#  Undo:  \cp -p /root/finance/clinic_register.py.bak_S636_38d0cb4f /root/finance/clinic_register.py && \cp -p /root/finance/owner_console.py.bak_S636_2b985708 /root/finance/owner_console.py && mv /root/finance/day_check.py /root/finance/day_check.py.off_S636 && systemctl restart clinic-finance
# =============================================================================
set -u
KIT="S636_DAY_CHECK"
KDIR="$(cd "$(dirname "$0")" && pwd)"
PY="${PY:-/usr/bin/python3}"
FIN="${FIN:-/root/finance}"
LOCK="${LOCK:-/root/deploy/.claude_code_build.lock}"
SVC="${SVC:-clinic-finance}"; PORT="${PORT:-8106}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CR="clinic_register.py"; CR_FROM=38d0cb4f0615c9aefcf16d3dee5dfea0; CR_TO=321f659a7310323c7c3003bc044a595a
OC="owner_console.py";   OC_FROM=2b985708b1dc3239fafbb7f41e969e55; OC_TO=32780bcbf4c2a0877df819519cb1334a
DC="day_check.py";       DC_TO=f223cbf68450fe2043068d6698d68a3a
CR_BAK="$FIN/$CR.bak_S636_${CR_FROM:0:8}"; OC_BAK="$FIN/$OC.bak_S636_${OC_FROM:0:8}"
HAVE_LOCK=0
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
on_exit() { [ "$HAVE_LOCK" = 1 ] && rm -rf "$LOCK"; find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
trap on_exit EXIT
stop() { echo "!! STOPPED: $1"; echo "   Nothing was changed. Send a photo of this screen to Claude."; exit 1; }
health() { curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:$PORT/finance/healthz"; }
restore() {
  \cp -p "$CR_BAK" "$FIN/$CR"; \cp -p "$OC_BAK" "$FIN/$OC"
  [ -f "$FIN/$DC" ] && mv "$FIN/$DC" "$FIN/$DC.off_S636"
}

echo "== $KIT =="
cd "$KDIR" || stop "kit folder not found"
md5sum -c SUMS.md5 --quiet >/dev/null 2>&1 || stop "the kit's files do not match SUMS.md5"
echo "1. kit files: all match SUMS.md5"
[ "$(m5 "$KDIR/$CR")" = "$CR_TO" ] || stop "the kit's $CR is not the built file"
[ "$(m5 "$KDIR/$OC")" = "$OC_TO" ] || stop "the kit's $OC is not the built file"
[ "$(m5 "$KDIR/$DC")" = "$DC_TO" ] || stop "the kit's $DC is not the built file"
L_CR=$(m5 "$FIN/$CR"); L_OC=$(m5 "$FIN/$OC"); L_DC=$(m5 "$FIN/$DC")
if [ "$L_CR" = "$CR_TO" ] && [ "$L_OC" = "$OC_TO" ] && [ "$L_DC" = "$DC_TO" ]; then echo "ALREADY INSTALLED."; exit 0; fi
[ "$L_CR" = "$CR_FROM" ] || stop "the live $CR changed since this kit was built (live ${L_CR:0:8}, kit expects ${CR_FROM:0:8})"
[ "$L_OC" = "$OC_FROM" ] || stop "the live $OC changed since this kit was built (live ${L_OC:0:8}, kit expects ${OC_FROM:0:8})"
[ -e "$FIN/$DC" ] && stop "$FIN/$DC already exists (${L_DC:0:8}) - this kit does not overwrite it"
echo "2. the live files are the ones this kit was built from; $DC is new"
for f in "$CR" "$OC" "$DC" walk_s636.py; do "$PY" -B -m py_compile "$KDIR/$f" || stop "$f does not compile with $PY"; done
R=$("$PY" -B walk_s636.py "$KDIR" "$FIN" 2>&1 | tail -1); case "$R" in "27 of 27 green") echo "3. walk: $R";; *) "$PY" -B walk_s636.py "$KDIR" "$FIN" 2>&1 | grep RED; stop "the walk is not green ($R)";; esac
R=$("$PY" -B walk_s636.py "$FIN" "$FIN" --old 2>&1 | tail -1); case "$R" in "24 S636 check(s) red · 0 older red · 3 green") echo "   control on the live files: $R";; *) echo "$R"; stop "the control on the live files did not go red as expected";; esac
R=$("$PY" -B walk_s636.py "$KDIR" "$FIN" --no-day-check 2>&1 | tail -1); case "$R" in *" 0 older red · 3 green") echo "   the new register without day_check.py: $R";; *) echo "$R"; stop "the new register does not stand without day_check.py";; esac
[ "$(health)" = 200 ] || stop "the finance app is not healthy before the install"
[ "${DRY:-0}" = 1 ] && { echo "DRY=1: every gate green; nothing written."; exit 0; }
mkdir "$LOCK" 2>/dev/null || stop "another install is running (lock $LOCK). Wait 5 minutes and run the line again"
HAVE_LOCK=1
\cp -p "$FIN/$CR" "$CR_BAK" && \cp -p "$FIN/$OC" "$OC_BAK" || stop "could not keep the backups"
\cp "$KDIR/$DC" "$FIN/$DC" && chmod --reference="$CR_BAK" "$FIN/$DC" 2>/dev/null
\cp "$KDIR/$CR" "$FIN/$CR" && chmod --reference="$CR_BAK" "$FIN/$CR" 2>/dev/null
\cp "$KDIR/$OC" "$FIN/$OC" && chmod --reference="$OC_BAK" "$FIN/$OC" 2>/dev/null
if [ "$(m5 "$FIN/$CR")" != "$CR_TO" ] || [ "$(m5 "$FIN/$OC")" != "$OC_TO" ] || [ "$(m5 "$FIN/$DC")" != "$DC_TO" ]; then
  restore; stop "read-back did not match; the old files are back"
fi
echo "4. placed $FIN/$DC $DC_TO · $FIN/$CR $CR_TO · $FIN/$OC $OC_TO (backups ${CR_BAK##*/}, ${OC_BAK##*/})"
"$SYSTEMCTL" restart "$SVC"
h=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h=$(health); [ "$h" = 200 ] && break; done
if [ "$h" != 200 ]; then
  echo "!! RED after placing (healthz $h) - putting the old files back"
  restore; "$SYSTEMCTL" restart "$SVC"
  h2=000; for _t in 1 2 3 4 5 6 7 8 9 10; do sleep 3; h2=$(health); [ "$h2" = 200 ] && break; done
  echo "   after the restore: healthz $h2. Send a photo of this screen to Claude."; exit 1
fi
journalctl -u "$SVC" --since "-60 s" --no-pager 2>/dev/null | grep -q "day_check NOT mounted" && echo "   NOTE: the log says day_check did not mount - tell Claude."
echo "5. $SVC restarted; healthz 200"
echo ""
echo "INSTALLED. Each day's corrections: the register's day list -> the day's chip."
