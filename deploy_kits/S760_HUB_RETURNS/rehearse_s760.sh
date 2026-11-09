#!/bin/bash
# rehearse_s760.sh -- the installer rehearsed on a MADE-UP root (never the box): a root with finance/ (the live bytes: finance, spine,
# finance_ui), shared/, a copy of a finance.db; stubs for systemctl and the health probe. In PHASES:
#   bash rehearse_s760.sh setup <kit dir> <live root holding finance/ and shared/> <finance.db copy> <scratch dir> [<flask lib dir>]
#   bash rehearse_s760.sh dry   <kit dir> <scratch dir>        # DRY on the made-up root: must end '-- DRY RUN ...'
#   bash rehearse_s760.sh real  <kit dir> <scratch dir>        # the real placing: must end 'S760_HUB_RETURNS: DONE'; the TO pins
#   bash rehearse_s760.sh again <kit dir> <scratch dir>        # ALREADY INSTALLED
#   bash rehearse_s760.sh red   <kit dir> <scratch dir> <live root>   # a forced red at [7/7] on the FROM files: restored
# Each phase prints 'REHEARSAL S760 <phase>: ok' or 'RED'. The earlier walks run as walk_s677 alone here (REHEARSE_EARLIER); S406 and
# S368 were run by hand on the same files (identical old / new); on the box the installer runs all three.
set -u
PHASE="$1"; KIT="$2"
F3="finance/returns_kinds.py finance/darpan_app.py finance/finance_ui/finance_approvals.html finance/sanjeevni_approvals.py"
case "$PHASE" in
setup)
  LR="$3"; FDB="$4"; W="$5"; LIB="${6:-}"
  rm -rf "$W/root" "$W/stub" && mkdir -p "$W/root/finance/spine" "$W/root/finance/finance_ui" "$W/root/shared" "$W/root/wa/venv/bin" "$W/root/deploy" "$W/stub"
  cp -p "$LR"/finance/*.py "$LR"/finance/*.json "$LR"/finance/*.sql "$LR"/finance/*.html "$W/root/finance/" 2>/dev/null
  cp -p "$LR"/finance/spine/* "$W/root/finance/spine/"; cp -p "$LR"/finance/finance_ui/* "$W/root/finance/finance_ui/"
  cp -p "$LR"/shared/*.py "$W/root/shared/"
  cp "$FDB" "$W/root/finance/finance.db"
  PY="$(command -v python3)"
  printf '#!/bin/bash\nexport PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}%s"\nexec %s "$@"\n' "$LIB" "$PY" > "$W/root/wa/venv/bin/python3"
  chmod +x "$W/root/wa/venv/bin/python3"
  printf '#!/bin/bash\ncase "$1" in show) echo 0;; *) exit 0;; esac\n' > "$W/stub/systemctl"
  printf '#!/bin/bash\ncase "$1" in /finance/healthz) echo 200;; *) echo 403;; esac\n' > "$W/stub/health"
  chmod +x "$W/stub/systemctl" "$W/stub/health"
  echo "PY=$PY" > "$W/env.sh"
  echo "REHEARSAL S760 setup: ok ($W/root: finance $(ls "$W/root/finance" | wc -l) entries, shared $(ls "$W/root/shared" | wc -l))"
  ;;
dry|real|again|red)
  W="$3"; . "$W/env.sh"
  ENV="ROOT=$W/root APY=$PY VPY=$W/root/wa/venv/bin/python3 DB=$W/root/finance/finance.db LOCK=$W/root/deploy/.lock HEALTH_CMD=$W/stub/health SYSTEMCTL=$W/stub/systemctl JOURNALCTL=/bin/false TMPW=$W"
  ok=1
  case "$PHASE" in
  dry)
    env $ENV REHEARSE_EARLIER="walk_s677" DRY=1 SKIP_WINDOW=1 bash "$KIT/install_S760_HUB_RETURNS.sh" > "$W/reh_dry.txt" 2>&1
    grep -q -- "-- DRY RUN: every gate" "$W/reh_dry.txt" || { ok=0; grep -E '^!!|RED|ERROR' "$W/reh_dry.txt" | head -6; }
    ;;
  real)
    env $ENV REHEARSE_EARLIER="walk_s677" SKIP_WINDOW=1 bash "$KIT/install_S760_HUB_RETURNS.sh" > "$W/reh_real.txt" 2>&1
    grep -q "S760_HUB_RETURNS: DONE" "$W/reh_real.txt" || { ok=0; grep -E '^!!|RED|ERROR' "$W/reh_real.txt" | head -8; }
    for f in $F3; do
      want="$(awk -v f="$f" '$2==f{print $1}' "$KIT/TO_PINS.md5")"; have="$(md5sum "$W/root/$f" | awk '{print $1}')"
      [ "$want" = "$have" ] || { ok=0; echo "   !! after the real run $f is ${have:0:8}, not the TO ${want:0:8}"; }
    done
    ;;
  again)
    env $ENV REHEARSE_EARLIER="walk_s677" SKIP_WINDOW=1 bash "$KIT/install_S760_HUB_RETURNS.sh" > "$W/reh_again.txt" 2>&1
    grep -q "ALREADY INSTALLED" "$W/reh_again.txt" || { ok=0; tail -3 "$W/reh_again.txt"; }
    ;;
  red)
    LR="$4"
    for f in $F3; do cp -p "$LR/$f" "$W/root/$f"; done
    rm -f "$W/root"/finance/*.bak_S760_* "$W/root"/finance/finance_ui/*.bak_S760_*
    env $ENV REHEARSE_EARLIER="walk_s677" SKIP_WINDOW=1 REHEARSE_RED_AT=7 bash "$KIT/install_S760_HUB_RETURNS.sh" > "$W/reh_red.txt" 2>&1
    grep -q "RED after placing" "$W/reh_red.txt" || { ok=0; echo "   !! the forced red did not trigger the restore"; tail -3 "$W/reh_red.txt"; }
    for f in $F3; do
      [ "$(md5sum "$W/root/$f" | awk '{print $1}')" = "$(md5sum "$LR/$f" | awk '{print $1}')" ] || { ok=0; echo "   !! after the forced red $f is not the FROM bytes"; }
    done
    ;;
  esac
  echo "   last line: $(tail -n 1 "$W/reh_$PHASE.txt" | cut -c1-220)"
  [ "$ok" = 1 ] && echo "REHEARSAL S760 $PHASE: ok" || echo "REHEARSAL S760 $PHASE: RED -- read the lines above"
  ;;
*) echo "usage: see the header"; exit 2;;
esac
