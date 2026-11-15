#!/bin/bash
# rehearse_s837.sh BUNDLE_ROOT FINANCE_DB VPY OLDK DMAP [PART] -- the installer on a stand-in root (never the box). PART A: dry, install,
# the switch, again, undo, again. PART B: a forced red at [4/7] and at [5/7], his list page 404, a drifted live file, a corrupt kit, the lock
# held. PART C: the section A walk (S812) judged as a regression check, with made-up walks: the same reds on live and rebuilt -> installed;
# a check red only on the rebuilt -> stop; the walk not finishing -> stop. all (default): A, B and C.
# The health answer is a one-line script that prints 200 (the installer calls "$HEALTH_CMD /finance/healthz"). Last line 'REHEARSAL n/m'.
set -u
B="$1"; FDB="$2"; VPY="$3"; OLDK="$4"; DMAP="$5"; PART="${6:-all}"; K="$(cd "$(dirname "$0")" && pwd)"; W=$(mktemp -d /tmp/r837_XXXX); ok=0; tot=0
printf '#!/bin/sh\necho 200\n' > "$W/hz.sh"; chmod +x "$W/hz.sh"
chk() { tot=$((tot+1)); if eval "$2"; then ok=$((ok+1)); echo "PASS  $1"; else echo "FAIL  $1"; fi; }
mk() { rm -rf "$W/root" "$W/kit" "$W/lock"; mkdir -p "$W/root/finance/spine" "$W/root/deploy"; cp -rp "$B/finance/." "$W/root/finance/"; cp -rp "$B/marg_ingest" "$W/root/";
  cp -rp "$B/shared" "$W/root/"; cp "$FDB" "$W/root/finance/finance.db"; "$VPY" -c "import sqlite3;sqlite3.connect('$W/root/finance/spine/spine.db').close()"; cp -rp "$K" "$W/kit"; }
run() { env ROOT="$W/root" VPY="$VPY" APY=python3 OLDK="$OLDK" DMAP="$DMAP" LOCK="$W/lock" SYSTEMCTL=true HEALTH_CMD="$W/hz.sh" NAP=0 TMPW="$W" \
  REHEARSE_NO_S812=1 "$@" bash "$W/kit/install_S837_STOCK_REGISTER_ONE_ITEM.sh" 2>&1; }
pins() { (cd "$W/root" && md5sum -c "$W/kit/TO_PINS.md5" >/dev/null 2>&1); }
from() { for f in finance/marg_billwatch.py:960b5309 finance/reports_tile.py:163a869a finance/sanjeevni_approvals.py:ae29e2bc \
  finance/finance_ui/finance_approvals.html:82f459ef marg_ingest/marg_take.py:5cad2d24 marg_ingest/marg_ingest.py:828c4dad; do
  [ "$(md5sum "$W/root/${f%%:*}" | cut -c1-8)" = "${f##*:}" ] || return 1; done; [ ! -e "$W/root/marg_ingest/marg_register.py" ]; }
