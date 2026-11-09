#!/bin/bash
# rehearse_s756.sh -- the installer rehearsed on a MADE-UP root (never the box): a root with finance/ (the live bytes), shared/, portal/,
# a copy of a finance.db, an assets.db (any copy or a made-up one); stubs for systemctl, journalctl and the health probe. In PHASES:
#   bash rehearse_s756.sh setup <kit dir> <live finance dir> <shared dir> <portal dir> <finance.db copy> <assets.db copy> <scratch dir>
#   bash rehearse_s756.sh dry   <kit dir> <scratch dir>        # DRY on the made-up root: must end '-- DRY RUN ...'
#   bash rehearse_s756.sh real  <kit dir> <scratch dir>        # the real placing: must end 'S756_SUMMARY_DEALER_WA: DONE'; the TO pins
#   bash rehearse_s756.sh again <kit dir> <scratch dir>        # ALREADY INSTALLED
#   bash rehearse_s756.sh red   <kit dir> <scratch dir> <live finance dir>   # a forced red at [7/7] on the FROM files: restored
# Each phase prints its verdict line: 'REHEARSAL S756 <phase>: ok' or 'RED'. The earlier kits' walks run as walk_s755 and walk_s750 in the
# rehearsal (REHEARSE_EARLIER) -- every one of them was run by hand on the same files; on the box the installer runs them all.
set -u
PHASE="$1"; KIT="$2"
F3="scan_register.py purchase_app.py owner_notice.py"
case "$PHASE" in
setup)
  FIN="$3"; SHR="$4"; POR="$5"; FDB="$6"; ADB="$7"; W="$8"
  rm -rf "$W/root" "$W/stub" && mkdir -p "$W/root/finance" "$W/root/assetapp" "$W/root/shared" "$W/root/portal" "$W/root/wa/venv/bin" "$W/root/deploy" "$W/stub"
  cp -p "$FIN"/*.py "$W/root/finance/"; cp -p "$FIN"/*.sql "$W/root/finance/" 2>/dev/null; cp -p "$FIN"/*.json "$FIN"/*.html "$W/root/finance/" 2>/dev/null
  cp -p "$SHR"/*.py "$W/root/shared/"; cp -p "$POR/portal.py" "$W/root/portal/"
  cp "$FDB" "$W/root/finance/finance.db"; cp "$ADB" "$W/root/assetapp/assets.db"
  PY="$(command -v python3)"
  ln -sf "$PY" "$W/root/wa/venv/bin/python3"
  printf '#!/bin/bash\ncase "$1" in show) echo 0;; *) exit 0;; esac\n' > "$W/stub/systemctl"
  printf '#!/bin/bash\ncase "$1" in /finance/healthz) echo 200;; *) echo 403;; esac\n' > "$W/stub/health"
  chmod +x "$W/stub/systemctl" "$W/stub/health"
  echo "PY=$PY" > "$W/env.sh"
  echo "REHEARSAL S756 setup: ok ($W/root: finance $(ls "$W/root/finance" | wc -l) files, shared $(ls "$W/root/shared" | wc -l))"
  ;;
dry|real|again|red)
  W="$3"; . "$W/env.sh"
  ENV="ROOT=$W/root APY=$PY VPY=$W/root/wa/venv/bin/python3 DB=$W/root/finance/finance.db ADB=$W/root/assetapp/assets.db LOCK=$W/root/deploy/.lock HEALTH_CMD=$W/stub/health SYSTEMCTL=$W/stub/systemctl JOURNALCTL=/bin/false TMPW=$W"
  ok=1
  case "$PHASE" in
  dry)
    env $ENV REHEARSE_EARLIER="walk_s755 walk_s750" DRY=1 SKIP_WINDOW=1 bash "$KIT/install_S756_SUMMARY_DEALER_WA.sh" > "$W/reh_dry.txt" 2>&1
    grep -q -- "-- DRY RUN: every gate" "$W/reh_dry.txt" || { ok=0; grep -E '^!!|FAIL|ERROR' "$W/reh_dry.txt" | head -6; }
    ;;
  real)
    env $ENV REHEARSE_EARLIER="walk_s755 walk_s750" SKIP_WINDOW=1 bash "$KIT/install_S756_SUMMARY_DEALER_WA.sh" > "$W/reh_real.txt" 2>&1
    grep -q "S756_SUMMARY_DEALER_WA: DONE" "$W/reh_real.txt" || { ok=0; grep -E '^!!|FAIL|ERROR' "$W/reh_real.txt" | head -8; }
    for f in $F3; do
      want="$(awk -v f="finance/$f" '$2==f{print $1}' "$KIT/TO_PINS.md5")"; have="$(md5sum "$W/root/finance/$f" | awk '{print $1}')"
      [ "$want" = "$have" ] || { ok=0; echo "   !! after the real run finance/$f is ${have:0:8}, not the TO ${want:0:8}"; }
    done
    "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.execute('SELECT COUNT(*) FROM s756_pause')" "$W/root/finance/finance.db" || { ok=0; echo "   !! the table s756_pause was not made"; }
    ;;
  again)
    env $ENV REHEARSE_EARLIER="walk_s755 walk_s750" SKIP_WINDOW=1 bash "$KIT/install_S756_SUMMARY_DEALER_WA.sh" > "$W/reh_again.txt" 2>&1
    grep -q "ALREADY INSTALLED" "$W/reh_again.txt" || { ok=0; tail -3 "$W/reh_again.txt"; }
    ;;
  red)
    FIN="$4"
    for f in $F3; do cp -p "$FIN/$f" "$W/root/finance/$f"; done
    rm -f "$W/root"/finance/*.bak_S756_*
    env $ENV REHEARSE_EARLIER="walk_s755 walk_s750" SKIP_WINDOW=1 REHEARSE_RED_AT=7 bash "$KIT/install_S756_SUMMARY_DEALER_WA.sh" > "$W/reh_red.txt" 2>&1
    grep -q "RED after placing" "$W/reh_red.txt" || { ok=0; echo "   !! the forced red did not trigger the restore"; tail -3 "$W/reh_red.txt"; }
    for f in $F3; do
      [ "$(md5sum "$W/root/finance/$f" | awk '{print $1}')" = "$(md5sum "$FIN/$f" | awk '{print $1}')" ] || { ok=0; echo "   !! after the forced red finance/$f is not the FROM bytes"; }
    done
    ;;
  esac
  echo "   last line: $(tail -n 1 "$W/reh_$PHASE.txt" | cut -c1-220)"
  [ "$ok" = 1 ] && echo "REHEARSAL S756 $PHASE: ok" || echo "REHEARSAL S756 $PHASE: RED -- read the lines above"
  ;;
*) echo "usage: see the header"; exit 2;;
esac
