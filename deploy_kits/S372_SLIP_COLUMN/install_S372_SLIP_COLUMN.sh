#!/bin/bash
# install_S372_SLIP_COLUMN.sh · kit S372_SLIP_COLUMN (session 279, 23-Sep-2026)
# THE OWNER, 23-Sep-2026: "assign that slip number to the daily report ... so that the first column is the physical
# slip number. Wherever ... not available, leave it blank for the time being till the staff get used to this workflow."
# The Day Revenue page (/finance/clinic/day/<date>) and its PDF (the one shared to WhatsApp) gain a first column "Slip"
# from the Chamber Slip Log (D557): OPD book for consultations / revisits / concessions, X-ray & Proc book for X-rays
# and procedures; blank when there is no live slip for that person, that book, that day. Read-only on the slip log.
#   NEW /root/finance/slip_lookup.py            06e06cd0986c9cb862d8cb7895cfcc1f
#   /root/finance/finance_clinic_day.py  15818d91 -> 738308b3af38db09d98b25a450d98bef   (three anchored edits)
#   /root/finance/clinic_day_pdf.py      518affe9 -> ce843733539bb091d86abf1f664c43d7   (six anchored edits)
#   finance_app.py NOT touched (it imports both modules unchanged). Restarts clinic-finance.
# Run: cd /root/deploy/repo && git pull --ff-only && bash /root/deploy/repo/deploy_kits/S372_SLIP_COLUMN/install_S372_SLIP_COLUMN.sh
set -u
KIT="S372_SLIP_COLUMN"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"; PORT="${FIN_PORT:-8106}"
D_FROM=15818d91ab1b553e76e317d603d37963; D_TO=738308b3af38db09d98b25a450d98bef; P_FROM=518affe983e02a266f943bced48e9c35; P_TO=ce843733539bb091d86abf1f664c43d7; SL=06e06cd0986c9cb862d8cb7895cfcc1f
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s372_walk_$STAMP"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }; probe() { curl -s -o /dev/null -m 8 -w '%{http_code}' "$1"; }
cd "$KDIR" || exit 1
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/6] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/6] KIT_ID.txt names another kit"; exit 1; }
[ "$(m5 finance_clinic_day.py)" = "$D_TO" ] && [ "$(m5 clinic_day_pdf.py)" = "$P_TO" ] && [ "$(m5 slip_lookup.py)" = "$SL" ] || { say "!! [1/6] kit files not at their pins"; exit 1; }
say "[1/6] kit gates green"
if [ "$(m5 "$FIN/finance_clinic_day.py")" = "$D_TO" ] && [ "$(m5 "$FIN/clinic_day_pdf.py")" = "$P_TO" ] && [ "$(m5 "$FIN/slip_lookup.py")" = "$SL" ]; then say "-- ALREADY INSTALLED. Nothing to do."; exit 0; fi
[ "$(m5 "$FIN/finance_clinic_day.py")" = "$D_FROM" ] && [ "$(m5 "$FIN/clinic_day_pdf.py")" = "$P_FROM" ] || { say "!! [2/6] live files are $(m5 "$FIN/finance_clinic_day.py") / $(m5 "$FIN/clinic_day_pdf.py"), not the S255/S224 pins - nothing installed"; exit 1; }
[ -e "$FIN/slip_lookup.py" ] && { say "!! [2/6] $FIN/slip_lookup.py already exists and is not the kit's - nothing installed"; exit 1; }
say "[2/6] live pins exact"
mkdir -p "$WALK/new" "$WALK/live" && \cp -p finance_clinic_day.py clinic_day_pdf.py slip_lookup.py "$WALK/new/" && \cp -p "$FIN/finance_clinic_day.py" "$FIN/clinic_day_pdf.py" "$WALK/live/" || { say "!! [3/6] scratch copy failed"; rm -rf "$WALK"; exit 1; }
"$VPY" -B -m py_compile "$WALK/new/finance_clinic_day.py" "$WALK/new/clinic_day_pdf.py" "$WALK/new/slip_lookup.py" || { say "!! [3/6] compile failed"; rm -rf "$WALK"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s372.py" "$WALK/new" "$WALK/live" 2>&1 | tail -1 )"; rm -rf "$WALK"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/6] walk red: $WOUT - nothing installed"; exit 1; }
say "[3/6] $WOUT (scratch db with a real-shaped day; the LIVE modules are the negative control)"
BD="$FIN/finance_clinic_day.py.bak_S372_15818d91"; BP="$FIN/clinic_day_pdf.py.bak_S372_518affe9"
\cp -p "$FIN/finance_clinic_day.py" "$BD" && \cp -p "$FIN/clinic_day_pdf.py" "$BP" || { say "!! [4/6] backup failed"; exit 1; }
restore() { say "!! RED after placing - restoring byte-identically"; \cp -p "$BD" "$FIN/finance_clinic_day.py"; \cp -p "$BP" "$FIN/clinic_day_pdf.py"; mv -f "$FIN/slip_lookup.py" "$FIN/slip_lookup.py.removed_S372_$STAMP" 2>/dev/null; systemctl restart clinic-finance || true; sleep 4; say "   $(m5 "$FIN/finance_clinic_day.py") · finance $(probe http://127.0.0.1:$PORT/finance/healthz)"; exit 1; }
\cp -p slip_lookup.py finance_clinic_day.py clinic_day_pdf.py "$FIN/" && [ "$(m5 "$FIN/finance_clinic_day.py")" = "$D_TO" ] && [ "$(m5 "$FIN/clinic_day_pdf.py")" = "$P_TO" ] || restore
say "[4/6] placed; backups $BD · $BP"
systemctl restart clinic-finance || restore; sleep 5; systemctl is-active --quiet clinic-finance || restore
H=$(probe "http://127.0.0.1:$PORT/finance/healthz"); DY=$(probe "http://127.0.0.1:$PORT/finance/clinic/day"); SH=$(probe "http://127.0.0.1:$PORT/finance/clinic/share")
say "      healthz $H · /finance/clinic/day without login $DY · /finance/clinic/share $SH (302/401 expected)"
[ "$H" = 200 ] && { [ "$DY" = 302 ] || [ "$DY" = 401 ] || [ "$DY" = 200 ]; } || restore
journalctl -u clinic-finance --since "-2 min" --no-pager 2>/dev/null | grep -qi "Traceback\|ImportError" && restore
say "[5/6] clinic-finance active, no import error"
say "[6/6] all green -- $KIT: DONE. Read next: https://followup.dr-manoj.in/finance/clinic/day"
md5sum "$FIN/finance_clinic_day.py" "$FIN/clinic_day_pdf.py" "$FIN/slip_lookup.py"