if [ "$PART" = A ] || [ "$PART" = all ]; then
mk; O=$(run DRY=1); chk "dry run: every gate and walk green, nothing written" 'echo "$O" | grep -q "DRY RUN: every gate" && from'
O=$(run); chk "install: DONE, the seven files at their TO pins" 'echo "$O" | grep -q ": DONE" && pins'
chk "... the switch OFF and the tables made" '"$VPY" -c "import sqlite3;c=sqlite3.connect(\"$W/root/finance/finance.db\");print(c.execute(\"select value from setting where key=\x27mwr.reg_shavez\x27\").fetchone()[0])" | grep -qx off'
O=$(run); chk "again: ALREADY INSTALLED" 'echo "$O" | grep -q "ALREADY INSTALLED"'
"$VPY" -c "import sqlite3;c=sqlite3.connect('$W/root/finance/finance.db');c.execute(\"INSERT INTO marg_watch_report (ref, kind, day_from, day_to, why, row_keys, asked_by, asked_at, item) VALUES ('reg:R', 'REGISTER', '2026-11-01', '2026-11-02', 'r', '', 'manoj', '2026-11-03 10:00:00', 'DEMO')\");c.execute(\"UPDATE setting SET value='on' WHERE key='mwr.reg_shavez'\");c.commit()"
O=$(env ROOT="$W/root" VPY="$VPY" SYSTEMCTL=true bash "$W/kit/undo_s837.sh" 2>&1)
chk "the undo line (undo_s837.sh) puts the live files back, the new reader gone, the open Stock Register ask closed" 'echo "$O" | grep -q "S837 UNDONE" && echo "$O" | grep -q "asks closed 1" && from'
O=$(run); chk "installed again after the undo (Shavez's switch either way): DONE" 'echo "$O" | grep -q ": DONE" && pins'
fi
if [ "$PART" = B ] || [ "$PART" = all ]; then
mk; O=$(run REHEARSE_RED_AT=4); chk "a red at [4/7]: the files back, the new reader gone" 'echo "$O" | grep -q "RED after placing" && from'
mk; O=$(run REHEARSE_RED_AT=5); chk "a red at [5/7]: the files back, the new reader gone" 'echo "$O" | grep -q "RED after placing" && from'
printf '#!/bin/sh\ncase "$1" in */take) echo 404;; *) echo 200;; esac\n' > "$W/hz404.sh"; chmod +x "$W/hz404.sh"
mk; O=$(run HEALTH_CMD="$W/hz404.sh"); chk "his list page 404 after the restart: RED, the files back, the new reader gone" 'echo "$O" | grep -q "not mounted" && from'
mk; echo "# drift" >> "$W/root/finance/reports_tile.py"; O=$(run); chk "a live file changed since the build: STOP at [2/7], nothing placed" 'echo "$O" | grep -q "\[2/7\].*changed after this kit" && [ ! -e "$W/root/marg_ingest/marg_register.py" ]'
mk; echo x >> "$W/kit/README.md"; O=$(run); chk "a corrupt kit: STOP at [1/7]" 'echo "$O" | grep -q "SUMS.md5 gate failed"'
mk; mkdir -p "$W/lock"; O=$(run); chk "another build holds the lock: nothing installed" 'echo "$O" | grep -q "another build holds the lock" && from'
fi
if [ "$PART" = C ] || [ "$PART" = all ]; then
cat > "$W/f812_same.py" <<'PY'
print("PASS  a check"); print("FAIL  a frozen expectation of mid-November (got 15)"); print("WALK 1/2")
PY
cat > "$W/f812_worse.py" <<'PY'
import sys
print("PASS  a check"); print("FAIL  a frozen expectation of mid-November (got 15)")
print("FAIL  section A lists them to look at" if "root_new" in sys.argv[1] else "PASS  section A lists them to look at"); print("WALK %d/3" % (1 if "root_new" in sys.argv[1] else 2))
PY
cat > "$W/f812_crash.py" <<'PY'
import sys
if "root_new" in sys.argv[1]:
    raise SystemExit("Traceback: made-up")
print("PASS  a check"); print("WALK 1/1")
PY
mk; O=$(run REHEARSE_NO_S812=0 W812="$W/f812_same.py"); chk "S812 red on the live files and the same on the rebuilt: installed, the frozen red named" 'echo "$O" | grep -q ": DONE" && echo "$O" | grep -q "already red on the LIVE" && pins'
mk; O=$(run REHEARSE_NO_S812=0 W812="$W/f812_worse.py"); chk "S812 a check red only on the rebuilt: STOP at [3/7], it is named, nothing installed" 'echo "$O" | grep -q "passes on the live files fails on the rebuilt" && echo "$O" | grep -q "FAIL  section A lists" && from'
mk; O=$(run REHEARSE_NO_S812=0 W812="$W/f812_crash.py"); chk "S812 not finishing on the rebuilt: STOP at [3/7], nothing installed" 'echo "$O" | grep -q "did not finish on the rebuilt" && from'
fi
rm -rf "$W"
echo "REHEARSAL $ok/$tot"
