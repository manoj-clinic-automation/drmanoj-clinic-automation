#!/bin/bash
# rehearse_s750.sh -- the installer rehearsed on a MADE-UP root (never the box): a root with finance/ (the live bytes), assetapp/ (the bundle's),
# shared/, portal/, a copy of a finance.db, a made-up empty assets.db the scan app makes itself; stubs for systemctl, journalctl and the
# health probe. In PHASES, each a few minutes at most (the device shell times a call out at three minutes):
#   bash rehearse_s750.sh setup <kit dir> <live finance dir> <assetapp dir> <shared dir> <portal dir> <finance.db copy> <scratch dir>
#   bash rehearse_s750.sh dry   <kit dir> <scratch dir>        # DRY on the made-up root: must end '-- DRY RUN ...'
#   bash rehearse_s750.sh real  <kit dir> <scratch dir>        # the real placing: must end 'S750_MONTH_END: DONE'; the TO pins; the two tables
#   bash rehearse_s750.sh again <kit dir> <scratch dir>        # ALREADY INSTALLED
#   bash rehearse_s750.sh red   <kit dir> <scratch dir> <live finance dir> <assetapp dir>   # a forced red at [7/8] on the FROM files: restored
# Each phase prints its verdict line; 'REHEARSAL S750 <phase>: ok' or 'RED'. The earlier kits' walks run as walk_s740 only in the rehearsal
# (REHEARSE_EARLIER) -- every one of them was run by hand on the same files; on the box the installer runs them all.
set -u
PHASE="$1"; KIT="$2"
case "$PHASE" in
setup)
  FIN="$3"; AST="$4"; SHR="$5"; POR="$6"; FDB="$7"; W="$8"
  rm -rf "$W/root" "$W/stub" "$W/tmpw" && mkdir -p "$W/root/finance" "$W/root/assetapp" "$W/root/shared" "$W/root/portal" "$W/root/wa/venv/bin" "$W/root/deploy" "$W/stub" "$W/tmpw"
  cp -p "$FIN"/*.py "$W/root/finance/"; cp -p "$FIN"/*.sql "$W/root/finance/" 2>/dev/null; cp -p "$FIN"/*.json "$FIN"/*.html "$W/root/finance/" 2>/dev/null
  cp -p "$AST"/*.py "$W/root/assetapp/"; cp -p "$AST"/*.js "$AST"/*.json "$W/root/assetapp/" 2>/dev/null
  cp -p "$SHR"/*.py "$W/root/shared/"; cp -p "$POR/portal.py" "$W/root/portal/"
  cp "$FDB" "$W/root/finance/finance.db"
  PY="$(command -v python3)"
  ln -sf "$PY" "$W/root/wa/venv/bin/python3"
  ( cd "$W/root/assetapp" && ASSETS_DB="$W/root/assetapp/assets.db" ASSETS_UPLOADS="$W/root/assetapp/uploads" SHARED_LIB_DIR="$W/noshared" \
    SCANAPP_ANTHROPIC_KEY_FILE="$W/nokey" CLINIC_PORTAL_DIR="$W/noportal" FINANCE_LOCAL_URL="http://127.0.0.1:9" FINANCE_DB_FOR_SCANS="$W/nofin.db" \
    "$PY" -W ignore -B -c "import asset_register" >/dev/null 2>&1 ) || true
  [ -f "$W/root/assetapp/assets.db" ] || { echo "REHEARSAL S750 setup: RED -- the made-up assets.db was not created"; exit 1; }
  printf '#!/bin/bash\ncase "$1" in show) echo 0;; *) exit 0;; esac\n' > "$W/stub/systemctl"
  printf '#!/bin/bash\ncase "$1" in /finance/healthz|/healthz) echo 200;; *) echo 403;; esac\n' > "$W/stub/health"
  chmod +x "$W/stub/systemctl" "$W/stub/health"
  echo "PY=$PY" > "$W/env.sh"
  echo "REHEARSAL S750 setup: ok ($W/root: finance $(ls "$W/root/finance" | wc -l) files, assetapp $(ls "$W/root/assetapp" | wc -l), a made-up assets.db)"
  ;;
dry|real|again|red)
  W="$3"; . "$W/env.sh"
  ENV="ROOT=$W/root APY=$PY VPY=$W/root/wa/venv/bin/python3 DB=$W/root/finance/finance.db ADB=$W/root/assetapp/assets.db LOCK=$W/root/deploy/.lock HEALTH_CMD=$W/stub/health SYSTEMCTL=$W/stub/systemctl JOURNALCTL=/bin/false TMPW=$W/tmpw TMPDIR=$W/tmpw REHEARSE_EARLIER=walk_s740"
  ok=1
  case "$PHASE" in
  dry)
    env $ENV DRY=1 SKIP_WINDOW=1 bash "$KIT/install_S750_MONTH_END.sh" > "$W/reh_dry.txt" 2>&1
    grep -q -- "-- DRY RUN: every gate" "$W/reh_dry.txt" || { ok=0; grep -E '^!!|FAIL' "$W/reh_dry.txt" | head -6; }
    ;;
  real)
    env $ENV SKIP_WINDOW=1 bash "$KIT/install_S750_MONTH_END.sh" > "$W/reh_real.txt" 2>&1
    grep -q "S750_MONTH_END: DONE" "$W/reh_real.txt" || { ok=0; grep -E '^!!|FAIL' "$W/reh_real.txt" | head -8; }
    for f in finance/scan_register.py finance/purchase_app.py finance/amir_day.py finance/porders_s454.py assetapp/asset_register.py assetapp/claude_reader.py; do
      want="$(awk -v f="$f" '$2==f{print $1}' "$KIT/TO_PINS.md5")"; have="$(md5sum "$W/root/$f" | awk '{print $1}')"
      [ "$want" = "$have" ] || { ok=0; echo "   !! after the real run $f is ${have:0:8}, not the TO ${want:0:8}"; }
    done
    "$PY" - "$W/root/finance/finance.db" <<'EOF' || ok=0
import sqlite3, sys
con = sqlite3.connect(sys.argv[1]); t = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 's750_%'")}
print("   tables after the real run:", ", ".join(sorted(t)) or "none"); sys.exit(0 if t == {"s750_answer", "s750_dealer_of"} else 1)
EOF
    ;;
  again)
    env $ENV SKIP_WINDOW=1 bash "$KIT/install_S750_MONTH_END.sh" > "$W/reh_again.txt" 2>&1
    grep -q "ALREADY INSTALLED" "$W/reh_again.txt" || { ok=0; tail -3 "$W/reh_again.txt"; }
    ;;
  red)
    FIN="$4"; AST="$5"
    for f in scan_register.py purchase_app.py amir_day.py porders_s454.py; do cp -p "$FIN/$f" "$W/root/finance/$f"; done
    for f in asset_register.py claude_reader.py; do cp -p "$AST/$f" "$W/root/assetapp/$f"; done
    rm -f "$W/root"/finance/*.bak_S750_* "$W/root"/assetapp/*.bak_S750_*
    env $ENV SKIP_WINDOW=1 REHEARSE_RED_AT=7 bash "$KIT/install_S750_MONTH_END.sh" > "$W/reh_red.txt" 2>&1
    grep -q "RED after placing" "$W/reh_red.txt" || { ok=0; echo "   !! the forced red did not trigger the restore"; tail -3 "$W/reh_red.txt"; }
    for f in scan_register.py purchase_app.py amir_day.py porders_s454.py; do
      [ "$(md5sum "$W/root/finance/$f" | awk '{print $1}')" = "$(md5sum "$FIN/$f" | awk '{print $1}')" ] || { ok=0; echo "   !! after the forced red finance/$f is not the FROM bytes"; }
    done
    for f in asset_register.py claude_reader.py; do
      [ "$(md5sum "$W/root/assetapp/$f" | awk '{print $1}')" = "$(md5sum "$AST/$f" | awk '{print $1}')" ] || { ok=0; echo "   !! after the forced red assetapp/$f is not the FROM bytes"; }
    done
    ;;
  esac
  echo "   last line: $(tail -n 1 "$W/reh_$PHASE.txt" | cut -c1-220)"
  [ "$ok" = 1 ] && echo "REHEARSAL S750 $PHASE: ok" || echo "REHEARSAL S750 $PHASE: RED -- read the lines above"
  ;;
*) echo "usage: see the header"; exit 2;;
esac
