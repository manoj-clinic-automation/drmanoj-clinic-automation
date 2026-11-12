#!/bin/bash
# rehearse_s803.sh FINANCE_DIR SHARED_DIR SCHEMA_DB ASSETS_DB -- the installer on a MADE-UP root (never /root):
#   dry / a changed live file / the new file already there / install / again / the undo line / a red at [6/6] / a kit file altered.
# FINANCE_DIR, SHARED_DIR: copies of /root/finance and /root/shared (the newest bundle). SCHEMA_DB: a finance.db (the walk reads its layout;
# the stand-in root gets a COPY as its finance.db). ASSETS_DB: a stand-in assets.db for the proof. Last line: 'REHEARSAL S803 8/8'.
set -u
KDIR="$(cd "$(dirname "$0")" && pwd)"; LIVE="$1"; SH="$2"; SDB="$3"; ADB="$4"
PY="${PY:-$(command -v python3)}"
R="${RTMP:-/tmp}/r803"; OK=0
mk() { rm -rf "$R"; mkdir -p "$R/root" "$R/tmp"; \cp -rp "$LIVE" "$R/root/finance"; \cp -rp "$SH" "$R/root/shared"; \cp -p "$SDB" "$R/root/finance/finance.db"; find "$R/root" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null; }
cat > "$R.sysctl" <<'E'
#!/bin/bash
exit 0
E
cat > "$R.health" <<'E'
#!/bin/bash
echo 200
E
chmod +x "$R.sysctl" "$R.health"
run() { env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL=/nonexistent HEALTH_CMD="$R.health" NAP=0 \
          PROOF_ASSETS="$ADB" ASSETS_DB="$ADB" OWNER_NOTICE_STUB="$R/tmp/said.jsonl" OWNER_NOTICE_LOCK="$R/tmp/tick.lock" "$@" bash "$KDIR/install_S803_MARG_WATCH_BILLS.sh" 2>&1; }
pins() { for f in sanjeevni_approvals.py owner_notice.py finance_ui/finance_approvals.html marg_billwatch.py; do printf '%s ' "$(md5sum "$R/root/finance/$f" 2>/dev/null | cut -c1-8)"; done; }
FROMP="569c5ee4 537b7c32 6a4178ea  "
TOP="$(awk '$2=="finance/sanjeevni_approvals.py"{a=substr($1,1,8)} $2=="finance/owner_notice.py"{b=substr($1,1,8)} $2=="finance/finance_ui/finance_approvals.html"{h=substr($1,1,8)} $2=="finance/marg_billwatch.py"{c=substr($1,1,8)} END{printf "%s %s %s %s ", a, b, h, c}' "$KDIR/TO_PINS.md5")"
tabs() { "$PY" -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute(\"select count(*) from sqlite_master where name like 'billwatch_%' and type='table'\").fetchone()[0], (c.execute(\"select count(*) from setting where key='billchange.since'\").fetchone()[0]))" "$R/root/finance/finance.db"; }

mk; O=$(run DRY=1); P=$(pins)
echo "$O" | grep -q "DRY RUN: every gate" && [ "$P" = "$FROMP" ] && [ "$(tabs)" = "0 0" ] && { echo "GREEN 1 dry: every gate green, nothing written (no file, no table)"; OK=$((OK+1)); } || { echo "RED 1 dry"; echo "$O" | tail -6; echo "pins: $P tabs: $(tabs)"; }

mk; echo "# a change" >> "$R/root/finance/owner_notice.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*changed after this kit was built" && [ ! -e "$R/root/finance/marg_billwatch.py" ] && [ ! -d "$R/lock" ] && { echo "GREEN 2 a changed live file: stopped at [2/6], nothing placed, lock released"; OK=$((OK+1)); } || { echo "RED 2"; echo "$O" | tail -4; }

mk; echo "# stray" > "$R/root/finance/marg_billwatch.py"; O=$(run)
echo "$O" | grep -q "\[2/6\].*already exists" && [ "$(md5sum "$R/root/finance/sanjeevni_approvals.py" | cut -c1-8)" = "569c5ee4" ] && [ ! -d "$R/lock" ] && { echo "GREEN 3 the new file already there: stopped at [2/6], nothing placed"; OK=$((OK+1)); } || { echo "RED 3"; echo "$O" | tail -4; }

mk; O=$(run); P=$(pins)
echo "$O" | grep -q "S803_MARG_WATCH_BILLS: DONE" && [ "$P" = "$TOP" ] && [ "$(tabs)" = "2 1" ] && ls "$R/root/finance/"*.bak_S803_* >/dev/null 2>&1 && [ ! -d "$R/lock" ] && [ ! -s "$R/tmp/said.jsonl" ] \
  && { echo "GREEN 4 install: the four files at TO, the fill done (2 tables, the page begun), backups, lock released, NOTHING said to the phone road"; OK=$((OK+1)); } || { echo "RED 4"; echo "$O" | tail -10; echo "pins $P / $TOP; tabs $(tabs)"; }
UNDO="$(echo "$O" | grep '^undo (one line): ' | sed 's/^undo (one line): //')"

O2=$(run); echo "$O2" | grep -q "ALREADY INSTALLED" && { echo "GREEN 5 again: already installed, nothing written"; OK=$((OK+1)); } || { echo "RED 5"; echo "$O2" | tail -3; }

( eval "$UNDO" ) >/dev/null 2>&1; P=$(pins)
[ -n "$UNDO" ] && [ "$P" = "$FROMP" ] && { echo "GREEN 6 the undo line: the three files back byte-identical, the new file gone"; OK=$((OK+1)); } || { echo "RED 6 undo"; echo "pins: $P"; echo "$UNDO"; }

mk; O=$(run REHEARSE_RED_AT=6); P=$(pins)
echo "$O" | grep -q "RED after placing" && [ "$P" = "$FROMP" ] && [ ! -d "$R/lock" ] && { echo "GREEN 7 a red at [6/6]: the three files put back, the new one removed, lock released"; OK=$((OK+1)); } || { echo "RED 7"; echo "$O" | tail -6; echo "pins: $P"; }

mk; K2="$R/kit"; \cp -rp "$KDIR" "$K2"; echo "# altered" >> "$K2/marg_billwatch.py"
O=$(env ROOT="$R/root" SKIP_WINDOW=1 LOCK="$R/lock" TMPW="$R/tmp" APY="$PY" VPY="$PY" SYSTEMCTL="$R.sysctl" JOURNALCTL=/nonexistent HEALTH_CMD="$R.health" NAP=0 bash "$K2/install_S803_MARG_WATCH_BILLS.sh" 2>&1); P=$(pins)
echo "$O" | grep -q "SUMS.md5 gate failed" && [ "$P" = "$FROMP" ] && { echo "GREEN 8 a kit file altered: the SUMS gate stops it, nothing installed"; OK=$((OK+1)); } || { echo "RED 8"; echo "$O" | tail -4; }
rm -rf "$R" "$R.sysctl" "$R.health"
echo "REHEARSAL S803 $OK/8"
