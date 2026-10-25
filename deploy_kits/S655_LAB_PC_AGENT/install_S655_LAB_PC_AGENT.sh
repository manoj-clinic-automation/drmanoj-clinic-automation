#!/bin/bash
# =============================================================================
#  install_S655_LAB_PC_AGENT.sh · kit S655_LAB_PC_AGENT (session 351, the NK Pathology chat, 25-Oct-2026, D784)
#  The lab road's server end: /root/finance/lab_door.py (NEW, this project's), /root/labdata/ (NEW: the lab PC's
#  public key, the job key, the snapshot store), and TWO anchored edits to the parent's finance_app.py (the lab
#  doors in PUBLIC_PATHS; the guarded mount). The service clinic-finance is restarted once.
#
#  Run by (ONE line on the VPS; the lab PC's public key is the 64-hex word the lab PC's installer printed --
#  it is on the clinic Drive at Clinic Data Archive\FromLab\lab_public_key.txt):
#    cd /root/deploy/repo && git pull --ff-only && bash deploy_kits/S655_LAB_PC_AGENT/install_S655_LAB_PC_AGENT.sh <64-hex public key>
#
#    /root/finance/finance_app.py  f2e86ca7 (the 25-Oct bundle) -> built from the live bytes by make_S655_finance_app.py
#    /root/finance/lab_door.py     NEW  (pin in SUMS.md5)
#    /root/labdata/lab_keys.txt, lab_job_keys.txt  NEW   · /root/labdata/incoming/, lab_jobs/  (mode 700)
#    finance.db is NOT touched (no table of this kit); it is still backed up first, as every kit does.
#    Undo: put back finance_app.py.bak_S655_f2e86ca7, restart clinic-finance, healthz 200 (lab_door.py may stay).
# =============================================================================
set -u
KIT="S655_LAB_PC_AGENT"
KDIR="$(cd "$(dirname "$0")" && pwd)"
SPY="${SPY:-/usr/bin/python3}"; VPY="${VPY:-/root/wa/venv/bin/python3}"; FIN="${FIN:-/root/finance}"; LABH="${LABH:-/root/labdata}"
STAMP="$(date +%Y%m%d_%H%M%S)"; WALK="/tmp/s655_walk_$STAMP"
FROM=f2e86ca7919abc9e660b1bd5e811eebf
PUBKEY="${1:-}"
m5() { md5sum "$1" 2>/dev/null | awk '{print $1}'; }
say() { echo "$@"; }
cd "$KDIR" || { say "!! cannot enter the kit folder"; exit 1; }
md5sum -c SUMS.md5 >/dev/null 2>&1 || { say "!! [1/8] SUMS.md5 gate failed - nothing installed"; exit 1; }
[ "$(awk 'NR==1{print $3}' KIT_ID.txt)" = "$KIT" ] || { say "!! [1/8] KIT_ID.txt names another kit - nothing installed"; exit 1; }
DOOR_TO="$(m5 server/lab_door.py)"
echo "$PUBKEY" | grep -Eq '^[0-9a-f]{64}$' || { say "!! [1/8] the lab PC's PUBLIC key (64 hex) must be the one argument - nothing installed"; exit 1; }
say "[1/8] kit gates green; lab_door.py ${DOOR_TO:0:8}; the lab PC's key ${PUBKEY:0:8}..."
# --- the lock (CLAUDE.md: one build at a time on the shared server) ---
if ! mkdir /root/deploy/.claude_code_build.lock 2>/dev/null; then say "!! another build holds /root/deploy/.claude_code_build.lock - try again in a few minutes"; exit 1; fi
echo "$KIT" > /root/deploy/.claude_code_build.lock/owner
unlock() { rm -f /root/deploy/.claude_code_build.lock/owner; rmdir /root/deploy/.claude_code_build.lock 2>/dev/null; }
trap unlock EXIT
# --- already installed? ---
if grep -q "S655_LAB_PC_AGENT begin" "$FIN/finance_app.py" 2>/dev/null && [ "$(m5 "$FIN/lab_door.py")" = "$DOOR_TO" ]; then
  say "-- ALREADY INSTALLED (finance_app.py carries the S655 mount; lab_door.py at its pin). Keys refreshed below, nothing else."
  mkdir -p "$LABH" && chmod 700 "$LABH"
  grep -q "^$PUBKEY" "$LABH/lab_keys.txt" 2>/dev/null || printf '# lab_keys.txt -- PUBLIC keys that may post to /finance/api/lab/* (S655)\n%s  labpc (enrolled %s)\n' "$PUBKEY" "$STAMP" >> "$LABH/lab_keys.txt"
  cp -p server/lab_job_keys.txt "$LABH/lab_job_keys.txt"; chmod 600 "$LABH"/lab_keys.txt "$LABH"/lab_job_keys.txt
  curl -s -o /dev/null -w '   healthz %{http_code}\n' https://followup.dr-manoj.in/finance/healthz; exit 0
