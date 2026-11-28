#!/bin/bash
# rehearse_s979.sh · S979_BATCH_SWAP: the installer on a MADE-UP root (never /root): bash rehearse_s979.sh SETUP|STEP
#   SETUP  lays out R from a code bundle folder (B), a database copy (DB) and the repository's deploy_kits (KITS)
#   STEP   dry | red4 | red5 | install | again | undo | reinstall | wrongfrom | readpin | lock | corrupt   (one step per call)
set -u
K="$(cd "$(dirname "$0")" && pwd)"; R="${R:?R}"; STEP="${1:?step}"
export ROOT="$R/root" LOCK="$R/lock" APY=python3 VPY=python3 TMPW="$R/tmp" NAP=0 REPO_KITS="${KITS:?KITS}"
export SYSTEMCTL="$R/bin/systemctl" CRONTAB="$R/bin/crontab" HEALTH_CMD="$R/bin/health" DOOR_CMD="$R/bin/door" LOG_CMD="$R/bin/log"
export LIVE_DB="$ROOT/finance/finance.db" SPINE="$ROOT/finance/spine/spine.db" ARCHIVE="$ROOT/marg_ingest/archive"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
kit() { rm -rf "$R/kit"; \cp -rp "$K" "$R/kit"; }
inst() { bash "$R/kit/install_S979_BATCH_SWAP.sh" 2>&1 | tail -${1:-6}; }
state() { echo "   files: $(for f in expiry_watch.py stockmatch.py stockmatch.html batch_swap.py; do printf '%s ' "$(m5 "$ROOT/finance/$f" | cut -c1-8)"; done)· cron $(grep -c S979_BATCH_SWAP "$R/crontab.txt")"; }
case "$STEP" in
SETUP) rm -rf "$R"; mkdir -p "$ROOT/finance/spine" "$ROOT/shared" "$ROOT/marg_ingest/archive" "$ROOT/deploy" "$R/bin" "$R/tmp"
  \cp -p "$B"/root/finance/*.py "$B"/root/finance/*.html "$B"/root/finance/*.json "$ROOT/finance/" 2>/dev/null; \cp -p "$B"/root/shared/*.py "$ROOT/shared/"
  \cp -p "$B"/root/finance/spine/*.py "$B"/root/finance/spine/*.json "$ROOT/finance/spine/" 2>/dev/null; \cp -rp "$B"/root/marg_ingest/*.py "$ROOT/marg_ingest/"
  [ -d "$B/root/marg_ingest/xlrd" ] && \cp -rp "$B/root/marg_ingest/xlrd" "$ROOT/marg_ingest/"
  rm -f "$ROOT/finance/batch_swap.py"; \cp -p "$DB" "$LIVE_DB"
  python3 -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); c.executescript('''CREATE TABLE sp_alias (alias TEXT, k20 TEXT); CREATE TABLE sp_close (k20 TEXT, as_on TEXT, units INTEGER);
CREATE TABLE sp_move (k20 TEXT, date TEXT, kind TEXT, units INTEGER); CREATE TABLE sp_sale_line (date TEXT, k20 TEXT, batch TEXT, expiry TEXT, units INTEGER, bill TEXT);
CREATE TABLE sp_sale_bill (date TEXT, bill TEXT, credit_note INTEGER); CREATE TABLE sp_item (k20 TEXT); CREATE TABLE sp_purchase_line (k20 TEXT, date TEXT, supkey TEXT, packing TEXT);'''); c.commit()" "$SPINE"
  printf '30 6 * * * echo old line # S428_STOCK_WATCH\n' > "$R/crontab.txt"
  printf '#!/bin/bash\nexit 0\n' > "$R/bin/systemctl"; printf '#!/bin/bash\necho 200\n' > "$R/bin/health"; printf '#!/bin/bash\necho 302\n' > "$R/bin/door"; printf '#!/bin/bash\necho\n' > "$R/bin/log"
  printf '#!/bin/bash\nif [ "$1" = "-l" ]; then cat "%s"; elif [ "$1" = "-" ]; then cat > "%s.new" && mv "%s.new" "%s"; fi\n' "$R/crontab.txt" "$R/crontab.txt" "$R/crontab.txt" "$R/crontab.txt" > "$R/bin/crontab"
  chmod +x "$R"/bin/*; state; echo "SETUP done";;
dry) kit; DRY=1 inst 8; state;;
red4) kit; REHEARSE_RED_AT=4 inst 9; state;;
red5) kit; REHEARSE_RED_AT=5 inst 9; state; rm -f "$ROOT"/finance/batch_swap.py.removed_S979_*;;
install) kit; inst 8; state;;
again) inst 2; state;;
undo) bash "$R/kit/undo_s979.sh" 2>&1 | tail -7; state;;
reinstall) kit; inst 3; state;;
wrongfrom) bash "$R/kit/undo_s979.sh" >/dev/null 2>&1; echo "# x" >> "$ROOT/finance/stockmatch.py"; kit; inst 2; state; sed -i '$ d' "$ROOT/finance/stockmatch.py";;
readpin) echo "# x" >> "$ROOT/finance/order_rules.py"; kit; inst 2; sed -i '$ d' "$ROOT/finance/order_rules.py"; state;;
lock) mkdir -p "$LOCK"; echo other > "$LOCK/owner"; kit; inst 2; rm -rf "$LOCK"; state;;
corrupt) kit; echo "# x" >> "$R/kit/batch_swap.py"; inst 2; state;;
*) echo "unknown step";;
esac
