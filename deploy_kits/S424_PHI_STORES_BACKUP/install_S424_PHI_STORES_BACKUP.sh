#!/bin/bash
# install_S424_PHI_STORES_BACKUP.sh -- session 284, 27-Sep-2026. The Surgical Case Pack's records (/root/wa/casepack)
# and Vitals & Plan's (/root/wa/vitals) into the encrypted nightly state backup (v4 -> v5). Two anchored edits to
# /root/state_backup/clinic_state_backup.py; no service to restart (cron 01:50). Proven on a scratch copy first;
# then a read-only gather of the two REAL trees into /tmp (counted, then deleted) proves tonight's run will take them.
set -u
KIT="S424_PHI_STORES_BACKUP"; KDIR="$(cd "$(dirname "$0")" && pwd)"; VPY="${VPY:-/root/wa/venv/bin/python3}"
F=/root/state_backup/clinic_state_backup.py; FROM=05397337a09fbb3eafcc02bb12f3267d; TO=ede26d98a6aaf36188a797d732f4a4d7
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }; say() { echo "$@"; }
cd "$KDIR" || exit 1
say "[1/5] kit gates"
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/5] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/5] KIT_ID.txt names another kit"; exit 1; }
say "      green"
[ "$(m5 "$F")" = "$TO" ] && { say "-- ALREADY INSTALLED. Nothing to do."; exit 0; }
say "[2/5] live pin"
[ "$(m5 "$F")" = "$FROM" ] || { say "!! [2/5] live clinic_state_backup.py is $(m5 "$F"), not v4 $FROM - nothing installed"; exit 1; }
say "      exact (v4)"
say "[3/5] scratch: patch a copy + the walk"
W="/tmp/s424_walk_$(date +%Y%m%d_%H%M%S)"; mkdir -p "$W" && \cp -p "$F" "$W/csb.py" || { say "!! [3/5] scratch copy failed"; exit 1; }
"$VPY" -B apply_s424.py "$W/csb.py" >/dev/null && [ "$(m5 "$W/csb.py")" = "$TO" ] || { say "!! [3/5] the patched copy is not the predicted bytes - nothing installed"; rm -rf "$W"; exit 1; }
"$VPY" -B -m py_compile "$W/csb.py" || { say "!! [3/5] py_compile failed"; rm -rf "$W"; exit 1; }
WOUT="$( cd /tmp && timeout 120 "$VPY" -B "$KDIR/walk_s424.py" "$W/csb.py" "$KDIR" 2>/dev/null | tail -1 )"; rm -rf "$W"
echo "$WOUT" | grep -q "^WALK OK" || { say "!! [3/5] walk red: $WOUT - nothing installed"; exit 1; }
say "      $WOUT"
say "[4/5] backup + place"
BAK="$F.bak_S424_05397337"; \cp -p "$F" "$BAK" || { say "!! [4/5] backup failed"; exit 1; }
"$VPY" -B apply_s424.py "$F" | sed 's/^/      /'
[ "$(m5 "$F")" = "$TO" ] || { \cp -p "$BAK" "$F"; say "!! [4/5] placed bytes wrong - restored"; exit 1; }
say "[5/5] a read-only gather of the REAL trees (into /tmp, counted, then deleted)"
"$VPY" -B - "$F" <<'PY' || { \cp -p "$BAK" "$F"; say "!! [5/5] the real-tree gather failed - restored v4"; exit 1; }
import importlib.util, os, shutil, sys, tempfile
spec = importlib.util.spec_from_file_location("csb", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.SRC_FILES, m.SRC_DIRS = [], []
t = tempfile.mkdtemp(prefix="s424_real_")
try:
    g = m.gather({}, t, integrity_fatal=True)
    for d in m.SRC_TREES:
        lab = os.path.basename(d)
        n = [e for e in g.entries if e[0].startswith("data/%s/" % lab)]
        print("      %-18s %s file(s), %.1f KB%s" % (d, len(n), sum(e[1] for e in n) / 1024.0, "" if os.path.isdir(d) else "  (not there yet)"))
    print("      secrets skipped %d · sources for the guard: %s" % (g.secrets_skipped, ", ".join(x for x in g.sources_present if x in m.SRC_TREES)))
finally:
    shutil.rmtree(t, ignore_errors=True)
PY
say "      all green -- $KIT: DONE (tonight's 01:50 run carries both stores; the state file will list them)"
say "      backup: $BAK"
md5sum "$F"