fi
[ "$(m5 "$FIN/finance_app.py")" = "$FROM" ] || { say "!! [2/8] $FIN/finance_app.py is not its pin ${FROM:0:8} (someone changed it since the brief) - nothing installed"; exit 1; }
[ -f "$FIN/lab_door.py" ] && [ "$(m5 "$FIN/lab_door.py")" != "$DOOR_TO" ] && { say "!! [2/8] $FIN/lab_door.py already exists and is not this kit's - nothing installed"; exit 1; }
say "[2/8] live finance_app.py at its pin (${FROM:0:8}); no lab_door.py on the box yet"
# --- build the TO file from the LIVE bytes ---
mkdir -p "$WALK" || exit 1
"$SPY" -B server/make_S655_finance_app.py "$FIN/finance_app.py" "$WALK/finance_app_TO.py" || { say "!! [3/8] the anchored edit did not apply - nothing installed"; rm -rf "$WALK"; exit 1; }
cp -p server/lab_door.py "$WALK/lab_door.py"
( cd "$WALK" && "$SPY" -m py_compile finance_app_TO.py && "$SPY" -m py_compile lab_door.py && "$VPY" -m py_compile finance_app_TO.py && "$VPY" -m py_compile lab_door.py ) \
  || { say "!! [3/8] compile failed on one of the two pythons - nothing installed"; rm -rf "$WALK"; exit 1; }
find "$WALK" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
TO="$(m5 "$WALK/finance_app_TO.py")"
say "[3/8] finance_app.py built from the live bytes -> ${TO:0:8}; both files compile on both pythons"
# --- the walk, on a loopback server with LAB_HOME on scratch (needs a file to send: the kit's own lab_door.py will do) ---
cp -p walk_s655.py labpc/lab_agent.py manojz/lab_sign.py "$WALK/"
WPY="$SPY"; "$SPY" -c "import flask" 2>/dev/null || WPY="$VPY"     # the walk needs Flask: the service's python first, else the venv
WOUT="$( cd "$WALK" && LAB_HOME="$WALK/labdata" timeout 420 "$WPY" -B walk_s655.py --door lab_door.py --agent lab_agent.py --sign lab_sign.py --mdb lab_door.py --port 18655 2>&1 | grep -E 'GREEN|RED|WALK_S655' )"
echo "$WOUT" | sed 's/^/   /'
echo "$WOUT" | grep -q "^WALK_S655 GREEN" || { say "!! [4/8] walk red - nothing installed"; rm -rf "$WALK"; exit 1; }
say "[4/8] walk green on loopback (30 checks, $WPY)"
# --- backups ---
"$SPY" - "$FIN/finance.db" "$FIN/finance.db.bak_S655_$STAMP" <<'PYEOF' || { say "!! [5/8] database backup failed - nothing installed"; rm -rf "$WALK"; exit 1; }
import sqlite3, sys
s = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); d = sqlite3.connect(sys.argv[2]); s.backup(d); d.close()
PYEOF
\cp -p "$FIN/finance_app.py" "$FIN/finance_app.py.bak_S655_${FROM:0:8}" || { say "!! [5/8] could not back up finance_app.py"; rm -rf "$WALK"; exit 1; }
say "[5/8] finance.db.bak_S655_$STAMP and finance_app.py.bak_S655_${FROM:0:8} made"
restore() {
  say "!! RED after placing - restoring finance_app.py byte-identically"
  \cp -p "$FIN/finance_app.py.bak_S655_${FROM:0:8}" "$FIN/finance_app.py"
  systemctl restart clinic-finance; sleep 4
  say "   finance_app.py $(m5 "$FIN/finance_app.py") · healthz $(curl -s -o /dev/null -w '%{http_code}' https://followup.dr-manoj.in/finance/healthz) · lab_door.py left in place (unmounted)"
  rm -rf "$WALK"; exit 1
}
# --- place ---
mkdir -p "$LABH/incoming" "$LABH/lab_jobs" && chmod 700 "$LABH" "$LABH/incoming" "$LABH/lab_jobs"
printf '# lab_keys.txt -- PUBLIC keys that may post to /finance/api/lab/* (S655). One per line: <64 hex> <label>\n%s  labpc (enrolled %s)\n' "$PUBKEY" "$STAMP" > "$LABH/lab_keys.txt"
cp -p server/lab_job_keys.txt "$LABH/lab_job_keys.txt"
chmod 600 "$LABH/lab_keys.txt" "$LABH/lab_job_keys.txt"
\cp -p server/lab_door.py "$FIN/lab_door.py" && chmod 644 "$FIN/lab_door.py" || restore
\cp -p "$WALK/finance_app_TO.py" "$FIN/finance_app.py" && chmod 644 "$FIN/finance_app.py" || restore
find "$KDIR" -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null
[ "$(m5 "$FIN/finance_app.py")" = "$TO" ] || restore
[ "$(m5 "$FIN/lab_door.py")" = "$DOOR_TO" ] || restore
say "[6/8] placed; md5 read back: finance_app.py ${TO:0:8}, lab_door.py ${DOOR_TO:0:8}; /root/labdata ready (keys 600, store 700)"
systemctl restart clinic-finance; sleep 5
HC="$(curl -s -o /dev/null -w '%{http_code}' https://followup.dr-manoj.in/finance/healthz)"
[ "$HC" = "200" ] || restore
# the lab door answers for itself: an unsigned post must be refused by the DOOR (401 NOT_YOU), not by the login gate (302)
LC="$(curl -s -o /dev/null -w '%{http_code}' -X POST --data-binary '{}' https://followup.dr-manoj.in/finance/api/lab/heartbeat)"
[ "$LC" = "401" ] || { say "   the lab door answered $LC to an unsigned post (expected 401 from the door itself)"; restore; }
say "[7/8] clinic-finance restarted; healthz $HC; the lab door answers 401 to an unsigned post (mounted, gate open, door shut)"
rm -rf "$WALK"
say "[8/8] $KIT: DONE. The lab PC's next heartbeat will be KEPT in $LABH/lab_heartbeat.json; snapshots land in $LABH/incoming/."
md5sum "$FIN/finance_app.py" "$FIN/lab_door.py"
