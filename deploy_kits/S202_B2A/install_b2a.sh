#!/bin/bash
# =============================================================================
#  install_b2a.sh · kit S202_B2A — B2, the VPS half of the pipeline heartbeat.
#
#  Every health check on this server watches ARRIVAL AT THE VPS. Four of the
#  seven ways the Marg chain can fail happen entirely on the owner's machines:
#  the medical watcher dies · the 10-minute pull stops · the outbox stops
#  draining · the Drive offsite silently stops. None is visible here. F-179 is
#  the proof -- eleven verified reports sat undelivered for three days while
#  every component reported success.
#
#  This adds the ear: POST /finance/api/pipeline-status (token-scoped, storage
#  in its own table, cannot touch money), six checks that read it, and the
#  NEVER-FIRED WITNESS -- any check that has not once left "ok" in 14+ days is
#  named, because AF-2 was born dead at S195 and stayed green for five sessions.
#
#  NO NEW SECRET: it reuses FINANCE_MARG_TOKEN. Rotation is already the oldest
#  open item and there are three copies of that token; a fourth thing to rotate
#  is a cost paid forever for a convenience used once.
#
#  PROVEN OFFLINE on a harness rebuilt from LIVE BYTES ONLY (S189 method, D188):
#      SMOKE 701 -> 713, +12 exactly (projection written before measuring)
#      FAIL SET BYTE-IDENTICAL (48 -> 48), against BOTH the pre- and
#      post-migration databases.
# =============================================================================
set -u
KIT_NAME="S202_B2A"
APP=/root/finance/finance_app.py
APP_MD5_EXPECTED=eca3723ee5cc391abfbfb0747f375618
APP_MD5_NEW=3576c013464be4fc89eb850d3b5f8ab9
PY=/usr/bin/python3
SVC=clinic-finance.service

echo "=============================================================="
echo "  $KIT_NAME — B2: the VPS can finally see your machines"
echo "=============================================================="
for c in md5sum awk cp date systemctl; do
  command -v "$c" >/dev/null 2>&1 || { echo "!! preflight: '$c' missing — refusing"; exit 1; }
done
[ -x "$PY" ] || { echo "!! preflight: $PY not executable — refusing"; exit 1; }
echo "[1/7] preflight ok"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { echo "!! [2/7] kit SUMS mismatch — refusing"; exit 1; }
echo "[2/7] kit integrity ok"
A="$(md5sum "$APP" | awk '{print $1}')"
[ "$A" = "$APP_MD5_EXPECTED" ] || { echo "!! [3/7] currency gate — $APP is $A, expected $APP_MD5_EXPECTED"; exit 1; }
echo "[3/7] live-code currency gate ok"
BAK="${APP}.bak_${KIT_NAME}_$(date +%Y%m%d_%H%M%S)"
cp -f "$APP" "$BAK" || { echo "!! [4/7] backup failed"; exit 1; }
echo "[4/7] backup: $BAK"
restore(){ cp -f "$BAK" "$APP"; systemctl restart "$SVC" >/dev/null 2>&1; echo "   restored and restarted"; }
cp -f finance_app.py "$APP" || { echo "!! copy failed"; restore; exit 1; }
[ "$(md5sum "$APP"|awk '{print $1}')" = "$APP_MD5_NEW" ] || { echo "!! installed bytes wrong — restoring"; restore; exit 1; }
systemctl restart "$SVC" || { echo "!! restart failed — restoring"; restore; exit 1; }
sleep 2
systemctl is-active --quiet "$SVC" || { echo "!! $SVC not active — restoring"; restore; exit 1; }
echo "[5/7] installed and $SVC active"
echo "[6/7] running the live smoke suite"
OUT="$(cd /root/finance && "$PY" finance_app.py --selftest 2>&1)"; SUM="$(echo "$OUT" | head -1)"
echo "      $SUM"
if ! echo "$SUM" | grep -qE "(^|[^0-9])713/713([^0-9]|$)"; then
  echo "!! the suite did not report 713/713 — restoring"
  echo "$OUT" | grep "FAIL" | head -12; restore; exit 1; fi
echo "[6/7] smoke 713/713 ✓  (was 701/701)"
echo "[7/7] done"
echo
echo "=============================================================="
echo "  GREEN.  https://followup.dr-manoj.in/finance/health"
echo
echo "  A new row: 'Pipeline heartbeat — manojz has never posted a status'."
echo "  That is CORRECT until the manojz half (S202_B2B) is placed. It is the"
echo "  never-fired witness working: a check that cannot see is saying so,"
echo "  instead of showing a green light that means nothing."
echo
echo "  Reverse:  cp -f $BAK $APP && systemctl restart $SVC"
echo "=============================================================="
